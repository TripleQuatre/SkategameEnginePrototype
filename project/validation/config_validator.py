from config.match_policies import (
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
    RelevanceCriterion,
)
from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.preset_registry import PresetRegistry
from config.rule_interactions import is_attack_repetition_synergy_compatible
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

        display_names = list(match_config.player_display_names or [])
        if display_names and len(display_names) != player_count:
            raise InvalidStateError(
                "player_display_names must match the number of configured players."
            )

        if len(set(match_config.player_ids)) != player_count:
            raise InvalidStateError("Configured player ids must be unique.")

        if len(match_config.player_profile_ids) not in {0, player_count}:
            raise InvalidStateError(
                "player_profile_ids must be empty or aligned with configured players."
            )

        if not structure_name:
            raise InvalidStateError("A structure name is required.")

        if structure_name not in {"one_vs_one", "battle"}:
            raise InvalidStateError(f"Unknown structure: {structure_name}")

        if structure_name == "one_vs_one" and player_count != 2:
            raise InvalidStateError("One vs one structure requires exactly two players.")

        if structure_name == "battle" and player_count < 3:
            raise InvalidStateError("Battle structure requires at least three players.")

        self._validate_runtime_config(match_config)
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

    def _validate_runtime_config(self, match_config: MatchConfig) -> None:
        if not match_config.scoring.letters_word:
            raise ValueError("letters_word cannot be empty")

        if len(match_config.scoring.letters_word) > 10:
            raise ValueError("letters_word cannot exceed 10 characters")

        if match_config.attack.attack_attempts < 1:
            raise ValueError("attack_attempts must be greater than or equal to 1")

        if not (1 <= match_config.defense.defense_attempts <= 3):
            raise ValueError("defense_attempts must be between 1 and 3")

        if (
            match_config.sport != "inline"
            and match_config.fine_rules.switch_mode != "disabled"
        ):
            raise InvalidStateError(
                "Switch is only supported for inline sport in the current version."
            )

        if not is_attack_repetition_synergy_compatible(
            match_config.attack.attack_attempts,
            match_config.fine_rules.repetition_mode,
            match_config.fine_rules.repetition_limit,
            multiple_attack_enabled=match_config.fine_rules.multiple_attack_enabled,
            no_repetition=match_config.fine_rules.no_repetition,
        ):
            raise InvalidStateError(
                "When Attack is greater than 1 and Repetition is active, "
                "repetition_limit must be a multiple of attack_attempts."
            )

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

        if structure_name == "one_vs_one" and (
            policies.defender_order != DefenderOrderPolicy.FOLLOW_TURN_ORDER
        ):
            raise InvalidStateError(
                "One vs one structure requires defenders to follow turn order."
            )

        if policies.initial_turn_order == InitialTurnOrderPolicy.RELEVANCE:
            if policies.relevance_criterion is None:
                raise InvalidStateError(
                    "Relevance order requires a relevance criterion."
                )
        elif policies.relevance_criterion is not None and not isinstance(
            policies.relevance_criterion,
            RelevanceCriterion,
        ):
            raise InvalidStateError("Unknown relevance criterion configured.")

        if policies.initial_turn_order in {
            InitialTurnOrderPolicy.EXPLICIT_CHOICE,
            InitialTurnOrderPolicy.RELEVANCE,
        }:
            expected_player_ids = set(match_config.player_ids)
            explicit_player_order = tuple(policies.explicit_player_order)
            if len(explicit_player_order) != len(match_config.player_ids):
                raise InvalidStateError(
                    "Explicit order must include every configured player exactly once."
                )
            if set(explicit_player_order) != expected_player_ids:
                raise InvalidStateError(
                    "Explicit order must match the configured player ids."
                )
        elif policies.explicit_player_order:
            raise InvalidStateError(
                "Explicit order may only be configured for choice or relevance."
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

        if match_config.scoring.letters_word != preset.rule_set.letters_word:
            raise InvalidStateError(
                "preset_name does not match the configured rule set."
            )

        if match_config.attack.attack_attempts != preset.rule_set.attack_attempts:
            raise InvalidStateError(
                "preset_name does not match the configured rule set."
            )

        if match_config.defense.defense_attempts != preset.rule_set.defense_attempts:
            raise InvalidStateError(
                "preset_name does not match the configured rule set."
            )

        if match_config.victory.elimination_enabled != preset.rule_set.elimination_enabled:
            raise InvalidStateError(
                "preset_name does not match the configured rule set."
            )

        if match_config.fine_rules != preset.fine_rules:
            raise InvalidStateError(
                "preset_name does not match the configured fine rules."
            )
