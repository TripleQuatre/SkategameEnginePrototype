from copy import deepcopy
from dataclasses import dataclass, field

from config.match_parameters import MatchParameters
from core.state import GameState
from persistence.serializers import Serializer


@dataclass
class Snapshot:
    state_data: dict
    match_parameters_data: dict | None = None

    @classmethod
    def from_state(
        cls,
        state: GameState,
        match_parameters: MatchParameters | None = None,
    ) -> "Snapshot":
        serializer = Serializer()
        match_parameters_data = None
        if match_parameters is not None:
            match_parameters_data = deepcopy(
                serializer.serialize_match_parameters(match_parameters)
            )

        return cls(
            state_data=deepcopy(serializer.serialize_game_state(state)),
            match_parameters_data=match_parameters_data,
        )

    def restore_state(self) -> GameState:
        serializer = Serializer()
        return serializer.deserialize_game_state(deepcopy(self.state_data))

    def restore_match_parameters(self) -> MatchParameters | None:
        if self.match_parameters_data is None:
            return None

        serializer = Serializer()
        return serializer.deserialize_match_parameters(
            deepcopy(self.match_parameters_data)
        )


@dataclass
class SnapshotHistory:
    max_size: int | None = None
    snapshots: list[Snapshot] = field(default_factory=list)

    def push(
        self,
        state: GameState,
        match_parameters: MatchParameters | None = None,
    ) -> None:
        self.snapshots.append(Snapshot.from_state(state, match_parameters))

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
