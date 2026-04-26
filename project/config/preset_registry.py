from config.match_config import MatchConfig
from config.fine_rules_config import FineRulesConfig
from config.match_policies import InitialTurnOrderPolicy, MatchPolicies
from config.match_parameters import MatchParameters
from config.match_preset import MatchPreset
from config.match_setup import MatchSetup
from config.rule_set_config import RuleSetConfig


class PresetRegistry:
    def __init__(self) -> None:
        self._presets = {
            preset.name: preset for preset in self._build_official_presets()
        }

    def get(self, preset_name: str) -> MatchPreset:
        preset = self._presets.get(preset_name)
        if preset is None:
            raise ValueError(f"Unknown preset: {preset_name}")
        return preset

    def has(self, preset_name: str) -> bool:
        return preset_name in self._presets

    def list_presets(self) -> list[MatchPreset]:
        return list(self._presets.values())

    def list_preset_names(self) -> list[str]:
        return list(self._presets.keys())

    def create_match_setup(
        self, preset_name: str, player_ids: list[str]
    ) -> MatchSetup:
        return self.get(preset_name).create_match_setup(player_ids)

    def create_match_config(
        self, preset_name: str, player_ids: list[str]
    ) -> MatchConfig:
        return self.get(preset_name).create_match_config(player_ids)

    def create_match_parameters(
        self, preset_name: str, player_ids: list[str]
    ) -> MatchParameters:
        return self.get(preset_name).create_match_parameters(player_ids)

    def _build_official_presets(self) -> list[MatchPreset]:
        return [
            MatchPreset(
                name="classic_skate",
                structure_name="one_vs_one",
                rule_set=RuleSetConfig(
                    letters_word="SKATE",
                    elimination_enabled=True,
                    attack_attempts=1,
                    defense_attempts=3,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.FIXED_PLAYER_ORDER,
                ),
                description="Classic one-versus-one skate setup.",
            ),
            MatchPreset(
                name="classic_blade",
                structure_name="one_vs_one",
                rule_set=RuleSetConfig(
                    letters_word="BLADE",
                    elimination_enabled=True,
                    attack_attempts=1,
                    defense_attempts=1,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.FIXED_PLAYER_ORDER,
                ),
                description="Classic one-versus-one blade setup.",
            ),
            MatchPreset(
                name="battle_standard",
                structure_name="battle",
                rule_set=RuleSetConfig(
                    letters_word="OUT",
                    elimination_enabled=True,
                    attack_attempts=1,
                    defense_attempts=3,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
                ),
                description="Standard multiplayer battle setup.",
            ),
            MatchPreset(
                name="battle_hardcore",
                structure_name="battle",
                rule_set=RuleSetConfig(
                    letters_word="SKATE",
                    elimination_enabled=True,
                    attack_attempts=1,
                    defense_attempts=1,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
                ),
                description="Hardcore multiplayer battle setup.",
            ),
            MatchPreset(
                name="classic_skate_v8",
                structure_name="one_vs_one",
                rule_set=RuleSetConfig(
                    letters_word="SKATE",
                    elimination_enabled=True,
                    attack_attempts=2,
                    defense_attempts=3,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.FIXED_PLAYER_ORDER,
                ),
                fine_rules=FineRulesConfig(
                    uniqueness_enabled=True,
                    repetition_mode="choice",
                    repetition_limit=4,
                ),
                description="V8 duel preset with assisted tricks, uniqueness and per-attacker repetition.",
            ),
            MatchPreset(
                name="blade_open_v8",
                structure_name="one_vs_one",
                rule_set=RuleSetConfig(
                    letters_word="BLADE",
                    elimination_enabled=True,
                    attack_attempts=2,
                    defense_attempts=1,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.FIXED_PLAYER_ORDER,
                ),
                fine_rules=FineRulesConfig(
                    uniqueness_enabled=False,
                    repetition_mode="disabled",
                    repetition_limit=3,
                ),
                description="V8 duel preset with free trick reuse and no repetition cap.",
            ),
            MatchPreset(
                name="battle_common_v8",
                structure_name="battle",
                rule_set=RuleSetConfig(
                    letters_word="OUT",
                    elimination_enabled=True,
                    attack_attempts=2,
                    defense_attempts=3,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
                ),
                fine_rules=FineRulesConfig(
                    uniqueness_enabled=True,
                    repetition_mode="common",
                    repetition_limit=4,
                ),
                description="V8 battle preset with shared repetition limit across attackers.",
            ),
            MatchPreset(
                name="battle_hardcore_v8",
                structure_name="battle",
                rule_set=RuleSetConfig(
                    letters_word="SKATE",
                    elimination_enabled=True,
                    attack_attempts=2,
                    defense_attempts=1,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
                ),
                fine_rules=FineRulesConfig(
                    uniqueness_enabled=True,
                    repetition_mode="common",
                    repetition_limit=2,
                ),
                description="V8 hardcore battle preset with strict shared repetition.",
            ),
            MatchPreset(
                name="duel_short_strict_v9_3",
                structure_name="one_vs_one",
                rule_set=RuleSetConfig(
                    letters_word="S",
                    elimination_enabled=True,
                    attack_attempts=3,
                    defense_attempts=1,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.FIXED_PLAYER_ORDER,
                ),
                fine_rules=FineRulesConfig(
                    uniqueness_enabled=True,
                    repetition_mode="choice",
                    repetition_limit=3,
                ),
                description="V9.3 reference duel preset with the shortest word and the strictest per-attacker repetition.",
            ),
            MatchPreset(
                name="duel_long_open_v9_3",
                structure_name="one_vs_one",
                rule_set=RuleSetConfig(
                    letters_word="SKATEBOARD",
                    elimination_enabled=True,
                    attack_attempts=3,
                    defense_attempts=3,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.FIXED_PLAYER_ORDER,
                ),
                fine_rules=FineRulesConfig(
                    uniqueness_enabled=False,
                    repetition_mode="disabled",
                    repetition_limit=3,
                ),
                description="V9.3 reference duel preset with a long word and fully open trick reuse.",
            ),
            MatchPreset(
                name="battle_balanced_v9_3",
                structure_name="battle",
                rule_set=RuleSetConfig(
                    letters_word="OUT",
                    elimination_enabled=True,
                    attack_attempts=3,
                    defense_attempts=2,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
                ),
                fine_rules=FineRulesConfig(
                    uniqueness_enabled=True,
                    repetition_mode="common",
                    repetition_limit=3,
                ),
                description="V9.3 reference battle preset with mid defense pressure and shared repetition.",
            ),
            MatchPreset(
                name="battle_long_open_v9_3",
                structure_name="battle",
                rule_set=RuleSetConfig(
                    letters_word="SKATEBOARD",
                    elimination_enabled=True,
                    attack_attempts=2,
                    defense_attempts=2,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
                ),
                fine_rules=FineRulesConfig(
                    uniqueness_enabled=False,
                    repetition_mode="disabled",
                    repetition_limit=3,
                ),
                description="V9.3 reference battle preset with a long word and open fine-rule constraints.",
            ),
        ]
