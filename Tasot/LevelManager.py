"""Multi-level game manager for TITE24 RocketGame.

Coordinates transitions between Level 1-5 (Taso1-Taso5).
Each level is a separate RocketGame.Game instance managing waves and progression.
"""

import os
import sys

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from RocketGame import Game


class LevelManager:
    """Manages multiple game level instances and coordinates progression."""

    def __init__(self, screen, num_levels=5):
        """Initialize level manager with N level instances.

        Args:
            screen: Pygame display surface.
            num_levels: Number of levels to create (default 5 for Taso1-5).
        """
        self.screen = screen
        self.num_levels = num_levels
        self.current_level_index = 0
        self.total_score = 0

        # Create level instances (each Game instance for a level)
        self.levels = [Game(screen, level_number=i + 1) for i in range(num_levels)]

        # Active level reference
        self.current_level = self.levels[self.current_level_index]

        # Game-wide state
        self.game_over = False
        self.all_levels_completed = False

    def _prime_level_timing(self, level):
        """Reset timing after level activation to avoid large first-frame dt."""
        try:
            level.clock.tick(60)
        except Exception:
            pass

        try:
            if level.physics_world is not None:
                level.physics_world.accumulator = 0.0
        except Exception:
            pass

    def next_level(self):
        """Advance to next level.

        Returns:
            bool: True if there's a next level, False if all levels completed.
        """
        # Tallenna nykyisen tason pisteet yhteissaldoon ennen siirtymää
        if hasattr(self.current_level, "pistejarjestelma"):
            self.total_score += int(getattr(self.current_level.pistejarjestelma, "pisteet", 0))

        if self.current_level_index < self.num_levels - 1:
            self.current_level_index += 1
            self.current_level = self.levels[self.current_level_index]
            self._prime_level_timing(self.current_level)

        # Näytä uuden tason pisteinä tähän asti kerätty yhteissaldo
            if hasattr(self.current_level, "pistejarjestelma"):
                self.current_level.pistejarjestelma.pisteet = self.total_score

            return True
        else:
            self.all_levels_completed = True
            return False

    def is_level_complete(self):
        """Check if current level is complete."""
        return getattr(self.current_level, 'level_completed', False)

    def is_game_over(self):
        """Check if current level resulted in game over."""
        return getattr(self.current_level, 'game_over', False)

    def update(self, events):
        """Update current level."""
        self.current_level.update(events)

    def draw(self, target_screen):
        """Draw current level."""
        self.current_level.draw(target_screen)

    def get_current_level_number(self):
        """Get 1-indexed current level number."""
        return self.current_level_index + 1

    def reset_current_level(self):
        """Reset current level to initial state."""
        self.current_level.reset_game()
        self._prime_level_timing(self.current_level)
