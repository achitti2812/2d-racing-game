"""Deterministic Step 10 track definitions and central registry."""

from game.track import AIDifficultyConfig, TrackConfig, TrackSegment


EASY_AI = AIDifficultyConfig(
    max_speed_multiplier=0.985,
    acceleration_multiplier=0.96,
    deceleration_multiplier=1.0,
    target_factor_adjustment=-0.006,
    curve_caution_multiplier=1.08,
    decision_time_multiplier=1.05,
)

MEDIUM_AI = AIDifficultyConfig(
    max_speed_multiplier=1.0,
    acceleration_multiplier=1.0,
    deceleration_multiplier=1.0,
    target_factor_adjustment=0.0,
    curve_caution_multiplier=1.0,
    decision_time_multiplier=1.0,
)

HARD_AI = AIDifficultyConfig(
    max_speed_multiplier=1.015,
    acceleration_multiplier=1.04,
    deceleration_multiplier=1.05,
    target_factor_adjustment=0.004,
    curve_caution_multiplier=0.94,
    decision_time_multiplier=0.90,
)


TRACK_1 = TrackConfig(
    id="track_1",
    name="GREENWAY SPRINT",
    race_distance=9000.0,
    difficulty="EASY",
    description="Long straights and flowing bends for learning the racing line.",
    terrain_color=(27, 67, 42),
    terrain_stripe_color=(24, 61, 38),
    shoulder_color=(65, 67, 70),
    ai_difficulty=EASY_AI,
    segments=(
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
        TrackSegment(8550.0, 9000.0, 0.0, 0.0, "final straight"),
    ),
)


TRACK_2 = TrackConfig(
    id="track_2",
    name="CANYON SWITCHBACK",
    race_distance=10000.0,
    difficulty="MEDIUM",
    description="Shorter straights link repeated left-right direction changes.",
    terrain_color=(83, 70, 42),
    terrain_stripe_color=(73, 61, 37),
    shoulder_color=(112, 94, 63),
    ai_difficulty=MEDIUM_AI,
    segments=(
        TrackSegment(0.0, 700.0, 0.0, 0.0, "opening straight"),
        TrackSegment(700.0, 1450.0, 0.0, 100.0, "first right"),
        TrackSegment(1450.0, 1850.0, 100.0, 100.0, "high straight"),
        TrackSegment(1850.0, 2650.0, 100.0, -80.0, "switchback left"),
        TrackSegment(2650.0, 3150.0, -80.0, -80.0, "short straight"),
        TrackSegment(3150.0, 3950.0, -80.0, 105.0, "switchback right"),
        TrackSegment(3950.0, 4450.0, 105.0, 105.0, "ridge straight"),
        TrackSegment(4450.0, 5600.0, 105.0, -115.0, "long canyon left"),
        TrackSegment(5600.0, 6000.0, -115.0, -115.0, "canyon chute"),
        TrackSegment(6000.0, 6750.0, -115.0, 40.0, "sharp right"),
        TrackSegment(6750.0, 7150.0, 40.0, 40.0, "short plateau"),
        TrackSegment(7150.0, 7900.0, 40.0, -90.0, "left return"),
        TrackSegment(7900.0, 8350.0, -90.0, -90.0, "lower straight"),
        TrackSegment(8350.0, 9200.0, -90.0, 45.0, "final right bend"),
        TrackSegment(9200.0, 10000.0, 45.0, 45.0, "final straight"),
    ),
)


TRACK_3 = TrackConfig(
    id="track_3",
    name="MIDNIGHT RIDGE",
    race_distance=11200.0,
    difficulty="HARD",
    description="Tight linked bends reward braking and selective nitro use.",
    terrain_color=(34, 43, 55),
    terrain_stripe_color=(29, 37, 49),
    shoulder_color=(58, 66, 79),
    ai_difficulty=HARD_AI,
    segments=(
        TrackSegment(0.0, 550.0, 0.0, 0.0, "opening straight"),
        TrackSegment(550.0, 1200.0, 0.0, -105.0, "opening left"),
        TrackSegment(1200.0, 1500.0, -105.0, -105.0, "short chute"),
        TrackSegment(1500.0, 2150.0, -105.0, 105.0, "hard right"),
        TrackSegment(2150.0, 2500.0, 105.0, 105.0, "ridge chute"),
        TrackSegment(2500.0, 3250.0, 105.0, -120.0, "hard left"),
        TrackSegment(3250.0, 3600.0, -120.0, -120.0, "low chute"),
        TrackSegment(3600.0, 4350.0, -120.0, 70.0, "climbing right"),
        TrackSegment(4350.0, 4650.0, 70.0, 70.0, "brief straight"),
        TrackSegment(4650.0, 5350.0, 70.0, -95.0, "falling left"),
        TrackSegment(5350.0, 5700.0, -95.0, -95.0, "midway chute"),
        TrackSegment(5700.0, 6500.0, -95.0, 120.0, "long right"),
        TrackSegment(6500.0, 6800.0, 120.0, 120.0, "high chute"),
        TrackSegment(6800.0, 7500.0, 120.0, -100.0, "technical left"),
        TrackSegment(7500.0, 7850.0, -100.0, -100.0, "short recovery"),
        TrackSegment(7850.0, 8650.0, -100.0, 90.0, "technical right"),
        TrackSegment(8650.0, 9000.0, 90.0, 90.0, "upper chute"),
        TrackSegment(9000.0, 9700.0, 90.0, -60.0, "late left"),
        TrackSegment(9700.0, 10100.0, -60.0, -60.0, "last recovery"),
        TrackSegment(10100.0, 10650.0, -60.0, 0.0, "return right"),
        TrackSegment(10650.0, 11200.0, 0.0, 0.0, "final straight"),
    ),
)


TRACKS = (TRACK_1, TRACK_2, TRACK_3)
TRACKS_BY_ID = {track.id: track for track in TRACKS}
