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

    with pytest.raises(InvalidStateError):
        validator.validate_rule_set(rule_set)


def test_config_validator_rejects_invalid_defense_attempts() -> None:
    validator = ConfigValidator()
    rule_set = RuleSetConfig(defense_attempts=0)

    with pytest.raises(InvalidStateError):
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
    validator = ActionValidator()
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
    validator = ActionValidator()
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
    validator = ActionValidator()
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