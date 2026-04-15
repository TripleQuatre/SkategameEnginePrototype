import random

from config.match_policies import InitialTurnOrderPolicy
from core.exceptions import InvalidStateError
from core.state import GameState
from core.types import Phase

from modes.base_mode import BaseMode


class BattleMode(BaseMode):
    def initialize_game(self, state: GameState) -> None:
        state.phase = Phase.TURN
        state.turn_order = list(range(len(state.players)))

        if self.policies.initial_turn_order == InitialTurnOrderPolicy.RANDOMIZED:
            random.shuffle(state.turn_order)

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
        if len(state.players) < 3:
            raise InvalidStateError("Battle mode requires at least three players.")

        if state.turn_order and len(state.turn_order) != len(state.players):
            raise InvalidStateError(
                "Battle mode requires turn_order to include every player."
            )
