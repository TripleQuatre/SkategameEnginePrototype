from core.events import Event
from core.state import GameState
from core.types import DefenseResolutionStatus, EventName, Phase
from engine.end_conditions import EndConditions
from engine.turn_resolver import TurnResolver
from modes.base_mode import BaseMode
from rules.rules_registry import RulesRegistry
from validation.action_validator import ActionValidator


class GameFlow:
    def __init__(self, mode: BaseMode) -> None:
        self.mode = mode
        self.rules_registry = RulesRegistry()
        self.turn_resolver = TurnResolver(self.rules_registry)
        self.end_conditions = EndConditions()
        self.action_validator = ActionValidator(self.rules_registry)

    def start_game(self, state: GameState) -> None:
        self.mode.initialize_game(state)

        state.history.add_event(
            Event(
                name=EventName.GAME_STARTED,
                payload={
                    "player_ids": [player.id for player in state.players],
                    "turn_order": state.turn_order,
                    "starting_attacker_id": state.players[state.attacker_index].id,
                },
            )
        )

    def start_turn(self, state: GameState, trick: str) -> None:
        self.action_validator.validate_start_turn(state, trick)

        attacker = state.players[state.attacker_index]

        state.current_trick = trick
        state.defender_indices = self.mode.build_defender_indices(state)
        state.current_defender_position = 0
        state.defense_attempts_left = state.rule_set.defense_attempts

        state.history.add_event(
            Event(
                name=EventName.TURN_STARTED,
                payload={
                    "attacker_id": attacker.id,
                    "trick": trick,
                    "defender_ids": [
                        state.players[index].id for index in state.defender_indices
                    ],
                },
            )
        )

    def resolve_defense(
        self, state: GameState, success: bool
    ) -> DefenseResolutionStatus:
        self.action_validator.validate_resolve_defense(state)

        turn_finished = self.turn_resolver.resolve_defense_attempt(state, success)

        eliminated_players = self.end_conditions.apply_eliminations(state)
        for player in eliminated_players:
            state.history.add_event(
                Event(
                    name=EventName.PLAYER_ELIMINATED,
                    payload={
                        "player_id": player.id,
                    },
                )
            )

        if self.end_conditions.is_game_finished(state):
            winner = self.end_conditions.get_winner(state)
            state.phase = Phase.END

            state.history.add_event(
                Event(
                    name=EventName.GAME_FINISHED,
                    payload={
                        "winner_id": winner.id if winner else None,
                    },
                )
            )

            self._consume_current_trick(state)
            self._clear_current_turn_state(state)
            return DefenseResolutionStatus.GAME_FINISHED

        if turn_finished:
            self._consume_current_trick(state)
            self._advance_to_next_attacker(state, log_turn_end=True)
            return DefenseResolutionStatus.TURN_FINISHED

        return DefenseResolutionStatus.DEFENSE_CONTINUES

    def _consume_current_trick(self, state: GameState) -> None:
        if state.current_trick is None:
            return

        normalized_trick = self.rules_registry.special.normalize_trick(
            state.current_trick
        )

        if normalized_trick not in state.validated_tricks:
            state.validated_tricks.append(normalized_trick)

    def _clear_current_turn_state(self, state: GameState) -> None:
        state.current_trick = None
        state.defender_indices = []
        state.current_defender_position = 0
        state.defense_attempts_left = 0


    def _advance_to_next_attacker(
        self, state: GameState, log_turn_end: bool = True
    ) -> None:
        next_attacker_index = self.mode.get_next_attacker_index(state)

        if next_attacker_index is None:
            state.phase = Phase.END
            return

        state.attacker_index = next_attacker_index
        self._clear_current_turn_state(state)

        if log_turn_end:
            state.history.add_event(
                Event(
                    name=EventName.TURN_ENDED,
                    payload={
                        "next_attacker_id": state.players[state.attacker_index].id,
                    },
                )
            )

    def cancel_turn(self, state: GameState, trick: str) -> None:
        self.action_validator.validate_cancel_turn(state, trick)

        attacker = state.players[state.attacker_index]

        self._advance_to_next_attacker(state, log_turn_end=False)

        state.history.add_event(
            Event(
                name=EventName.TURN_FAILED,
                payload={
                    "attacker_id": attacker.id,
                    "trick": trick,
                    "next_attacker_id": state.players[state.attacker_index].id,
                },
            )
        )
