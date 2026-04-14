from dataclasses import dataclass, field
from typing import Optional

from core.player import Player
from core.types import Phase
from core.history import History
from config.rule_set_config import RuleSetConfig

@dataclass
class GameState:
    players: list[Player]
    phase: Phase = Phase.SETUP
    turn_order: list[int] = field(default_factory=list)
    attacker_index: int = 0
    defender_indices: list[int] = field(default_factory=list)
    current_defender_position: int = 0
    defense_attempts_left: int = 0
    current_trick: Optional[str] = None
    history: History = field(default_factory=History)
    rule_set: RuleSetConfig = field(default_factory=RuleSetConfig)
    validated_tricks: list[str] = field(default_factory=list)
