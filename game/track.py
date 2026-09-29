"""Reusable track geometry and configuration models."""

from dataclasses import dataclass

from game import settings


@dataclass(frozen=True)
class TrackSegment:
    """One smooth transition between two horizontal track offsets."""

    start_distance: float
    end_distance: float
    start_offset: float
    end_offset: float
    name: str


@dataclass(frozen=True)
class AIDifficultyConfig:
    """Small multipliers applied to every existing AI personality."""

    max_speed_multiplier: float
    acceleration_multiplier: float
    deceleration_multiplier: float
    target_factor_adjustment: float
    curve_caution_multiplier: float
    decision_time_multiplier: float


@dataclass(frozen=True)
class TrackConfig:
    """Immutable data used to construct one playable track."""

    id: str
    name: str
    race_distance: float
    segments: tuple
    difficulty: str
    description: str
    terrain_color: tuple
    terrain_stripe_color: tuple
    shoulder_color: tuple
    ai_difficulty: AIDifficultyConfig


class Track:
    """Provide geometry and shared coordinate mapping for a TrackConfig."""

    def __init__(self, config):
        self.config = config
        self.segments = config.segments
        self.race_distance = config.race_distance
        self._validate_config()

    @property
    def id(self):
        return self.config.id

    @property
    def name(self):
        return self.config.name

    @property
    def difficulty(self):
        return self.config.difficulty

    def _validate_config(self):
        """Reject discontinuous or incomplete segment data immediately."""
        if not self.segments:
            raise ValueError("A track must contain at least one segment.")
        if self.segments[0].start_distance != 0.0:
            raise ValueError("The first track segment must start at 0.")
        if self.segments[-1].end_distance != self.race_distance:
            raise ValueError("The final segment must end at race_distance.")

        minimum_center = (
            settings.ROAD_WIDTH / 2 + settings.ROAD_SHOULDER_WIDTH
        )
        maximum_center = settings.SCREEN_WIDTH - minimum_center
        previous_segment = None
        for segment in self.segments:
            if segment.end_distance <= segment.start_distance:
                raise ValueError("Track segments must have positive length.")
            if previous_segment is not None:
                if segment.start_distance != previous_segment.end_distance:
                    raise ValueError("Track segments must be distance-contiguous.")
                if segment.start_offset != previous_segment.end_offset:
                    raise ValueError("Track segment offsets must be continuous.")

            for offset in (segment.start_offset, segment.end_offset):
                center_x = settings.SCREEN_WIDTH / 2 + offset
                if not minimum_center <= center_x <= maximum_center:
                    raise ValueError(
                        "Track road and shoulders must remain inside the window."
                    )
            previous_segment = segment

    @staticmethod
    def _smoothstep(value):
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    def get_center_x(self, world_distance):
        """Return the road center X at a logical race distance."""
        clamped_distance = max(0.0, min(self.race_distance, world_distance))

        for segment in self.segments:
            if clamped_distance <= segment.end_distance:
                segment_length = segment.end_distance - segment.start_distance
                progress = (
                    clamped_distance - segment.start_distance
                ) / segment_length
                eased_progress = self._smoothstep(progress)
                offset = segment.start_offset + (
                    segment.end_offset - segment.start_offset
                ) * eased_progress
                return settings.SCREEN_WIDTH / 2 + offset

        return settings.SCREEN_WIDTH / 2 + self.segments[-1].end_offset

    def get_boundaries(self, world_distance):
        """Return the left and right road edges at a world distance."""
        center_x = self.get_center_x(world_distance)
        half_width = settings.ROAD_WIDTH / 2
        return center_x - half_width, center_x + half_width

    def get_curve_strength(self, world_distance):
        """Return signed horizontal centerline change per world-distance unit."""
        sample_distance = settings.TRACK_CURVE_SAMPLE_DISTANCE
        before = self.get_center_x(world_distance - sample_distance / 2)
        after = self.get_center_x(world_distance + sample_distance / 2)
        return (after - before) / sample_distance

    def get_upcoming_curve_strength(self, world_distance):
        """Return the strongest absolute curve in the AI look-ahead window."""
        sample_count = settings.AI_CURVE_LOOKAHEAD_SAMPLES
        lookahead = settings.AI_CURVE_LOOKAHEAD_DISTANCE
        return max(
            abs(
                self.get_curve_strength(
                    world_distance + lookahead * index / sample_count
                )
            )
            for index in range(sample_count + 1)
        )

    @staticmethod
    def world_distance_to_screen_y(world_distance, camera_distance):
        """Map forward world distance to screen Y relative to the camera."""
        relative_distance = world_distance - camera_distance
        return (
            settings.PLAYER_Y
            - relative_distance * settings.RELATIVE_MOTION_SCALE
        )

    @staticmethod
    def screen_y_to_world_distance(screen_y, camera_distance):
        """Map a screen Y coordinate back to its logical world distance."""
        relative_distance = (
            settings.PLAYER_Y - screen_y
        ) / settings.RELATIVE_MOTION_SCALE
        return camera_distance + relative_distance
