"""Taso 3 wave-rakenne RocketGame.Game:lle.

Meteor-only test level for wave 1-4.
"""

import random

from Meteor.meteor_helpers import spawn_moving_meteor


def _spawn_hazard_meteor_cluster(game, speed=80):
	"""Spawn a moving meteor cluster using HazardSystem meteors.

	Falls back to legacy meteors if hazard system is not available.
	"""
	hs = getattr(game, "hazard_system", None)
	if hs is None:
		spawn_moving_meteor(game, speed=speed)
		return

	width = game.tausta_leveys
	spawn_margin = 140
	x = random.randint(80, max(80, width - 80))
	y = -spawn_margin
	dx = random.choice((-1, 1))
	base_vx = dx * speed * 0.7071
	base_vy = speed * 0.7071

	lead_tier = 3 if speed >= 120 else 2
	hs.spawn_meteor(tier=lead_tier, center=(x, y), velocity=(base_vx, base_vy))

	small_count = random.randint(2, 4)
	for _ in range(small_count):
		offset_x = random.randint(-140, 140)
		offset_y = random.randint(-120, 30)
		tier = random.choice((1, 1, 2))
		speed_mul = random.uniform(1.02, 1.22)
		small_vel = (
			base_vx * speed_mul + random.uniform(-12.0, 12.0),
			base_vy * speed_mul + random.uniform(-10.0, 10.0),
		)
		hs.spawn_meteor(tier=tier, center=(x + offset_x, y + offset_y), velocity=small_vel)

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
	zigzag_enemy_cls=None,
    chase_enemy_cls=None,
	enemy_speeds=None,  # Dict with speed overrides
):
	"""Spawn Level 3 meteor waves for the requested wave.

	Returns:
		bool: True if wave was handled by this level module, else False.
	"""
	# Unused parameters are kept for compatibility with the level dispatch API.
	_ = (
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
		enemy_speeds,
	)

	if wave_num == 1:
		_spawn_hazard_meteor_cluster(game, speed=95)
		return True

	if wave_num == 2:
		_spawn_hazard_meteor_cluster(game, speed=110)
		return True

	if wave_num == 3:
		_spawn_hazard_meteor_cluster(game, speed=125)
		return True

	if wave_num == 4:
		_spawn_hazard_meteor_cluster(game, speed=140)
		return True

	return False