from core.events import Event
from core.state import GameState
from core.types import EventName
from match.flow.turn_state import clear_turn_runtime, mark_game_finished, mark_turn_finished, set_turn_open


class TurnCycle:
    def __init__(self, structure, special_rules) -> None:
        self.structure = structure
        self.special_rules = special_rules

    @property
    def structure_name(self):
        return self.structure.structure_name

    def consume_current_trick(self, state: GameState) -> None:
        if state.current_trick is None:
            return

        normalized_trick = self.special_rules.normalize_trick(state.current_trick)

        if normalized_trick not in state.validated_tricks:
            state.validated_tricks.append(normalized_trick)

    def finish_game_runtime(self, state: GameState) -> None:
        mark_game_finished(state)
        clear_turn_runtime(state)

    def advance_to_next_attacker(
        self, state: GameState, log_turn_end: bool = True
    ) -> None:
        next_attacker_index = self.structure.get_next_attacker_index(state)

        if next_attacker_index is None:
            mark_game_finished(state)
            return

        state.attacker_index = next_attacker_index
        clear_turn_runtime(state)
        set_turn_open(state)

        if log_turn_end:
            state.history.add_event(
                Event(
                    name=EventName.TURN_ENDED,
                    payload={
                        "next_attacker_id": state.players[state.attacker_index].id,
                        "next_attacker_name": state.players[state.attacker_index].name,
                    },
                )
            )

    def fail_current_turn(
        self,
        state: GameState,
        attacker_id: str,
        attacker_name: str,
        trick: str | None,
    ) -> None:
        mark_turn_finished(state)
        self.advance_to_next_attacker(state, log_turn_end=False)

        state.history.add_event(
            Event(
                name=EventName.TURN_FAILED,
                payload={
                    "attacker_id": attacker_id,
                    "attacker_name": attacker_name,
                    "trick": trick,
                    "next_attacker_id": state.players[state.attacker_index].id,
                    "next_attacker_name": state.players[state.attacker_index].name,
                },
            )
        )
