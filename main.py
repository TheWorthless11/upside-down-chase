"""Main entry point for Upside Down: Tactical Escape."""

import pygame

from game import Game


def main():
    """Initialize and run the game."""
    pygame.init()
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
    except pygame.error:
        pass

    game = Game()
    game.run()


if __name__ == "__main__":
    main()
