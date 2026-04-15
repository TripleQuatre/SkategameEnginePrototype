from core.exceptions import InvalidStateError
from core.state import GameState
from core.types import Phase

from modes.base_mode import BaseMode


class OneVsOneMode(BaseMode):
    def initialize_game(self, state: GameState) -> None:
        state.phase = Phase.TURN
        state.turn_order = [0, 1]
        state.attacker_index = state.turn_order[0]
        state.current_trick = None
        state.defender_indices = []
        state.current_defender_position = 0
        state.defense_attempts_left = 0
        state.validated_tricks = []

    def build_defender_indices(self, state: GameState) -> list[int]:
        return self._build_defender_indices_from_turn_order(state)

    def get_next_attacker_index(self, state: GameState) -> int | None:
        return self._get_next_attacker_from_turn_order(state)

    def validate(self, state: GameState) -> None:
        if len(state.players) != 2:
            raise InvalidStateError("One vs one mode requires exactly two players.")

        if state.turn_order and state.turn_order != [0, 1]:
            raise InvalidStateError(
                "One vs one mode requires a fixed turn_order of [0, 1]."
            )
