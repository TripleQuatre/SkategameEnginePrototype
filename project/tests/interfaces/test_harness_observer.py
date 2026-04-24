import tkinter as tk
from collections.abc import Iterator

import pytest

from harness import TkGUIHarnessDriver, TkGUIHarnessObserver


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


@pytest.fixture
def harness_observer() -> TkGUIHarnessObserver:
    return TkGUIHarnessObserver()


def test_tk_harness_observer_reads_setup_view_state(
    harness_driver: TkGUIHarnessDriver,
    harness_observer: TkGUIHarnessObserver,
) -> None:
    visible_state = harness_observer.read_visible_state(harness_driver)

    assert visible_state.active_view == "setup"
    assert visible_state.status_text == "Configure the game to begin."
    assert visible_state.button_states["setup.start_game_button"] == "normal"
    assert visible_state.texts["setup.preset_combo"] == "classic_skate"
    assert visible_state.texts["setup.word_entry"] == "SKATE"
    assert visible_state.dropdown_items == ()


def test_tk_harness_observer_reads_match_view_score_and_dropdown(
    harness_driver: TkGUIHarnessDriver,
    harness_observer: TkGUIHarnessObserver,
) -> None:
    assert harness_driver.app is not None

    harness_driver.type_text("setup.player_name_entry.1", "Stan")
    harness_driver.type_text("setup.player_name_entry.2", "Denise")
    harness_driver.click("setup.start_game_button")
    harness_driver.type_text("match.trick_entry", "switch soul")

    visible_state = harness_observer.read_visible_state(harness_driver)

    assert visible_state.active_view == "match"
    assert visible_state.texts["match.phase_title_label"] == "Stan sets the next trick"
    assert visible_state.button_states["match.confirm_trick_button"] == "disabled"
    assert visible_state.score_cells["0,0"] == "━━━━"
    assert visible_state.score_cells["1,0"] == "STAN"
    assert visible_state.score_cells["1,2"] == "DENISE"
    assert "Soul Switch" in visible_state.dropdown_items


def test_tk_harness_observer_reads_history_rows(
    harness_driver: TkGUIHarnessDriver,
    harness_observer: TkGUIHarnessObserver,
) -> None:
    assert harness_driver.app is not None

    harness_driver.type_text("setup.player_name_entry.1", "Stan")
    harness_driver.type_text("setup.player_name_entry.2", "Denise")
    harness_driver.click("setup.start_game_button")
    harness_driver.type_text("match.trick_entry", "soul")
    harness_driver.select_suggestion("match.trick_suggestions_listbox", "Soul")
    harness_driver.click("match.confirm_trick_button")
    harness_driver.click("match.failure_button")
    harness_driver.click("match.history_button")

    visible_state = harness_observer.read_visible_state(harness_driver)

    assert visible_state.active_view == "history"
    assert "history.tree" in visible_state.table_rows
    assert visible_state.table_rows["history.tree"]
    first_row = visible_state.table_rows["history.tree"][0]
    assert first_row[1] == "Stan"
    assert first_row[2] == "Soul"


def test_tk_harness_observer_reads_setup_details_body(
    harness_driver: TkGUIHarnessDriver,
    harness_observer: TkGUIHarnessObserver,
) -> None:
    assert harness_driver.app is not None

    harness_driver.type_text("setup.player_name_entry.1", "Stan")
    harness_driver.type_text("setup.player_name_entry.2", "Denise")
    harness_driver.click("setup.start_game_button")
    harness_driver.click("match.setup_details_button")

    visible_state = harness_observer.read_visible_state(harness_driver)

    assert visible_state.active_view == "setup_details"
    body = visible_state.texts["setup_details.body_label"]
    assert "Preset: classic_skate" in body
    assert "Dictionary profile: inline_primary_grind" in body
