"""Meteor classes for RocketGame.

Meteors are moving obstacles that:
- Move linearly across the screen
- Damage the player on collision
- Break into smaller pieces when shot
- Do not interact with enemy ships

Three meteor sizes:
- MainMeteorite (100%): 300x300, breaks into 4x50% Meteors
- Meteor (50%): ~150x150, breaks into 2x25% SmallMeteorites
- SmallMeteorite (25%): ~75x75, does not break
"""

import pygame
import os
import math


class Meteor(pygame.sprite.Sprite):
    """Medium meteor obstacle (50% size) that damages the player on collision.
    
    Properties:
        - Size: ~150x150 pixels (50% scale)
        - Damages player 1 health on collision
        - Breaks into 2x25% SmallMeteorites when shot
        - Moves linearly
    """
    
    def __init__(self, x, y, image=None, bounds=None, speed=80, velocity=None, size_scale=0.5):
        """Initialize a medium (50%) meteor at the given position.
        
        Args:
            x: X position in pixels
            y: Y position in pixels
            image: Pygame surface image (optional, loads Meteor_05 if not provided)
            bounds: Tuple (width, height) of movement area
            speed: Movement speed in pixels per second (default 80)
            velocity: Optional explicit velocity vector (pygame.Vector2 or tuple)
            size_scale: Visual size multiplier (0.5 = 50% size)
        """
        super().__init__()
        
        # Load image if not provided
        if image is None:
            try:
                base_path = os.path.dirname(os.path.dirname(__file__))
                meteor_path = os.path.join(base_path, 'images', 'Space-Shooter_objects', 'PNG', 'Meteors', 'Meteor_05.png')
                image = pygame.image.load(meteor_path).convert_alpha()
            except Exception as e:
                print(f"Warning: Could not load Meteor_05.png: {e}")
                # Fallback: create a simple surface
                image = pygame.Surface((150, 150), pygame.SRCALPHA)
                pygame.draw.circle(image, (100, 180, 200), (75, 75), 70)

        if size_scale != 1.0:
            w = max(24, int(image.get_width() * float(size_scale)))
            h = max(24, int(image.get_height() * float(size_scale)))
            image = pygame.transform.smoothscale(image, (w, h))
        
        self.base_image = image
        self.image = self.base_image
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        
        # Physics properties
        self.pos = pygame.Vector2(x, y)
        self.bounds = bounds or (1600, 800)
        self.speed = speed

        if velocity is None:
            self.vel = pygame.Vector2(self.speed, 0)
        else:
            self.vel = pygame.Vector2(velocity)

        self.rotation_angle = 0.0
        self.rotation_offset = 45.0
        self._update_rotation_from_velocity()
        
        self.mass = 100.0  # Very heavy - won't move during collisions

        # Trail points in world coordinates for a small comet-like tail.
        self.trail_positions = []
        self._trail_timer = 0.0
        self._trail_interval = 0.035
        self._trail_max_points = 11
        
        # Collision radius for spatial collision detection
        self.collision_radius = max(
            8,
            int(max(self.rect.width, self.rect.height) * 0.5)
        )
        
        # Meteor is not an enemy or a destructible object
        self.is_meteor = True
        self.meteor_type = "medium"  # 50% size meteor
        self.health = 1  # 1 health - breaks on one bullet hit
        self.max_health = 1
        self.damage_to_player = 1  # Damages player 1 health
        self.dead = False
        self._entered_play_area = False

    def _update_rotation_from_velocity(self):
        """Rotate sprite so its nose points toward movement direction."""
        if self.vel.length_squared() == 0:
            return

        # Screen Y-axis grows downward, so angle sign is inverted.
        self.rotation_angle = -math.degrees(math.atan2(self.vel.y, self.vel.x)) + self.rotation_offset
        old_center = self.rect.center
        self.image = pygame.transform.rotate(self.base_image, self.rotation_angle)
        self.rect = self.image.get_rect(center=old_center)
    
    def update(self, dt):
        """Update meteor position and despawn after it crosses the play area.
        
        Args:
            dt: Delta time in milliseconds
        """
        # Convert dt from milliseconds to seconds
        dt_seconds = dt / 1000.0
        
        # Move meteor
        self.pos += self.vel * dt_seconds

        # Store sampled previous positions for a fading tail.
        self._trail_timer += dt_seconds
        while self._trail_timer >= self._trail_interval:
            self._trail_timer -= self._trail_interval
            self.trail_positions.append(self.pos.copy())
            if len(self.trail_positions) > self._trail_max_points:
                self.trail_positions.pop(0)
        
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
    
    def get_fragments(self):
        """Break this meteor into 2x25% SmallMeteorites.
        
        Returns:
            List of SmallMeteorite instances
        """
        fragments = []
        for i in range(2):
            offset_angle = (i * 180 + 45) * math.pi / 180.0
            fragment_vel = pygame.Vector2(
                math.cos(offset_angle) * self.speed * 0.8,
                math.sin(offset_angle) * self.speed * 0.8
            )
            fragment = SmallMeteorite(
                self.pos.x,
                self.pos.y,
                bounds=self.bounds,
                speed=self.speed * 0.8,
                velocity=fragment_vel
            )
            fragments.append(fragment)
        return fragments
    
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

        if self.trail_positions:
            trail_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            total = len(self.trail_positions)
            for i, trail_pos in enumerate(self.trail_positions):
                t = (i + 1) / total
                alpha = int(22 + 95 * t)
                radius = max(2, int(2 + 7 * t))
                sx = int(trail_pos.x - camera_x)
                sy = int(trail_pos.y - camera_y)
                pygame.draw.circle(trail_surface, (255, 210, 130, alpha), (sx, sy), radius)
            surface.blit(trail_surface, (0, 0))

        surface.blit(self.image, draw_pos)


