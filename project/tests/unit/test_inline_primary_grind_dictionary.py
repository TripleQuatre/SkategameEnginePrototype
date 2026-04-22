from dictionary import (
    DictionaryFilters,
    InlinePrimaryGrindDictionary,
    Sport,
    TrickType,
)


def test_inline_primary_grind_definition_is_inline() -> None:
    dictionary = InlinePrimaryGrindDictionary()

    assert dictionary.definition.sport is Sport.INLINE
    assert dictionary.definition.profile == "inline_primary_grind"
    assert dictionary.definition.max_segments == 3


def test_inline_primary_grind_resolves_switch_prefix_and_suffix_to_same_trick() -> None:
    dictionary = InlinePrimaryGrindDictionary()

    from_prefix = dictionary.resolve("Switch Soul")
    from_suffix = dictionary.resolve("Soul Switch")

    assert from_prefix is not None
    assert from_suffix is not None
    assert from_prefix.canonical_key == from_suffix.canonical_key
    assert from_prefix.label == "Soul Switch"


def test_inline_primary_grind_resolves_negative_and_combo_with_exit() -> None:
    dictionary = InlinePrimaryGrindDictionary()

    negative = dictionary.resolve("Zero Negative Soul")
    combo = dictionary.resolve("Back UFO to True Spin Soul Reverse 360")

    assert negative is not None
    assert negative.label == "Zero Negative Soul"
    assert combo is not None
    assert combo.label == "Back UFO to True Spin Soul Reverse 360"


def test_inline_primary_grind_rejects_explicit_switch_inside_combo() -> None:
    dictionary = InlinePrimaryGrindDictionary()

    resolution = dictionary.resolve("Soul Switch to Top Soul")

    assert resolution is None


def test_inline_primary_grind_suggests_segment_completion_and_combo_continuation() -> None:
    dictionary = InlinePrimaryGrindDictionary()

    suggestions = dictionary.suggest("Soul")
    labels = [suggestion.label for suggestion in suggestions]

    assert "Soul" in labels
    assert "Soul 180" in labels
    assert "Soul Switch" in labels
    assert "Soul to" in labels


def test_inline_primary_grind_suggests_from_switch_alias_input() -> None:
    dictionary = InlinePrimaryGrindDictionary()

    suggestions = dictionary.suggest("Switch Soul")
    labels = [suggestion.label for suggestion in suggestions]

    assert "Soul Switch" in labels


def test_inline_primary_grind_suggests_next_combo_segment() -> None:
    dictionary = InlinePrimaryGrindDictionary()

    suggestions = dictionary.suggest("Soul to True")
    labels = [suggestion.label for suggestion in suggestions]

    assert "Soul to True Spin Acid" in labels
    assert "Soul to True Spin Soul" in labels


def test_inline_primary_grind_filters_can_forbid_negative_and_reduce_segment_count() -> None:
    dictionary = InlinePrimaryGrindDictionary()

    root_suggestions = dictionary.suggest(
        "Negative",
        filters=DictionaryFilters(
            forbidden_trick_types=(TrickType.NEGATIVE,),
        ),
    )
    combo_suggestions = dictionary.suggest(
        "Soul",
        filters=DictionaryFilters(max_segments=1),
    )

    assert all("Negative" not in suggestion.label for suggestion in root_suggestions)
    assert all(suggestion.label != "Soul to" for suggestion in combo_suggestions)
