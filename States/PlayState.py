from states.GameState import GameState
import RocketGame

class PlayState(GameState):

    def __init__(self, manager):
        super().__init__(manager)

        # käynnistä peli
        self.game = RocketGame.Game()

    def update(self, events):
        self.game.update(events)

    def draw(self, screen):
        self.game.draw(screen)