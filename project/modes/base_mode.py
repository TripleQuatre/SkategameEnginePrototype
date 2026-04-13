from abc import ABC, abstractmethod

class BaseMode(ABC):
    @abstractmethod
    def validate(self, state) -> None:
        pass
