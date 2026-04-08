from rules.scoring_rules import ScoringRules
from rules.special_rules import SpecialRules


class RulesRegistry:
    def __init__(self) -> None:
        self.scoring = ScoringRules()
        self.special = SpecialRules()