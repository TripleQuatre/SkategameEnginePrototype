from application.game_session import GameSession
from config.fine_rules_config import FineRulesConfig
from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from core.types import AttackResolutionStatus, TurnPhase


def test_game_session_can_resolve_multi_attempt_attack_before_defense() -> None:
    session = GameSession(
        MatchParameters(
            player_ids=["p1", "p2"],
            rule_set=RuleSetConfig(attack_attempts=2),
            fine_rules=FineRulesConfig(
                repetition_mode="choice",
                repetition_limit=4,
            ),
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


def test_game_session_filters_switch_suggestions_when_switch_is_disabled() -> None:
    session = GameSession(
        MatchParameters(
            player_ids=["p1", "p2"],
            fine_rules=FineRulesConfig(switch_mode="disabled"),
        )
    )
    session.start_game()

    labels = [suggestion.label for suggestion in session.suggest_tricks("switch soul")]

    assert "Soul Switch" not in labels


def test_game_session_exposes_only_normalized_switches_in_normal_mode() -> None:
    session = GameSession(
        MatchParameters(
            player_ids=["p1", "p2"],
            fine_rules=FineRulesConfig(
                switch_mode="normal",
                uniqueness_enabled=False,
                repetition_mode="disabled",
            ),
        )
    )
    session.start_game()

    labels_before = [suggestion.label for suggestion in session.suggest_tricks("switch soul")]
    assert "Soul Switch" not in labels_before

    session.start_turn("Soul")
    session.resolve_defense(True)
    session.cancel_turn("Makio")

    labels_after = [suggestion.label for suggestion in session.suggest_tricks("switch soul")]
    assert "Soul Switch" in labels_after
