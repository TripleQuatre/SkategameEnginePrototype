from config.match_parameters import MatchParameters
from controllers.game_controller import GameController
from core.types import DefenseResolutionStatus, EventName, Phase


def test_game_controller_can_start_a_game() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()

    state = controller.get_state()
    assert state.phase == Phase.TURN
    assert state.attacker_index == 0
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_game_controller_can_start_a_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("kickflip")

    state = controller.get_state()
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.history.events[-1].name == EventName.TURN_STARTED


def test_game_controller_defense_success_finishes_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("kickflip")
    result = controller.resolve_defense(True)

    state = controller.get_state()
    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert state.attacker_index == 1
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == EventName.TURN_ENDED


def test_game_controller_defense_failure_can_finish_game() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.get_state().rule_set.letters_word = "S"

    controller.start_game()
    controller.start_turn("kickflip")
    result = controller.resolve_defense(False)

    state = controller.get_state()
    assert result == DefenseResolutionStatus.GAME_FINISHED
    assert state.phase == Phase.END
    assert state.players[1].is_active is False
    assert state.history.events[-1].name == EventName.GAME_FINISHED
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0


def test_game_controller_undo_returns_false_when_no_snapshot_exists() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    assert controller.undo() is False


def test_game_controller_undo_restores_state_before_start_game() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()

    undone = controller.undo()
    state = controller.get_state()

    assert undone is True
    assert state.phase == Phase.SETUP
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events == []


def test_game_controller_undo_restores_state_before_start_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("kickflip")

    undone = controller.undo()
    state = controller.get_state()

    assert undone is True
    assert state.phase == Phase.TURN
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_game_controller_undo_restores_state_before_resolve_defense() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()
    controller.start_turn("kickflip")
    controller.resolve_defense(True)

    undone = controller.undo()
    state = controller.get_state()

    assert undone is True
    assert state.phase == Phase.TURN
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == state.rule_set.defense_attempts
    assert state.validated_tricks == []
    assert state.history.events[-1].name == EventName.TURN_STARTED


def test_game_controller_undo_restores_state_before_cancel_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    controller = GameController(match_parameters)

    controller.start_game()
    controller.cancel_turn("Soul")

    undone = controller.undo()
    state = controller.get_state()

    assert undone is True
    assert state.phase == Phase.TURN
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == EventName.GAME_STARTED
