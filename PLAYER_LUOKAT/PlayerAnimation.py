import pygame
import os

class PlayerAnimation:
    def __init__(self, scale_factor):
        self.scale_factor = scale_factor

    def load_destroyed_sprites(self):
        destroyed_dir = 'alukset/alus/Corvette/Destroyed'
        frames = []
        files = sorted([f for f in os.listdir(destroyed_dir) if f.lower().endswith('.png')], key=lambda x: int(os.path.splitext(x)[0]))
        for fname in files:
            path = os.path.join(destroyed_dir, fname)
            img = pygame.image.load(path).convert_alpha()
            w = max(1, int(img.get_width() * self.scale_factor))
            h = max(1, int(img.get_height() * self.scale_factor))
            frames.append(pygame.transform.scale(img, (w, h)))
        return frames


    def scale_frames(self, frames):
        if not frames:
            return []
        scaled = []
        for f in frames:
            w = max(1, int(f.get_width() * self.scale_factor))
            h = max(1, int(f.get_height() * self.scale_factor))
            scaled.append(pygame.transform.scale(f, (w, h)))
        return scaled