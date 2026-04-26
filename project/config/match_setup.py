from dataclasses import dataclass

from config.match_policies import MatchPolicies
from config.setup_defaults import build_default_policies_for_structure


@dataclass(init=False)
class MatchSetup:
    player_ids: list[str]
    player_profile_ids: list[str | None]
    player_display_names: list[str]
    structure_name: str
    sport: str = "inline"
    policies: MatchPolicies | None = None
    letters_word: str = "SKATE"
    attack_attempts: int = 1
    defense_attempts: int = 1
    elimination_enabled: bool = True
    uniqueness_enabled: bool = True
    multiple_attack_enabled: bool = False
    no_repetition: bool = False
    switch_mode: str = "disabled"
    repetition_mode: str = "choice"
    repetition_limit: int = 3
    preset_name: str | None = None

    def __init__(
        self,
        player_ids: list[str],
        player_profile_ids: list[str | None] | None = None,
        player_display_names: list[str] | None = None,
        structure_name: str = "one_vs_one",
        sport: str = "inline",
        policies: MatchPolicies | None = None,
        letters_word: str = "SKATE",
        attack_attempts: int = 1,
        defense_attempts: int = 1,
        elimination_enabled: bool = True,
        uniqueness_enabled: bool = True,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
        switch_mode: str = "disabled",
        repetition_mode: str = "choice",
        repetition_limit: int = 3,
        preset_name: str | None = None,
    ) -> None:
        self.player_ids = list(player_ids)
        self.player_profile_ids = list(player_profile_ids or [])
        self.player_display_names = list(player_display_names or player_ids)
        self.structure_name = structure_name
        self.sport = sport
        self.policies = policies
        self.letters_word = letters_word
        self.attack_attempts = attack_attempts
        self.defense_attempts = defense_attempts
        self.elimination_enabled = elimination_enabled
        self.uniqueness_enabled = uniqueness_enabled
        self.multiple_attack_enabled = multiple_attack_enabled
        self.no_repetition = no_repetition
        self.switch_mode = switch_mode
        self.repetition_mode = repetition_mode
        self.repetition_limit = repetition_limit
        self.preset_name = preset_name

        if self.policies is None:
            self.policies = build_default_policies_for_structure(self.structure_name)
