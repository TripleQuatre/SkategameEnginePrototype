from __future__ import annotations

import json
from pathlib import Path

from core.player_profile import PlayerProfile


class LocalPlayerProfileRepository:
    DEFAULT_PROFILES_DIR = Path(__file__).resolve().parents[1] / "local_profiles"

    def __init__(self, profiles_dir: Path | None = None) -> None:
        self.profiles_dir = profiles_dir or self.DEFAULT_PROFILES_DIR
        self._profiles_cache: list[PlayerProfile] | None = None

    def list_profiles(self) -> list[PlayerProfile]:
        if self._profiles_cache is None:
            profiles = [
                self._load_profile_from_path(profile_path)
                for profile_path in sorted(self.profiles_dir.glob("*.json"))
            ]
            self._profiles_cache = sorted(
                profiles,
                key=lambda profile: profile.display_name.casefold(),
            )
        return list(self._profiles_cache)

    def get_profile(self, profile_id: str) -> PlayerProfile:
        for profile in self.list_profiles():
            if profile.profile_id == profile_id:
                return profile
        raise ValueError(f"Unknown local player profile: {profile_id}")

    def _load_profile_from_path(self, profile_path: Path) -> PlayerProfile:
        try:
            payload = json.loads(profile_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid local player profile JSON: {profile_path.name}"
            ) from error

        if not isinstance(payload, dict):
            raise ValueError(
                f"Local player profile payload must be an object: {profile_path.name}"
            )

        return PlayerProfile.from_dict(payload)
