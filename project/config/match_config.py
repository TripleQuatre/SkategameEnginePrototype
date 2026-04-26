from dataclasses import dataclass, field

from config.attack_config import AttackConfig
from config.defense_config import DefenseConfig
from config.fine_rules_config import FineRulesConfig
from config.match_policies import MatchPolicies
from config.scoring_config import ScoringConfig
from config.structure_config import StructureConfig
from config.victory_config import VictoryConfig


@dataclass(frozen=True)
class MatchConfig:
    player_ids: list[str] = field(default_factory=list)
    player_profile_ids: list[str | None] = field(default_factory=list)
    player_display_names: list[str] = field(default_factory=list)
    structure: StructureConfig = field(default_factory=StructureConfig)
    sport: str = "inline"
    attack: AttackConfig = field(default_factory=AttackConfig)
    defense: DefenseConfig = field(default_factory=DefenseConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    victory: VictoryConfig = field(default_factory=VictoryConfig)
    fine_rules: FineRulesConfig = field(default_factory=FineRulesConfig)
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
    def uniqueness_enabled(self) -> bool:
        return self.fine_rules.uniqueness_enabled

    @property
    def repetition_mode(self) -> str:
        return self.fine_rules.repetition_mode

    @property
    def repetition_limit(self) -> int:
        return self.fine_rules.repetition_limit
