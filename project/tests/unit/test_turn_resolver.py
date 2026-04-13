import pytest

from core.player import Player
from core.state import GameState
from core.types import EventName, Phase
from engine.turn_resolver import TurnResolver
from rules.rules_registry import RulesRegistry


@pytest.fixture
def resolver() -> TurnResolver:
    return TurnResolver(RulesRegistry())


@pytest.fixture
def state() -> GameState:
    players = [
        Player(id="p1", name="Player 1"),
        Player(id="p2", name="Player 2"),
    ]
    state = GameState(players=players)
    state.phase = Phase.TURN
    state.attacker_index = 0
    state.defender_indices = [1]
    state.current_defender_position = 0
    state.defense_attempts_left = 2
    state.current_trick = "kickflip"
    return state


def test_resolve_defense_success_moves_to_next_defender(
    resolver: TurnResolver, state: GameState
) -> None:
    turn_finished = resolver.resolve_defense_attempt(state, success=True)

    assert turn_finished is True
    assert state.current_defender_position == 1
    assert state.players[1].score == 0
    assert state.history.events[-1].name == EventName.DEFENSE_SUCCEEDED


def test_resolve_defense_failed_attempt_keeps_same_defender(
    resolver: TurnResolver, state: GameState
) -> None:
    turn_finished = resolver.resolve_defense_attempt(state, success=False)

    assert turn_finished is False
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 1
    assert state.players[1].score == 0
    assert state.history.events[-1].name == EventName.DEFENSE_FAILED_ATTEMPT


def test_resolve_defense_final_failure_applies_letter_penalty(
    resolver: TurnResolver, state: GameState
) -> None:
    state.defense_attempts_left = 1

    turn_finished = resolver.resolve_defense_attempt(state, success=False)

    assert turn_finished is True
    assert state.current_defender_position == 1
    assert state.players[1].score == 1
    assert state.history.events[-1].name == EventName.LETTER_RECEIVED
    assert state.history.events[-1].payload["penalty_display"] == "S"
