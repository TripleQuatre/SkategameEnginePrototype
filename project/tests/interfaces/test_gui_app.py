import match.structure.battle_structure as battle_structure_module
import pytest
import tkinter as tk
from collections.abc import Iterator

from core.types import Phase, TurnPhase
from interfaces.gui.gui_app import GUIApp


@pytest.fixture
def gui_app(monkeypatch) -> Iterator[GUIApp]:
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
        == "Consultation mode. Use Undo, Save, Load, History, Setup details or New game."
    )
    assert str(gui_app.confirm_trick_button.cget("state")) == "disabled"
    assert str(gui_app.success_button.cget("state")) == "disabled"


def test_gui_uses_scrollable_root_layout(gui_app: GUIApp) -> None:
    assert gui_app.scroll_host is not None
    assert gui_app.scroll_canvas is not None
    assert gui_app.scrollbar is not None
    assert gui_app.current_view == "setup"


def test_gui_exposes_harness_targets_for_critical_widgets(gui_app: GUIApp) -> None:
    target_ids = gui_app.list_harness_targets()

    assert "root.scroll_canvas" in target_ids
    assert "view.setup" in target_ids
    assert "view.match" in target_ids
    assert "view.history" in target_ids
    assert "view.setup_details" in target_ids
    assert "setup.start_game_button" in target_ids
    assert "setup.sport_combo" in target_ids
    assert "setup.player_profile_combo.1" in target_ids
    assert "setup.player_name_entry.1" in target_ids
    assert "match.trick_entry" in target_ids
    assert "match.setup_details_button" in target_ids
    assert "history.tree" in target_ids
    assert "setup_details.body_label" in target_ids

    assert gui_app.get_harness_target("setup.start_game_button") is gui_app.start_game_button
    assert gui_app.get_harness_target("match.trick_entry") is gui_app.trick_entry
    assert gui_app.get_harness_target("history.tree") is gui_app.history_tree


def test_harness_helpers_track_active_view_and_button_state(gui_app: GUIApp) -> None:
    assert gui_app.get_harness_active_view() == "setup"
    assert gui_app.sport_combo is not None
    assert gui_app.sport_var.get() == "inline"
    assert str(gui_app.sport_combo.cget("state")) == "disabled"

    gui_app.setup_mode_var.set("custom")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    assert gui_app.get_harness_active_view() == "game"
    assert gui_app.get_harness_target_state("match.add_player_button") == "normal"

    assert gui_app.controller is not None
    gui_app.controller.start_turn("kickflip")
    gui_app._refresh_game_view()

    assert gui_app.get_harness_target_state("match.add_player_button") == "disabled"

    gui_app._show_setup_details_view()
    assert gui_app.get_harness_active_view() == "setup_details"


