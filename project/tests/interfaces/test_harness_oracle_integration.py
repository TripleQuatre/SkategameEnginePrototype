import tkinter as tk
from collections.abc import Iterator

import pytest

from harness import GUIOracleEngine, TkGUIHarnessDriver, TkGUIHarnessObserver


@pytest.fixture
def harness_driver(monkeypatch) -> Iterator[TkGUIHarnessDriver]:
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showinfo",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showerror",
        lambda *args, **kwargs: None,
    )

    driver = TkGUIHarnessDriver(withdraw_on_launch=True)

    try:
        driver.launch()
    except tk.TclError as error:
        pytest.skip(f"Tk GUI is unavailable in this environment: {error}")

    yield driver
    driver.shutdown()


def test_gui_oracle_engine_validates_real_match_view_state(
    harness_driver: TkGUIHarnessDriver,
) -> None:
    observer = TkGUIHarnessObserver()
    oracle = GUIOracleEngine()

    harness_driver.type_text("setup.player_name_entry.1", "Stan")
    harness_driver.type_text("setup.player_name_entry.2", "Denise")
    harness_driver.click("setup.start_game_button")
    harness_driver.type_text("match.trick_entry", "switch soul")

    visible_state = observer.read_visible_state(harness_driver)

    oracle.evaluate_step(
        scenario={"metadata": {"id": "real_match"}},
        step={
            "name": "check real match view",
            "action": "type",
            "expect": {
                "view": "match",
                "status_text_contains": "Select a valid suggestion",
                "button_states": {
                    "match.confirm_trick_button": "disabled",
                    "match.add_player_button": "normal",
                },
                "text_equals": {
                    "match.phase_title_label": "Stan sets the next trick",
                },
                "score_cells": {
                    "0,0": "━━━━",
                    "1,0": "STAN",
                    "1,2": "DENISE",
                },
                "dropdown_contains": ["Soul Switch"],
            },
        },
        visible_state=visible_state,
    )


def test_gui_oracle_engine_validates_real_setup_details_state(
    harness_driver: TkGUIHarnessDriver,
) -> None:
    observer = TkGUIHarnessObserver()
    oracle = GUIOracleEngine()

    harness_driver.type_text("setup.player_name_entry.1", "Stan")
    harness_driver.type_text("setup.player_name_entry.2", "Denise")
    harness_driver.click("setup.start_game_button")
    harness_driver.click("match.setup_details_button")

    visible_state = observer.read_visible_state(harness_driver)

    oracle.evaluate_step(
        scenario={"metadata": {"id": "real_setup_details"}},
        step={
            "name": "check setup details",
            "action": "click",
            "expect": {
                "view": "setup_details",
                "text_contains": {
                    "setup_details.body_label": "Preset: classic_skate",
                },
            },
        },
        visible_state=visible_state,
    )


def test_gui_oracle_engine_accepts_real_consultation_state_without_explicit_expectations(
    harness_driver: TkGUIHarnessDriver,
) -> None:
    observer = TkGUIHarnessObserver()
    oracle = GUIOracleEngine()

    harness_driver.select_option("setup.preset_combo", "duel_short_strict_v9_3")
    harness_driver.type_text("setup.player_name_entry.1", "Stan")
    harness_driver.type_text("setup.player_name_entry.2", "Denise")
    harness_driver.click("setup.start_game_button")
    harness_driver.type_text("match.trick_entry", "soul")
    harness_driver.select_suggestion("match.trick_suggestions_listbox", "Soul")
    harness_driver.click("match.confirm_trick_button")
    harness_driver.click("match.success_button")
    harness_driver.click("match.failure_button")

    visible_state = observer.read_visible_state(harness_driver)

    oracle.evaluate_step(
        scenario={"metadata": {"id": "real_consultation"}},
        step={
            "name": "check consultation invariants",
            "action": "click",
        },
        visible_state=visible_state,
    )
