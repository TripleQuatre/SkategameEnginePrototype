from dataclasses import dataclass, field

from config.match_config import MatchConfig
from config.match_policies import MatchPolicies
from config.match_parameters import MatchParameters
from config.match_setup import MatchSetup
from config.rule_set_config import RuleSetConfig
from config.setup_translator import SetupTranslator


@dataclass(frozen=True)
class MatchPreset:
    name: str
    structure_name: str
    policies: MatchPolicies = field(default_factory=MatchPolicies)
    rule_set: RuleSetConfig = field(default_factory=RuleSetConfig)
    description: str = ""

    def create_match_setup(self, player_ids: list[str]) -> MatchSetup:
        return MatchSetup(
            player_ids=list(player_ids),
            structure_name=self.structure_name,
            policies=self.policies,
            letters_word=self.rule_set.letters_word,
            attack_attempts=self.rule_set.attack_attempts,
            defense_attempts=self.rule_set.defense_attempts,
            elimination_enabled=self.rule_set.elimination_enabled,
            preset_name=self.name,
        )

    def create_match_config(self, player_ids: list[str]) -> MatchConfig:
        translator = SetupTranslator()
        return translator.to_match_config(self.create_match_setup(player_ids))

    def create_match_parameters(self, player_ids: list[str]) -> MatchParameters:
        translator = SetupTranslator()
        return translator.to_match_parameters(self.create_match_setup(player_ids))
