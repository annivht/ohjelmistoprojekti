import pygame
from display_settings import load_display_settings


class GameStateManager:

    def __init__(self, initial_state):
        pygame.init()

        display = load_display_settings()
        flags = pygame.FULLSCREEN if display.get("fullscreen", False) else 0
        self.screen = pygame.display.set_mode((display["width"], display["height"]), flags)
        pygame.display.set_caption("Rocket Game")

        self.clock = pygame.time.Clock()
        self.running = True
        self.level_manager = None

        self.state = initial_state
        self.state.manager = self

    def set_state(self, new_state):
        """Vaihtaa pelitilan"""
        self.state = new_state
        self.state.manager = self

    def run(self):
        """Pelin pääsilmukka"""

        while self.running:
            current_surface = pygame.display.get_surface()
            if current_surface is not None and current_surface != self.screen:
                self.screen = current_surface

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            # Päivitä state
            if self.state:
                self.state.update(events)

            # Piirrä state
            if self.state:
                self.state.draw(self.screen)

            pygame.display.flip()

            self.clock.tick(60)

        pygame.quit()