"""Headless tests for Step 13 user-settings persistence."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from game.settings_manager import SettingsManager
from game.user_settings import UserSettings


class UserSettingsTests(unittest.TestCase):
    def test_defaults(self):
        user_settings = UserSettings()

        self.assertEqual(user_settings.schema_version, 1)
        self.assertEqual(user_settings.master_volume, 0.8)
        self.assertEqual(user_settings.sfx_volume, 0.8)
        self.assertEqual(user_settings.music_volume, 0.6)
        self.assertFalse(user_settings.show_fps)
        self.assertTrue(user_settings.screen_shake)

    def test_volume_validation(self):
        for invalid_volume in (-0.1, 1.1, True, "0.5"):
            data = UserSettings().to_dict()
            data["master_volume"] = invalid_volume
            with self.assertRaises(ValueError):
                UserSettings.from_dict(data)

    def test_boolean_validation(self):
        data = UserSettings().to_dict()
        data["show_fps"] = 1
        with self.assertRaises(ValueError):
            UserSettings.from_dict(data)


class SettingsManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "settings.json"
        self.manager = SettingsManager(self.path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_missing_settings_load_defaults(self):
        result = self.manager.load_settings()

        self.assertEqual(result.settings, UserSettings())
        self.assertEqual(result.message, "")

    def test_atomic_round_trip(self):
        expected = UserSettings(
            master_volume=0.4,
            sfx_volume=0.7,
            music_volume=0.2,
            show_fps=True,
            screen_shake=False,
        )

        self.manager.save_settings(expected)
        actual = self.manager.load_settings().settings

        self.assertEqual(actual, expected)
        self.assertFalse(Path(f"{self.path}.tmp").exists())

    def test_corrupt_settings_are_preserved_and_defaults_restored(self):
        self.path.write_text("{bad-json", encoding="utf-8")

        result = self.manager.load_settings()

        self.assertEqual(result.settings, UserSettings())
        self.assertIsNotNone(result.corrupt_backup_path)
        self.assertTrue(result.corrupt_backup_path.exists())
        self.assertFalse(self.path.exists())

    def test_unsupported_schema_is_preserved(self):
        self.path.write_text(
            json.dumps({"schema_version": 99}), encoding="utf-8"
        )

        result = self.manager.load_settings()

        self.assertEqual(result.settings, UserSettings())
        self.assertIsNotNone(result.corrupt_backup_path)
        self.assertIn("Unsupported settings schema", result.message)


if __name__ == "__main__":
    unittest.main()
