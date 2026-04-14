from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from core.exceptions import InvalidStateError


class ConfigValidator:
    def validate_match_parameters(self, match_parameters: MatchParameters) -> None:
        player_count = len(match_parameters.player_ids)

        if player_count < 2:
            raise InvalidStateError("At least two players are required.")

        if not match_parameters.mode_name:
            raise InvalidStateError("A mode name is required.")

        if match_parameters.mode_name == "one_vs_one" and player_count != 2:
            raise InvalidStateError("One vs one mode requires exactly two players.")

        if match_parameters.mode_name == "battle" and player_count < 3:
            raise InvalidStateError("Battle mode requires at least three players.")

    def validate_rule_set(self, rule_set: RuleSetConfig) -> None:
        if not rule_set.letters_word:
            raise ValueError("letters_word cannot be empty")

        if len(rule_set.letters_word) > 10:
            raise ValueError("letters_word cannot exceed 10 characters")

        if not (1 <= rule_set.defense_attempts <= 3):
            raise ValueError("defense_attempts must be between 1 and 3")
