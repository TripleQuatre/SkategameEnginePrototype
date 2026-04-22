import pytest

from config.fine_rules_config import FineRulesConfig
from config.match_parameters import MatchParameters
from config.match_policies import DefenderOrderPolicy, InitialTurnOrderPolicy, MatchPolicies
from config.rule_set_config import RuleSetConfig
from core.player import Player
from core.state import GameState
from core.types import Phase, TurnPhase
from core.exceptions import InvalidActionError, InvalidStateError
from dictionary.runtime import resolve_runtime_trick_record
from match.flow.trick_rules import TrickRules
from validation.action_validator import ActionValidator
from validation.config_validator import ConfigValidator
from validation.state_validator import StateValidator


def test_config_validator_rejects_less_than_two_players() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(player_ids=["p1"])

    with pytest.raises(InvalidStateError):
        validator.validate_match_parameters(match_parameters)


def test_config_validator_rejects_empty_structure_name() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(player_ids=["p1", "p2"], structure_name="")

    with pytest.raises(InvalidStateError):
        validator.validate_match_parameters(match_parameters)


def test_config_validator_rejects_unknown_structure_name() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(player_ids=["p1", "p2"], structure_name="weird_mode")

    with pytest.raises(InvalidStateError):
        validator.validate_match_parameters(match_parameters)


def test_config_validator_rejects_randomized_one_vs_one_order_policy() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        structure_name="one_vs_one",
        policies=MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
        ),
    )

    with pytest.raises(InvalidStateError):
        validator.validate_match_parameters(match_parameters)


def test_config_validator_rejects_reverse_defender_order_for_one_vs_one() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        structure_name="one_vs_one",
        policies=MatchPolicies(
            defender_order=DefenderOrderPolicy.REVERSE_TURN_ORDER,
        ),
    )

    with pytest.raises(InvalidStateError):
        validator.validate_match_parameters(match_parameters)


def test_config_validator_accepts_official_preset_configuration() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        structure_name="one_vs_one",
        preset_name="classic_skate",
        rule_set=RuleSetConfig(
            letters_word="SKATE",
            elimination_enabled=True,
            defense_attempts=3,
        ),
    )

    validator.validate_match_parameters(match_parameters)


def test_config_validator_rejects_unknown_preset_name() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        structure_name="one_vs_one",
        preset_name="unknown_preset",
    )

    with pytest.raises(InvalidStateError):
        validator.validate_match_parameters(match_parameters)


def test_config_validator_rejects_preset_name_mismatch_with_policies() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        structure_name="one_vs_one",
        preset_name="classic_skate",
        rule_set=RuleSetConfig(
            letters_word="SKATE",
            elimination_enabled=True,
            defense_attempts=3,
        ),
        policies=MatchPolicies(
            defender_order=DefenderOrderPolicy.REVERSE_TURN_ORDER,
        ),
    )

    with pytest.raises(InvalidStateError):
        validator.validate_match_parameters(match_parameters)


def test_config_validator_rejects_preset_name_mismatch_with_rule_set() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
        preset_name="battle_hardcore",
        policies=MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
        ),
        rule_set=RuleSetConfig(
            letters_word="OUT",
            elimination_enabled=True,
            defense_attempts=3,
        ),
    )

    with pytest.raises(InvalidStateError):
        validator.validate_match_parameters(match_parameters)


def test_config_validator_rejects_empty_letters_word() -> None:
    validator = ConfigValidator()
    rule_set = RuleSetConfig(letters_word="")

    with pytest.raises(ValueError):
        validator.validate_rule_set(rule_set)


def test_config_validator_rejects_invalid_defense_attempts() -> None:
    validator = ConfigValidator()
    rule_set = RuleSetConfig(defense_attempts=0)

    with pytest.raises(ValueError):
        validator.validate_rule_set(rule_set)


