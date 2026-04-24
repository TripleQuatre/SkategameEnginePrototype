import pytest

from harness import GUIOracleEngine, GUIOracleError, GUIVisibleState


def test_gui_oracle_engine_accepts_matching_visible_state() -> None:
    engine = GUIOracleEngine()
    visible_state = GUIVisibleState(
        active_view="match",
        status_text="Valid trick selected.",
        button_states={
            "match.confirm_trick_button": "normal",
            "match.failure_button": "disabled",
        },
        texts={
            "match.phase_title_label": "Stan sets the next trick",
            "setup_details.body_label": "Preset: classic_skate\nDictionary profile: inline_primary_grind",
        },
        score_cells={"1,0": "STAN", "2,0": "SK"},
        dropdown_items=("Soul", "Soul Switch"),
    )

    engine.evaluate_step(
        scenario={"metadata": {"id": "unit"}},
        step={
            "name": "check match",
            "action": "click",
            "expect": {
                "view": "match",
                "status_text_contains": "trick",
                "button_states": {
                    "match.confirm_trick_button": "normal",
                    "match.failure_button": "disabled",
                },
                "text_contains": {
                    "setup_details.body_label": "Dictionary profile: inline_primary_grind",
                },
                "score_cells": {"1,0": "STAN", "2,0": "SK"},
                "dropdown_contains": ["Soul Switch"],
            },
        },
        visible_state=visible_state,
    )


def test_gui_oracle_engine_reports_expected_and_observed_values() -> None:
    engine = GUIOracleEngine()

    with pytest.raises(GUIOracleError) as error:
        engine.evaluate_step(
            scenario={"metadata": {"id": "unit"}},
            step={
                "name": "check setup",
                "action": "click",
                "expect": {"view": "setup"},
            },
            visible_state=GUIVisibleState(active_view="match"),
        )

    assert error.value.expected == "setup"
    assert error.value.observed == "match"
    assert "Active view" in str(error.value)


def test_gui_oracle_engine_fails_on_missing_dropdown_item() -> None:
    engine = GUIOracleEngine()

    with pytest.raises(GUIOracleError) as error:
        engine.evaluate_step(
            scenario={"metadata": {"id": "unit"}},
            step={
                "name": "check dropdown",
                "action": "type",
                "expect": {"dropdown_contains": ["Soul Switch"]},
            },
            visible_state=GUIVisibleState(dropdown_items=("Soul", "Mistrial")),
        )

    assert error.value.expected == "Soul Switch"
    assert error.value.observed == ("Soul", "Mistrial")
