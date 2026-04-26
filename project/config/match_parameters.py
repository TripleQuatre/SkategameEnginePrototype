from dataclasses import dataclass, field

from config.attack_config import AttackConfig
from config.defense_config import DefenseConfig
from config.fine_rules_config import FineRulesConfig
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
    player_profile_ids: list[str] = field(default_factory=list)
    structure_name: str
    sport: str = "inline"
    rule_set: RuleSetConfig = field(default_factory=RuleSetConfig)
    policies: MatchPolicies | None = None
    fine_rules: FineRulesConfig = field(default_factory=FineRulesConfig)
    preset_name: str | None = None

    def __init__(
        self,
        player_ids: list[str],
        player_profile_ids: list[str] | None = None,
        structure_name: str = "one_vs_one",
        sport: str = "inline",
        rule_set: RuleSetConfig | None = None,
        policies: MatchPolicies | None = None,
        fine_rules: FineRulesConfig | None = None,
        preset_name: str | None = None,
    ) -> None:
        self.player_ids = list(player_ids)
        self.player_profile_ids = list(player_profile_ids or [])
        self.structure_name = structure_name
        self.sport = sport
        self.rule_set = rule_set if rule_set is not None else RuleSetConfig()
        self.policies = policies
        self.fine_rules = fine_rules if fine_rules is not None else FineRulesConfig()
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
            player_profile_ids=list(self.player_profile_ids),
            structure=StructureConfig(
                structure_name=self.structure_name,
                policies=self.policies,
            ),
            sport=self.sport,
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
            fine_rules=self.fine_rules,
            preset_name=self.preset_name,
        )
