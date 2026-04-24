import tkinter as tk
from collections.abc import Iterator

import pytest

from harness import TkGUIHarnessDriver


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


def test_tk_harness_driver_can_launch_and_shutdown_gui(
    harness_driver: TkGUIHarnessDriver,
) -> None:
    assert harness_driver.app is not None
    assert harness_driver.app.get_harness_active_view() == "setup"

    harness_driver.shutdown()

    assert harness_driver.app is None


def test_tk_harness_driver_can_drive_start_game_flow(
    harness_driver: TkGUIHarnessDriver,
) -> None:
    assert harness_driver.app is not None

    harness_driver.type_text("setup.player_name_entry.1", "Stan")
    harness_driver.type_text("setup.player_name_entry.2", "Denise")
    harness_driver.press_key("setup.start_game_button", "enter")

    assert harness_driver.app.controller is not None
    assert harness_driver.app.get_harness_active_view() == "game"
    assert harness_driver.app.controller.get_state().phase.name == "TURN"


def test_tk_harness_driver_can_search_and_select_trick_suggestion(
    harness_driver: TkGUIHarnessDriver,
) -> None:
    assert harness_driver.app is not None

    harness_driver.type_text("setup.player_name_entry.1", "Stan")
    harness_driver.type_text("setup.player_name_entry.2", "Denise")
    harness_driver.click("setup.start_game_button")

    harness_driver.type_text("match.trick_entry", "switch soul")
    harness_driver.press_key("match.trick_entry", "down")
    harness_driver.select_suggestion("match.trick_suggestions_listbox", "Soul Switch")
    harness_driver.press_key("match.confirm_trick_button", "enter")

    assert harness_driver.app.controller is not None
    assert harness_driver.app.trick_var.get() == ""
    assert harness_driver.app.controller.get_state().current_trick == "Soul Switch"
