"""
Module: EnemyAI.py - All enemy types and movement AI behaviors
Dependencies: pygame, math, random, enemy (class Enemy)
Provides: 
  - StraightEnemy: Flies in a straight direction (figure-8 and magnet support)
  - CircleEnemy: Moves in circular paths with behavioral states
  - DownEnemy: Spawns at top, moves downward, bounces at boundaries
  - UpEnemy: Spawns at bottom, moves upward, bounces at boundaries
  - ZigZagEnemy: Moves in zigzag pattern (sine wave horizontally)
  - ChaseEnemy: Follows the player with wall avoidance
Used by: RocketGame.py
"""

import math
import random
import pygame
from typing import Optional
from Enemies.enemy import Enemy
from Physics.animation import DampedOscillator


class StraightEnemy(Enemy):
    """Lentää suoraan valittuun suuntaan"""
    def __init__(self, image, x, y, speed=220, path_type: str = 'random', pattern_params: dict | None = None, sprite_index: int | None = None):
        super().__init__(image, x, y)
        if sprite_index is not None:
            self.set_sprite_config(sprite_index)
        angle = random.uniform(0, math.tau)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.speed = speed

        # use float position for smooth movement
        self.pos = pygame.Vector2(self.rect.center)

        # velocity vector for physics (px / s)
        self.vel = pygame.Vector2(self.vx, self.vy)

        # boost/turbo flags (can be assigned externally)
        self.turbo = False
        self.turbo_multiplier = 1.5

        # exhaust/shot lists can be attached externally (e.g. RocketGame)
        # self.exhaust_turbo = []
        # self.exhaust_normal = []
        # self.shots = []

        # simple exhaust animation state
        self.exhaust_index = 0
        self._exhaust_timer = 0
        self.exhaust_speed_ms = 80
        # random motion nudges
        self.random_motion = True
        self._change_timer = 0
        self._change_interval_min = 400
        self._change_interval_max = 1200
        self._change_interval = random.randint(self._change_interval_min, self._change_interval_max)
        # simple bounce settings: when colliding with world bounds, perform a short bounce
        self.simple_bounce = True
        self.bouncing = False
        self.bounce_duration = 2.0  # seconds (longer, calmer bounce)
        self.bounce_timer = 0.0
        self.bounce_initial_vel = pygame.Vector2(0, 0)
        # Bounce tuning: strength scales initial reverse impulse,
        # oscillations = how many half-oscillations over duration,
        # damping controls how quickly oscillation amplitude decays.
        self.boost_strength = 1.8
        self.bounce_oscillations = 2.0
        self.bounce_damping = 2.2
        # gravity / attraction settings
        self.gravity_enabled = False
        self.gravity_center = pygame.Vector2(0, 0)
        self.gravity_strength = 0.0
        self.max_speed = max(200, speed * 2)
        # ensure display_angle faces initial velocity (subtract π/2 offset for sprite orientation)
        self.display_angle = math.atan2(self.vel.y, self.vel.x) - math.pi / 2

        # pathing mode: 'random' (legacy) or 'figure8'
        self.path_type = path_type
        params = pattern_params or {}
        # figure-8 parameters (pixels, seconds)
        self.pattern_A = float(params.get('A', 140.0))
        self.pattern_B = float(params.get('B', 80.0))
        self.pattern_period = float(params.get('period', 4.0))
        self._pattern_time = params.get('phase', random.uniform(0, self.pattern_period))
        self._pattern_center_set = False

        # Magneettinen vetovoima pelaajaan, joka saa vihollisen kiertämään pelaajaa ja yrittämään osua siihen. Vältetään seinäkiinnittymistä ja luodaan dynaamisempi liike.
        self.magnet_enabled = True
        self.magnet_radius = float(params.get('magnet_radius', 1000.0))
        self.magnet_strength = float(params.get('magnet_strength', 400.0))
        self.magnet_min_distance = float(params.get('magnet_min_distance', 48.0))
        
        # Boundary avoidance: intelligent course correction before hitting walls
        self.boundary_avoidance_enabled = True
        self.boundary_avoidance_distance = float(params.get('avoidance_distance', 120.0))  # Distance to start avoiding
        self.boundary_turn_strength = 0.5  # How strongly to turn away (0-1)

    def update(self, dt_ms, player=None, world_rect=None):
        """
        Update StraightEnemy: movement, wall collision, random motion.
        Handles figure-8 pathing and wall bounces without double-updating position.
        """
        # Handle figure-8 pathing independently (don't use RigidBody physics for this)
        if getattr(self, 'path_type', 'random') == 'figure8':
            # set path center once
            if not self._pattern_center_set:
                try:
                    if world_rect is not None:
                        margin_x = int(self.pattern_A + 8)
                        margin_y = int(self.pattern_B + 8)
                        cx = max(world_rect.left + margin_x, min(self.pos.x, world_rect.right - margin_x))
                        cy = max(world_rect.top + margin_y, min(self.pos.y, world_rect.bottom - margin_y))
                        self.path_center = pygame.Vector2(cx, cy)
                    else:
                        self.path_center = pygame.Vector2(self.pos)
                except Exception:
                    self.path_center = pygame.Vector2(self.pos)
                self._pattern_center_set = True

            dt = dt_ms / 1000.0
            
            # advance pattern time and compute figure-8 (Lissajous-like) position
            self._pattern_time += dt
            A = self.pattern_A
            B = self.pattern_B
            period = max(0.001, self.pattern_period)
            omega = 2.0 * math.pi / period
            t = self._pattern_time
            x = self.path_center.x + A * math.sin(omega * t)
            y = self.path_center.y + B * math.sin(2.0 * omega * t)
            # derivative for velocity
            dx = A * omega * math.cos(omega * t)
            dy = 2.0 * B * omega * math.cos(2.0 * omega * t)

            self.pos = pygame.Vector2(x, y)
            self.vel = pygame.Vector2(dx, dy)
            self.rect.center = (int(self.pos.x), int(self.pos.y))

            # exhaust animation update
            speed_mag = self.vel.length()
            if speed_mag > 5.0:
                self._exhaust_timer += int(dt_ms)
                if self._exhaust_timer >= self.exhaust_speed_ms:
                    self._exhaust_timer -= self.exhaust_speed_ms
                    self.exhaust_index = (self.exhaust_index + 1) % max(1, len(getattr(self, 'exhaust_normal', []) or getattr(self, 'exhaust_turbo', [])))
            else:
                self.exhaust_index = 0

            # update facing based on velocity
            if speed_mag > 0.001:
                target = math.atan2(self.vel.y, self.vel.x) - math.pi / 2
                self._update_display_angle(dt_ms, target)
            
            # Handle world boundaries for figure-8 path
            if world_rect is not None:
                if self.rect.left < world_rect.left:
                    self.pos.x = world_rect.left
                    self.rect.centerx = int(self.pos.x)
                elif self.rect.right > world_rect.right:
                    self.pos.x = world_rect.right
                    self.rect.centerx = int(self.pos.x)
                if self.rect.top < world_rect.top:
                    self.pos.y = world_rect.top
                    self.rect.centery = int(self.pos.y)
                elif self.rect.bottom > world_rect.bottom:
                    self.pos.y = world_rect.bottom
                    self.rect.centery = int(self.pos.y)
            
            return  # Skip regular physics for figure-8 mode

        # For normal straight/random movement, set velocity and use RigidBody physics
        dt = dt_ms / 1000.0

        # Boundary avoidance: predict and steer away from walls BEFORE collision
        if getattr(self, 'boundary_avoidance_enabled', True) and world_rect is not None:
            try:
                avoidance_dist = getattr(self, 'boundary_avoidance_distance', 120.0)
                turn_strength = getattr(self, 'boundary_turn_strength', 0.5)
                
                # Check distances to all four walls
                dist_left = self.pos.x - world_rect.left
                dist_right = world_rect.right - self.pos.x
                dist_top = self.pos.y - world_rect.top
                dist_bottom = world_rect.bottom - self.pos.y
                
                # Calculate steering force away from walls
                steering = pygame.Vector2(0, 0)
                
                # Left wall
                if dist_left < avoidance_dist and self.vel.x < 0:
                    steering.x += (1.0 - dist_left / avoidance_dist) * turn_strength * self.speed
                
                # Right wall
                if dist_right < avoidance_dist and self.vel.x > 0:
                    steering.x -= (1.0 - dist_right / avoidance_dist) * turn_strength * self.speed
                
                # Top wall
                if dist_top < avoidance_dist and self.vel.y < 0:
                    steering.y += (1.0 - dist_top / avoidance_dist) * turn_strength * self.speed
                
                # Bottom wall
                if dist_bottom < avoidance_dist and self.vel.y > 0:
                    steering.y -= (1.0 - dist_bottom / avoidance_dist) * turn_strength * self.speed
                
                # Apply steering to velocity (smooth course correction)
                self.vel += steering * dt
            except Exception:
                pass

        # Apply gravity acceleration if enabled
        if self.gravity_enabled:
            dir_to_center = (pygame.Vector2(self.gravity_center) - self.pos)
            if dir_to_center.length_squared() > 0.0:
                acc = dir_to_center.normalize() * float(self.gravity_strength)
                self.vel += acc * dt

        # Magnetic attraction toward player
        if getattr(self, 'magnet_enabled', False) and player is not None:
            try:
                to_player = pygame.Vector2(player.rect.center) - self.pos
                dist = to_player.length()
                if dist > 0.0:
                    if dist < self.magnet_radius:
                        dirp = to_player.normalize()
                        strength = self.magnet_strength * max(0.0, (1.0 - dist / self.magnet_radius))
                        self.vel += dirp * (strength * dt)
                    if dist < self.magnet_min_distance:
                        dirp = to_player.normalize()
                        repulse = -dirp * max(self.magnet_strength * 2.0, 160.0)
                        self.vel += repulse * dt
            except Exception:
                pass

        # Only call parent update AFTER setting velocity fields
        # This will call RigidBody.update() which handles physics and position sync
        super().update(dt_ms, player, world_rect)
        
        # Wall collision handling (after position is updated by parent)
        if world_rect is not None:
            collided_sides = []
            if self.rect.left <= world_rect.left:
                collided_sides.append('left')
            if self.rect.right >= world_rect.right:
                collided_sides.append('right')
            if self.rect.top <= world_rect.top:
                collided_sides.append('top')
            if self.rect.bottom >= world_rect.bottom:
                collided_sides.append('bottom')

            if collided_sides:
                # Compute penetration depth
                overlap_left = max(0, world_rect.left - self.rect.left)
                overlap_right = max(0, self.rect.right - world_rect.right)
                overlap_top = max(0, world_rect.top - self.rect.top)
                overlap_bottom = max(0, self.rect.bottom - world_rect.bottom)

                overlaps = {
                    'left': overlap_left,
                    'right': overlap_right,
                    'top': overlap_top,
                    'bottom': overlap_bottom,
                }
                side = max(overlaps, key=overlaps.get)
                pen = overlaps[side]
                if pen <= 0:
                    normal = pygame.Vector2(0, 0)
                    if 'left' in collided_sides:
                        normal += pygame.Vector2(1, 0)
                    if 'right' in collided_sides:
                        normal += pygame.Vector2(-1, 0)
                    if 'top' in collided_sides:
                        normal += pygame.Vector2(0, 1)
                    if 'bottom' in collided_sides:
                        normal += pygame.Vector2(0, -1)
                    if normal.length_squared() == 0:
                        normal = pygame.Vector2(1, 0)
                    normal = normal.normalize()
                    sep = 8
                else:
                    if side == 'left':
                        normal = pygame.Vector2(1, 0)
                    elif side == 'right':
                        normal = pygame.Vector2(-1, 0)
                    elif side == 'top':
                        normal = pygame.Vector2(0, 1)
                    else:
                        normal = pygame.Vector2(0, -1)
                    sep = pen + 1.0

                # Separate from collision
                try:
                    extra_push = max(4.0, min(32.0, pen * 0.5))
                    self.pos += normal * (sep + extra_push)
                except Exception:
                    pass
                self.rect.center = (int(self.pos.x), int(self.pos.y))

                # Simple velocity reflection: just bounce velocity off the wall
                # No animation, just instant direction change
                e = getattr(self, 'wall_restitution', 0.6)  # Elasticity
                mu = getattr(self, 'wall_friction', 0.15)   # Friction
                
                v = pygame.Vector2(self.vel)
                vn = v.dot(normal)
                v_normal = vn * normal
                v_tangent = v - v_normal
                
                # Reflect normal component
                new_v_normal = -(1.0 + e) * v_normal
                # Apply friction to tangential component
                new_v_tangent = v_tangent * max(0.0, 1.0 - mu)
                new_v = new_v_normal + new_v_tangent
                
                # Ensure minimum velocity to not get stuck
                if new_v.length_squared() < 1.0:
                    new_v = normal * (self.speed * 0.5)
                
                self.vel = new_v

            self.rect.clamp_ip(world_rect)

        # Keep legacy vx/vy in sync
        self.vx, self.vy = float(self.vel.x), float(self.vel.y)
        
        # Update display angle
        if abs(self.vel.x) > 0.001 or abs(self.vel.y) > 0.001:
            target = math.atan2(self.vel.y, self.vel.x) - math.pi / 2
            self._update_display_angle(dt_ms, target)

        # Random nudge
        if self.random_motion:
            self._change_timer += int(dt_ms)
            if self._change_timer >= self._change_interval:
                self._change_timer -= self._change_interval
                self._apply_random_nudge()
                self._change_interval = random.randint(self._change_interval_min, self._change_interval_max)

    def _apply_random_nudge(self):
        # Extract angle from velocity (standard convention: atan2(y, x) - π/2 for sprite orientation)
        angle = math.atan2(self.vel.y, self.vel.x) - math.pi / 2
        # Apply small random rotation
        angle += random.uniform(-math.pi / 12, math.pi / 12)
        # Maintain speed and apply rotated direction
        speed = self.vel.length() or self.speed
        speed *= random.uniform(0.9, 1.1)
        # Add π/2 to convert back to velocity space
        angle += math.pi / 2
        self.vel.x = math.cos(angle) * speed
        self.vel.y = math.sin(angle) * speed


