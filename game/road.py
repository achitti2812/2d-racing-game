"""Road, terrain, scrolling markings, and checkered race lines."""

import pygame

from game import settings


def world_distance_to_screen_y(world_distance, camera_distance):
    """Convert a fixed world distance into its vertical screen position."""
    return settings.PLAYER_Y - (
        world_distance - camera_distance
    ) * settings.RELATIVE_MOTION_SCALE


class Road:
    """Own the scrolling road offset and all road-related drawing."""

    def __init__(self):
        self.dash_offset = 0.0

    def update(self, player_speed, delta_time):
        dash_cycle = settings.DASH_HEIGHT + settings.DASH_GAP
        road_scroll_speed = player_speed * settings.ROAD_SCROLL_MULTIPLIER
        self.dash_offset = (
            self.dash_offset + road_scroll_speed * delta_time
        ) % dash_cycle

    def draw(self, surface, camera_distance):
        self._draw_terrain(surface)
        self._draw_highway(surface)
        self._draw_race_lines(surface, camera_distance)

    def _draw_terrain(self, surface):
        surface.fill(settings.TERRAIN_COLOR)

        stripe_width = 24
        for x in range(0, settings.ROAD_LEFT, stripe_width * 2):
            pygame.draw.rect(
                surface,
                settings.TERRAIN_STRIPE_COLOR,
                (x, 0, stripe_width, settings.SCREEN_HEIGHT),
            )
        for x in range(
            settings.ROAD_RIGHT, settings.SCREEN_WIDTH, stripe_width * 2
        ):
            pygame.draw.rect(
                surface,
                settings.TERRAIN_STRIPE_COLOR,
                (x, 0, stripe_width, settings.SCREEN_HEIGHT),
            )

    def _draw_highway(self, surface):
        pygame.draw.rect(
            surface,
            settings.ROAD_SHOULDER_COLOR,
            (
                settings.ROAD_LEFT - 12,
                0,
                12,
                settings.SCREEN_HEIGHT,
            ),
        )
        pygame.draw.rect(
            surface,
            settings.ROAD_COLOR,
            (
                settings.ROAD_LEFT,
                0,
                settings.ROAD_WIDTH,
                settings.SCREEN_HEIGHT,
            ),
        )
        pygame.draw.rect(
            surface,
            settings.ROAD_SHOULDER_COLOR,
            (settings.ROAD_RIGHT, 0, 12, settings.SCREEN_HEIGHT),
        )

        pygame.draw.line(
            surface,
            settings.WHITE,
            (settings.ROAD_LEFT, 0),
            (settings.ROAD_LEFT, settings.SCREEN_HEIGHT),
            settings.EDGE_LINE_WIDTH,
        )
        pygame.draw.line(
            surface,
            settings.WHITE,
            (settings.ROAD_RIGHT, 0),
            (settings.ROAD_RIGHT, settings.SCREEN_HEIGHT),
            settings.EDGE_LINE_WIDTH,
        )

        dash_cycle = settings.DASH_HEIGHT + settings.DASH_GAP
        for divider_number in (1, 2):
            divider_x = (
                settings.ROAD_LEFT
                + settings.LANE_WIDTH * divider_number
            )
            dash_y = -dash_cycle + self.dash_offset

            while dash_y < settings.SCREEN_HEIGHT:
                pygame.draw.rect(
                    surface,
                    settings.WHITE,
                    (
                        divider_x - settings.LANE_LINE_WIDTH // 2,
                        int(dash_y),
                        settings.LANE_LINE_WIDTH,
                        settings.DASH_HEIGHT,
                    ),
                )
                dash_y += dash_cycle

    def _draw_race_lines(self, surface, camera_distance):
        start_line_y = world_distance_to_screen_y(
            settings.START_LINE_DISTANCE, camera_distance
        )
        finish_line_y = world_distance_to_screen_y(
            settings.RACE_DISTANCE, camera_distance
        )
        self._draw_checkered_line(surface, start_line_y)
        self._draw_checkered_line(surface, finish_line_y)

    def _draw_checkered_line(self, surface, center_y):
        line_height = settings.CHECKER_SIZE * settings.CHECKER_ROWS
        line_top = round(center_y - line_height / 2)
        if (
            line_top > settings.SCREEN_HEIGHT
            or line_top + line_height < 0
        ):
            return

        column_count = (
            settings.ROAD_WIDTH + settings.CHECKER_SIZE - 1
        ) // settings.CHECKER_SIZE
        for row in range(settings.CHECKER_ROWS):
            for column in range(column_count):
                square_x = (
                    settings.ROAD_LEFT + column * settings.CHECKER_SIZE
                )
                square_width = min(
                    settings.CHECKER_SIZE,
                    settings.ROAD_RIGHT - square_x,
                )
                square_color = (
                    settings.WHITE
                    if (row + column) % 2 == 0
                    else settings.BLACK
                )
                pygame.draw.rect(
                    surface,
                    square_color,
                    (
                        square_x,
                        line_top + row * settings.CHECKER_SIZE,
                        square_width,
                        settings.CHECKER_SIZE,
                    ),
                )

        pygame.draw.rect(
            surface,
            settings.WHITE,
            (
                settings.ROAD_LEFT,
                line_top,
                settings.ROAD_WIDTH,
                line_height,
            ),
            width=1,
        )
