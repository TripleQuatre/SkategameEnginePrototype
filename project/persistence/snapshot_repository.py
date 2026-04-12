import json
from pathlib import Path

from core.state import GameState
from persistence.serializers import Serializer


class SnapshotRepository:
    def __init__(self) -> None:
        self.serializer = Serializer()

    def save(self, state: GameState, filepath: str) -> None:
        path = Path(filepath)
        data = self.serializer.serialize_game_state(state)

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load(self, filepath: str) -> GameState:
        path = Path(filepath)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return self.serializer.deserialize_game_state(data)