def test_gui_order_preview_updates_for_relevance(gui_app: GUIApp) -> None:
    assert gui_app.order_preview_label is not None

    gui_app.setup_mode_var.set("custom")
    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()
    gui_app.player_profile_vars[0].set("Stan")
    gui_app.player_profile_vars[1].set("Denise")
    gui_app.player_profile_vars[2].set("Alex")
    gui_app.order_mode_var.set("relevance")
    gui_app.relevance_criterion_var.set("age")

    assert (
        gui_app.order_preview_label.cget("text")
        == "Order preview: Alex -> Stan -> Denise"
    )


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
    assert gui_app.controller.match_parameters.sport == "inline"
    assert gui_app.controller.structure_name == "battle"
    assert state.turn_order == [1, 2, 0]
    assert state.attacker_index == 1

    assert gui_app.matchup_label is not None
    assert gui_app.preset_label is not None
    assert gui_app.score_frame is not None
    assert gui_app.phase_title_label is not None
    assert gui_app.phase_description_label is not None

    assert gui_app.preset_label.cget("text") == "Preset: battle_standard"
    assert gui_app.phase_title_label.cget("text") == "Denise sets the next trick"
    assert gui_app.phase_description_label.cget("text") == "Defenders: Stan, Margaux"

    texts = {
        (int(child.grid_info()["row"]), int(child.grid_info()["column"])): child.cget("text")
        for child in gui_app.score_frame.winfo_children()
    }
    assert texts[(0, 2)] == "━━━━"
    assert texts[(1, 0)] == "STAN"
    assert texts[(1, 2)] == "DENISE"
    assert texts[(1, 4)] == "MARGAUX"


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
    gui_app.custom_uniqueness_var.set(False)
    gui_app.custom_repetition_mode_var.set("common")
    gui_app.custom_repetition_limit_var.set(2)

    gui_app._start_game()

    assert gui_app.controller is not None
    match_parameters = gui_app.controller.match_parameters
    assert match_parameters.preset_name is None
    assert match_parameters.structure_name == "one_vs_one"
    assert match_parameters.structure_name == "one_vs_one"
    assert match_parameters.rule_set.letters_word == "OUT"
    assert match_parameters.rule_set.attack_attempts == 2
    assert match_parameters.rule_set.defense_attempts == 3
    assert match_parameters.sport == "inline"
    assert match_parameters.fine_rules.uniqueness_enabled is False
    assert match_parameters.fine_rules.repetition_mode == "common"
    assert match_parameters.fine_rules.repetition_limit == 2


def test_gui_preset_mode_reflects_v8_fine_rules(gui_app: GUIApp) -> None:
    assert gui_app.repetition_mode_combo is not None
    assert gui_app.repetition_limit_spinbox is not None
    assert gui_app.uniqueness_checkbutton is not None

    gui_app.preset_var.set("battle_common_v8")

    assert gui_app.custom_uniqueness_var.get() is True
    assert gui_app.custom_repetition_mode_var.get() == "common"
    assert gui_app.custom_repetition_limit_var.get() == 4
    assert str(gui_app.repetition_mode_combo.cget("state")) == "disabled"
    assert str(gui_app.repetition_limit_spinbox.cget("state")) == "disabled"
    assert str(gui_app.uniqueness_checkbutton.cget("state")) == "disabled"


def test_gui_blocks_invalid_attack_repetition_synergy_with_feedback(gui_app: GUIApp) -> None:
    assert gui_app.start_game_button is not None
    assert gui_app.attack_repetition_feedback_label is not None
    assert gui_app.setup_summary_label is not None

    gui_app.setup_mode_var.set("custom")
    gui_app.custom_attack_attempts_var.set(2)
    gui_app.custom_repetition_mode_var.set("choice")
    gui_app.custom_repetition_limit_var.set(3)

    assert str(gui_app.start_game_button.cget("state")) == "disabled"
    assert (
        gui_app.attack_repetition_feedback_label.cget("text")
        == "Attack/Repetition synergy active: repetition limit must be a "
        "multiple of Attack. Suggested values: 2, 4, 6."
    )
    assert "multiple attack=disabled" in gui_app.setup_summary_label.cget("text")


def test_gui_multiple_attack_feedback_explains_current_mode(gui_app: GUIApp) -> None:
    assert gui_app.multiple_attack_feedback_label is not None

    gui_app.setup_mode_var.set("custom")
    gui_app.custom_attack_attempts_var.set(2)
    gui_app.custom_multiple_attack_enabled_var.set(True)

    assert (
        gui_app.multiple_attack_feedback_label.cget("text")
        == "Enabled: the attacker may change trick from the second attack attempt."
    )


def test_gui_refresh_game_view_shows_attack_phase_details(gui_app: GUIApp) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.custom_attack_attempts_var.set(2)
    gui_app.custom_repetition_limit_var.set(4)
    gui_app._start_game()

    assert gui_app.controller is not None
    gui_app.controller.start_turn("kickflip")

    gui_app._refresh_game_view()

    assert gui_app.phase_title_label is not None
    assert gui_app.phase_description_label is not None
    assert gui_app.attempts_label is not None
    assert gui_app.success_button is not None

    assert gui_app.phase_title_label.cget("text") == "Stan attacks"
    assert (
        gui_app.phase_description_label.cget("text")
        == "Pending defenders: Denise"
    )
    assert (
        gui_app.attempts_label.cget("text")
        == "Stan has 2 attack attempt(s) left"
    )
    assert str(gui_app.success_button.cget("state")) == "normal"


