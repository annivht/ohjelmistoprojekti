import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pygame
from Valikot.SettingsMenu import main as settings_menu_main
from Valikot.menu_style import MenuButton, draw_dim_overlay, draw_menu_panel


# Oletusnäytön asetukset (käytetään vain koordinaatteihin, ei luoda uutta ikkunaa)
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800

DARK_BLUE = (52, 78, 91)


class PauseMenu:
    """Pausemenun hallinta"""
    
    def __init__(self, screen=None):
        self.screen = screen
        panel_width = 760
        panel_height = 560
        self.panel_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - panel_width // 2,
            SCREEN_HEIGHT // 2 - panel_height // 2,
            panel_width,
            panel_height,
        )
        button_width = 300
        button_height = 78
        button_spacing = 22
        total_height = 3 * button_height + 2 * button_spacing
        start_y = self.panel_rect.top + 170 + (self.panel_rect.height - 240 - total_height) // 2
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        self.buttons = [
            MenuButton(center_x, start_y, button_width, button_height, "CONTINUE", action="continue", variant="success"),
            MenuButton(center_x, start_y + button_height + button_spacing, button_width, button_height, "SETTINGS", action="settings"),
            MenuButton(center_x, start_y + 2 * (button_height + button_spacing), button_width, button_height, "QUIT", action="quit", variant="danger"),
        ]
        self.clock = pygame.time.Clock()
        self.running = True

    def handle_events_from(self, events):
        """Käsittelee valmiiksi annetut eventit (state-driven käyttö)."""
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "continue"

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in self.buttons:
                    if button.is_clicked(mouse_pos):
                        return button.action

        return None

    def resolve_action(self, action):
        if action == "continue":
            return "continue"
        if action == "settings":
            settings_menu_main()
            return None
        if action == "quit":
            return "quit"
        return None
    
    def handle_events(self):
        """Käsittelee näppäimistö ja hiiri-eventit"""
        return self.handle_events_from(pygame.event.get())
    
    def draw(self, background_surface=None):
        """Piirtää pausemenun"""
        screen = self.screen if self.screen is not None else pygame.display.get_surface()
        if background_surface is not None and isinstance(background_surface, pygame.Surface):
            try:
                screen.blit(background_surface, (0, 0))
            except Exception:
                # Fall back to a solid fill if the cached background surface is stale.
                screen.fill(DARK_BLUE)
        else:
            screen.fill(DARK_BLUE)
        draw_dim_overlay(screen)
        draw_menu_panel(screen, self.panel_rect, "PAUSED", "Game is paused")
        # Piirrä napit
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
            button.draw(screen)
        if self.screen is None:
            pygame.display.update()
    
    def run(self, background_surface):
        #print("PauseMenu.run() called")        #vian etsintä
        """Pääsilmukka pauselle"""
        while self.running:
            action = self.handle_events()
            result = self.resolve_action(action)
            if result is not None:
                return result
            
            self.draw(background_surface)
            self.clock.tick(60)
        
        return "continue"
