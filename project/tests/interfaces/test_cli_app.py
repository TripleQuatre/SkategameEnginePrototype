import modes.battle as battle_module

from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.events import Event
from core.types import EventName
from interfaces.cli.cli_app import CLIApp


def test_cli_end_of_game_loop_can_undo_finished_game(monkeypatch, capsys) -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.get_state().rule_set.letters_word = "S"
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


def test_cli_load_saved_game_controller_reports_consultation_for_finished_game(
    tmp_path, monkeypatch, capsys
) -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.get_state().rule_set.letters_word = "S"
    controller.start_game()
    controller.start_turn("soul")
    controller.resolve_defense(False)

    save_path = tmp_path / "finished_game.json"
    controller.save_game(str(save_path))

    cli = CLIApp()
    monkeypatch.setattr(cli, "_choose_save_file", lambda: save_path)

    loaded_controller = cli._load_saved_game_controller()
    output = capsys.readouterr().out

    assert loaded_controller is not None
    assert "Consultation mode." in output
    assert loaded_controller.get_state().phase.value == "end"


def test_cli_display_history_renders_battle_turns(monkeypatch, capsys) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_module.random, "shuffle", fixed_shuffle)

    match_parameters = MatchParameters(
        player_ids=["Stan", "Denise", "Alex"],
        mode_name="battle",
    )
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("kickflip")
    controller.resolve_defense(True)
    controller.resolve_defense(False)

    cli = CLIApp()
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
    tmp_path, monkeypatch, capsys
) -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.get_state().rule_set.letters_word = "S"
    controller.start_game()
    controller.start_turn("soul")
    controller.resolve_defense(False)

    save_path = tmp_path / "finished_game.json"
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


def test_cli_new_game_preset_flow_selects_preset_before_player_names(
    monkeypatch,
) -> None:
    cli = CLIApp()
    prompts: list[str] = []
    answers = iter(["1", "3", "3", "Stan", "Denise", "Alex"])

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr("builtins.input", fake_input)

    controller = cli._create_new_game_controller()

    assert controller.engine.match_parameters.preset_name == "battle_standard"
    assert prompts.index("Choose a preset (1-4): ") < prompts.index(
        "Player 1 name: "
    )


def test_cli_new_game_can_start_without_preset(monkeypatch) -> None:
    cli = CLIApp()
    answers = iter(["2", "2", "Stan", "Denise", "OUT", "3"])

    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    controller = cli._create_new_game_controller()
    match_parameters = controller.engine.match_parameters

    assert match_parameters.preset_name is None
    assert match_parameters.mode_name == "one_vs_one"
    assert match_parameters.rule_set.letters_word == "OUT"
    assert match_parameters.rule_set.defense_attempts == 3


def test_cli_join_command_can_add_player_between_turns(monkeypatch, capsys) -> None:
    controller = GameController(MatchParameters(player_ids=["p1", "p2"]))
    controller.start_game()

    cli = CLIApp()
    monkeypatch.setattr("builtins.input", lambda _prompt="": "Alex")

    result = cli._handle_global_command(controller, "/join")
    output = capsys.readouterr().out

    assert result is None
    assert [player.id for player in controller.get_state().players] == ["p1", "p2", "Alex"]
    assert controller.engine.match_parameters.mode_name == "battle"
    assert "Alex joined the game." in output


def test_cli_remove_command_can_remove_player_between_turns(monkeypatch, capsys) -> None:
    controller = GameController(
        MatchParameters(player_ids=["p1", "p2", "p3"], mode_name="battle")
    )
    controller.start_game()

    cli = CLIApp()
    monkeypatch.setattr("builtins.input", lambda _prompt="": "p2")

    result = cli._handle_global_command(controller, "/remove")
    output = capsys.readouterr().out

    assert result is None
    assert [player.id for player in controller.get_state().players] == ["p1", "p3"]
    assert controller.engine.match_parameters.mode_name == "one_vs_one"
    assert "p2 left the game." in output


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
        MatchParameters(player_ids=["p1", "p2", "p3"], mode_name="battle")
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
