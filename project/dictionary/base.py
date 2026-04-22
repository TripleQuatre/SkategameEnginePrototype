from dataclasses import dataclass
from typing import Protocol

from dictionary.models import ConstructedTrick
from dictionary.types import Sport, TrickType


@dataclass(frozen=True)
class DictionaryFilters:
    forbidden_trick_types: tuple[TrickType, ...] = ()
    max_segments: int | None = None
    forbidden_exit_degrees: tuple[int, ...] = ()
    forbid_reverse_exits: bool = False


@dataclass(frozen=True)
class DictionaryDefinition:
    sport: Sport
    profile: str
    max_segments: int = 3


@dataclass(frozen=True)
class DictionaryResolution:
    trick: ConstructedTrick

    @property
    def label(self) -> str:
        return self.trick.label

    @property
    def canonical_key(self) -> str:
        return self.trick.canonical_key

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "canonical_key": self.canonical_key,
            "trick": self.trick.to_dict(),
        }


@dataclass(frozen=True)
class DictionarySuggestion:
    label: str
    is_terminal: bool
    completion: str | None = None


class TrickDictionary(Protocol):
    @property
    def definition(self) -> DictionaryDefinition: ...

    def resolve(
        self,
        raw_value: str,
        *,
        filters: DictionaryFilters | None = None,
    ) -> DictionaryResolution | None: ...

    def suggest(
        self,
        raw_value: str,
        *,
        filters: DictionaryFilters | None = None,
    ) -> list[DictionarySuggestion]: ...
