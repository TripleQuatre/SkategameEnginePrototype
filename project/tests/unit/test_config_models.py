from config.match_parameters import MatchParameters
from config.match_policies import (
    AttackerRotationPolicy,
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
    MatchPolicies,
)
from config.preset_registry import PresetRegistry


def test_match_parameters_include_v6_configuration_fields() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])

    assert match_parameters.mode_name == "one_vs_one"
    assert match_parameters.structure_name == "one_vs_one"
    assert match_parameters.policies.initial_turn_order == (
        InitialTurnOrderPolicy.FIXED_PLAYER_ORDER
    )
    assert match_parameters.policies.attacker_rotation == (
        AttackerRotationPolicy.FOLLOW_TURN_ORDER
    )
    assert match_parameters.policies.defender_order == (
        DefenderOrderPolicy.FOLLOW_TURN_ORDER
    )
    assert match_parameters.preset_name is None


def test_match_parameters_structure_name_alias_tracks_mode_name() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"])

    match_parameters.structure_name = "battle"

    assert match_parameters.mode_name == "battle"
    assert match_parameters.structure_name == "battle"


def test_match_parameters_accept_structure_name_as_primary_constructor_field() -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
    )

    assert match_parameters.structure_name == "battle"
    assert match_parameters.mode_name == "battle"


def test_battle_match_parameters_keep_v5_randomized_default_policy() -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        mode_name="battle",
    )

    assert match_parameters.policies.initial_turn_order == (
        InitialTurnOrderPolicy.RANDOMIZED
    )


def test_match_policies_can_be_customized_independently() -> None:
    policies = MatchPolicies(
        initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
        defender_order=DefenderOrderPolicy.REVERSE_TURN_ORDER,
    )

    assert policies.initial_turn_order == InitialTurnOrderPolicy.RANDOMIZED
    assert policies.attacker_rotation == AttackerRotationPolicy.FOLLOW_TURN_ORDER
    assert policies.defender_order == DefenderOrderPolicy.REVERSE_TURN_ORDER


def test_preset_registry_exposes_official_v6_presets() -> None:
    registry = PresetRegistry()

    assert registry.has("classic_skate") is True
    assert registry.has("classic_blade") is True
    assert registry.has("battle_standard") is True
    assert registry.has("battle_hardcore") is True


def test_preset_registry_returns_expected_preset_configuration() -> None:
    registry = PresetRegistry()

    preset = registry.get("battle_hardcore")

    assert preset.structure_name == "battle"
    assert preset.mode_name == "battle"
    assert preset.rule_set.letters_word == "SKATE"
    assert preset.rule_set.attack_attempts == 1
    assert preset.rule_set.defense_attempts == 1
    assert preset.rule_set.elimination_enabled is True
    assert preset.policies.initial_turn_order == InitialTurnOrderPolicy.RANDOMIZED
