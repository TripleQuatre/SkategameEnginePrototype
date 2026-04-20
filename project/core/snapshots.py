from copy import deepcopy
from dataclasses import dataclass, field

from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.setup_translator import SetupTranslator
from core.state import GameState
from persistence.serializers import Serializer


@dataclass
class Snapshot:
    state_data: dict
    match_config_data: dict | None = None

    @classmethod
    def from_state(
        cls,
        state: GameState,
        match_config: MatchConfig | MatchParameters | None = None,
    ) -> "Snapshot":
        serializer = Serializer()
        translator = SetupTranslator()
        match_config_data = None
        if match_config is not None:
            if isinstance(match_config, MatchParameters):
                match_config = translator.from_match_parameters(match_config)
            match_config_data = deepcopy(
                serializer.serialize_match_config(match_config)
            )

        return cls(
            state_data=deepcopy(serializer.serialize_game_state(state)),
            match_config_data=match_config_data,
        )

    def restore_state(self) -> GameState:
        serializer = Serializer()
        return serializer.deserialize_game_state(deepcopy(self.state_data))

    def restore_match_config(self) -> MatchConfig | None:
        if self.match_config_data is None:
            return None

        serializer = Serializer()
        return serializer.deserialize_match_config(deepcopy(self.match_config_data))

    def restore_match_parameters(self) -> MatchParameters | None:
        match_config = self.restore_match_config()
        if match_config is None:
            return None
        return SetupTranslator().from_match_config(match_config)


@dataclass
class SnapshotHistory:
    max_size: int | None = None
    snapshots: list[Snapshot] = field(default_factory=list)

    def push(
        self,
        state: GameState,
        match_config: MatchConfig | MatchParameters | None = None,
    ) -> None:
        self.snapshots.append(Snapshot.from_state(state, match_config))

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
