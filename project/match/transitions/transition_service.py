from dataclasses import dataclass

from config.match_parameters import MatchParameters
from core.player import Player
from core.events import Event
from core.state import GameState
from match.flow.turn_flow import TurnFlow
from match.structure.base_structure import BaseStructure
from match.structure.structure_factory import StructureFactory
from validation.action_validator import ActionValidator
from validation.config_validator import ConfigValidator
from validation.state_validator import StateValidator

from match.transitions.roster_transitions import RosterTransitions


@dataclass
class TransitionApplication:
    event: Event
    structure: BaseStructure
    game_flow: TurnFlow

    @property
    def structure_name(self) -> str:
        return self.structure.structure_name

    @property
    def previous_structure_name(self) -> str | None:
        return self.event.payload.get("previous_structure_name")

    @property
    def structure_changed(self) -> bool:
        return bool(self.event.payload.get("structure_changed"))

    @property
    def preset_name(self) -> str | None:
        return self.event.payload.get("preset_name")

    @property
    def previous_preset_name(self) -> str | None:
        return self.event.payload.get("previous_preset_name")

    @property
    def preset_invalidated(self) -> bool:
        if "preset_invalidated" in self.event.payload:
            return bool(self.event.payload["preset_invalidated"])
        previous_preset_name = self.previous_preset_name
        return previous_preset_name is not None and self.preset_name is None

    @property
    def previous_player_ids(self) -> list[str]:
        return list(self.event.payload.get("previous_player_ids", []))

    @property
    def player_ids(self) -> list[str]:
        return list(self.event.payload.get("player_ids", []))

    @property
    def previous_player_count(self) -> int:
        if "previous_player_count" in self.event.payload:
            return int(self.event.payload["previous_player_count"])
        return len(self.previous_player_ids)

    @property
    def player_count(self) -> int:
        if "player_count" in self.event.payload:
            return int(self.event.payload["player_count"])
        return len(self.player_ids)

    @property
    def previous_turn_order(self) -> list[int]:
        return list(self.event.payload.get("previous_turn_order", []))

    @property
    def turn_order(self) -> list[int]:
        return list(self.event.payload.get("turn_order", []))

    @property
    def previous_attacker_id(self) -> str | None:
        return self.event.payload.get("previous_attacker_id")

    @property
    def attacker_id(self) -> str | None:
        return self.event.payload.get("attacker_id")

    @property
    def previous_attacker_name(self) -> str | None:
        return self.event.payload.get("previous_attacker_name")

    @property
    def attacker_name(self) -> str | None:
        return self.event.payload.get("attacker_name")


@dataclass
class RuntimeSession:
    state: GameState
    match_parameters: MatchParameters
    structure: BaseStructure
    game_flow: TurnFlow


class MatchTransitionService:
    def __init__(
        self,
        config_validator: ConfigValidator,
        structure_factory: StructureFactory | None = None,
        roster_transitions: RosterTransitions | None = None,
    ) -> None:
        self.config_validator = config_validator
        self.structure_factory = structure_factory or StructureFactory()
        self.roster_transitions = roster_transitions or RosterTransitions()

    def create_initial_runtime(
        self,
        match_parameters: MatchParameters,
        state_validator: StateValidator,
    ) -> RuntimeSession:
        self.config_validator.validate_match_parameters(match_parameters)

        state = GameState(
            players=[
                Player(id=player_id, name=player_id)
                for player_id in match_parameters.player_ids
            ]
        )
        state.rule_set = match_parameters.rule_set

        self.config_validator.validate_rule_set(state.rule_set)
        state_validator.validate(state)

        structure, game_flow = self.build_runtime(state, match_parameters)
        return RuntimeSession(
            state=state,
            match_parameters=match_parameters,
            structure=structure,
            game_flow=game_flow,
        )

    def restore_runtime(
        self,
        state: GameState,
        match_parameters: MatchParameters,
        state_validator: StateValidator,
    ) -> RuntimeSession:
        state.rule_set = match_parameters.rule_set
        self.config_validator.validate_match_parameters(match_parameters)
        self.config_validator.validate_rule_set(match_parameters.rule_set)
        state_validator.validate(state)

        structure, game_flow = self.build_runtime(state, match_parameters)
        return RuntimeSession(
            state=state,
            match_parameters=match_parameters,
            structure=structure,
            game_flow=game_flow,
        )

    def add_player_between_turns(
        self,
        state: GameState,
        match_parameters: MatchParameters,
        action_validator: ActionValidator,
        player_id: str,
    ) -> TransitionApplication:
        action_validator.validate_add_player_between_turns(state, player_id)

        event = self.roster_transitions.add_player_between_turns(
            state,
            match_parameters,
            player_id,
        )
        return self._build_transition_application(state, match_parameters, event)

    def execute_add_player_between_turns(
        self,
        state: GameState,
        match_parameters: MatchParameters,
        action_validator: ActionValidator,
        state_validator: StateValidator,
        player_id: str,
    ) -> TransitionApplication:
        transition = self.add_player_between_turns(
            state,
            match_parameters,
            action_validator,
            player_id,
        )
        self.apply_transition(state, transition, state_validator)
        return transition

    def remove_player_between_turns(
        self,
        state: GameState,
        match_parameters: MatchParameters,
        action_validator: ActionValidator,
        player_id: str,
    ) -> TransitionApplication:
        action_validator.validate_remove_player_between_turns(state, player_id)

        event = self.roster_transitions.remove_player_between_turns(
            state,
            match_parameters,
            player_id,
        )
        return self._build_transition_application(state, match_parameters, event)

    def execute_remove_player_between_turns(
        self,
        state: GameState,
        match_parameters: MatchParameters,
        action_validator: ActionValidator,
        state_validator: StateValidator,
        player_id: str,
    ) -> TransitionApplication:
        transition = self.remove_player_between_turns(
            state,
            match_parameters,
            action_validator,
            player_id,
        )
        self.apply_transition(state, transition, state_validator)
        return transition

    def apply_transition(
        self,
        state: GameState,
        transition: TransitionApplication,
        state_validator: StateValidator,
    ) -> RuntimeSession:
        state.history.add_event(transition.event)
        state_validator.validate(state)
        transition.structure.validate(state)
        return RuntimeSession(
            state=state,
            match_parameters=transition.game_flow.match_parameters,
            structure=transition.structure,
            game_flow=transition.game_flow,
        )

    def build_runtime(
        self,
        state: GameState,
        match_parameters: MatchParameters,
    ) -> tuple[BaseStructure, TurnFlow]:
        self.config_validator.validate_match_parameters(match_parameters)
        structure = self.structure_factory.create(
            match_parameters.structure_name,
            match_parameters.policies,
        )
        structure.validate(state)
        game_flow = TurnFlow(structure, match_parameters)
        return structure, game_flow

    def _build_transition_application(
        self,
        state: GameState,
        match_parameters: MatchParameters,
        event: Event,
    ) -> TransitionApplication:
        structure, game_flow = self.build_runtime(state, match_parameters)
        return TransitionApplication(
            event=event,
            structure=structure,
            game_flow=game_flow,
        )
