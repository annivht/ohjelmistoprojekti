"""Test level 2 spawn setup.

Contains only Straight enemies + Bosses + hazards (meteors, bombs).
No zigzag/down/up/circle enemies are spawned here.
"""

from pathlib import Path
import random
import re
import types

import pygame

from Enemies.EnemyHelpers import EnemyBullet


_SMALL_MISSILE_CACHE = None


def _set_enemy_hp(enemy, hp):
    enemy.hp = hp
    enemy.max_hp = hp
    return enemy


def _load_small_missile_frames(scale=0.16):
    global _SMALL_MISSILE_CACHE
    if _SMALL_MISSILE_CACHE is not None:
        return _SMALL_MISSILE_CACHE

    root = Path(__file__).resolve().parent.parent / "images" / "Space-Shooter_objects" / "PNG" / "Sprites" / "Missile"

    def _select(paths, label, min_idx, max_idx):
        out = []
        rx = re.compile(rf"_{label}_(\d{{3}})\.png$", re.IGNORECASE)
        for p in paths:
            m = rx.search(p.name)
            if not m:
                continue
            idx = int(m.group(1))
            if min_idx <= idx <= max_idx:
                out.append((idx, p))
        out.sort(key=lambda item: item[0])
        return [p for _, p in out]

    flight_paths = _select(sorted(root.glob("Missile_1_Flying_*.png")), "Flying", 0, 9)
    explode_paths = _select(sorted(root.glob("Missile_1_Explosion_*.png")), "Explosion", 0, 8)

    flight = []
    explode = []
    for p in flight_paths:
        try:
            raw = pygame.image.load(str(p)).convert_alpha()
            w = max(4, int(raw.get_width() * scale))
            h = max(4, int(raw.get_height() * scale))
            flight.append(pygame.transform.smoothscale(raw, (w, h)))
        except Exception:
            continue
    for p in explode_paths:
        try:
            raw = pygame.image.load(str(p)).convert_alpha()
            w = max(6, int(raw.get_width() * scale))
            h = max(6, int(raw.get_height() * scale))
            explode.append(pygame.transform.smoothscale(raw, (w, h)))
        except Exception:
            continue

    if not flight:
        fallback = pygame.Surface((8, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(fallback, (255, 170, 80, 230), fallback.get_rect())
        flight = [fallback]

    _SMALL_MISSILE_CACHE = {"flight": flight, "explode": explode}
    return _SMALL_MISSILE_CACHE


def _patch_straight_enemy(enemy, game, can_drop_bombs=False):
    frames = _load_small_missile_frames()

    enemy._test2_game = game
    enemy._mini_missile_flight = frames["flight"]
    enemy._mini_missile_explode = frames["explode"]
    enemy._mini_missile_cd_ms = random.randint(2200, 3600)
    enemy._mini_bomb_cd_ms = random.randint(5000, 7600)
    enemy._can_drop_bombs = bool(can_drop_bombs)
    enemy.drop_bomb_on_death = bool(can_drop_bombs)

    def _maybe_shoot(self, dt_ms: int, containers: dict | None = None, player=None):
        if player is None or not containers:
            return
        bullets = containers.get("bullets")
        if bullets is None:
            return

        self._mini_missile_cd_ms -= int(dt_ms)
        if self._mini_missile_cd_ms <= 0:
            self._mini_missile_cd_ms = random.randint(2600, 4200)
            target_vec = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
            if target_vec.length_squared() <= 1e-6:
                target_vec = pygame.Vector2(1, 0)
            direction = target_vec.normalize().rotate(random.uniform(-9.0, 9.0))

            spawn = pygame.Vector2(self.rect.center) + direction * (max(self.rect.width, self.rect.height) * 0.52)
            speed = random.uniform(220.0, 300.0)
            vel = direction * speed
            shot = EnemyBullet(
                spawn,
                vel,
                flight_frames=self._mini_missile_flight,
                explode_frames=self._mini_missile_explode,
                speed=speed,
            )
            shot.anim_speed = 74
            bullets.append(shot)

        if self._can_drop_bombs:
            self._mini_bomb_cd_ms -= int(dt_ms)
            if self._mini_bomb_cd_ms <= 0:
                self._mini_bomb_cd_ms = random.randint(6200, 9000)
                hs = getattr(self._test2_game, "hazard_system", None)
                if hs is not None:
                    offset = pygame.Vector2(random.uniform(-26, 26), random.uniform(18, 36))
                    hs.spawn_bomb(pygame.Vector2(self.rect.center) + offset)

    enemy.maybe_shoot = types.MethodType(_maybe_shoot, enemy)



def spawn_wave_test2(
    game,
    wave_num,
    apply_hitbox,
    hitbox_enemy,
    hitbox_boss,
    straight_enemy_cls,
    circle_enemy_cls,
    boss_enemy_cls,
    down_enemy_cls,
    up_enemy_cls,
    zigzag_enemy_cls=None,
    chase_enemy_cls=None,
    enemy_speeds=None,
):
    _ = (circle_enemy_cls, down_enemy_cls, up_enemy_cls, zigzag_enemy_cls, chase_enemy_cls, enemy_speeds)

    if wave_num != 1:
        return True

    world_w = game.tausta_leveys
    world_h = game.tausta_korkeus

    straight_specs = [
        (world_w * 0.24, world_h * 0.26, 112, True),
        (world_w * 0.50, world_h * 0.22, 118, False),
        (world_w * 0.78, world_h * 0.28, 114, False),
    ]

    for idx, (x, y, speed, bomb_dropper) in enumerate(straight_specs):
        sprite_idx = idx % len(game.enemy_imgs)
        e = straight_enemy_cls(
            game.enemy_imgs[sprite_idx],
            x,
            y,
            speed=speed,
            sprite_index=sprite_idx + 1,
        )
        _set_enemy_hp(e, 3 if bomb_dropper else 2)
        apply_hitbox(e, hitbox_enemy)
        _patch_straight_enemy(e, game, can_drop_bombs=bomb_dropper)
        game.enemies.append(e)

    boss_left = boss_enemy_cls(
        game.boss_image,
        pygame.Rect(0, 0, world_w, world_h),
        hp=24,
        enter_speed=170,
        move_speed=185,
        hitbox_size=hitbox_boss,
        hitbox_offset=(0, 0),
    )

    apply_hitbox(boss_left, hitbox_boss)

    boss_left.rect.centerx = int(world_w * 0.50)
    boss_left.target_y = int(world_h * 0.22)
    boss_left.vx = abs(float(getattr(boss_left, "vx", 205)))

    game.boss = boss_left
    game.enemies.append(boss_left)

    return True
