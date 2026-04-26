import shutil
from pathlib import Path

import match.structure.battle_structure as battle_structure_module

from config.fine_rules_config import FineRulesConfig
from config.match_parameters import MatchParameters
from config.match_policies import InitialTurnOrderPolicy
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.events import Event
from core.types import EventName, Phase
from interfaces.cli.cli_app import CLIApp


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "cli_app"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_cli_end_of_game_loop_can_undo_finished_game(monkeypatch, capsys) -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        rule_set=RuleSetConfig(letters_word="S"),
    )
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("soul")
    controller.resolve_defense(False)

    cli = CLIApp()

    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    returned_controller = cli._run_end_of_game_loop(controller)
    output = capsys.readouterr().out

    assert returned_controller is controller
    assert "Consultation mode:" in output
    assert "Undo successful." in output

    state = returned_controller.get_state()
    assert state.phase.value == "turn"
    assert state.current_trick == "soul"


def test_cli_end_of_game_loop_reports_return_to_setup_after_undo_of_initial_snapshot(
    monkeypatch, capsys
) -> None:
    controller = GameController(MatchParameters(player_ids=["p1", "p2"]))
    controller.start_game()

    cli = CLIApp()

    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    returned_controller = cli._run_end_of_game_loop(controller)
    output = capsys.readouterr().out

    assert returned_controller is controller
    assert "Undo successful. Returned to setup." in output
    assert returned_controller.get_state().phase == Phase.SETUP


def test_cli_load_saved_game_controller_reports_consultation_for_finished_game(
    monkeypatch, capsys
) -> None:
    case_dir = _make_case_dir("load_saved_finished_game")

    try:
        match_parameters = MatchParameters(
            player_ids=["p1", "p2"],
            rule_set=RuleSetConfig(letters_word="S"),
        )
        controller = GameController(match_parameters)

        controller.start_game()
        controller.start_turn("soul")
        controller.resolve_defense(False)

        save_path = case_dir / "finished_game.json"
        controller.save_game(str(save_path))

        cli = CLIApp()
        monkeypatch.setattr(cli, "_choose_save_file", lambda: save_path)

        loaded_controller = cli._load_saved_game_controller()
        output = capsys.readouterr().out

        assert loaded_controller is not None
        assert "Consultation mode." in output
        assert loaded_controller.get_state().phase.value == "end"
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_cli_display_history_renders_battle_turns(monkeypatch, capsys) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    match_parameters = MatchParameters(
        player_ids=["Stan", "Denise", "Alex"],
        structure_name="battle",
    )
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("kickflip")
    controller.resolve_defense(True)
    controller.resolve_defense(False)

    cli = CLIApp()
    cli.controller = controller
    cli._display_history(controller.get_state())
    output = capsys.readouterr().out

    assert "History:" in output
    assert "kickflip" in output
    assert "Stan" in output
    assert "Denise" in output
    assert "Alex" in output
    assert "V" in output
    assert "S" in output


def test_cli_run_can_load_finished_game_and_quit_from_consultation(
    monkeypatch, capsys
) -> None:
    case_dir = _make_case_dir("run_load_finished_game")

    try:
        match_parameters = MatchParameters(
            player_ids=["p1", "p2"],
            rule_set=RuleSetConfig(letters_word="S"),
        )
        controller = GameController(match_parameters)

        controller.start_game()
        controller.start_turn("soul")
        controller.resolve_defense(False)

        save_path = case_dir / "finished_game.json"
        controller.save_game(str(save_path))

        cli = CLIApp()

        inputs = iter(["2", "1", "6"])

        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
        monkeypatch.setattr(cli, "_list_save_files", lambda: [save_path])

        try:
            cli.run()
        except SystemExit:
            pass

        output = capsys.readouterr().out

        assert "Finished game loaded from finished_game.json. Consultation mode." in output
        assert "Consultation mode:" in output
        assert "1. Undo" in output
        assert "6. Quit" in output
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_cli_format_event_prefers_display_names_over_ids() -> None:
    cli = CLIApp()

    message = cli._format_event(
        Event(
            name=EventName.GAME_FINISHED,
            payload={
                "winner_id": "user_42",
                "winner_name": "Stan",
            },
        )
    )

    assert message == "Game finished. Winner: Stan"


def test_cli_display_state_shows_active_preset(capsys) -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        sport="inline",
        preset_name="classic_skate",
        rule_set=RuleSetConfig(
            letters_word="SKATE",
            elimination_enabled=True,
            defense_attempts=3,
        ),
    )
    controller = GameController(match_parameters)
    controller.start_game()

    cli = CLIApp()
    cli._display_state(controller.get_state())
    output = capsys.readouterr().out

    assert "Preset: classic_skate" in output
    assert "Sport: inline" in output


