"""Application entry point for the 2D racing game."""

import pygame

from game import settings
from game.cars import CARS
from game.race import Race
from game.tracks import TRACKS
from screens.car_select import CarSelectScreen
from screens.track_select import TrackSelectScreen


def main():
    pygame.init()
    screen = pygame.display.set_mode(
        (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
    )
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()
    car_select = CarSelectScreen(CARS)
    track_select = TrackSelectScreen(TRACKS)
    app_state = settings.CAR_SELECTION
    selected_car = None
    race = None
    running = True

    try:
        while running:
            delta_time = clock.tick(settings.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif app_state == settings.CAR_SELECTION:
                    selected_car = car_select.handle_event(event)
                    if selected_car is not None:
                        app_state = settings.TRACK_SELECTION
                elif app_state == settings.TRACK_SELECTION:
                    selected_track = track_select.handle_event(event)
                    if selected_track is not None:
                        race = Race(selected_track, selected_car)
                        app_state = settings.RACE_SCREEN
                else:
                    requested_state = race.handle_event(event)
                    if requested_state == settings.TRACK_SELECTION:
                        race = None
                        app_state = settings.TRACK_SELECTION
                    elif requested_state == settings.CAR_SELECTION:
                        race = None
                        selected_car = None
                        app_state = settings.CAR_SELECTION

            if not running:
                break

            if app_state == settings.CAR_SELECTION:
                car_select.draw(screen)
            elif app_state == settings.TRACK_SELECTION:
                track_select.draw(screen, selected_car)
            elif race is not None:
                race.update(delta_time)
                race.draw(screen)
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
