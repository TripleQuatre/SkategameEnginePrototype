from application.game_session import GameSession as GameEngine
import match.structure.battle_structure as battle_structure_module

from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from core.types import DefenseResolutionStatus, Phase
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
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        rule_set=RuleSetConfig(defense_attempts=2),
    )
    engine = GameEngine(match_parameters)

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
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        rule_set=RuleSetConfig(letters_word="S"),
    )
    engine = GameEngine(match_parameters)

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


def test_battle_simulation_sequence_keeps_state_valid(monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    assert_valid_state(engine)

    engine.start_turn("kickflip")
    assert_valid_state(engine)

    result = engine.resolve_defense(True)
    assert result == DefenseResolutionStatus.DEFENSE_CONTINUES
    assert_valid_state(engine)

    result = engine.resolve_defense(False)
    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert_valid_state(engine)

    state = engine.get_state()
    assert state.attacker_index == 0
    assert state.players[1].score == 1


def test_battle_eliminated_previous_defender_keeps_state_valid(monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
        rule_set=RuleSetConfig(letters_word="S"),
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    assert_valid_state(engine)

    engine.start_turn("makio")
    assert_valid_state(engine)

    result = engine.resolve_defense(False)
    assert result == DefenseResolutionStatus.DEFENSE_CONTINUES
    assert_valid_state(engine)

    state = engine.get_state()
    assert state.players[0].is_active is False
    assert state.current_defender_position == 1
    assert state.defender_indices == [0, 1]


def test_reconfiguration_sequence_keeps_state_valid_at_each_step() -> None:
    engine = GameEngine(MatchParameters(player_ids=["p1", "p2"]))

    engine.start_game()
    assert_valid_state(engine)

    engine.add_player_between_turns("p3")
    assert_valid_state(engine)

    engine.remove_player_between_turns("p2")
    assert_valid_state(engine)

    assert engine.undo() is True
    assert_valid_state(engine)

    assert engine.undo() is True
    assert_valid_state(engine)