class MainMeteorite(pygame.sprite.Sprite):
    """Large meteor obstacle (100% size) that damages the player on collision.
    
    Properties:
        - Size: ~300x300 pixels (100% scale)
        - Damages player 2 health on collision
        - Breaks into 4x50% Meteors when shot
        - Moves linearly
    """
    
    def __init__(self, x, y, image=None, bounds=None, speed=80, velocity=None):
        """Initialize a large (100%) meteor at the given position.
        
        Args:
            x: X position in pixels
            y: Y position in pixels
            image: Pygame surface image (optional, loads Meteor_01 if not provided)
            bounds: Tuple (width, height) of movement area
            speed: Movement speed in pixels per second (default 80)
            velocity: Optional explicit velocity vector (pygame.Vector2 or tuple)
        """
        super().__init__()
        
        # Load image if not provided
        if image is None:
            try:
                base_path = os.path.dirname(os.path.dirname(__file__))
                meteor_path = os.path.join(base_path, 'images', 'Space-Shooter_objects', 'PNG', 'Meteors', 'Meteor_01.png')
                image = pygame.image.load(meteor_path).convert_alpha()
            except Exception as e:
                print(f"Warning: Could not load Meteor_01.png: {e}")
                # Fallback: create a simple surface
                image = pygame.Surface((300, 300), pygame.SRCALPHA)
                pygame.draw.circle(image, (200, 120, 60), (150, 150), 140)

        self.base_image = image
        self.image = self.base_image
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        
        # Physics properties
        self.pos = pygame.Vector2(x, y)
        self.bounds = bounds or (1600, 800)
        self.speed = speed

        if velocity is None:
            self.vel = pygame.Vector2(self.speed, 0)
        else:
            self.vel = pygame.Vector2(velocity)

        self.rotation_angle = 0.0
        self.rotation_offset = 45.0
        self._update_rotation_from_velocity()
        
        self.mass = 200.0  # Very heavy - won't move during collisions

        # Trail points in world coordinates for a small comet-like tail.
        self.trail_positions = []
        self._trail_timer = 0.0
        self._trail_interval = 0.035
        self._trail_max_points = 11
        
        # Collision radius for spatial collision detection
        self.collision_radius = max(
            8,
            int(max(self.rect.width, self.rect.height) * 0.5)
        )
        
        # Meteor properties
        self.is_meteor = True
        self.meteor_type = "main"  # 100% size meteor
        self.health = 1  # 1 health - breaks on one bullet hit
        self.max_health = 1
        self.damage_to_player = 2  # Damages player 2 health
        self.dead = False
        self._entered_play_area = False

    def _update_rotation_from_velocity(self):
        """Rotate sprite so its nose points toward movement direction."""
        if self.vel.length_squared() == 0:
            return
        self.rotation_angle = -math.degrees(math.atan2(self.vel.y, self.vel.x)) + self.rotation_offset
        old_center = self.rect.center
        self.image = pygame.transform.rotate(self.base_image, self.rotation_angle)
        self.rect = self.image.get_rect(center=old_center)
    
    def update(self, dt):
        """Update meteor position and despawn after it crosses the play area.
        
        Args:
            dt: Delta time in milliseconds
        """
        dt_seconds = dt / 1000.0
        self.pos += self.vel * dt_seconds

        self._trail_timer += dt_seconds
        while self._trail_timer >= self._trail_interval:
            self._trail_timer -= self._trail_interval
            self.trail_positions.append(self.pos.copy())
            if len(self.trail_positions) > self._trail_max_points:
                self.trail_positions.pop(0)
        
        width, height = self.bounds
        play_rect = pygame.Rect(0, 0, width, height)
        if self.rect.colliderect(play_rect):
            self._entered_play_area = True

        if self._entered_play_area and not self.rect.colliderect(play_rect):
            self.dead = True
        
        self.rect.center = (int(self.pos.x), int(self.pos.y))
    
    def get_fragments(self):
        """Break this meteor into 4x50% Meteors.
        
        Returns:
            List of Meteor instances
        """
        fragments = []
        for i in range(4):
            offset_angle = (i * 90) * math.pi / 180.0
            fragment_vel = pygame.Vector2(
                math.cos(offset_angle) * self.speed * 1.2,
                math.sin(offset_angle) * self.speed * 1.2
            )
            fragment = Meteor(
                self.pos.x,
                self.pos.y,
                bounds=self.bounds,
                speed=self.speed * 1.2,
                velocity=fragment_vel,
                size_scale=0.5
            )
            fragments.append(fragment)
        return fragments
    
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

        if self.trail_positions:
            trail_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            total = len(self.trail_positions)
            for i, trail_pos in enumerate(self.trail_positions):
                t = (i + 1) / total
                alpha = int(22 + 95 * t)
                radius = max(2, int(2 + 7 * t))
                sx = int(trail_pos.x - camera_x)
                sy = int(trail_pos.y - camera_y)
                pygame.draw.circle(trail_surface, (255, 210, 130, alpha), (sx, sy), radius)
            surface.blit(trail_surface, (0, 0))

        surface.blit(self.image, draw_pos)


