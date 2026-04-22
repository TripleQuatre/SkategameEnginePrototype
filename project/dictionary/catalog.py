from dataclasses import dataclass

from dictionary.base import (
    DictionaryDefinition,
    DictionaryFilters,
    DictionaryResolution,
    DictionarySuggestion,
    TrickDictionary,
)


def normalize_dictionary_text(value: str) -> str:
    return " ".join(value.strip().lower().replace("-", " ").split())


@dataclass(frozen=True)
class CatalogEntry:
    resolution: DictionaryResolution
    aliases: tuple[str, ...] = ()

    @property
    def search_texts(self) -> tuple[str, ...]:
        values = [self.resolution.label, *self.aliases]
        return tuple(normalize_dictionary_text(value) for value in values)


class StaticCatalogDictionary(TrickDictionary):
    def __init__(
        self,
        definition: DictionaryDefinition,
        entries: list[CatalogEntry],
    ) -> None:
        self._definition = definition
        self._entries = list(entries)
        self._continuations = self._build_continuations(self._entries)

    @property
    def definition(self) -> DictionaryDefinition:
        return self._definition

    def resolve(
        self,
        raw_value: str,
        *,
        filters: DictionaryFilters | None = None,
    ) -> DictionaryResolution | None:
        normalized_raw = normalize_dictionary_text(raw_value)
        if not normalized_raw:
            return None

        for entry in self._iter_filtered_entries(filters):
            if normalized_raw in entry.search_texts:
                return entry.resolution
        return None

    def suggest(
        self,
        raw_value: str,
        *,
        filters: DictionaryFilters | None = None,
    ) -> list[DictionarySuggestion]:
        normalized_raw = normalize_dictionary_text(raw_value)
        suggestions_by_label: dict[str, DictionarySuggestion] = {}

        for entry in self._iter_filtered_entries(filters):
            if not normalized_raw or any(
                search_text.startswith(normalized_raw)
                for search_text in entry.search_texts
            ):
                suggestions_by_label[entry.resolution.label] = DictionarySuggestion(
                    label=entry.resolution.label,
                    is_terminal=True,
                    completion=entry.resolution.label,
                )

        for continuation in self._iter_filtered_continuations(filters):
            if not normalized_raw or normalize_dictionary_text(
                continuation
            ).startswith(normalized_raw):
                suggestions_by_label[continuation] = DictionarySuggestion(
                    label=continuation,
                    is_terminal=False,
                    completion=continuation,
                )

        return sorted(
            suggestions_by_label.values(),
            key=lambda suggestion: (suggestion.is_terminal is False, suggestion.label),
        )

    def _iter_filtered_entries(
        self,
        filters: DictionaryFilters | None,
    ) -> list[CatalogEntry]:
        return [
            entry
            for entry in self._entries
            if self._resolution_matches_filters(entry.resolution, filters)
        ]

    def _iter_filtered_continuations(
        self,
        filters: DictionaryFilters | None,
    ) -> list[str]:
        allowed_labels = {
            entry.resolution.label for entry in self._iter_filtered_entries(filters)
        }
        return [
            continuation
            for continuation, parent_labels in self._continuations.items()
            if any(parent_label in allowed_labels for parent_label in parent_labels)
        ]

    def _resolution_matches_filters(
        self,
        resolution: DictionaryResolution,
        filters: DictionaryFilters | None,
    ) -> bool:
        if filters is None:
            return True

        trick = resolution.trick

        if filters.max_segments is not None and trick.segment_count > filters.max_segments:
            return False

        if filters.forbidden_trick_types and any(
            segment.trick_type in filters.forbidden_trick_types
            for segment in trick.segments
        ):
            return False

        if trick.trick_exit is not None:
            if trick.trick_exit.degrees in filters.forbidden_exit_degrees:
                return False
            if filters.forbid_reverse_exits and trick.trick_exit.reverse:
                return False

        return True

    def _build_continuations(
        self,
        entries: list[CatalogEntry],
    ) -> dict[str, set[str]]:
        continuations: dict[str, set[str]] = {}
        for entry in entries:
            trick = entry.resolution.trick
            if trick.segment_count < 2:
                continue

            segment_labels = [segment.label for segment in trick.segments]
            for index in range(1, len(segment_labels)):
                continuation = f"{' to '.join(segment_labels[:index])} to"
                continuations.setdefault(continuation, set()).add(entry.resolution.label)

        return continuations
