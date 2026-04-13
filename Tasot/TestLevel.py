"""Hazard-focused test level spawn setup.

Wave 1 spawns a small enemy set plus one boss so hazard mechanics can be tested.
"""

import pygame


def _set_enemy_hp(enemy, hp):
    enemy.hp = hp
    enemy.max_hp = hp
    return enemy


def spawn_wave_test(
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
    if wave_num != 1:
        return True

    world_w = game.tausta_leveys
    world_h = game.tausta_korkeus

    enemies = [
        straight_enemy_cls(game.enemy_imgs[0], world_w * 0.26, world_h * 0.38, speed=130, sprite_index=1),
        circle_enemy_cls(game.enemy_imgs[1], world_w * 0.55, world_h * 0.50, radius=170, angular_speed=1.6, sprite_index=2),
        down_enemy_cls(game.enemy_imgs[2], world_w * 0.72, 60, speed=130, sprite_index=3),
    ]

    for e in enemies:
        _set_enemy_hp(e, 3)
        apply_hitbox(e, hitbox_enemy)
        game.enemies.append(e)

    boss = boss_enemy_cls(
        game.boss_image,
        pygame.Rect(0, 0, world_w, world_h),
        hp=45,
        enter_speed=180,
        move_speed=210,
        hitbox_size=hitbox_boss,
        hitbox_offset=(0, 0),
    )
    apply_hitbox(boss, hitbox_boss)
    game.boss = boss
    game.enemies.append(boss)
    
    # BOSS SAAPUI - TAUOTA TAUSTAMUSIIKKI JA TOISTA BOSS ÄÄNI
    from Audio import pelimusat
    if pelimusat.game_sounds:
        pelimusat.game_sounds.pause_music()  # TAUOTA PELIMUSA-ROOT
        pelimusat.game_sounds.play_music("boss_sound", loops=-1)  # TOISTA BOSS SOUND LOOPISSA

    return True
