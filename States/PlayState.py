from States.GameState import GameState
import RocketGame

class PlayState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        self.game = RocketGame.Game(manager.screen)

    def update(self, events):
        self.game.update(events)
        if not self.game.running:
            self.manager.running = False

    def draw(self, screen):
        self.game.draw(screen)