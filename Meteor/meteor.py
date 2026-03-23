"""Meteor class for RocketGame.

Meteors are immobile obstacles that:
- Damage the player on collision (1 health)
- Cannot be destroyed by player bullets
- Do not interact with enemy ships
"""

import pygame
import os


class Meteor(pygame.sprite.Sprite):
    """Static meteor obstacle that damages the player on collision.
    
    Properties:
        - Immobile (no velocity or movement)
        - Player loses 1 health on collision
        - Bullets pass through meteors without effect
        - Enemies are not affected by meteors
    """
    
    def __init__(self, x, y, image=None):
        """Initialize a meteor at the given position.
        
        Args:
            x: X position in pixels
            y: Y position in pixels
            image: Pygame surface image (optional, loads default if not provided)
        """
        super().__init__()
        
        # Load image if not provided
        if image is None:
            try:
                base_path = os.path.dirname(os.path.dirname(__file__))
                meteor_path = os.path.join(base_path, 'images', 'planeetat', 'slice2.png')
                image = pygame.image.load(meteor_path).convert_alpha()
                # Scale to reasonable size (100x100)
                image = pygame.transform.scale(image, (100, 100))
            except Exception as e:
                print(f"Warning: Could not load meteor image: {e}")
                # Fallback: create a simple surface
                image = pygame.Surface((100, 100), pygame.SRCALPHA)
                pygame.draw.circle(image, (180, 100, 50), (50, 50), 45)
        
        self.image = image
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        
        # Physics properties for collision handling
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)  # Meteors don't move
        self.mass = 100.0  # Very heavy - won't move during collisions
        
        # Collision radius for spatial collision detection
        self.collision_radius = max(
            8,
            int(max(self.rect.width, self.rect.height) * 0.5)
        )
        
        # Meteor is not an enemy or a destructible object
        self.is_meteor = True
        self.health = float('inf')  # Meteors cannot be destroyed
    
    def update(self, dt):
        """Update meteor state.
        
        Meteors are static, so this just ensures position stays synced.
        
        Args:
            dt: Delta time in milliseconds
        """
        # Ensure position stays synchronized
        if hasattr(self, 'pos'):
            self.rect.center = (int(self.pos.x), int(self.pos.y))
    
    def draw(self, surface, camera_x, camera_y):
        """Draw the meteor on the given surface, accounting for camera offset.
        
        Args:
            surface: Pygame display surface
            camera_x: Camera X offset in pixels
            camera_y: Camera Y offset in pixels
        """
        draw_pos = (
            int(self.rect.x - camera_x),
            int(self.rect.y - camera_y)
        )
        surface.blit(self.image, draw_pos)
