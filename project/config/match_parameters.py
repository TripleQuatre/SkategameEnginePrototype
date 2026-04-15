from dataclasses import dataclass, field

from config.match_policies import InitialTurnOrderPolicy, MatchPolicies
from config.rule_set_config import RuleSetConfig


@dataclass
class MatchParameters:
    player_ids: list[str]
    mode_name: str = "one_vs_one"
    rule_set: RuleSetConfig = field(default_factory=RuleSetConfig)
    policies: MatchPolicies | None = None
    preset_name: str | None = None

    def __post_init__(self) -> None:
        if self.policies is None:
            self.policies = self._build_default_policies_for_mode(self.mode_name)

    @staticmethod
    def _build_default_policies_for_mode(mode_name: str) -> MatchPolicies:
        if mode_name == "battle":
            return MatchPolicies(
                initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
            )

        return MatchPolicies()
