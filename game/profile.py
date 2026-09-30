"""Single-player profile data, validation, records, and unlock processing."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import math

from game.cars import CARS, CARS_BY_ID
from game.progression import TRACK_COMPLETION_REWARDS
from game.tracks import TRACKS, TRACKS_BY_ID


SCHEMA_VERSION = 1
MAX_PLAYER_NAME_LENGTH = 20
DEFAULT_CAR_ID = "car_1"
DEFAULT_TRACK_ID = "track_1"


def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


def normalize_player_name(name):
    """Trim and validate a profile name accepted by the setup screen."""
    if not isinstance(name, str):
        raise ValueError("Player name must be text.")
    normalized = name.strip()
    if not normalized:
        raise ValueError("Player name cannot be empty.")
    if len(normalized) > MAX_PLAYER_NAME_LENGTH:
        raise ValueError(
            f"Player name must be {MAX_PLAYER_NAME_LENGTH} characters or fewer."
        )
    if not all(
        character.isalnum() or character in " -_"
        for character in normalized
    ):
        raise ValueError(
            "Use letters, numbers, spaces, hyphens, or underscores."
        )
    return normalized


@dataclass(frozen=True)
class ProfileUpdate:
    """One race's record/unlock changes for results-screen presentation."""

    best_time: float
    new_best_time: bool
    new_unlock_ids: tuple = ()
    new_unlock_names: tuple = ()


@dataclass
class PlayerProfile:
    schema_version: int
    player_name: str
    unlocked_car_ids: list = field(default_factory=lambda: [DEFAULT_CAR_ID])
    unlocked_track_ids: list = field(
        default_factory=lambda: [DEFAULT_TRACK_ID]
    )
    selected_car_id: str = DEFAULT_CAR_ID
    total_races: int = 0
    total_wins: int = 0
    total_podiums: int = 0
    best_finish_by_track: dict = field(default_factory=dict)
    best_time_by_track: dict = field(default_factory=dict)
    races_by_track: dict = field(default_factory=dict)
    wins_by_track: dict = field(default_factory=dict)
    created_at: str = field(default_factory=current_timestamp)
    last_played_at: str = field(default_factory=current_timestamp)

    def to_dict(self):
        return asdict(self)

    def select_car(self, car_id):
        if car_id not in CARS_BY_ID or car_id not in self.unlocked_car_ids:
            raise ValueError("Selected car must exist and be unlocked.")
        self.selected_car_id = car_id
        self.last_played_at = current_timestamp()

    def record_race(self, race_result):
        """Apply one valid race result and return its presentation summary."""
        if race_result.track_id not in TRACKS_BY_ID:
            raise ValueError("Race result contains an unknown track.")
        if race_result.car_id not in CARS_BY_ID:
            raise ValueError("Race result contains an unknown car.")
        if race_result.player_position not in (1, 2, 3, 4):
            raise ValueError("Race result position must be between 1 and 4.")
        if (
            not math.isfinite(race_result.player_time)
            or race_result.player_time <= 0.0
        ):
            raise ValueError("Race result time must be positive and finite.")

        track_id = race_result.track_id
        self.total_races += 1
        self.races_by_track[track_id] = (
            self.races_by_track.get(track_id, 0) + 1
        )

        if race_result.player_position == 1:
            self.total_wins += 1
            self.wins_by_track[track_id] = (
                self.wins_by_track.get(track_id, 0) + 1
            )
        if race_result.player_position <= 3:
            self.total_podiums += 1

        previous_finish = self.best_finish_by_track.get(track_id)
        if (
            previous_finish is None
            or race_result.player_position < previous_finish
        ):
            self.best_finish_by_track[track_id] = race_result.player_position

        previous_time = self.best_time_by_track.get(track_id)
        new_best_time = (
            previous_time is None or race_result.player_time < previous_time
        )
        if new_best_time:
            self.best_time_by_track[track_id] = race_result.player_time

        new_unlock_ids = []
        for unlock_id in TRACK_COMPLETION_REWARDS.get(track_id, ()):
            if unlock_id in CARS_BY_ID:
                if unlock_id not in self.unlocked_car_ids:
                    self.unlocked_car_ids.append(unlock_id)
                    new_unlock_ids.append(unlock_id)
            elif unlock_id in TRACKS_BY_ID:
                if unlock_id not in self.unlocked_track_ids:
                    self.unlocked_track_ids.append(unlock_id)
                    new_unlock_ids.append(unlock_id)

        self._order_unlock_ids()
        self.last_played_at = current_timestamp()
        new_unlock_names = tuple(
            CARS_BY_ID[unlock_id].name
            if unlock_id in CARS_BY_ID
            else TRACKS_BY_ID[unlock_id].name
            for unlock_id in new_unlock_ids
        )
        return ProfileUpdate(
            best_time=self.best_time_by_track[track_id],
            new_best_time=new_best_time,
            new_unlock_ids=tuple(new_unlock_ids),
            new_unlock_names=new_unlock_names,
        )

    def _order_unlock_ids(self):
        self.unlocked_car_ids = [
            car.id for car in CARS if car.id in self.unlocked_car_ids
        ]
        self.unlocked_track_ids = [
            track.id
            for track in TRACKS
            if track.id in self.unlocked_track_ids
        ]

    @classmethod
    def from_dict(cls, data):
        """Validate and normalize untrusted JSON profile data."""
        if not isinstance(data, dict):
            raise ValueError("Profile data must be a JSON object.")
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported profile schema version.")

        player_name = normalize_player_name(data.get("player_name"))
        unlocked_car_ids = _validated_id_list(
            data.get("unlocked_car_ids"), CARS_BY_ID, DEFAULT_CAR_ID
        )
        unlocked_track_ids = _validated_id_list(
            data.get("unlocked_track_ids"),
            TRACKS_BY_ID,
            DEFAULT_TRACK_ID,
        )

        selected_car_id = data.get("selected_car_id", DEFAULT_CAR_ID)
        if (
            selected_car_id not in CARS_BY_ID
            or selected_car_id not in unlocked_car_ids
        ):
            selected_car_id = DEFAULT_CAR_ID

        total_races = _non_negative_int(data, "total_races", 0)
        total_wins = _non_negative_int(data, "total_wins", 0)
        total_podiums = _non_negative_int(data, "total_podiums", 0)
        if total_wins > total_races or total_podiums > total_races:
            raise ValueError("Win and podium totals cannot exceed race total.")

        races_by_track = _validated_count_dict(
            data.get("races_by_track", {}), "races_by_track"
        )
        wins_by_track = _validated_count_dict(
            data.get("wins_by_track", {}), "wins_by_track"
        )
        for track_id, wins in wins_by_track.items():
            if wins > races_by_track.get(track_id, 0):
                raise ValueError("Track wins cannot exceed track races.")

        profile = cls(
            schema_version=SCHEMA_VERSION,
            player_name=player_name,
            unlocked_car_ids=unlocked_car_ids,
            unlocked_track_ids=unlocked_track_ids,
            selected_car_id=selected_car_id,
            total_races=total_races,
            total_wins=total_wins,
            total_podiums=total_podiums,
            best_finish_by_track=_validated_finish_dict(
                data.get("best_finish_by_track", {})
            ),
            best_time_by_track=_validated_time_dict(
                data.get("best_time_by_track", {})
            ),
            races_by_track=races_by_track,
            wins_by_track=wins_by_track,
            created_at=_validated_timestamp(
                data.get("created_at"), current_timestamp()
            ),
            last_played_at=_validated_timestamp(
                data.get("last_played_at"), current_timestamp()
            ),
        )
        profile._order_unlock_ids()
        return profile