def test_gui_roster_buttons_are_only_enabled_between_turns(gui_app: GUIApp) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    assert gui_app.add_player_button is not None
    assert gui_app.remove_player_button is not None
    assert str(gui_app.add_player_button.cget("state")) == "normal"
    assert str(gui_app.remove_player_button.cget("state")) == "normal"

    assert gui_app.controller is not None
    gui_app.controller.start_turn("kickflip")
    gui_app._refresh_game_view()

    assert str(gui_app.add_player_button.cget("state")) == "disabled"
    assert str(gui_app.remove_player_button.cget("state")) == "disabled"


def test_gui_setup_details_view_renders_custom_match_configuration(
    gui_app: GUIApp,
) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.player_name_vars[2].set("Frank")
    gui_app.custom_word_var.set("BLADE")
    gui_app.custom_attack_attempts_var.set(2)
    gui_app.custom_defense_attempts_var.set(3)
    gui_app.custom_uniqueness_var.set(False)
    gui_app.custom_repetition_mode_var.set("common")
    gui_app.custom_repetition_limit_var.set(4)
    gui_app._start_game()

    assert gui_app.setup_details_button is not None
    assert gui_app.setup_details_body_label is not None

    gui_app.setup_details_button.invoke()

    body = gui_app.setup_details_body_label.cget("text")
    assert gui_app.current_view == "setup_details"
    assert "Preset: custom" in body
    assert "Structure: battle" in body
    assert "Sport: inline" in body
    assert "Players: Stan, Denise, Frank" in body
    assert "Word: BLADE" in body
    assert "Attack attempts: 2" in body
    assert "Defense attempts: 3" in body
    assert "Uniqueness: disabled" in body
    assert "Multiple Attack: disabled" in body
    assert "Repetition: common (limit 4)" in body
    assert "Dictionary sport: inline" in body
    assert "Dictionary profile: inline_primary_grind" in body


def test_gui_setup_details_view_renders_preset_configuration(
    gui_app: GUIApp,
) -> None:
    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.player_name_vars[2].set("Frank")
    gui_app.preset_var.set("battle_common_v8")
    gui_app._start_game()

    assert gui_app.setup_details_body_label is not None
    gui_app._show_setup_details_view()

    body = gui_app.setup_details_body_label.cget("text")
    assert "Preset: battle_common_v8" in body
    assert "Sport: inline" in body
    assert "Uniqueness: enabled" in body
    assert "Repetition: common (limit 4)" in body


def test_gui_setup_details_view_can_return_to_game(gui_app: GUIApp) -> None:
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    assert gui_app.back_from_setup_details_button is not None
    gui_app._show_setup_details_view()
    assert gui_app.current_view == "setup_details"

    gui_app.back_from_setup_details_button.invoke()
    assert gui_app.current_view == "game"


def test_gui_match_view_renders_one_vs_one_score_table(gui_app: GUIApp) -> None:
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.custom_word_var.set("SKATE")
    gui_app._start_game()

    assert gui_app.controller is not None
    state = gui_app.controller.get_state()
    state.players[0].score = 2
    state.players[1].score = 5

    gui_app._refresh_game_view()

    assert gui_app.score_frame is not None
    texts = {
        (int(child.grid_info()["row"]), int(child.grid_info()["column"])): child.cget("text")
        for child in gui_app.score_frame.winfo_children()
    }

    assert texts[(0, 0)] == "━━━━"
    assert texts[(1, 0)] == "STAN"
    assert texts[(1, 2)] == "DENISE"
    assert texts[(2, 0)] == "SK"
    assert texts[(2, 2)] == "SKATE"


