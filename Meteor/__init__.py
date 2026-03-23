"""Meteor module for RocketGame.

Provides meteor obstacles that damage the player on collision.
"""

from Meteor.meteor import Meteor
from Meteor.meteor_helpers import (
    spawn_meteor,
    spawn_meteors_in_line,
    spawn_meteors_grid,
    spawn_meteors_circle,
)

__all__ = [
    'Meteor',
    'spawn_meteor',
    'spawn_meteors_in_line',
    'spawn_meteors_grid',
    'spawn_meteors_circle',
]
