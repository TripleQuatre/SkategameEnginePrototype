from dataclasses import dataclass, replace

from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.match_policies import (
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
    MatchPolicies,
)
from config.structure_config import StructureConfig
from core.events import Event
from core.exceptions import InvalidActionError
from core.player import Player
from core.state import GameState
from core.types import EventName


@dataclass(frozen=True)
class TransitionResult:
    match_config: MatchConfig
    event: Event

    def __getattr__(self, name: str):
        return getattr(self.event, name)


class RosterTransitions:
    def _coerce_match_config(
        self,
        match_config: MatchConfig | MatchParameters,
    ) -> MatchConfig:
        if isinstance(match_config, MatchParameters):
            return match_config.to_match_config()
        return match_config

    def add_player_between_turns(
        self,
        state: GameState,
        match_config: MatchConfig | MatchParameters,
        player_id: str,
        *,
        player_name: str | None = None,
        player_profile_id: str | None = None,
    ) -> TransitionResult:
        match_config = self._coerce_match_config(match_config)
        if any(player.id == player_id for player in state.players):
            raise InvalidActionError("This player already exists in the game.")

        previous_player_profile_ids = self._normalize_player_profile_ids(match_config)
        previous_player_display_names = self._normalize_player_display_names(match_config)
        previous_structure_name = match_config.structure_name
        previous_preset_name = match_config.preset_name
        previous_player_ids = list(match_config.player_ids)
        previous_player_names = [player.name for player in state.players]
        previous_turn_order = list(state.turn_order)
        previous_attacker_id = state.players[state.attacker_index].id
        previous_attacker_name = state.players[state.attacker_index].name

        new_player = Player(id=player_id, name=player_name or player_id)
        state.players.append(new_player)
        state.turn_order.append(len(state.players) - 1)

        next_structure_name = (
            "battle" if match_config.structure_name == "one_vs_one" else match_config.structure_name
        )
        next_match_config = replace(
            match_config,
            player_ids=[player.id for player in state.players],
            player_profile_ids=previous_player_profile_ids + [player_profile_id],
            player_display_names=previous_player_display_names + [new_player.name],
            structure=replace(
                match_config.structure,
                structure_name=next_structure_name,
                policies=self._build_policies_after_addition(
                    match_config,
                    player_id=player_id,
                ),
            ),
            preset_name=None,
        )

        structure_changed = (
            previous_structure_name != next_match_config.structure_name
        )
        preset_invalidated = (
            previous_preset_name is not None and next_match_config.preset_name is None
        )

        result = TransitionResult(
            match_config=next_match_config,
            event=Event(
                name=EventName.PLAYER_JOINED,
                payload={
                    "player_id": new_player.id,
                    "player_name": new_player.name,
                    "previous_structure_name": previous_structure_name,
                    "structure_name": next_match_config.structure_name,
                    "structure_changed": structure_changed,
                    "previous_preset_name": previous_preset_name,
                    "preset_name": next_match_config.preset_name,
                    "preset_invalidated": preset_invalidated,
                    "previous_player_ids": previous_player_ids,
                    "player_ids": [player.id for player in state.players],
                    "previous_player_names": previous_player_names,
                    "player_names": [player.name for player in state.players],
                    "previous_player_count": len(previous_player_ids),
                    "player_count": len(state.players),
                    "previous_turn_order": previous_turn_order,
                    "turn_order": list(state.turn_order),
                    "previous_attacker_id": previous_attacker_id,
                    "previous_attacker_name": previous_attacker_name,
                    "attacker_id": state.players[state.attacker_index].id,
                    "attacker_name": state.players[state.attacker_index].name,
                },
            ),
        )
        return result

    def remove_player_between_turns(
        self,
        state: GameState,
        match_config: MatchConfig | MatchParameters,
        player_id: str,
    ) -> TransitionResult:
        match_config = self._coerce_match_config(match_config)
        removed_index = self._find_player_index(state, player_id)
        if removed_index is None:
            raise InvalidActionError("This player does not exist in the game.")

        if len(state.players) <= 2:
            raise InvalidActionError(
                "Cannot remove a player if fewer than two players would remain."
            )

        previous_structure_name = match_config.structure_name
        previous_preset_name = match_config.preset_name
        previous_player_ids = list(match_config.player_ids)
        previous_player_profile_ids = self._normalize_player_profile_ids(match_config)
        previous_player_display_names = self._normalize_player_display_names(match_config)
        previous_player_names = [player.name for player in state.players]
        previous_turn_order = list(state.turn_order)
        previous_attacker_id = state.players[state.attacker_index].id
        previous_attacker_name = state.players[state.attacker_index].name
        removed_player = state.players[removed_index]

        new_attacker_index = self._compute_attacker_after_removal(state, removed_index)
        remaining_players = [
            player
            for index, player in enumerate(state.players)
            if index != removed_index
        ]
        remapped_turn_order = self._remap_turn_order_after_removal(
            state, removed_index
        )

        state.players = remaining_players
        state.turn_order = remapped_turn_order
        state.attacker_index = new_attacker_index

        next_structure = replace(
            match_config.structure,
            policies=self._build_policies_after_removal(
                match_config,
                player_id=player_id,
            ),
        )
        if len(state.players) == 2 and match_config.structure_name == "battle":
            next_structure = replace(
                next_structure,
                structure_name="one_vs_one",
                policies=self._normalize_policies_for_one_vs_one(
                    next_structure.policies
                ),
            )
            state.turn_order = [0, 1]
        next_match_config = replace(
            match_config,
            player_ids=[player.id for player in state.players],
            player_profile_ids=[
                profile_id
                for index, profile_id in enumerate(previous_player_profile_ids)
                if index != removed_index
            ],
            player_display_names=[
                display_name
                for index, display_name in enumerate(previous_player_display_names)
                if index != removed_index
            ],
            structure=next_structure,
            preset_name=None,
        )

        structure_changed = (
            previous_structure_name != next_match_config.structure_name
        )
        preset_invalidated = (
            previous_preset_name is not None and next_match_config.preset_name is None
        )

        result = TransitionResult(
            match_config=next_match_config,
            event=Event(
                name=EventName.PLAYER_REMOVED,
                payload={
                    "player_id": removed_player.id,
                    "player_name": removed_player.name,
                    "previous_structure_name": previous_structure_name,
                    "structure_name": next_match_config.structure_name,
                    "structure_changed": structure_changed,
                    "previous_preset_name": previous_preset_name,
                    "preset_name": next_match_config.preset_name,
                    "preset_invalidated": preset_invalidated,
                    "previous_player_ids": previous_player_ids,
                    "player_ids": [player.id for player in state.players],
                    "previous_player_names": previous_player_names,
                    "player_names": [player.name for player in state.players],
                    "previous_player_count": len(previous_player_ids),
                    "player_count": len(state.players),
                    "previous_turn_order": previous_turn_order,
                    "turn_order": list(state.turn_order),
                    "previous_attacker_id": previous_attacker_id,
                    "previous_attacker_name": previous_attacker_name,
                    "attacker_id": state.players[state.attacker_index].id,
                    "attacker_name": state.players[state.attacker_index].name,
                },
            ),
        )
        return result

    def _find_player_index(self, state: GameState, player_id: str) -> int | None:
        for index, player in enumerate(state.players):
            if player.id == player_id:
                return index
        return None

    def _normalize_player_profile_ids(
        self,
        match_config: MatchConfig,
    ) -> list[str | None]:
        if not match_config.player_profile_ids:
            return [None] * len(match_config.player_ids)
        return list(match_config.player_profile_ids)

    def _normalize_player_display_names(
        self,
        match_config: MatchConfig,
    ) -> list[str]:
        if not match_config.player_display_names:
            return list(match_config.player_ids)
        return list(match_config.player_display_names)

    def _remap_turn_order_after_removal(
        self, state: GameState, removed_index: int
    ) -> list[int]:
        old_to_new: dict[int, int] = {}
        next_index = 0

        for index in range(len(state.players)):
            if index == removed_index:
                continue
            old_to_new[index] = next_index
            next_index += 1

        return [
            old_to_new[index]
            for index in state.turn_order
            if index != removed_index
        ]

    def _compute_attacker_after_removal(
        self, state: GameState, removed_index: int
    ) -> int:
        if state.attacker_index != removed_index:
            old_to_new = {
                old_index: new_index
                for new_index, old_index in enumerate(
                    index
                    for index in range(len(state.players))
                    if index != removed_index
                )
            }
            return old_to_new[state.attacker_index]

        current_position = state.turn_order.index(removed_index)
        turn_order_length = len(state.turn_order)

        for offset in range(1, turn_order_length + 1):
            candidate_index = state.turn_order[
                (current_position + offset) % turn_order_length
            ]
            if candidate_index == removed_index:
                continue
            if not state.players[candidate_index].is_active:
                continue

            old_to_new = {
                old_index: new_index
                for new_index, old_index in enumerate(
                    index
                    for index in range(len(state.players))
                    if index != removed_index
                )
            }
            return old_to_new[candidate_index]

        raise InvalidActionError("No valid attacker can be assigned after removal.")

    def _build_policies_after_addition(
        self,
        match_config: MatchConfig,
        *,
        player_id: str,
    ) -> MatchPolicies:
        policies = match_config.policies
        explicit_player_order = tuple(policies.explicit_player_order)

        if policies.initial_turn_order == InitialTurnOrderPolicy.EXPLICIT_CHOICE:
            return replace(
                policies,
                explicit_player_order=explicit_player_order + (player_id,),
            )

        if policies.initial_turn_order == InitialTurnOrderPolicy.RELEVANCE:
            return replace(
                policies,
                initial_turn_order=InitialTurnOrderPolicy.EXPLICIT_CHOICE,
                relevance_criterion=None,
                explicit_player_order=explicit_player_order + (player_id,),
            )

        return policies

    def _build_policies_after_removal(
        self,
        match_config: MatchConfig,
        *,
        player_id: str,
    ) -> MatchPolicies:
        policies = match_config.policies
        if not policies.explicit_player_order:
            return policies

        explicit_player_order = tuple(
            configured_player_id
            for configured_player_id in policies.explicit_player_order
            if configured_player_id != player_id
        )

        if policies.initial_turn_order == InitialTurnOrderPolicy.RELEVANCE:
            remaining_profile_ids = [
                profile_id
                for configured_player_id, profile_id in zip(
                    match_config.player_ids,
                    self._normalize_player_profile_ids(match_config),
                    strict=True,
                )
                if configured_player_id != player_id
            ]
            if any(profile_id is None for profile_id in remaining_profile_ids):
                return replace(
                    policies,
                    initial_turn_order=InitialTurnOrderPolicy.EXPLICIT_CHOICE,
                    relevance_criterion=None,
                    explicit_player_order=explicit_player_order,
                )

        return replace(
            policies,
            explicit_player_order=explicit_player_order,
        )

    def _normalize_policies_for_one_vs_one(
        self,
        policies: MatchPolicies,
    ) -> MatchPolicies:
        if policies.defender_order == DefenderOrderPolicy.FOLLOW_TURN_ORDER:
            return policies
        return replace(
            policies,
            defender_order=DefenderOrderPolicy.FOLLOW_TURN_ORDER,
        )
