from dataclasses import dataclass, field

from config.match_policies import MatchPolicies
from config.rule_set_config import RuleSetConfig
from config.setup_defaults import build_default_policies_for_structure


@dataclass(init=False)
class MatchParameters:
    player_ids: list[str]
    structure_name: str
    rule_set: RuleSetConfig = field(default_factory=RuleSetConfig)
    policies: MatchPolicies | None = None
    preset_name: str | None = None

    def __init__(
        self,
        player_ids: list[str],
        structure_name: str = "one_vs_one",
        rule_set: RuleSetConfig | None = None,
        policies: MatchPolicies | None = None,
        preset_name: str | None = None,
        mode_name: str | None = None,
    ) -> None:
        self.player_ids = player_ids
        self.structure_name = mode_name if mode_name is not None else structure_name
        self.rule_set = rule_set if rule_set is not None else RuleSetConfig()
        self.policies = policies
        self.preset_name = preset_name

        if self.policies is None:
            self.policies = self._build_default_policies_for_structure(
                self.structure_name
            )

    @property
    def mode_name(self) -> str:
        return self.structure_name

    @mode_name.setter
    def mode_name(self, value: str) -> None:
        self.structure_name = value

    @staticmethod
    def _build_default_policies_for_structure(structure_name: str) -> MatchPolicies:
        return build_default_policies_for_structure(structure_name)

    @staticmethod
    def _build_default_policies_for_mode(mode_name: str) -> MatchPolicies:
        return MatchParameters._build_default_policies_for_structure(mode_name)
