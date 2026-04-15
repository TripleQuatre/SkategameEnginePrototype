from dataclasses import dataclass, field

from config.match_policies import MatchPolicies
from config.rule_set_config import RuleSetConfig


@dataclass(frozen=True)
class MatchPreset:
    name: str
    mode_name: str
    policies: MatchPolicies = field(default_factory=MatchPolicies)
    rule_set: RuleSetConfig = field(default_factory=RuleSetConfig)
    description: str = ""
