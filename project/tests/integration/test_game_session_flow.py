from application.game_session import GameSession
from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from core.types import AttackResolutionStatus, TurnPhase


def test_game_session_can_resolve_multi_attempt_attack_before_defense() -> None:
    session = GameSession(
        MatchParameters(
            player_ids=["p1", "p2"],
            rule_set=RuleSetConfig(attack_attempts=2),
        )
    )
    session.start_game()
    session.start_turn("Soul")

    first_attack = session.resolve_attack(False)
    second_attack = session.resolve_attack(True)
    state = session.get_state()

    assert first_attack == AttackResolutionStatus.ATTACK_CONTINUES
    assert second_attack == AttackResolutionStatus.DEFENSE_READY
    assert state.turn_phase == TurnPhase.DEFENSE
    assert state.defender_indices == [1]


def test_game_session_can_apply_roster_transition_between_turns() -> None:
    session = GameSession(MatchParameters(player_ids=["p1", "p2"]))
    session.start_game()
    session.add_player_between_turns("p3")
    state = session.get_state()

    assert session.structure_name == "battle"
    assert [player.id for player in state.players] == ["p1", "p2", "p3"]
    assert state.turn_phase == TurnPhase.TURN_OPEN
