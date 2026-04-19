import json
import shutil
from pathlib import Path

from config.match_parameters import MatchParameters
from config.match_policies import (
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
    MatchPolicies,
)
from config.rule_set_config import RuleSetConfig
from core.snapshots import Snapshot, SnapshotHistory
from core.player import Player
from core.state import GameState
from core.types import EventName, Phase, TurnPhase
from persistence.game_save import GameSave
from persistence.game_save_repository import GameSaveRepository
from persistence.serializers import Serializer


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "persistence"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_serializer_can_roundtrip_game_state() -> None:
    serializer = Serializer()

    state = GameState(
        players=[
            Player(id="p1", name="Stan", score=1),
            Player(id="p2", name="Denise", score=2, is_active=False),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        turn_order=[1, 0],
        attacker_index=1,
        attack_attempts_left=0,
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
    assert restored_state.turn_phase == TurnPhase.DEFENSE
    assert restored_state.attack_attempts_left == 0
    assert restored_state.turn_order == [1, 0]
    assert restored_state.attacker_index == 1
    assert restored_state.current_trick == "Soul"
    assert restored_state.defense_attempts_left == 2
    assert restored_state.validated_tricks == ["acid", "soul"]
    assert restored_state.players[0].name == "Stan"
    assert restored_state.players[1].score == 2
    assert restored_state.players[1].is_active is False
    assert len(restored_state.history.events) == 1
    assert restored_state.history.events[0].name == EventName.TURN_STARTED


def test_serializer_can_roundtrip_game_save() -> None:
    serializer = Serializer()

    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
        preset_name=None,
        policies=MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
            defender_order=DefenderOrderPolicy.REVERSE_TURN_ORDER,
        ),
        rule_set=RuleSetConfig(
            letters_word="SKATE",
            elimination_enabled=False,
            defense_attempts=2,
        ),
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
            Player(id="p3", name="Alex"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        turn_order=[2, 0, 1],
        attacker_index=2,
        attack_attempts_left=0,
        defender_indices=[0, 1],
        current_defender_position=1,
        defense_attempts_left=1,
        current_trick="Soul",
        validated_tricks=["makio"],
    )

    game_save = GameSave(
        match_parameters=match_parameters,
        game_state=state,
    )

    data = serializer.serialize_game_save(game_save)
    restored_game_save = serializer.deserialize_game_save(data)

    assert restored_game_save.match_parameters.structure_name == "battle"
    assert restored_game_save.match_parameters.preset_name is None
    assert restored_game_save.match_parameters.player_ids == ["p1", "p2", "p3"]
    assert (
        restored_game_save.match_parameters.policies.initial_turn_order
        == InitialTurnOrderPolicy.RANDOMIZED
    )
    assert (
        restored_game_save.match_parameters.policies.defender_order
        == DefenderOrderPolicy.REVERSE_TURN_ORDER
    )
    assert restored_game_save.match_parameters.rule_set.elimination_enabled is False
    assert restored_game_save.game_state.turn_order == [2, 0, 1]
    assert restored_game_save.game_state.attacker_index == 2
    assert restored_game_save.game_state.current_trick == "Soul"


def test_snapshot_restores_independent_game_state_copy() -> None:
    state = GameState(
        players=[
            Player(id="p1", name="Stan", score=1),
            Player(id="p2", name="Denise", score=0),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        turn_order=[0, 1],
        attacker_index=0,
        attack_attempts_left=0,
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
        current_trick="Makio",
        validated_tricks=["makio"],
    )

    snapshot = Snapshot.from_state(state)
    restored_state = snapshot.restore_state()

    state.players[0].name = "Changed"
    state.validated_tricks.append("soul")
    state.history.events.clear()

    assert restored_state.players[0].name == "Stan"
    assert restored_state.turn_order == [0, 1]
    assert restored_state.validated_tricks == ["makio"]
    assert restored_state.history.events == []


def test_snapshot_can_restore_match_parameters_copy() -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        preset_name="classic_skate",
        rule_set=RuleSetConfig(
            letters_word="SKATE",
            elimination_enabled=True,
            defense_attempts=3,
        ),
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[0, 1],
        attacker_index=0,
    )

    snapshot = Snapshot.from_state(state, match_parameters)
    restored_match_parameters = snapshot.restore_match_parameters()

    match_parameters.player_ids.append("p3")
    match_parameters.structure_name = "battle"

    assert restored_match_parameters is not None
    assert restored_match_parameters.player_ids == ["p1", "p2"]
    assert restored_match_parameters.structure_name == "one_vs_one"
    assert restored_match_parameters.preset_name == "classic_skate"


def test_snapshot_history_push_pop_and_peek() -> None:
    history = SnapshotHistory()

    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ]
    )

    history.push(state)

    assert history.can_undo() is True
    assert history.peek() is not None

    snapshot = history.pop()

    assert snapshot is not None
    assert history.peek() is None
    assert history.can_undo() is False


