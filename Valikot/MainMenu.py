import pygame
import os
import json
from Valikot.menu_style import (
    MenuButton,
    draw_dim_overlay,
    draw_menu_panel,
)



BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (52, 78, 91)

class TextInput:
    """Simple text input box used by the settings menu."""

    def __init__(self, x, y, width, height, text='', color=WHITE, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.active = False
        self.last_saved_text = text

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5)

        text_surface = pygame.font.Font(None, 36).render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.save_if_changed('player_name.txt')
    
    def set_rect(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
    
    def get_value(self):
        return self.text.strip()
    
    def set_value(self, value):
        self.text = value

    def clear(self):
        self.text = ''
    
    def __str__(self):
        return self.text
    
    def save_to_file(self, filename):
        """TALLENNA TEKSTI TIEDOSTOON"""
        with open(filename, 'w') as file:
            file.write(self.text)
    
    def save_if_changed(self, filename):
        """TALLENNA VAIN JOS TEKSTI ON MUUTTUNUT"""
        if self.text != self.last_saved_text:
            self.save_to_file(filename)
            self.last_saved_text = self.text

    
    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                self.text = file.read().strip()
        except FileNotFoundError:
            self.text = ''

class MainMenu:
    """State-friendly main menu that draws to an external surface."""

    def __init__(self, sounds=None):
        if not pygame.get_init():
            pygame.init()

        if not pygame.font.get_init():
            pygame.font.init()

        self.sounds = sounds
        self.previous_hovered_button = None

        self.button_width = 300
        self.button_height = 78
        self.button_spacing = 22
        self.panel_width = 760
        self.panel_height = 560
        self.buttons = []
        self.panel_rect = None
        self.background_image = None
        self.text_input = TextInput(1600, 800, 300, 40)
        self._update_layout()

    def _update_layout(self):
        # Hae nykyinen ikkunan koko
        screen = pygame.display.get_surface()
        if screen is not None:
            width, height = screen.get_width(), screen.get_height()
        else:
            width, height = 1600, 800

        panel_left = width // 2 - self.panel_width // 2
        panel_top = height // 2 - self.panel_height // 2
        self.panel_rect = pygame.Rect(panel_left, panel_top, self.panel_width, self.panel_height)

        total_height = 3 * self.button_height + 2 * self.button_spacing
        start_y = self.panel_rect.top + 170 + (self.panel_rect.height - 240 - total_height) // 2
        center_x = width // 2 - self.button_width // 2

        self.buttons = [
            MenuButton(
                center_x,
                start_y,
                self.button_width,
                self.button_height,
                "START GAME",
                action="start",
            ),
            MenuButton(
                center_x,
                start_y + self.button_height + self.button_spacing,
                self.button_width,
                self.button_height,
                "SETTINGS",
                action="settings",
            ),
            MenuButton(
                center_x,
                start_y + 2 * (self.button_height + self.button_spacing),
                self.button_width,
                self.button_height,
                "QUIT",
                action="quit",
                variant="danger",
            ),
        ]
        
        # Menu backdrop: draw scene-like background and translucent veil
        # instead of a flat solid color.
        self.background_image = None
        # Päivitä taustakuva oikeaan kokoon
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))
            bg_path = os.path.join(project_root, "images", "taustat", "avaruus.png")
            bg = pygame.image.load(bg_path).convert()
            self.background_image = pygame.transform.scale(bg, (width, height))
        except Exception:
            self.background_image = None
        
        self.text_input.set_rect(center_x, start_y + 3 * (self.button_height + self.button_spacing), self.button_width, 40)

    def handle_events(self, events):
        """Handle a frame's events and return selected action or None."""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    if button.is_clicked(event.pos):
                        return button.action

        return None
    
    def get_value(self):
        return self.text_input.get_value()
    
    def show_score(self, x, y, font, screen, filename='leaderboard.json', top_n=5):
        try:
            with open(filename, 'r') as file:
                scores = json.load(file)
            scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n])
            screen.blit(font.render("LEADERBOARD", True, (255, 255, 255)), (x, y))
            for player_id, score in scores.items():
                score_text = f"{player_id}: {score}"
                score = font.render(score_text, True, (255, 255, 255))
                screen.blit(score, (x, y + 30 * (list(scores.keys()).index(player_id) + 1)))
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass

    def draw(self, surface):
        # Päivitä layout aina ennen piirtämistä, jos ikkunan koko on muuttunut
        self._update_layout()
        if self.background_image is not None:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(DARK_BLUE)
        draw_dim_overlay(surface)
        draw_menu_panel(surface, self.panel_rect, "ROCKET GAME", "Main Menu")

        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
            # SOITA HOVER-ÄÄNI KUN HIIRI SIIRTYY NAPIN PÄÄLLE
            if button.is_hovered and button != self.previous_hovered_button:
                if self.sounds:
                    self.sounds.play_sfx("button_hover")
            self.previous_hovered_button = button if button.is_hovered else None
            button.draw(surface)
        
        self.show_score(50, 50, pygame.font.Font(None, 36), surface, filename='leaderboard.json', top_n=5)
        
        self.text_input.handle_event(pygame.event.poll())
        self.text_input.draw(surface)