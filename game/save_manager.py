"""Centralized atomic JSON persistence for the single local profile."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from game.profile import PlayerProfile


DEFAULT_SAVE_PATH = (
    Path(__file__).resolve().parent.parent / "save_data" / "profile.json"
)


class SaveDataError(Exception):
    """Raised when profile data cannot be written safely."""


@dataclass(frozen=True)
class ProfileLoadResult:
    profile: object
    message: str = ""
    corrupt_backup_path: object = None


class SaveManager:
    def __init__(self, save_path=DEFAULT_SAVE_PATH):
        self.save_path = Path(save_path)

    def load_profile(self):
        if not self.save_path.exists():
            return ProfileLoadResult(profile=None)

        try:
            with self.save_path.open("r", encoding="utf-8") as save_file:
                data = json.load(save_file)
            return ProfileLoadResult(profile=PlayerProfile.from_dict(data))
        except (json.JSONDecodeError, TypeError, ValueError, KeyError) as error:
            backup_path = self._preserve_corrupt_save()
            if backup_path is not None:
                message = (
                    "Invalid save preserved as "
                    f"{backup_path.name}. Create a new profile."
                )
            else:
                message = (
                    "Profile data is invalid and could not be moved. "
                    "Create a new profile."
                )
            return ProfileLoadResult(
                profile=None,
                message=f"{message} ({error})",
                corrupt_backup_path=backup_path,
            )
        except OSError as error:
            return ProfileLoadResult(
                profile=None,
                message=f"Could not read profile save: {error}",
            )

    def save_profile(self, profile):
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.save_path.with_suffix(
            self.save_path.suffix + ".tmp"
        )
        try:
            with temporary_path.open("w", encoding="utf-8") as save_file:
                json.dump(profile.to_dict(), save_file, indent=2, sort_keys=True)
                save_file.write("\n")
                save_file.flush()
                os.fsync(save_file.fileno())
            os.replace(temporary_path, self.save_path)
        except OSError as error:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise SaveDataError(f"Could not save profile: {error}") from error

    def _preserve_corrupt_save(self):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        backup_path = self.save_path.with_name(
            f"profile.corrupt-{timestamp}.json"
        )
        try:
            os.replace(self.save_path, backup_path)
            return backup_path
        except OSError:
            return None
