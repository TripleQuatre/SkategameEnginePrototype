from config.match_parameters import MatchParameters
from core.types import DefenseResolutionStatus, Phase
from engine.game_engine import GameEngine
from validation.state_validator import StateValidator


def assert_valid_state(engine: GameEngine) -> None:
    StateValidator().validate(engine.get_state())


def test_simulation_sequence_with_turn_finish_and_cancel_keeps_state_valid() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    assert_valid_state(engine)

    engine.start_game()
    assert_valid_state(engine)

    engine.start_turn("kickflip")
    assert_valid_state(engine)

    result = engine.resolve_defense(True)
    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert_valid_state(engine)

    engine.cancel_turn("heelflip")
    assert_valid_state(engine)

    state = engine.get_state()
    assert state.phase == Phase.TURN
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0


def test_simulation_sequence_with_failed_attempt_then_undo_keeps_state_valid() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.get_state().rule_set.defense_attempts = 2

    engine.start_game()
    assert_valid_state(engine)

    engine.start_turn("soul")
    assert_valid_state(engine)

    result = engine.resolve_defense(False)
    assert result == DefenseResolutionStatus.DEFENSE_CONTINUES
    assert_valid_state(engine)

    assert engine.undo() is True
    assert_valid_state(engine)

    state = engine.get_state()
    assert state.phase == Phase.TURN
    assert state.current_trick == "soul"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 2
    assert state.validated_tricks == []


def test_simulation_sequence_with_game_finish_then_undo_keeps_state_valid() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.get_state().rule_set.letters_word = "S"

    engine.start_game()
    assert_valid_state(engine)

    engine.start_turn("makio")
    assert_valid_state(engine)

    result = engine.resolve_defense(False)
    assert result == DefenseResolutionStatus.GAME_FINISHED
    assert_valid_state(engine)

    state = engine.get_state()
    assert state.phase == Phase.END
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.validated_tricks == ["makio"]

    assert engine.undo() is True
    assert_valid_state(engine)

    restored_state = engine.get_state()
    assert restored_state.phase == Phase.TURN
    assert restored_state.current_trick == "makio"
    assert restored_state.defender_indices == [1]
    assert restored_state.current_defender_position == 0
    assert restored_state.defense_attempts_left == 1
    assert restored_state.validated_tricks == []


def test_simulation_sequence_with_multiple_undos_keeps_state_valid_at_each_step() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    assert_valid_state(engine)

    engine.start_turn("soul")
    assert_valid_state(engine)

    result = engine.resolve_defense(True)
    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert_valid_state(engine)

    assert engine.undo() is True
    assert_valid_state(engine)

    assert engine.undo() is True
    assert_valid_state(engine)

    assert engine.undo() is True
    assert_valid_state(engine)

    state = engine.get_state()
    assert state.phase == Phase.SETUP
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0

    assert engine.undo() is False
    assert_valid_state(engine)
