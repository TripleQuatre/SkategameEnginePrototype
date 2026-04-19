from config.match_policies import MatchPolicies
from match.structure.base_structure import BaseStructure
from match.structure.battle_structure import BattleStructure
from match.structure.one_vs_one_structure import OneVsOneStructure


class StructureFactory:
    def create(
        self, structure_name: str, policies: MatchPolicies | None = None
    ) -> BaseStructure:
        if structure_name == "one_vs_one":
            return OneVsOneStructure(policies)

        if structure_name == "battle":
            return BattleStructure(policies)

        raise ValueError(f"Unknown structure: {structure_name}")
