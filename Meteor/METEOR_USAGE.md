"""Meteor System Usage Guide for RocketGame

The meteor system provides immobile obstacles that:
- Damage the player by 1 health on collision
- Cannot be destroyed by player bullets
- Do not interact with enemy ships
- Apply knockback to the player on collision

## Basic Usage

### Single Meteor
```python
from Meteor.meteor_helpers import spawn_meteor

# In a level's spawn_wave function:
spawn_meteor(game, x=400, y=300)
```

### Multiple Meteors - Patterns

1. **Line Formation** (diagonal/straight lines)
```python
from Meteor.meteor_helpers import spawn_meteors_line

spawn_meteors_line(
    game,
    start_x=100, start_y=100,
    end_x=800, end_y=400,
    count=5
)
```

2. **Grid Formation** (rectangular grid)
```python
from Meteor.meteor_helpers import spawn_meteors_grid

spawn_meteors_grid(
    game,
    start_x=200, start_y=200,
    spacing=150,
    cols=3,
    rows=2
)
```

3. **Circular Formation** (around a center point)
```python
from Meteor.meteor_helpers import spawn_meteors_circle

spawn_meteors_circle(
    game,
    center_x=800, center_y=400,
    radius=200,
    count=8
)
```

## Implementation Details

### Meteor Class Properties
- `pos`: pygame.Vector2 position
- `vel`: Always (0, 0) - meteors don't move
- `mass`: 100.0 (very heavy)
- `collision_radius`: Calculated from image size
- `is_meteor`: True (flag for identification)
- `health`: float('inf') (cannot be destroyed)

### Collision Behavior
- **Player vs Meteor**: Player loses 1 health, receives knockback (420 velocity)
- **Bullet vs Meteor**: Bullet is destroyed/removed, meteor unaffected
- **Enemy vs Meteor**: No interaction (enemies can pass through or hit meteors without effect)

### Rendering
Meteors are drawn:
- After planets but before enemies
- With camera offset applied
- Using the provided sprite (default: images/planeetat/slice2.png, scaled to 100x100)

## Integration in Levels

### Example - Adding meteors to Taso2

```python
# In Tasot/Taso2.py

import pygame
from Meteor.meteor_helpers import spawn_meteor, spawn_meteors_line, spawn_meteors_grid

def spawn_wave_taso2(game, wave_num, ...):
    if wave_num == 1:
        # Add enemies...
        
        # Add meteors
        spawn_meteors_grid(
            game,
            start_x=300, start_y=200,
            spacing=200,
            cols=2,
            rows=2
        )
        return True
    
    return False
```

## Customization

### Custom Meteor Image
```python
import pygame

custom_image = pygame.image.load("path/to/image.png")
custom_image = pygame.transform.scale(custom_image, (100, 100))

spawn_meteor(game, x=400, y=300, image=custom_image)
```

### Dynamic Meteor Spawning
Meteors can be spawned anytime during gameplay (not just in spawn_wave):
```python
# Directly create and add
from Meteor.meteor import Meteor

meteor = Meteor(x=400, y=300)
game.meteors.append(meteor)
```

## File Structure
```
Meteor/
  __init__.py              # Package exports
  meteor.py                # Meteor class definition
  meteor_helpers.py        # Spawning helper functions
  METEOR_USAGE.md         # This documentation
```

## Known Limitations
- Meteors are static - they don't move or rotate
- No special visual feedback when meteor is hit by bullets
- Meteors don't have hitpoints/health (they're indestructible)
- No meteor-to-meteor collision handling needed