class CircleEnemy(Enemy):
    """Simple, readable circular-motion enemy.

    - `angular_speed` is the base angular speed in radians/sec.
    - A behavior multiplier modifies that base speed (pause, slow, dash, reverse).
    - Position is computed directly from angle, so speed control is explicit.
    """
    def __init__(self, image, center_x, center_y, radius=160, angular_speed=2.0, sprite_index: int | None = None):
        super().__init__(image, center_x + radius, center_y)
        if sprite_index is not None:
            self.set_sprite_config(sprite_index)
        self.center = pygame.Vector2(center_x, center_y)
        self.radius = float(radius)
        # base angular speed (radians per second)
        self.base_angular_speed = float(angular_speed)
        # current angle around the circle
        self.angle = random.uniform(0.0, math.tau)

        # initial facing: tangent to the circle
        vx = -math.sin(self.angle) * self.base_angular_speed * self.radius
        vy = math.cos(self.angle) * self.base_angular_speed * self.radius
        self.display_angle = math.atan2(-vy, vx)

        # Physics / external push support
        self.mass = 1.0
        # push system: linear-decay push applied to position for short durations
        self._push_initial = pygame.Vector2(0, 0)
        self._push_elapsed = 0.0
        self._push_duration = 0.0

        # behavior state for simple, readable speed control
        self._behavior = 'normal'
        self._behavior_timer = 0.0
        self._behavior_duration = random.uniform(0.8, 2.5)
        # explicit multiplier applied to base_angular_speed
        self._speed_mult = 1.0

    def _choose_behavior(self):
        """Pick a simple behavior and set the speed multiplier."""
        r = random.random()
        if r < 0.10:
            self._behavior = 'pause'
            self._speed_mult = 0.0
        elif r < 0.30:
            self._behavior = 'reverse'
            self._speed_mult = -1.0
        elif r < 0.60:
            self._behavior = 'dash'
            # dash is a clear multiplicative increase
            self._speed_mult = random.uniform(0.8, 0.9)
        elif r < 0.85:
            self._behavior = 'slow'
            self._speed_mult = random.uniform(0.4, 0.8)
        else:
            self._behavior = 'normal'
            self._speed_mult = 1.0

    def update(self, dt_ms, player=None, world_rect=None):
        # keep base animation ticking
        super().update(dt_ms, player, world_rect)

        dt = dt_ms / 1000.0
        
        # Boundary avoidance: adjust circle center away from walls to prevent collision
        if world_rect is not None:
            try:
                avoidance_dist = 100.0  # Distance from wall to start avoiding
                min_buffer = 50.0  # Minimum distance to maintain from walls
                
                # Check distances and push center away from walls
                margin = self.radius + min_buffer
                
                if self.center.x - self.radius < world_rect.left + avoidance_dist:
                    self.center.x = max(self.center.x, world_rect.left + margin)
                if self.center.x + self.radius > world_rect.right - avoidance_dist:
                    self.center.x = min(self.center.x, world_rect.right - margin)
                if self.center.y - self.radius < world_rect.top + avoidance_dist:
                    self.center.y = max(self.center.y, world_rect.top + margin)
                if self.center.y + self.radius > world_rect.bottom - avoidance_dist:
                    self.center.y = min(self.center.y, world_rect.bottom - margin)
            except Exception:
                pass

        # behavior timer: pick a new behavior when time's up
        self._behavior_timer += dt
        if self._behavior_timer >= self._behavior_duration:
            self._behavior_timer = 0.0
            self._behavior_duration = random.uniform(0.6, 3.0)
            self._choose_behavior()

        # compute angular change explicitly using base speed and multiplier
        angular_speed = self.base_angular_speed * self._speed_mult
        self.angle += angular_speed * dt

        # keep angle in a reasonable range
        if self.angle > math.tau or self.angle < -math.tau:
            self.angle = self.angle % math.tau

        # update position from angle
        self.pos = pygame.Vector2(
            self.center.x + math.cos(self.angle) * self.radius,
            self.center.y + math.sin(self.angle) * self.radius,
        )
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # If an external short push is active, apply it as a position offset that decays linearly
        if self._push_duration > 0.0 and self._push_elapsed < self._push_duration:
            t = self._push_elapsed / max(1e-6, self._push_duration)
            # current push vector decays linearly from initial to zero
            current_push = self._push_initial * (1.0 - t)
            self.pos += current_push * dt
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            self._push_elapsed += dt

        # update facing based on instantaneous tangent direction
        vx = -math.sin(self.angle) * angular_speed * self.radius
        vy = math.cos(self.angle) * angular_speed * self.radius
        if abs(vx) > 1e-6 or abs(vy) > 1e-6:
            target = math.atan2(-vy, vx)
            self._update_display_angle(dt_ms, target)

    def apply_push(self, impulse_vec: pygame.Vector2, duration: float = 0.5):
        """Apply a short-lived positional push to the circle enemy.

        The push decays linearly to zero over `duration` seconds. `impulse_vec` is
        interpreted as an initial velocity-like offset (px/s) applied to position.
        """
        try:
            self._push_initial = pygame.Vector2(impulse_vec)
            self._push_elapsed = 0.0
            self._push_duration = max(0.001, float(duration))
        except Exception:
            pass

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        # keep sprite visually upright (no rotation)
        r = self.image.get_rect(center=(self.rect.centerx - camera_x, self.rect.centery - camera_y))
        screen.blit(self.image, r.topleft)