def test_config_validator_rejects_invalid_attack_attempts() -> None:
    validator = ConfigValidator()
    rule_set = RuleSetConfig(attack_attempts=0)

    with pytest.raises(ValueError):
        validator.validate_rule_set(rule_set)


def test_state_validator_rejects_invalid_attacker_index() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        attacker_index=5,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)


def test_state_validator_rejects_negative_defense_attempts_left() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        defense_attempts_left=-1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)


def test_action_validator_rejects_start_turn_outside_turn_phase() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.SETUP,
    )

    with pytest.raises(InvalidActionError):
        validator.validate_start_turn(state, "kickflip")


def test_action_validator_rejects_empty_trick() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
    )

    with pytest.raises(InvalidActionError):
        validator.validate_start_turn(state, "")


def test_action_validator_rejects_start_turn_when_a_trick_is_already_engaged() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        current_trick="soul",
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidActionError):
        validator.validate_start_turn(state, "kickflip")


def test_action_validator_rejects_resolve_defense_without_current_trick() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        defender_indices=[1],
        current_defender_position=0,
        current_trick=None,
    )

    with pytest.raises(InvalidActionError):
        validator.validate_resolve_defense(state)

def test_action_validator_allows_cancel_turn_when_no_trick_is_engaged() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        current_trick=None,
    )

    validator.validate_cancel_turn(state, "Soul")

def test_action_validator_rejects_cancel_turn_outside_turn_phase() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.SETUP,
        current_trick=None,
    )

    with pytest.raises(InvalidActionError):
        validator.validate_cancel_turn(state, "Soul")

def test_action_validator_rejects_cancel_turn_without_trick_name() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        current_trick=None,
    )

    with pytest.raises(InvalidActionError):
        validator.validate_cancel_turn(state, "")

def test_action_validator_rejects_cancel_turn_when_trick_is_engaged() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        current_trick="Soul",
    )

    with pytest.raises(InvalidActionError):
        validator.validate_cancel_turn(state, "Soul")

def test_action_validator_rejects_start_turn_with_already_consumed_trick() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        validated_tricks=["soul"],
    )

    with pytest.raises(InvalidActionError):
        validator.validate_start_turn(state, "Soul")


def test_action_validator_rejects_canonically_equivalent_dictionary_trick() -> None:
    validator = ActionValidator(TrickRules())
    _, trick_data = resolve_runtime_trick_record("Soul Switch")
    assert trick_data is not None
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        validated_trick_data=[trick_data],
    )

    with pytest.raises(InvalidActionError):
        validator.validate_start_turn(state, "Switch Soul")


def test_action_validator_allows_revalidated_trick_when_uniqueness_disabled() -> None:
    validator = ActionValidator(
        TrickRules(FineRulesConfig(uniqueness_enabled=False))
    )
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        validated_tricks=["soul"],
    )

    validator.validate_start_turn(state, "Soul")


def test_action_validator_rejects_dictionary_trick_when_choice_repetition_limit_is_reached() -> None:
    validator = ActionValidator(
        TrickRules(FineRulesConfig(repetition_mode="choice", repetition_limit=1))
    )
    _, trick_data = resolve_runtime_trick_record("Soul Switch")
    assert trick_data is not None
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        failed_attack_trick_data=[
            {
                "attacker_id": "p1",
                "trick": "Soul Switch",
                "trick_key": trick_data["canonical_key"],
                "trick_label": trick_data["label"],
                "trick_data": trick_data,
            }
        ],
    )

    with pytest.raises(InvalidActionError):
        validator.validate_start_turn(state, "Switch Soul")


def test_action_validator_rejects_dictionary_trick_when_common_repetition_limit_is_reached() -> None:
    validator = ActionValidator(
        TrickRules(FineRulesConfig(repetition_mode="common", repetition_limit=1))
    )
    _, trick_data = resolve_runtime_trick_record("Soul")
    assert trick_data is not None
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        attacker_index=1,
        failed_attack_trick_data=[
            {
                "attacker_id": "p1",
                "trick": "Soul",
                "trick_key": trick_data["canonical_key"],
                "trick_label": trick_data["label"],
                "trick_data": trick_data,
            }
        ],
    )

    with pytest.raises(InvalidActionError):
        validator.validate_start_turn(state, "Soul")


