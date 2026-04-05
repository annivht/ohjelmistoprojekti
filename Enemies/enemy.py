



from Enemies.EnemyHelpers import EnemyBullet
import pygame
import math
import random
from Physics.core import RigidBody
from Physics.animation import DampedOscillator
from Enemies.sprite_config import get_sprite_config, apply_angle_constraints

# Collision configuration:
# `DEFAULT_COLLISION_RADIUS_FACTOR` is multiplied by the sprite's max dimension
# (width/height) to get a sane default collision radius. Adjust to tune how
# large the circular collision area is relative to the visible sprite.
# `MIN_COLLISION_RADIUS` enforces a sensible lower bound in pixels.
DEFAULT_COLLISION_RADIUS_FACTOR = 0.45
MIN_COLLISION_RADIUS = 8

class Enemy(RigidBody, pygame.sprite.Sprite):
    """
    Base enemy class combining pygame.sprite.Sprite with Physics.RigidBody.
    
    Provides physics simulation, collision detection, and animations.
    Handles damped oscillations for collision bounces.
    
    Attributes:
        image/rect: pygame sprite display
        hp: health points
        pos/vel: physics position and velocity (from RigidBody)
        mass: physics mass (from RigidBody)
        collision_radius: collision detection radius
        oscillator: DampedOscillator for collision bounces
    """
    
    def __init__(self, image: pygame.Surface, x: float, y: float, hp: int = 1):
        """
        Initialize enemy with physics and sprite attributes.
        
        Args:
            image: pygame.Surface sprite image
            x: initial X position
            y: initial Y position
            hp: health points (default 1)
        """
        RigidBody.__init__(self, x=x, y=y, mass=1.0)
        pygame.sprite.Sprite.__init__(self)
        
        self.image = image
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.hp = hp
        
        # Collision configuration
        try:
            self.collision_radius = max(MIN_COLLISION_RADIUS, int(max(self.rect.width, self.rect.height) * DEFAULT_COLLISION_RADIUS_FACTOR))
        except Exception:
            self.collision_radius = MIN_COLLISION_RADIUS
        
        # Collision bounce animation (replaces old collision_bounce_* logic)
        self.oscillator = None
        
        # Display angle for rotation (radians)
        self.display_angle = 0.0
        
        # Sprite-specific rotation configuration
        self.rotation_config = {
            'rotation_enabled': True,
            'rotation_offset': 0.0,
            'min_angle': None,
            'max_angle': None,
        }
        # Set specific rotation config based on sprite index or type if needed
        self.shots = {
            "shot": [self._create_debug_bullet()]
        }

    def update(self, dt_ms: int, player=None, world_rect: pygame.Rect | None = None):
        """
        Update enemy state: physics, animations, oscillations.
        
        Args:
            dt_ms: delta time in milliseconds
            player: player reference (for AI targeting)
            world_rect: world boundaries (for movement constraints)
        """
        dt = dt_ms / 1000.0
        
        # Update damped oscillator if active (collision bounce animation)
        if self.oscillator is not None and self.oscillator.is_active():
            # Oscillator modifies position during collision bounce
            self.pos = self.oscillator.update(dt)
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            return  # Skip regular physics update during bounce
        else:
            self.oscillator = None
        
        # Regular physics update: apply forces, update velocity and position
        RigidBody.update(self, dt)
        
        # Sync rect with physics position
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    
    def start_collision_bounce(self, base_pos, initial_disp, duration=2.0, oscillations=2.0, damping=2.2):
        """
        Start damped oscillation animation (collision bounce).
        
        Creates a DampedOscillator that will be applied in next update() calls.
        
        Args:
            base_pos: position to oscillate around
            initial_disp: initial displacement from base
            duration: animation duration in seconds
            oscillations: number of oscillation cycles
            damping: exponential decay rate
        """
        self.oscillator = DampedOscillator(
            base_pos=base_pos,
            initial_displacement=initial_disp,
            duration=duration,
            oscillations=oscillations,
            damping=damping
        )

    def _update_display_angle(self, dt_ms: int, target: float, max_deg_per_sec: float = 720.0):
        """
        Smooth rotation toward target angle, respecting sprite rotation config.
        
        Args:
            dt_ms: delta time in milliseconds
            target: target angle in radians
            max_deg_per_sec: maximum rotation speed (degrees/second)
        """
        # Check if rotation is enabled for this sprite
        if not self.rotation_config.get('rotation_enabled', True):
            return  # Don't update angle if rotation is disabled
        
        # Apply rotation offset (e.g., for sprites with non-standard orientation)
        offset = self.rotation_config.get('rotation_offset', 0.0)
        target = target + offset
        
        try:
            curr = float(getattr(self, 'display_angle', 0.0))
        except Exception:
            curr = 0.0
        
        # Normalize angle difference to [-pi, pi]
        diff = (target - curr + math.pi) % (2.0 * math.pi) - math.pi
        max_change = math.radians(max_deg_per_sec) * (dt_ms / 1000.0)
        
        if abs(diff) <= max_change:
            new = target
        else:
            new = curr + (max_change if diff > 0 else -max_change)
        
        # Apply min/max angle constraints
        new = apply_angle_constraints(new, self.rotation_config)
        
        self.display_angle = new
    
    def set_sprite_config(self, sprite_index):
        """Configure rotation settings based on sprite index."""
        self.rotation_config = get_sprite_config(sprite_index)

    def maybe_shoot(self, dt_ms: int, containers: dict | None = None, player=None):
    # Ei ammuta jos ei sallittu
        if not getattr(self, "can_shoot", False):
            return

        if player is None or containers is None:
            return

        # Cooldown
        if not hasattr(self, "shoot_timer"):
            self.shoot_timer = 0
            self.shoot_interval = 2000
            self.shoot_range = 300

        self.shoot_timer -= dt_ms
        if self.shoot_timer > 0:
            return

        # Etäisyys pelaajaan
        dx = player.pos.x - self.pos.x
        dy = player.pos.y - self.pos.y
        dist = math.hypot(dx, dy)

        if dist <= 0 or dist > self.shoot_range:
            return

        # Reset cooldown
        self.shoot_timer = self.shoot_interval

        # Tähtäys
        angle = math.atan2(dy, dx)
        self._update_display_angle(dt_ms, angle)

        # Luo bullet
        bullet = EnemyBullet.from_enemy(self)

        if not bullet:
            return

        direction = pygame.Vector2(dx, dy)

        if direction.length_squared() == 0:
            return

        direction = direction.normalize()
        bullet.vel = direction * 420

        # visuaalinen
        bullet.image = pygame.Surface((6, 6))
        bullet.image.fill((255, 0, 0))
        bullet.rect = bullet.image.get_rect(center=self.rect.center)

        # tallenna aktiivinen ammus
        self.active_bullet = bullet

        # lisää peliin
        containers["enemy_bullets"].append(bullet)

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        try:
            ang = float(getattr(self, 'display_angle', 0.0))
        except Exception:
            ang = 0.0
        # Muunna radiaanit asteiksi; pygame pyörittää vastapäivään, joten negatoi kulma
        deg = -math.degrees(ang)
        try:
            if abs(deg) > 0.0001:
                # Rotoi ja skaalaa 1.0-kertoimella (vain rotointi käytössä)
                surf = pygame.transform.rotozoom(self.image, deg, 1.0)
                r = surf.get_rect(center=(self.rect.centerx - camera_x, self.rect.centery - camera_y))
                screen.blit(surf, r.topleft)
            else:
                # Ei merkittävää rotaatiota -> piirrä kuva siten, että
                # kuva on keskitetty `self.rect.center` koordinaattiin.
                img_r = self.image.get_rect(center=(self.rect.centerx - camera_x,
                                                    self.rect.centery - camera_y))
                screen.blit(self.image, img_r.topleft)
        except Exception:
            # Viimeinen varmistus: fallback vanhaan tapaan
            screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))
    
    def _create_debug_bullet(self):
        surf = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 0, 0), (4, 4), 4)
        return surf