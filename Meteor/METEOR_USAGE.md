# Meteor System Usage Guide for RocketGame

The meteor system provides large moving obstacles that:
- Move linearly in random directions (up/down/left/right)
- Bounce off screen edges
- Damage the player by 1 health on collision
- Cannot be destroyed by player bullets
- Do not interact with enemy ships
- Spawn at random edges with random movement direction

## Basic Usage

### Single Moving Meteor (Recommended)
```python
from Meteor.meteor_helpers import spawn_moving_meteor

# In a level's spawn_wave function:
spawn_moving_meteor(game, speed=150)
```

The meteor will:
- Spawn at a random edge (top/bottom/left/right)
- Move in a random linear direction (left/right/up/down)
- Bounce off screen boundaries
- Move at the specified speed (pixels per second)

### Custom Position Moving Meteor
```python
from Meteor.meteor_helpers import spawn_meteor

# Spawn at specific position with random direction
spawn_meteor(game, x=800, y=400, image=None)
```

## Implementation Details

### Meteor Class Properties
- `pos`: pygame.Vector2 position
- `vel`: pygame.Vector2 velocity (moves linearly)
- `mass`: 100.0 (very heavy)
- `collision_radius`: Calculated from 150x150 image size
- `is_meteor`: True (flag for identification)
- `health`: float('inf') (cannot be destroyed)
- `speed`: Movement speed in pixels per second
- `bounds`: Screen dimensions for bounce calculations

### Collision Behavior
- **Player vs Meteor**: Player loses 1 health, receives knockback (420 velocity)
- **Bullet vs Meteor**: Bullet is destroyed/removed, meteor unaffected
- **Enemy vs Meteor**: No interaction (enemies can pass through)

### Movement Mechanics
- Linear motion: Meteors move in straight lines (horizontal or vertical)
- Bouncing: Meteors reflect off screen edges
- Random spawn: Meteors spawn at random edges
- Random direction: Each meteor moves in a random cardinal direction

### Rendering
Meteors are drawn:
- After planets but before enemies
- With camera offset applied
- Using the provided sprite (default: images/planeetat/slice2.png, scaled to 150x150)

## Integration in Levels

### Example - Adding meteors to Taso2

```python
# In Tasot/Taso2.py

import pygame
from Meteor.meteor_helpers import spawn_moving_meteor

def spawn_wave_taso2(game, wave_num, ...):
    if wave_num == 1:
        # Add enemies...
        
        # Add one moving meteor
        spawn_moving_meteor(game, speed=150)
        
        return True
    
    if wave_num == 2:
        # More enemies...
        
        # Add a faster meteor
        spawn_moving_meteor(game, speed=200)
        
        return True
    
    return False
```

## Customization

### Adjust Speed
Faster meteors = harder difficulty
```python
spawn_moving_meteor(game, speed=250)  # Fast
spawn_moving_meteor(game, speed=100)  # Slow
```

### Change Movement Behavior
Modify the update() method in Meteor class to:
- Add acceleration/deceleration
- Create curved paths
- Make meteors disappear after time
- Add diagonal movement patterns

## File Structure
```
Meteor/
  __init__.py                      # Package exports
  meteor.py                        # Meteor class with movement logic
  meteor_helpers.py                # Spawning helper functions
  METEOR_USAGE_UPDATED.md          # This documentation
  IMPLEMENTATION_SUMMARY.md        # Implementation reference
```

## Known Limitations
- Only one meteor per spawn call (recommended for gameplay balance)
- Meteors move in cardinal directions (up/down/left/right, not diagonal)
- No meteor-to-meteor collision handling
- Simple bounce physics

## Physics Notes
- Meteors have infinite mass and cannot be moved by collisions
- Collision cooldown prevents repeated damage in single frame
- Camera offset is properly handled for all rendering
- Screen boundaries are based on `game.tausta_leveys` and `game.tausta_korkeus`
