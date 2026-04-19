from dataclasses import dataclass, field

from config.match_policies import MatchPolicies


@dataclass(frozen=True)
class StructureConfig:
    structure_name: str = "one_vs_one"
    policies: MatchPolicies = field(default_factory=MatchPolicies)
