"""Meteor class for RocketGame.

Meteors are moving obstacles that:
- Move linearly across the screen
- Damage the player on collision (1 health)
- Cannot be destroyed by player bullets
- Do not interact with enemy ships
"""

import pygame
import os


class Meteor(pygame.sprite.Sprite):
    """Moving meteor obstacle that damages the player on collision.
    
    Properties:
        - Moves linearly in random directions (up/down/left/right)
        - Player loses 1 health on collision
        - Bullets pass through meteors without effect
        - Enemies are not affected by meteors
    """
    
    def __init__(self, x, y, image=None, bounds=None, speed=80, velocity=None):
        """Initialize a moving meteor at the given position.
        
        Args:
            x: X position in pixels
            y: Y position in pixels
            image: Pygame surface image (optional, loads default if not provided)
            bounds: Tuple (width, height) of movement area
            speed: Movement speed in pixels per second (default 80)
            velocity: Optional explicit velocity vector (pygame.Vector2 or tuple)
        """
        super().__init__()
        
        # Load image if not provided
        if image is None:
            try:
                base_path = os.path.dirname(os.path.dirname(__file__))
                meteor_path = os.path.join(base_path, 'images', 'planeetat', 'slice2.png')
                image = pygame.image.load(meteor_path).convert_alpha()
                # Scale to larger size (220x220)
                image = pygame.transform.scale(image, (220, 220))
            except Exception as e:
                print(f"Warning: Could not load meteor image: {e}")
                # Fallback: create a simple surface
                image = pygame.Surface((220, 220), pygame.SRCALPHA)
                pygame.draw.circle(image, (180, 100, 50), (110, 110), 105)
        
        self.image = image
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        
        # Physics properties
        self.pos = pygame.Vector2(x, y)
        self.bounds = bounds or (1600, 800)
        self.speed = speed

        if velocity is None:
            self.vel = pygame.Vector2(self.speed, 0)
        else:
            self.vel = pygame.Vector2(velocity)
        
        self.mass = 100.0  # Very heavy - won't move during collisions
        
        # Collision radius for spatial collision detection
        self.collision_radius = max(
            8,
            int(max(self.rect.width, self.rect.height) * 0.5)
        )
        
        # Meteor is not an enemy or a destructible object
        self.is_meteor = True
        self.health = float('inf')  # Meteors cannot be destroyed
        self.dead = False
        self._entered_play_area = False
    
    def update(self, dt):
        """Update meteor position and despawn after it crosses the play area.
        
        Args:
            dt: Delta time in milliseconds
        """
        # Convert dt from milliseconds to seconds
        dt_seconds = dt / 1000.0
        
        # Move meteor
        self.pos += self.vel * dt_seconds
        
        # Track whether meteor has entered visible play area at least once.
        width, height = self.bounds
        play_rect = pygame.Rect(0, 0, width, height)
        if self.rect.colliderect(play_rect):
            self._entered_play_area = True

        # Despawn after meteor has crossed screen and moved out again.
        if self._entered_play_area and not self.rect.colliderect(play_rect):
            self.dead = True
        
        # Update rect position
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

