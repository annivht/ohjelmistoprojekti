import pygame
import os
from Valikot.menu_style import (
    MenuButton,
    draw_dim_overlay,
    draw_menu_panel,
)

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (52, 78, 91)

class MainMenu:
    """State-friendly main menu that draws to an external surface."""

    def __init__(self):
        if not pygame.get_init():
            pygame.init()

        if not pygame.font.get_init():
            pygame.font.init()

        button_width = 340
        button_height = 78
        button_spacing = 22
        panel_width = 760
        panel_height = 560
        panel_left = SCREEN_WIDTH // 2 - panel_width // 2
        panel_top = SCREEN_HEIGHT // 2 - panel_height // 2
        self.panel_rect = pygame.Rect(panel_left, panel_top, panel_width, panel_height)
        button_width = 300
        button_height = 78
        total_height = 3 * button_height + 2 * button_spacing
        start_y = self.panel_rect.top + 170 + (self.panel_rect.height - 240 - total_height) // 2
        center_x = SCREEN_WIDTH // 2 - button_width // 2

        self.buttons = [
            MenuButton(
                center_x,
                start_y,
                button_width,
                button_height,
                "START GAME",
                action="start",
            ),
            MenuButton(
                center_x,
                start_y + button_height + button_spacing,
                button_width,
                button_height,
                "SETTINGS",
                action="settings",
            ),
            MenuButton(
                center_x,
                start_y + 2 * (button_height + button_spacing),
                button_width,
                button_height,
                "QUIT",
                action="quit",
                variant="danger",
            ),
        ]

        # Menu backdrop: draw scene-like background and translucent veil
        # instead of a flat solid color.
        self.background_image = None
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))
            bg_path = os.path.join(project_root, "images", "taustat", "avaruus.png")
            bg = pygame.image.load(bg_path).convert()
            self.background_image = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            self.background_image = None

    def handle_events(self, events):
        """Handle a frame's events and return selected action or None."""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.buttons:
                    if button.is_clicked(event.pos):
                        return button.action

        return None

    def draw(self, surface):
        if self.background_image is not None:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(DARK_BLUE)
        draw_dim_overlay(surface)
        draw_menu_panel(surface, self.panel_rect, "ROCKET GAME", "Main Menu")

        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
            button.draw(surface)
