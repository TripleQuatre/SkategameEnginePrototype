from config.match_policies import InitialTurnOrderPolicy, MatchPolicies
from config.match_preset import MatchPreset
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

    def _build_official_presets(self) -> list[MatchPreset]:
        return [
            MatchPreset(
                name="classic_skate",
                mode_name="one_vs_one",
                rule_set=RuleSetConfig(
                    letters_word="SKATE",
                    elimination_enabled=True,
                    defense_attempts=3,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.FIXED_PLAYER_ORDER,
                ),
                description="Classic one-versus-one skate setup.",
            ),
            MatchPreset(
                name="classic_blade",
                mode_name="one_vs_one",
                rule_set=RuleSetConfig(
                    letters_word="BLADE",
                    elimination_enabled=True,
                    defense_attempts=1,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.FIXED_PLAYER_ORDER,
                ),
                description="Classic one-versus-one blade setup.",
            ),
            MatchPreset(
                name="battle_standard",
                mode_name="battle",
                rule_set=RuleSetConfig(
                    letters_word="OUT",
                    elimination_enabled=True,
                    defense_attempts=3,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
                ),
                description="Standard multiplayer battle setup.",
            ),
            MatchPreset(
                name="battle_hardcore",
                mode_name="battle",
                rule_set=RuleSetConfig(
                    letters_word="SKATE",
                    elimination_enabled=True,
                    defense_attempts=1,
                ),
                policies=MatchPolicies(
                    initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
                ),
                description="Hardcore multiplayer battle setup.",
            ),
        ]
