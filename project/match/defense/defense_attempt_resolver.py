from core.events import Event
from core.exceptions import InvalidStateError
from core.state import GameState
from core.types import EventName
from dictionary.runtime import build_runtime_trick_payload


class DefenseAttemptResolver:
    def __init__(self, scoring, defense_attempts: int = 1) -> None:
        self.scoring = scoring
        self.defense_attempts = defense_attempts

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
                        "player_name": defender.name,
                        **build_runtime_trick_payload(
                            state.current_trick,
                            state.current_trick_data,
                        ),
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
                        "player_name": defender.name,
                        "attempts_left": state.defense_attempts_left,
                        **build_runtime_trick_payload(
                            state.current_trick,
                            state.current_trick_data,
                        ),
                    },
                )
            )
            return False

        self.scoring.apply_letter_penalty(state, defender)
        state.history.add_event(
            Event(
                name=EventName.LETTER_RECEIVED,
                payload={
                    "player_id": defender.id,
                    "player_name": defender.name,
                    "new_score": defender.score,
                    "penalty_display": self.scoring.get_penalty_display(
                        state, defender
                    ),
                    **build_runtime_trick_payload(
                        state.current_trick,
                        state.current_trick_data,
                    ),
                },
            )
        )
        return self._move_to_next_defender(state)

    def _move_to_next_defender(self, state: GameState) -> bool:
        state.current_defender_position += 1

        if self.is_turn_finished(state):
            return True

        state.defense_attempts_left = self.defense_attempts
        return False

    def is_turn_finished(self, state: GameState) -> bool:
        return state.current_defender_position >= len(state.defender_indices)
