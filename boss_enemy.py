import pygame
from enemy import Enemy

class BossEnemy(Enemy):
    def __init__(self, image: pygame.Surface, world_rect: pygame.Rect,
                 hp: int = 10, enter_speed: float = 250, move_speed: float = 300):
        
        # Spawn ylävasemmalta, hieman ruudun ulkopuolelta
        start_x = world_rect.left + image.get_width() // 2
        start_y = world_rect.top - image.get_height() // 2
        
        super().__init__(image, start_x, start_y)

        self.world_rect = world_rect
        self.hp = hp

        self.enter_speed = enter_speed
        self.move_speed = move_speed

        self.state = "entering"   # entering -> active
        self.vx = move_speed

        # Mihin kohtaan boss pysähtyy pystysuunnassa
        self.target_y = world_rect.top + 180

    def take_hit(self, amount=1):
        self.hp -= amount
        return self.hp <= 0

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0

        if self.state == "entering":
            # Liikkuu alaspäin
            self.rect.y += int(self.enter_speed * dt)

            if self.rect.centery >= self.target_y:
                self.rect.centery = self.target_y
                self.state = "active"

        elif self.state == "active":
            # Liikkuu vasen-oikea
            self.rect.x += int(self.vx * dt)

            if self.rect.left <= self.world_rect.left:
                self.rect.left = self.world_rect.left
                self.vx *= -1

            if self.rect.right >= self.world_rect.right:
                self.rect.right = self.world_rect.right
                self.vx *= -1
