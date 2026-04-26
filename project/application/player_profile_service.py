from __future__ import annotations

from persistence.player_profile_repository import LocalPlayerProfileRepository


class PlayerProfileService:
    def __init__(
        self,
        repository: LocalPlayerProfileRepository | None = None,
    ) -> None:
        self.repository = (
            repository if repository is not None else LocalPlayerProfileRepository()
        )

    def list_profiles(self):
        return self.repository.list_profiles()

    def list_profile_ids(self) -> list[str]:
        return [profile.profile_id for profile in self.list_profiles()]

    def get_profile(self, profile_id: str):
        return self.repository.get_profile(profile_id)