def create_default_profile(name):
    return PlayerProfile(
        schema_version=SCHEMA_VERSION,
        player_name=normalize_player_name(name),
    )


def _validated_id_list(value, registry, required_id):
    if value is None:
        value = []
    if not isinstance(value, list):
        raise ValueError("Unlocked IDs must be stored as a list.")
    valid_ids = []
    for identifier in value:
        if identifier in registry and identifier not in valid_ids:
            valid_ids.append(identifier)
    if required_id not in valid_ids:
        valid_ids.insert(0, required_id)
    return valid_ids


def _non_negative_int(data, key, default):
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{key} must be a non-negative integer.")
    return value


def _validated_count_dict(value, field_name):
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object.")
    validated = {}
    for track_id, count in value.items():
        if track_id not in TRACKS_BY_ID:
            continue
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"{field_name} values must be non-negative integers.")
        validated[track_id] = count
    return validated


def _validated_finish_dict(value):
    if not isinstance(value, dict):
        raise ValueError("best_finish_by_track must be an object.")
    validated = {}
    for track_id, position in value.items():
        if track_id not in TRACKS_BY_ID:
            continue
        if isinstance(position, bool) or position not in (1, 2, 3, 4):
            raise ValueError("Best finish positions must be between 1 and 4.")
        validated[track_id] = position
    return validated


def _validated_time_dict(value):
    if not isinstance(value, dict):
        raise ValueError("best_time_by_track must be an object.")
    validated = {}
    for track_id, best_time in value.items():
        if track_id not in TRACKS_BY_ID:
            continue
        if isinstance(best_time, bool) or not isinstance(best_time, (int, float)):
            raise ValueError("Best times must be numeric.")
        best_time = float(best_time)
        if not math.isfinite(best_time) or best_time <= 0.0:
            raise ValueError("Best times must be positive and finite.")
        validated[track_id] = best_time
    return validated


def _validated_timestamp(value, default):
    return value if isinstance(value, str) and value else default
