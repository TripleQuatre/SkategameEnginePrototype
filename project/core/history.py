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
    mode_name: str | None = None
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

    def build_match_context(self) -> HistoryMatchContext | None:
        context: HistoryMatchContext | None = None

        for event in self.events:
            payload = event.payload

            if event.name == EventName.GAME_STARTED:
                context = HistoryMatchContext(
                    mode_name=payload.get("mode_name"),
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
                context.mode_name = payload.get("mode_name", context.mode_name)
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
                    trick_status="validated",
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

            elif name == EventName.DEFENSE_FAILED_ATTEMPT and current_defense is not None:
                current_defense.attempts_trace += "X"

            elif name == EventName.DEFENSE_SUCCEEDED and current_defense is not None:
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
                current_turn = None
                current_defense = None
                remaining_defender_ids = []

            elif name == EventName.GAME_FINISHED:
                current_turn = None
                current_defense = None
                remaining_defender_ids = []

            elif name == EventName.TURN_FAILED:
                turn_number += 1
                turns.append(
                    HistoryTurn(
                        turn_number=turn_number,
                        attacker_name=payload.get("attacker_name", payload["attacker_id"]),
                        trick_name=payload["trick"],
                        trick_status="failed",
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
                        trick_validated="V" if turn.trick_status == "validated" else "X",
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
                        trick_validated="V" if turn.trick_status == "validated" else "X",
                        defender_name=defense.defender_name,
                        defense_result=defense.attempts_trace,
                        letters=defense.letters,
                    )
                )

        return rows
