import random
import pygame

def _spawn_hazard_meteor_cluster(game, speed=80):
    hs = getattr(game, "hazard_system", None)
    if hs is None:
        return

    width = game.tausta_leveys
    height = game.tausta_korkeus

    x = random.randint(80, max(80, width - 80))
    y = 36

    dx = random.choice((-1, 1))
    base_vx = dx * speed * 0.7071
    base_vy = speed * 0.7071

    hs.spawn_meteor(tier=2, center=(x, y), velocity=(base_vx, base_vy))

    for _ in range(random.randint(2, 4)):
        offset_x = random.randint(-140, 140)
        offset_y = random.randint(-30, 90)

        child_x = max(24, min(width - 24, x + offset_x))
        child_y = max(24, min(height - 24, y + offset_y))

        small_vel = (
            base_vx * random.uniform(1.0, 1.2),
            base_vy * random.uniform(1.0, 1.2),
        )

        hs.spawn_meteor(tier=1, center=(child_x, child_y), velocity=small_vel)


def _spawn_wave_meteors(game, wave_num):
    wave_speeds = {
        1: (95,),
        2: (110,),
        3: (125, 135),
        4: (140,),
    }

    for speed in wave_speeds.get(wave_num, (100,)):
        _spawn_hazard_meteor_cluster(game, speed)


# =========================
# ENEMY HELPERS
# =========================

def _set_enemy_hp(enemy, hp=2):
    enemy.hp = hp
    enemy.max_hp = hp
    return enemy


# =========================
# MAIN WAVE SPAWN
# =========================

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
    enemy_speeds=None,
):
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

    # =========================
    # WAVE 1
    # =========================
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

        for i, ((x, y), v) in enumerate(zip(spawns, velocities)):

            sprite_idx = i % len(game.enemy_imgs)

            enemy = straight_enemy_cls(
                game.enemy_imgs[sprite_idx],
                x,
                y,
                speed=speeds['straight'],
                sprite_index=sprite_idx + 1,
            )

            # 🔥 yksi ampuu
            if i == 1:
                enemy.can_shoot = True

            if v.length_squared() > 0:
                v = v.normalize() * speeds['straight']
                enemy.vx = v.x
                enemy.vy = v.y

            _set_enemy_hp(enemy, 4)
            apply_hitbox(enemy, hitbox_enemy)
            game.enemies.append(enemy)

        _spawn_wave_meteors(game, wave_num)
        return True

    # =========================
    # WAVE 2
    # =========================
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

        for i, enemy in enumerate((e1, e2, e3, e4)):

            # 🔥 kaksi ampuu
            if i >= 2:
                enemy.can_shoot = True

            _set_enemy_hp(enemy, 4)
            apply_hitbox(enemy, hitbox_enemy)
            game.enemies.append(enemy)

        _spawn_wave_meteors(game, wave_num)
        return True

    # =========================
    # WAVE 3
    # =========================
    if wave_num == 3:

        top_x = [w // 6, w // 2, 5 * w // 6]
        bottom_x = [w // 4, w // 2, 3 * w // 4]

        # YLHÄÄLTÄ
        for i, x in enumerate(top_x):

            sprite_idx = i % len(game.enemy_imgs)

            enemy = down_enemy_cls(
                game.enemy_imgs[sprite_idx],
                x,
                40,
                speed=speeds['down'],
                sprite_index=sprite_idx + 1,
            )

            if i == 1:
                enemy.can_shoot = True

            _set_enemy_hp(enemy, 4)
            apply_hitbox(enemy, hitbox_enemy)
            game.enemies.append(enemy)

        # ALHAALTA
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

        # ZIGZAG
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

            mid.can_shoot = True

            _set_enemy_hp(mid, 5)
            apply_hitbox(mid, hitbox_enemy)
            game.enemies.append(mid)

        _spawn_wave_meteors(game, wave_num)
        return True

    # =========================
    # BOSS
    # =========================
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