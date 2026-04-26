import pytest

from harness import GUIOracleEngine, GUIOracleError, GUIVisibleState


def test_gui_oracle_engine_accepts_matching_visible_state() -> None:
    engine = GUIOracleEngine()
    visible_state = GUIVisibleState(
        active_view="match",
        status_text="Valid trick selected.",
        button_states={
            "match.undo_button": "normal",
            "match.save_button": "normal",
            "match.load_button": "normal",
            "match.history_button": "normal",
            "match.setup_details_button": "normal",
            "match.add_player_button": "normal",
            "match.remove_player_button": "normal",
            "match.new_game_button": "normal",
            "match.confirm_trick_button": "normal",
            "match.success_button": "disabled",
            "match.failure_button": "disabled",
        },
        texts={
            "match.phase_title_label": "Stan sets the next trick",
            "match.trick_label": "",
            "match.phase_description_label": "Defenders: Denise",
            "match.attempts_label": "",
            "setup_details.body_label": "Preset: classic_skate\nStructure: one_vs_one\nSport: inline\nPlayers: Stan, Denise\nProfiles: stan, denise\nOrder: random\nBase order: Stan, Denise\nWord: SKATE\nAttack attempts: 1\nDefense attempts: 3\nUniqueness: enabled\nMultiple Attack: disabled\nRepetition: choice (limit 3)\nDictionary sport: inline\nDictionary profile: inline_primary_grind\nDictionary max segments: 3",
        },
        score_cells={"1,0": "STAN", "1,2": "DENISE", "2,0": "SK", "2,2": "-"},
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
            visible_state=GUIVisibleState(
                active_view="match",
                texts={
                    "match.phase_title_label": "Stan sets the next trick",
                    "match.trick_label": "",
                    "match.phase_description_label": "Defenders: Denise",
                    "match.attempts_label": "",
                },
                button_states={
                    "match.undo_button": "normal",
                    "match.save_button": "normal",
                    "match.load_button": "normal",
                    "match.history_button": "normal",
                    "match.setup_details_button": "normal",
                    "match.add_player_button": "normal",
                    "match.remove_player_button": "normal",
                    "match.new_game_button": "normal",
                    "match.success_button": "disabled",
                    "match.failure_button": "disabled",
                },
                score_cells={"1,0": "STAN", "1,2": "DENISE", "2,0": "-", "2,2": "-"},
            ),
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
            visible_state=GUIVisibleState(
                active_view="match",
                texts={
                    "match.phase_title_label": "Stan sets the next trick",
                    "match.trick_label": "",
                    "match.phase_description_label": "Defenders: Denise",
                    "match.attempts_label": "",
                },
                button_states={
                    "match.undo_button": "normal",
                    "match.save_button": "normal",
                    "match.load_button": "normal",
                    "match.history_button": "normal",
                    "match.setup_details_button": "normal",
                    "match.add_player_button": "normal",
                    "match.remove_player_button": "normal",
                    "match.new_game_button": "normal",
                    "match.success_button": "disabled",
                    "match.failure_button": "disabled",
                },
                score_cells={"1,0": "STAN", "1,2": "DENISE", "2,0": "-", "2,2": "-"},
                dropdown_items=("Soul", "Mistrial"),
            ),
        )

    assert error.value.expected == "Soul Switch"
    assert error.value.observed == ("Soul", "Mistrial")


def test_gui_oracle_engine_rejects_open_turn_with_disabled_roster_buttons() -> None:
    engine = GUIOracleEngine()

    with pytest.raises(GUIOracleError) as error:
        engine.evaluate_step(
            scenario={"metadata": {"id": "unit"}},
            step={"name": "check open turn", "action": "click"},
            visible_state=GUIVisibleState(
                active_view="match",
                texts={
                    "match.phase_title_label": "Stan sets the next trick",
                    "match.trick_label": "",
                    "match.phase_description_label": "Defenders: Denise",
                    "match.attempts_label": "",
                },
                button_states={
                    "match.undo_button": "normal",
                    "match.save_button": "normal",
                    "match.load_button": "normal",
                    "match.history_button": "normal",
                    "match.setup_details_button": "normal",
                    "match.add_player_button": "disabled",
                    "match.remove_player_button": "disabled",
                    "match.new_game_button": "normal",
                    "match.success_button": "disabled",
                    "match.failure_button": "disabled",
                },
                score_cells={"1,0": "STAN", "1,2": "DENISE", "2,0": "-", "2,2": "-"},
            ),
        )

    assert "roster transitions" in str(error.value)


