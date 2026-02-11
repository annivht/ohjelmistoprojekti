import pygame
import math
import os
from PLAYER_LUOKAT.PlayerAnimation import PlayerAnimation
from PLAYER_LUOKAT.PlayerWeapons import PlayerWeapons
from PLAYER_LUOKAT.PlayerInput import PlayerInput

class Player(pygame.sprite.Sprite):
    def __init__(self, scale_factor, frames, x, y, boost_frames=None):
        super().__init__()
        self.scale_factor = scale_factor
        self.input = PlayerInput()
        self.animation = PlayerAnimation(scale_factor)
        self.weapons = PlayerWeapons(scale_factor)
        self.attack_offset_distance = 4.5 # asetettu 0.5 scalefactorille RocketGame.py(scale_factor=0.5) 

        liike_frames = frames if frames else [pygame.Surface((32, 32), pygame.SRCALPHA)]
        self.animaatio = {
            'move': self.animation.scale_frames(liike_frames),
            'boost': self.animation.scale_frames(boost_frames) if boost_frames else []
        }
        self.frame_index = 0
        self.current_anim = 'move'
        self.image = self.animaatio[self.current_anim][self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.angle = 0.0
        self.turn_speed = 180.0
        self.accel = 300.0
        self.max_speed = 400.0
        self.brake_decel = 500.0
        self.anim_timer = 0
        self.anim_speed = 100

        # Destroyed animation
        self.destroyed_sprites = self.animation.load_destroyed_sprites()
        self.destroyed_anim_timer = 0
        self.destroyed_anim_duration = 1200
        self.destroyed_anim_speed = 60
        self.is_destroyed = False
        self.destroyed_frame_index = 0

        # Attack animation
        self.attack_frames = []
        project_root = os.path.dirname(os.path.dirname(__file__))
        attack_paths = [
            os.path.join(project_root, 'alukset', 'alus', 'Corvette', 'Attack_1', '000_attack_1_0.png'),
            os.path.join(project_root, 'alukset', 'alus', 'Corvette', 'Attack_1', '001_attack_1_1.png'),
            os.path.join(project_root, 'alukset', 'alus', 'Corvette', 'Attack_1', '002_attack_1_2.png'),
            os.path.join(project_root, 'alukset', 'alus', 'Corvette', 'Attack_1', '003_attack_1_3.png'),
        ]
        for path in attack_paths:
            img = pygame.image.load(path).convert_alpha()
            w = max(1, int(img.get_width() * self.scale_factor))
            h = max(1, int(img.get_height() * self.scale_factor))
            self.attack_frames.append(pygame.transform.scale(img, (w, h)))
        self.attack_frame_index = 0
        self.attack_anim_timer = 0
        self.attack_anim_speed = 80

        # Osuma-animaatio
        self.hit_anim_timer = 0
        self.hit_anim_duration = 200
        self.hit_flash_color = (255, 80, 80)

        # Vahinko-animaatio
        self.damage_sprites = []
        self.damage_sprite_names = []
        damage_dir = os.path.join(project_root, 'alukset', 'alus', 'Corvette', 'Damage')
        damage_files = sorted([f for f in os.listdir(damage_dir) if f.lower().endswith('.png')])
        for fname in damage_files:
            path = os.path.join(damage_dir, fname)
            img = pygame.image.load(path).convert_alpha()
            w = max(1, int(img.get_width() * self.scale_factor))
            h = max(1, int(img.get_height() * self.scale_factor))
            self.damage_sprites.append(pygame.transform.scale(img, (w, h)))
            self.damage_sprite_names.append(fname)


    def update(self, dt):
        self.input.update()
        self.update_destroyed_animation(dt)
        self.weapons.update(dt)
        self.update_hit_animation(dt)
        self.handle_attack_animation(dt)
        self.handle_animation(dt)
        self.handle_movement(dt)

    def update_destroyed_animation(self, dt):
        if self.is_destroyed:
            self.destroyed_anim_timer += dt
            frame_count = len(self.destroyed_sprites)
            if frame_count > 0:
                self.destroyed_frame_index = min(int(self.destroyed_anim_timer / self.destroyed_anim_speed), frame_count - 1)

    def update_hit_animation(self, dt):
        if self.hit_anim_timer > 0:
            self.hit_anim_timer -= dt
            if self.hit_anim_timer < 0:
                self.hit_anim_timer = 0
        if self.input.hit:
            self.trigger_hit_animation()

    def handle_attack_animation(self, dt):
        if self.input.shoot:
            if self.attack_frames:
                self.attack_anim_timer += dt
                if self.attack_anim_timer >= self.attack_anim_speed:
                    self.attack_anim_timer -= self.attack_anim_speed
                    self.attack_frame_index = (self.attack_frame_index + 1) % len(self.attack_frames)
            self.weapons.shoot(self.pos, self.angle)
        else:
            self.attack_frame_index = 0
            self.attack_anim_timer = 0

    def handle_animation(self, dt):
        new_anim = 'boost' if (self.input.moveUp and self.animaatio.get('boost')) else 'move'
        if new_anim != self.current_anim:
            self.current_anim = new_anim
            self.frame_index = 0
            self.anim_timer = 0
        frames = self.animaatio.get(self.current_anim, [])
        if frames:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer -= self.anim_speed
                self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]

    def handle_movement(self, dt):
        dt_s = dt / 1000.0
        if self.input.turnLeft:
            self.angle += self.turn_speed * dt_s
        if self.input.turnRight:
            self.angle -= self.turn_speed * dt_s
        if self.input.moveUp:
            rad = math.radians(self.angle)
            thrust = pygame.math.Vector2(math.cos(rad), math.sin(rad)) * self.accel * dt_s
            self.vel += thrust
            if self.vel.length() > self.max_speed:
                self.vel.scale_to_length(self.max_speed)
        if self.input.moveDown:
            speed = self.vel.length()
            if speed > 0:
                dec = self.brake_decel * dt_s
                new_speed = max(0.0, speed - dec)
                if new_speed == 0:
                    self.vel = pygame.math.Vector2(0, 0)
                else:
                    self.vel.scale_to_length(new_speed)
        self.pos += self.vel * dt_s
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def move(self, dx, dy, world_w, world_h):
        self.rect.x += dx
        self.rect.y += dy
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery
        self.rect.x = max(0, min(self.rect.x, world_w - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, world_h - self.rect.height))
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery

    def draw(self, screen, cam_x, cam_y):
        if self.is_destroyed and self.destroyed_sprites:
            destroyed_sprite = self.destroyed_sprites[self.destroyed_frame_index]
            destroyed_rect = destroyed_sprite.get_rect(center=(self.pos.x - cam_x, self.pos.y - cam_y))
            screen.blit(destroyed_sprite, destroyed_rect.topleft)
            return

        # Piirrä pelaajan sprite
        rotated = pygame.transform.rotate(self.image, -self.angle)
        rot_rect = rotated.get_rect(center=(self.pos.x - cam_x, self.pos.y - cam_y))
        screen.blit(rotated, rot_rect.topleft)

        # Piirrä aseiden ammukset
        for bullet in self.weapons.bullets:
            screen.blit(bullet.image, (bullet.rect.x - cam_x, bullet.rect.y - cam_y))

        # Piirrä hyökkäysanimaatio
        if self.input.shoot and self.attack_frames:
            attack_sprite = self.attack_frames[self.attack_frame_index]
            attack_rotated = pygame.transform.rotate(attack_sprite, -self.angle)
            rad = math.radians(self.angle)
            offset_x = math.cos(rad) * self.attack_offset_distance
            offset_y = math.sin(rad) * self.attack_offset_distance
            attack_center = (self.pos.x - cam_x + offset_x, self.pos.y - cam_y + offset_y)
            attack_rect = attack_rotated.get_rect(center=attack_center)
            screen.blit(attack_rotated, attack_rect.topleft)

    def trigger_hit_animation(self):
        self.hit_anim_timer = self.hit_anim_duration