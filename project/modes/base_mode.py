from abc import ABC, abstractmethod

from core.state import GameState


class BaseMode(ABC):
    @abstractmethod
    def initialize_game(self, state: GameState) -> None:
        pass

    @abstractmethod
    def build_defender_indices(self, state: GameState) -> list[int]:
        pass

    @abstractmethod
    def get_next_attacker_index(self, state: GameState) -> int | None:
        pass

    @abstractmethod
    def validate(self, state: GameState) -> None:
        pass
