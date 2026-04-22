from dictionary import (
    CatalogEntry,
    ConstructedTrick,
    DictionaryDefinition,
    DictionaryFilters,
    DictionaryResolution,
    Sport,
    StaticCatalogDictionary,
    TrickExit,
    TrickSegment,
    TrickType,
)


def _build_dictionary() -> StaticCatalogDictionary:
    return StaticCatalogDictionary(
        definition=DictionaryDefinition(
            sport=Sport.INLINE,
            profile="test_catalog",
        ),
        entries=[
            CatalogEntry(
                resolution=DictionaryResolution(
                    trick=ConstructedTrick(
                        segments=(
                            TrickSegment(
                                trick_type=TrickType.SOULPLATE,
                                base_name="Soul",
                            ),
                        )
                    )
                )
            ),
            CatalogEntry(
                resolution=DictionaryResolution(
                    trick=ConstructedTrick(
                        segments=(
                            TrickSegment(
                                trick_type=TrickType.SOULPLATE,
                                base_name="Soul",
                                switch=True,
                            ),
                        )
                    )
                ),
                aliases=("Switch Soul",),
            ),
            CatalogEntry(
                resolution=DictionaryResolution(
                    trick=ConstructedTrick(
                        segments=(
                            TrickSegment(
                                trick_type=TrickType.SOULPLATE,
                                base_name="Soul",
                            ),
                        ),
                        trick_exit=TrickExit(degrees=180),
                    )
                )
            ),
            CatalogEntry(
                resolution=DictionaryResolution(
                    trick=ConstructedTrick(
                        segments=(
                            TrickSegment(
                                trick_type=TrickType.NEGATIVE,
                                base_name="Soul",
                            ),
                        )
                    )
                )
            ),
            CatalogEntry(
                resolution=DictionaryResolution(
                    trick=ConstructedTrick(
                        segments=(
                            TrickSegment(
                                trick_type=TrickType.SOULPLATE,
                                base_name="Soul",
                            ),
                            TrickSegment(
                                trick_type=TrickType.SOULPLATE,
                                variation="Top",
                                base_name="Soul",
                            ),
                        )
                    )
                )
            ),
            CatalogEntry(
                resolution=DictionaryResolution(
                    trick=ConstructedTrick(
                        segments=(
                            TrickSegment(
                                trick_type=TrickType.SOULPLATE,
                                base_name="Soul",
                            ),
                            TrickSegment(
                                trick_type=TrickType.SOULPLATE,
                                variation="Top",
                                base_name="Soul",
                            ),
                            TrickSegment(
                                trick_type=TrickType.SOULPLATE,
                                variation="True Spin",
                                base_name="Acid",
                            ),
                        )
                    )
                )
            ),
        ],
    )


def test_catalog_resolves_canonical_trick_from_display_label() -> None:
    dictionary = _build_dictionary()

    resolution = dictionary.resolve("Soul 180")

    assert resolution is not None
    assert resolution.label == "Soul 180"
    assert resolution.canonical_key.endswith("exit=180")


def test_catalog_resolves_switch_alias_to_same_canonical_trick() -> None:
    dictionary = _build_dictionary()

    resolution = dictionary.resolve("Switch Soul")

    assert resolution is not None
    assert resolution.label == "Soul Switch"


def test_catalog_suggests_terminal_tricks_and_combo_continuations() -> None:
    dictionary = _build_dictionary()

    suggestions = dictionary.suggest("Soul")
    labels = [suggestion.label for suggestion in suggestions]

    assert "Soul" in labels
    assert "Soul 180" in labels
    assert "Soul Switch" in labels
    assert "Soul to" in labels


def test_catalog_suggests_second_combo_continuation_for_three_segment_trick() -> None:
    dictionary = _build_dictionary()

    suggestions = dictionary.suggest("Soul to Top Soul")
    labels = [suggestion.label for suggestion in suggestions]

    assert "Soul to Top Soul" in labels
    assert "Soul to Top Soul to" in labels


def test_catalog_filters_can_hide_forbidden_trick_types() -> None:
    dictionary = _build_dictionary()

    suggestions = dictionary.suggest(
        "",
        filters=DictionaryFilters(
            forbidden_trick_types=(TrickType.NEGATIVE,),
        ),
    )
    labels = [suggestion.label for suggestion in suggestions]

    assert "Negative Soul" not in labels
    assert "Soul" in labels


def test_catalog_filters_can_limit_max_segments() -> None:
    dictionary = _build_dictionary()

    suggestions = dictionary.suggest(
        "Soul",
        filters=DictionaryFilters(max_segments=1),
    )
    labels = [suggestion.label for suggestion in suggestions]

    assert "Soul" in labels
    assert "Soul to" not in labels

