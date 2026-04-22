from dictionary.base import (
    DictionaryDefinition,
    DictionaryFilters,
    DictionaryResolution,
    DictionarySuggestion,
    TrickDictionary,
)
from dictionary.catalog import normalize_dictionary_text
from dictionary.models import ConstructedTrick, TrickExit, TrickSegment
from dictionary.types import Sport, TrickType


SOULPLATE_FIGURES = (
    "Soul",
    "Soyale",
    "Acid",
    "Mizu",
    "Mistrial",
    "Star",
    "Makio",
    "Makio Christ",
    "X-Grind",
    "Top Soul",
    "Top Soyale",
    "Top Acid",
    "Sweaty",
    "Top Mistrial",
    "Sunny",
    "Fish",
    "Fish Christ",
    "Top X-Grind",
)

H_BLOCK_FIGURES = (
    "Torque",
    "Back Torque",
    "Backslide",
    "Back Backslide",
    "Fastslide",
    "Back Fastslide",
    "Pudslide",
    "Back Pudslide",
    "UFO",
    "Back UFO",
    "Royal",
    "Back Royal",
    "Full",
    "Back Full",
    "Unity",
    "Back Unity",
    "Savannah",
    "Back Sav",
    "Cowboy",
    "Back Cowboy",
    "Kamikaze",
    "Back Kamikaze",
    "Tabernacle",
    "Back Tabernacle",
)

SOULPLATE_VARIATIONS = (
    "Alley-Oop",
    "True Spin",
    "Half Cab",
    "Blind",
    "Hurricane",
    "Full Cab",
    "Zero",
)

H_BLOCK_VARIATIONS = (
    "270",
    "Fakie 270",
    "450",
    "Fakie 450",
    "Zero",
)

GRAB_ELIGIBLE_FIGURES = {
    "Makio",
    "Fish",
    "Torque",
    "Back Torque",
    "Backslide",
    "Back Backslide",
    "Fastslide",
    "Back Fastslide",
    "Pudslide",
    "Back Pudslide",
}

EXIT_OPTIONS = (
    TrickExit(degrees=180),
    TrickExit(degrees=360),
    TrickExit(degrees=540),
    TrickExit(degrees=180, reverse=True),
    TrickExit(degrees=360, reverse=True),
    TrickExit(degrees=540, reverse=True),
)


