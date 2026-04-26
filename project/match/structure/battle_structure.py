import random

from core.exceptions import InvalidStateError
from core.state import GameState
from match.flow.turn_state import clear_turn_runtime, set_turn_open
from match.structure.base_structure import BaseStructure


class BattleStructure(BaseStructure):
    structure_name = "battle"

    def initialize_game(self, state: GameState) -> None:
        set_turn_open(state)
        state.turn_order = self._build_initial_turn_order(state)
        state.attacker_index = state.turn_order[0]
        clear_turn_runtime(state)
        state.validated_tricks = []
        state.validated_trick_data = []
        state.failed_attack_trick_data = []
        state.failed_attack_turn_trick_keys = []

    def build_defender_indices(self, state: GameState) -> list[int]:
        return self._build_defender_indices_from_turn_order(state)

    def get_next_attacker_index(self, state: GameState) -> int | None:
        return self._get_next_attacker_from_turn_order(state)

    def validate(self, state: GameState) -> None:
        if len(state.players) < 3:
            raise InvalidStateError("Battle mode requires at least three players.")

        if state.turn_order and len(state.turn_order) != len(state.players):
            raise InvalidStateError(
                "Battle mode requires turn_order to include every player."
            )
