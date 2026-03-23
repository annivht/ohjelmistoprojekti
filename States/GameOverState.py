import pygame
from States.GameState import GameState
from States.MainMenuState import MainMenuState
from Valikot.gameOver import GameOverScreen

class GameOverState(GameState):

    def __init__(self, manager):
        super().__init__(manager)
        self.background_surface = manager.screen.copy()
        self.game_over_screen = GameOverScreen(manager.screen)

    def update(self, events):
        for event in events:
            result = self.game_over_screen.handle_event(event)

            if result == "TRY AGAIN":
                from States.PlayState import PlayState
                self.manager.set_state(PlayState(self.manager))
                return

            if result == "MAIN MENU":
                self.manager.set_state(MainMenuState(self.manager))
                return

            if result == "QUIT":
                self.manager.running = False
                return

            if event.type == pygame.KEYDOWN:
                # Pidä vanha fallback: mikä tahansa näppäin palaa valikkoon.
                self.manager.set_state(MainMenuState(self.manager))
                return

    def draw(self, screen):
        w, h = screen.get_size()
        self.game_over_screen.show(w, h, overlay=True, background_surface=self.background_surface)