def test_gui_match_view_renders_battle_score_table(gui_app: GUIApp, monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [1, 2, 0]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    gui_app.player_count_var.set(3)
    gui_app._rebuild_player_inputs()
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.player_name_vars[2].set("Frank")
    gui_app.custom_word_var.set("SKATE")
    gui_app.setup_mode_var.set("custom")
    gui_app._start_game()

    assert gui_app.controller is not None
    state = gui_app.controller.get_state()
    state.players[0].score = 2
    state.players[1].score = 3
    state.players[2].score = 4

    gui_app._refresh_game_view()

    assert gui_app.score_frame is not None
    texts = {
        (int(child.grid_info()["row"]), int(child.grid_info()["column"])): child.cget("text")
        for child in gui_app.score_frame.winfo_children()
    }

    assert texts[(0, 0)] == ""
    assert texts[(0, 2)] == "━━━━"
    assert texts[(1, 0)] == "STAN"
    assert texts[(1, 2)] == "DENISE"
    assert texts[(1, 4)] == "FRANK"
    assert texts[(2, 0)] == "SK"
    assert texts[(2, 2)] == "SKA"
    assert texts[(2, 4)] == "SKAT"


def test_gui_trick_input_requires_selecting_a_terminal_suggestion(
    gui_app: GUIApp,
) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.custom_switch_mode_var.set("enabled")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    assert gui_app.confirm_trick_button is not None
    assert gui_app.trick_dropdown_frame is not None
    assert gui_app.trick_suggestions_listbox is not None

    gui_app.trick_var.set("switch soul")
    gui_app._refresh_trick_suggestions()

    suggestions = list(gui_app.trick_suggestions_listbox.get(0, tk.END))
    assert any("Soul Switch" in suggestion for suggestion in suggestions)
    assert gui_app.trick_dropdown_frame.winfo_manager() == "grid"
    assert str(gui_app.confirm_trick_button.cget("state")) == "disabled"

    selected_index = next(
        index for index, suggestion in enumerate(suggestions) if "Soul Switch" in suggestion
    )
    gui_app.trick_suggestions_listbox.selection_set(selected_index)
    gui_app._handle_trick_suggestion_selection()

    assert gui_app.trick_var.get() == "Soul Switch"
    assert str(gui_app.confirm_trick_button.cget("state")) == "normal"


def test_gui_keyboard_navigation_can_select_and_confirm_trick(
    gui_app: GUIApp,
) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.custom_switch_mode_var.set("enabled")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    assert gui_app.controller is not None
    assert gui_app.trick_suggestions_listbox is not None
    assert gui_app.confirm_trick_button is not None

    gui_app.trick_var.set("switch soul")
    gui_app._refresh_trick_suggestions()

    selected_index = next(
        index
        for index, suggestion in enumerate(gui_app._current_trick_suggestions)
        if suggestion.label == "Soul Switch"
    )
    gui_app.trick_suggestions_listbox.selection_clear(0, tk.END)
    gui_app.trick_suggestions_listbox.selection_set(selected_index)
    gui_app.trick_suggestions_listbox.activate(selected_index)
    gui_app._handle_trick_suggestion_activate()

    assert gui_app.trick_var.get() == "Soul Switch"
    assert str(gui_app.confirm_trick_button.cget("state")) == "normal"

    assert gui_app.confirm_trick_button.bind("<Return>") != ""
    gui_app.confirm_trick_button.invoke()

    assert gui_app.controller.get_state().current_trick == "Soul Switch"
    assert gui_app.controller.get_state().phase == Phase.TURN


def test_gui_trick_entry_submit_selects_first_suggestion_when_needed(
    gui_app: GUIApp,
) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.custom_switch_mode_var.set("enabled")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    assert gui_app.trick_suggestions_listbox is not None

    gui_app.trick_var.set("switch soul")
    gui_app._refresh_trick_suggestions()

    result = gui_app._handle_trick_entry_submit()

    assert result == "break"
    assert gui_app.trick_suggestions_listbox.curselection() == (0,)


def test_gui_trick_entry_submit_confirms_selected_terminal_trick(
    gui_app: GUIApp,
) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.custom_switch_mode_var.set("enabled")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    assert gui_app.controller is not None
    assert gui_app.trick_suggestions_listbox is not None

    gui_app.trick_var.set("switch soul")
    gui_app._refresh_trick_suggestions()

    selected_index = next(
        index
        for index, suggestion in enumerate(gui_app._current_trick_suggestions)
        if suggestion.label == "Soul Switch"
    )
    gui_app.trick_suggestions_listbox.selection_clear(0, tk.END)
    gui_app.trick_suggestions_listbox.selection_set(selected_index)
    gui_app.trick_suggestions_listbox.activate(selected_index)
    gui_app._handle_trick_suggestion_selection()

    result = gui_app._handle_trick_entry_submit()

    assert result == "break"
    assert gui_app.controller.get_state().current_trick == "Soul Switch"


def test_gui_start_button_supports_return_activation(gui_app: GUIApp) -> None:
    assert gui_app.start_game_button is not None
    assert gui_app.start_game_button.bind("<Return>") != ""

    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.start_game_button.invoke()

    assert gui_app.controller is not None
    assert gui_app.current_view == "game"


def test_gui_show_game_view_without_controller_returns_to_setup(gui_app: GUIApp) -> None:
    gui_app._show_view("history")

    gui_app._show_game_view()

    assert gui_app.current_view == "setup"


def test_gui_resolve_buttons_can_drive_attack_phase(gui_app: GUIApp) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.custom_word_var.set("S")
    gui_app.custom_attack_attempts_var.set(2)
    gui_app.custom_defense_attempts_var.set(1)
    gui_app.custom_repetition_limit_var.set(4)
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


def test_gui_finished_game_keeps_secondary_views_available_but_roster_locked(
    gui_app: GUIApp,
) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app.custom_word_var.set("S")
    gui_app.custom_defense_attempts_var.set(1)
    gui_app._start_game()

    assert gui_app.controller is not None
    assert gui_app.setup_details_button is not None
    assert gui_app.history_button is not None
    assert gui_app.add_player_button is not None
    assert gui_app.remove_player_button is not None

    gui_app.controller.start_turn("soul")
    gui_app.controller.resolve_defense(False)
    gui_app._refresh_game_view()

    assert gui_app.controller.get_state().phase == Phase.END
    assert str(gui_app.setup_details_button.cget("state")) == "normal"
    assert str(gui_app.history_button.cget("state")) == "normal"
    assert str(gui_app.add_player_button.cget("state")) == "disabled"
    assert str(gui_app.remove_player_button.cget("state")) == "disabled"


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


def test_gui_undo_to_initial_snapshot_returns_to_setup_without_trick_input_bug(
    gui_app: GUIApp,
) -> None:
    gui_app.setup_mode_var.set("custom")
    gui_app.player_name_vars[0].set("Stan")
    gui_app.player_name_vars[1].set("Denise")
    gui_app._start_game()

    assert gui_app.controller is not None
    assert gui_app.current_view == "game"
    assert gui_app.trick_suggestions_listbox is not None
    assert gui_app.confirm_trick_button is not None

    gui_app._undo_action()

    assert gui_app.current_view == "setup"
    assert gui_app.controller is not None
    assert gui_app.controller.get_state().phase == Phase.SETUP
    assert gui_app.status_var.get() == "Undo successful. Returned to setup."

    gui_app.trick_var.set("soul")
    gui_app._refresh_trick_suggestions()

    assert list(gui_app.trick_suggestions_listbox.get(0, tk.END)) == []
    assert gui_app.trick_dropdown_frame is not None
    assert gui_app.trick_dropdown_frame.winfo_manager() == ""
    assert str(gui_app.confirm_trick_button.cget("state")) == "disabled"

    gui_app._undo_action()

    assert gui_app.current_view == "setup"
    assert gui_app.status_var.get() == "Nothing to undo."
