import pytest

from dictionary import (
    ConstructedTrick,
    DictionaryDefinition,
    DictionaryFilters,
    DictionaryResolution,
    Sport,
    TrickExit,
    TrickSegment,
    TrickType,
)


def test_simple_segment_uses_switch_as_suffix_in_label() -> None:
    segment = TrickSegment(
        trick_type=TrickType.SOULPLATE,
        variation="True Spin",
        base_name="Soul",
        switch=True,
    )

    assert segment.label == "True Spin Soul Switch"
    assert "variation=true_spin" in segment.canonical_key
    assert "base=soul" in segment.canonical_key
    assert "switch=1" in segment.canonical_key


def test_negative_segment_inserts_negative_before_base_name() -> None:
    segment = TrickSegment(
        trick_type=TrickType.NEGATIVE,
        variation="Zero",
        base_name="Soul",
        grab=True,
    )

    assert segment.label == "Zero Negative Soul Grab"
    assert "type=negative" in segment.canonical_key
    assert "grab=1" in segment.canonical_key


def test_constructed_trick_formats_combo_and_exit() -> None:
    trick = ConstructedTrick(
        segments=(
            TrickSegment(
                trick_type=TrickType.H_BLOCK,
                variation="Back",
                base_name="UFO",
            ),
            TrickSegment(
                trick_type=TrickType.SOULPLATE,
                variation="True Spin",
                base_name="Soul",
            ),
        ),
        trick_exit=TrickExit(degrees=360, reverse=True),
    )

    assert trick.is_combo is True
    assert trick.label == "Back UFO to True Spin Soul Reverse 360"
    assert trick.canonical_key.endswith("exit=reverse_360")


def test_combo_order_changes_canonical_identity() -> None:
    first = ConstructedTrick(
        segments=(
            TrickSegment(trick_type=TrickType.SOULPLATE, base_name="Soul"),
            TrickSegment(
                trick_type=TrickType.SOULPLATE,
                variation="Top",
                base_name="Soul",
            ),
        )
    )
    second = ConstructedTrick(
        segments=(
            TrickSegment(
                trick_type=TrickType.SOULPLATE,
                variation="Top",
                base_name="Soul",
            ),
            TrickSegment(trick_type=TrickType.SOULPLATE, base_name="Soul"),
        )
    )

    assert first.canonical_key != second.canonical_key


def test_exit_degrees_are_limited_to_v8_values() -> None:
    with pytest.raises(ValueError):
        TrickExit(degrees=720)


def test_trick_rejects_more_than_three_segments() -> None:
    with pytest.raises(ValueError):
        ConstructedTrick(
            segments=(
                TrickSegment(trick_type=TrickType.SOULPLATE, base_name="Soul"),
                TrickSegment(trick_type=TrickType.H_BLOCK, base_name="UFO"),
                TrickSegment(trick_type=TrickType.NEGATIVE, base_name="Makio"),
                TrickSegment(trick_type=TrickType.SOULPLATE, base_name="Top Soul"),
            )
        )


def test_trick_can_roundtrip_to_dict() -> None:
    trick = ConstructedTrick(
        segments=(
            TrickSegment(
                trick_type=TrickType.NEGATIVE,
                variation="Zero",
                base_name="Soul",
                grab=True,
            ),
        ),
        trick_exit=TrickExit(degrees=180),
    )

    restored = ConstructedTrick.from_dict(trick.to_dict())

    assert restored == trick
    assert restored.label == "Zero Negative Soul Grab 180"


def test_combo_rejects_explicit_switch_on_any_segment() -> None:
    with pytest.raises(ValueError):
        ConstructedTrick(
            segments=(
                TrickSegment(
                    trick_type=TrickType.SOULPLATE,
                    base_name="Soul",
                    switch=True,
                ),
                TrickSegment(trick_type=TrickType.SOULPLATE, base_name="Top Soul"),
            )
        )


def test_dictionary_definition_and_filters_expose_autonomous_domain_types() -> None:
    definition = DictionaryDefinition(
        sport=Sport.INLINE,
        profile="inline_primary_grind",
    )
    filters = DictionaryFilters(
        forbidden_trick_types=(TrickType.NEGATIVE,),
        max_segments=2,
        forbidden_exit_degrees=(540,),
        forbid_reverse_exits=True,
    )

    assert definition.sport is Sport.INLINE
    assert definition.max_segments == 3
    assert filters.forbidden_trick_types == (TrickType.NEGATIVE,)
    assert filters.max_segments == 2


def test_dictionary_resolution_can_be_serialized_for_history_or_persistence() -> None:
    resolution = DictionaryResolution(
        trick=ConstructedTrick(
            segments=(
                TrickSegment(
                    trick_type=TrickType.SOULPLATE,
                    variation="True Spin",
                    base_name="Soul",
                ),
            )
        )
    )

    data = resolution.to_dict()

    assert data["label"] == "True Spin Soul"
    assert data["canonical_key"] == resolution.canonical_key
    assert data["trick"]["segments"][0]["trick_type"] == "soulplate"
