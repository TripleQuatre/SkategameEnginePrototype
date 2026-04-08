import pytest

from core.player import Player
from core.state import GameState
from core.types import Phase, DefenseResolutionStatus
from engine.game_flow import GameFlow


@pytest.fixture
def game_flow() -> GameFlow:
    return GameFlow()


@pytest.fixture
def state() -> GameState:
    players = [
        Player(id="p1", name="Player 1"),
        Player(id="p2", name="Player 2"),
    ]
    return GameState(players=players)


def test_start_game_sets_turn_phase(game_flow: GameFlow, state: GameState) -> None:
    game_flow.start_game(state)

    assert state.phase == Phase.TURN
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.history.events[-1].name == "game_started"


def test_start_turn_sets_trick_and_defenders(
    game_flow: GameFlow, state: GameState
) -> None:
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == state.rule_set.defense_attempts
    assert state.history.events[-1].name == "turn_started"


def test_resolve_defense_returns_defense_continues_on_failed_attempt(
    game_flow: GameFlow, state: GameState
) -> None:
    state.rule_set.defense_attempts = 2
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    result = game_flow.resolve_defense(state, success=False)

    assert result == DefenseResolutionStatus.DEFENSE_CONTINUES
    assert state.players[1].score == 0
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 1


def test_resolve_defense_returns_turn_finished_on_success(
    game_flow: GameFlow, state: GameState
) -> None:
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    result = game_flow.resolve_defense(state, success=True)

    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert state.attacker_index == 1
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == "turn_ended"


def test_resolve_defense_returns_game_finished_on_final_elimination(
    game_flow: GameFlow, state: GameState
) -> None:
    state.rule_set.letters_word = "S"
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    result = game_flow.resolve_defense(state, success=False)

    assert result == DefenseResolutionStatus.GAME_FINISHED
    assert state.phase == Phase.END
    assert state.players[1].is_active is False
    assert state.history.events[-1].name == "game_finished"