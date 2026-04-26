from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlayerProfile:
    profile_id: str
    display_name: str
    age: int
    experience_time: int
    local_rank: int
    primary_sport: str = "inline"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlayerProfile":
        profile_id = data.get("profile_id")
        display_name = data.get("display_name")
        age = data.get("age")
        experience_time = data.get("experience_time")
        local_rank = data.get("local_rank")
        primary_sport = data.get("primary_sport", "inline")
        metadata = data.get("metadata") or {}

        if not isinstance(profile_id, str) or not profile_id.strip():
            raise ValueError("Player profile requires a non-empty profile_id.")
        if not isinstance(display_name, str) or not display_name.strip():
            raise ValueError("Player profile requires a non-empty display_name.")
        if not isinstance(age, int) or age < 1:
            raise ValueError("Player profile age must be an integer greater than 0.")
        if not isinstance(experience_time, int) or experience_time < 0:
            raise ValueError(
                "Player profile experience_time must be an integer greater than or equal to 0."
            )
        if not isinstance(local_rank, int) or local_rank < 1:
            raise ValueError(
                "Player profile local_rank must be an integer greater than 0."
            )
        if not isinstance(primary_sport, str) or not primary_sport.strip():
            raise ValueError("Player profile requires a non-empty primary_sport.")
        if not isinstance(metadata, dict):
            raise ValueError("Player profile metadata must be a mapping.")

        return cls(
            profile_id=profile_id.strip(),
            display_name=display_name.strip(),
            age=age,
            experience_time=experience_time,
            local_rank=local_rank,
            primary_sport=primary_sport.strip(),
            metadata=dict(metadata),
        )

