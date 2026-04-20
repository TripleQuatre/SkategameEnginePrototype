from config.match_policies import (
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
)
from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.preset_registry import PresetRegistry
from config.rule_set_config import RuleSetConfig
from config.setup_translator import SetupTranslator
from core.exceptions import InvalidStateError


class ConfigValidator:
    def __init__(self) -> None:
        self.preset_registry = PresetRegistry()
        self.setup_translator = SetupTranslator()

    def validate_match_parameters(self, match_parameters: MatchParameters) -> None:
        self.validate_match_config(
            self.setup_translator.from_match_parameters(match_parameters)
        )

    def validate_match_config(self, match_config: MatchConfig) -> None:
        player_count = len(match_config.player_ids)
        structure_name = match_config.structure_name

        if player_count < 2:
            raise InvalidStateError("At least two players are required.")

        if not structure_name:
            raise InvalidStateError("A structure name is required.")

        if structure_name not in {"one_vs_one", "battle"}:
            raise InvalidStateError(f"Unknown structure: {structure_name}")

        if structure_name == "one_vs_one" and player_count != 2:
            raise InvalidStateError("One vs one structure requires exactly two players.")

        if structure_name == "battle" and player_count < 3:
            raise InvalidStateError("Battle structure requires at least three players.")

        self.validate_rule_set(match_config.to_rule_set_config())
        self._validate_policies(match_config)
        self._validate_runtime_families(match_config)
        self._validate_preset_coherence(match_config)

    def validate_rule_set(self, rule_set: RuleSetConfig) -> None:
        if not rule_set.letters_word:
            raise ValueError("letters_word cannot be empty")

        if len(rule_set.letters_word) > 10:
            raise ValueError("letters_word cannot exceed 10 characters")

        if rule_set.attack_attempts < 1:
            raise ValueError("attack_attempts must be greater than or equal to 1")

        if not (1 <= rule_set.defense_attempts <= 3):
            raise ValueError("defense_attempts must be between 1 and 3")

    def _validate_runtime_families(self, match_config: MatchConfig) -> None:
        if match_config.scoring.scoring_type != "letters":
            raise InvalidStateError(
                f"Unsupported scoring type: {match_config.scoring.scoring_type}"
            )

        if match_config.victory.victory_type != "last_player_standing":
            raise InvalidStateError(
                f"Unsupported victory type: {match_config.victory.victory_type}"
            )

    def _validate_policies(self, match_config: MatchConfig) -> None:
        policies = match_config.policies
        structure_name = match_config.structure_name

        if structure_name == "one_vs_one":
            if policies.initial_turn_order != InitialTurnOrderPolicy.FIXED_PLAYER_ORDER:
                raise InvalidStateError(
                    "One vs one structure requires a fixed initial turn order policy."
                )

            if policies.defender_order != DefenderOrderPolicy.FOLLOW_TURN_ORDER:
                raise InvalidStateError(
                    "One vs one structure requires defenders to follow turn order."
                )

    def _validate_preset_coherence(self, match_config: MatchConfig) -> None:
        preset_name = match_config.preset_name
        if preset_name is None:
            return

        if not self.preset_registry.has(preset_name):
            raise InvalidStateError(f"Unknown preset: {preset_name}")

        preset = self.preset_registry.get(preset_name)

        if match_config.structure_name != preset.structure_name:
            raise InvalidStateError(
                "preset_name does not match the configured structure_name."
            )

        if match_config.policies != preset.policies:
            raise InvalidStateError(
                "preset_name does not match the configured match policies."
            )

        if match_config.to_rule_set_config() != preset.rule_set:
            raise InvalidStateError(
                "preset_name does not match the configured rule set."
            )
