from dataclasses import dataclass, field

from core.events import Event


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
class History:
    events: list[Event] = field(default_factory=list)

    def add_event(self, event: Event) -> None:
        self.events.append(event)

    def build_rows(self) -> list[HistoryRow]:
        rows: list[HistoryRow] = []
        current_row: HistoryRow | None = None
        turn_number = 0

        for event in self.events:
            name = event.name
            payload = event.payload

            if name == "turn_started":
                turn_number += 1
                current_row = HistoryRow(
                    turn_number=turn_number,
                    attacker_name=payload["attacker_id"],
                    trick_name=payload["trick"],
                    trick_validated="V",
                    defender_name="",
                    defense_result="",
                    letters="",
                )

                defender_ids = payload.get("defender_ids", [])
                if defender_ids:
                    current_row.defender_name = defender_ids[0]

            elif name == "defense_succeeded" and current_row is not None:
                current_row.defense_result += "V"

            elif name == "defense_failed_attempt" and current_row is not None:
                current_row.defense_result += "X"

            elif name == "letter_received" and current_row is not None:
                current_row.defense_result += "X"
                current_row.letters = payload["penalty_display"]

            elif name == "turn_ended" and current_row is not None:
                rows.append(current_row)
                current_row = None

            elif name == "turn_cancelled":
                turn_number += 1
                rows.append(
                    HistoryRow(
                        turn_number=turn_number,
                        attacker_name=payload["attacker_id"],
                        trick_name=payload["trick"],
                        trick_validated="X",
                        defender_name="",
                        defense_result="",
                        letters="",
                    )
                )

        if current_row is not None:
            rows.append(current_row)
            
        return rows