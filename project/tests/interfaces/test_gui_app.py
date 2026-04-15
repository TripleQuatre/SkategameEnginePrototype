import modes.battle as battle_module
import pytest

from core.types import Phase
from interfaces.gui.gui_app import GUIApp


@pytest.fixture
def gui_app(monkeypatch) -> GUIApp:
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showinfo",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showerror",
        lambda *args, **kwargs: None,
    )

    app = GUIApp()
    app.root.withdraw()

    yield app

    app.root.destroy()


def test_gui_refresh_game_view_shows_consultation_mode_for_finished_game(
    gui_app: GUIApp,
) -> None:
    for index, player_var in enumerate(gui_app.player_name_vars):
        player_var.set(f"Player {index + 1}")

    gui_app.word_var.set("S")
    gui_app._start_game()

    assert gui_app.controller is not None
    gui_app.controller.start_turn("soul")
    gui_app.controller.resolve_defense(False)

    gui_app._refresh_game_view()

    assert gui_app.controller.get_state().phase == Phase.END
    assert gui_app.phase_title_label is not None
    assert gui_app.phase_description_label is not None
    assert gui_app.confirm_trick_button is not None
    assert gui_app.success_button is not None

    assert gui_app.phase_title_label.cget("text") == "Game over"
    assert (
        gui_app.phase_description_label.cget("text")
        == "Consultation mode. Use Undo, Save, Load, History or New game."
    )
    assert str(gui_app.confirm_trick_button.cget("state")) == "disabled"
    assert str(gui_app.success_button.cget("state")) == "disabled"


def test_gui_history_view_renders_battle_turns(
    gui_app: GUIApp, monkeypatch
) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_module.random, "shuffle", fixed_shuffle)

    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()

    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.player_name_vars[2].set("Alex")
    gui_app.word_var.set("SKATE")
    gui_app.defense_attempts_var.set(1)

    gui_app._start_game()

    assert gui_app.controller is not None
    gui_app.controller.start_turn("kickflip")
    gui_app.controller.resolve_defense(True)
    gui_app.controller.resolve_defense(False)

    gui_app._refresh_history_view()

    assert gui_app.history_tree is not None
    rows = gui_app.history_tree.get_children()

    assert len(rows) == 2

    first_row = gui_app.history_tree.item(rows[0], "values")
    second_row = gui_app.history_tree.item(rows[1], "values")

    assert first_row == ("1", "Alex", "kickflip", "V", "Stan", "V", "-")
    assert second_row == ("", "", "", "", "Denise", "X", "S")


def test_gui_start_game_with_three_players_uses_battle_mode(
    gui_app: GUIApp, monkeypatch
) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [1, 2, 0]

    monkeypatch.setattr(battle_module.random, "shuffle", fixed_shuffle)

    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()

    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.player_name_vars[2].set("Margaux")
    gui_app.word_var.set("OUT")
    gui_app.defense_attempts_var.set(1)

    gui_app._start_game()

    assert gui_app.controller is not None
    state = gui_app.controller.get_state()

    assert gui_app.controller.engine.match_parameters.mode_name == "battle"
    assert state.turn_order == [1, 2, 0]
    assert state.attacker_index == 1

    assert gui_app.matchup_label is not None
    assert gui_app.phase_title_label is not None
    assert gui_app.phase_description_label is not None

    assert gui_app.matchup_label.cget("text") == "STAN / DENISE / MARGAUX"
    assert gui_app.phase_title_label.cget("text") == "Denise sets the next trick"
    assert gui_app.phase_description_label.cget("text") == "Defenders: Stan, Margaux"


def test_gui_return_to_setup_clears_controller_and_status(gui_app: GUIApp) -> None:
    for index, player_var in enumerate(gui_app.player_name_vars):
        player_var.set(f"Player {index + 1}")

    gui_app._start_game()
    assert gui_app.controller is not None

    gui_app._return_to_setup()

    assert gui_app.controller is None
    assert gui_app.current_view == "setup"
    assert gui_app.trick_var.get() == ""
    assert gui_app.status_var.get() == "Configure the game to begin."
