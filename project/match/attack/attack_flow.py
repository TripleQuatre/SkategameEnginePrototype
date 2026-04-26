from core.events import Event
from core.state import GameState
from core.types import EventName
from dictionary.runtime import build_runtime_trick_payload, resolve_runtime_trick_record
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
                    "attack_attempts": attack_attempts,
                    "defender_ids": defender_ids,
                    "defender_names": defender_names,
                    **build_runtime_trick_payload(
                        state.current_trick,
                        state.current_trick_data,
                    ),
                },
            )
        )

    def resolve_attack(
        self,
        state: GameState,
        success: bool,
        *,
        switch_normal_verified: bool | None = None,
        attacker_id: str,
        attacker_name: str,
        on_attack_failed_attempt,
        on_attack_succeeded,
        on_attack_failed,
        switch_normal_verification_required: bool = False,
    ) -> ExchangeOutcome:
        if success:
            if switch_normal_verification_required:
                if switch_normal_verified is None:
                    raise ValueError(
                        "Switch normal verification result is required for verified switch attacks."
                    )
                if not switch_normal_verified:
                    state.attack_attempts_left -= 1
                    state.history.add_event(
                        Event(
                            name=EventName.ATTACK_FAILED_ATTEMPT,
                            payload={
                                "attacker_id": attacker_id,
                                "attacker_name": attacker_name,
                                "attempts_left": state.attack_attempts_left,
                                "switch_normal_verification": "failed",
                                **build_runtime_trick_payload(
                                    state.current_trick,
                                    state.current_trick_data,
                                ),
                            },
                        )
                    )
                    if state.attack_attempts_left > 0:
                        on_attack_failed_attempt()
                        return ExchangeOutcome.attack_continues()

                    on_attack_failed_attempt()
                    on_attack_failed()
                    return ExchangeOutcome.attacker_failed()

            state.history.add_event(
                Event(
                    name=EventName.ATTACK_SUCCEEDED,
                    payload={
                        "attacker_id": attacker_id,
                        "attacker_name": attacker_name,
                        "switch_normal_verification": (
                            "verified"
                            if switch_normal_verification_required
                            else None
                        ),
                        **build_runtime_trick_payload(
                            state.current_trick,
                            state.current_trick_data,
                        ),
                    },
                )
            )
            on_attack_succeeded()
            return ExchangeOutcome.defense_ready()

        state.attack_attempts_left -= 1

        if state.attack_attempts_left > 0:
            on_attack_failed_attempt()
            state.history.add_event(
                Event(
                    name=EventName.ATTACK_FAILED_ATTEMPT,
                    payload={
                        "attacker_id": attacker_id,
                        "attacker_name": attacker_name,
                        "attempts_left": state.attack_attempts_left,
                        **build_runtime_trick_payload(
                            state.current_trick,
                            state.current_trick_data,
                        ),
                    },
                )
            )
            return ExchangeOutcome.attack_continues()

        on_attack_failed_attempt()
        on_attack_failed()
        return ExchangeOutcome.attacker_failed()

    def change_attack_trick(
        self,
        state: GameState,
        trick: str,
        attacker_id: str,
        attacker_name: str,
    ) -> None:
        previous_trick = state.current_trick
        previous_trick_data = state.current_trick_data
        _, current_trick_data = resolve_runtime_trick_record(trick)
        state.current_trick = trick
        state.current_trick_data = current_trick_data

        state.history.add_event(
            Event(
                name=EventName.ATTACK_TRICK_CHANGED,
                payload={
                    "attacker_id": attacker_id,
                    "attacker_name": attacker_name,
                    "previous_trick": previous_trick,
                    "previous_trick_label": (
                        previous_trick_data["label"]
                        if previous_trick_data is not None
                        else None
                    ),
                    **build_runtime_trick_payload(
                        state.current_trick,
                        state.current_trick_data,
                    ),
                },
            )
        )
