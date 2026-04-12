import json
from pathlib import Path

from config.match_parameters import MatchParameters
from persistence.serializers import Serializer


class ConfigRepository:
    def __init__(self) -> None:
        self.serializer = Serializer()

    def save(self, match_parameters: MatchParameters, filepath: str) -> None:
        path = Path(filepath)
        data = self.serializer.serialize_match_parameters(match_parameters)

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load(self, filepath: str) -> MatchParameters:
        path = Path(filepath)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return self.serializer.deserialize_match_parameters(data)