def test_action_validator_allows_trick_when_repetition_is_disabled() -> None:
    validator = ActionValidator(
        TrickRules(FineRulesConfig(repetition_mode="disabled", repetition_limit=1))
    )
    _, trick_data = resolve_runtime_trick_record("Soul")
    assert trick_data is not None
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        failed_attack_trick_data=[
            {
                "attacker_id": "p1",
                "trick": "Soul",
                "trick_key": trick_data["canonical_key"],
                "trick_label": trick_data["label"],
                "trick_data": trick_data,
            }
        ],
    )

    validator.validate_start_turn(state, "Soul")

def test_state_validator_rejects_defender_indices_when_no_trick_is_engaged() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        current_trick=None,
        defender_indices=[1],
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_current_defender_position_when_no_trick_is_engaged() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        current_trick=None,
        current_defender_position=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_defense_attempts_left_when_no_trick_is_engaged() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        current_trick=None,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_defender_indices_when_no_trick_is_engaged() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        current_trick=None,
        defender_indices=[1],
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_current_defender_position_when_no_trick_is_engaged() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        current_trick=None,
        current_defender_position=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_defense_attempts_left_when_no_trick_is_engaged() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        current_trick=None,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_engaged_trick_outside_turn_phase() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.SETUP,
        current_trick="Soul",
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_engaged_trick_without_defenders() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        current_trick="Soul",
        defender_indices=[],
        current_defender_position=0,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_current_defender_position_out_of_range_for_engaged_trick() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        current_trick="Soul",
        defender_indices=[1],
        current_defender_position=1,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_non_positive_defense_attempts_for_engaged_trick() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        current_trick="Soul",
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=0,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_attacker_in_defender_indices() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        attacker_index=0,
        current_trick="Soul",
        defender_indices=[0, 1],
        current_defender_position=0,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_duplicate_defender_indices() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        current_trick="Soul",
        defender_indices=[1, 1],
        current_defender_position=0,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_rejects_inactive_player_in_defender_indices() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2", is_active=False),
        ],
        phase=Phase.TURN,
        current_trick="Soul",
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)

def test_state_validator_accepts_consistent_engaged_trick_state() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        attacker_index=0,
        current_trick="Soul",
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
    )

    validator.validate(state)


def test_action_validator_rejects_start_turn_when_turn_is_not_open() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
    )

    with pytest.raises(InvalidActionError):
        validator.validate_start_turn(state, "kickflip")


def test_action_validator_rejects_resolve_defense_outside_defense_phase() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        current_trick="Soul",
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
    )

    with pytest.raises(InvalidActionError):
        validator.validate_resolve_defense(state)


def test_action_validator_rejects_resolve_attack_outside_attack_phase() -> None:
    validator = ActionValidator(TrickRules())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        current_trick="Soul",
    )

    with pytest.raises(InvalidActionError):
        validator.validate_resolve_attack(state)


def test_state_validator_rejects_non_open_turn_phase_when_no_trick_is_engaged() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        current_trick=None,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)


def test_state_validator_accepts_consistent_attack_phase_state() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.ATTACK,
        current_trick="Soul",
        attack_attempts_left=1,
        defender_indices=[],
        current_defender_position=0,
        defense_attempts_left=0,
    )

    validator.validate(state)


def test_state_validator_rejects_attack_phase_without_attack_attempts() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.ATTACK,
        current_trick="Soul",
        attack_attempts_left=0,
        defender_indices=[],
        current_defender_position=0,
        defense_attempts_left=0,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)


def test_state_validator_rejects_negative_attack_attempts_left() -> None:
    validator = StateValidator()
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        attack_attempts_left=-1,
    )

    with pytest.raises(InvalidStateError):
        validator.validate(state)
