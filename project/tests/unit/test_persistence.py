import json

from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from core.player import Player
from core.state import GameState
from core.types import Phase
from persistence.config_repository import ConfigRepository
from persistence.serializers import Serializer
from persistence.snapshot_repository import SnapshotRepository


def test_serializer_can_roundtrip_game_state() -> None:
    serializer = Serializer()

    state = GameState(
        players=[
            Player(id="p1", name="Stan", score=1),
            Player(id="p2", name="Denise", score=2, is_active=False),
        ],
        phase=Phase.TURN,
        attacker_index=1,
        defender_indices=[0],
        current_defender_position=0,
        defense_attempts_left=2,
        current_trick="Soul",
        validated_tricks=["acid", "soul"],
    )

    state.history.add_event(
        serializer.deserialize_event(
            {
                "name": "turn_started",
                "payload": {
                    "attacker_id": "p2",
                    "trick": "Soul",
                    "defender_ids": ["p1"],
                },
            }
        )
    )

    data = serializer.serialize_game_state(state)
    restored_state = serializer.deserialize_game_state(data)

    assert restored_state.phase == Phase.TURN
    assert restored_state.attacker_index == 1
    assert restored_state.current_trick == "Soul"
    assert restored_state.defense_attempts_left == 2
    assert restored_state.validated_tricks == ["acid", "soul"]
    assert restored_state.players[0].name == "Stan"
    assert restored_state.players[1].score == 2
    assert restored_state.players[1].is_active is False
    assert len(restored_state.history.events) == 1
    assert restored_state.history.events[0].name == "turn_started"


def test_snapshot_repository_can_save_and_load_game_state(tmp_path) -> None:
    repository = SnapshotRepository()

    state = GameState(
        players=[
            Player(id="p1", name="Stan", score=1),
            Player(id="p2", name="Denise", score=0),
        ],
        phase=Phase.TURN,
        attacker_index=0,
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
        current_trick="Makio",
        validated_tricks=["makio"],
    )

    filepath = tmp_path / "snapshots" / "game_state.json"

    repository.save(state, str(filepath))
    loaded_state = repository.load(str(filepath))

    assert filepath.exists()
    assert loaded_state.phase == Phase.TURN
    assert loaded_state.current_trick == "Makio"
    assert loaded_state.attacker_index == 0
    assert loaded_state.defender_indices == [1]
    assert loaded_state.validated_tricks == ["makio"]
    assert loaded_state.players[0].name == "Stan"


def test_config_repository_can_save_and_load_match_parameters(tmp_path) -> None:
    repository = ConfigRepository()

    match_parameters = MatchParameters(
        player_ids=["Stan", "Denise"],
        mode_name="one_vs_one",
        rule_set=RuleSetConfig(
            letters_word="OUT",
            elimination_enabled=True,
            defense_attempts=3,
        ),
    )

    filepath = tmp_path / "configs" / "match_config.json"

    repository.save(match_parameters, str(filepath))
    loaded_match_parameters = repository.load(str(filepath))

    assert filepath.exists()
    assert loaded_match_parameters.player_ids == ["Stan", "Denise"]
    assert loaded_match_parameters.mode_name == "one_vs_one"
    assert loaded_match_parameters.rule_set.letters_word == "OUT"
    assert loaded_match_parameters.rule_set.defense_attempts == 3


def test_snapshot_repository_writes_valid_json(tmp_path) -> None:
    repository = SnapshotRepository()
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ]
    )

    filepath = tmp_path / "snapshot.json"
    repository.save(state, str(filepath))

    with filepath.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert "players" in data
    assert "phase" in data
    assert "history" in data
    assert data["players"][0]["name"] == "Stan"