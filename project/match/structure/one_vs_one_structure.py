from core.exceptions import InvalidStateError
from core.state import GameState
from match.flow.turn_state import clear_turn_runtime, set_turn_open
from match.structure.base_structure import BaseStructure


class OneVsOneStructure(BaseStructure):
    structure_name = "one_vs_one"

    def initialize_game(self, state: GameState) -> None:
        set_turn_open(state)
        state.turn_order = [0, 1]
        state.attacker_index = state.turn_order[0]
        clear_turn_runtime(state)
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
