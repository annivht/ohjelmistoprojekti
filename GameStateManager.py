class GameStateManager:

    def __init__(self):
        self.state = None

    def set_state(self, new_state):
        self.state = new_state

    def update(self, events):
        if self.state:
            self.state.update(events)

    def draw(self, screen):
        if self.state:
            self.state.draw(screen)