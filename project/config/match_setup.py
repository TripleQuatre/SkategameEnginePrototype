from dataclasses import dataclass

from config.match_policies import MatchPolicies
from config.rule_set_config import RuleSetConfig
from config.setup_defaults import build_default_policies_for_structure


@dataclass(init=False)
class MatchSetup:
    player_ids: list[str]
    structure_name: str
    policies: MatchPolicies | None = None
    letters_word: str = "SKATE"
    attack_attempts: int = 1
    defense_attempts: int = 1
    elimination_enabled: bool = True
    preset_name: str | None = None

    def __init__(
        self,
        player_ids: list[str],
        structure_name: str = "one_vs_one",
        policies: MatchPolicies | None = None,
        letters_word: str = "SKATE",
        attack_attempts: int = 1,
        defense_attempts: int = 1,
        elimination_enabled: bool = True,
        preset_name: str | None = None,
    ) -> None:
        self.player_ids = player_ids
        self.structure_name = structure_name
        self.policies = policies
        self.letters_word = letters_word
        self.attack_attempts = attack_attempts
        self.defense_attempts = defense_attempts
        self.elimination_enabled = elimination_enabled
        self.preset_name = preset_name

        if self.policies is None:
            self.policies = build_default_policies_for_structure(self.structure_name)

    def to_rule_set_config(self) -> RuleSetConfig:
        return RuleSetConfig(
            letters_word=self.letters_word,
            elimination_enabled=self.elimination_enabled,
            attack_attempts=self.attack_attempts,
            defense_attempts=self.defense_attempts,
        )
