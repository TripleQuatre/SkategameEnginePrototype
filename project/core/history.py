from dataclasses import dataclass, field

from core.events import Event
from core.types import EventName


@dataclass
class HistoryDefenseRow:
    defender_name: str
    attempts_trace: str
    result: str
    letters: str


@dataclass
class HistoryTurn:
    turn_number: int
    attacker_name: str
    trick_name: str
    trick_status: str
    attack_trace: str = ""
    defenses: list[HistoryDefenseRow] = field(default_factory=list)


@dataclass
class HistoryRow:
    turn_number: int
    attacker_name: str
    trick_name: str
    trick_validated: str
    defender_name: str
    defense_result: str
    letters: str


@dataclass
class HistoryMatchContext:
    structure_name: str | None = None
    preset_name: str | None = None
    player_names: list[str] = field(default_factory=list)
    turn_order: list[int] = field(default_factory=list)
    starting_attacker_name: str | None = None
    initial_turn_order_policy: str | None = None
    attacker_rotation_policy: str | None = None
    defender_order_policy: str | None = None


@dataclass
class History:
    events: list[Event] = field(default_factory=list)

    def add_event(self, event: Event) -> None:
        self.events.append(event)

    @staticmethod
    def _get_payload_structure_name(
        payload: dict[str, object],
        fallback: str | None = None,
    ) -> str | None:
        return payload.get("structure_name", fallback)

    def build_match_context(self) -> HistoryMatchContext | None:
        context: HistoryMatchContext | None = None

        for event in self.events:
            payload = event.payload

            if event.name == EventName.GAME_STARTED:
                structure_name = self._get_payload_structure_name(payload)
                context = HistoryMatchContext(
                    structure_name=structure_name,
                    preset_name=payload.get("preset_name"),
                    player_names=list(payload.get("player_names", [])),
                    turn_order=list(payload.get("turn_order", [])),
                    starting_attacker_name=payload.get(
                        "starting_attacker_name",
                        payload.get("starting_attacker_id"),
                    ),
                    initial_turn_order_policy=payload.get("initial_turn_order_policy"),
                    attacker_rotation_policy=payload.get("attacker_rotation_policy"),
                    defender_order_policy=payload.get("defender_order_policy"),
                )
                continue

            if event.name in {EventName.PLAYER_JOINED, EventName.PLAYER_REMOVED} and context is not None:
                structure_name = self._get_payload_structure_name(
                    payload,
                    context.structure_name,
                )
                context.structure_name = structure_name
                context.preset_name = payload.get("preset_name", context.preset_name)
                context.player_names = list(
                    payload.get("player_names", context.player_names)
                )
                context.turn_order = list(payload.get("turn_order", context.turn_order))

        return context

    def build_turns(self) -> list[HistoryTurn]:
        turns: list[HistoryTurn] = []
        current_turn: HistoryTurn | None = None
        current_defense: HistoryDefenseRow | None = None
        remaining_defender_ids: list[str] = []
        turn_number = 0

        for event in self.events:
            name = event.name
            payload = event.payload

            if name == EventName.TURN_STARTED:
                turn_number += 1
                current_turn = HistoryTurn(
                    turn_number=turn_number,
                    attacker_name=payload.get("attacker_name", payload["attacker_id"]),
                    trick_name=payload["trick"],
                    trick_status="pending",
                )
                turns.append(current_turn)

                remaining_defender_ids = list(
                    payload.get("defender_names", payload.get("defender_ids", []))
                )
                current_defense = None

                if remaining_defender_ids:
                    current_defense = HistoryDefenseRow(
                        defender_name=remaining_defender_ids.pop(0),
                        attempts_trace="",
                        result="",
                        letters="",
                    )
                    current_turn.defenses.append(current_defense)

            elif name == EventName.ATTACK_FAILED_ATTEMPT and current_turn is not None:
                current_turn.attack_trace += self._build_attack_attempt_trace(
                    payload,
                    success=False,
                )

            elif name == EventName.ATTACK_SUCCEEDED and current_turn is not None:
                current_turn.attack_trace += self._build_attack_attempt_trace(
                    payload,
                    success=True,
                )
                current_turn.trick_status = "validated"

            elif name == EventName.DEFENSE_FAILED_ATTEMPT and current_defense is not None:
                self._mark_attack_succeeded_if_missing(current_turn)
                current_defense.attempts_trace += "X"

            elif name == EventName.DEFENSE_SUCCEEDED and current_defense is not None:
                self._mark_attack_succeeded_if_missing(current_turn)
                current_defense.attempts_trace += "V"
                current_defense.result = "success"

                if remaining_defender_ids and current_turn is not None:
                    current_defense = HistoryDefenseRow(
                        defender_name=remaining_defender_ids.pop(0),
                        attempts_trace="",
                        result="",
                        letters="",
                    )
                    current_turn.defenses.append(current_defense)
                else:
                    current_defense = None

            elif name == EventName.LETTER_RECEIVED and current_defense is not None:
                self._mark_attack_succeeded_if_missing(current_turn)
                current_defense.attempts_trace += "X"
                current_defense.result = "letter"
                current_defense.letters = payload["penalty_display"]

                if remaining_defender_ids and current_turn is not None:
                    current_defense = HistoryDefenseRow(
                        defender_name=remaining_defender_ids.pop(0),
                        attempts_trace="",
                        result="",
                        letters="",
                    )
                    current_turn.defenses.append(current_defense)
                else:
                    current_defense = None

            elif name == EventName.TURN_ENDED:
                self._mark_attack_succeeded_if_missing(current_turn)
                current_turn = None
                current_defense = None
                remaining_defender_ids = []

            elif name == EventName.GAME_FINISHED:
                self._mark_attack_succeeded_if_missing(current_turn)
                current_turn = None
                current_defense = None
                remaining_defender_ids = []

            elif name == EventName.TURN_FAILED:
                if current_turn is not None:
                    current_turn.trick_status = "failed"
                    if not current_turn.attack_trace:
                        current_turn.attack_trace = "X"
                else:
                    turn_number += 1
                    turns.append(
                        HistoryTurn(
                            turn_number=turn_number,
                            attacker_name=payload.get(
                                "attacker_name", payload["attacker_id"]
                            ),
                            trick_name=payload["trick"],
                            trick_status="failed",
                            attack_trace="X",
                        )
                    )
                current_turn = None
                current_defense = None
                remaining_defender_ids = []

        return turns

    def build_rows(self) -> list[HistoryRow]:
        rows: list[HistoryRow] = []

        for turn in self.build_turns():
            if not turn.defenses:
                rows.append(
                    HistoryRow(
                        turn_number=turn.turn_number,
                        attacker_name=turn.attacker_name,
                        trick_name=turn.trick_name,
                        trick_validated=self._build_attack_display(turn),
                        defender_name="",
                        defense_result="",
                        letters="",
                    )
                )
                continue

            for defense in turn.defenses:
                rows.append(
                    HistoryRow(
                        turn_number=turn.turn_number,
                        attacker_name=turn.attacker_name,
                        trick_name=turn.trick_name,
                        trick_validated=self._build_attack_display(turn),
                        defender_name=defense.defender_name,
                        defense_result=defense.attempts_trace,
                        letters=defense.letters,
                    )
                )

        return rows

    def _mark_attack_succeeded_if_missing(
        self, current_turn: HistoryTurn | None
    ) -> None:
        if current_turn is None or current_turn.trick_status == "failed":
            return

        current_turn.trick_status = "validated"
        if not current_turn.attack_trace:
            current_turn.attack_trace = "V"

    def _build_attack_display(self, turn: HistoryTurn) -> str:
        if turn.attack_trace:
            return turn.attack_trace
        return "V" if turn.trick_status == "validated" else "X"

    def _build_attack_attempt_trace(
        self,
        payload: dict[str, object],
        *,
        success: bool,
    ) -> str:
        switch_verification = payload.get("switch_normal_verification")
        if switch_verification == "verified":
            return "V N(V)"
        if switch_verification == "failed":
            return "V N(X)"
        return "V" if success else "X"
