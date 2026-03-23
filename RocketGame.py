"""
Module: RocketGame.py
Dependencies: pygame, os, random, SpriteSettings, PLAYER_LUOKAT.Player2 (Player2), EnemyAI (StraightEnemy, CircleEnemy), boss_enemy (BossEnemy), Points
Provides: main game loop, loads sprites and spawns enemies/boss, handles collisions and draws
Uses: EnemyHelpers for specific explosion spawn when needed
"""

import sys
import os
import time
from types import SimpleNamespace
from Enemies import enemy
import pygame
import random
from Enemies.EnemyAI import StraightEnemy, CircleEnemy, DownEnemy, UpEnemy, ZigZagEnemy, ChaseEnemy
from boss_enemy import BossEnemy
from points import Points
sys.path.append(os.path.dirname(__file__))
from player2 import Player2
from Valikot.NextLevel import NextLevel
from Valikot.gameOver import GameOverScreen
from leaderboard import Leaderboard
from SpriteSettings import SpriteSettings
from explosion import ExplosionManager
from Collision.collisions import SpatialHash, apply_impact, separate, _get_pos, get_collision_radius
from ui import init_enemy_health_bars, draw_hud
from Physics.box2d_world import Box2DPhysicsWorld, CollisionCategory
from physics_settings import load_physics_settings
import planets
from Meteor.meteor import Meteor
from Tasot.Taso1 import spawn_wave_taso1
# Import other level wave-spawn functions as they're created
try:
    from Tasot.Taso2 import spawn_wave_taso2
except ImportError:
    spawn_wave_taso2 = None
try:
    from Tasot.Taso3 import spawn_wave_taso3
except ImportError:
    spawn_wave_taso3 = None
try:
    from Tasot.Taso4 import spawn_wave_taso4
except ImportError:
    spawn_wave_taso4 = None
try:
    from Tasot.Taso5 import spawn_wave_taso5
except ImportError:
    spawn_wave_taso5 = None

from States.GameStateManager import GameStateManager
# Näytön koko
X, Y = 1600, 800
HEALTH_ICON_SIZE = (600, 200)
HEALTH_ICON_MARGIN = 16
max_w = max(1, X - 2 * HEALTH_ICON_MARGIN)
max_h = max(1, Y - 2 * HEALTH_ICON_MARGIN)
scale = min(max_w / HEALTH_ICON_SIZE[0], max_h / HEALTH_ICON_SIZE[1], 1.0)
HEALTH_ICON_SCALE_SIZE = (max(1, int(HEALTH_ICON_SIZE[0]*scale)), max(1, int(HEALTH_ICON_SIZE[1]*scale)))
HEALTH_ICON_POS = (X - HEALTH_ICON_SCALE_SIZE[0] - HEALTH_ICON_MARGIN, HEALTH_ICON_MARGIN)

# Hitbox-koko per tyyppi
HITBOX_SIZE_PLAYER = (64, 64)
HITBOX_SIZE_ENEMY = (48, 48)
HITBOX_SIZE_BOSS = (140, 140)
BOSS_EXPLOSION_HOLD_MS = 900
PLAYER_DEATH_HOLD_MS = 1100
PLAYER_DEATH_EXPLOSION_FPS = 12
PLAYER_DESTROYED_FRAME_MS = 95


def apply_hitbox(obj, size=None):
    """Asettaa objektin hitboxin ja collision_radiusin"""
    if size is None:
        return
    c = obj.rect.center
    w, h = int(size[0]), int(size[1])
    obj.rect.size = (w, h)
    obj.rect.center = c
    if hasattr(obj, 'pos'):
        obj.pos = pygame.Vector2(obj.rect.center)
    try:
        obj.collision_radius = max(8, int(max(obj.rect.width, obj.rect.height)*0.45))
    except Exception:
        pass


