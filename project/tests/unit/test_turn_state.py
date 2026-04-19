from core.player import Player
from core.state import GameState
from core.types import Phase, TurnPhase
from match.flow.turn_state import (
    begin_attack_phase,
    begin_defense_phase,
    clear_turn_runtime,
    initialize_open_turn,
    mark_game_finished,
    mark_turn_finished,
    promote_attack_to_defense,
    set_turn_open,
)


def _make_state() -> GameState:
    return GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ]
    )


def test_initialize_open_turn_sets_turn_state_and_clears_runtime() -> None:
    state = _make_state()
    state.current_trick = "Soul"
    state.defender_indices = [1]
    state.current_defender_position = 1
    state.defense_attempts_left = 2

    initialize_open_turn(state)

    assert state.phase == Phase.TURN
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0


def test_begin_defense_phase_sets_runtime_fields() -> None:
    state = _make_state()
    state.current_trick = "Kickflip"

    begin_defense_phase(
        state,
        defender_indices=[1],
        defense_attempts=3,
    )

    assert state.phase == Phase.TURN
    assert state.turn_phase == TurnPhase.DEFENSE
    assert state.current_trick == "Kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 3


def test_begin_attack_phase_sets_attack_runtime_fields() -> None:
    state = _make_state()

    begin_attack_phase(
        state,
        trick="Kickflip",
        attack_attempts=2,
    )

    assert state.phase == Phase.TURN
    assert state.turn_phase == TurnPhase.ATTACK
    assert state.current_trick == "Kickflip"
    assert state.attack_attempts_left == 2
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0


def test_promote_attack_to_defense_clears_attack_attempts() -> None:
    state = _make_state()
    begin_attack_phase(
        state,
        trick="Kickflip",
        attack_attempts=2,
    )

    promote_attack_to_defense(
        state,
        defender_indices=[1],
        defense_attempts=3,
    )

    assert state.phase == Phase.TURN
    assert state.turn_phase == TurnPhase.DEFENSE
    assert state.current_trick == "Kickflip"
    assert state.attack_attempts_left == 0
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 3


def test_mark_turn_finished_only_updates_turn_phase() -> None:
    state = _make_state()
    set_turn_open(state)

    mark_turn_finished(state)

    assert state.phase == Phase.TURN
    assert state.turn_phase == TurnPhase.TURN_FINISHED


def test_mark_game_finished_sets_end_phase() -> None:
    state = _make_state()

    mark_game_finished(state)

    assert state.phase == Phase.END
    assert state.turn_phase == TurnPhase.TURN_FINISHED


def test_clear_turn_runtime_preserves_phase_markers() -> None:
    state = _make_state()
    state.phase = Phase.END
    state.turn_phase = TurnPhase.TURN_FINISHED
    state.current_trick = "Soul"
    state.attack_attempts_left = 1
    state.defender_indices = [1]
    state.current_defender_position = 0
    state.defense_attempts_left = 1

    clear_turn_runtime(state)

    assert state.phase == Phase.END
    assert state.turn_phase == TurnPhase.TURN_FINISHED
    assert state.current_trick is None
    assert state.attack_attempts_left == 0
    assert state.defender_indices == []
