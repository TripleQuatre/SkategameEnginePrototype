from core.state import GameState
from core.types import Phase, TurnPhase


def clear_turn_runtime(state: GameState) -> None:
    state.current_trick = None
    state.attack_attempts_left = 0
    state.defender_indices = []
    state.current_defender_position = 0
    state.defense_attempts_left = 0


def set_turn_open(state: GameState) -> None:
    state.phase = Phase.TURN
    state.turn_phase = TurnPhase.TURN_OPEN


def initialize_open_turn(state: GameState) -> None:
    set_turn_open(state)
    clear_turn_runtime(state)


def begin_defense_phase(
    state: GameState,
    defender_indices: list[int],
    defense_attempts: int,
) -> None:
    state.phase = Phase.TURN
    state.turn_phase = TurnPhase.DEFENSE
    state.defender_indices = list(defender_indices)
    state.current_defender_position = 0
    state.defense_attempts_left = defense_attempts


def begin_attack_phase(
    state: GameState,
    trick: str,
    attack_attempts: int,
) -> None:
    state.phase = Phase.TURN
    state.turn_phase = TurnPhase.ATTACK
    state.current_trick = trick
    state.attack_attempts_left = attack_attempts
    state.defender_indices = []
    state.current_defender_position = 0
    state.defense_attempts_left = 0


def promote_attack_to_defense(
    state: GameState,
    defender_indices: list[int],
    defense_attempts: int,
) -> None:
    state.turn_phase = TurnPhase.DEFENSE
    state.attack_attempts_left = 0
    begin_defense_phase(
        state,
        defender_indices=defender_indices,
        defense_attempts=defense_attempts,
    )


def mark_turn_finished(state: GameState) -> None:
    state.turn_phase = TurnPhase.TURN_FINISHED


def mark_game_finished(state: GameState) -> None:
    state.phase = Phase.END
    state.turn_phase = TurnPhase.TURN_FINISHED