def test_cli_new_game_preset_flow_selects_preset_before_player_names(
    monkeypatch,
) -> None:
    cli = CLIApp()
    prompts: list[str] = []
    answers = iter(["1", "3", "3", "6", "2", "1"])

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr("builtins.input", fake_input)

    controller = cli._create_new_game_controller()

    assert controller.match_parameters.preset_name == "battle_standard"
    preset_prompt = next(
        prompt for prompt in prompts if prompt.startswith("Choose a preset (1-")
    )
    first_profile_prompt = next(
        prompt for prompt in prompts if prompt.startswith("Choose profile 1")
    )
    assert prompts.index(preset_prompt) < prompts.index(first_profile_prompt)


def test_cli_new_game_can_start_without_preset(monkeypatch, capsys) -> None:
    cli = CLIApp()
    answers = iter(
        [
            "2",
            "2",
            "6",
            "2",
            "choice",
            "1 2",
            "OUT",
            "2",
            "disabled",
            "3",
            "n",
            "common",
            "2",
            "1",
        ]
    )

    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    controller = cli._create_new_game_controller()
    output = capsys.readouterr().out
    match_parameters = controller.match_parameters

    assert match_parameters.preset_name is None
    assert match_parameters.structure_name == "one_vs_one"
    assert match_parameters.structure_name == "one_vs_one"
    assert match_parameters.sport == "inline"
    assert match_parameters.rule_set.letters_word == "OUT"
    assert match_parameters.rule_set.attack_attempts == 2
    assert match_parameters.rule_set.defense_attempts == 3
    assert match_parameters.fine_rules.multiple_attack_enabled is False
    assert match_parameters.fine_rules.no_repetition is False
    assert match_parameters.fine_rules.uniqueness_enabled is False
    assert match_parameters.fine_rules.repetition_mode == "common"
    assert match_parameters.fine_rules.repetition_limit == 2
    assert "Setup summary:" in output
    assert "- multiple attack: disabled" in output
    assert "- repetition: common (limit 2)" in output


def test_cli_custom_setup_prints_relevance_order_preview(monkeypatch, capsys) -> None:
    cli = CLIApp()
    answers = iter(
        [
            "2",
            "3",
            "6",
            "2",
            "1",
            "relevance",
            "age",
            "OUT",
            "1",
            "1",
            "y",
            "disabled",
            "1",
        ]
    )

    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    controller = cli._create_new_game_controller()
    output = capsys.readouterr().out

    assert controller.match_parameters.policies.initial_turn_order == InitialTurnOrderPolicy.RELEVANCE
    assert "Order preview (age): Alex -> Stan -> Denise" in output


def test_cli_custom_setup_reprompts_invalid_attack_repetition_synergy(
    monkeypatch, capsys
) -> None:
    cli = CLIApp()
    answers = iter(
        [
            "2",
            "2",
            "6",
            "2",
            "choice",
            "1 2",
            "OUT",
            "2",
            "disabled",
            "1",
            "y",
            "common",
            "3",
            "4",
            "1",
        ]
    )

    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    controller = cli._create_new_game_controller()
    output = capsys.readouterr().out

    assert controller.match_parameters.fine_rules.repetition_limit == 4
    assert (
        "Attack/Repetition synergy active: repetition limit must be a multiple "
        "of Attack. Suggested values: 2, 4, 6."
    ) in output