def test_gui_oracle_engine_rejects_consultation_view_with_active_resolution_buttons() -> None:
    engine = GUIOracleEngine()

    with pytest.raises(GUIOracleError) as error:
        engine.evaluate_step(
            scenario={"metadata": {"id": "unit"}},
            step={"name": "check end view", "action": "click"},
            visible_state=GUIVisibleState(
                active_view="match",
                texts={
                    "match.phase_title_label": "Game over",
                    "match.trick_label": "",
                    "match.phase_description_label": "Consultation mode. Use Undo, Save, Load, History, Setup details or New game.",
                    "match.attempts_label": "",
                },
                button_states={
                    "match.undo_button": "normal",
                    "match.save_button": "normal",
                    "match.load_button": "normal",
                    "match.history_button": "normal",
                    "match.setup_details_button": "normal",
                    "match.add_player_button": "disabled",
                    "match.remove_player_button": "disabled",
                    "match.new_game_button": "normal",
                    "match.success_button": "normal",
                    "match.failure_button": "disabled",
                },
                score_cells={"1,0": "STAN", "1,2": "DENISE", "2,0": "S", "2,2": "[S]"},
            ),
        )

    assert "defense resolution buttons" in str(error.value)


def test_gui_oracle_engine_rejects_unknown_match_phase_title() -> None:
    engine = GUIOracleEngine()

    with pytest.raises(GUIOracleError) as error:
        engine.evaluate_step(
            scenario={"metadata": {"id": "unit"}},
            step={"name": "check weird match phase", "action": "click"},
            visible_state=GUIVisibleState(
                active_view="match",
                texts={
                    "match.phase_title_label": "Stan is vibing",
                    "match.trick_label": "",
                    "match.phase_description_label": "Defenders: Denise",
                    "match.attempts_label": "",
                },
                button_states={
                    "match.undo_button": "normal",
                    "match.save_button": "normal",
                    "match.load_button": "normal",
                    "match.history_button": "normal",
                    "match.setup_details_button": "normal",
                    "match.add_player_button": "normal",
                    "match.remove_player_button": "normal",
                    "match.new_game_button": "normal",
                    "match.success_button": "disabled",
                    "match.failure_button": "disabled",
                },
                score_cells={"1,0": "STAN", "1,2": "DENISE", "2,0": "-", "2,2": "-"},
            ),
        )

    assert "unknown phase title" in str(error.value)
    assert error.value.expected == (
        "Game over",
        "... sets the next trick",
        "... attacks",
    )
    assert error.value.observed == "Stan is vibing"


def test_gui_oracle_engine_rejects_setup_view_missing_v10_targets() -> None:
    engine = GUIOracleEngine()

    with pytest.raises(GUIOracleError) as error:
        engine.evaluate_step(
            scenario={"metadata": {"id": "unit"}},
            step={"name": "check setup invariants", "action": "click"},
            visible_state=GUIVisibleState(
                active_view="setup",
                texts={
                    "setup.preset_combo": "classic_skate",
                    "setup.word_entry": "SKATE",
                },
                button_states={
                    "setup.start_game_button": "normal",
                    "setup.load_from_setup_button": "normal",
                },
            ),
        )

    assert "setup.sport_combo" in str(error.value)


def test_gui_oracle_engine_rejects_setup_details_missing_required_fields() -> None:
    engine = GUIOracleEngine()

    with pytest.raises(GUIOracleError) as error:
        engine.evaluate_step(
            scenario={"metadata": {"id": "unit"}},
            step={"name": "check setup details", "action": "click"},
            visible_state=GUIVisibleState(
                active_view="setup_details",
                texts={
                    "setup_details.body_label": "Preset: classic_skate\nStructure: one_vs_one\nSport: inline\nPlayers: Stan, Denise\nWord: SKATE\nAttack attempts: 1\nDefense attempts: 3\nUniqueness: enabled\nRepetition: choice (limit 3)\nDictionary sport: inline\nDictionary profile: inline_primary_grind\nDictionary max segments: 3"
                },
                button_states={"setup_details.back_to_game_button": "normal"},
            ),
        )

    assert "missing structured configuration fields" in str(error.value)
