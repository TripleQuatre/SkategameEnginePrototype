from dataclasses import dataclass, field

from config.attack_config import AttackConfig
from config.defense_config import DefenseConfig
from config.match_config import MatchConfig
from config.match_policies import MatchPolicies
from config.rule_set_config import RuleSetConfig
from config.scoring_config import ScoringConfig
from config.setup_defaults import build_default_policies_for_structure
from config.structure_config import StructureConfig
from config.victory_config import VictoryConfig


@dataclass(init=False)
class MatchParameters:
    player_ids: list[str]
    structure_name: str
    rule_set: RuleSetConfig = field(default_factory=RuleSetConfig)
    policies: MatchPolicies | None = None
    preset_name: str | None = None

    def __init__(
        self,
        player_ids: list[str],
        structure_name: str = "one_vs_one",
        rule_set: RuleSetConfig | None = None,
        policies: MatchPolicies | None = None,
        preset_name: str | None = None,
    ) -> None:
        self.player_ids = player_ids
        self.structure_name = structure_name
        self.rule_set = rule_set if rule_set is not None else RuleSetConfig()
        self.policies = policies
        self.preset_name = preset_name

        if self.policies is None:
            self.policies = self._build_default_policies_for_structure(
                self.structure_name
            )

    @staticmethod
    def _build_default_policies_for_structure(structure_name: str) -> MatchPolicies:
        return build_default_policies_for_structure(structure_name)

    def to_match_config(self) -> MatchConfig:
        return MatchConfig(
            player_ids=list(self.player_ids),
            structure=StructureConfig(
                structure_name=self.structure_name,
                policies=self.policies,
            ),
            attack=AttackConfig(
                attack_attempts=self.rule_set.attack_attempts,
            ),
            defense=DefenseConfig(
                defense_attempts=self.rule_set.defense_attempts,
            ),
            scoring=ScoringConfig(
                scoring_type="letters",
                letters_word=self.rule_set.letters_word,
            ),
            victory=VictoryConfig(
                victory_type="last_player_standing",
                elimination_enabled=self.rule_set.elimination_enabled,
            ),
            preset_name=self.preset_name,
        )
