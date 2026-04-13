import pygame
from pathlib import Path
import random
import math
import re
from Enemies.enemy import Enemy
from ui import get_enemy_bar_images, draw_healthbar_custom

class BossMissile(pygame.sprite.Sprite):
    """Boss missile with staged launch and car-like steering/drift."""

    def __init__(self, pos, flight_frames, explode_frames, player, launch_dir=(1, 0)):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.target = player
        self.dead = False

        self.launch_dir = pygame.Vector2(launch_dir)
        if self.launch_dir.length_squared() <= 1e-6:
            self.launch_dir = pygame.Vector2(1, 0)
        self.launch_dir = self.launch_dir.normalize()

        self.vel = self.launch_dir * random.uniform(24.0, 54.0)
        self.vel.y += random.uniform(85.0, 145.0)

        self.state = "drop"
        self.drop_ms = random.randint(260, 390)
        self.hover_ms = random.randint(320, 560)
        self.ignite_ms = random.randint(280, 430)
        self.timer_ms = 0
        self.guidance_locked = False
        self.lock_angle_deg = random.uniform(5.0, 8.0)

        # Steering/engine parameters for controlled turn + drift feel.
        self.heading = pygame.Vector2(self.launch_dir)
        self.thrust = random.uniform(760.0, 920.0)
        self.forward_drag = 0.18
        self.lateral_drag_guided = 1.65
        self.lateral_drag_locked = 3.05
        self.turn_rate_rad = math.radians(random.uniform(255.0, 320.0))
        self.max_speed = random.uniform(420.0, 540.0)
        self.cruise_speed = random.uniform(450.0, 580.0)
        self.ignite_blend = 0.0
        self._hover_phase = random.uniform(0.0, math.tau)
        self._render_spin_deg = 0.0
        # Sprite faces up in source art; offset aligns nose with heading.
        self.sprite_heading_offset_deg = -90.0
        self.explosion_draw_angle = 0.0

        # Animation state.
        self.flight_frames = list(flight_frames) if flight_frames else []
        self.explode_frames = list(explode_frames) if explode_frames else []
        self.frame_index = 0
        self.anim_timer = 0
        # Smooth flight, faster explosion impact.
        self.flight_anim_speed = 96
        self.explode_anim_speed = 52

        self.image = self.flight_frames[0] if self.flight_frames else pygame.Surface((16, 8), pygame.SRCALPHA)
        if not self.flight_frames:
            pygame.draw.ellipse(self.image, (255, 170, 80, 230), self.image.get_rect())
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _advance_flight_anim(self, dt_ms):
        if not self.flight_frames:
            return
        self.anim_timer += int(dt_ms)
        while self.anim_timer >= self.flight_anim_speed:
            self.anim_timer -= self.flight_anim_speed
            self.frame_index = (self.frame_index + 1) % len(self.flight_frames)
        self.image = self.flight_frames[self.frame_index]

    def _advance_explosion_anim(self, dt_ms):
        if not self.explode_frames:
            self.dead = True
            return
        self.anim_timer += int(dt_ms)
        while self.anim_timer >= self.explode_anim_speed:
            self.anim_timer -= self.explode_anim_speed
            self.frame_index += 1
            if self.frame_index >= len(self.explode_frames):
                self.dead = True
                return
        self.image = self.explode_frames[self.frame_index]

    def _rotate_towards_target(self, dt):
        if self.target is None or not hasattr(self.target, 'rect'):
            return None
        to_target = pygame.Vector2(self.target.rect.center) - self.pos
        if to_target.length_squared() <= 1e-6:
            return 0.0
        desired = to_target.normalize()

        cur_ang = math.atan2(self.heading.y, self.heading.x)
        desired_ang = math.atan2(desired.y, desired.x)
        diff = (desired_ang - cur_ang + math.pi) % (2.0 * math.pi) - math.pi
        max_turn = self.turn_rate_rad * dt
        if diff > max_turn:
            diff = max_turn
        elif diff < -max_turn:
            diff = -max_turn

        new_ang = cur_ang + diff
        self.heading = pygame.Vector2(math.cos(new_ang), math.sin(new_ang))
        return abs(math.degrees((desired_ang - new_ang + math.pi) % (2.0 * math.pi) - math.pi))

    def _integrate_guided_flight(self, dt):
        angle_error = self._rotate_towards_target(dt)

        # Engine ramp after ignition so the turn starts controlled.
        self.ignite_blend = min(1.0, self.ignite_blend + dt * 2.3)
        thrust_now = self.thrust * (0.35 + 0.65 * self.ignite_blend)

        accel = self.heading * thrust_now
        self.vel += accel * dt

        if self.vel.length_squared() > 1e-6:
            forward_speed = self.vel.dot(self.heading)
            forward_vec = self.heading * forward_speed
            lateral_vec = self.vel - forward_vec

            # Stronger sideways damping gives drift-like correction.
            self.vel -= forward_vec * self.forward_drag * dt
            self.vel -= lateral_vec * self.lateral_drag_guided * dt

        speed = self.vel.length()
        if speed > self.max_speed:
            self.vel.scale_to_length(self.max_speed)

        self.pos += self.vel * dt

        if angle_error is not None and angle_error <= self.lock_angle_deg:
            self.guidance_locked = True
            lock_speed = max(self.vel.length(), self.cruise_speed)
            self.vel = self.heading * lock_speed

    def _integrate_locked_flight(self, dt):
        # Keep fixed trajectory after lock; no more target steering.
        self.vel += self.heading * (self.thrust * 0.38) * dt
        if self.vel.length_squared() > 1e-6:
            forward_speed = self.vel.dot(self.heading)
            forward_vec = self.heading * forward_speed
            lateral_vec = self.vel - forward_vec
            self.vel -= lateral_vec * self.lateral_drag_locked * dt
        speed = self.vel.length()
        if speed > self.cruise_speed:
            self.vel.scale_to_length(self.cruise_speed)
        self.pos += self.vel * dt

    def update(self, dt_ms: int, world_rect: pygame.Rect | None = None):
        dt = max(0.0, float(dt_ms) / 1000.0)
        self.timer_ms += int(dt_ms)

        if self.state == "drop":
            # Horizontal release, then a short visible drop.
            self.vel.y += 315.0 * dt
            self.vel.x *= 0.988
            self.pos += self.vel * dt
            self._advance_flight_anim(dt_ms)
            if self.timer_ms >= self.drop_ms:
                self.state = "hover"
                self.timer_ms = 0
                self.vel *= 0.20

        elif self.state == "hover":
            # Brief hover pause before ignition.
            self._advance_flight_anim(dt_ms)
            t = self.timer_ms / 1000.0
            bob = math.sin(self._hover_phase + t * 5.2) * 6.0
            self.pos.y += bob * dt * 30.0
            self.vel *= 0.94
            self.pos += self.vel * dt

            if self.timer_ms >= self.hover_ms:
                self.state = "ignite"
                self.timer_ms = 0
                self.ignite_blend = 0.0
                self._render_spin_deg = 0.0

        elif self.state == "ignite":
            # Engine startup + roll before aggressive turn-in.
            self._advance_flight_anim(dt_ms)
            self.ignite_blend = min(1.0, self.ignite_blend + dt * 1.55)
            self._render_spin_deg = (self._render_spin_deg + 560.0 * dt) % 360.0
            self.vel += self.heading * (self.thrust * 0.18 * self.ignite_blend) * dt
            self.vel.y += 40.0 * dt
            self.vel *= 0.992
            self.pos += self.vel * dt

            if self.timer_ms >= self.ignite_ms:
                self.state = "flight"
                self.timer_ms = 0

        elif self.state == "flight":
            self._advance_flight_anim(dt_ms)
            if self.guidance_locked:
                self._integrate_locked_flight(dt)
            else:
                self._integrate_guided_flight(dt)

            # Explode when exiting gameplay area instead of disappearing.
            if world_rect is not None and not world_rect.colliderect(self.rect):
                self.explode()

        elif self.state == "explode":
            self._advance_explosion_anim(dt_ms)

        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def explode(self, parent=None):
        if self.state == "explode":
            return
        ang = math.degrees(math.atan2(self.heading.y, self.heading.x))
        self.explosion_draw_angle = -ang + self.sprite_heading_offset_deg
        self.state = "explode"
        self.frame_index = 0
        self.anim_timer = 0
        self.vel = pygame.Vector2(0, 0)
        if self.explode_frames:
            self.image = self.explode_frames[0]
        else:
            self.dead = True

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        if self.state == "explode":
            rotated = pygame.transform.rotate(self.image, self.explosion_draw_angle)
            r = rotated.get_rect(center=(int(self.rect.centerx - camera_x), int(self.rect.centery - camera_y)))
            screen.blit(rotated, r.topleft)
            return

        # Draw by heading to visually show drift when velocity differs.
        ang = math.degrees(math.atan2(self.heading.y, self.heading.x))
        draw_angle = -ang + self.sprite_heading_offset_deg
        if self.state == "ignite":
            draw_angle += self._render_spin_deg
        rotated = pygame.transform.rotate(self.image, draw_angle)
        r = rotated.get_rect(center=(int(self.rect.centerx - camera_x), int(self.rect.centery - camera_y)))
        screen.blit(rotated, r.topleft)


