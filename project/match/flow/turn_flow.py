from config.match_parameters import MatchParameters
from core.events import Event
from core.exceptions import InvalidStateError
from core.state import GameState
from core.types import (
    AttackResolutionStatus,
    DefenseResolutionStatus,
    EventName,
    TurnPhase,
)
from match.attack.attack_flow import AttackFlow
from match.defense.defense_attempt_resolver import DefenseAttemptResolver
from match.defense.defense_flow import DefenseFlow
from match.flow.turn_cycle import TurnCycle
from match.flow.turn_state import promote_attack_to_defense
from match.flow.trick_rules import TrickRules
from match.scoring.letters_scoring import LettersScoring
from match.structure.base_structure import BaseStructure
from match.victory.last_player_standing import LastPlayerStandingVictory
from validation.action_validator import ActionValidator


class TurnFlow:
    def __init__(
        self,
        structure: BaseStructure,
        match_parameters: MatchParameters | None = None,
    ) -> None:
        self.structure = structure
        self.match_parameters = match_parameters
        self.scoring = LettersScoring()
        self.special_rules = TrickRules()
        self.turn_resolver = DefenseAttemptResolver(self.scoring)
        self.attack_flow = AttackFlow()
        self.end_conditions = LastPlayerStandingVictory()
        self.defense_flow = DefenseFlow(self.turn_resolver, self.end_conditions)
        self.turn_cycle = TurnCycle(self.structure, self.special_rules)
        self.action_validator = ActionValidator(self.special_rules)

    @property
    def structure_name(self) -> str:
        return self.structure.structure_name

    def start_game(self, state: GameState) -> None:
        self.structure.initialize_game(state)

        state.history.add_event(
            Event(
                name=EventName.GAME_STARTED,
                payload={
                    "player_ids": [player.id for player in state.players],
                    "player_names": [player.name for player in state.players],
                    "turn_order": state.turn_order,
                    "starting_attacker_id": state.players[state.attacker_index].id,
                    "starting_attacker_name": state.players[state.attacker_index].name,
                    "structure_name": (
                        self.structure_name
                    ),
                    "mode_name": (
                        self.match_parameters.structure_name
                        if self.match_parameters is not None
                        else None
                    ),
                    "preset_name": (
                        self.match_parameters.preset_name
                        if self.match_parameters is not None
                        else None
                    ),
                    "initial_turn_order_policy": (
                        self.match_parameters.policies.initial_turn_order.value
                        if self.match_parameters is not None
                        else None
                    ),
                    "attacker_rotation_policy": (
                        self.match_parameters.policies.attacker_rotation.value
                        if self.match_parameters is not None
                        else None
                    ),
                    "defender_order_policy": (
                        self.match_parameters.policies.defender_order.value
                        if self.match_parameters is not None
                        else None
                    ),
                },
            )
        )

    def start_turn(self, state: GameState, trick: str) -> None:
        self.action_validator.validate_start_turn(state, trick)

        attacker = state.players[state.attacker_index]
        defender_indices = self.structure.build_defender_indices(state)
        defender_ids = [state.players[index].id for index in defender_indices]
        defender_names = [state.players[index].name for index in defender_indices]

        self.attack_flow.start_turn(
            state,
            trick=trick,
            attack_attempts=state.rule_set.attack_attempts,
            attacker_id=attacker.id,
            attacker_name=attacker.name,
            defender_ids=defender_ids,
            defender_names=defender_names,
        )

        if state.rule_set.attack_attempts == 1:
            self._promote_attack_to_defense(state)

    def resolve_attack(
        self, state: GameState, success: bool
    ) -> AttackResolutionStatus:
        self.action_validator.validate_resolve_attack(state)

        attacker = state.players[state.attacker_index]
        return self.attack_flow.resolve_attack(
            state,
            success=success,
            attacker_id=attacker.id,
            attacker_name=attacker.name,
            on_attack_succeeded=lambda: self._promote_attack_to_defense(state),
            on_attack_failed=lambda: self.turn_cycle.fail_current_turn(
                state,
                attacker_id=attacker.id,
                attacker_name=attacker.name,
                trick=state.current_trick,
            ),
        )

    def resolve_defense(
        self, state: GameState, success: bool
    ) -> DefenseResolutionStatus:
        if state.turn_phase == TurnPhase.ATTACK:
            attack_result = self.resolve_attack(state, success=True)
            if attack_result != AttackResolutionStatus.DEFENSE_READY:
                raise InvalidStateError(
                    "Attack must reach DEFENSE_READY before resolving defense."
                )

        self.action_validator.validate_resolve_defense(state)
        return self.defense_flow.resolve_defense(
            state,
            success=success,
            on_mark_game_finished=lambda: self.turn_cycle.finish_game_runtime(state),
            on_mark_turn_finished=lambda: None,
            on_consume_current_trick=lambda: self.turn_cycle.consume_current_trick(
                state
            ),
            on_advance_to_next_attacker=lambda log_turn_end: self.turn_cycle.advance_to_next_attacker(
                state,
                log_turn_end=log_turn_end,
            ),
        )

    def cancel_turn(self, state: GameState, trick: str) -> None:
        self.action_validator.validate_cancel_turn(state, trick)

        attacker = state.players[state.attacker_index]
        self.turn_cycle.fail_current_turn(
            state,
            attacker_id=attacker.id,
            attacker_name=attacker.name,
            trick=trick,
        )

    def _promote_attack_to_defense(self, state: GameState) -> None:
        promote_attack_to_defense(
            state,
            defender_indices=self.structure.build_defender_indices(state),
            defense_attempts=state.rule_set.defense_attempts,
        )
