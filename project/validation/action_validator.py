from core.exceptions import InvalidActionError
from core.state import GameState
from core.types import Phase


class ActionValidator:
    def validate_start_turn(self, state: GameState, trick: str) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError("Cannot start a turn outside TURN phase.")

        if not trick:
            raise InvalidActionError("A trick is required to start a turn.")

        if not state.players[state.attacker_index].is_active:
            raise InvalidActionError("Current attacker is not active.")

    def validate_resolve_defense(self, state: GameState) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError("Cannot resolve defense outside TURN phase.")

        if state.current_trick is None:
            raise InvalidActionError("No current trick to defend.")

        if state.current_defender_position >= len(state.defender_indices):
            raise InvalidActionError("No current defender to resolve.")