def test_cli_run_recovers_by_restarting_setup_after_undo_to_initial_snapshot(
    monkeypatch, capsys
) -> None:
    initial_controller = GameController(MatchParameters(player_ids=["p1", "p2"]))
    initial_controller.start_game()

    replacement_controller = GameController(MatchParameters(player_ids=["a", "b"]))
    replacement_controller.start_game()

    cli = CLIApp()
    cli._setup_or_load_game = lambda: initial_controller
    cli._create_new_game_controller = lambda: replacement_controller

    answers = iter(["/undo", "/quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    try:
        cli.run()
    except SystemExit:
        pass

    output = capsys.readouterr().out

    assert "Undo successful." in output
    assert "Returned to setup. Configure a new game." in output
    assert cli.controller is replacement_controller


def test_cli_display_state_shows_attack_phase_details(capsys) -> None:
    controller = GameController(
        MatchParameters(
            player_ids=["Stan", "Denise"],
            rule_set=RuleSetConfig(
                letters_word="SKATE",
                attack_attempts=2,
                defense_attempts=3,
            ),
            fine_rules=FineRulesConfig(
                repetition_mode="choice",
                repetition_limit=4,
            ),
        )
    )
    controller.start_game()
    controller.start_turn("kickflip")

    cli = CLIApp()
    cli._display_state(controller.get_state())
    output = capsys.readouterr().out

    assert "Stan attacks" in output
    assert "Pending defenders: Denise" in output
    assert "Current trick: kickflip (2 attack attempt(s) left)" in output


def test_cli_run_can_resolve_attack_phase_before_defense(
    monkeypatch, capsys
) -> None:
    cli = CLIApp()
    answers = iter(
        [
            "1",
            "2",
            "2",
            "6",
            "2",
            "choice",
            "1 2",
            "S",
            "2",
            "disabled",
            "1",
            "y",
            "choice",
            "4",
            "2",
            "switch soul",
            "1",
            "y",
            "n",
            "y",
            "n",
            "6",
        ]
    )

    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    try:
        cli.run()
    except SystemExit:
        pass

    output = capsys.readouterr().out

    assert "Stan attacks 'Soul Switch' (2 attempt(s) left)" in output
    assert "Stan missed 'Soul Switch' (1 attack attempt(s) left)." in output
    assert "Stan landed 'Soul Switch' to set the trick." in output
    assert "Denise tries 'Soul Switch' (1 attempt(s) left)" in output
    assert "Game finished. Winner: Stan" in output


def test_cli_trick_input_requires_selecting_a_suggestion(monkeypatch) -> None:
    controller = GameController(MatchParameters(player_ids=["p1", "p2"]))
    controller.start_game()

    cli = CLIApp()
    inputs = iter(["soul", "1", "y"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    trick = cli._ask_validated_trick_input(controller)

    assert trick == "Soul"


def test_cli_choose_official_preset_displays_v8_fine_rules(monkeypatch, capsys) -> None:
    cli = CLIApp()
    monkeypatch.setattr("builtins.input", lambda _prompt="": "5")

    preset = cli._choose_official_preset()
    output = capsys.readouterr().out

    assert preset.name == "classic_skate_v8"
    assert "Uniqueness=on, Repetition=choice, limit=4" in output


def test_cli_join_command_can_add_player_between_turns(monkeypatch, capsys) -> None:
    controller = GameController(MatchParameters(player_ids=["p1", "p2"]))
    controller.start_game()

    cli = CLIApp()
    monkeypatch.setattr("builtins.input", lambda _prompt="": "Alex")

    result = cli._handle_global_command(controller, "/join")
    output = capsys.readouterr().out

    assert result is None
    assert [player.id for player in controller.get_state().players] == ["p1", "p2", "Alex"]
    assert controller.structure_name == "battle"
    assert (
        "Alex joined the game. Structure changed: one_vs_one -> battle."
        in output
    )


def test_cli_remove_command_can_remove_player_between_turns(monkeypatch, capsys) -> None:
    controller = GameController(
        MatchParameters(player_ids=["p1", "p2", "p3"], structure_name="battle")
    )
    controller.start_game()

    cli = CLIApp()
    monkeypatch.setattr("builtins.input", lambda _prompt="": "p2")

    result = cli._handle_global_command(controller, "/remove")
    output = capsys.readouterr().out

    assert result is None
    assert [player.id for player in controller.get_state().players] == ["p1", "p3"]
    assert controller.structure_name == "one_vs_one"
    assert (
        "p2 left the game. Structure changed: battle -> one_vs_one."
        in output
    )


def test_cli_format_event_describes_structure_change_on_transition() -> None:
    cli = CLIApp()

    message = cli._format_event(
        Event(
            name=EventName.PLAYER_JOINED,
            payload={
                "player_id": "Alex",
                "player_name": "Alex",
                "previous_structure_name": "one_vs_one",
                "structure_name": "battle",
                "structure_changed": True,
                "preset_invalidated": True,
            },
        )
    )

    assert (
        message
        == "Alex joined the game. Structure changed: one_vs_one -> battle. Preset cleared."
    )


def test_cli_join_command_rejects_duplicate_player(monkeypatch, capsys) -> None:
    controller = GameController(MatchParameters(player_ids=["p1", "p2"]))
    controller.start_game()

    cli = CLIApp()
    monkeypatch.setattr("builtins.input", lambda _prompt="": "p2")

    result = cli._handle_global_command(controller, "/join")
    output = capsys.readouterr().out

    assert result is None
    assert [player.id for player in controller.get_state().players] == ["p1", "p2"]
    assert "Action invalide:" in output


def test_cli_remove_command_rejects_unknown_player(monkeypatch, capsys) -> None:
    controller = GameController(
        MatchParameters(player_ids=["p1", "p2", "p3"], structure_name="battle")
    )
    controller.start_game()

    cli = CLIApp()
    monkeypatch.setattr("builtins.input", lambda _prompt="": "p4")

    result = cli._handle_global_command(controller, "/remove")
    output = capsys.readouterr().out

    assert result is None
    assert [player.id for player in controller.get_state().players] == [
        "p1",
        "p2",
        "p3",
    ]
    assert "Action invalide:" in output
