from dataclasses import dataclass, field

from config.attack_config import AttackConfig
from config.defense_config import DefenseConfig
from config.scoring_config import ScoringConfig
from config.structure_config import StructureConfig
from config.victory_config import VictoryConfig


@dataclass(frozen=True)
class MatchConfig:
    structure: StructureConfig = field(default_factory=StructureConfig)
    attack: AttackConfig = field(default_factory=AttackConfig)
    defense: DefenseConfig = field(default_factory=DefenseConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    victory: VictoryConfig = field(default_factory=VictoryConfig)
    legacy_mode_name: str | None = None
    preset_name: str | None = None

    @property
    def structure_name(self) -> str:
        if self.structure.structure_name:
            return self.structure.structure_name
        if self.legacy_mode_name is not None:
            return self.legacy_mode_name
        return ""

    @property
    def mode_name(self) -> str | None:
        return self.legacy_mode_name or self.structure_name