class DownEnemy(Enemy):
    """Enemy that spawns at top and moves downward."""
    def __init__(self, image, x, y, speed=200, hp=1, sprite_index: int | None = None):
        super().__init__(image, x, y, hp)
        if sprite_index is not None:
            self.set_sprite_config(sprite_index)
        # Vertical movers must always rotate to match movement direction.
        self.rotation_config['rotation_enabled'] = True
        self.rotation_config['min_angle'] = None
        self.rotation_config['max_angle'] = None
        self.speed = speed  # Positive = downward
        self.vel = pygame.Vector2(0, self.speed)
        # Match common enemy angle convention from velocity.
        self.display_angle = math.atan2(self.speed, 0.0) - math.pi / 2

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0
        
        # Move vertically (positive = down, negative = up)
        self.pos.y += self.speed * dt
        
        # Boundary avoidance: constrain horizontal position away from walls
        if world_rect is not None:
            margin = 30
            self.pos.x = max(world_rect.left + margin, min(self.pos.x, world_rect.right - margin))
        
        # Bounce off vertical boundaries and update angle
        if world_rect is not None:
            if self.pos.y - (self.rect.height // 2) <= world_rect.top:
                self.pos.y = world_rect.top + (self.rect.height // 2)
                self.speed = abs(self.speed)  # Ensure moving downward
                self._update_display_angle(dt_ms, math.atan2(self.speed, 0.0) - math.pi / 2)
            elif self.pos.y + (self.rect.height // 2) >= world_rect.bottom:
                self.pos.y = world_rect.bottom - (self.rect.height // 2)
                self.speed = -abs(self.speed)  # Reverse to moving upward
                self._update_display_angle(dt_ms, math.atan2(self.speed, 0.0) - math.pi / 2)

        # Keep facing in sync every frame even when no boundary bounce occurs.
        self._update_display_angle(dt_ms, math.atan2(self.speed, 0.0) - math.pi / 2)
        
        # Update rect to follow pos
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class UpEnemy(Enemy):
    """Enemy that spawns at bottom and moves upward."""
    def __init__(self, image, x, y, speed=200, hp=1, sprite_index: int | None = None):
        super().__init__(image, x, y, hp)
        if sprite_index is not None:
            self.set_sprite_config(sprite_index)
        # Vertical movers must always rotate to match movement direction.
        self.rotation_config['rotation_enabled'] = True
        self.rotation_config['min_angle'] = None
        self.rotation_config['max_angle'] = None
        self.speed = -speed  # Negative = upward movement
        self.vel = pygame.Vector2(0, self.speed)
        # Match common enemy angle convention from velocity.
        self.display_angle = math.atan2(self.speed, 0.0) - math.pi / 2

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0
        
        # Move vertically (negative = up, positive = down)
        self.pos.y += self.speed * dt
        
        # Boundary avoidance: constrain horizontal position away from walls
        if world_rect is not None:
            margin = 30
            self.pos.x = max(world_rect.left + margin, min(self.pos.x, world_rect.right - margin))
        
        # Bounce off vertical boundaries and update angle
        if world_rect is not None:
            if self.pos.y - (self.rect.height // 2) <= world_rect.top:
                self.pos.y = world_rect.top + (self.rect.height // 2)
                self.speed = abs(self.speed)  # Reverse to moving downward
                self._update_display_angle(dt_ms, math.atan2(self.speed, 0.0) - math.pi / 2)
            elif self.pos.y + (self.rect.height // 2) >= world_rect.bottom:
                self.pos.y = world_rect.bottom - (self.rect.height // 2)
                self.speed = -abs(self.speed)  # Reverse to moving upward
                self._update_display_angle(dt_ms, math.atan2(self.speed, 0.0) - math.pi / 2)

        # Keep facing in sync every frame even when no boundary bounce occurs.
        self._update_display_angle(dt_ms, math.atan2(self.speed, 0.0) - math.pi / 2)
        
        # Update rect to follow pos
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class ZigZagEnemy(Enemy):
    """Enemy that moves in zigzag pattern (horizontal and vertical)."""
    def __init__(self, image, x, y, speed=260, amplitude=120, frequency=3.0, hp=1, sprite_index: int | None = None):
        super().__init__(image, x, y, hp)
        if sprite_index is not None:
            self.set_sprite_config(sprite_index)
        self.start_x = x
        self.pos = pygame.Vector2(x, y)
        self.speed = speed
        self.amplitude = amplitude
        self.frequency = frequency
        self.time = 0.0
        self.vy_dir = 1  # 1 = down, -1 = up
        self.vel = pygame.Vector2(0, self.speed * self.vy_dir)

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0
        
        self.time += dt
        
        # Vertical movement (constant)
        self.pos.y += self.speed * self.vy_dir * dt
        
        # Horizontal zigzag (sine wave)
        self.pos.x = self.start_x + math.sin(self.time * self.frequency) * self.amplitude
        
        # Boundary constraints
        if world_rect is not None:
            margin = 50
            max_amp = self.amplitude * 0.8
            
            # Constrain center x to keep oscillation within bounds
            if self.start_x - max_amp < world_rect.left + margin:
                self.start_x = world_rect.left + margin + max_amp
            elif self.start_x + max_amp > world_rect.right - margin:
                self.start_x = world_rect.right - margin - max_amp
            
            # Recalculate x after constraint
            self.pos.x = self.start_x + math.sin(self.time * self.frequency) * self.amplitude
            
            # Reverse direction at vertical boundaries
            if self.pos.y - (self.rect.height // 2) <= world_rect.top:
                self.pos.y = world_rect.top + (self.rect.height // 2)
                self.vy_dir = 1
            elif self.pos.y + (self.rect.height // 2) >= world_rect.bottom:
                self.pos.y = world_rect.bottom - (self.rect.height // 2)
                self.vy_dir = -1
        
        # Update rect and velocity vector
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.vel = pygame.Vector2(
            math.cos(self.time * self.frequency) * self.frequency * self.amplitude,
            self.speed * self.vy_dir
        )
        
        # Update display angle to face movement direction
        if self.vel.length_squared() > 0.01:
            self._update_display_angle(dt_ms, math.atan2(self.vel.y, self.vel.x) - math.pi / 2)


class ChaseEnemy(Enemy):
    """Enemy that chases the player."""
    def __init__(self, image, x, y, speed=220, hp=1, sprite_index: int | None = None):
        super().__init__(image, x, y, hp)
        if sprite_index is not None:
            self.set_sprite_config(sprite_index)
        self.pos = pygame.Vector2(x, y)
        self.speed = speed
        self.vel = pygame.Vector2(0, 0)
        self.hit_player_cooldown = 0.0

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0

        # Decrease cooldown
        if self.hit_player_cooldown > 0:
            self.hit_player_cooldown -= dt

        # Move toward player if cooldown is not active
        if player is not None and self.hit_player_cooldown <= 0:
            target = pygame.Vector2(player.rect.center)
            direction = target - self.pos

            if direction.length_squared() > 0:
                direction = direction.normalize()
                
                # Boundary avoidance: steer away from walls
                if world_rect is not None:
                    avoidance_dist = 100.0
                    turn_strength = 0.4
                    
                    # Check distances to walls
                    dist_left = self.pos.x - world_rect.left
                    dist_right = world_rect.right - self.pos.x
                    dist_top = self.pos.y - world_rect.top
                    dist_bottom = world_rect.bottom - self.pos.y
                    
                    # Create avoidance steering
                    avoidance = pygame.Vector2(0, 0)
                    
                    if dist_left < avoidance_dist:
                        avoidance.x += (1.0 - dist_left / avoidance_dist) * turn_strength
                    if dist_right < avoidance_dist:
                        avoidance.x -= (1.0 - dist_right / avoidance_dist) * turn_strength
                    if dist_top < avoidance_dist:
                        avoidance.y += (1.0 - dist_top / avoidance_dist) * turn_strength
                    if dist_bottom < avoidance_dist:
                        avoidance.y -= (1.0 - dist_bottom / avoidance_dist) * turn_strength
                    
                    # Blend chase direction with avoidance
                    if avoidance.length_squared() > 0:
                        direction = (direction * 0.7 + avoidance.normalize() * 0.3).normalize()
                
                self.pos += direction * self.speed * dt
                self.vel = direction * self.speed
                # Update angle to face chase direction
                self._update_display_angle(dt_ms, math.atan2(direction.y, direction.x) - math.pi / 2)

        # Update rect to follow position
        self.rect.center = (int(self.pos.x), int(self.pos.y))
