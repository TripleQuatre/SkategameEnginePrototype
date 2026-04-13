import pytest

from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from core.player import Player
from core.state import GameState
from core.types import Phase
from core.exceptions import InvalidActionError, InvalidStateError
from validation.action_validator import ActionValidator
from validation.config_validator import ConfigValidator
from validation.state_validator import StateValidator
from rules.rules_registry import RulesRegistry


def test_config_validator_rejects_less_than_two_players() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(player_ids=["p1"])

    with pytest.raises(InvalidStateError):
        validator.validate_match_parameters(match_parameters)


def test_config_validator_rejects_empty_mode_name() -> None:
    validator = ConfigValidator()
    match_parameters = MatchParameters(player_ids=["p1", "p2"], mode_name="")

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
    validator = ActionValidator(RulesRegistry())
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
    validator = ActionValidator(RulesRegistry())
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
        ],
        phase=Phase.TURN,
    )

    with pytest.raises(InvalidActionError):
        validator.validate_start_turn(state, "")


def test_action_validator_rejects_resolve_defense_without_current_trick() -> None:
    validator = ActionValidator(RulesRegistry())
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
    validator = ActionValidator(RulesRegistry())
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
    validator = ActionValidator(RulesRegistry())
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
    validator = ActionValidator(RulesRegistry())
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
    validator = ActionValidator(RulesRegistry())
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
    validator = ActionValidator(RulesRegistry())
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
