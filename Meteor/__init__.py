"""Meteor module for RocketGame.

Provides moving meteor obstacles that damage the player on collision.
"""

from Meteor.meteor import Meteor
from Meteor.meteor_helpers import (
    spawn_moving_meteor,
    spawn_meteor,
)

__all__ = [
    'Meteor',
    'spawn_moving_meteor',
    'spawn_meteor',
]
