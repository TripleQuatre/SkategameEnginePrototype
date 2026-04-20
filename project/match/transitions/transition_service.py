from dataclasses import dataclass

from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.setup_translator import SetupTranslator
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
    match_config: MatchConfig
    structure: BaseStructure
    game_flow: TurnFlow
    legacy_match_parameters: MatchParameters | None = None

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
    match_config: MatchConfig
    structure: BaseStructure
    game_flow: TurnFlow
    legacy_match_parameters: MatchParameters | None = None

    @property
    def match_parameters(self) -> MatchParameters:
        if self.legacy_match_parameters is not None:
            return self.legacy_match_parameters
        return SetupTranslator().from_match_config(self.match_config)


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
        self.setup_translator = SetupTranslator()

    def _coerce_match_config(
        self,
        match_config: MatchConfig | MatchParameters,
    ) -> MatchConfig:
        if isinstance(match_config, MatchParameters):
            return self.setup_translator.from_match_parameters(match_config)
        return match_config

    def _sync_legacy_match_parameters(
        self,
        legacy_match_parameters: MatchParameters,
        match_config: MatchConfig,
    ) -> None:
        updated = self.setup_translator.from_match_config(match_config)
        legacy_match_parameters.player_ids = updated.player_ids
        legacy_match_parameters.structure_name = updated.structure_name
        legacy_match_parameters.rule_set = updated.rule_set
        legacy_match_parameters.policies = updated.policies
        legacy_match_parameters.preset_name = updated.preset_name

    def create_initial_runtime(
        self,
        match_config: MatchConfig | MatchParameters,
        state_validator: StateValidator,
    ) -> RuntimeSession:
        legacy_match_parameters = (
            match_config if isinstance(match_config, MatchParameters) else None
        )
        match_config = self._coerce_match_config(match_config)
        self.config_validator.validate_match_config(match_config)

        state = GameState(
            players=[
                Player(id=player_id, name=player_id)
                for player_id in match_config.player_ids
            ]
        )
        state.rule_set = (
            legacy_match_parameters.rule_set
            if legacy_match_parameters is not None
            else match_config.to_rule_set_config()
        )

        state_validator.validate(state)

        structure, game_flow = self.build_runtime(state, match_config)
        return RuntimeSession(
            state=state,
            match_config=match_config,
            structure=structure,
            game_flow=game_flow,
            legacy_match_parameters=legacy_match_parameters,
        )

    def restore_runtime(
        self,
        state: GameState,
        match_config: MatchConfig | MatchParameters,
        state_validator: StateValidator,
    ) -> RuntimeSession:
        legacy_match_parameters = (
            match_config if isinstance(match_config, MatchParameters) else None
        )
        match_config = self._coerce_match_config(match_config)
        state.rule_set = (
            legacy_match_parameters.rule_set
            if legacy_match_parameters is not None
            else match_config.to_rule_set_config()
        )
        self.config_validator.validate_match_config(match_config)
        state_validator.validate(state)

        structure, game_flow = self.build_runtime(state, match_config)
        return RuntimeSession(
            state=state,
            match_config=match_config,
            structure=structure,
            game_flow=game_flow,
            legacy_match_parameters=legacy_match_parameters,
        )

    def add_player_between_turns(
        self,
        state: GameState,
        match_config: MatchConfig | MatchParameters,
        action_validator: ActionValidator,
        player_id: str,
    ) -> TransitionApplication:
        legacy_match_parameters = (
            match_config if isinstance(match_config, MatchParameters) else None
        )
        match_config = self._coerce_match_config(match_config)
        action_validator.validate_add_player_between_turns(state, player_id)

        transition_result = self.roster_transitions.add_player_between_turns(
            state,
            match_config,
            player_id,
        )
        if legacy_match_parameters is not None:
            self._sync_legacy_match_parameters(
                legacy_match_parameters,
                transition_result.match_config,
            )
        return self._build_transition_application(
            state,
            transition_result.match_config,
            transition_result.event,
            legacy_match_parameters=legacy_match_parameters,
        )

    def execute_add_player_between_turns(
        self,
        state: GameState,
        match_config: MatchConfig | MatchParameters,
        action_validator: ActionValidator,
        state_validator: StateValidator,
        player_id: str,
    ) -> TransitionApplication:
        transition = self.add_player_between_turns(
            state,
            match_config,
            action_validator,
            player_id,
        )
        self.apply_transition(state, transition, state_validator)
        return transition

    def remove_player_between_turns(
        self,
        state: GameState,
        match_config: MatchConfig | MatchParameters,
        action_validator: ActionValidator,
        player_id: str,
    ) -> TransitionApplication:
        legacy_match_parameters = (
            match_config if isinstance(match_config, MatchParameters) else None
        )
        match_config = self._coerce_match_config(match_config)
        action_validator.validate_remove_player_between_turns(state, player_id)

        transition_result = self.roster_transitions.remove_player_between_turns(
            state,
            match_config,
            player_id,
        )
        if legacy_match_parameters is not None:
            self._sync_legacy_match_parameters(
                legacy_match_parameters,
                transition_result.match_config,
            )
        return self._build_transition_application(
            state,
            transition_result.match_config,
            transition_result.event,
            legacy_match_parameters=legacy_match_parameters,
        )

    def execute_remove_player_between_turns(
        self,
        state: GameState,
        match_config: MatchConfig | MatchParameters,
        action_validator: ActionValidator,
        state_validator: StateValidator,
        player_id: str,
    ) -> TransitionApplication:
        transition = self.remove_player_between_turns(
            state,
            match_config,
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
            match_config=transition.match_config,
            structure=transition.structure,
            game_flow=transition.game_flow,
            legacy_match_parameters=transition.legacy_match_parameters,
        )

    def build_runtime(
        self,
        state: GameState,
        match_config: MatchConfig | MatchParameters,
    ) -> tuple[BaseStructure, TurnFlow]:
        legacy_match_parameters = (
            match_config if isinstance(match_config, MatchParameters) else None
        )
        match_config = self._coerce_match_config(match_config)
        self.config_validator.validate_match_config(match_config)
        structure = self.structure_factory.create(
            match_config.structure_name,
            match_config.policies,
        )
        structure.validate(state)
        game_flow = TurnFlow(
            structure,
            match_config,
            legacy_match_parameters=legacy_match_parameters,
        )
        return structure, game_flow

    def _build_transition_application(
        self,
        state: GameState,
        match_config: MatchConfig,
        event: Event,
        legacy_match_parameters: MatchParameters | None = None,
    ) -> TransitionApplication:
        state.rule_set = match_config.to_rule_set_config()
        structure, game_flow = self.build_runtime(state, match_config)
        return TransitionApplication(
            event=event,
            match_config=match_config,
            structure=structure,
            game_flow=game_flow,
            legacy_match_parameters=legacy_match_parameters,
        )
