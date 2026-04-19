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
    preset_name: str | None = None

    @property
    def structure_name(self) -> str:
        return self.structure.structure_name
