"""Deterministic trackside crowds, safety furniture, and race signage."""

from dataclasses import dataclass
import random

import pygame

from game import settings


SHIRT_COLORS = (
    (238, 77, 66),
    (58, 166, 224),
    (250, 190, 65),
    (104, 207, 126),
    (179, 101, 216),
    (235, 235, 225),
)
BANNER_WORDS = ("RACING", "BOOST", "TURBO", "APEX", "SPEED", "RACEWAY")


@dataclass(frozen=True)
class CrowdZone:
    start_distance: float
    end_distance: float
    density: float


@dataclass(frozen=True)
class Spectator:
    world_distance: float
    side: int
    lateral_offset: float
    shirt_color: tuple
    activity_phase: int


@dataclass(frozen=True)
class Chevron:
    world_distance: float
    side: int
    direction: int


class TrackScenery:
    """Cache track-specific visual atmosphere and filter it by camera range."""

    def __init__(self, track):
        self.track = track
        seed = sum((index + 1) * ord(char) for index, char in enumerate(track.id))
        self.random_source = random.Random(seed)
        self.crowd_zones = self._build_crowd_zones()
        self.spectators = tuple(self._generate_spectators())
        self.chevrons = tuple(self._generate_chevrons())
        self.banner_font = pygame.font.Font(None, 15)
        self.gantry_font = pygame.font.Font(None, 20)

    def _build_crowd_zones(self):
        distance = self.track.race_distance
        return (
            CrowdZone(0.0, min(850.0, distance), 1.0),
            CrowdZone(distance * 0.27, distance * 0.27 + 430.0, 0.58),
            CrowdZone(distance * 0.53, distance * 0.53 + 480.0, 0.64),
            CrowdZone(distance * 0.76, distance * 0.76 + 400.0, 0.55),
            CrowdZone(max(0.0, distance - 850.0), distance, 1.0),
        )

    def _generate_spectators(self):
        half_road = settings.ROAD_WIDTH / 2
        minimum_offset = (
            half_road
            + settings.ROAD_SHOULDER_WIDTH
            + settings.SPECTATOR_SAFETY_GAP
        )
        spectators = []
        for zone in self.crowd_zones:
            spacing = settings.SCENERY_SAMPLE_SPACING / zone.density
            distance = zone.start_distance + self.random_source.uniform(0, spacing)
            while distance <= min(zone.end_distance, self.track.race_distance):
                for side in (-1, 1):
                    if self.random_source.random() <= 0.55 + zone.density * 0.35:
                        spectators.append(
                            Spectator(
                                world_distance=distance
                                + self.random_source.uniform(-5.0, 5.0),
                                side=side,
                                lateral_offset=minimum_offset
                                + self.random_source.uniform(5.0, 42.0),
                                shirt_color=self.random_source.choice(SHIRT_COLORS),
                                activity_phase=self.random_source.randrange(6),
                            )
                        )
                distance += spacing
        return spectators

    def _generate_chevrons(self):
        chevrons = []
        distance = 500.0
        while distance < self.track.race_distance - 450.0:
            strength = self.track.get_curve_strength(distance)
            if abs(strength) >= 0.16:
                direction = 1 if strength > 0.0 else -1
                outside_side = -direction
                chevrons.append(Chevron(distance, outside_side, direction))
                distance += 180.0
            else:
                distance += 130.0
        return chevrons

    def visible_spectators(self, camera_distance):
        margin = settings.SPECTATOR_VISIBLE_MARGIN
        return tuple(
            spectator
            for spectator in self.spectators
            if -margin
            <= self.track.world_distance_to_screen_y(
                spectator.world_distance, camera_distance
            )
            <= settings.SCREEN_HEIGHT + margin
        )

    def crowd_intensity_at(self, world_distance):
        intensity = 0.0
        for zone in self.crowd_zones:
            if zone.start_distance <= world_distance <= zone.end_distance:
                center = (zone.start_distance + zone.end_distance) / 2
                half_width = max(1.0, (zone.end_distance - zone.start_distance) / 2)
                edge_fade = max(0.3, 1.0 - abs(world_distance - center) / half_width)
                intensity = max(intensity, zone.density * edge_fade)
        return intensity

    def draw(self, surface, camera_distance):
        self._draw_spectators(surface, camera_distance)
        self._draw_barriers(surface, camera_distance)
        self._draw_banners(surface, camera_distance)
        self._draw_chevrons(surface, camera_distance)
        self._draw_gantry(
            surface,
            camera_distance,
            settings.START_LINE_DISTANCE,
            "2D RACING",
            (47, 194, 228),
        )
        self._draw_gantry(
            surface,
            camera_distance,
            self.track.race_distance,
            "FINISH",
            (246, 201, 68),
        )

    def _draw_spectators(self, surface, camera_distance):
        activity_tick = int(camera_distance / 12.0)
        for spectator in self.visible_spectators(camera_distance):
            y = round(
                self.track.world_distance_to_screen_y(
                    spectator.world_distance, camera_distance
                )
            )
            center = self.track.get_center_x(spectator.world_distance)
            x = round(center + spectator.side * spectator.lateral_offset)
            if not -10 <= x <= settings.SCREEN_WIDTH + 10:
                continue
            cheering = (activity_tick + spectator.activity_phase) % 6 < 2
            pygame.draw.circle(surface, (224, 180, 145), (x, y - 5), 3)
            pygame.draw.rect(
                surface,
                spectator.shirt_color,
                (x - 3, y - 2, 6, 8),
                border_radius=2,
            )
            arm_y = y - 4 if cheering else y + 1
            pygame.draw.line(
                surface,
                spectator.shirt_color,
                (x - 3, y),
                (x - 7, arm_y),
                2,
            )
            pygame.draw.line(
                surface,
                spectator.shirt_color,
                (x + 3, y),
                (x + 7, arm_y),
                2,
            )

    def _draw_barriers(self, surface, camera_distance):
        barrier_offset = (
            settings.ROAD_WIDTH / 2 + settings.ROAD_SHOULDER_WIDTH + 8
        )
        for zone in self.crowd_zones:
            if zone.density < 0.9:
                continue
            for side in (-1, 1):
                points = []
                distance = zone.start_distance
                while distance <= zone.end_distance:
                    y = self.track.world_distance_to_screen_y(
                        distance, camera_distance
                    )
                    if -30 <= y <= settings.SCREEN_HEIGHT + 30:
                        x = self.track.get_center_x(distance) + side * barrier_offset
                        points.append((round(x), round(y)))
                    distance += 18.0
                if len(points) >= 2:
                    pygame.draw.lines(surface, (38, 42, 46), False, points, 8)
                    pygame.draw.lines(surface, (218, 222, 218), False, points, 3)
                    for point in points[::4]:
                        pygame.draw.circle(surface, (234, 71, 61), point, 3)

    def _draw_banners(self, surface, camera_distance):
        for index, zone in enumerate(self.crowd_zones[1:-1]):
            distance = (zone.start_distance + zone.end_distance) / 2
            y = round(self.track.world_distance_to_screen_y(distance, camera_distance))
            if not -25 <= y <= settings.SCREEN_HEIGHT + 25:
                continue
            side = -1 if index % 2 == 0 else 1
            center = self.track.get_center_x(distance)
            x = round(center + side * (settings.ROAD_WIDTH / 2 + 62))
            board = pygame.Rect(0, 0, 74, 22)
            board.center = (x, y)
            pygame.draw.rect(surface, (17, 24, 30), board, border_radius=3)
            pygame.draw.rect(surface, (47, 194, 228), board, 2, border_radius=3)
            text = self.banner_font.render(
                BANNER_WORDS[index % len(BANNER_WORDS)], True, settings.WHITE
            )
            surface.blit(text, text.get_rect(center=board.center))

    def _draw_chevrons(self, surface, camera_distance):
        offset = (
            settings.ROAD_WIDTH / 2 + settings.ROAD_SHOULDER_WIDTH + 20
        )
        for chevron in self.chevrons:
            y = round(
                self.track.world_distance_to_screen_y(
                    chevron.world_distance, camera_distance
                )
            )
            if not -25 <= y <= settings.SCREEN_HEIGHT + 25:
                continue
            center = self.track.get_center_x(chevron.world_distance)
            x = round(center + chevron.side * offset)
            board = pygame.Rect(x - 16, y - 10, 32, 20)
            pygame.draw.rect(surface, (245, 203, 62), board, border_radius=2)
            pygame.draw.rect(surface, (24, 27, 30), board, 2, border_radius=2)
            direction = chevron.direction
            points = (
                (x - direction * 7, y - 6),
                (x + direction * 7, y),
                (x - direction * 7, y + 6),
            )
            pygame.draw.lines(surface, (24, 27, 30), False, points, 4)

    def _draw_gantry(self, surface, camera_distance, distance, text, color):
        y = round(self.track.world_distance_to_screen_y(distance, camera_distance))
        if not -35 <= y <= settings.SCREEN_HEIGHT + 35:
            return
        left, right = self.track.get_boundaries(distance)
        left = round(left - settings.ROAD_SHOULDER_WIDTH - 6)
        right = round(right + settings.ROAD_SHOULDER_WIDTH + 6)
        pygame.draw.rect(surface, (20, 25, 30), (left, y - 16, right - left, 24))
        pygame.draw.rect(surface, color, (left, y - 16, right - left, 24), 3)
        pygame.draw.rect(surface, (28, 31, 34), (left - 5, y - 16, 9, 38))
        pygame.draw.rect(surface, (28, 31, 34), (right - 4, y - 16, 9, 38))
        rendered = self.gantry_font.render(text, True, settings.WHITE)
        surface.blit(rendered, rendered.get_rect(center=((left + right) // 2, y - 4)))
