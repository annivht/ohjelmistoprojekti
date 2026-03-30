"""Taso 3 wave-rakenne RocketGame.Game:lle.

Taso 3 käyttää Taso 2:n kaltaista wave-rakennetta ja lisää meteoreja.
"""
import random

import pygame

from Meteor.meteor_helpers import spawn_moving_meteor


def _set_enemy_hp(enemy, hp=2):
    """Aseta viholliselle elämät."""
    enemy.hp = hp
    enemy.max_hp = hp
    return enemy


def _spawn_hazard_meteor_cluster(game, speed=80):
    """Spawn a moving meteor cluster using HazardSystem meteors.

    Falls back to legacy meteors if hazard system is not available.
    """
    hs = getattr(game, "hazard_system", None)
    if hs is None:
        spawn_moving_meteor(game, speed=speed)
        return

    width = game.tausta_leveys
    height = game.tausta_korkeus
    x = random.randint(80, max(80, width - 80))
    # HazardSystem removes meteors outside world bounds, so spawn from inside top edge.
    y = 36
    dx = random.choice((-1, 1))
    base_vx = dx * speed * 0.7071
    base_vy = speed * 0.7071

    lead_tier = 3 if speed >= 120 else 2
    hs.spawn_meteor(tier=lead_tier, center=(x, y), velocity=(base_vx, base_vy))

    small_count = random.randint(2, 4)
    for _ in range(small_count):
        offset_x = random.randint(-140, 140)
        offset_y = random.randint(-30, 90)
        tier = random.choice((1, 1, 2))
        speed_mul = random.uniform(1.02, 1.22)
        child_x = max(24, min(width - 24, x + offset_x))
        child_y = max(24, min(height - 24, y + offset_y))
        small_vel = (
            base_vx * speed_mul + random.uniform(-12.0, 12.0),
            base_vy * speed_mul + random.uniform(-10.0, 10.0),
        )
        hs.spawn_meteor(tier=tier, center=(child_x, child_y), velocity=small_vel)


def _spawn_wave_meteors(game, wave_num):
    """Lisää meteorit wavekohtaisesti."""
    wave_speeds = {
        1: (95,),
        2: (110,),
        3: (125, 135),
        4: (140, 150),
    }

    for speed in wave_speeds.get(wave_num, (100,)):
        _spawn_hazard_meteor_cluster(game, speed=speed)


