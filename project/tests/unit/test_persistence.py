import json

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
from core.types import EventName, Phase
from persistence.config_repository import ConfigRepository
from persistence.game_save import GameSave
from persistence.game_save_repository import GameSaveRepository
from persistence.serializers import Serializer


def test_serializer_can_roundtrip_game_state() -> None:
    serializer = Serializer()

    state = GameState(
        players=[
            Player(id="p1", name="Stan", score=1),
            Player(id="p2", name="Denise", score=2, is_active=False),
        ],
        phase=Phase.TURN,
        turn_order=[1, 0],
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
        mode_name="battle",
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
        turn_order=[2, 0, 1],
        attacker_index=2,
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

    assert restored_game_save.match_parameters.mode_name == "battle"
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
        turn_order=[0, 1],
        attacker_index=0,
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
        turn_order=[0, 1],
        attacker_index=0,
    )

    snapshot = Snapshot.from_state(state, match_parameters)
    restored_match_parameters = snapshot.restore_match_parameters()

    match_parameters.player_ids.append("p3")
    match_parameters.mode_name = "battle"

    assert restored_match_parameters is not None
    assert restored_match_parameters.player_ids == ["p1", "p2"]
    assert restored_match_parameters.mode_name == "one_vs_one"
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


def test_game_save_repository_can_save_and_load_game_save(tmp_path) -> None:
    repository = GameSaveRepository()

    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        mode_name="battle",
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
        turn_order=[2, 0, 1],
        attacker_index=2,
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

    filepath = tmp_path / "saves" / "game_save.json"

    repository.save(game_save, str(filepath))
    loaded_game_save = repository.load(str(filepath))

    assert filepath.exists()
    assert loaded_game_save.match_parameters.mode_name == "battle"
    assert loaded_game_save.match_parameters.preset_name == "battle_standard"
    assert loaded_game_save.match_parameters.player_ids == ["p1", "p2", "p3"]
    assert (
        loaded_game_save.match_parameters.policies.initial_turn_order
        == InitialTurnOrderPolicy.RANDOMIZED
    )
    assert loaded_game_save.game_state.phase == Phase.TURN
    assert loaded_game_save.game_state.turn_order == [2, 0, 1]
    assert loaded_game_save.game_state.current_trick == "Makio"
    assert loaded_game_save.game_state.players[0].name == "Stan"


def test_config_repository_can_save_and_load_match_parameters(tmp_path) -> None:
    repository = ConfigRepository()

    match_parameters = MatchParameters(
        player_ids=["Stan", "Denise"],
        mode_name="one_vs_one",
        preset_name="classic_skate",
        rule_set=RuleSetConfig(
            letters_word="SKATE",
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
    assert loaded_match_parameters.preset_name == "classic_skate"
    assert loaded_match_parameters.rule_set.letters_word == "SKATE"
    assert loaded_match_parameters.rule_set.defense_attempts == 3


def test_game_save_repository_writes_valid_json(tmp_path) -> None:
    repository = GameSaveRepository()

    game_save = GameSave(
        match_parameters=MatchParameters(
            player_ids=["p1", "p2"],
            mode_name="one_vs_one",
        ),
        game_state=GameState(
            players=[
                Player(id="p1", name="Stan"),
                Player(id="p2", name="Denise"),
            ]
        ),
    )

    filepath = tmp_path / "game_save.json"
    repository.save(game_save, str(filepath))

    with filepath.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert "match_parameters" in data
    assert "game_state" in data
    assert data["match_parameters"]["mode_name"] == "one_vs_one"
    assert "policies" in data["match_parameters"]
    assert "preset_name" in data["match_parameters"]
    assert data["game_state"]["players"][0]["name"] == "Stan"


def test_serializer_can_read_legacy_match_parameters_without_v6_fields() -> None:
    serializer = Serializer()

    restored_match_parameters = serializer.deserialize_match_parameters(
        {
            "player_ids": ["p1", "p2"],
            "mode_name": "one_vs_one",
            "rule_set": {
                "letters_word": "SKATE",
                "elimination_enabled": True,
                "defense_attempts": 1,
            },
        }
    )

    assert restored_match_parameters.preset_name is None
    assert (
        restored_match_parameters.policies.initial_turn_order
        == InitialTurnOrderPolicy.FIXED_PLAYER_ORDER
    )
