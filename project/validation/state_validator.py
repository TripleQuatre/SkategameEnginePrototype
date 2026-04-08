from core.exceptions import InvalidStateError
from core.state import GameState


class StateValidator:
    def validate(self, state: GameState) -> None:
        if len(state.players) < 2:
            raise InvalidStateError("State must contain at least two players.")

        if state.attacker_index < 0 or state.attacker_index >= len(state.players):
            raise InvalidStateError("attacker_index is out of range.")

        if state.current_defender_position < 0:
            raise InvalidStateError("current_defender_position cannot be negative.")

        for defender_index in state.defender_indices:
            if defender_index < 0 or defender_index >= len(state.players):
                raise InvalidStateError("defender_indices contains an out-of-range index.")

        if state.defense_attempts_left < 0:
            raise InvalidStateError("defense_attempts_left cannot be negative.")