def spawn_wave_taso3(
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
    zigzag_enemy_cls,
    chase_enemy_cls,
    enemy_speeds=None,  # Dict with speed overrides
):
    """Spawn Level 3 enemies for the requested wave.

    Taso 3 wave-rakenne on Taso 2:n kaltainen, mutta jokaiseen waveen lisätään meteoreja.

    Args:
        enemy_speeds: Optional dict with enemy speed overrides.
            Keys: 'straight', 'circle', 'down', 'up', 'zigzag', 'chase', 'boss_enter', 'boss_move'
            Default speeds are used if not specified.

    Returns:
        bool: True if wave was handled by this level module, else False.
    """
    if enemy_speeds is None:
        enemy_speeds = {}

    speeds = {
        'straight': enemy_speeds.get('straight', 190),
        'circle': enemy_speeds.get('circle', 2.0),
        'down': enemy_speeds.get('down', 330),
        'up': enemy_speeds.get('up', 340),
        'zigzag': enemy_speeds.get('zigzag', 250),
        'chase': enemy_speeds.get('chase', 200),
        'boss_enter': enemy_speeds.get('boss_enter', 360),
        'boss_move': enemy_speeds.get('boss_move', 410),
    }

    w = game.tausta_leveys
    h = game.tausta_korkeus

    if wave_num == 1:
        spawns = [
            (120, 120),
            (w - 120, 120),
            (120, h - 120),
            (w - 120, h - 120),
        ]

        velocities = [
            pygame.Vector2(1, 1),
            pygame.Vector2(-1, 1),
            pygame.Vector2(1, -1),
            pygame.Vector2(-1, -1),
        ]

        speed = speeds['straight']

        for i, ((x, y), v) in enumerate(zip(spawns, velocities)):
            sprite_idx = i % len(game.enemy_imgs)
            enemy = straight_enemy_cls(
                game.enemy_imgs[sprite_idx],
                x,
                y,
                speed=speed,
                sprite_index=sprite_idx + 1,
            )

            if v.length_squared() > 0:
                v = v.normalize() * speed
                enemy.vx = v.x
                enemy.vy = v.y

            _set_enemy_hp(enemy, 4)
            apply_hitbox(enemy, hitbox_enemy)
            game.enemies.append(enemy)

        _spawn_wave_meteors(game, wave_num)
        return True

    if wave_num == 2:
        if zigzag_enemy_cls is None or chase_enemy_cls is None:
            return False

        e1 = zigzag_enemy_cls(
            game.enemy_imgs[0],
            w // 4,
            40,
            speed=speeds['zigzag'],
            amplitude=120,
            frequency=4.0,
            hp=4,
            sprite_index=1,
        )
        e2 = zigzag_enemy_cls(
            game.enemy_imgs[1],
            3 * w // 4,
            40,
            speed=speeds['zigzag'],
            amplitude=120,
            frequency=4.5,
            hp=4,
            sprite_index=2,
        )

        e3 = chase_enemy_cls(
            game.enemy_imgs[2],
            120,
            h // 2,
            speed=speeds['chase'],
            hp=4,
            sprite_index=3,
        )
        e4 = chase_enemy_cls(
            game.enemy_imgs[3],
            w - 120,
            h // 2,
            speed=speeds['chase'],
            hp=4,
            sprite_index=4,
        )

        for enemy in (e1, e2, e3, e4):
            _set_enemy_hp(enemy, 4)
            apply_hitbox(enemy, hitbox_enemy)
            game.enemies.append(enemy)

        _spawn_wave_meteors(game, wave_num)
        return True

    if wave_num == 3:
        top_x = [w // 6, w // 2, 5 * w // 6]
        bottom_x = [w // 4, w // 2, 3 * w // 4]

        for i, x in enumerate(top_x):
            sprite_idx = i % len(game.enemy_imgs)
            enemy = down_enemy_cls(
                game.enemy_imgs[sprite_idx],
                x,
                40,
                speed=speeds['down'],
                sprite_index=sprite_idx + 1,
            )
            _set_enemy_hp(enemy, 4)
            apply_hitbox(enemy, hitbox_enemy)
            game.enemies.append(enemy)

        for i, x in enumerate(bottom_x):
            sprite_idx = (i + 3) % len(game.enemy_imgs)
            enemy = up_enemy_cls(
                game.enemy_imgs[sprite_idx],
                x,
                h - 40,
                speed=speeds['up'],
                sprite_index=sprite_idx + 1,
            )
            _set_enemy_hp(enemy, 4)
            apply_hitbox(enemy, hitbox_enemy)
            game.enemies.append(enemy)

        if zigzag_enemy_cls is not None:
            mid = zigzag_enemy_cls(
                game.enemy_imgs[0],
                w // 2,
                60,
                speed=speeds['zigzag'],
                amplitude=160,
                frequency=3.5,
                hp=5,
                sprite_index=1,
            )
            _set_enemy_hp(mid, 5)
            apply_hitbox(mid, hitbox_enemy)
            game.enemies.append(mid)

        _spawn_wave_meteors(game, wave_num)
        return True

    if wave_num == 4:
        game.boss = boss_enemy_cls(
            game.boss_image,
            pygame.Rect(0, 0, w, h),
            hp=40,
            enter_speed=speeds['boss_enter'],
            move_speed=speeds['boss_move'],
            hitbox_size=hitbox_boss,
            hitbox_offset=(0, 0),
        )
        apply_hitbox(game.boss, hitbox_boss)
        game.enemies.append(game.boss)

        _spawn_wave_meteors(game, wave_num)
        return True

    return False