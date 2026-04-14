from modes.base_mode import BaseMode
from modes.battle import BattleMode
from modes.one_vs_one import OneVsOneMode


class ModeFactory:
    def create(self, mode_name: str) -> BaseMode:
        if mode_name == "one_vs_one":
            return OneVsOneMode()

        if mode_name == "battle":
            return BattleMode()

        raise ValueError(f"Unknown mode: {mode_name}")
