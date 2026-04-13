from core.exceptions import InvalidStateError
from core.state import GameState
from core.types import Phase


class StateValidator:
    def validate(self, state: GameState) -> None:
        if len(state.players) < 2:
            raise InvalidStateError("State must contain at least two players.")

        if state.attacker_index < 0 or state.attacker_index >= len(state.players):
            raise InvalidStateError("attacker_index is out of range.")

        if state.current_defender_position < 0:
            raise InvalidStateError("current_defender_position cannot be negative.")

        if state.defense_attempts_left < 0:
            raise InvalidStateError("defense_attempts_left cannot be negative.")

        seen_defender_indices: set[int] = set()

        for defender_index in state.defender_indices:
            if defender_index < 0 or defender_index >= len(state.players):
                raise InvalidStateError("defender_indices contains an out-of-range index.")

            if defender_index == state.attacker_index:
                raise InvalidStateError(
                    "attacker_index cannot also appear in defender_indices."
                )

            if defender_index in seen_defender_indices:
                raise InvalidStateError("defender_indices cannot contain duplicates.")

            if not state.players[defender_index].is_active:
                raise InvalidStateError(
                    "defender_indices cannot contain inactive players."
                )

            seen_defender_indices.add(defender_index)

        if state.current_trick is None:
            if state.defender_indices:
                raise InvalidStateError(
                    "defender_indices must be empty when no trick is engaged."
                )

            if state.current_defender_position != 0:
                raise InvalidStateError(
                    "current_defender_position must be 0 when no trick is engaged."
                )

            if state.defense_attempts_left != 0:
                raise InvalidStateError(
                    "defense_attempts_left must be 0 when no trick is engaged."
                )

            return

        if state.phase != Phase.TURN:
            raise InvalidStateError("A trick can only be engaged during TURN phase.")

        if not state.defender_indices:
            raise InvalidStateError(
                "defender_indices cannot be empty when a trick is engaged."
            )

        if state.current_defender_position >= len(state.defender_indices):
            raise InvalidStateError(
                "current_defender_position is out of range for the engaged trick."
            )

        if state.defense_attempts_left <= 0:
            raise InvalidStateError(
                "defense_attempts_left must be positive when a trick is engaged."
            )
