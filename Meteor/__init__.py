"""Meteor module for RocketGame.

Provides three-tier meteor system:
- MainMeteorite (100%): Large breakable meteor, breaks into 4x Meteor
- Meteor (50%): Medium breakable meteor, breaks into 2x SmallMeteorite
- SmallMeteorite (25%): Small meteor, does not break
"""

from Meteor.meteor import Meteor, MainMeteorite, SmallMeteorite
from Meteor.meteor_helpers import (
    spawn_moving_meteor,
    spawn_meteor,
)

__all__ = [
    'Meteor',
    'MainMeteorite',
    'SmallMeteorite',
    'spawn_moving_meteor',
    'spawn_meteor',
]
