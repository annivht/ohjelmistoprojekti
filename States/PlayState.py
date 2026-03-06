from States.GameState import GameState
import RocketGame

class PlayState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        RocketGame.init()

    def update(self, events):
        RocketGame.update(events)
        if not RocketGame.is_running():
            self.manager.running = False

    def draw(self, screen):
        RocketGame.draw(screen)