import pygame
import math
import random

class Enemy(pygame.sprite.Sprite):
    def __init__(self, image: pygame.Surface, x: float, y: float):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self, dt_ms: int, player=None, world_rect: pygame.Rect | None = None):
        pass

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
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
