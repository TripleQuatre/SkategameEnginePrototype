import modes.battle as battle_module

from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.types import EventName, Phase
from engine.game_engine import GameEngine


def test_game_engine_can_save_and_load_engaged_turn(tmp_path) -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")

    filepath = tmp_path / "saved_game.json"
    engine.save_game(str(filepath))

    reloaded_engine = GameEngine(match_parameters)
    reloaded_engine.load_game(str(filepath))
    state = reloaded_engine.get_state()

    assert filepath.exists()
    assert state.phase == Phase.TURN
    assert state.turn_order == [0, 1]
    assert state.attacker_index == 0
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == state.rule_set.defense_attempts
    assert state.validated_tricks == []
    assert state.history.events[-1].name == EventName.TURN_STARTED


def test_game_engine_can_save_and_load_finished_game(tmp_path) -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.get_state().rule_set.letters_word = "S"

    engine.start_game()
    engine.start_turn("soul")
    engine.resolve_defense(False)

    filepath = tmp_path / "finished_game.json"
    engine.save_game(str(filepath))

    reloaded_engine = GameEngine(match_parameters)
    reloaded_engine.load_game(str(filepath))
    state = reloaded_engine.get_state()

    assert filepath.exists()
    assert state.phase == Phase.END
    assert state.turn_order == [0, 1]
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.players[1].is_active is False
    assert state.players[1].score == 1
    assert state.validated_tricks == ["soul"]
    assert state.history.events[-1].name == EventName.GAME_FINISHED


def test_game_engine_load_clears_previous_undo_history(tmp_path) -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")

    filepath = tmp_path / "saved_game.json"
    engine.save_game(str(filepath))

    engine.resolve_defense(True)
    assert engine.undo() is True

    engine.load_game(str(filepath))

    assert engine.undo() is False


def test_game_controller_can_save_and_load_engaged_turn(tmp_path) -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("kickflip")

    filepath = tmp_path / "controller_saved_game.json"
    controller.save_game(str(filepath))

    reloaded_controller = GameController(match_parameters)
    reloaded_controller.load_game(str(filepath))
    state = reloaded_controller.get_state()

    assert filepath.exists()
    assert state.phase == Phase.TURN
    assert state.turn_order == [0, 1]
    assert state.attacker_index == 0
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == state.rule_set.defense_attempts
    assert state.validated_tricks == []
    assert state.history.events[-1].name == EventName.TURN_STARTED


def test_game_controller_load_clears_previous_undo_history(tmp_path) -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("kickflip")

    filepath = tmp_path / "controller_saved_game.json"
    controller.save_game(str(filepath))

    controller.resolve_defense(True)
    assert controller.undo() is True

    controller.load_game(str(filepath))

    assert controller.undo() is False


def test_game_engine_can_load_battle_save_from_one_vs_one_placeholder(
    tmp_path, monkeypatch
) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_module.random, "shuffle", fixed_shuffle)

    battle_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        mode_name="battle",
    )
    engine = GameEngine(battle_parameters)

    engine.start_game()
    engine.start_turn("kickflip")

    filepath = tmp_path / "battle_saved_game.json"
    engine.save_game(str(filepath))

    placeholder_engine = GameEngine(
        MatchParameters(player_ids=["placeholder1", "placeholder2"])
    )
    placeholder_engine.load_game(str(filepath))
    state = placeholder_engine.get_state()

    assert filepath.exists()
    assert placeholder_engine.match_parameters.mode_name == "battle"
    assert state.phase == Phase.TURN
    assert state.turn_order == [2, 0, 1]
    assert state.attacker_index == 2
    assert state.defender_indices == [0, 1]
    assert state.current_trick == "kickflip"


def test_game_engine_load_relinks_match_parameters_and_state_rule_set(tmp_path) -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()

    filepath = tmp_path / "saved_game.json"
    engine.save_game(str(filepath))

    reloaded_engine = GameEngine(match_parameters)
    reloaded_engine.load_game(str(filepath))

    assert reloaded_engine.match_parameters.rule_set is reloaded_engine.get_state().rule_set

    reloaded_engine.get_state().rule_set.letters_word = "OUT"

    updated_filepath = tmp_path / "updated_saved_game.json"
    reloaded_engine.save_game(str(updated_filepath))

    final_engine = GameEngine(match_parameters)
    final_engine.load_game(str(updated_filepath))

    assert final_engine.match_parameters.rule_set.letters_word == "OUT"
    assert final_engine.get_state().rule_set.letters_word == "OUT"


def test_game_engine_can_save_and_load_reconfigured_one_vs_one_to_battle_game(
    tmp_path,
) -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        preset_name="classic_skate",
        rule_set=RuleSetConfig(
            letters_word="SKATE",
            elimination_enabled=True,
            defense_attempts=3,
        ),
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.add_player_between_turns("p3")

    filepath = tmp_path / "reconfigured_game.json"
    engine.save_game(str(filepath))

    reloaded_engine = GameEngine(MatchParameters(player_ids=["placeholder1", "placeholder2"]))
    reloaded_engine.load_game(str(filepath))

    state = reloaded_engine.get_state()
    assert reloaded_engine.match_parameters.mode_name == "battle"
    assert reloaded_engine.match_parameters.preset_name is None
    assert reloaded_engine.match_parameters.player_ids == ["p1", "p2", "p3"]
    assert [player.id for player in state.players] == ["p1", "p2", "p3"]
    assert state.turn_order == [0, 1, 2]
    assert state.history.events[-1].name == EventName.PLAYER_JOINED


def test_game_engine_can_save_and_load_reconfigured_battle_to_one_vs_one_game(
    tmp_path,
) -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        mode_name="battle",
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.remove_player_between_turns("p2")

    filepath = tmp_path / "reconfigured_one_vs_one_game.json"
    engine.save_game(str(filepath))

    reloaded_engine = GameEngine(
        MatchParameters(player_ids=["placeholder1", "placeholder2"])
    )
    reloaded_engine.load_game(str(filepath))

    state = reloaded_engine.get_state()
    assert reloaded_engine.match_parameters.mode_name == "one_vs_one"
    assert reloaded_engine.match_parameters.preset_name is None
    assert reloaded_engine.match_parameters.player_ids == ["p1", "p3"]
    assert [player.id for player in state.players] == ["p1", "p3"]
    assert state.turn_order == [0, 1]
    assert state.history.events[-1].name == EventName.PLAYER_REMOVED
