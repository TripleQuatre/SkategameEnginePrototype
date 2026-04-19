from application.game_session import GameSession as GameEngine
import match.structure.battle_structure as battle_structure_module

from config.match_parameters import MatchParameters
from core.types import DefenseResolutionStatus, EventName, Phase
from validation.state_validator import StateValidator


def assert_open_turn_state(
    engine: GameEngine,
    *,
    attacker_index: int,
    expected_phase: Phase = Phase.TURN,
) -> None:
    state = engine.get_state()

    assert state.phase == expected_phase
    assert state.turn_order
    assert sorted(state.turn_order) == list(range(len(state.players)))
    assert state.attacker_index == attacker_index
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0

    StateValidator().validate(state)


def assert_engaged_turn_state(
    engine: GameEngine,
    *,
    attacker_index: int,
    trick: str,
    defender_indices: list[int],
    defense_attempts_left: int,
) -> None:
    state = engine.get_state()

    assert state.phase == Phase.TURN
    assert state.turn_order
    assert sorted(state.turn_order) == list(range(len(state.players)))
    assert state.attacker_index == attacker_index
    assert state.current_trick == trick
    assert state.defender_indices == defender_indices
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == defense_attempts_left

    StateValidator().validate(state)


def test_start_game_leaves_engine_in_open_turn_state() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()

    assert_open_turn_state(engine, attacker_index=0)
    assert engine.get_state().history.events[-1].name == EventName.GAME_STARTED


def test_start_turn_enters_engaged_turn_state() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")

    assert_engaged_turn_state(
        engine,
        attacker_index=0,
        trick="kickflip",
        defender_indices=[1],
        defense_attempts_left=engine.get_state().rule_set.defense_attempts,
    )
    assert engine.get_state().history.events[-1].name == EventName.TURN_STARTED


def test_failed_defense_keeps_turn_engaged_with_same_defender() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.get_state().rule_set.defense_attempts = 2

    engine.start_game()
    engine.start_turn("kickflip")
    result = engine.resolve_defense(False)

    assert result == DefenseResolutionStatus.DEFENSE_CONTINUES
    assert_engaged_turn_state(
        engine,
        attacker_index=0,
        trick="kickflip",
        defender_indices=[1],
        defense_attempts_left=1,
    )
    assert engine.get_state().history.events[-1].name == EventName.DEFENSE_FAILED_ATTEMPT


def test_successful_defense_closes_turn_and_rotates_attacker() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")
    result = engine.resolve_defense(True)

    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert_open_turn_state(engine, attacker_index=1)
    assert engine.get_state().validated_tricks == ["kickflip"]
    assert engine.get_state().history.events[-1].name == EventName.TURN_ENDED


def test_game_finished_clears_current_turn_state() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.get_state().rule_set.letters_word = "S"

    engine.start_game()
    engine.start_turn("kickflip")
    result = engine.resolve_defense(False)

    state = engine.get_state()

    assert result == DefenseResolutionStatus.GAME_FINISHED
    assert state.phase == Phase.END
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.players[1].is_active is False
    assert state.validated_tricks == ["kickflip"]
    assert state.history.events[-1].name == EventName.GAME_FINISHED

    StateValidator().validate(state)


def test_cancel_turn_keeps_engine_in_open_turn_state() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.cancel_turn("soul")

    assert_open_turn_state(engine, attacker_index=1)
    assert engine.get_state().validated_tricks == []
    assert engine.get_state().history.events[-1].name == EventName.TURN_FAILED


def test_battle_start_game_leaves_engine_in_open_turn_state(monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [1, 2, 0]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
    )
    engine = GameEngine(match_parameters)

    engine.start_game()

    state = engine.get_state()
    assert state.phase == Phase.TURN
    assert state.turn_order == [1, 2, 0]
    assert state.attacker_index == 1
    assert state.current_trick is None
    assert state.defender_indices == []
    StateValidator().validate(state)
