import pygame
import math
import random

class Enemy(pygame.sprite.Sprite):
    def __init__(self, image: pygame.Surface, x: float, y: float):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        # collision-bounce lock: when true, entity is immobilized for collision_bounce_timer seconds
        self.collision_bounce_locked = False
        self.collision_bounce_timer = 0.0
        self.collision_bounce_duration = 3
        self.collision_bounce_target = None
        # physical mass for collision resolution (can be overridden per-type)
        self.mass = 1.0

        # collision bounce active (damped oscillation around a base position)
        self.collision_bounce_active = False
        self.collision_bounce_base = pygame.Vector2(self.rect.center)
        self.collision_bounce_initial_disp = pygame.Vector2(0, 0)
        self.collision_bounce_timer = 0.0
        self.collision_bounce_duration = 0.0
        self.collision_bounce_osc = 0.0
        self.collision_bounce_damping = 0.0

    def update(self, dt_ms: int, player=None, world_rect: pygame.Rect | None = None):
        # If a collision bounce animation is active, update it first.
        if getattr(self, 'collision_bounce_active', False):
            try:
                dt = dt_ms / 1000.0
                self.collision_bounce_timer -= dt
                elapsed = max(0.0, self.collision_bounce_duration - self.collision_bounce_timer)
                T = max(1e-6, float(self.collision_bounce_duration))
                omega = 2.0 * math.pi * (float(self.collision_bounce_osc) / T)
                envelope = math.exp(- (float(self.collision_bounce_damping) * elapsed) / T)
                osc = math.cos(omega * elapsed)
                disp = pygame.Vector2(self.collision_bounce_initial_disp) * (envelope * osc)
                try:
                    self.pos = pygame.Vector2(self.collision_bounce_base) + disp
                    self.rect.center = (int(self.pos.x), int(self.pos.y))
                except Exception:
                    pass
                if self.collision_bounce_timer <= 0.0:
                    self.collision_bounce_active = False
                    self.collision_bounce_timer = 0.0
                    # ensure we end exactly at base
                    try:
                        self.pos = pygame.Vector2(self.collision_bounce_base)
                        self.rect.center = (int(self.pos.x), int(self.pos.y))
                    except Exception:
                        pass
                return
            except Exception:
                pass

        # Handle collision-bounce lock: keep entity immobilized and anchored to target
        if getattr(self, 'collision_bounce_locked', False):
            try:
                dt = dt_ms / 1000.0
                self.collision_bounce_timer -= dt
                if self.collision_bounce_target is not None:
                    # anchor to exact target position
                    try:
                        self.pos = pygame.Vector2(self.collision_bounce_target)
                        self.rect.center = (int(self.pos.x), int(self.pos.y))
                    except Exception:
                        pass
                if self.collision_bounce_timer <= 0.0:
                    self.collision_bounce_locked = False
                    self.collision_bounce_timer = 0.0
                    self.collision_bounce_target = None
                return
            except Exception:
                return

    def start_collision_bounce(self, base_pos, initial_disp, duration=3, oscillations=2.0, damping=2.2):
        """Start a damped oscillation bounce around `base_pos`.

        - `base_pos`: center position (tuple/vector) where oscillation settles.
        - `initial_disp`: vector from base to the entity's current position (so motion starts from rest).
        - `duration`: seconds total for the bounce animation.
        - `oscillations`: number of full oscillations (or half-oscillations scaler used previously).
        - `damping`: exponential damping factor.
        """
        try:
            self.collision_bounce_active = True
            self.collision_bounce_base = pygame.Vector2(base_pos)
            self.collision_bounce_initial_disp = pygame.Vector2(initial_disp)
            self.collision_bounce_duration = float(max(0.01, duration))
            self.collision_bounce_timer = float(self.collision_bounce_duration)
            self.collision_bounce_osc = float(oscillations)
            self.collision_bounce_damping = float(damping)
        except Exception:
            pass

    def _update_display_angle(self, dt_ms: int, target: float, max_deg_per_sec: float = 720.0):
        """Smoothly rotate a `display_angle` attribute toward `target`.

        - `target` is in radians (math.atan2 convention used in codebase).
        - `max_deg_per_sec` limits rotation speed to avoid snaps.
        """
        try:
            curr = float(getattr(self, 'display_angle', 0.0))
        except Exception:
            curr = 0.0
        # normalize difference to [-pi, pi]
        diff = (target - curr + math.pi) % (2.0 * math.pi) - math.pi
        max_change = math.radians(max_deg_per_sec) * (dt_ms / 1000.0)
        if abs(diff) <= max_change:
            new = target
        else:
            new = curr + (max_change if diff > 0 else -max_change)
        self.display_angle = new

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        try:
            ang = float(getattr(self, 'display_angle', 0.0))
        except Exception:
            ang = 0.0
        # convert to degrees; pygame rotates counter-clockwise, so negate angle
        deg = -math.degrees(ang)
        try:
            if abs(deg) > 0.0001:
                surf = pygame.transform.rotozoom(self.image, deg, 1.0)
                r = surf.get_rect(center=(self.rect.centerx - camera_x, self.rect.centery - camera_y))
                screen.blit(surf, r.topleft)
            else:
                screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))
        except Exception:
            screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))


