import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pygame
from Valikot.SettingsMenu import main as settings_menu_main


# Oletusnäytön asetukset (käytetään vain koordinaatteihin, ei luoda uutta ikkunaa)
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800

# Värit
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (52, 78, 91)
LIGHT_BLUE = (100, 150, 200)
HOVER_COLOR = (150, 200, 255)
SEMI_TRANSPARENT = (0, 0, 0, 150)

# Fontit
title_font = pygame.font.Font(None, 80)
button_font = pygame.font.Font(None, 50)


class Button:
    """Nappi-luokka pauseluokalle"""
    
    def __init__(self, x, y, width, height, text, color, text_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.action = action
        self.is_hovered = False
    
    def draw(self, surface):
        """Piirtää napin"""
        current_color = HOVER_COLOR if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=10)
        
        text_surf = button_font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def is_clicked(self, pos):
        """Tarkistaa onko nappia klikattu"""
        return self.rect.collidepoint(pos)
    
    def update(self, pos):
        """Päivittää hover-tilan"""
        self.is_hovered = self.rect.collidepoint(pos)


class PauseMenu:
    """Pausemenun hallinta"""
    
    def __init__(self, screen=None):
        self.screen = screen
        # Nappien asettelu: spacing ja keskitys, Quit aina alimmaiseksi
        button_width = 300
        button_height = 80
        button_spacing = 30
        # Continue ylös, Settings keskelle, Quit aivan alas
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        continue_y = SCREEN_HEIGHT // 2 - button_height - button_spacing // 2
        quit_y = SCREEN_HEIGHT // 2 + button_spacing // 2
        settings_y = SCREEN_HEIGHT - button_height - 80  # 80px marginaali alareunasta
        self.buttons = [
            Button(center_x, continue_y, button_width, button_height, "Continue", (46, 163, 67), WHITE, action="continue"),
            Button(center_x, quit_y, button_width, button_height, "Settings", (70, 85, 170), WHITE, action="settings"),
            Button(center_x, settings_y, button_width, button_height, "Quit", (163, 67, 67), WHITE, action="quit"),
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
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        # Piirrä otsikko keskelle
        title_surf = title_font.render("PAUSED", True, WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 180))
        screen.blit(title_surf, title_rect)
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