class SmallMeteorite(pygame.sprite.Sprite):
    """Small meteor obstacle (25% size) that damages the player on collision.
    
    Properties:
        - Size: ~75x75 pixels (25% scale)
        - Damages player 1 health on collision
        - Does NOT break into smaller pieces
        - Moves linearly
    """
    
    def __init__(self, x, y, image=None, bounds=None, speed=80, velocity=None):
        """Initialize a small (25%) meteor at the given position.
        
        Args:
            x: X position in pixels
            y: Y position in pixels
            image: Pygame surface image (optional, loads Meteor_10 if not provided)
            bounds: Tuple (width, height) of movement area
            speed: Movement speed in pixels per second (default 80)
            velocity: Optional explicit velocity vector (pygame.Vector2 or tuple)
        """
        super().__init__()
        
        # Load image if not provided
        if image is None:
            try:
                base_path = os.path.dirname(os.path.dirname(__file__))
                meteor_path = os.path.join(base_path, 'images', 'Space-Shooter_objects', 'PNG', 'Meteors', 'Meteor_10.png')
                image = pygame.image.load(meteor_path).convert_alpha()
            except Exception as e:
                print(f"Warning: Could not load Meteor_10.png: {e}")
                # Fallback: create a simple surface
                image = pygame.Surface((75, 75), pygame.SRCALPHA)
                pygame.draw.circle(image, (200, 150, 100), (37, 37), 35)

        self.base_image = image
        self.image = self.base_image
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        
        # Physics properties
        self.pos = pygame.Vector2(x, y)
        self.bounds = bounds or (1600, 800)
        self.speed = speed

        if velocity is None:
            self.vel = pygame.Vector2(self.speed, 0)
        else:
            self.vel = pygame.Vector2(velocity)

        self.rotation_angle = 0.0
        self.rotation_offset = 45.0
        self._update_rotation_from_velocity()
        
        self.mass = 50.0

        # Trail points in world coordinates
        self.trail_positions = []
        self._trail_timer = 0.0
        self._trail_interval = 0.05
        self._trail_max_points = 8
        
        # Collision radius for spatial collision detection
        self.collision_radius = max(
            8,
            int(max(self.rect.width, self.rect.height) * 0.5)
        )
        
        # Meteor properties
        self.is_meteor = True
        self.meteor_type = "small"  # 25% size meteor
        self.health = 1  # 1 health - disappears on bullet hit
        self.max_health = 1
        self.damage_to_player = 1  # Damages player 1 health
        self.dead = False
        self._entered_play_area = False

    def _update_rotation_from_velocity(self):
        """Rotate sprite so its nose points toward movement direction."""
        if self.vel.length_squared() == 0:
            return
        self.rotation_angle = -math.degrees(math.atan2(self.vel.y, self.vel.x)) + self.rotation_offset
        old_center = self.rect.center
        self.image = pygame.transform.rotate(self.base_image, self.rotation_angle)
        self.rect = self.image.get_rect(center=old_center)
    
    def update(self, dt):
        """Update meteor position and despawn after it crosses the play area.
        
        Args:
            dt: Delta time in milliseconds
        """
        dt_seconds = dt / 1000.0
        self.pos += self.vel * dt_seconds

        self._trail_timer += dt_seconds
        while self._trail_timer >= self._trail_interval:
            self._trail_timer -= self._trail_interval
            self.trail_positions.append(self.pos.copy())
            if len(self.trail_positions) > self._trail_max_points:
                self.trail_positions.pop(0)
        
        width, height = self.bounds
        play_rect = pygame.Rect(0, 0, width, height)
        if self.rect.colliderect(play_rect):
            self._entered_play_area = True

        if self._entered_play_area and not self.rect.colliderect(play_rect):
            self.dead = True
        
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

        if self.trail_positions:
            trail_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            total = len(self.trail_positions)
            for i, trail_pos in enumerate(self.trail_positions):
                t = (i + 1) / total
                alpha = int(15 + 70 * t)
                radius = max(1, int(1 + 5 * t))
                sx = int(trail_pos.x - camera_x)
                sy = int(trail_pos.y - camera_y)
                pygame.draw.circle(trail_surface, (255, 200, 100, alpha), (sx, sy), radius)
            surface.blit(trail_surface, (0, 0))

        surface.blit(self.image, draw_pos)

