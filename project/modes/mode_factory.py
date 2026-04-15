from config.match_policies import MatchPolicies
from modes.base_mode import BaseMode
from modes.battle import BattleMode
from modes.one_vs_one import OneVsOneMode


class ModeFactory:
    def create(self, mode_name: str, policies: MatchPolicies | None = None) -> BaseMode:
        if mode_name == "one_vs_one":
            return OneVsOneMode(policies)

        if mode_name == "battle":
            return BattleMode(policies)

        raise ValueError(f"Unknown mode: {mode_name}")
