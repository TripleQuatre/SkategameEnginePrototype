from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from core.exceptions import InvalidStateError


class ConfigValidator:
    def validate_match_parameters(self, match_parameters: MatchParameters) -> None:
        if len(match_parameters.player_ids) < 2:
            raise InvalidStateError("At least two players are required.")

        if not match_parameters.mode_name:
            raise InvalidStateError("A mode name is required.")

    def validate_rule_set(self, rule_set: RuleSetConfig) -> None:
        if not rule_set.letters_word:
            raise ValueError("letters_word cannot be empty")

        if len(rule_set.letters_word) > 10:
            raise ValueError("letters_word cannot exceed 10 characters")

        if not (1 <= rule_set.defense_attempts <= 3):
            raise ValueError("defense_attempts must be between 1 and 3")