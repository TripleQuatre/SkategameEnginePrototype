from abc import ABC, abstractmethod

from config.match_policies import (
    AttackerRotationPolicy,
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
    MatchPolicies,
)
from core.exceptions import InvalidStateError
from core.state import GameState


class BaseStructure(ABC):
    structure_name = ""

    def __init__(self, policies: MatchPolicies | None = None) -> None:
        self.policies = policies or MatchPolicies()

    @abstractmethod
    def initialize_game(self, state: GameState) -> None:
        pass

    @abstractmethod
    def build_defender_indices(self, state: GameState) -> list[int]:
        pass

    @abstractmethod
    def get_next_attacker_index(self, state: GameState) -> int | None:
        pass

    @abstractmethod
    def validate(self, state: GameState) -> None:
        pass

    def _build_defender_indices_from_turn_order(self, state: GameState) -> list[int]:
        defender_indices = [
            index
            for index in state.turn_order
            if index != state.attacker_index and state.players[index].is_active
        ]

        if self.policies.defender_order == DefenderOrderPolicy.REVERSE_TURN_ORDER:
            defender_indices.reverse()

        return defender_indices

    def _get_next_attacker_from_turn_order(self, state: GameState) -> int | None:
        if self.policies.attacker_rotation != AttackerRotationPolicy.FOLLOW_TURN_ORDER:
            raise ValueError(
                f"Unsupported attacker rotation policy: {self.policies.attacker_rotation}"
            )

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

    def _build_initial_turn_order(self, state: GameState) -> list[int]:
        base_turn_order = list(range(len(state.players)))
        policy = self.policies.initial_turn_order

        if policy == InitialTurnOrderPolicy.FIXED_PLAYER_ORDER:
            return base_turn_order

        if policy == InitialTurnOrderPolicy.RANDOMIZED:
            randomized_order = list(base_turn_order)
            import random

            random.shuffle(randomized_order)
            return randomized_order

        if policy in {
            InitialTurnOrderPolicy.EXPLICIT_CHOICE,
            InitialTurnOrderPolicy.RELEVANCE,
        }:
            explicit_player_order = tuple(self.policies.explicit_player_order)
            player_index_by_id = {
                player.id: index for index, player in enumerate(state.players)
            }
            try:
                return [
                    player_index_by_id[player_id]
                    for player_id in explicit_player_order
                ]
            except KeyError as error:
                raise InvalidStateError(
                    "Explicit player order references an unknown player."
                ) from error

        raise InvalidStateError(f"Unsupported initial turn order policy: {policy}")
