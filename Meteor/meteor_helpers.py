"""Helper functions for spawning meteors in levels.

Provides convenience functions to spawn moving meteors of different sizes:
- MainMeteorite (100%): Large breakable meteor
- Meteor (50%): Medium breakable meteor
- SmallMeteorite (25%): Small meteor
"""

import random
from Meteor.meteor import Meteor, MainMeteorite, SmallMeteorite


def spawn_moving_meteor(game, speed=80, use_main=True):
    """Spawn a meteor cluster with one large meteor and smaller meteors.
    
    The meteor spawns above the play area and moves diagonally downward
    (down-left or down-right), then despawns after exiting.
    
    Args:
        game: The Game instance
        speed: Movement speed in pixels per second (default 80)
        use_main: If True, spawn MainMeteorite (100%), else spawn Meteor (50%) as lead
        
    Returns:
        The lead meteor instance
    """
    # Get screen bounds
    width = game.tausta_leveys
    height = game.tausta_korkeus
    spawn_margin = 140
    
    # Spawn above top edge and move diagonally downward.
    x = random.randint(80, max(80, width - 80))
    y = -spawn_margin
    dx = random.choice((-1, 1))
    vel = (dx * speed * 0.7071, speed * 0.7071)
    
    # Spawn lead meteor (MainMeteorite or Meteor)
    if use_main:
        lead_meteor = MainMeteorite(
            x, y,
            image=None,
            bounds=(width, height),
            speed=speed,
            velocity=vel
        )
    else:
        lead_meteor = Meteor(
            x, y,
            image=None,
            bounds=(width, height),
            speed=speed,
            velocity=vel,
            size_scale=0.5
        )
    game.meteors.append(lead_meteor)

    # Add 2-4 smaller meteors (50% size) around the lead meteor to form a cluster.
    small_count = random.randint(2, 4)
    for _ in range(small_count):
        offset_x = random.randint(-140, 140)
        offset_y = random.randint(-120, 30)
        speed_mul = random.uniform(1.02, 1.22)

        small_vel = (
            vel[0] * speed_mul + random.uniform(-12.0, 12.0),
            vel[1] * speed_mul + random.uniform(-10.0, 10.0),
        )

        small_meteor = Meteor(
            x + offset_x,
            y + offset_y,
            image=None,
            bounds=(width, height),
            speed=speed * speed_mul,
            velocity=small_vel,
            size_scale=0.5
        )
        game.meteors.append(small_meteor)

    return lead_meteor


def spawn_meteor(game, x, y, image=None, meteor_type="medium"):
    """Spawn a single meteor at a specific position.
    
    Args:
        game: The Game instance
        x: X position in pixels
        y: Y position in pixels
        image: Optional pre-loaded pygame Surface for the meteor
        meteor_type: "main" (100%), "medium" (50%), or "small" (25%)
        
    Returns:
        The created meteor instance
    """
    bounds = (game.tausta_leveys, game.tausta_korkeus)
    
    if meteor_type == "main":
        meteor = MainMeteorite(x, y, image=image, bounds=bounds, speed=80)
    elif meteor_type == "small":
        meteor = SmallMeteorite(x, y, image=image, bounds=bounds, speed=80)
    else:  # "medium" or default
        meteor = Meteor(x, y, image=image, bounds=bounds, speed=80, size_scale=0.5)
    
    game.meteors.append(meteor)
    return meteor