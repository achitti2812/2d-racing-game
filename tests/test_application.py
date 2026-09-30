"""Headless navigation, pause, abandonment, and audio safety tests."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game import settings
from game.application import GameApplication
from game.audio import AudioManager
from game.cars import CARS
from game.profile import create_default_profile
from game.race import Race
from game.save_manager import SaveManager
from game.settings_manager import SettingsManager
from game.tracks import TRACKS
from game.user_settings import UserSettings


def key_event(key, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode)


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.save_manager = SaveManager(root / "profile.json")
        self.settings_manager = SettingsManager(root / "settings.json")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def make_application(self, with_profile=True):
        if with_profile:
            self.save_manager.save_profile(create_default_profile("Driver"))
        silent_audio = AudioManager(UserSettings(), force_silent=True)
        return GameApplication(
            save_manager=self.save_manager,
            settings_manager=self.settings_manager,
            audio_manager=silent_audio,
        )

    def attach_race(self, application, race_state=settings.RACING):
        application.race = Race(TRACKS[0], CARS[0], random_seed=7)
        application.race.state = race_state
        application.state = settings.RACE_SCREEN
        return application.race

    def test_first_profile_creation_and_existing_profile_open_main_menu(self):
        application = self.make_application(with_profile=False)
        self.assertEqual(application.state, settings.PROFILE_SETUP)

        for character in "Driver":
            application.handle_event(
                key_event(ord(character.lower()), character)
            )
        application.handle_event(key_event(pygame.K_RETURN, "\r"))
        self.assertEqual(application.state, settings.MAIN_MENU)

        reloaded = self.make_application(with_profile=False)
        self.assertEqual(reloaded.state, settings.MAIN_MENU)

    def test_main_profile_settings_and_selector_back_navigation(self):
        application = self.make_application()

        application.handle_event(key_event(pygame.K_RETURN))
        self.assertEqual(application.state, settings.CAR_SELECTION)
        application.handle_event(key_event(pygame.K_ESCAPE))
        self.assertEqual(application.state, settings.MAIN_MENU)

        application.main_menu.selected_index = 1
        application.handle_event(key_event(pygame.K_RETURN))
        self.assertEqual(application.state, settings.PROFILE_SCREEN)
        application.handle_event(key_event(pygame.K_b))
        self.assertEqual(application.state, settings.MAIN_MENU)

        application.main_menu.selected_index = 2
        application.handle_event(key_event(pygame.K_RETURN))
        self.assertEqual(application.state, settings.SETTINGS_SCREEN)
        application.handle_event(key_event(pygame.K_ESCAPE))
        self.assertEqual(application.state, settings.MAIN_MENU)

        application.main_menu.selected_index = 0
        application.handle_event(key_event(pygame.K_RETURN))
        application.handle_event(key_event(pygame.K_1, "1"))
        self.assertEqual(application.state, settings.TRACK_SELECTION)
        application.handle_event(key_event(pygame.K_ESCAPE))
        self.assertEqual(application.state, settings.CAR_SELECTION)

    def test_results_navigation_to_main_and_profile(self):
        for destination_key, expected_state in (
            (pygame.K_m, settings.MAIN_MENU),
            (pygame.K_p, settings.PROFILE_SCREEN),
        ):
            application = self.make_application()
            race = self.attach_race(application, settings.FINISHED)
            race.finishing_order = ["PLAYER", "BLUE", "PURPLE", "GOLD"]
            race.player.finished = True
            race.player.finish_position = 1
            race.player.finish_time = 50.0

            application.handle_event(key_event(destination_key))

            self.assertEqual(application.state, expected_state)
            self.assertIsNone(application.race)

    def test_finished_result_commits_once_across_repeated_updates(self):
        application = self.make_application()
        race = self.attach_race(application, settings.FINISHED)
        race.finishing_order = ["PLAYER", "BLUE", "PURPLE", "GOLD"]
        race.player.finished = True
        race.player.finish_position = 1
        race.player.finish_time = 50.0

        for _ in range(120):
            application.update(1.0 / 60.0)

        self.assertEqual(application.profile.total_races, 1)
        self.assertEqual(application.profile.total_wins, 1)
        self.assertTrue(application.race_result_committed)

    def test_collision_shake_respects_user_setting(self):
        application = self.make_application()
        race = self.attach_race(application)
        race._presentation_events.append("collision")

        application.update(0.0)
        self.assertEqual(
            application.screen_shake_timer,
            settings.COLLISION_SHAKE_DURATION,
        )

        application.user_settings.screen_shake = False
        application.screen_shake_timer = 0.0
        race._presentation_events.append("collision")
        application.update(0.0)
        self.assertEqual(application.screen_shake_timer, 0.0)

    def test_pause_freezes_all_active_race_state(self):
        application = self.make_application()
        race = self.attach_race(application)
        race.race_timer = 12.5
        race.player.distance = 100.0
        race.player.nitro_amount = 42.0
        race.player.collision_cooldown = 0.8
        race.player.crash_message_timer = 0.4
        race.opponents[0].distance = 130.0

        application.handle_event(key_event(pygame.K_p))
        snapshot = (
            race.race_timer,
            race.player.distance,
            race.player.nitro_amount,
            race.player.collision_cooldown,
            race.player.crash_message_timer,
            race.opponents[0].distance,
        )
        application.update(10.0)

        self.assertEqual(application.state, settings.PAUSED)
        self.assertEqual(
            snapshot,
            (
                race.race_timer,
                race.player.distance,
                race.player.nitro_amount,
                race.player.collision_cooldown,
                race.player.crash_message_timer,
                race.opponents[0].distance,
            ),
        )

    def test_pause_freezes_countdown_and_settings_returns_to_pause(self):
        application = self.make_application()
        race = self.attach_race(application, settings.COUNTDOWN)
        race.countdown_timer = 2.4

        application.handle_event(key_event(pygame.K_ESCAPE))
        application.update(8.0)
        self.assertEqual(race.countdown_timer, 2.4)

        application.pause_menu.selected_index = 2
        application.handle_event(key_event(pygame.K_RETURN))
        self.assertEqual(application.state, settings.SETTINGS_SCREEN)
        application.handle_event(key_event(pygame.K_ESCAPE))
        self.assertEqual(application.state, settings.PAUSED)
        self.assertIs(application.race, race)

    def test_pause_restart_is_fresh_and_does_not_commit_profile(self):
        application = self.make_application()
        race = self.attach_race(application)
        race.player.distance = 500.0
        race.race_timer = 9.0
        race.player.nitro_amount = 10.0
        original_profile = application.profile.to_dict()

        application.handle_event(key_event(pygame.K_p))
        application.pause_menu.selected_index = 1
        application.handle_event(key_event(pygame.K_RETURN))

        self.assertEqual(application.state, settings.RACE_SCREEN)
        self.assertIs(application.race, race)
        self.assertEqual(race.track_config.id, "track_1")
        self.assertEqual(race.car_config.id, "car_1")
        self.assertEqual(race.state, settings.COUNTDOWN)
        self.assertEqual(race.player.distance, 0.0)
        self.assertEqual(race.race_timer, 0.0)
        self.assertEqual(race.player.nitro_amount, race.player.nitro_capacity)
        self.assertEqual(application.profile.to_dict(), original_profile)

    def test_pause_abandon_does_not_create_result(self):
        application = self.make_application()
        self.attach_race(application)
        application.audio.start_race_audio()
        original_profile = application.profile.to_dict()

        application.handle_event(key_event(pygame.K_p))
        application.pause_menu.selected_index = 3
        application.handle_event(key_event(pygame.K_RETURN))

        self.assertEqual(application.state, settings.MAIN_MENU)
        self.assertIsNone(application.race)
        self.assertFalse(application.audio.race_audio_active)
        self.assertEqual(application.profile.to_dict(), original_profile)

    def test_silent_audio_manager_is_safe(self):
        audio = AudioManager(UserSettings(), force_silent=True)

        audio.play_sfx("collision")
        audio.start_music("missing.ogg")
        audio.stop_music()

        self.assertFalse(audio.available)

    def test_audio_manager_handles_mixer_initialization_failure(self):
        with patch("pygame.mixer.get_init", return_value=None), patch(
            "pygame.mixer.init", side_effect=pygame.error("no audio device")
        ):
            audio = AudioManager(UserSettings())

        audio.play_sfx("go")
        self.assertFalse(audio.available)

    def test_countdown_and_nitro_emit_edge_events(self):
        race = Race(TRACKS[0], CARS[0], random_seed=7)

        race.update(0.016)
        self.assertEqual(
            race.consume_presentation_events(),
            ("crowd_start", "countdown"),
        )

        race.countdown_timer = 0.005
        race.update(0.010)
        self.assertEqual(race.consume_presentation_events(), ("go",))

        race.player.get_control_input = lambda: (0, True, False, True)
        race.update(0.016)
        self.assertIn("nitro", race.consume_presentation_events())
        race.update(0.016)
        self.assertNotIn("nitro", race.consume_presentation_events())


if __name__ == "__main__":
    unittest.main()
