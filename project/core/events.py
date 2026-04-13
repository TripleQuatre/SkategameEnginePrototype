from dataclasses import dataclass, field
from typing import Any

from core.types import EventName


@dataclass
class Event:
    name: EventName
    payload: dict[str, Any] = field(default_factory=dict)
