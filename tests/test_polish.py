"""Headless tests for Step 14 audio, steering, scenery, and headings."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game import settings
from game.audio import AudioManager, ENGINE_FREQUENCIES
from game.cars import BALANCED_CAR
from game.opponent import Opponent
from game.player import Player
from game.race import Race
from game.scenery import TrackScenery
from game.track import Track
from game.tracks import TRACK_1, TRACK_2
from game.user_settings import UserSettings
from ui.speedometer import speed_to_angle


class PolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_visual_steering_targets_and_returns_to_center(self):
        player = Player(BALANCED_CAR)
        player.speed = BALANCED_CAR.max_speed

        for _ in range(20):
            player.update_visual_steering(-1, 1.0 / 60.0)
        self.assertGreater(player.visual_steer_angle, 0.0)
        self.assertLessEqual(
            player.visual_steer_angle, settings.MAX_VISUAL_STEER_ANGLE
        )

        for _ in range(30):
            player.update_visual_steering(0, 1.0 / 60.0)
        self.assertAlmostEqual(player.visual_steer_angle, 0.0)

        player.speed = 0.0
        player.update_visual_steering(1, 1.0)
        self.assertEqual(player.visual_steer_target, 0.0)

    def test_opponent_heading_uses_track_tangent_and_is_bounded(self):
        track = Track(TRACK_2)
        heading = Opponent.calculate_heading(track, 1000.0)

        self.assertNotEqual(heading, 0.0)
        self.assertLessEqual(abs(heading), settings.OPPONENT_MAX_HEADING_ANGLE)

    def test_spectators_are_deterministic_and_safely_outside_road(self):
        track = Track(TRACK_1)
        first = TrackScenery(track)
        second = TrackScenery(track)
        minimum_offset = (
            settings.ROAD_WIDTH / 2
            + settings.ROAD_SHOULDER_WIDTH
            + settings.SPECTATOR_SAFETY_GAP
        )

        self.assertEqual(first.spectators, second.spectators)
        self.assertGreater(len(first.spectators), 0)
        self.assertTrue(
            all(
                spectator.lateral_offset >= minimum_offset
                for spectator in first.spectators
            )
        )

    def test_scenery_visibility_filter_only_returns_nearby_people(self):
        track = Track(TRACK_1)
        scenery = TrackScenery(track)
        visible = scenery.visible_spectators(0.0)

        self.assertGreater(len(visible), 0)
        self.assertLess(len(visible), len(scenery.spectators))
        for spectator in visible:
            y = track.world_distance_to_screen_y(spectator.world_distance, 0.0)
            self.assertGreaterEqual(y, -settings.SPECTATOR_VISIBLE_MARGIN)
            self.assertLessEqual(
                y, settings.SCREEN_HEIGHT + settings.SPECTATOR_VISIBLE_MARGIN
            )

    def test_engine_bands_are_monotonic_and_cover_full_range(self):
        audio = AudioManager(UserSettings())
        bands = [audio.get_engine_band(speed, 220.0) for speed in range(0, 221, 20)]

        self.assertEqual(bands[0], 0)
        self.assertEqual(bands[-1], len(ENGINE_FREQUENCIES) - 1)
        self.assertEqual(bands, sorted(bands))
        audio.shutdown()

    def test_engine_lifecycle_prevents_duplicate_loops(self):
        audio = AudioManager(UserSettings())
        audio.start_race_audio()
        original_channels = audio.engine_channels
        original_count = len(original_channels)
        original_race_channels = tuple(audio._race_channels())

        audio.start_race_audio()
        self.assertIs(audio.engine_channels, original_channels)
        self.assertEqual(original_count, len(ENGINE_FREQUENCIES))
        self.assertEqual(original_race_channels, tuple(audio._race_channels()))
        self.assertEqual(len(original_race_channels), len(ENGINE_FREQUENCIES) + 3)

        audio.update_race_audio(180.0, 220.0, throttle=True)
        self.assertEqual(audio.current_engine_band, 6)
        audio.pause_race_audio()
        self.assertTrue(audio.race_audio_paused)
        audio.resume_race_audio()
        self.assertFalse(audio.race_audio_paused)

        muted = UserSettings(master_volume=0.0, sfx_volume=1.0)
        audio.set_user_settings(muted)
        audio.update_race_audio(180.0, 220.0, throttle=True)
        self.assertTrue(
            all(channel.get_volume() == 0.0 for channel in audio._race_channels())
        )

        audio.stop_race_audio()
        self.assertFalse(audio.race_audio_active)
        self.assertEqual(audio.engine_channels, [])

    def test_finish_event_is_emitted_once(self):
        race = Race(TRACK_1, BALANCED_CAR, random_seed=4)
        race.state = settings.RACING
        race.player.distance = race.track.race_distance - 1.0
        race.player.speed = 100.0
        race.player.get_control_input = lambda: (0, False, False, False)

        race.update(0.02)
        first_events = race.consume_presentation_events()
        race.update(0.02)
        second_events = race.consume_presentation_events()

        self.assertIn("finish", first_events)
        self.assertNotIn("finish", second_events)

    def test_start_crowd_event_is_emitted_once(self):
        race = Race(TRACK_1, BALANCED_CAR, random_seed=4)

        race.update(0.01)
        first_events = race.consume_presentation_events()
        race.update(0.01)
        second_events = race.consume_presentation_events()

        self.assertEqual(first_events.count("crowd_start"), 1)
        self.assertNotIn("crowd_start", second_events)

    def test_speedometer_range_mapping_and_visual_smoothing(self):
        self.assertEqual(speed_to_angle(0.0), 135.0)
        self.assertEqual(speed_to_angle(60.0), 202.5)
        self.assertEqual(speed_to_angle(120.0), 270.0)
        self.assertEqual(speed_to_angle(180.0), 337.5)
        self.assertEqual(speed_to_angle(240.0), 405.0)
        self.assertEqual(speed_to_angle(500.0), 405.0)

        race = Race(TRACK_1, BALANCED_CAR, random_seed=4)
        race.player.speed = 180.0
        race._update_speedometer(1.0 / 60.0)

        self.assertGreater(race.displayed_speed, 0.0)
        self.assertLess(race.displayed_speed, race.player.speed)
        self.assertEqual(race.player.speed, 180.0)

        frozen_value = race.displayed_speed
        race.player.speed = 0.0
        race._update_speedometer(1.0 / 60.0)
        self.assertGreater(race.displayed_speed, 0.0)
        self.assertLess(race.displayed_speed, frozen_value)

        race.reset_race()
        self.assertEqual(race.displayed_speed, 0.0)
        self.assertNotEqual(frozen_value, race.displayed_speed)


if __name__ == "__main__":
    unittest.main()
