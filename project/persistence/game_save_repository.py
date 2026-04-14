import json
from pathlib import Path

from persistence.game_save import GameSave
from persistence.serializers import Serializer


class GameSaveRepository:
    def __init__(self) -> None:
        self.serializer = Serializer()

    def save(self, game_save: GameSave, filepath: str) -> None:
        path = Path(filepath)
        data = self.serializer.serialize_game_save(game_save)

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load(self, filepath: str) -> GameSave:
        path = Path(filepath)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return self.serializer.deserialize_game_save(data)
