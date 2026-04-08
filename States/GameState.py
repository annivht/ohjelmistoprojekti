class GameState:

    def __init__(self, manager):
        self.manager = manager

    def on_enter(self):
        """KUTSUTAAN KUN TILAAN SIIRRYTÄÄN - OVERRIDE ALATILUOKISSA"""
        pass

    def update(self, events):
        pass

    def draw(self, screen):
        pass