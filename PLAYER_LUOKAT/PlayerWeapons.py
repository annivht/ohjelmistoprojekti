import pygame
import math
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Ammus import Ammus

class PlayerWeapons:
    def __init__(self, scale_factor):
        self.scale_factor = scale_factor
        self.bullet_img = pygame.image.load('alukset/alus/Corvette/Charge_1/000_Charge_1_0.png').convert_alpha()
        w = max(1, int(self.bullet_img.get_width() * self.scale_factor))
        h = max(1, int(self.bullet_img.get_height() * self.scale_factor))
        self.bullet_img = pygame.transform.scale(self.bullet_img, (w, h))
        self.bullets = pygame.sprite.Group()
        self.shoot_cooldown = 300
        self.shoot_timer = 0

    def shoot(self, pos, angle):
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_cooldown
            side_offset = 15 # asetettu 0.5 scalefactorille. RocketGame.py(scale_factor=0.5) -> 10px
            forward_offset = 20
            rad = math.radians(angle)
            perp_rad = rad + math.pi/2
            x1 = pos.x + math.cos(rad) * forward_offset + math.cos(perp_rad) * side_offset
            y1 = pos.y + math.sin(rad) * forward_offset + math.sin(perp_rad) * side_offset
            x2 = pos.x + math.cos(rad) * forward_offset - math.cos(perp_rad) * side_offset
            y2 = pos.y + math.sin(rad) * forward_offset - math.sin(perp_rad) * side_offset
            self.bullets.add(Ammus(x1, y1, angle, self.bullet_img))
            self.bullets.add(Ammus(x2, y2, angle, self.bullet_img))

    def update(self, dt):
        if self.shoot_timer > 0:
            self.shoot_timer -= dt
        self.bullets.update(dt)