class Game:
    """Modulaarinen RocketGame-luokka, ohjattavissa PlayState kautta"""

    def __init__(self, screen, level_number=1):
        self.screen = screen
        self.level_number = level_number  # Track which level this instance manages (1-5)
        self.dt = 0
        self.camera_x = 0
        self.camera_y = 0
        self.running = True
        self.pause = False

        # Peliobjektit
        self.player = None
        self.enemies = []
        self.enemy_bullets = []
        self.muzzles = []
        self.meteors = []  # Static meteor obstacles
        self.boss = None
        self.current_wave = 1
        self.MAX_WAVE = 4  # Each level has up to 4 waves (1-3 normal, 4 = boss)
        self.wave_cleared = False
        self.boss_clear_menu_delay_remaining = None
        self.player_death_menu_delay_remaining = None
        self.level_completed = False
        self.game_over = False
        self.lives = 3
        self.enemy_hit_cooldown = 0
        self.enemy_hit_cooldown_duration = 1400
        self.enemy_calm_timer_ms = 0
        self.enemy_calm_duration_ms = 2400
        self.enemy_calm_shoot_scale = 0.45
        self.pistejarjestelma = None
        self.leaderboard = Leaderboard()
        try:
            self.leaderboard.load_from_file(os.path.join(os.path.dirname(__file__), 'leaderboard.json'))
        except FileNotFoundError:
            pass

        # Pygame-resurssit
        self.clock = pygame.time.Clock()
        self.explosion_manager = ExplosionManager()
        self.spatial_hash = SpatialHash()
        self.collisions = set()
        self.DEBUG_DRAW_COLLISIONS = True
        self.DEBUG_DRAW_ENEMY_FACING = os.environ.get('RG_DEBUG_ENEMY_FACING', '0').strip() in ('1', 'true', 'True', 'yes', 'on')
        self.USE_SPATIAL_COLLISIONS = True
        self.physics_world = None
        self.physics_metrics = {
            'physics_step_ms': 0.0,
            'substeps': 0,
            'contacts': 0,
            'profile': 'disabled',
            'fixed_dt': 0.0,
            'frame_ms': 0.0,
        }
        self.show_physics_stats = True
        self.physics_font = pygame.font.SysFont('Consolas', 16)
        self.enemy_debug_font = pygame.font.SysFont('Consolas', 14)
        self.user_physics_settings = load_physics_settings()
        env_profile = os.environ.get('RG_PHYSICS_PROFILE', '').strip().lower()
        self.physics_profile_name = env_profile or str(self.user_physics_settings.get('physics_profile', 'balanced')).strip().lower() or 'balanced'

        try:
            self.physics_world = Box2DPhysicsWorld(profile_name=self.physics_profile_name)
            self.physics_metrics['profile'] = self.physics_profile_name
            self.physics_metrics['fixed_dt'] = self.physics_world.fixed_dt
        except Exception:
            self.physics_world = None

        # Lataa tausta ja planeetat
        self._load_assets()

        # Alusta pelaaja ja ensimmäinen wave
        self.init_game_objects()

    def _load_assets(self):
        """Lataa tausta, vihollisten kuvat ja planeetat"""
        base_path = os.path.dirname(__file__)
        self.base_path = base_path
        self.tausta = pygame.image.load(os.path.join(base_path,'images','taustat','avaruus.png')).convert()
        self.tausta = pygame.transform.scale(self.tausta, (X, Y))
        self.tausta_leveys, self.tausta_korkeus = self.tausta.get_width(), self.tausta.get_height()

        # Lataa vihollisten kuvat
        viholliset_path = os.path.join(base_path, "images", "viholliset")
        self.enemy_imgs = [
            pygame.transform.scale(
                pygame.image.load(os.path.join(viholliset_path, f)).convert_alpha(),
                (64, 64)
            )
            for f in sorted([fn for fn in os.listdir(viholliset_path) if fn.lower().endswith(".png")],
                            key=lambda name: int(os.path.splitext(name)[0]))
        ]

        # SpriteSettings vihollisille
        self.ss = SpriteSettings(base_path=os.path.join(base_path, 'enemy-sprite'))
        self.ss.load_all()

        # Boss-kuva tason mukaan
        boss_files = {
            1: "12.png",
            2: "13.png",   
            #3: "14.png",
            #4: "15.png",
            #5: "16.png",
}

        boss_file = boss_files.get(self.level_number, "12.png")

        self.boss_image = pygame.transform.scale(
            pygame.image.load(os.path.join(viholliset_path, boss_file)).convert_alpha(),
            (320, 320)
)

        # Planeetat
        self.planeetat = [
            pygame.transform.scale(pygame.image.load(f"images/planeetat/slice{i}.png"), (100,100))
            for i in range(2,11)
        ]
        self.planeetta_paikat = [
            (random.randint(0, max(0,self.tausta_leveys-300)),
             random.randint(0, max(0,self.tausta_korkeus-300)))
            for _ in range(len(self.planeetat))
        ]

        # Pelaajan health HUD kuvat: images/elementit/15.png .. 20.png
        self.health_imgs = {}
        health_dir = os.path.join(base_path, 'images', 'elementit')
        for h in range(0, 6):
            img_index = 15 + h
            path = os.path.join(health_dir, f"{img_index}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, HEALTH_ICON_SCALE_SIZE)
                self.health_imgs[h] = img
            except Exception:
                self.health_imgs[h] = None

        # Initialize boss/enemy health bar images used by BossEnemy.
        try:
            init_enemy_health_bars(base_path)
        except Exception:
            try:
                init_enemy_health_bars()
            except Exception:
                pass

        # Ensure explosion animations are loaded before gameplay starts.
        # Without frames, spawn_enemy/spawn_boss are no-ops.
        try:
            self.explosion_manager.load_all_defaults()
        except Exception:
            pass

    def init_game_objects(self):
        """Alusta pelaaja, pistejärjestelmä ja ensimmäinen wave"""
        self.pistejarjestelma = Points()

        player_ship = 'FIGHTER'
        player_start_x = self.tausta_leveys // 2
        player_start_y = self.tausta_korkeus // 2
        player_scale_factor = 1

        self.player = Player2(player_ship, player_scale_factor, player_start_x, player_start_y, max_health=5)
        if hasattr(self.player, 'destroyed_anim_speed'):
            self.player.destroyed_anim_speed = PLAYER_DESTROYED_FRAME_MS

        apply_hitbox(self.player, HITBOX_SIZE_PLAYER)
        self._init_player_physics()
        self.lives = int(getattr(self.player, 'health', getattr(self.player, 'max_health', 5)))
        self.spawn_wave(self.current_wave)

    def _init_player_physics(self):
        if self.physics_world is None or self.player is None:
            return

        old_body = self.physics_world.get_body(self.player)
        if old_body is not None:
            self.physics_world.remove_entity(self.player)

        radius = max(8, int(getattr(self.player, 'collision_radius', 24)))
        body = self.physics_world.add_circle_body(
            self.player,
            radius_px=radius,
            mass=1.8,
            dynamic=True,
            bullet=False,
            category=CollisionCategory.PLAYER,
            mask=(CollisionCategory.ENEMY | CollisionCategory.METEOR | CollisionCategory.SENSOR),
        )
        speed_mul = float(self.user_physics_settings.get('speed_multiplier', 1.0))
        turn_mul = float(self.user_physics_settings.get('turn_multiplier', 1.0))
        base_profile = self.physics_world.profile
        body.profile = SimpleNamespace(
            name=base_profile.name,
            linear_damping=base_profile.linear_damping,
            angular_damping=base_profile.angular_damping,
            thrust_force=base_profile.thrust_force * speed_mul,
            turn_torque=base_profile.turn_torque * turn_mul,
            max_speed_mps=base_profile.max_speed_mps * speed_mul,
            brake_impulse=base_profile.brake_impulse * speed_mul,
            lateral_drift_damping=base_profile.lateral_drift_damping,
        )

        self.player.sprite_angle_offset_deg = float(self.user_physics_settings.get('sprite_angle_offset_deg', 0.0))
        self.physics_metrics['profile'] = f"{self.physics_profile_name} xS{speed_mul:.2f} xT{turn_mul:.2f}"
        self.player.bind_box2d_body(body)

    def _apply_player_knockback(self, direction, speed_px_per_s, blend_with_current=0.55):
        knockback = pygame.Vector2(direction) * float(speed_px_per_s)
        current = pygame.Vector2(getattr(self.player, 'vel', pygame.Vector2(0, 0)))
        blend = max(0.0, min(1.0, float(blend_with_current)))
        final_vel = current * blend + knockback * (1.0 - blend)

        if hasattr(self.player, 'vel'):
            self.player.vel = final_vel

        if self.physics_world is not None:
            body = self.physics_world.get_body(self.player)
            if body is not None:
                body.linearVelocity = (
                    float(final_vel.x) / self.physics_world.PPM,
                    float(final_vel.y) / self.physics_world.PPM,
                )

    def _start_enemy_calm_period(self):
        self.enemy_calm_timer_ms = max(self.enemy_calm_timer_ms, self.enemy_calm_duration_ms)

    def _calm_nearby_enemies(self, center, radius_px=260.0, cooldown_seconds=1.8):
        c = pygame.Vector2(center)
        r2 = float(radius_px) * float(radius_px)
        for enemy in self.enemies:
            try:
                d2 = (pygame.Vector2(enemy.rect.center) - c).length_squared()
            except Exception:
                continue
            if d2 <= r2 and hasattr(enemy, 'hit_player_cooldown'):
                enemy.hit_player_cooldown = max(float(getattr(enemy, 'hit_player_cooldown', 0.0)), float(cooldown_seconds))

    def _draw_physics_overlay(self, screen):
        if not self.show_physics_stats:
            return
        lines = [
            f"Physics profile: {self.physics_metrics.get('profile', 'n/a')}",
            f"Frame ms: {self.physics_metrics.get('frame_ms', 0.0):5.2f}",
            f"Physics ms: {self.physics_metrics.get('physics_step_ms', 0.0):5.2f}",
            f"Substeps: {self.physics_metrics.get('substeps', 0)}",
            f"Contacts: {self.physics_metrics.get('contacts', 0)}",
        ]
        y = 10
        for line in lines:
            surf = self.physics_font.render(line, True, (220, 230, 255))
            screen.blit(surf, (10, y))
            y += 18

    def _get_enemy_velocity(self, enemy):
        vel = getattr(enemy, 'vel', None)
        if vel is not None:
            try:
                return pygame.Vector2(float(vel.x), float(vel.y))
            except Exception:
                pass
        vx = float(getattr(enemy, 'vx', 0.0))
        vy = float(getattr(enemy, 'vy', 0.0))
        return pygame.Vector2(vx, vy)

    def _get_enemy_render_forward(self, enemy, vel):
        try:
            ang = float(getattr(enemy, 'display_angle', 0.0))
            forward = pygame.Vector2(math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2))
            if forward.length_squared() > 1e-6:
                return forward.normalize()
        except Exception:
            pass

        if vel.length_squared() > 1e-6:
            return vel.normalize()
        return pygame.Vector2(1, 0)

    def _draw_enemy_facing_debug(self, screen):
        if not self.DEBUG_DRAW_ENEMY_FACING:
            return

        cam = pygame.Vector2(float(self.camera_x), float(self.camera_y))
        for enemy in self.enemies:
            vel = self._get_enemy_velocity(enemy)
            forward = self._get_enemy_render_forward(enemy, vel)

            center = pygame.Vector2(float(enemy.rect.centerx), float(enemy.rect.centery))
            p0 = center - cam
            p1 = p0 + forward * 28.0

            vx = float(vel.x)
            expected_sign = 0
            if abs(vx) > 5.0:
                expected_sign = 1 if vx > 0 else -1
            facing_sign = 1 if forward.x >= 0 else -1

            mismatch = expected_sign != 0 and facing_sign != expected_sign
            color = (255, 80, 80) if mismatch else (120, 255, 140)

            pygame.draw.line(screen, color, (int(p0.x), int(p0.y)), (int(p1.x), int(p1.y)), 2)

            tip = p1
            side = pygame.Vector2(-forward.y, forward.x)
            left = tip - forward * 8.0 + side * 5.0
            right = tip - forward * 8.0 - side * 5.0
            pygame.draw.polygon(screen, color, [
                (int(tip.x), int(tip.y)),
                (int(left.x), int(left.y)),
                (int(right.x), int(right.y)),
            ])

            facing_txt = 'right' if facing_sign > 0 else 'left'
            label = f"{enemy.__class__.__name__} facing {facing_txt} | vx={vx:+.1f}"
            txt_color = (255, 120, 120) if mismatch else (200, 230, 255)
            txt = self.enemy_debug_font.render(label, True, txt_color)
            screen.blit(txt, (int(p0.x + 12), int(p0.y - 18)))

    def reset_game(self):
        """Resettaa pelin tilan ja pelaajan"""
        self.current_wave = 1
        self.wave_cleared = False
        self.boss_clear_menu_delay_remaining = None
        self.player_death_menu_delay_remaining = None
        self.level_completed = False
        self.game_over = False
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.muzzles.clear()
        self.meteors.clear()
        self.collisions.clear()
        self.player.health = getattr(self.player, 'max_health', 5)
        if hasattr(self.player, 'is_destroyed'):
            self.player.is_destroyed = False
        if hasattr(self.player, 'destroyed_anim_timer'):
            self.player.destroyed_anim_timer = 0
        if hasattr(self.player, 'destroyed_frame_index'):
            self.player.destroyed_frame_index = 0
        if hasattr(self.player, 'destroyed_angle'):
            self.player.destroyed_angle = float(getattr(self.player, 'angle', 0.0))
        self.lives = self.player.health
        self.spawn_wave(self.current_wave)
        self.pistejarjestelma = Points()
        pygame.event.clear()

    def spawn_wave(self, wave_num):
        """Spawnaa viholliset wave-numeroon ja level-numeroon perustuen"""
        self.enemies.clear()

        # Dispatch to correct level's spawn function
        spawn_func = None
        if self.level_number == 1:
            spawn_func = spawn_wave_taso1
        elif self.level_number == 2 and spawn_wave_taso2:
            spawn_func = spawn_wave_taso2
        elif self.level_number == 3 and spawn_wave_taso3:
            spawn_func = spawn_wave_taso3
        elif self.level_number == 4 and spawn_wave_taso4:
            spawn_func = spawn_wave_taso4
        elif self.level_number == 5 and spawn_wave_taso5:
            spawn_func = spawn_wave_taso5

        if spawn_func:
            handled = spawn_func(
                game=self,
                wave_num=wave_num,
                apply_hitbox=apply_hitbox,
                hitbox_enemy=HITBOX_SIZE_ENEMY,
                hitbox_boss=HITBOX_SIZE_BOSS,
                straight_enemy_cls=StraightEnemy,
                circle_enemy_cls=CircleEnemy,
                boss_enemy_cls=BossEnemy,
                down_enemy_cls=DownEnemy,
                up_enemy_cls=UpEnemy,
                zigzag_enemy_cls=ZigZagEnemy,
                chase_enemy_cls=ChaseEnemy,
            )
            if handled:
                return

        # Fallback: if no level handler or unhandled wave, spawn nothing
        # (Level 2-5 will use their own spawn logic when implemented)

    def update(self, events):
        """Päivitä pelilogiikka: pelaaja, viholliset, ammukset, collisionit jne."""
        frame_start = time.perf_counter()
        self.dt = self.clock.tick(60)

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                self.DEBUG_DRAW_ENEMY_FACING = not self.DEBUG_DRAW_ENEMY_FACING

        # Päivitä planeetat ja pelaaja
        planets.update_planet(self.dt)
        self.player.update(self.dt)

        if self.physics_world is not None:
            self.physics_world.step(self.dt / 1000.0)
            self.physics_metrics.update(self.physics_world.get_metrics())

        self.player.move(0,0,self.tausta_leveys,self.tausta_korkeus)

        if self.enemy_calm_timer_ms > 0:
            self.enemy_calm_timer_ms = max(0, self.enemy_calm_timer_ms - self.dt)

        # Kamera pelaajan ympärillä
        self.camera_x = max(0, min(self.player.rect.centerx - X//2, self.tausta_leveys - X))
        self.camera_y = max(0, min(self.player.rect.centery - Y//2, self.tausta_korkeus - Y))

        # Päivitä viholliset
        for e in self.enemies:
            e.update(self.dt, self.player, pygame.Rect(0,0,self.tausta_leveys,self.tausta_korkeus))
            shoot_dt = self.dt
            if self.enemy_calm_timer_ms > 0:
                shoot_dt = self.dt * self.enemy_calm_shoot_scale
            if isinstance(e, BossEnemy):
                e.maybe_shoot(shoot_dt, {'bullets': self.enemy_bullets, 'muzzles': self.muzzles}, player=self.player)
            else:
                e.maybe_shoot(shoot_dt, {'bullets': self.enemy_bullets, 'muzzles': self.muzzles})

        # Päivitä meteorit ja poista ruudun läpi menneet
        for meteor in list(self.meteors):
            meteor.update(self.dt)
            if getattr(meteor, 'dead', False):
                self.meteors.remove(meteor)

        # Ammukset
        for bullet in list(self.player.weapons.bullets):
            for enemy in list(self.enemies):
                if bullet.rect.colliderect(enemy.rect):
                    impact_pos = bullet.rect.center

                    if bullet in self.player.weapons.bullets:
                        self.player.weapons.bullets.remove(bullet)

                    if isinstance(enemy, BossEnemy):
                        damage = getattr(bullet, "damage", 1)
                        died = enemy.take_hit(damage)

                        if died:
                            self.explosion_manager.spawn_boss(enemy.rect.center, fps=20)
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                                self.pistejarjestelma.lisaa_piste(5)
                        else:
                            self.explosion_manager.spawn_hit(impact_pos, fps=24)

                    else:
                        damage = getattr(bullet, "damage", 1)

                        if hasattr(enemy, "hp"):
                            enemy.hp -= damage
                            if enemy.hp <= 0:
                                self.explosion_manager.spawn_enemy(enemy.rect.center, fps=20)
                                if enemy in self.enemies:
                                    self.enemies.remove(enemy)
                                self.pistejarjestelma.lisaa_piste(1)
                            else:
                                self.explosion_manager.spawn_hit(impact_pos, fps=24)
                        else:
                            self.explosion_manager.spawn_enemy(impact_pos, fps=20)
                    
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                            self.pistejarjestelma.lisaa_piste(1)

                    break

        for b in list(self.enemy_bullets):
            b.update(self.dt, pygame.Rect(0,0,self.tausta_leveys,self.tausta_korkeus))
            if getattr(b,'dead',False):
                self.enemy_bullets.remove(b)
            elif (
                getattr(b,'state','')=='flight'
                and b.rect.colliderect(self.player.rect)
                and self.lives > 0
                and self.player_death_menu_delay_remaining is None
            ):
                b.explode()
                self.enemy_bullets.remove(b)
                self.player.health = max(0, self.player.health-1)
                self.lives = self.player.health
                try:
                    if hasattr(self.player, 'trigger_hit_animation'):
                        self.player.trigger_hit_animation()
                except Exception:
                    pass

        # Meteor collision handling
        # Player vs meteors: player loses health on collision
        meteor_hit_cooldown = getattr(self, '_meteor_hit_cooldown', 0)
        if meteor_hit_cooldown <= 0 and self.lives > 0 and self.player_death_menu_delay_remaining is None:
            for meteor in self.meteors:
                if self.player.rect.colliderect(meteor.rect):
                    self.player.health = max(0, self.player.health - 1)
                    self.lives = self.player.health
                    try:
                        if hasattr(self.player, 'trigger_hit_animation'):
                            self.player.trigger_hit_animation()
                    except Exception:
                        pass
                    
                    # Apply knockback to player
                    player_center = pygame.Vector2(self.player.rect.center)
                    meteor_center = pygame.Vector2(meteor.rect.center)
                    direction = player_center - meteor_center
                    if direction.length_squared() == 0:
                        direction = pygame.Vector2(1, 0)
                    else:
                        direction = direction.normalize()
                    
                    self._apply_player_knockback(direction, 360)
                    
                    if hasattr(self.player, "collision_bounce_locked"):
                        self.player.collision_bounce_locked = True
                        self.player.collision_bounce_timer = 0.18
                    
                    self._meteor_hit_cooldown = self.enemy_hit_cooldown_duration
                    break
        
        if meteor_hit_cooldown > 0:
            self._meteor_hit_cooldown = max(0, meteor_hit_cooldown - self.dt)
        
        # Player bullets vs meteors: bullets pass through (no damage to meteors)
        # Meteors are invulnerable, so bullets just pass through them
        for meteor in self.meteors:
            for bullet in list(self.player.weapons.bullets):
                if bullet.rect.colliderect(meteor.rect):
                    # Remove bullet that hits meteor
                    if bullet in self.player.weapons.bullets:
                        self.player.weapons.bullets.remove(bullet)

        # Kontakti-osuma vihollisen ja pelaajan välillä cooldownilla.
        if self.enemy_hit_cooldown <= 0 and self.lives > 0 and self.player_death_menu_delay_remaining is None:
            for enemy in self.enemies:
                if self.player.rect.colliderect(enemy.rect):
                    self.player.health = max(0, int(getattr(self.player, 'health', self.lives)) - 1)
                    self.lives = self.player.health

                    try:
                        if hasattr(self.player, 'trigger_hit_animation'):
                            self.player.trigger_hit_animation()
                    except Exception:
                        pass

                    player_center = pygame.Vector2(self.player.rect.center)
                    enemy_center = pygame.Vector2(enemy.rect.center)
                    direction = player_center - enemy_center

                    if direction.length_squared() == 0:
                        direction = pygame.Vector2(1, 0)
                    else:
                        direction = direction.normalize()

                # Smooth knockback pelaajalle
                    self._apply_player_knockback(direction, 320)

                # Lukitse ohjaus hetkeksi, jotta knockback ehtii näkyä
                    if hasattr(self.player, "collision_bounce_locked"):
                        self.player.collision_bounce_locked = True
                        self.player.collision_bounce_timer = 0.22
                    # estä vihollista jahtaamasta heti takaisin
                    if hasattr(enemy, "hit_player_cooldown"):
                        enemy.hit_player_cooldown = 2.5

                    # Non-boss enemies explode on collision to prevent instant chain hits.
                    if not isinstance(enemy, BossEnemy):
                        self.explosion_manager.spawn_enemy(enemy.rect.center, fps=22)
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                            self.pistejarjestelma.lisaa_piste(1)

                    self._start_enemy_calm_period()
                    self._calm_nearby_enemies(self.player.rect.center)

                    self.enemy_hit_cooldown = self.enemy_hit_cooldown_duration
                    break
        if self.enemy_hit_cooldown > 0:
            self.enemy_hit_cooldown -= self.dt
        

        # Wave progression: wave 1 -> 2 -> 3 -> boss (4).
        # A wave is clear only when both enemies and meteors are gone.
        if len(self.enemies) == 0 and len(self.meteors) == 0 and not self.level_completed and self.lives > 0:
            if self.current_wave < self.MAX_WAVE:
                self.current_wave += 1
                self.enemy_bullets.clear()
                self.muzzles.clear()
                self.spawn_wave(self.current_wave)
            else:
                # Boss beaten: let explosion animation play briefly before
                # moving to level complete state.
                if self.boss_clear_menu_delay_remaining is None:
                    self.boss_clear_menu_delay_remaining = BOSS_EXPLOSION_HOLD_MS

        if self.lives <= 0 and self.player_death_menu_delay_remaining is None:
            self.leaderboard.add_score("", self.pistejarjestelma.hae_pisteet())
            self.leaderboard.save_to_file(os.path.join(self.base_path, 'leaderboard.json'))
            print(self.leaderboard.get_player_scores())

            if hasattr(self.player, 'is_destroyed'):
                self.player.is_destroyed = True
            if hasattr(self.player, 'destroyed_anim_timer'):
                self.player.destroyed_anim_timer = 0
            if hasattr(self.player, 'destroyed_frame_index'):
                self.player.destroyed_frame_index = 0
            if hasattr(self.player, 'destroyed_angle'):
                self.player.destroyed_angle = float(getattr(self.player, 'angle', 0.0))
            if hasattr(self.player, 'vel'):
                self.player.vel = pygame.Vector2(0, 0)

            # Keep Game Over delay long enough for the slower destroyed + explosion animations.
            destroyed_count = len(getattr(self.player, 'destroyed_frames', []) or getattr(self.player, 'destroyed_sprites', []))
            destroyed_speed_ms = int(getattr(self.player, 'destroyed_anim_speed', PLAYER_DESTROYED_FRAME_MS))
            destroyed_total_ms = destroyed_count * max(1, destroyed_speed_ms)
            self.player_death_menu_delay_remaining = max(
                PLAYER_DEATH_HOLD_MS,
                destroyed_total_ms + 180,
            )

            try:
                print(
                    f"[DEATH DEBUG] destroyed_frames={destroyed_count}, "
                    f"destroyed_frame_ms={destroyed_speed_ms}, "
                    f"player_explosion_frames=0, "
                    f"player_explosion_fps=0, "
                    f"hold_ms={self.player_death_menu_delay_remaining}"
                )
            except Exception:
                pass

        # Räjähdykset
        self.explosion_manager.update(self.dt)

        if self.boss_clear_menu_delay_remaining is not None:
            self.boss_clear_menu_delay_remaining -= self.dt
            if self.boss_clear_menu_delay_remaining <= 0:
                self.level_completed = True
                self.running = False

        if self.player_death_menu_delay_remaining is not None:
            self.player_death_menu_delay_remaining -= self.dt
            if self.player_death_menu_delay_remaining <= 0:
                self.game_over = True
                self.running = False

        self.physics_metrics['frame_ms'] = (time.perf_counter() - frame_start) * 1000.0

    def draw(self, target_screen):
        """Piirrä kaikki peliobjektit annettuun ruutuun"""
        self.screen = target_screen
        self.screen.blit(self.tausta, (0,0), area=(self.camera_x, self.camera_y, X, Y))

        for kuva, (x, y) in zip(self.planeetat, self.planeetta_paikat):
            self.screen.blit(kuva, (x - self.camera_x, y - self.camera_y))

        for meteor in self.meteors:
            meteor.draw(self.screen, self.camera_x, self.camera_y)

        for e in self.enemies:
            e.draw(self.screen, self.camera_x, self.camera_y)

        # Boss HP barit vasempaan yläkulmaan
        for idx, e in enumerate([be for be in self.enemies if isinstance(be, BossEnemy)]):
            e.draw_health_bar(self.screen, idx)

        for b in self.enemy_bullets:
            b.draw(self.screen, self.camera_x, self.camera_y)

        for m in self.muzzles:
            m.draw(self.screen, self.camera_x, self.camera_y)

        self.player.draw(self.screen, self.camera_x, self.camera_y)
        self.explosion_manager.draw(self.screen, self.camera_x, self.camera_y)

        self.pistejarjestelma.show_score(10,10, pygame.font.SysFont('Arial',24), self.screen)
        draw_hud(self.screen, X, Y, self.player, self.lives, self.health_imgs, HEALTH_ICON_POS)
        self._draw_enemy_facing_debug(self.screen)
        self._draw_physics_overlay(self.screen)


# Compatibility bridge for old function-style callers.
_active_game = None


def init(screen):
    """Initialize a single active Game instance for legacy callers."""
    global _active_game
    _active_game = Game(screen)
    return _active_game


def update(events):
    """Update active Game instance if initialized."""
    if _active_game is not None:
        _active_game.update(events)


def draw(screen):
    """Draw active Game instance if initialized."""
    if _active_game is not None:
        _active_game.draw(screen)


def is_running():
    """Return whether active Game instance is running."""
    return _active_game is not None and bool(_active_game.running)


def get_active_game():
    """Expose active game for code that still needs direct access."""
    return _active_game