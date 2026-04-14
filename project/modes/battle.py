import random

from core.exceptions import InvalidStateError
from core.state import GameState
from core.types import Phase

from modes.base_mode import BaseMode


class BattleMode(BaseMode):
    def initialize_game(self, state: GameState) -> None:
        state.phase = Phase.TURN
        state.turn_order = list(range(len(state.players)))
        random.shuffle(state.turn_order)
        state.attacker_index = state.turn_order[0]
        state.current_trick = None
        state.defender_indices = []
        state.current_defender_position = 0
        state.defense_attempts_left = 0
        state.validated_tricks = []

    def build_defender_indices(self, state: GameState) -> list[int]:
        return [
            index
            for index in state.turn_order
            if index != state.attacker_index and state.players[index].is_active
        ]

    def get_next_attacker_index(self, state: GameState) -> int | None:
        if not state.turn_order:
            return None

        current_position = state.turn_order.index(state.attacker_index)
        turn_order_length = len(state.turn_order)

        for offset in range(1, turn_order_length + 1):
            candidate_index = state.turn_order[
                (current_position + offset) % turn_order_length
            ]
            if state.players[candidate_index].is_active:
                return candidate_index

        return None

    def validate(self, state: GameState) -> None:
        if len(state.players) < 3:
            raise InvalidStateError("Battle mode requires at least three players.")

        if state.turn_order and len(state.turn_order) != len(state.players):
            raise InvalidStateError(
                "Battle mode requires turn_order to include every player."
            )
