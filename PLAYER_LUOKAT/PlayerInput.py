import pygame

class PlayerInput:
    def __init__(self):
        self.moveUp = False
        self.moveDown = False
        self.turnLeft = False
        self.turnRight = False
        self.shoot = False
        self.hit = False

    def update(self):
        keys = pygame.key.get_pressed()
        self.moveUp = keys[pygame.K_w]
        self.moveDown = keys[pygame.K_s]
        self.turnLeft = keys[pygame.K_d]
        self.turnRight = keys[pygame.K_a]
        self.shoot = keys[pygame.K_RCTRL]
        self.hit = keys[pygame.K_h]