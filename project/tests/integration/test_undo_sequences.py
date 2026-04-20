from application.game_session import GameSession as GameEngine
from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.types import DefenseResolutionStatus, EventName, Phase


def test_game_engine_can_undo_multiple_steps_back_to_setup() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")
    result = engine.resolve_defense(True)

    assert result == DefenseResolutionStatus.TURN_FINISHED

    assert engine.undo() is True
    state = engine.get_state()
    assert state.phase == Phase.TURN
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == engine.match_config.defense_attempts
    assert state.validated_tricks == []
    assert state.history.events[-1].name == EventName.TURN_STARTED

    assert engine.undo() is True
    state = engine.get_state()
    assert state.phase == Phase.TURN
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.history.events[-1].name == EventName.GAME_STARTED

    assert engine.undo() is True
    state = engine.get_state()
    assert state.phase == Phase.SETUP
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events == []

    assert engine.undo() is False


def test_game_engine_undo_after_game_finished_restores_engaged_turn() -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        rule_set=RuleSetConfig(letters_word="S"),
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("soul")
    result = engine.resolve_defense(False)

    assert result == DefenseResolutionStatus.GAME_FINISHED

    undone = engine.undo()
    state = engine.get_state()

    assert undone is True
    assert state.phase == Phase.TURN
    assert state.current_trick == "soul"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 1
    assert state.players[1].is_active is True
    assert state.players[1].score == 0
    assert state.validated_tricks == []
    assert state.history.events[-1].name == EventName.TURN_STARTED


def test_game_engine_can_replay_same_trick_after_undo_of_finished_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("soul")
    result = engine.resolve_defense(True)

    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert "soul" in engine.get_state().validated_tricks

    assert engine.undo() is True

    replay_result = engine.resolve_defense(True)
    state = engine.get_state()

    assert replay_result == DefenseResolutionStatus.TURN_FINISHED
    assert "soul" in state.validated_tricks
    assert state.history.events[-1].name == EventName.TURN_ENDED


def test_game_engine_undo_after_cancel_turn_restores_open_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.cancel_turn("soul")

    assert engine.undo() is True
    state = engine.get_state()

    assert state.phase == Phase.TURN
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.validated_tricks == []
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_game_controller_can_undo_multiple_steps_back_to_setup() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("kickflip")
    result = controller.resolve_defense(True)

    assert result == DefenseResolutionStatus.TURN_FINISHED

    assert controller.undo() is True
    state = controller.get_state()
    assert state.phase == Phase.TURN
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == controller.match_config.defense_attempts
    assert state.validated_tricks == []
    assert state.history.events[-1].name == EventName.TURN_STARTED

    assert controller.undo() is True
    state = controller.get_state()
    assert state.phase == Phase.TURN
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.history.events[-1].name == EventName.GAME_STARTED

    assert controller.undo() is True
    state = controller.get_state()
    assert state.phase == Phase.SETUP
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events == []

    assert controller.undo() is False


def test_game_engine_undo_after_player_join_restores_one_vs_one_configuration() -> None:
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2"],
            preset_name="classic_skate",
            rule_set=RuleSetConfig(
                letters_word="SKATE",
                elimination_enabled=True,
                defense_attempts=3,
            ),
        )
    )

    engine.start_game()
    engine.add_player_between_turns("p3")

    assert engine.undo() is True

    state = engine.get_state()
    assert engine.structure_name == "one_vs_one"
    assert engine.match_parameters.preset_name == "classic_skate"
    assert engine.match_parameters.player_ids == ["p1", "p2"]
    assert [player.id for player in state.players] == ["p1", "p2"]
    assert state.turn_order == [0, 1]
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_game_engine_undo_after_player_removal_restores_previous_battle_configuration(
) -> None:
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            structure_name="battle",
        )
    )

    engine.start_game()
    engine.remove_player_between_turns("p2")

    assert engine.undo() is True

    state = engine.get_state()
    assert engine.structure_name == "battle"
    assert engine.match_parameters.player_ids == ["p1", "p2", "p3"]
    assert [player.id for player in state.players] == ["p1", "p2", "p3"]
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_game_engine_undo_can_walk_back_join_then_remove_sequence() -> None:
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2"],
            preset_name="classic_skate",
            rule_set=RuleSetConfig(
                letters_word="SKATE",
                elimination_enabled=True,
                defense_attempts=3,
            ),
        )
    )

    engine.start_game()
    engine.add_player_between_turns("p3")
    engine.remove_player_between_turns("p2")

    assert engine.undo() is True
    state = engine.get_state()
    assert engine.structure_name == "battle"
    assert engine.match_parameters.preset_name is None
    assert engine.match_parameters.player_ids == ["p1", "p2", "p3"]
    assert [player.id for player in state.players] == ["p1", "p2", "p3"]
    assert state.turn_order == [0, 1, 2]
    assert state.history.events[-1].name == EventName.PLAYER_JOINED

    assert engine.undo() is True
    state = engine.get_state()
    assert engine.structure_name == "one_vs_one"
    assert engine.match_parameters.preset_name == "classic_skate"
    assert engine.match_parameters.player_ids == ["p1", "p2"]
    assert [player.id for player in state.players] == ["p1", "p2"]
    assert state.turn_order == [0, 1]
    assert state.history.events[-1].name == EventName.GAME_STARTED
