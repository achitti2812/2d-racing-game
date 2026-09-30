"""Validated persistent presentation and audio preferences."""

from dataclasses import asdict, dataclass
import math


SETTINGS_SCHEMA_VERSION = 1


@dataclass
class UserSettings:
    schema_version: int = SETTINGS_SCHEMA_VERSION
    master_volume: float = 0.8
    sfx_volume: float = 0.8
    music_volume: float = 0.6
    show_fps: bool = False
    screen_shake: bool = True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Settings data must be a JSON object.")
        if data.get("schema_version") != SETTINGS_SCHEMA_VERSION:
            raise ValueError("Unsupported settings schema version.")

        defaults = cls()
        return cls(
            schema_version=SETTINGS_SCHEMA_VERSION,
            master_volume=_validated_volume(
                data.get("master_volume", defaults.master_volume),
                "master_volume",
            ),
            sfx_volume=_validated_volume(
                data.get("sfx_volume", defaults.sfx_volume), "sfx_volume"
            ),
            music_volume=_validated_volume(
                data.get("music_volume", defaults.music_volume),
                "music_volume",
            ),
            show_fps=_validated_bool(
                data.get("show_fps", defaults.show_fps), "show_fps"
            ),
            screen_shake=_validated_bool(
                data.get("screen_shake", defaults.screen_shake),
                "screen_shake",
            ),
        )


def _validated_volume(value, field_name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric.")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0.")
    return value


def _validated_bool(value, field_name):
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean.")
    return value
