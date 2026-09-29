"""Persistent fixed-speed opponent cars."""

import pygame

from game import settings


class Opponent:
    """A fixed-speed Step 6 race opponent."""

    def __init__(
        self, identifier, lane, start_y, speed, color, accent_color
    ):
        self.identifier = identifier
        self.lane = lane
        self.x = settings.ROAD_LEFT + settings.LANE_WIDTH * (lane + 0.5)
        self.y = start_y
        self.speed = speed
        self.distance = (
            settings.PLAYER_Y - start_y
        ) / settings.RELATIVE_MOTION_SCALE
        self.color = color
        self.accent_color = accent_color
        self.finished = False
        self.finish_time = None
        self.finish_position = None

    def update_distance(self, delta_time):
        if not self.finished:
            self.distance += self.speed * delta_time

    def update_screen_position(self, camera_distance):
        distance_difference = self.distance - camera_distance
        self.y = (
            settings.PLAYER_Y
            - distance_difference * settings.RELATIVE_MOTION_SCALE
        )

    def is_visible(self):
        return (
            not self.finished
            and -settings.OPPONENT_HEIGHT - 20
            <= self.y
            <= settings.SCREEN_HEIGHT + 20
        )

    def get_hitbox(self):
        """Return a fair collision rectangle centered within the car body."""
        return pygame.Rect(
            round(self.x - settings.OPPONENT_HITBOX_WIDTH / 2),
            round(
                self.y
                + (
                    settings.OPPONENT_HEIGHT
                    - settings.OPPONENT_HITBOX_HEIGHT
                )
                / 2
            ),
            settings.OPPONENT_HITBOX_WIDTH,
            settings.OPPONENT_HITBOX_HEIGHT,
        )

    def draw(self, surface):
        """Draw the existing compact race-car design."""
        car_center_x = round(self.x)
        car_top = round(self.y)
        car_left = car_center_x - settings.OPPONENT_WIDTH // 2

        wheel_width = 9
        wheel_height = 25
        for wheel_x in (
            car_left - 4,
            car_left + settings.OPPONENT_WIDTH - 5,
        ):
            pygame.draw.rect(
                surface,
                settings.BLACK,
                (wheel_x, car_top + 20, wheel_width, wheel_height),
                border_radius=3,
            )
            pygame.draw.rect(
                surface,
                settings.BLACK,
                (wheel_x, car_top + 74, wheel_width, wheel_height),
                border_radius=3,
            )

        body_points = [
            (car_center_x - 19, car_top),
            (car_center_x + 19, car_top),
            (car_left + settings.OPPONENT_WIDTH, car_top + 24),
            (
                car_left + settings.OPPONENT_WIDTH - 3,
                car_top + settings.OPPONENT_HEIGHT - 13,
            ),
            (car_center_x + 22, car_top + settings.OPPONENT_HEIGHT),
            (car_center_x - 22, car_top + settings.OPPONENT_HEIGHT),
            (car_left + 3, car_top + settings.OPPONENT_HEIGHT - 13),
            (car_left, car_top + 24),
        ]
        pygame.draw.polygon(surface, self.color, body_points)
        pygame.draw.polygon(surface, settings.BLACK, body_points, width=2)

        pygame.draw.rect(
            surface,
            self.accent_color,
            (
                car_center_x - 4,
                car_top + 5,
                8,
                settings.OPPONENT_HEIGHT - 15,
            ),
        )
        pygame.draw.polygon(
            surface,
            settings.WINDOW_COLOR,
            [
                (car_center_x - 19, car_top + 34),
                (car_center_x + 19, car_top + 34),
                (car_center_x + 23, car_top + 57),
                (car_center_x - 23, car_top + 57),
            ],
        )
        pygame.draw.polygon(
            surface,
            settings.WINDOW_COLOR,
            [
                (car_center_x - 22, car_top + 64),
                (car_center_x + 22, car_top + 64),
                (car_center_x + 18, car_top + 83),
                (car_center_x - 18, car_top + 83),
            ],
        )
        pygame.draw.rect(
            surface,
            self.accent_color,
            (
                car_left - 3,
                car_top + settings.OPPONENT_HEIGHT - 13,
                settings.OPPONENT_WIDTH + 6,
                7,
            ),
            border_radius=2,
        )
        pygame.draw.rect(
            surface, settings.BLACK, (car_left - 3, car_top + 10, 10, 5)
        )
        pygame.draw.rect(
            surface,
            settings.BLACK,
            (car_left + settings.OPPONENT_WIDTH - 7, car_top + 10, 10, 5),
        )


def create_opponents():
    """Create the unchanged three-car Step 6 starting formation."""
    opponent_specs = [
        ("BLUE", 0, 445.0, 125.0, (45, 143, 207), (225, 240, 248)),
        ("GOLD", 1, 330.0, 155.0, (224, 164, 43), (75, 51, 14)),
        ("PURPLE", 2, 445.0, 140.0, (137, 83, 190), (236, 224, 247)),
    ]
    return [Opponent(*spec) for spec in opponent_specs]
