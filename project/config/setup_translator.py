from config.attack_config import AttackConfig
from config.defense_config import DefenseConfig
from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.match_setup import MatchSetup
from config.scoring_config import ScoringConfig
from config.structure_config import StructureConfig
from config.victory_config import VictoryConfig


class SetupTranslator:
    def to_match_parameters(self, setup: MatchSetup) -> MatchParameters:
        return MatchParameters(
            player_ids=list(setup.player_ids),
            structure_name=setup.structure_name,
            policies=setup.policies,
            rule_set=setup.to_rule_set_config(),
            preset_name=setup.preset_name,
        )

    def to_match_config(self, setup: MatchSetup) -> MatchConfig:
        return MatchConfig(
            player_ids=list(setup.player_ids),
            structure=StructureConfig(
                structure_name=setup.structure_name,
                policies=setup.policies,
            ),
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
            preset_name=setup.preset_name,
        )

    def from_match_parameters(self, match_parameters: MatchParameters) -> MatchConfig:
        return match_parameters.to_match_config()

    def from_match_config(self, match_config: MatchConfig) -> MatchParameters:
        return MatchParameters(
            player_ids=list(match_config.player_ids),
            structure_name=match_config.structure_name,
            policies=match_config.policies,
            rule_set=match_config.to_rule_set_config(),
            preset_name=match_config.preset_name,
        )
