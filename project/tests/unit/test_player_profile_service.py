import json
import shutil
from pathlib import Path

import pytest

from application.player_profile_service import PlayerProfileService
from persistence.player_profile_repository import LocalPlayerProfileRepository


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "player_profile_service"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_local_player_profile_repository_loads_profiles_sorted_by_display_name() -> None:
    repository = LocalPlayerProfileRepository()

    profiles = repository.list_profiles()

    assert [profile.display_name for profile in profiles] == [
        "Alex",
        "Denise",
        "Frank",
        "Jamie",
        "Margaux",
        "Stan",
    ]
    assert profiles[0].primary_sport == "inline"


def test_local_player_profile_repository_can_get_profile_by_id() -> None:
    repository = LocalPlayerProfileRepository()

    profile = repository.get_profile("margaux")

    assert profile.display_name == "Margaux"
    assert profile.local_rank == 1


def test_local_player_profile_repository_rejects_invalid_profile_payload() -> None:
    case_dir = _make_case_dir("invalid_payload")
    (case_dir / "broken.json").write_text(
        json.dumps(
            {
                "profile_id": "broken",
                "display_name": "",
                "age": 24,
                "experience_time": 3,
                "local_rank": 2,
                "primary_sport": "inline",
            }
        ),
        encoding="utf-8",
    )
    repository = LocalPlayerProfileRepository(case_dir)

    with pytest.raises(ValueError) as error:
        repository.list_profiles()

    assert "display_name" in str(error.value)


def test_player_profile_service_exposes_profile_ids() -> None:
    service = PlayerProfileService()

    assert service.list_profile_ids() == [
        "alex",
        "denise",
        "frank",
        "jamie",
        "margaux",
        "stan",
    ]

