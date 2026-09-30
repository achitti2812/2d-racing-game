"""Persistent competitive opponent cars."""

import math
import random

import pygame

from game import settings


class Opponent:
    """A persistent opponent with its own competitive speed personality."""

    def __init__(
        self,
        identifier,
        personality,
        lane,
        start_y,
        max_speed,
        acceleration,
        deceleration,
        min_target_factor,
        max_target_factor,
        decision_time_range,
        curve_caution,
        color,
        accent_color,
        random_source,
        track,
    ):
        self.identifier = identifier
        self.personality = personality
        self.lane = lane
        self.lane_offset = (lane - 1) * settings.LANE_WIDTH
        self.y = start_y
        self.current_speed = 0.0
        self.max_speed = max_speed
        self.acceleration = acceleration
        self.deceleration = deceleration
        self.min_target_factor = min_target_factor
        self.max_target_factor = max_target_factor
        self.decision_time_range = decision_time_range
        self.curve_caution = curve_caution
        self.random_source = random_source
        self.distance = (
            settings.PLAYER_Y - start_y
        ) / settings.RELATIVE_MOTION_SCALE
        self.color = color
        self.accent_color = accent_color
        self.finished = False
        self.finish_time = None
        self.finish_position = None
        self.cruise_target_speed = self._random_target_speed()
        self.target_speed = self.cruise_target_speed
        self.upcoming_curve_strength = 0.0
        self.decision_timer = self._random_decision_time()
        self.x = track.get_center_x(self.distance) + self.lane_offset
        self.heading_angle = self.calculate_heading(track, self.distance)

    def _random_decision_time(self):
        return self.random_source.uniform(*self.decision_time_range)

    def _random_target_speed(self):
        target_factor = self.random_source.uniform(
            self.min_target_factor, self.max_target_factor
        )
        return self.max_speed * target_factor

    def _choose_target_speed(self, player_distance):
        """Choose a restrained target within this racer's real performance."""
        target_factor = self.random_source.uniform(
            self.min_target_factor, self.max_target_factor
        )
        distance_gap = player_distance - self.distance

        if distance_gap > settings.AI_RACE_CONTEXT_DISTANCE:
            target_factor += settings.AI_BEHIND_TARGET_BONUS
        elif distance_gap < -settings.AI_RACE_CONTEXT_DISTANCE:
            target_factor -= settings.AI_AHEAD_TARGET_PENALTY

        target_factor = max(
            self.min_target_factor,
            min(target_factor, self.max_target_factor),
        )
        target_factor = max(
            settings.AI_MIN_TARGET_FACTOR,
            min(target_factor, settings.AI_MAX_TARGET_FACTOR),
        )
        self.cruise_target_speed = min(
            self.max_speed, self.max_speed * target_factor
        )
        self.decision_timer = self._random_decision_time()

    def update_ai(self, player_distance, delta_time, track):
        """Smoothly approach a periodically selected competitive target."""
        if self.finished:
            return

        self.decision_timer -= delta_time
        if self.decision_timer <= 0.0:
            self._choose_target_speed(player_distance)

        # Looking ahead lets lane-locked racers brake physically before a bend.
        # Personality only scales a modest reduction; it never changes distance.
        self.upcoming_curve_strength = track.get_upcoming_curve_strength(
            self.distance
        )
        curve_reduction = min(
            settings.AI_MAX_CURVE_SPEED_REDUCTION,
            self.upcoming_curve_strength
            * settings.AI_CURVE_SPEED_REDUCTION_FACTOR
            * self.curve_caution,
        )
        self.target_speed = max(
            settings.AI_MIN_CURVE_TARGET_SPEED,
            self.cruise_target_speed - curve_reduction,
        )

        if self.current_speed < self.target_speed:
            self.current_speed = min(
                self.target_speed,
                self.current_speed + self.acceleration * delta_time,
            )
        elif self.current_speed > self.target_speed:
            self.current_speed = max(
                self.target_speed,
                self.current_speed - self.deceleration * delta_time,
            )

        self.current_speed = max(
            0.0, min(self.current_speed, self.max_speed)
        )

    def update_distance(self, delta_time):
        if not self.finished:
            self.distance += self.current_speed * delta_time

    def update_screen_position(self, camera_distance, track):
        self.y = track.world_distance_to_screen_y(
            self.distance, camera_distance
        )
        self.x = track.get_center_x(self.distance) + self.lane_offset
        self.heading_angle = self.calculate_heading(track, self.distance)

    @staticmethod
    def calculate_heading(track, world_distance):
        """Return a visual-only heading from the local centerline tangent."""
        sample = settings.OPPONENT_HEADING_SAMPLE_DISTANCE
        before = track.get_center_x(world_distance - sample / 2)
        after = track.get_center_x(world_distance + sample / 2)
        screen_forward = sample * settings.RELATIVE_MOTION_SCALE
        heading = -math.degrees(math.atan2(after - before, screen_forward))
        return max(
            -settings.OPPONENT_MAX_HEADING_ANGLE,
            min(heading, settings.OPPONENT_MAX_HEADING_ANGLE),
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
        """Draw a shadowed local car rotated to the track tangent."""
        car_surface = pygame.Surface((112, 164), pygame.SRCALPHA)
        center_x = car_surface.get_width() // 2
        top = 24
        left = center_x - settings.OPPONENT_WIDTH // 2

        shadow = pygame.Surface(car_surface.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(
            shadow,
            (0, 0, 0, 95),
            (left - 5, top + 7, settings.OPPONENT_WIDTH + 14, 116),
        )
        car_surface.blit(shadow, (3, 4))

        for wheel_x in (left - 4, left + settings.OPPONENT_WIDTH - 5):
            for wheel_y in (top + 20, top + 74):
                pygame.draw.rect(
                    car_surface,
                    (10, 12, 14),
                    (wheel_x, wheel_y, 9, 25),
                    border_radius=3,
                )

        body_points = (
            (center_x - 19, top),
            (center_x + 19, top),
            (left + settings.OPPONENT_WIDTH, top + 24),
            (left + settings.OPPONENT_WIDTH - 3, top + 103),
            (center_x + 22, top + settings.OPPONENT_HEIGHT),
            (center_x - 22, top + settings.OPPONENT_HEIGHT),
            (left + 3, top + 103),
            (left, top + 24),
        )
        pygame.draw.polygon(car_surface, self.color, body_points)
        pygame.draw.polygon(car_surface, self.accent_color, body_points, width=3)
        highlight = tuple(min(255, channel + 38) for channel in self.color)
        pygame.draw.line(
            car_surface, highlight, body_points[0], body_points[7], 2
        )
        pygame.draw.rect(
            car_surface,
            self.accent_color,
            (center_x - 4, top + 5, 8, settings.OPPONENT_HEIGHT - 15),
        )
        pygame.draw.polygon(
            car_surface,
            settings.WINDOW_COLOR,
            (
                (center_x - 19, top + 34),
                (center_x + 19, top + 34),
                (center_x + 23, top + 57),
                (center_x - 23, top + 57),
            ),
        )
        pygame.draw.line(
            car_surface,
            settings.WINDOW_HIGHLIGHT,
            (center_x - 13, top + 38),
            (center_x + 10, top + 38),
            2,
        )
        pygame.draw.polygon(
            car_surface,
            (65, 108, 128),
            (
                (center_x - 22, top + 64),
                (center_x + 22, top + 64),
                (center_x + 18, top + 83),
                (center_x - 18, top + 83),
            ),
        )
        pygame.draw.rect(
            car_surface,
            self.accent_color,
            (
                left - 3,
                top + settings.OPPONENT_HEIGHT - 13,
                settings.OPPONENT_WIDTH + 6,
                7,
            ),
            border_radius=2,
        )
        for light_x in (left + 7, left + settings.OPPONENT_WIDTH - 17):
            pygame.draw.rect(
                car_surface, (245, 226, 146), (light_x, top + 9, 10, 5)
            )
            pygame.draw.rect(
                car_surface, (226, 60, 52), (light_x, top + 105, 10, 5)
            )

        rotated = pygame.transform.rotozoom(
            car_surface, self.heading_angle, 1.0
        )
        physical_center = (
            round(self.x),
            round(self.y + settings.OPPONENT_HEIGHT / 2),
        )
        surface.blit(rotated, rotated.get_rect(center=physical_center))

    def draw_debug(self, surface, font):
        """Draw lightweight speed and target information beside the car."""
        lines = [
            self.identifier,
            f"SPD {round(self.current_speed)}",
            f"TGT {round(self.target_speed)}",
        ]
        rendered_lines = [
            font.render(line, True, settings.WHITE) for line in lines
        ]
        padding = 4
        line_gap = 1
        panel_width = max(line.get_width() for line in rendered_lines) + 8
        panel_height = (
            sum(line.get_height() for line in rendered_lines)
            + line_gap * (len(rendered_lines) - 1)
            + padding * 2
        )
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((8, 10, 12, 185))

        panel_x = round(self.x + settings.OPPONENT_WIDTH / 2 + 8)
        panel_y = round(self.y + 18)
        panel_x = min(panel_x, settings.SCREEN_WIDTH - panel_width - 4)
        panel_y = max(4, min(panel_y, settings.SCREEN_HEIGHT - panel_height - 4))
        surface.blit(panel, (panel_x, panel_y))

        text_y = panel_y + padding
        for rendered_line in rendered_lines:
            surface.blit(rendered_line, (panel_x + padding, text_y))
            text_y += rendered_line.get_height() + line_gap


def create_opponents(track, random_source=None):
    """Create three personalities scaled by the selected track difficulty."""
    if random_source is None:
        random_source = random.Random()

    opponent_specs = [
        {
            "identifier": "BLUE",
            "personality": "FAST START",
            "lane": 0,
            "start_y": 445.0,
            "max_speed": 178.0,
            "acceleration": 108.0,
            "deceleration": 48.0,
            "min_target_factor": 0.97,
            "max_target_factor": 1.0,
            "decision_time_range": (1.5, 2.4),
            "curve_caution": 1.05,
            "color": (45, 143, 207),
            "accent_color": (225, 240, 248),
        },
        {
            "identifier": "GOLD",
            "personality": "TOP END",
            "lane": 1,
            "start_y": 330.0,
            "max_speed": 183.0,
            "acceleration": 66.0,
            "deceleration": 38.0,
            "min_target_factor": 0.94,
            "max_target_factor": 0.99,
            "decision_time_range": (2.6, 4.0),
            "curve_caution": 1.0,
            "color": (224, 164, 43),
            "accent_color": (75, 51, 14),
        },
        {
            "identifier": "PURPLE",
            "personality": "BALANCED",
            "lane": 2,
            "start_y": 445.0,
            "max_speed": 181.0,
            "acceleration": 82.0,
            "deceleration": 44.0,
            "min_target_factor": 0.965,
            "max_target_factor": 0.995,
            "decision_time_range": (2.0, 3.2),
            "curve_caution": 0.95,
            "color": (137, 83, 190),
            "accent_color": (236, 224, 247),
        },
    ]
    difficulty = track.config.ai_difficulty
    opponents = []
    for base_spec in opponent_specs:
        spec = dict(base_spec)
        spec["max_speed"] *= difficulty.max_speed_multiplier
        spec["acceleration"] *= difficulty.acceleration_multiplier
        spec["deceleration"] *= difficulty.deceleration_multiplier
        spec["min_target_factor"] = max(
            settings.AI_MIN_TARGET_FACTOR,
            min(
                settings.AI_MAX_TARGET_FACTOR,
                spec["min_target_factor"]
                + difficulty.target_factor_adjustment,
            ),
        )
        spec["max_target_factor"] = max(
            spec["min_target_factor"],
            min(
                settings.AI_MAX_TARGET_FACTOR,
                spec["max_target_factor"]
                + difficulty.target_factor_adjustment,
            ),
        )
        spec["decision_time_range"] = tuple(
            decision_time * difficulty.decision_time_multiplier
            for decision_time in spec["decision_time_range"]
        )
        spec["curve_caution"] *= difficulty.curve_caution_multiplier
        opponents.append(
            Opponent(random_source=random_source, track=track, **spec)
        )
    return opponents