def test_snapshot_history_clear_removes_all_snapshots() -> None:
    history = SnapshotHistory()

    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ]
    )

    history.push(state)
    history.push(state)

    history.clear()

    assert history.can_undo() is False
    assert history.peek() is None
    assert history.pop() is None


def test_snapshot_history_respects_max_size() -> None:
    history = SnapshotHistory(max_size=2)

    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ]
    )

    state.attacker_index = 0
    history.push(state)

    state.attacker_index = 1
    history.push(state)

    state.attacker_index = 0
    history.push(state)

    assert len(history.snapshots) == 2
    assert history.snapshots[0].restore_state().attacker_index == 1
    assert history.snapshots[1].restore_state().attacker_index == 0


def test_game_save_repository_can_save_and_load_game_save() -> None:
    case_dir = _make_case_dir("repository_roundtrip")
    repository = GameSaveRepository()

    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
        preset_name="battle_standard",
        policies=MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
        ),
        rule_set=RuleSetConfig(
            letters_word="SKATE",
            elimination_enabled=True,
            defense_attempts=1,
        ),
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan", score=1),
            Player(id="p2", name="Denise", score=0),
            Player(id="p3", name="Alex", score=2),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        turn_order=[2, 0, 1],
        attacker_index=2,
        attack_attempts_left=0,
        defender_indices=[0, 1],
        current_defender_position=0,
        defense_attempts_left=1,
        current_trick="Makio",
        validated_tricks=["makio"],
    )

    game_save = GameSave(
        match_parameters=match_parameters,
        game_state=state,
    )

    try:
        filepath = case_dir / "saves" / "game_save.json"

        repository.save(game_save, str(filepath))
        loaded_game_save = repository.load(str(filepath))

        assert filepath.exists()
        assert loaded_game_save.match_parameters.structure_name == "battle"
        assert loaded_game_save.match_parameters.preset_name == "battle_standard"
        assert loaded_game_save.match_parameters.player_ids == ["p1", "p2", "p3"]
        assert (
            loaded_game_save.match_parameters.policies.initial_turn_order
            == InitialTurnOrderPolicy.RANDOMIZED
        )
        assert loaded_game_save.game_state.phase == Phase.TURN
        assert loaded_game_save.game_state.turn_phase == TurnPhase.DEFENSE
        assert loaded_game_save.game_state.attack_attempts_left == 0
        assert loaded_game_save.game_state.turn_order == [2, 0, 1]
        assert loaded_game_save.game_state.current_trick == "Makio"
        assert loaded_game_save.game_state.players[0].name == "Stan"
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_game_save_repository_writes_valid_json() -> None:
    case_dir = _make_case_dir("repository_writes_json")
    repository = GameSaveRepository()

    game_save = GameSave(
        match_parameters=MatchParameters(
            player_ids=["p1", "p2"],
            structure_name="one_vs_one",
        ),
        game_state=GameState(
            players=[
                Player(id="p1", name="Stan"),
                Player(id="p2", name="Denise"),
            ]
        ),
    )

    try:
        filepath = case_dir / "game_save.json"
        repository.save(game_save, str(filepath))

        with filepath.open("r", encoding="utf-8") as file:
            data = json.load(file)

        assert "match_parameters" in data
        assert "game_state" in data
        assert data["match_parameters"]["structure_name"] == "one_vs_one"
        assert "policies" in data["match_parameters"]
        assert "preset_name" in data["match_parameters"]
        assert data["game_state"]["players"][0]["name"] == "Stan"
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_serializer_can_read_v7_match_parameters_with_structure_name() -> None:
    serializer = Serializer()

    restored_match_parameters = serializer.deserialize_match_parameters(
        {
            "player_ids": ["p1", "p2", "p3"],
            "structure_name": "battle",
            "rule_set": {
                "letters_word": "SKATE",
                "elimination_enabled": True,
                "defense_attempts": 1,
            },
        }
    )

    assert restored_match_parameters.structure_name == "battle"
    assert restored_match_parameters.preset_name is None


def test_serializer_infers_turn_phase_for_legacy_saved_state() -> None:
    serializer = Serializer()

    restored_state = serializer.deserialize_game_state(
        {
            "players": [
                {
                    "id": "p1",
                    "name": "Stan",
                    "internal_id": "p1",
                    "score": 0,
                    "is_active": True,
                },
                {
                    "id": "p2",
                    "name": "Denise",
                    "internal_id": "p2",
                    "score": 0,
                    "is_active": True,
                },
            ],
            "phase": "turn",
            "turn_order": [0, 1],
            "attacker_index": 0,
            "defender_indices": [1],
            "current_defender_position": 0,
            "defense_attempts_left": 1,
            "current_trick": "Soul",
            "history": {"events": []},
            "rule_set": {
                "letters_word": "SKATE",
                "elimination_enabled": True,
                "defense_attempts": 1,
            },
            "validated_tricks": [],
        }
    )

    assert restored_state.turn_phase == TurnPhase.DEFENSE
    assert restored_state.attack_attempts_left == 0
