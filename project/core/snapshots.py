from dataclasses import dataclass, field

from core.state import GameState
from persistence.serializers import Serializer


@dataclass
class Snapshot:
    state_data: dict

    @classmethod
    def from_state(cls, state: GameState) -> "Snapshot":
        serializer = Serializer()
        return cls(state_data=serializer.serialize_game_state(state))

    def restore_state(self) -> GameState:
        serializer = Serializer()
        return serializer.deserialize_game_state(self.state_data.copy())


@dataclass
class SnapshotHistory:
    snapshots: list[Snapshot] = field(default_factory=list)

    def push(self, state: GameState) -> None:
        self.snapshots.append(Snapshot.from_state(state))

    def pop(self) -> Snapshot | None:
        if not self.snapshots:
            return None
        return self.snapshots.pop()

    def can_undo(self) -> bool:
        return len(self.snapshots) > 0