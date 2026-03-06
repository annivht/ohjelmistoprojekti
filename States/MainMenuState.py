from states.GameState import GameState
from Valikot.MainMenu import MainMenu
from states.PlayState import PlayState


class MainMenuState(GameState):

    def __init__(self, manager):
        super().__init__(manager)
        self.menu = MainMenu()

    def update(self, events):

        result = self.menu.run()

        if result == "start_game":
            self.manager.set_state(PlayState(self.manager))

    def draw(self, screen):
        pass