import pygame
import sys

# Näytön asetukset
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800

# Värit
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (52, 78, 91)
LIGHT_BLUE = (100, 150, 200)
HOVER_COLOR = (150, 200, 255)

# Fontit
title_font = None
button_font = None
small_font = None


class Button:
    """Nappi-luokka päämenutille"""
    
    def __init__(self, x, y, width, height, text, color, text_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.action = action
        self.is_hovered = False
    
    def draw(self, surface):
        """Piirtää napin"""
        # Vaihda väri hover-tilassa
        current_color = HOVER_COLOR if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=10)
        
        # Piirtää teksti napin päälle
        text_surf = button_font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def is_clicked(self, pos):
        """Tarkistaa onko nappia klikattu"""
        return self.rect.collidepoint(pos)
    
    def update(self, pos):
        """Päivittää hover-tilan"""
        self.is_hovered = self.rect.collidepoint(pos)


class MainMenu:
    """Päämenun hallinta"""
    
    def __init__(self):
        global title_font, button_font, small_font

        # init vain jos ei ole jo initattu
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Rocket Game - Main Menu")

        # fontit vasta nyt
        title_font = pygame.font.Font(None, 80)
        button_font = pygame.font.Font(None, 50)
        small_font = pygame.font.Font(None, 30)

        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 100, 300, 80, "START GAME", LIGHT_BLUE, WHITE, action="start"),
            Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 20,  300, 80, "SETTINGS",   LIGHT_BLUE, WHITE, action="settings"),
            Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 140, 300, 80, "QUIT",       LIGHT_BLUE, WHITE, action="quit"),
        ]
        self.clock = pygame.time.Clock()
        self.running = True
    
    def handle_events(self):
        """Käsittelee näppäimistö ja hiiri-eventit"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in self.buttons:
                    if button.is_clicked(mouse_pos):
                        return button.action
        
        return None
    
    def draw(self):
        """Piirtää menun"""
        self.screen.fill(DARK_BLUE)
        
        # Piirtää otsikko
        title_surf = title_font.render("ROCKET GAME", True, WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_surf, title_rect)
        
        # Piirtää napit
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
            button.draw(self.screen)
        
        pygame.display.update()
    
    def run(self):
        """Pääsilmukka"""
        while self.running:
            action = self.handle_events()
            
            if action == "start":
                print("Peli käynnistyy...")
                return "start_game"
            elif action == "settings":
                print("Asetukset avautuvat...")
                # Tähän tulee settings-screen myöhemmin
            elif action == "quit":
                print("Peli suljetaan...")
                return "quit"
            
            self.draw()
            self.clock.tick(60)
        
        return "quit"