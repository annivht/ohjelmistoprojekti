from States.GameState import GameState
import pygame
from Tasot.LevelManager import LevelManager


class PlayState(GameState):
    def __init__(self, manager, level_manager=None):
        super().__init__(manager)
        # Accept external level_manager or create new one
        self.level_manager = level_manager if level_manager else LevelManager(manager.screen)
        # Expose level_manager on the manager so other states can reuse it
        self.manager.level_manager = self.level_manager

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                from States.PauseState import PauseState
                background = self.manager.screen.copy()
                self.manager.set_state(PauseState(self.manager, self, background_surface=background))
                return

        self.level_manager.update(events)

        # Check if current level is complete
        if self.level_manager.is_level_complete():
            from States.LevelCompleteState import LevelCompleteState
            self.manager.set_state(LevelCompleteState(self.manager, self.level_manager))
            return

        # Check if current level resulted in game over.
        # The level itself handles a short death animation delay before setting game_over=True.
        if self.level_manager.is_game_over():
            from States.GameOverState import GameOverState
            self.manager.set_state(GameOverState(self.manager))
            return

    def draw(self, screen):
        screen.fill((0, 0, 0))
        self.level_manager.draw(screen)