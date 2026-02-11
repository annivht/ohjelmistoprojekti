import pygame
import math

class Ammus(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, image):
        super().__init__()
        self.image = pygame.transform.rotate(image, -angle)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.speed = 700  # px/s
        self.angle = angle
        self.vel = pygame.math.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * self.speed

    def update(self, dt):
        dt_s = dt / 1000.0
        self.pos += self.vel * dt_s
        self.rect.center = (int(self.pos.x), int(self.pos.y))
