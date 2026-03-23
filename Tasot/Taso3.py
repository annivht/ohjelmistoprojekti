"""Taso 3 wave-rakenne RocketGame.Game:lle.

Meteor-only test level for wave 1-4.
"""

from Meteor.meteor_helpers import spawn_moving_meteor

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
		spawn_moving_meteor(game, speed=70)
		return True

	if wave_num == 2:
		spawn_moving_meteor(game, speed=80)
		return True

	if wave_num == 3:
		spawn_moving_meteor(game, speed=90)
		return True

	if wave_num == 4:
		spawn_moving_meteor(game, speed=100)
		return True

	return False