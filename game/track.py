"""Deterministic centerline geometry for the Step 9 race track."""

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


class Track:
    """Provide track geometry and shared world/screen coordinate mapping."""

    def __init__(self):
        # Consecutive segments share the same boundary offset. Smoothstep also
        # has a zero slope at both ends, preventing kinks between sections.
        self.segments = (
            TrackSegment(0.0, 900.0, 0.0, 0.0, "opening straight"),
            TrackSegment(900.0, 1900.0, 0.0, 85.0, "gentle right"),
            TrackSegment(1900.0, 2600.0, 85.0, 85.0, "right straight"),
            TrackSegment(2600.0, 4200.0, 85.0, -105.0, "long left bend"),
            TrackSegment(4200.0, 4900.0, -105.0, -105.0, "left straight"),
            TrackSegment(4900.0, 6200.0, -105.0, 95.0, "sweeping right"),
            TrackSegment(6200.0, 6750.0, 95.0, 95.0, "right straight"),
            TrackSegment(6750.0, 7650.0, 95.0, -55.0, "gentle left"),
            TrackSegment(7650.0, 8200.0, -55.0, -55.0, "left straight"),
            TrackSegment(8200.0, 8550.0, -55.0, 0.0, "final right"),
            TrackSegment(8550.0, settings.RACE_DISTANCE, 0.0, 0.0, "final straight"),
        )

    @staticmethod
    def _smoothstep(value):
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    def get_center_x(self, world_distance):
        """Return the road center X at a logical race distance."""
        clamped_distance = max(0.0, min(settings.RACE_DISTANCE, world_distance))

        for segment in self.segments:
            if clamped_distance <= segment.end_distance:
                segment_length = segment.end_distance - segment.start_distance
                progress = (clamped_distance - segment.start_distance) / segment_length
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
            abs(self.get_curve_strength(world_distance + lookahead * index / sample_count))
            for index in range(sample_count + 1)
        )

    @staticmethod
    def world_distance_to_screen_y(world_distance, camera_distance):
        """Map forward world distance to screen Y relative to the player camera."""
        relative_distance = world_distance - camera_distance
        return settings.PLAYER_Y - relative_distance * settings.RELATIVE_MOTION_SCALE

    @staticmethod
    def screen_y_to_world_distance(screen_y, camera_distance):
        """Map a screen Y coordinate back to the corresponding world distance."""
        relative_distance = (settings.PLAYER_Y - screen_y) / settings.RELATIVE_MOTION_SCALE
        return camera_distance + relative_distance