class InlinePrimaryGrindDictionary(TrickDictionary):
    def __init__(self) -> None:
        self._definition = DictionaryDefinition(
            sport=Sport.INLINE,
            profile="inline_primary_grind",
            max_segments=3,
        )
        self._segments = self._build_segment_catalog()

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
        if not normalized_raw or normalized_raw.endswith(" to"):
            return None

        exit_value, trick_body = self._extract_exit(normalized_raw)
        segment_values = trick_body.split(" to ")
        if len(segment_values) > self.definition.max_segments:
            return None

        segments: list[TrickSegment] = []
        for segment_value in segment_values:
            segment = self._segments.get(segment_value)
            if segment is None:
                return None
            segments.append(segment)

        try:
            trick = ConstructedTrick(
                segments=tuple(segments),
                trick_exit=exit_value,
            )
        except ValueError:
            return None

        resolution = DictionaryResolution(trick=trick)
        if not self._resolution_matches_filters(resolution, filters):
            return None
        return resolution

    def suggest(
        self,
        raw_value: str,
        *,
        filters: DictionaryFilters | None = None,
    ) -> list[DictionarySuggestion]:
        normalized_raw = normalize_dictionary_text(raw_value)
        suggestions_by_label: dict[str, DictionarySuggestion] = {}

        if " to " in normalized_raw or normalized_raw.endswith(" to"):
            self._collect_combo_suggestions(normalized_raw, filters, suggestions_by_label)
        else:
            self._collect_root_suggestions(normalized_raw, filters, suggestions_by_label)

        return sorted(
            suggestions_by_label.values(),
            key=lambda suggestion: (suggestion.is_terminal is False, suggestion.label),
        )

    def _collect_root_suggestions(
        self,
        normalized_raw: str,
        filters: DictionaryFilters | None,
        suggestions_by_label: dict[str, DictionarySuggestion],
    ) -> None:
        for segment in self._iter_allowed_segments(filters):
            segment_label = segment.label
            if normalized_raw and not self._segment_matches_query(
                segment,
                normalized_raw,
            ):
                continue

            self._add_terminal_suggestion(
                suggestions_by_label,
                segment_label,
            )

            for exit_option in self._iter_allowed_exits(filters):
                self._add_terminal_suggestion(
                    suggestions_by_label,
                    f"{segment_label} {exit_option.label}",
                )

            if self._can_extend(1, filters):
                continuation = f"{segment_label} to"
                if not normalized_raw or normalize_dictionary_text(continuation).startswith(
                    normalized_raw
                ):
                    suggestions_by_label[continuation] = DictionarySuggestion(
                        label=continuation,
                        is_terminal=False,
                        completion=continuation,
                    )

    def _collect_combo_suggestions(
        self,
        normalized_raw: str,
        filters: DictionaryFilters | None,
        suggestions_by_label: dict[str, DictionarySuggestion],
    ) -> None:
        if normalized_raw.endswith(" to"):
            prefix_text = normalized_raw[:-3].strip()
            current_partial = ""
        else:
            prefix_text, current_partial = normalized_raw.rsplit(" to ", 1)

        prefix_values = [value for value in prefix_text.split(" to ") if value]
        prefix_segments: list[TrickSegment] = []
        for prefix_value in prefix_values:
            segment = self._segments.get(prefix_value)
            if segment is None:
                return
            prefix_segments.append(segment)

        if len(prefix_segments) >= self.definition.max_segments:
            return

        for next_segment in self._iter_allowed_segments(filters):
            next_label = next_segment.label
            normalized_next = normalize_dictionary_text(next_label)
            if current_partial and not normalized_next.startswith(current_partial):
                continue

            full_segments = tuple(prefix_segments + [next_segment])
            try:
                trick = ConstructedTrick(segments=full_segments)
            except ValueError:
                continue

            resolution = DictionaryResolution(trick=trick)
            if not self._resolution_matches_filters(resolution, filters):
                continue

            self._add_terminal_suggestion(suggestions_by_label, trick.label)

            for exit_option in self._iter_allowed_exits(filters):
                exited_trick = ConstructedTrick(
                    segments=full_segments,
                    trick_exit=exit_option,
                )
                self._add_terminal_suggestion(
                    suggestions_by_label,
                    exited_trick.label,
                )

            if self._can_extend(len(full_segments), filters):
                continuation = f"{trick.label} to"
                suggestions_by_label[continuation] = DictionarySuggestion(
                    label=continuation,
                    is_terminal=False,
                    completion=continuation,
                )

    def _build_segment_catalog(self) -> dict[str, TrickSegment]:
        segment_map: dict[str, TrickSegment] = {}

        def register(segment: TrickSegment, aliases: tuple[str, ...] = ()) -> None:
            segment_map[normalize_dictionary_text(segment.label)] = segment
            for alias in aliases:
                segment_map[normalize_dictionary_text(alias)] = segment

        for figure in SOULPLATE_FIGURES:
            for segment in self._build_segments_for_figure(
                trick_type=TrickType.SOULPLATE,
                base_name=figure,
                variations=SOULPLATE_VARIATIONS,
                grab_allowed=figure in GRAB_ELIGIBLE_FIGURES,
            ):
                aliases = self._build_switch_aliases(segment)
                register(segment, aliases)

        for figure in SOULPLATE_FIGURES:
            for segment in self._build_segments_for_figure(
                trick_type=TrickType.NEGATIVE,
                base_name=figure,
                variations=SOULPLATE_VARIATIONS,
                grab_allowed=figure in GRAB_ELIGIBLE_FIGURES,
            ):
                aliases = self._build_switch_aliases(segment)
                register(segment, aliases)

        for figure in H_BLOCK_FIGURES:
            for segment in self._build_segments_for_figure(
                trick_type=TrickType.H_BLOCK,
                base_name=figure,
                variations=H_BLOCK_VARIATIONS,
                grab_allowed=figure in GRAB_ELIGIBLE_FIGURES,
            ):
                aliases = self._build_switch_aliases(segment)
                register(segment, aliases)

        return segment_map

    def _build_segments_for_figure(
        self,
        *,
        trick_type: TrickType,
        base_name: str,
        variations: tuple[str, ...],
        grab_allowed: bool,
    ) -> list[TrickSegment]:
        segments: list[TrickSegment] = []
        variation_options = (None, *variations)

        for variation in variation_options:
            for grab in (False, True):
                if grab and not grab_allowed:
                    continue
                for switch in (False, True):
                    segments.append(
                        TrickSegment(
                            trick_type=trick_type,
                            base_name=base_name,
                            variation=variation,
                            grab=grab,
                            switch=switch,
                        )
                    )

        return segments

    def _build_switch_aliases(self, segment: TrickSegment) -> tuple[str, ...]:
        if not segment.switch:
            return ()

        parts: list[str] = ["Switch"]
        if segment.variation:
            parts.append(segment.variation)
        if segment.trick_type == TrickType.NEGATIVE:
            parts.append("Negative")
        parts.append(segment.base_name)
        if segment.grab:
            parts.append("Grab")
        return (" ".join(parts),)

    def _segment_matches_query(
        self,
        segment: TrickSegment,
        normalized_raw: str,
    ) -> bool:
        candidate_values = (segment.label, *self._build_switch_aliases(segment))
        return any(
            normalize_dictionary_text(candidate).startswith(normalized_raw)
            for candidate in candidate_values
        )

    def _extract_exit(
        self,
        normalized_raw: str,
    ) -> tuple[TrickExit | None, str]:
        for exit_option in sorted(EXIT_OPTIONS, key=lambda item: len(item.label), reverse=True):
            exit_text = normalize_dictionary_text(exit_option.label)
            suffix = f" {exit_text}"
            if normalized_raw.endswith(suffix):
                return exit_option, normalized_raw[: -len(suffix)].strip()
            if normalized_raw == exit_text:
                return exit_option, ""
        return None, normalized_raw

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

    def _iter_allowed_segments(
        self,
        filters: DictionaryFilters | None,
    ) -> list[TrickSegment]:
        unique_segments: dict[str, TrickSegment] = {}
        for segment in self._segments.values():
            unique_segments[segment.canonical_key] = segment

        return sorted(
            [
                segment
                for segment in unique_segments.values()
                if self._resolution_matches_filters(
                    DictionaryResolution(ConstructedTrick(segments=(segment,))),
                    filters,
                )
            ],
            key=lambda segment: segment.label,
        )

    def _iter_allowed_exits(
        self,
        filters: DictionaryFilters | None,
    ) -> list[TrickExit]:
        exits: list[TrickExit] = []
        for exit_option in EXIT_OPTIONS:
            if filters is not None:
                if exit_option.degrees in filters.forbidden_exit_degrees:
                    continue
                if filters.forbid_reverse_exits and exit_option.reverse:
                    continue
            exits.append(exit_option)
        return exits

    def _can_extend(
        self,
        segment_count: int,
        filters: DictionaryFilters | None,
    ) -> bool:
        max_segments = (
            filters.max_segments
            if filters is not None and filters.max_segments is not None
            else self.definition.max_segments
        )
        return segment_count < max_segments

    def _add_terminal_suggestion(
        self,
        suggestions_by_label: dict[str, DictionarySuggestion],
        label: str,
    ) -> None:
        suggestions_by_label[label] = DictionarySuggestion(
            label=label,
            is_terminal=True,
            completion=label,
        )
