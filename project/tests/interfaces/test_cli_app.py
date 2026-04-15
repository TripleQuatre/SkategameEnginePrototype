import modes.battle as battle_module

from config.match_parameters import MatchParameters
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
