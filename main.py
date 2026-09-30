"""Application entry point for the 2D racing game."""

import pygame

from game import settings
from game.application import GameApplication


def main():
    pygame.init()
    screen = pygame.display.set_mode(
        (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
    )
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()
    application = GameApplication()
    running = True

    try:
        while running:
            delta_time = clock.tick(settings.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    application.handle_event(event)

            if not running:
                break

            application.update(delta_time)
            application.draw(screen)
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
