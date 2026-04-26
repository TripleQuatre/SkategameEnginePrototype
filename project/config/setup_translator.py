from config.attack_config import AttackConfig
from config.defense_config import DefenseConfig
from config.fine_rules_config import FineRulesConfig
from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.match_setup import MatchSetup
from config.rule_set_config import RuleSetConfig
from config.scoring_config import ScoringConfig
from config.structure_config import StructureConfig
from config.victory_config import VictoryConfig


class SetupTranslator:
    def to_match_parameters(self, setup: MatchSetup) -> MatchParameters:
        return MatchParameters(
            player_ids=list(setup.player_ids),
            player_profile_ids=list(setup.player_profile_ids),
            player_display_names=list(setup.player_display_names),
            structure_name=setup.structure_name,
            sport=setup.sport,
            policies=setup.policies,
            rule_set=RuleSetConfig(
                letters_word=setup.letters_word,
                elimination_enabled=setup.elimination_enabled,
                attack_attempts=setup.attack_attempts,
                defense_attempts=setup.defense_attempts,
            ),
            fine_rules=FineRulesConfig(
                uniqueness_enabled=setup.uniqueness_enabled,
                multiple_attack_enabled=setup.multiple_attack_enabled,
                no_repetition=setup.no_repetition,
                switch_mode=setup.switch_mode,
                repetition_mode=setup.repetition_mode,
                repetition_limit=setup.repetition_limit,
            ),
            preset_name=setup.preset_name,
        )

    def to_match_config(self, setup: MatchSetup) -> MatchConfig:
        return MatchConfig(
            player_ids=list(setup.player_ids),
            player_profile_ids=list(setup.player_profile_ids),
            player_display_names=list(setup.player_display_names),
            structure=StructureConfig(
                structure_name=setup.structure_name,
                policies=setup.policies,
            ),
            sport=setup.sport,
            attack=AttackConfig(
                attack_attempts=setup.attack_attempts,
            ),
            defense=DefenseConfig(
                defense_attempts=setup.defense_attempts,
            ),
            scoring=ScoringConfig(
                scoring_type="letters",
                letters_word=setup.letters_word,
            ),
            victory=VictoryConfig(
                victory_type="last_player_standing",
                elimination_enabled=setup.elimination_enabled,
            ),
            fine_rules=FineRulesConfig(
                uniqueness_enabled=setup.uniqueness_enabled,
                multiple_attack_enabled=setup.multiple_attack_enabled,
                no_repetition=setup.no_repetition,
                switch_mode=setup.switch_mode,
                repetition_mode=setup.repetition_mode,
                repetition_limit=setup.repetition_limit,
            ),
            preset_name=setup.preset_name,
        )

    def from_match_parameters(self, match_parameters: MatchParameters) -> MatchConfig:
        return match_parameters.to_match_config()

    def from_match_config(self, match_config: MatchConfig) -> MatchParameters:
        return MatchParameters(
            player_ids=list(match_config.player_ids),
            player_profile_ids=list(match_config.player_profile_ids),
            player_display_names=list(match_config.player_display_names),
            structure_name=match_config.structure_name,
            sport=match_config.sport,
            policies=match_config.policies,
            rule_set=RuleSetConfig(
                letters_word=match_config.scoring.letters_word,
                elimination_enabled=match_config.victory.elimination_enabled,
                attack_attempts=match_config.attack.attack_attempts,
                defense_attempts=match_config.defense.defense_attempts,
            ),
            fine_rules=match_config.fine_rules,
            preset_name=match_config.preset_name,
        )
