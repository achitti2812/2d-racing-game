"""Curved road, terrain, lane markings, and checkered race lines."""

import pygame

from game import settings
from game.scenery import TrackScenery


class Road:
    """Draw the road by sampling one shared deterministic Track."""

    def __init__(self, track):
        self.track = track
        self.scenery = TrackScenery(track)

    def draw(self, surface, camera_distance):
        self._draw_terrain(surface)
        samples = self._make_road_samples(camera_distance)
        self._draw_highway(surface, samples)
        self._draw_lane_markings(surface, camera_distance)
        self._draw_race_lines(surface, camera_distance)
        self.scenery.draw(surface, camera_distance)

    def crowd_intensity_at(self, world_distance):
        return self.scenery.crowd_intensity_at(world_distance)

    def _draw_terrain(self, surface):
        surface.fill(self.track.config.terrain_color)

        stripe_width = 24
        for x in range(0, settings.SCREEN_WIDTH, stripe_width * 2):
            pygame.draw.rect(
                surface,
                self.track.config.terrain_stripe_color,
                (x, 0, stripe_width, settings.SCREEN_HEIGHT),
            )

    def _make_road_samples(self, camera_distance):
        """Sample road edges from just above to just below the window."""
        samples = []
        sample_height = settings.ROAD_SAMPLE_HEIGHT
        for screen_y in range(
            -sample_height,
            settings.SCREEN_HEIGHT + sample_height * 2,
            sample_height,
        ):
            world_distance = self.track.screen_y_to_world_distance(
                screen_y, camera_distance
            )
            left_x, right_x = self.track.get_boundaries(world_distance)
            samples.append((screen_y, left_x, right_x))
        return samples

    def _draw_highway(self, surface, samples):
        shoulder_width = settings.ROAD_SHOULDER_WIDTH
        for first, second in zip(samples, samples[1:]):
            y1, left1, right1 = first
            y2, left2, right2 = second
            pygame.draw.polygon(
                surface,
                self.track.config.shoulder_color,
                [
                    (left1 - shoulder_width, y1),
                    (right1 + shoulder_width, y1),
                    (right2 + shoulder_width, y2),
                    (left2 - shoulder_width, y2),
                ],
            )
            pygame.draw.polygon(
                surface,
                settings.ROAD_COLOR,
                [(left1, y1), (right1, y1), (right2, y2), (left2, y2)],
            )

        left_edge = [(round(left), y) for y, left, _ in samples]
        right_edge = [(round(right), y) for y, _, right in samples]
        pygame.draw.lines(
            surface, settings.WHITE, False, left_edge, settings.EDGE_LINE_WIDTH
        )
        pygame.draw.lines(
            surface, settings.WHITE, False, right_edge, settings.EDGE_LINE_WIDTH
        )

    def _draw_lane_markings(self, surface, camera_distance):
        """Draw moving dash segments whose X positions follow the centerline."""
        dash_cycle = settings.DASH_HEIGHT + settings.DASH_GAP
        dash_offset = (
            camera_distance * settings.RELATIVE_MOTION_SCALE
        ) % dash_cycle

        for lane_offset in (-settings.LANE_WIDTH / 2, settings.LANE_WIDTH / 2):
            dash_y = -dash_cycle + dash_offset
            while dash_y < settings.SCREEN_HEIGHT:
                dash_end = min(
                    dash_y + settings.DASH_HEIGHT,
                    settings.SCREEN_HEIGHT + settings.ROAD_SAMPLE_HEIGHT,
                )
                points = []
                point_y = dash_y
                while point_y < dash_end:
                    world_distance = self.track.screen_y_to_world_distance(
                        point_y, camera_distance
                    )
                    points.append(
                        (
                            round(
                                self.track.get_center_x(world_distance)
                                + lane_offset
                            ),
                            round(point_y),
                        )
                    )
                    point_y += settings.ROAD_SAMPLE_HEIGHT

                world_distance = self.track.screen_y_to_world_distance(
                    dash_end, camera_distance
                )
                points.append(
                    (
                        round(
                            self.track.get_center_x(world_distance)
                            + lane_offset
                        ),
                        round(dash_end),
                    )
                )
                if len(points) >= 2:
                    pygame.draw.lines(
                        surface,
                        settings.WHITE,
                        False,
                        points,
                        settings.LANE_LINE_WIDTH,
                    )
                dash_y += dash_cycle

    def _draw_race_lines(self, surface, camera_distance):
        start_line_y = self.track.world_distance_to_screen_y(
            settings.START_LINE_DISTANCE, camera_distance
        )
        finish_line_y = self.track.world_distance_to_screen_y(
            self.track.race_distance, camera_distance
        )
        self._draw_checkered_line(
            surface, start_line_y, settings.START_LINE_DISTANCE
        )
        self._draw_checkered_line(
            surface, finish_line_y, self.track.race_distance
        )

    def _draw_checkered_line(self, surface, center_y, world_distance):
        line_height = settings.CHECKER_SIZE * settings.CHECKER_ROWS
        line_top = round(center_y - line_height / 2)
        if line_top > settings.SCREEN_HEIGHT or line_top + line_height < 0:
            return

        road_left, road_right = self.track.get_boundaries(world_distance)
        road_left = round(road_left)
        road_right = round(road_right)
        column_count = (
            settings.ROAD_WIDTH + settings.CHECKER_SIZE - 1
        ) // settings.CHECKER_SIZE
        for row in range(settings.CHECKER_ROWS):
            for column in range(column_count):
                square_x = road_left + column * settings.CHECKER_SIZE
                square_width = min(
                    settings.CHECKER_SIZE,
                    road_right - square_x,
                )
                if square_width <= 0:
                    continue
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
            (road_left, line_top, settings.ROAD_WIDTH, line_height),
            width=1,
        )
