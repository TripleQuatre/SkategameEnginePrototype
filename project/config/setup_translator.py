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
        setup = MatchSetup(
            player_ids=list(match_parameters.player_ids),
            structure_name=match_parameters.structure_name,
            policies=match_parameters.policies,
            letters_word=match_parameters.rule_set.letters_word,
            attack_attempts=match_parameters.rule_set.attack_attempts,
            defense_attempts=match_parameters.rule_set.defense_attempts,
            elimination_enabled=match_parameters.rule_set.elimination_enabled,
            preset_name=match_parameters.preset_name,
        )
        return self.to_match_config(setup)
