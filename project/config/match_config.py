from dataclasses import dataclass, field, replace

from config.attack_config import AttackConfig
from config.defense_config import DefenseConfig
from config.match_policies import MatchPolicies
from config.rule_set_config import RuleSetConfig
from config.scoring_config import ScoringConfig
from config.structure_config import StructureConfig
from config.victory_config import VictoryConfig


@dataclass(frozen=True)
class MatchConfig:
    player_ids: list[str] = field(default_factory=list)
    structure: StructureConfig = field(default_factory=StructureConfig)
    attack: AttackConfig = field(default_factory=AttackConfig)
    defense: DefenseConfig = field(default_factory=DefenseConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    victory: VictoryConfig = field(default_factory=VictoryConfig)
    preset_name: str | None = None

    @property
    def structure_name(self) -> str:
        return self.structure.structure_name

    @property
    def policies(self) -> MatchPolicies:
        return self.structure.policies

    @property
    def letters_word(self) -> str:
        return self.scoring.letters_word

    @property
    def attack_attempts(self) -> int:
        return self.attack.attack_attempts

    @property
    def defense_attempts(self) -> int:
        return self.defense.defense_attempts

    @property
    def elimination_enabled(self) -> bool:
        return self.victory.elimination_enabled

    @property
    def rule_set(self) -> RuleSetConfig:
        return self.to_rule_set_config()

    def to_rule_set_config(self) -> RuleSetConfig:
        return RuleSetConfig(
            letters_word=self.scoring.letters_word,
            elimination_enabled=self.victory.elimination_enabled,
            attack_attempts=self.attack.attack_attempts,
            defense_attempts=self.defense.defense_attempts,
        )

    def with_rule_set(self, rule_set: RuleSetConfig) -> "MatchConfig":
        return replace(
            self,
            attack=AttackConfig(attack_attempts=rule_set.attack_attempts),
            defense=DefenseConfig(defense_attempts=rule_set.defense_attempts),
            scoring=replace(self.scoring, letters_word=rule_set.letters_word),
            victory=replace(
                self.victory,
                elimination_enabled=rule_set.elimination_enabled,
            ),
        )
