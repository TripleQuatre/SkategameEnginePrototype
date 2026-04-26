from application.game_session import GameSession as GameEngine
import match.structure.battle_structure as battle_structure_module

from config.fine_rules_config import FineRulesConfig
from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from core.exceptions import InvalidActionError
from core.types import AttackResolutionStatus, DefenseResolutionStatus, EventName, Phase, TurnPhase


def test_game_engine_can_start_a_game() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()

    state = engine.get_state()
    assert state.phase == Phase.TURN
    assert state.turn_order == [0, 1]
    assert state.attacker_index == 0
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_game_engine_can_start_a_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")

    state = engine.get_state()
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == engine.match_config.defense_attempts
    assert state.history.events[-1].name == EventName.TURN_STARTED


def test_game_engine_defense_failure_can_finish_game() -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        rule_set=RuleSetConfig(letters_word="S"),
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")
    result = engine.resolve_defense(False)

    state = engine.get_state()
    assert result == DefenseResolutionStatus.GAME_FINISHED
    assert state.phase == Phase.END
    assert state.players[1].score == 1
    assert state.players[1].is_active is False
    assert state.history.events[-1].name == EventName.GAME_FINISHED
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0

def test_game_engine_defense_success_finishes_turn_and_rotates_attacker() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")
    result = engine.resolve_defense(True)

    state = engine.get_state()
    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert state.attacker_index == 1
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == EventName.TURN_ENDED


def test_game_engine_undo_returns_false_when_no_snapshot_exists() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    assert engine.undo() is False


def test_game_engine_undo_restores_state_before_start_game() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()

    undone = engine.undo()
    state = engine.get_state()

    assert undone is True
    assert state.phase == Phase.SETUP
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events == []


def test_game_engine_undo_restores_state_before_start_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")

    undone = engine.undo()
    state = engine.get_state()

    assert undone is True
    assert state.phase == Phase.TURN
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_game_engine_undo_restores_state_before_resolve_defense() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")
    engine.resolve_defense(True)

    undone = engine.undo()
    state = engine.get_state()

    assert undone is True
    assert state.phase == Phase.TURN
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == engine.match_config.defense_attempts
    assert state.validated_tricks == []
    assert state.history.events[-1].name == EventName.TURN_STARTED


def test_game_engine_undo_restores_state_before_cancel_turn() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.cancel_turn("Soul")

    undone = engine.undo()
    state = engine.get_state()

    assert undone is True
    assert state.phase == Phase.TURN
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_battle_game_engine_start_turn_sets_multiple_defenders(monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")

    state = engine.get_state()
    assert state.turn_order == [2, 0, 1]
    assert state.attacker_index == 2
    assert state.defender_indices == [0, 1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == engine.match_config.defense_attempts


def test_battle_game_engine_rotates_to_next_active_attacker(monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")
    engine.resolve_defense(True)
    result = engine.resolve_defense(True)

    state = engine.get_state()
    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == EventName.TURN_ENDED


def test_game_engine_can_resolve_multi_attempt_attack_before_defense() -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        rule_set=RuleSetConfig(
            letters_word="SKATE",
            attack_attempts=2,
            defense_attempts=1,
        ),
        fine_rules=FineRulesConfig(
            repetition_mode="choice",
            repetition_limit=4,
        ),
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.start_turn("kickflip")

    state = engine.get_state()
    assert state.turn_phase == TurnPhase.ATTACK
    assert state.attack_attempts_left == 2
    assert state.defender_indices == []

    attack_result = engine.resolve_attack(False)
    state = engine.get_state()
    assert attack_result == AttackResolutionStatus.ATTACK_CONTINUES
    assert state.turn_phase == TurnPhase.ATTACK
    assert state.attack_attempts_left == 1

    attack_result = engine.resolve_attack(True)
    state = engine.get_state()
    assert attack_result == AttackResolutionStatus.DEFENSE_READY
    assert state.turn_phase == TurnPhase.DEFENSE
    assert state.attack_attempts_left == 0
    assert state.defender_indices == [1]
    assert state.defense_attempts_left == 1

    defense_result = engine.resolve_defense(False)
    state = engine.get_state()
    assert defense_result == DefenseResolutionStatus.TURN_FINISHED
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.attacker_index == 1

    history_names = [event.name for event in state.history.events]
    assert EventName.ATTACK_FAILED_ATTEMPT in history_names
    assert EventName.ATTACK_SUCCEEDED in history_names


def test_game_engine_can_add_player_between_turns_and_switch_to_battle() -> None:
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

    state = engine.get_state()
    assert engine.structure_name == "battle"
    assert engine.match_parameters.preset_name is None
    assert engine.match_parameters.player_ids == ["p1", "p2", "p3"]
    assert [player.id for player in state.players] == ["p1", "p2", "p3"]
    assert state.turn_order == [0, 1, 2]
    assert state.attacker_index == 0
    assert state.history.events[-1].name == EventName.PLAYER_JOINED


def test_game_engine_add_player_between_turns_extends_defenders_on_next_trick() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.add_player_between_turns("p3")
    engine.start_turn("kickflip")

    state = engine.get_state()
    assert state.defender_indices == [1, 2]


def test_game_engine_can_remove_player_between_turns_and_switch_to_one_vs_one() -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
    )
    engine = GameEngine(match_parameters)

    engine.start_game()
    engine.remove_player_between_turns("p2")

    state = engine.get_state()
    assert engine.structure_name == "one_vs_one"
    assert engine.match_parameters.preset_name is None
    assert engine.match_parameters.player_ids == ["p1", "p3"]
    assert [player.id for player in state.players] == ["p1", "p3"]
    assert state.turn_order == [0, 1]
    assert state.history.events[-1].name == EventName.PLAYER_REMOVED


def test_game_engine_remove_attacker_between_turns_reassigns_next_attacker(
    monkeypatch,
) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            structure_name="battle",
        )
    )

    engine.start_game()
    engine.remove_player_between_turns("p3")

    state = engine.get_state()
    assert [player.id for player in state.players] == ["p1", "p2"]
    assert state.attacker_index == 0
    assert state.turn_order == [0, 1]


def test_game_engine_rejects_adding_duplicate_player_between_turns() -> None:
    engine = GameEngine(MatchParameters(player_ids=["p1", "p2"]))

    engine.start_game()

    try:
        engine.add_player_between_turns("p2")
        assert False, "Expected InvalidActionError"
    except InvalidActionError:
        pass


def test_game_engine_rejects_removing_unknown_player_between_turns() -> None:
    engine = GameEngine(
        MatchParameters(player_ids=["p1", "p2", "p3"], structure_name="battle")
    )

    engine.start_game()

    try:
        engine.remove_player_between_turns("p4")
        assert False, "Expected InvalidActionError"
    except InvalidActionError:
        pass


def test_game_engine_remove_player_between_turns_keeps_battle_mode_with_three_players_left(
    monkeypatch,
) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [1, 3, 0, 2]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3", "p4"],
            structure_name="battle",
        )
    )

    engine.start_game()
    engine.remove_player_between_turns("p3")

    state = engine.get_state()
    assert engine.structure_name == "battle"
    assert engine.match_parameters.player_ids == ["p1", "p2", "p4"]
    assert [player.id for player in state.players] == ["p1", "p2", "p4"]
    assert state.turn_order == [1, 2, 0]
    assert state.attacker_index == 1