class StraightEnemy(Enemy):
    """Lentää suoraan valittuun suuntaan"""
    def __init__(self, image, x, y, speed=220):
        super().__init__(image, x, y)
        angle = random.uniform(0, math.tau)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)

        if world_rect is not None:
            if self.rect.left <= world_rect.left or self.rect.right >= world_rect.right:
                self.vx *= -1
            if self.rect.top <= world_rect.top or self.rect.bottom >= world_rect.bottom:
                self.vy *= -1
            self.rect.clamp_ip(world_rect)


class CircleEnemy(Enemy):
    """Kiertää pisteen ympäri."""
    def __init__(self, image, center_x, center_y, radius=160, angular_speed=2.0):
        super().__init__(image, center_x + radius, center_y)
        self.center = pygame.Vector2(center_x, center_y)
        self.radius = radius
        self.angular_speed = angular_speed
        self.angle = random.uniform(0, math.tau)

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0
        self.angle += self.angular_speed * dt

        x = self.center.x + math.cos(self.angle) * self.radius
        y = self.center.y + math.sin(self.angle) * self.radius
        self.rect.center = (int(x), int(y))


class DownEnemy(Enemy):
    """Lentää ylhäältä alas ja takaisin."""
    def __init__(self, image, x, y, speed=200):
        super().__init__(image, x, y)
        self.speed = speed
        self.vy = speed  # Liikkuu alas

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0
        self.rect.y += int(self.vy * dt)

        if world_rect is not None:
            if self.rect.top <= world_rect.top:
                self.rect.top = world_rect.top
                self.vy = self.speed  # Käänny alas
            elif self.rect.bottom >= world_rect.bottom:
                self.rect.bottom = world_rect.bottom
                self.vy = -self.speed  # Käänny ylös
            self.rect.clamp_ip(world_rect)


class UpEnemy(Enemy):
    """Lentää alhaalta ylös ja takaisin."""
    def __init__(self, image, x, y, speed=200):
        super().__init__(image, x, y)
        self.speed = speed
        self.vy = -speed  # Liikkuu ylös (negatiivinen)

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0
        self.rect.y += int(self.vy * dt)

        if world_rect is not None:
            if self.rect.top <= world_rect.top:
                self.rect.top = world_rect.top
                self.vy = self.speed  # Käänny alas
            elif self.rect.bottom >= world_rect.bottom:
                self.rect.bottom = world_rect.bottom
                self.vy = -self.speed  # Käänny ylös
            self.rect.clamp_ip(world_rect)
