"""Taso 1 wave-rakenne RocketGame.Game:lle.

Sisaltaa wave 1-3 vihollisaallot ja boss-wave (wave 4).
"""

import pygame
import random
from Meteor.meteor_helpers import spawn_meteor, spawn_meteors_in_line

def _set_enemy_hp(enemy, hp):
	enemy.hp = hp
	enemy.max_hp = hp
	return enemy

def spawn_wave_taso1(
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
	enemy_speeds=None,  # Dict with speed overrides: {'straight': 220, 'circle': 180, ...}
):
	"""Spawn Level 1 enemies for the requested wave.

	Args:
		enemy_speeds: Optional dict with enemy speed overrides.
			Keys: 'straight', 'circle', 'down', 'up', 'zigzag', 'chase'
			Default speeds are used if not specified.

	Returns:
		bool: True if wave was handled by this level module, else False.
	"""
	# Setup default speeds and apply overrides
	if enemy_speeds is None:
		enemy_speeds = {}
	
	speeds = {
		'straight': enemy_speeds.get('straight', 120),
		'circle': enemy_speeds.get('circle', 2.2),  # angular_speed for CircleEnemy
		'down': enemy_speeds.get('down', 150),
		'up': enemy_speeds.get('up', 150),
		'zigzag': enemy_speeds.get('zigzag', 160),
		'chase': enemy_speeds.get('chase', 120),
	}
	if wave_num == 1:
		e1 = straight_enemy_cls(game.enemy_imgs[0], 200, 200, speed=speeds['straight'], sprite_index=1)
		e2 = circle_enemy_cls(
			game.enemy_imgs[1],
			game.tausta_leveys // 2 + 300,
			game.tausta_korkeus // 2,
			radius=180,
			angular_speed=speeds['circle'],
			sprite_index=2,
		)
		for enemy in (e1, e2):
			_set_enemy_hp(enemy, 1)
			apply_hitbox(enemy, hitbox_enemy)
			game.enemies.append(enemy)
		return True

	if wave_num == 2:
		# Mix of StraightEnemy, ZigZagEnemy, and ChaseEnemy
		edges = ["right", "top", "left"]
		
		# Wave 2 Part 1: StraightEnemy from edges
		for i, edge in enumerate(edges[:2]):  # Just 2 straight enemies
			if edge == "left":
				x = 80
				y = random.randint(80, game.tausta_korkeus - 80)
			elif edge == "right":
				x = game.tausta_leveys - 80
				y = random.randint(80, game.tausta_korkeus - 80)
			elif edge == "top":
				x = random.randint(80, game.tausta_leveys - 80)
				y = 80

			sprite_idx = i % len(game.enemy_imgs)
			enemy = straight_enemy_cls(game.enemy_imgs[sprite_idx], x, y, speed=speeds['straight'], sprite_index=sprite_idx+1)
			_set_enemy_hp(enemy, 1)
			if hasattr(enemy, "vel"):
				v = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
				if v.length_squared() == 0:
					v = pygame.Vector2(1, 0)
				enemy.vel = v.normalize() * speeds['straight']
			apply_hitbox(enemy, hitbox_enemy)
			game.enemies.append(enemy)
		
		# Wave 2 Part 2: ZigZagEnemy
		if zigzag_enemy_cls:
			sprite_idx = 2 % len(game.enemy_imgs)
			enemy = zigzag_enemy_cls(
				game.enemy_imgs[sprite_idx],
				game.tausta_leveys // 2,
				50,
				speed=speeds['zigzag'],
				amplitude=120,
				frequency=3.0,
				sprite_index=sprite_idx+1,
			)
			_set_enemy_hp(enemy, 1)
			apply_hitbox(enemy, hitbox_enemy)
			game.enemies.append(enemy)
		
		# Wave 2 Part 3: ChaseEnemy
		if chase_enemy_cls:
			sprite_idx = 0 % len(game.enemy_imgs)
			enemy = chase_enemy_cls(
				game.enemy_imgs[sprite_idx],
				game.tausta_leveys - 100,
				100,
				speed=speeds['chase'],
				sprite_index=sprite_idx+1,
			)
			_set_enemy_hp(enemy, 1)
			apply_hitbox(enemy, hitbox_enemy)
			game.enemies.append(enemy)
		
		# Add meteors to wave 2 - diagonal line formation
		spawn_meteors_in_line(
			game,
			game.tausta_leveys * 0.2, game.tausta_korkeus * 0.3,
			game.tausta_leveys * 0.8, game.tausta_korkeus * 0.7,
			4
		)
		
		return True

	if wave_num == 3:
		spacing = game.tausta_leveys // 6

		for i in range(3):
			x = spacing * (i + 1)
			y = 30
			sprite_idx = i % len(game.enemy_imgs)
			enemy = down_enemy_cls(game.enemy_imgs[sprite_idx], x, y, speed=speeds['down'], sprite_index=sprite_idx+1)
			_set_enemy_hp(enemy, 1)
			apply_hitbox(enemy, hitbox_enemy)
			game.enemies.append(enemy)

		for i in range(2):
			x = spacing * (i + 3.5)
			y = game.tausta_korkeus - 30
			sprite_idx = (i + 3) % len(game.enemy_imgs)
			enemy = up_enemy_cls(game.enemy_imgs[sprite_idx], x, y, speed=speeds['up'], sprite_index=sprite_idx+1)
			_set_enemy_hp(enemy, 1)
			apply_hitbox(enemy, hitbox_enemy)
			game.enemies.append(enemy)
		
		# Add meteors to wave 3 - grid formation in the middle area
		spawn_meteors_in_line(
			game,
			game.tausta_leveys * 0.1, game.tausta_korkeus * 0.2,
			game.tausta_leveys * 0.9, game.tausta_korkeus * 0.2,
			5
		)
		spawn_meteors_in_line(
			game,
			game.tausta_leveys * 0.1, game.tausta_korkeus * 0.5,
			game.tausta_leveys * 0.9, game.tausta_korkeus * 0.5,
			5
		)
		
		return True

	if wave_num == 4:
		game.boss = boss_enemy_cls(
			game.boss_image,
			pygame.Rect(0, 0, game.tausta_leveys, game.tausta_korkeus),
			hp=12,
			enter_speed=280,
			move_speed=320,
			hitbox_size=hitbox_boss,
			hitbox_offset=(0, 0),
		)
		apply_hitbox(game.boss, hitbox_boss)
		game.enemies.append(game.boss)
		return True

	return False