# MODIFICATION NOTES:
# 2026-03-04 - Added optional `hitbox_size` and `hitbox_offset` parameters
# to `BossEnemy.__init__` so the collision rectangle can be tuned
# independently of the visual sprite. This fixes cases where the visual
# artwork is asymmetric or the sprite's pivot doesn't match the logical
# collision center. Passing `hitbox_size=(w,h)` will resize the boss's
# `rect` while preserving its center; `hitbox_offset=(dx,dy)` shifts the
# rect relative to the sprite center. The code also defensively re-centers
# the `rect` at spawn to ensure predictable placement.

class BossEnemy(Enemy):
    _MISSILE_CACHE = None

    def __init__(self, image: pygame.Surface, world_rect: pygame.Rect,
                 hp: int = 10, enter_speed: float = 250, move_speed: float = 300,
                 hitbox_size: tuple | None = None, hitbox_offset: tuple = (0, 0)):
        
        # Spawn ylävasemmalta, hieman ruudun ulkopuolelta
        start_x = world_rect.left + image.get_width() // 2
        start_y = world_rect.top - image.get_height() // 2
        
        super().__init__(image, start_x, start_y)

        # Ensure rect is centred where we expect (defensive in case parent
        # behaviour changes). Also allow overriding the hitbox size/offset so
        # collision rect and visual sprite can be independently tuned.
        try:
            self.rect.center = (int(start_x), int(start_y))
        except Exception:
            pass

        # Optional hitbox override: size=(w,h) will resize the collision rect
        # while preserving centre; offset=(dx,dy) will shift the rect relative
        # to the sprite centre (useful when the visible sprite's artwork is
        # not symmetric).
        if hitbox_size is not None:
            try:
                c = self.rect.center
                w, h = int(hitbox_size[0]), int(hitbox_size[1])
                self.rect.size = (w, h)
                # apply offset after resizing
                dx, dy = int(hitbox_offset[0]), int(hitbox_offset[1])
                self.rect.center = (c[0] + dx, c[1] + dy)
            except Exception:
                pass

        self.world_rect = world_rect
        self.hp = hp
        self.max_hp = hp

        self.enter_speed = enter_speed
        self.move_speed = move_speed

        self.state = "entering"   # entering -> active
        self.vx = move_speed

        # Mihin kohtaan boss pysähtyy pystysuunnassa
        self.target_y = world_rect.top + 180

        # Missile attack cadence.
        self._shoot_cooldown_ms = random.randint(900, 1700)

    @classmethod
    def _load_missile_frames(cls):
        if cls._MISSILE_CACHE is not None:
            return cls._MISSILE_CACHE

        def _select_index_range(paths, label, min_idx, max_idx):
            selected = []
            rx = re.compile(rf"_{label}_(\d{{3}})\.png$", re.IGNORECASE)
            for p in paths:
                m = rx.search(p.name)
                if not m:
                    continue
                idx = int(m.group(1))
                if min_idx <= idx <= max_idx:
                    selected.append((idx, p))
            selected.sort(key=lambda item: item[0])
            return [p for _, p in selected]

        variants = {}
        missile_scale = 0.10
        
        try:
            # Try to find missile sprites; start from project root
            root = Path(__file__).resolve().parent.parent / "images" / "Space-Shooter_objects" / "PNG" / "Sprites" / "Missile"
            
            for variant in ("3", "2", "1"):
                flight_paths = _select_index_range(sorted(root.glob(f"Missile_{variant}_Flying_*.png")), "Flying", 0, 9)
                explode_paths = _select_index_range(sorted(root.glob(f"Missile_{variant}_Explosion_*.png")), "Explosion", 0, 8)
                flight = []
                explode = []
                for p in flight_paths:
                    try:
                        raw = pygame.image.load(str(p)).convert_alpha()
                        w = max(4, int(raw.get_width() * missile_scale))
                        h = max(4, int(raw.get_height() * missile_scale))
                        flight.append(pygame.transform.smoothscale(raw, (w, h)))
                    except Exception:
                        continue
                for p in explode_paths:
                    try:
                        raw = pygame.image.load(str(p)).convert_alpha()
                        w = max(6, int(raw.get_width() * missile_scale))
                        h = max(6, int(raw.get_height() * missile_scale))
                        explode.append(pygame.transform.smoothscale(raw, (w, h)))
                    except Exception:
                        continue
                if flight:
                    variants[variant] = {"flight": flight, "explode": explode}
        except Exception:
            # If anything fails, just continue to fallback
            pass

        if not variants:
            fallback = pygame.Surface((26, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(fallback, (255, 170, 80, 230), fallback.get_rect())
            variants["fallback"] = {"flight": [fallback], "explode": []}

        cls._MISSILE_CACHE = variants
        return variants

    def maybe_shoot(self, dt_ms: int, containers: dict | None = None, player=None):
        if self.state != "active" or player is None or not containers:
            return

        bullets = containers.get('bullets')
        if bullets is None:
            return

        self._shoot_cooldown_ms -= int(dt_ms)
        if self._shoot_cooldown_ms > 0:
            return

        self._shoot_cooldown_ms = random.randint(900, 1650)

        frames = self._load_missile_frames()
        variant_key = "3" if "3" in frames else ("2" if "2" in frames else ("1" if "1" in frames else next(iter(frames.keys()))))
        selected = frames[variant_key]
        flight_frames = selected.get("flight", [])
        explode_frames = selected.get("explode", [])

        spawn_offset = pygame.Vector2(random.uniform(-58.0, 58.0), random.uniform(32.0, 64.0))
        spawn_pos = pygame.Vector2(self.rect.center) + spawn_offset
        horizontal_dir = 1.0 if float(getattr(self, 'vx', 0.0)) >= 0.0 else -1.0
        missile = BossMissile(
            spawn_pos,
            flight_frames=flight_frames,
            explode_frames=explode_frames,
            player=player,
            launch_dir=(horizontal_dir, 0.0),
        )
        bullets.append(missile)

    def take_hit(self, amount=1):
        self.hp -= amount
        return self.hp <= 0

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0

        if self.state == "entering":
            # Liikkuu alaspäin
            self.rect.y += int(self.enter_speed * dt)

            if self.rect.centery >= self.target_y:
                self.rect.centery = self.target_y
                self.state = "active"

        elif self.state == "active":
            # Liikkuu vasen-oikea
            self.rect.x += int(self.vx * dt)

            if self.rect.left <= self.world_rect.left:
                self.rect.left = self.world_rect.left
                self.vx *= -1

            if self.rect.right >= self.world_rect.right:
                self.rect.right = self.world_rect.right
                self.vx *= -1

    def draw_health_bar(self, screen: pygame.Surface, index: int = 0, margin: int = 16):
        """Draw this boss's stacked health bar in the left margin.

        - `index` selects vertical stack order (0 = top).
        - uses `get_enemy_bar_images()` and `draw_healthbar_custom()` from `ui`.
        """
        try:
            # frame size + padding
            frame_w, frame_h = 340, 56
            frame_x = margin
            frame_y = margin + index * (frame_h + 8)

            # derive an inner padding so the decorative frame can surround the fill
            pad = max(20, int(min(frame_w, frame_h) * 0.12))

            # mframe_w - pad * 2 = kehysleveys minus padding molemmilta puolilta, eli täytön "sisäleveys".
            # max(4, ...) varmistaa, että fill_w ei koskaan ole pienempi kuin 4 (turvaksi ettei leveys olisi nolla tai negatiivinen).
            # Sama logiikka fill_h varten korkeudelle.
            # Esimerkki: jos frame_w = 340 ja pad = 6, niin frame_w - pad*2 = 340 - 12 = 328, jolloin fill_w = max(4, 328) = 328.
            # Jos taas padding olisi liian suuri (esim. 200), lasku antaisi negatiivisen arvon ja max palauttaisi 4 niin ettei täyttö katoa.
            fill_w = max(4, frame_w - pad * 2)
            fill_h = max(4, frame_h - pad * 2)

            # center fill inside frame
            fill_x = frame_x + (frame_w - fill_w) // 2
            fill_y = frame_y + (frame_h - fill_h) // 2

            cur_hp = getattr(self, 'hp', getattr(self, 'health', getattr(self, 'HP', 0)))
            max_hp = getattr(self, 'max_hp', getattr(self, 'max_health', getattr(self, 'HP_MAX', cur_hp)))

            imgs = get_enemy_bar_images()
            draw_healthbar_custom(screen,
                                  fill_w, fill_h,
                                  fill_x, fill_y,
                                  frame_w, frame_h,
                                  frame_x, frame_y,
                                  cur_hp, max_hp,
                                  imgs=imgs,
                                  tint=(255, 40, 40))
        except Exception:
            pass