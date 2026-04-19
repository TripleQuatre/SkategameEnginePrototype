from config.match_policies import (
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
)
from config.match_parameters import MatchParameters
from config.preset_registry import PresetRegistry
from config.rule_set_config import RuleSetConfig
from core.exceptions import InvalidStateError


class ConfigValidator:
    def __init__(self) -> None:
        self.preset_registry = PresetRegistry()

    def validate_match_parameters(self, match_parameters: MatchParameters) -> None:
        player_count = len(match_parameters.player_ids)
        structure_name = match_parameters.structure_name

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

        self._validate_policies(match_parameters)
        self._validate_preset_coherence(match_parameters)

    def validate_rule_set(self, rule_set: RuleSetConfig) -> None:
        if not rule_set.letters_word:
            raise ValueError("letters_word cannot be empty")

        if len(rule_set.letters_word) > 10:
            raise ValueError("letters_word cannot exceed 10 characters")

        if rule_set.attack_attempts < 1:
            raise ValueError("attack_attempts must be greater than or equal to 1")

        if not (1 <= rule_set.defense_attempts <= 3):
            raise ValueError("defense_attempts must be between 1 and 3")

    def _validate_policies(self, match_parameters: MatchParameters) -> None:
        policies = match_parameters.policies
        structure_name = match_parameters.structure_name

        if structure_name == "one_vs_one":
            if policies.initial_turn_order != InitialTurnOrderPolicy.FIXED_PLAYER_ORDER:
                raise InvalidStateError(
                    "One vs one structure requires a fixed initial turn order policy."
                )

            if policies.defender_order != DefenderOrderPolicy.FOLLOW_TURN_ORDER:
                raise InvalidStateError(
                    "One vs one structure requires defenders to follow turn order."
                )

    def _validate_preset_coherence(self, match_parameters: MatchParameters) -> None:
        preset_name = match_parameters.preset_name
        if preset_name is None:
            return

        if not self.preset_registry.has(preset_name):
            raise InvalidStateError(f"Unknown preset: {preset_name}")

        preset = self.preset_registry.get(preset_name)

        if match_parameters.structure_name != preset.structure_name:
            raise InvalidStateError(
                "preset_name does not match the configured structure_name."
            )

        if match_parameters.policies != preset.policies:
            raise InvalidStateError(
                "preset_name does not match the configured match policies."
            )

        if match_parameters.rule_set != preset.rule_set:
            raise InvalidStateError(
                "preset_name does not match the configured rule set."
            )
