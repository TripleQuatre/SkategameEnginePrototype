from dataclasses import dataclass, field
from config.rule_set_config import RuleSetConfig


@dataclass
class MatchParameters:
    player_ids: list[str]
    mode_name: str = "one_vs_one"
    rule_set: RuleSetConfig = field(default_factory=RuleSetConfig)