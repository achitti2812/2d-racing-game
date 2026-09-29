"""Application entry point for the 2D racing game."""

import pygame

from game import settings
from game.race import Race
from game.tracks import TRACKS
from screens.track_select import TrackSelectScreen


def main():
    pygame.init()
    screen = pygame.display.set_mode(
        (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
    )
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()
    track_select = TrackSelectScreen(TRACKS)
    race = None
    running = True

    try:
        while running:
            delta_time = clock.tick(settings.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif race is None:
                    selected_track = track_select.handle_event(event)
                    if selected_track is not None:
                        race = Race(selected_track)
                else:
                    requested_state = race.handle_event(event)
                    if requested_state == settings.TRACK_SELECTION:
                        race = None

            if not running:
                break

            if race is None:
                track_select.draw(screen)
            else:
                race.update(delta_time)
                race.draw(screen)
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
