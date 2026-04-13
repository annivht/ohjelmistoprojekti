import math
from pathlib import Path

import pygame

from Valikot.menu_style import MenuButton, TEXT_COLOR, SUBTEXT_COLOR, draw_dim_overlay


class VictoryScreen:
    def __init__(self, screen, background_surface=None, sounds=None):
        self.screen = screen
        self.background_surface = background_surface
        self.sounds = sounds

        screen_w, screen_h = self.screen.get_size()
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.center = (screen_w // 2, screen_h // 2 - 10)

        self.title_font = pygame.font.Font(None, 96)
        self.subtitle_font = pygame.font.Font(None, 36)
        self._last_tick = pygame.time.get_ticks()
        self.frame_timer = 0
        self.frame_index = 0
        self.frame_duration_ms = 90

        self.pedro_frames = self._load_pedro_frames()
        self.button = MenuButton(
            screen_w // 2 - 160,
            screen_h - 118,
            320,
            74,
            "QUIT GAME",
            action="quit",
            variant="danger",
        )

    def _load_pedro_frames(self):
        frame_dir = Path(__file__).resolve().parent.parent / "images" / "pedro_frames"
        frame_paths = []

        if frame_dir.exists():
            frame_paths = sorted(
                [path for path in frame_dir.iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
            )

        frames = []
        for path in frame_paths:
            try:
                image = pygame.image.load(str(path)).convert_alpha()
                frames.append(image)
            except pygame.error:
                continue

        if not frames:
            fallback = pygame.Surface((220, 220), pygame.SRCALPHA)
            pygame.draw.circle(fallback, (73, 201, 163), (110, 110), 92)
            pygame.draw.circle(fallback, (255, 255, 255), (82, 92), 18)
            pygame.draw.circle(fallback, (255, 255, 255), (138, 92), 18)
            pygame.draw.arc(fallback, (20, 34, 40), (64, 74, 112, 96), math.radians(20), math.radians(160), 8)
            frames.append(fallback)

        return frames

    def _get_current_frame(self):
        if not self.pedro_frames:
            return None

        current = self.pedro_frames[self.frame_index % len(self.pedro_frames)]
        max_size = 250
        width, height = current.get_size()
        scale = min(max_size / max(1, width), max_size / max(1, height))
        scaled_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        return pygame.transform.smoothscale(current, scaled_size)

    def update(self):
        now = pygame.time.get_ticks()
        delta_ms = now - self._last_tick
        self._last_tick = now

        self.frame_timer += delta_ms
        if self.frame_timer >= self.frame_duration_ms:
            steps = self.frame_timer // self.frame_duration_ms
            self.frame_index = (self.frame_index + int(steps)) % len(self.pedro_frames)
            self.frame_timer %= self.frame_duration_ms

    def handle_events_from(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.button.is_clicked(pygame.mouse.get_pos()):
                    return self.button.action

        return None

    def draw(self, surface=None):
        target = self.screen if surface is None else surface

        if self.background_surface is not None:
            try:
                target.blit(self.background_surface, (0, 0))
            except Exception:
                target.fill((5, 10, 18))
        else:
            target.fill((5, 10, 18))

        draw_dim_overlay(target, (4, 10, 18, 170))

        title_surface = self.title_font.render("YOU WIN", True, TEXT_COLOR)
        title_rect = title_surface.get_rect(center=(self.screen_w // 2, 96))
        target.blit(title_surface, title_rect)

        subtitle_surface = self.subtitle_font.render("Pedro has entered the finale", True, SUBTEXT_COLOR)
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen_w // 2, 146))
        target.blit(subtitle_surface, subtitle_rect)

        frame_surface = self._get_current_frame()
        if frame_surface is not None:
            orbit_x = self.center[0] + int(math.sin(pygame.time.get_ticks() / 420.0) * 16)
            orbit_y = self.center[1] + int(math.cos(pygame.time.get_ticks() / 540.0) * 10)
            halo_rect = frame_surface.get_rect(center=(orbit_x, orbit_y))

            halo_surface = pygame.Surface((halo_rect.width + 100, halo_rect.height + 100), pygame.SRCALPHA)
            halo_center = (halo_surface.get_width() // 2, halo_surface.get_height() // 2)
            pygame.draw.circle(halo_surface, (255, 208, 86, 40), halo_center, max(halo_rect.width, halo_rect.height) // 2 + 26)
            pygame.draw.circle(halo_surface, (120, 215, 255, 28), halo_center, max(halo_rect.width, halo_rect.height) // 2 + 56)
            target.blit(halo_surface, halo_surface.get_rect(center=(orbit_x, orbit_y)))

            target.blit(frame_surface, frame_surface.get_rect(center=(orbit_x, orbit_y)))

        self.button.update(pygame.mouse.get_pos())
        self.button.draw(target)

        if surface is None:
            pygame.display.update()