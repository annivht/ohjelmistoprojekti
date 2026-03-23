"""Helper functions for spawning meteors in levels.

Provides convenience functions to spawn moving meteors.
"""

import random
from Meteor.meteor import Meteor


def spawn_moving_meteor(game, speed=80):
    """Spawn a single large moving meteor outside play area.
    
    The meteor spawns at a random edge (top/bottom/left/right) and moves
    linearly across the screen and despawns after exiting.
    
    Args:
        game: The Game instance
        speed: Movement speed in pixels per second (default 80)
        
    Returns:
        The created Meteor instance
    """
    # Get screen bounds
    width = game.tausta_leveys
    height = game.tausta_korkeus
    spawn_margin = 140
    
    # Choose a random edge to spawn from
    edge = random.randint(0, 3)
    
    if edge == 0:  # Top -> move down
        x = random.randint(80, max(80, width - 80))
        y = -spawn_margin
        vel = (0, speed)
    elif edge == 1:  # Bottom -> move up
        x = random.randint(80, max(80, width - 80))
        y = height + spawn_margin
        vel = (0, -speed)
    elif edge == 2:  # Left -> move right
        x = -spawn_margin
        y = random.randint(80, max(80, height - 80))
        vel = (speed, 0)
    else:  # Right -> move left
        x = width + spawn_margin
        y = random.randint(80, max(80, height - 80))
        vel = (-speed, 0)
    
    meteor = Meteor(
        x, y,
        image=None,
        bounds=(width, height),
        speed=speed,
        velocity=vel,
    )
    game.meteors.append(meteor)
    return meteor


def spawn_meteor(game, x, y, image=None):
    """Spawn a single meteor at a specific position with random direction.
    
    Args:
        game: The Game instance
        x: X position in pixels
        y: Y position in pixels
        image: Optional pre-loaded pygame Surface for the meteor
        
    Returns:
        The created Meteor instance
    """
    meteor = Meteor(
        x, y,
        image=image,
        bounds=(game.tausta_leveys, game.tausta_korkeus),
        speed=80
    )
    game.meteors.append(meteor)
    return meteor

