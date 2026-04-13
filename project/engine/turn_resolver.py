from core.events import Event
from core.exceptions import InvalidStateError
from core.state import GameState
from core.types import EventName
from rules.rules_registry import RulesRegistry


class TurnResolver:
    def __init__(self, rules_registry: RulesRegistry) -> None:
        self.rules_registry = rules_registry

    def resolve_defense_attempt(self, state: GameState, success: bool) -> bool:
        if self.is_turn_finished(state):
            raise InvalidStateError("No current defender to resolve.")

        if state.current_trick is None:
            raise InvalidStateError("No current trick to defend.")

        defender = state.players[state.defender_indices[state.current_defender_position]]

        if success:
            state.history.add_event(
                Event(
                    name=EventName.DEFENSE_SUCCEEDED,
                    payload={
                        "player_id": defender.id,
                        "trick": state.current_trick,
                    },
                )
            )
            return self._move_to_next_defender(state)

        state.defense_attempts_left -= 1

        if state.defense_attempts_left > 0:
            state.history.add_event(
                Event(
                    name=EventName.DEFENSE_FAILED_ATTEMPT,
                    payload={
                        "player_id": defender.id,
                        "trick": state.current_trick,
                        "attempts_left": state.defense_attempts_left,
                    },
                )
            )
            return False

        self.rules_registry.scoring.apply_letter_penalty(state, defender)
        state.history.add_event(
            Event(
                name=EventName.LETTER_RECEIVED,
                payload={
                    "player_id": defender.id,
                    "trick": state.current_trick,
                    "new_score": defender.score,
                    "penalty_display": self.rules_registry.scoring.get_penalty_display(
                        state, defender
                    ),
                },
            )
        )
        return self._move_to_next_defender(state)

    def _move_to_next_defender(self, state: GameState) -> bool:
        state.current_defender_position += 1

        if self.is_turn_finished(state):
            return True

        state.defense_attempts_left = state.rule_set.defense_attempts
        return False

    def is_turn_finished(self, state: GameState) -> bool:
        return state.current_defender_position >= len(state.defender_indices)
