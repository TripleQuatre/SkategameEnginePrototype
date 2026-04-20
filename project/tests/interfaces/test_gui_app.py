import match.structure.battle_structure as battle_structure_module
import pytest
import tkinter as tk

from core.types import Phase, TurnPhase
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

    try:
        app = GUIApp()
    except tk.TclError as error:
        pytest.skip(f"Tk GUI is unavailable in this environment: {error}")

    app.root.withdraw()

    yield app

    app.root.destroy()


def test_gui_refresh_game_view_shows_consultation_mode_for_finished_game(
    gui_app: GUIApp,
) -> None:
    gui_app.setup_mode_var.set("custom")
    for index, player_var in enumerate(gui_app.player_name_vars):
        player_var.set(f"Player {index + 1}")
    gui_app.custom_word_var.set("S")
    gui_app.custom_defense_attempts_var.set(1)

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

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()

    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.player_name_vars[2].set("Alex")
    gui_app.setup_mode_var.set("custom")
    gui_app.custom_word_var.set("OUT")
    gui_app.custom_defense_attempts_var.set(1)

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
    assert second_row == ("", "", "", "", "Denise", "X", "O")


def test_gui_start_game_with_three_players_uses_battle_mode(
    gui_app: GUIApp, monkeypatch
) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [1, 2, 0]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()

    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.player_name_vars[2].set("Margaux")
    gui_app.preset_var.set("battle_standard")

    gui_app._start_game()

    assert gui_app.controller is not None
    state = gui_app.controller.get_state()

    assert gui_app.controller.match_parameters.preset_name == "battle_standard"
    assert gui_app.controller.structure_name == "battle"
    assert state.turn_order == [1, 2, 0]
    assert state.attacker_index == 1

    assert gui_app.matchup_label is not None
    assert gui_app.preset_label is not None
    assert gui_app.phase_title_label is not None
    assert gui_app.phase_description_label is not None

    assert gui_app.matchup_label.cget("text") == "STAN / DENISE / MARGAUX"
    assert gui_app.preset_label.cget("text") == "Preset: battle_standard"
    assert gui_app.phase_title_label.cget("text") == "Denise sets the next trick"
    assert gui_app.phase_description_label.cget("text") == "Defenders: Stan, Margaux"


def test_gui_two_players_default_to_classic_skate_preset(gui_app: GUIApp) -> None:
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")

    gui_app._start_game()

    assert gui_app.controller is not None
    assert gui_app.controller.match_parameters.preset_name == "classic_skate"


def test_gui_can_start_custom_game_without_preset(gui_app: GUIApp) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.player_count_var.set(2)
    gui_app._rebuild_player_inputs()

    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.custom_word_var.set("OUT")
    gui_app.custom_attack_attempts_var.set(2)
    gui_app.custom_defense_attempts_var.set(3)

    gui_app._start_game()

    assert gui_app.controller is not None
    match_parameters = gui_app.controller.match_parameters
    assert match_parameters.preset_name is None
    assert match_parameters.structure_name == "one_vs_one"
    assert match_parameters.structure_name == "one_vs_one"
    assert match_parameters.rule_set.letters_word == "OUT"
    assert match_parameters.rule_set.attack_attempts == 2
    assert match_parameters.rule_set.defense_attempts == 3


def test_gui_refresh_game_view_shows_attack_phase_details(gui_app: GUIApp) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.custom_attack_attempts_var.set(2)
    gui_app._start_game()

    assert gui_app.controller is not None
    gui_app.controller.start_turn("kickflip")

    gui_app._refresh_game_view()

    assert gui_app.phase_title_label is not None
    assert gui_app.phase_description_label is not None
    assert gui_app.attempts_label is not None
    assert gui_app.success_button is not None

    assert gui_app.phase_title_label.cget("text") == "Stan attacks"
    assert gui_app.phase_description_label.cget("text") == "Pending defenders: Denise"
    assert (
        gui_app.attempts_label.cget("text")
        == "Stan has 2 attack attempt(s) left"
    )
    assert str(gui_app.success_button.cget("state")) == "normal"


def test_gui_resolve_buttons_can_drive_attack_phase(gui_app: GUIApp) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.custom_word_var.set("S")
    gui_app.custom_attack_attempts_var.set(2)
    gui_app.custom_defense_attempts_var.set(1)
    gui_app._start_game()

    assert gui_app.controller is not None
    gui_app.controller.start_turn("kickflip")

    gui_app._resolve_defense(False)
    assert gui_app.controller.get_state().turn_phase == TurnPhase.ATTACK
    assert (
        gui_app.status_var.get()
        == "Stan missed 'kickflip' (1 attack attempt(s) left)."
    )

    gui_app._resolve_defense(True)
    assert gui_app.controller.get_state().turn_phase == TurnPhase.DEFENSE
    assert gui_app.status_var.get() == "Stan landed 'kickflip' to set the trick."


def test_gui_can_add_player_between_turns(gui_app: GUIApp, monkeypatch) -> None:
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    monkeypatch.setattr(
        "interfaces.gui.gui_app.simpledialog.askstring",
        lambda *args, **kwargs: "Alex",
    )

    gui_app._add_player_between_turns()

    assert gui_app.controller is not None
    assert gui_app.controller.structure_name == "battle"
    assert [player.id for player in gui_app.controller.get_state().players] == [
        "Stan",
        "Denise",
        "Alex",
    ]
    assert (
        gui_app.status_var.get()
        == "Alex joined the game. Structure changed: one_vs_one -> battle. Preset cleared."
    )


def test_gui_can_remove_player_between_turns(gui_app: GUIApp, monkeypatch) -> None:
    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.player_name_vars[2].set("Alex")
    gui_app.preset_var.set("battle_standard")
    gui_app._start_game()

    monkeypatch.setattr(
        "interfaces.gui.gui_app.simpledialog.askstring",
        lambda *args, **kwargs: "Denise",
    )

    gui_app._remove_player_between_turns()

    assert gui_app.controller is not None
    assert gui_app.controller.structure_name == "one_vs_one"
    assert [player.id for player in gui_app.controller.get_state().players] == [
        "Stan",
        "Alex",
    ]
    assert (
        gui_app.status_var.get()
        == "Denise left the game. Structure changed: battle -> one_vs_one. Preset cleared."
    )


def test_gui_rejects_duplicate_player_join_between_turns(
    gui_app: GUIApp, monkeypatch
) -> None:
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    monkeypatch.setattr(
        "interfaces.gui.gui_app.simpledialog.askstring",
        lambda *args, **kwargs: "Denise",
    )

    gui_app._add_player_between_turns()

    assert gui_app.controller is not None
    assert [player.id for player in gui_app.controller.get_state().players] == [
        "Stan",
        "Denise",
    ]
    assert gui_app.status_var.get().startswith("Invalid action:")


def test_gui_rejects_unknown_player_removal_between_turns(
    gui_app: GUIApp, monkeypatch
) -> None:
    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.player_name_vars[2].set("Alex")
    gui_app.preset_var.set("battle_standard")
    gui_app._start_game()

    monkeypatch.setattr(
        "interfaces.gui.gui_app.simpledialog.askstring",
        lambda *args, **kwargs: "Margaux",
    )

    gui_app._remove_player_between_turns()

    assert gui_app.controller is not None
    assert [player.id for player in gui_app.controller.get_state().players] == [
        "Stan",
        "Denise",
        "Alex",
    ]
    assert gui_app.status_var.get().startswith("Invalid action:")


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
