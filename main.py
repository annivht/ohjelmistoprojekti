"""
Pelin entry point
Käyttää GameStateManageria hallitsemaan pelitiloja
"""

import pygame
import sys
import os

# Lisää ohjelmiston hakemisto Python-polkuun
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from GameStateManager import GameStateManager
from states.MainMenuState import MainMenuState


def main():

    pygame.init()

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Rocket Game")

    clock = pygame.time.Clock()

    # Luo state manager
    manager = GameStateManager()

    # Aloita päävalikosta
    manager.set_state(MainMenuState(manager))

    running = True

    while running:

        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        manager.update(events)

        screen.fill((0,0,0))
        manager.draw(screen)

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()