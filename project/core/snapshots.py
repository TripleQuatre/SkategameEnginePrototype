from copy import deepcopy
from dataclasses import dataclass, field

from core.state import GameState
from persistence.serializers import Serializer


@dataclass
class Snapshot:
    state_data: dict

    @classmethod
    def from_state(cls, state: GameState) -> "Snapshot":
        serializer = Serializer()
        return cls(state_data=deepcopy(serializer.serialize_game_state(state)))

    def restore_state(self) -> GameState:
        serializer = Serializer()
        return serializer.deserialize_game_state(deepcopy(self.state_data))


@dataclass
class SnapshotHistory:
    max_size: int | None = None
    snapshots: list[Snapshot] = field(default_factory=list)

    def push(self, state: GameState) -> None:
        self.snapshots.append(Snapshot.from_state(state))

        if self.max_size is not None and len(self.snapshots) > self.max_size:
            self.snapshots.pop(0)

    def pop(self) -> Snapshot | None:
        if not self.snapshots:
            return None
        return self.snapshots.pop()

    def peek(self) -> Snapshot | None:
        if not self.snapshots:
            return None
        return self.snapshots[-1]

    def clear(self) -> None:
        self.snapshots.clear()

    def can_undo(self) -> bool:
        return len(self.snapshots) > 0
