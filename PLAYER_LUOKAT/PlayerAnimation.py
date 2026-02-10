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

    @staticmethod
    def load_damage_offsets(offset_file='damage_sprite_offsets.txt'):
        offsets = {}
        try:
            with open(offset_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line:
                        name, val = line.strip().split(':')
                        try:
                            if ',' in val:
                                x_str, y_str = val.split(',')
                                x = int(x_str)
                                y = int(y_str)
                                offsets[name] = (x, y)
                            else:
                                offsets[name] = (int(val), 0)
                        except ValueError:
                            print(f"[PlayerAnimation] Offset-arvo virheellinen: {val} (rivi: {line.strip()})")
        except Exception as e:
            print(f"[PlayerAnimation] Offset-tiedoston luku epäonnistui: {e}")
        return offsets

    def scale_frames(self, frames):
        if not frames:
            return []
        scaled = []
        for f in frames:
            w = max(1, int(f.get_width() * self.scale_factor))
            h = max(1, int(f.get_height() * self.scale_factor))
            scaled.append(pygame.transform.scale(f, (w, h)))
        return scaled