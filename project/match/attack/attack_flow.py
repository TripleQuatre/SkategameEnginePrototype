from core.events import Event
from core.state import GameState
from core.types import EventName
from match.flow.exchange_outcome import ExchangeOutcome
from match.flow.turn_state import begin_attack_phase


class AttackFlow:
    def start_turn(
        self,
        state: GameState,
        trick: str,
        attack_attempts: int,
        attacker_id: str,
        attacker_name: str,
        defender_ids: list[str],
        defender_names: list[str],
    ) -> None:
        begin_attack_phase(
            state,
            trick=trick,
            attack_attempts=attack_attempts,
        )

        state.history.add_event(
            Event(
                name=EventName.TURN_STARTED,
                payload={
                    "attacker_id": attacker_id,
                    "attacker_name": attacker_name,
                    "trick": trick,
                    "attack_attempts": attack_attempts,
                    "defender_ids": defender_ids,
                    "defender_names": defender_names,
                },
            )
        )

    def resolve_attack(
        self,
        state: GameState,
        success: bool,
        attacker_id: str,
        attacker_name: str,
        on_attack_succeeded,
        on_attack_failed,
    ) -> ExchangeOutcome:
        if success:
            state.history.add_event(
                Event(
                    name=EventName.ATTACK_SUCCEEDED,
                    payload={
                        "attacker_id": attacker_id,
                        "attacker_name": attacker_name,
                        "trick": state.current_trick,
                    },
                )
            )
            on_attack_succeeded()
            return ExchangeOutcome.defense_ready()

        state.attack_attempts_left -= 1

        if state.attack_attempts_left > 0:
            state.history.add_event(
                Event(
                    name=EventName.ATTACK_FAILED_ATTEMPT,
                    payload={
                        "attacker_id": attacker_id,
                        "attacker_name": attacker_name,
                        "trick": state.current_trick,
                        "attempts_left": state.attack_attempts_left,
                    },
                )
            )
            return ExchangeOutcome.attack_continues()

        on_attack_failed()
        return ExchangeOutcome.attacker_failed()
