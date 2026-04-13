from States.GameState import GameState
from Valikot.VictoryScreen import VictoryScreen


class VictoryState(GameState):
    def __init__(self, manager, level_manager=None):
        super().__init__(manager)
        self.level_manager = level_manager
        self.background_surface = manager.screen.copy()
        self.victory_screen = VictoryScreen(
            manager.screen,
            background_surface=self.background_surface,
            sounds=getattr(manager, "sounds", None),
        )

    def on_enter(self):
        sounds = getattr(self.manager, "sounds", None)
        if sounds is not None:
            sounds.stop_music(fadeout_ms=250)
            sounds.play_music("pedro-pedro", loops=-1)

    def update(self, events):
        action = self.victory_screen.handle_events_from(events)
        if action == "quit":
            self.manager.running = False
            return

        self.victory_screen.update()

    def draw(self, screen):
        self.victory_screen.draw(screen)