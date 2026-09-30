"""Headless physical-pace and gap regression tests for the final AI tune."""

from dataclasses import dataclass
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game import settings
from game.cars import BALANCED_CAR, CARS, SPEED_CAR
from game.race import Race
from game.tracks import TRACKS


DELTA_TIME = 1.0 / 60.0


@dataclass
class DriverAudit:
    result: object
    progress_gaps: dict
    first_place_time: float
    post_first_gaps: dict
    average_player_speed: float
    average_non_nitro_speed: float
    average_ai_speeds: dict


def simulate_strong_driver(
    car,
    track_config,
    mistake=None,
    random_seed=3201,
):
    """Run an aggressive centerline driver and record physical pace gaps."""
    race = Race(track_config, car, random_seed=random_seed)
    race.state = settings.RACING
    race.player.collision_cooldown = 1_000_000.0
    checkpoints = {}
    post_first_gaps = {}
    first_place_time = None
    collision_applied = False
    player_speed_total = 0.0
    non_nitro_speed_total = 0.0
    player_samples = 0
    non_nitro_samples = 0
    ai_speed_totals = {
        opponent.identifier: 0.0 for opponent in race.opponents
    }
    ai_samples = {opponent.identifier: 0 for opponent in race.opponents}

    def controls():
        player = race.player
        center = race.track.get_center_x(player.distance)
        future_center = race.track.get_center_x(player.distance + 85.0)
        target_x = center + (future_center - center) * 0.28
        error = target_x - player.x
        steering = 1 if error > 2.0 else -1 if error < -2.0 else 0

        mistake_elapsed = (
            race.race_timer - first_place_time - 10.0
            if first_place_time is not None
            else -1.0
        )
        if mistake == "brake" and 0.0 <= mistake_elapsed < 2.0:
            return steering, False, True, False
        if mistake == "offroad" and 0.0 <= mistake_elapsed < 3.0:
            return 0, True, False, False

        curve = race.track.get_upcoming_curve_strength(player.distance)
        reduction = (
            max(0.0, curve - 0.10)
            * 95.0
            * car.curve_pressure_multiplier
        )
        target_speed = max(132.0, car.max_speed - reduction)
        braking = player.speed > target_speed + 3.0
        nitro = (
            not braking
            and curve < 0.075
            and abs(error) < 13.0
            and not player.off_road
            and player.nitro_amount > 2.0
        )
        return steering, not braking, braking, nitro

    race.player.get_control_input = controls
    for _ in range(60 * 180):
        if first_place_time is not None:
            mistake_elapsed = race.race_timer - first_place_time - 10.0
            if mistake == "offroad" and 0.0 <= mistake_elapsed < 3.0:
                race.player.x = race.player.outer_max_x
            if (
                mistake == "collision"
                and mistake_elapsed >= 0.0
                and not collision_applied
            ):
                race.player.speed *= settings.COLLISION_SPEED_RETENTION
                collision_applied = True

        race.update(DELTA_TIME)
        if not race.player.finished:
            player_samples += 1
            player_speed_total += race.player.speed
            if not race.player.nitro_active:
                non_nitro_samples += 1
                non_nitro_speed_total += race.player.speed
            for opponent in race.opponents:
                if not opponent.finished:
                    ai_speed_totals[opponent.identifier] += opponent.current_speed
                    ai_samples[opponent.identifier] += 1

        leading_ai_distance = max(
            opponent.distance for opponent in race.opponents
        )
        if first_place_time is None and race.player_position == 1:
            first_place_time = race.race_timer
        if first_place_time is not None:
            time_since_first = race.race_timer - first_place_time
            for seconds in (5, 10, 20, 30):
                if (
                    seconds not in post_first_gaps
                    and time_since_first >= seconds
                ):
                    post_first_gaps[seconds] = (
                        race.player.distance - leading_ai_distance
                    )
        for progress in (0.25, 0.50, 0.75):
            if (
                progress not in checkpoints
                and race.player.distance
                >= track_config.race_distance * progress
            ):
                checkpoints[progress] = (
                    race.player.distance - leading_ai_distance
                )
        if race.player.finished and 1.0 not in checkpoints:
            unfinished_distances = [
                opponent.distance
                for opponent in race.opponents
                if not opponent.finished
            ]
            checkpoints[1.0] = (
                track_config.race_distance - max(unfinished_distances)
                if unfinished_distances
                else 0.0
            )
        if race.state == settings.FINISHED:
            break

    return DriverAudit(
        result=race.get_result(),
        progress_gaps=checkpoints,
        first_place_time=first_place_time,
        post_first_gaps=post_first_gaps,
        average_player_speed=player_speed_total / max(1, player_samples),
        average_non_nitro_speed=(
            non_nitro_speed_total / max(1, non_nitro_samples)
        ),
        average_ai_speeds={
            identifier: ai_speed_totals[identifier] / max(1, ai_samples[identifier])
            for identifier in ai_speed_totals
        },
    )


class AICompetitivenessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_all_car_track_combinations_finish_physically(self):
        for track_config in TRACKS:
            for car in CARS:
                with self.subTest(track=track_config.id, car=car.id):
                    audit = simulate_strong_driver(car, track_config)
                    self.assertIsNotNone(audit.result)
                    self.assertEqual(len(set(audit.result.finishing_order)), 4)
                    self.assertEqual(
                        set(audit.progress_gaps), {0.25, 0.50, 0.75, 1.0}
                    )

    def test_aggressive_speed_car_records_post_overtake_gaps(self):
        maximum_ten_second_gaps = {
            "track_1": 200.0,
            "track_2": 160.0,
            "track_3": 120.0,
        }
        for track_config in TRACKS:
            audit = simulate_strong_driver(SPEED_CAR, track_config)
            with self.subTest(track=track_config.id):
                self.assertIsNotNone(audit.first_place_time)
                self.assertIn(5, audit.post_first_gaps)
                self.assertIn(10, audit.post_first_gaps)
                self.assertLess(
                    audit.post_first_gaps[10],
                    maximum_ten_second_gaps[track_config.id],
                )

    def test_post_overtake_mistakes_allow_ai_to_apply_pressure(self):
        for track_config in TRACKS[1:]:
            clean = simulate_strong_driver(SPEED_CAR, track_config)
            for mistake in ("brake", "collision", "offroad"):
                mistake_audit = simulate_strong_driver(
                    SPEED_CAR, track_config, mistake=mistake
                )
                with self.subTest(track=track_config.id, mistake=mistake):
                    self.assertGreaterEqual(
                        mistake_audit.result.player_position,
                        clean.result.player_position,
                    )
                    self.assertTrue(
                        mistake_audit.result.player_position
                        > clean.result.player_position
                        or mistake_audit.progress_gaps[1.0]
                        < clean.progress_gaps[1.0]
                    )

    def test_curve_target_recovers_as_soon_as_lookahead_is_clear(self):
        race = Race(TRACKS[1], BALANCED_CAR, random_seed=3201)
        opponent = race.opponents[0]
        opponent.cruise_target_speed = opponent.max_speed
        opponent.decision_timer = 999.0

        curve_distance = max(
            range(0, int(race.track.race_distance), 20),
            key=race.track.get_upcoming_curve_strength,
        )
        straight_distance = min(
            range(0, int(race.track.race_distance), 20),
            key=race.track.get_upcoming_curve_strength,
        )
        opponent.distance = curve_distance
        opponent.update_ai(0.0, 0.0, race.track)
        curve_target = opponent.target_speed

        opponent.distance = straight_distance
        opponent.update_ai(0.0, 0.0, race.track)

        self.assertLess(curve_target, opponent.cruise_target_speed)
        self.assertEqual(opponent.target_speed, opponent.cruise_target_speed)

    def test_mild_curvature_does_not_reduce_ai_target(self):
        race = Race(TRACKS[1], BALANCED_CAR, random_seed=3201)
        opponent = race.opponents[0]
        opponent.cruise_target_speed = opponent.max_speed
        opponent.decision_timer = 999.0
        mild_distance = next(
            distance
            for distance in range(0, int(race.track.race_distance), 10)
            if 0.0
            < race.track.get_upcoming_curve_strength(distance)
            <= settings.AI_MILD_CURVE_THRESHOLD
        )

        opponent.distance = mild_distance
        opponent.update_ai(0.0, 0.0, race.track)

        self.assertEqual(opponent.target_speed, opponent.cruise_target_speed)

    def test_opponent_distance_uses_current_speed_integration(self):
        race = Race(TRACKS[0], BALANCED_CAR, random_seed=3201)
        opponent = race.opponents[0]
        opponent.current_speed = 177.0
        old_distance = opponent.distance

        opponent.update_distance(0.25)

        self.assertAlmostEqual(
            opponent.distance,
            old_distance + opponent.current_speed * 0.25,
        )


if __name__ == "__main__":
    unittest.main()
