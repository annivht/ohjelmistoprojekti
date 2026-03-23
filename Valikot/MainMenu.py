import pygame
import os

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (52, 78, 91)
LIGHT_BLUE = (100, 150, 200)
HOVER_COLOR = (150, 200, 255)

title_font = None
button_font = None
small_font = None

class Button:
    """Simple UI button used by the main menu."""

    def __init__(self, x, y, width, height, text, color, text_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.action = action
        self.is_hovered = False

    def draw(self, surface):
        current_color = HOVER_COLOR if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=10)

        text_surface = button_font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def update(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

class MainMenu:
    """State-friendly main menu that draws to an external surface."""

    def __init__(self):
        global title_font, button_font, small_font

        if not pygame.get_init():
            pygame.init()

        if not pygame.font.get_init():
            pygame.font.init()

        title_font = pygame.font.Font(None, 80)
        button_font = pygame.font.Font(None, 50)
        small_font = pygame.font.Font(None, 30)

        button_width = 300
        button_height = 80
        button_spacing = 30
        total_height = 3 * button_height + 2 * button_spacing
        start_y = SCREEN_HEIGHT // 2 - total_height // 2 + 40

        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - button_width // 2,
                start_y,
                button_width,
                button_height,
                "START GAME",
                LIGHT_BLUE,
                WHITE,
                action="start",
            ),
            Button(
                SCREEN_WIDTH // 2 - button_width // 2,
                start_y + button_height + button_spacing,
                button_width,
                button_height,
                "SETTINGS",
                LIGHT_BLUE,
                WHITE,
                action="settings",
            ),
            Button(
                SCREEN_WIDTH // 2 - button_width // 2,
                start_y + 2 * (button_height + button_spacing),
                button_width,
                button_height,
                "QUIT",
                LIGHT_BLUE,
                WHITE,
                action="quit",
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

        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 120))

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
        surface.blit(self.overlay, (0, 0))

        title_surface = title_font.render("ROCKET GAME", True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 180))
        surface.blit(title_surface, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
            button.draw(surface)
