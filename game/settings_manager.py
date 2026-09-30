"""Atomic persistence and corruption recovery for user settings."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from game.user_settings import UserSettings


DEFAULT_SETTINGS_PATH = (
    Path(__file__).resolve().parent.parent / "save_data" / "settings.json"
)


class SettingsDataError(Exception):
    """Raised when settings cannot be written safely."""


@dataclass(frozen=True)
class SettingsLoadResult:
    settings: UserSettings
    message: str = ""
    corrupt_backup_path: object = None


class SettingsManager:
    def __init__(self, settings_path=DEFAULT_SETTINGS_PATH):
        self.settings_path = Path(settings_path)

    def load_settings(self):
        if not self.settings_path.exists():
            return SettingsLoadResult(settings=UserSettings())

        try:
            with self.settings_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return SettingsLoadResult(settings=UserSettings.from_dict(data))
        except (json.JSONDecodeError, TypeError, ValueError, KeyError) as error:
            backup_path = self._preserve_corrupt_settings()
            if backup_path is not None:
                message = (
                    f"Invalid settings preserved as {backup_path.name}. "
                    "Defaults restored."
                )
            else:
                message = "Invalid settings detected. Defaults restored."
            return SettingsLoadResult(
                settings=UserSettings(),
                message=f"{message} ({error})",
                corrupt_backup_path=backup_path,
            )
        except OSError as error:
            return SettingsLoadResult(
                settings=UserSettings(),
                message=f"Could not read settings; defaults restored: {error}",
            )

    def save_settings(self, user_settings):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.settings_path.with_suffix(
            self.settings_path.suffix + ".tmp"
        )
        try:
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(
                    user_settings.to_dict(), file, indent=2, sort_keys=True
                )
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.settings_path)
        except OSError as error:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise SettingsDataError(
                f"Could not save settings: {error}"
            ) from error

    def _preserve_corrupt_settings(self):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        backup_path = self.settings_path.with_name(
            f"settings.corrupt-{timestamp}.json"
        )
        try:
            os.replace(self.settings_path, backup_path)
            return backup_path
        except OSError:
            return None
