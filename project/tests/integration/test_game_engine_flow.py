from config.match_parameters import MatchParameters
from core.types import Phase, DefenseResolutionStatus
from engine.game_engine import GameEngine


def test_game_engine_can_start_a_game() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()

    state = engine.get_state()
    assert state.phase == Phase.TURN
    assert state.attacker_index == 0
    assert state.history.events[-1].name == "game_started"


def test_game_engine_can_start_a_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")

    state = engine.get_state()
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == state.rule_set.defense_attempts
    assert state.history.events[-1].name == "turn_started"


def test_game_engine_defense_failure_can_finish_game() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.state.rule_set.letters_word = "S"

    engine.start_game()
    engine.start_turn("kickflip")
    result = engine.resolve_defense(False)

    state = engine.get_state()
    assert result == DefenseResolutionStatus.GAME_FINISHED
    assert state.phase == Phase.END
    assert state.players[1].score == 1
    assert state.players[1].is_active is False
    assert state.history.events[-1].name == "game_finished"


def test_game_engine_defense_success_finishes_turn_and_rotates_attacker() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")
    result = engine.resolve_defense(True)

    state = engine.get_state()
    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert state.attacker_index == 1
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == "turn_ended"