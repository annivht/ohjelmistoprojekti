import pygame

try:
    from States.GameState import GameState
    from States.MainMenuState import MainMenuState
    from Valikot.NextLevel import NextLevel
except ModuleNotFoundError:
    import os
    import sys

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from States.GameState import GameState
    from States.MainMenuState import MainMenuState
    from Valikot.NextLevel import NextLevel
    from GameOverState import GameState


class LevelCompleteState(GameState):

    def __init__(self, manager, level_manager=None):
        super().__init__(manager)
        self.level_manager = level_manager
        self.background_surface = manager.screen.copy()
        
        # Get current level number from manager, if available
        current_level = 1 if not level_manager else level_manager.get_current_level_number()
        max_level = 3 if not level_manager else level_manager.num_levels
        next_level = current_level + 1 if current_level < max_level else current_level
        try_again = current_level if current_level <= max_level else max_level
        
        self.next_level_menu = NextLevel(
            current_level=current_level,
            max_level=max_level,
            display_current_level=current_level,
            display_next_level=next_level,
            screen=manager.screen,
            background_surface=self.background_surface,
        )

    def _handle_result(self, result):
        if isinstance(result, int):
            # Next level selected
            if self.level_manager:
                has_next = self.level_manager.next_level()
                if has_next:
                    # Continue with next level
                    from States.PlayState import PlayState
                    self.manager.set_state(PlayState(self.manager, level_manager=self.level_manager))
                    return True
                else:
                    # All levels completed
                    from States.VictoryState import VictoryState
                    self.manager.set_state(VictoryState(self.manager, self.level_manager))
                    return True
            else:
                # Fallback: restart PlayState if no level manager
                from States.PlayState import PlayState
                self.manager.set_state(PlayState(self.manager))
                return True

        if result == "game_completed":
            from States.VictoryState import VictoryState
            self.manager.set_state(VictoryState(self.manager, self.level_manager))
            return True

        if result == "settings":
            try:
                from Valikot.SettingsMenu import main as settings_menu_main
                settings_menu_main()
            except Exception as exc:
                print(f"Could not open settings menu: {exc}")
            return True

        if result == "quit":
            self.manager.running = False
            return True

        return False

    def update(self, events):
        action = self.next_level_menu.handle_events_from(events)
        result = self.next_level_menu.resolve_action(action)

        if self._handle_result(result):
            return

        for event in events:
            # Accept only SPACE or left click as quick continue input.
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                quick_result = self.next_level_menu.resolve_action("next_level")
                self._handle_result(quick_result)
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                quick_result = self.next_level_menu.resolve_action("next_level")
                self._handle_result(quick_result)
                return

    def draw(self, screen):
        self.next_level_menu.draw(screen)