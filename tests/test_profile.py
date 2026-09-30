"""Headless tests for Step 12 profile progression and persistence."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from game.profile import PlayerProfile, create_default_profile
from game.race_result import RaceResult
from game.save_manager import SaveManager


def race_result(track_id, position=2, player_time=60.0):
    track_names = {
        "track_1": "Greenway Sprint",
        "track_2": "Canyon Switchback",
        "track_3": "Midnight Ridge",
    }
    return RaceResult(
        track_id=track_id,
        track_name=track_names[track_id],
        car_id="car_1",
        car_name="Balanced",
        player_position=position,
        player_time=player_time,
        finishing_order=("BLUE", "PLAYER", "PURPLE", "GOLD"),
    )


class ProfileProgressionTests(unittest.TestCase):
    def test_default_profile_starts_with_first_car_and_track(self):
        profile = create_default_profile("  Test Driver  ")

        self.assertEqual(profile.player_name, "Test Driver")
        self.assertEqual(profile.unlocked_car_ids, ["car_1"])
        self.assertEqual(profile.unlocked_track_ids, ["track_1"])
        self.assertEqual(profile.selected_car_id, "car_1")
        self.assertEqual(profile.total_races, 0)

    def test_greenway_completion_updates_stats_records_and_unlocks(self):
        profile = create_default_profile("Driver")

        update = profile.record_race(
            race_result("track_1", position=1, player_time=51.25)
        )

        self.assertEqual(profile.total_races, 1)
        self.assertEqual(profile.total_wins, 1)
        self.assertEqual(profile.total_podiums, 1)
        self.assertEqual(profile.races_by_track["track_1"], 1)
        self.assertEqual(profile.wins_by_track["track_1"], 1)
        self.assertEqual(profile.best_finish_by_track["track_1"], 1)
        self.assertEqual(profile.best_time_by_track["track_1"], 51.25)
        self.assertEqual(update.new_unlock_ids, ("car_2", "track_2"))

    def test_canyon_rewards_and_repeated_unlocks_are_idempotent(self):
        profile = create_default_profile("Driver")
        profile.record_race(race_result("track_1"))
        repeated = profile.record_race(race_result("track_1", 3, 62.0))
        canyon = profile.record_race(race_result("track_2", 4, 70.0))

        self.assertEqual(repeated.new_unlock_ids, ())
        self.assertEqual(canyon.new_unlock_ids, ("car_3", "track_3"))
        self.assertEqual(len(profile.unlocked_car_ids), 3)
        self.assertEqual(len(profile.unlocked_track_ids), 3)

    def test_slower_time_and_worse_finish_do_not_replace_records(self):
        profile = create_default_profile("Driver")
        profile.record_race(race_result("track_1", 2, 55.0))
        update = profile.record_race(race_result("track_1", 4, 58.0))

        self.assertEqual(profile.best_finish_by_track["track_1"], 2)
        self.assertEqual(profile.best_time_by_track["track_1"], 55.0)
        self.assertFalse(update.new_best_time)

    def test_unknown_ids_are_filtered_and_locked_selection_is_repaired(self):
        data = create_default_profile("Driver").to_dict()
        data["unlocked_car_ids"] = ["missing_car"]
        data["unlocked_track_ids"] = ["missing_track"]
        data["selected_car_id"] = "car_3"

        repaired = PlayerProfile.from_dict(data)

        self.assertEqual(repaired.unlocked_car_ids, ["car_1"])
        self.assertEqual(repaired.unlocked_track_ids, ["track_1"])
        self.assertEqual(repaired.selected_car_id, "car_1")

    def test_invalid_statistics_and_records_are_rejected(self):
        data = create_default_profile("Driver").to_dict()
        data["total_races"] = -1
        with self.assertRaises(ValueError):
            PlayerProfile.from_dict(data)

        data = create_default_profile("Driver").to_dict()
        data["best_time_by_track"] = {"track_1": 0.0}
        with self.assertRaises(ValueError):
            PlayerProfile.from_dict(data)


class SaveManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.save_path = (
            Path(self.temporary_directory.name) / "save_data" / "profile.json"
        )
        self.save_manager = SaveManager(self.save_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_missing_save_requests_profile_setup(self):
        load_result = self.save_manager.load_profile()

        self.assertIsNone(load_result.profile)
        self.assertEqual(load_result.message, "")

    def test_atomic_save_load_round_trip(self):
        profile = create_default_profile("Round Trip")
        profile.record_race(race_result("track_1", 3, 52.75))

        self.save_manager.save_profile(profile)
        loaded = self.save_manager.load_profile().profile

        self.assertEqual(loaded.to_dict(), profile.to_dict())
        self.assertFalse(Path(f"{self.save_path}.tmp").exists())

    def test_malformed_json_is_preserved(self):
        self.save_path.parent.mkdir(parents=True)
        self.save_path.write_text("{not-json", encoding="utf-8")

        load_result = self.save_manager.load_profile()

        self.assertIsNone(load_result.profile)
        self.assertIsNotNone(load_result.corrupt_backup_path)
        self.assertTrue(load_result.corrupt_backup_path.exists())
        self.assertFalse(self.save_path.exists())

    def test_unsupported_schema_is_preserved(self):
        self.save_path.parent.mkdir(parents=True)
        self.save_path.write_text(
            json.dumps({"schema_version": 99, "player_name": "Driver"}),
            encoding="utf-8",
        )

        load_result = self.save_manager.load_profile()

        self.assertIsNone(load_result.profile)
        self.assertIsNotNone(load_result.corrupt_backup_path)
        self.assertIn("Unsupported profile schema", load_result.message)


if __name__ == "__main__":
    unittest.main()
