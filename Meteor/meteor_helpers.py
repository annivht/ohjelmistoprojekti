"""Helper functions for spawning meteors in levels.

Provides convenience functions to spawn meteors at specified locations
or in patterns suitable for level design.
"""

from Meteor.meteor import Meteor


def spawn_meteor(game, x, y, image=None):
    """Spawn a single meteor in the game.
    
    Args:
        game: The Game instance
        x: X position in pixels
        y: Y position in pixels
        image: Optional pre-loaded pygame Surface for the meteor
        
    Returns:
        The created Meteor instance
    """
    meteor = Meteor(x, y, image=image)
    game.meteors.append(meteor)
    return meteor


def spawn_meteors_in_line(game, x1, y1, x2, y2, count, image=None):
    """Spawn multiple meteors in a line pattern.
    
    Args:
        game: The Game instance
        x1, y1: Starting position
        x2, y2: Ending position
        count: Number of meteors to spawn
        image: Optional pre-loaded pygame Surface for the meteors
        
    Returns:
        List of created Meteor instances
    """
    meteors = []
    for i in range(count):
        t = i / max(1, count - 1)
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        meteor = spawn_meteor(game, x, y, image=image)
        meteors.append(meteor)
    return meteors


def spawn_meteors_grid(game, start_x, start_y, spacing, cols, rows, image=None):
    """Spawn meteors in a grid pattern.
    
    Args:
        game: The Game instance
        start_x: Starting X position
        start_y: Starting Y position
        spacing: Distance between meteors in pixels
        cols: Number of columns
        rows: Number of rows
        image: Optional pre-loaded pygame Surface for the meteors
        
    Returns:
        List of created Meteor instances
    """
    meteors = []
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * spacing
            y = start_y + r * spacing
            meteor = spawn_meteor(game, x, y, image=image)
            meteors.append(meteor)
    return meteors


def spawn_meteors_circle(game, center_x, center_y, radius, count, image=None):
    """Spawn meteors in a circular pattern.
    
    Args:
        game: The Game instance
        center_x: Circle center X
        center_y: Circle center Y
        radius: Radius of the circle in pixels
        count: Number of meteors to spawn around the circle
        image: Optional pre-loaded pygame Surface for the meteors
        
    Returns:
        List of created Meteor instances
    """
    import math
    meteors = []
    for i in range(count):
        angle = (i / count) * 2 * math.pi
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        meteor = spawn_meteor(game, x, y, image=image)
        meteors.append(meteor)
    return meteors
