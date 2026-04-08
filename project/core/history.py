from dataclasses import dataclass, field
from core.events import Event

@dataclass
class History:
    events: list[Event] = field(default_factory=list)

    def add_event(self, event: Event) -> None:
        self.events.append(event)