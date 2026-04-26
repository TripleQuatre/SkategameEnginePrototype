from config.match_parameters import MatchParameters
from config.match_policies import InitialTurnOrderPolicy
from config.match_config import MatchConfig
from config.match_setup import MatchSetup
from config.preset_registry import PresetRegistry
from config.structure_config import StructureConfig
from config.setup_translator import SetupTranslator


def test_match_setup_uses_battle_default_policies() -> None:
    setup = MatchSetup(player_ids=["p1", "p2", "p3"], structure_name="battle")

    assert setup.policies.initial_turn_order == InitialTurnOrderPolicy.RANDOMIZED
    assert setup.structure_name == "battle"


def test_setup_translator_builds_v7_match_config() -> None:
    setup = MatchSetup(
        player_ids=["p1", "p2"],
        player_profile_ids=["stan", "denise"],
        player_display_names=["Stan", "Denise"],
        structure_name="one_vs_one",
        sport="inline",
        letters_word="SKATE",
        attack_attempts=2,
        defense_attempts=3,
        elimination_enabled=True,
        preset_name="classic_skate",
    )

    match_config = SetupTranslator().to_match_config(setup)

    assert match_config.structure.structure_name == "one_vs_one"
    assert match_config.attack.attack_attempts == 2
    assert match_config.defense.defense_attempts == 3
    assert match_config.scoring.scoring_type == "letters"
    assert match_config.scoring.letters_word == "SKATE"
    assert match_config.victory.victory_type == "last_player_standing"
    assert match_config.victory.elimination_enabled is True
    assert match_config.structure_name == "one_vs_one"
    assert match_config.sport == "inline"
    assert match_config.player_profile_ids == ["stan", "denise"]
    assert match_config.player_display_names == ["Stan", "Denise"]
    assert match_config.preset_name == "classic_skate"


def test_setup_translator_can_build_legacy_match_parameters_from_setup() -> None:
    setup = MatchSetup(
        player_ids=["p1", "p2", "p3"],
        player_profile_ids=["stan", "denise", "alex"],
        player_display_names=["Stan", "Denise", "Alex"],
        structure_name="battle",
        sport="inline",
        letters_word="OUT",
        attack_attempts=2,
        defense_attempts=3,
        elimination_enabled=True,
        preset_name="battle_standard",
    )

    match_parameters = SetupTranslator().to_match_parameters(setup)

    assert match_parameters.player_ids == ["p1", "p2", "p3"]
    assert match_parameters.structure_name == "battle"
    assert match_parameters.sport == "inline"
    assert match_parameters.rule_set.letters_word == "OUT"
    assert match_parameters.rule_set.attack_attempts == 2
    assert match_parameters.rule_set.defense_attempts == 3
    assert match_parameters.rule_set.elimination_enabled is True
    assert match_parameters.player_profile_ids == ["stan", "denise", "alex"]
    assert match_parameters.player_display_names == ["Stan", "Denise", "Alex"]
    assert match_parameters.preset_name == "battle_standard"


def test_setup_translator_preserves_v6_match_parameters_shape() -> None:
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        player_profile_ids=["stan", "denise"],
        player_display_names=["Stan", "Denise"],
        sport="inline",
        preset_name="classic_skate",
    )

    match_config = SetupTranslator().from_match_parameters(match_parameters)

    assert match_config.structure.structure_name == "one_vs_one"
    assert match_config.attack.attack_attempts == 1
    assert match_config.defense.defense_attempts == 1
    assert match_config.scoring.letters_word == "SKATE"
    assert match_config.victory.elimination_enabled is True
    assert match_config.sport == "inline"
    assert match_config.player_profile_ids == ["stan", "denise"]
    assert match_config.player_display_names == ["Stan", "Denise"]
    assert match_config.preset_name == "classic_skate"


def test_preset_registry_can_build_v7_match_config_from_official_preset() -> None:
    registry = PresetRegistry()

    match_config = registry.create_match_config(
        "battle_hardcore",
        ["p1", "p2", "p3"],
    )

    assert match_config.structure.structure_name == "battle"
    assert match_config.structure.policies.initial_turn_order == (
        InitialTurnOrderPolicy.RANDOMIZED
    )
    assert match_config.attack.attack_attempts == 1
    assert match_config.defense.defense_attempts == 1
    assert match_config.scoring.letters_word == "SKATE"
    assert match_config.structure_name == "battle"
    assert match_config.sport == "inline"
    assert match_config.preset_name == "battle_hardcore"


def test_preset_registry_can_build_legacy_match_parameters_from_official_preset() -> None:
    registry = PresetRegistry()

    match_parameters = registry.create_match_parameters(
        "classic_skate",
        ["Stan", "Denise"],
    )

    assert match_parameters.player_ids == ["Stan", "Denise"]
    assert match_parameters.structure_name == "one_vs_one"
    assert match_parameters.sport == "inline"
    assert match_parameters.rule_set.letters_word == "SKATE"
    assert match_parameters.rule_set.attack_attempts == 1
    assert match_parameters.rule_set.defense_attempts == 3
    assert match_parameters.preset_name == "classic_skate"


def test_match_config_structure_name_comes_from_structure_config() -> None:
    match_config = MatchConfig(
        structure=StructureConfig(structure_name="battle"),
        sport="inline",
    )

    assert match_config.structure_name == "battle"
    assert match_config.sport == "inline"


def test_preset_registry_exposes_v9_3_reference_presets() -> None:
    registry = PresetRegistry()

    preset_names = registry.list_preset_names()

    assert "duel_short_strict_v9_3" in preset_names
    assert "duel_long_open_v9_3" in preset_names
    assert "battle_balanced_v9_3" in preset_names
    assert "battle_long_open_v9_3" in preset_names


def test_preset_registry_v9_3_reference_presets_cover_new_parameter_edges() -> None:
    registry = PresetRegistry()

    duel_short_strict = registry.get("duel_short_strict_v9_3")
    battle_balanced = registry.get("battle_balanced_v9_3")
    battle_long_open = registry.get("battle_long_open_v9_3")

    assert duel_short_strict.rule_set.letters_word == "S"
    assert duel_short_strict.rule_set.attack_attempts == 3
    assert duel_short_strict.rule_set.defense_attempts == 1
    assert duel_short_strict.fine_rules.uniqueness_enabled is True
    assert duel_short_strict.fine_rules.repetition_mode == "choice"
    assert duel_short_strict.fine_rules.repetition_limit == 3

    assert battle_balanced.rule_set.attack_attempts == 3
    assert battle_balanced.rule_set.defense_attempts == 2
    assert battle_balanced.fine_rules.repetition_mode == "common"
    assert battle_balanced.fine_rules.repetition_limit == 3

    assert battle_long_open.rule_set.letters_word == "SKATEBOARD"
    assert battle_long_open.fine_rules.uniqueness_enabled is False
    assert battle_long_open.fine_rules.repetition_mode == "disabled"


def test_preset_registry_exposes_v10_1_reference_presets() -> None:
    registry = PresetRegistry()

    preset_names = registry.list_preset_names()

    assert "duel_synergy_strict_v10_1" in preset_names
    assert "duel_verified_switch_v10_1" in preset_names
    assert "battle_switch_normal_v10_1" in preset_names
    assert "battle_multi_no_rep_v10_1" in preset_names


def test_preset_registry_v10_1_reference_presets_cover_v10_rule_interactions() -> None:
    registry = PresetRegistry()

    duel_synergy_strict = registry.get("duel_synergy_strict_v10_1")
    duel_verified_switch = registry.get("duel_verified_switch_v10_1")
    battle_switch_normal = registry.get("battle_switch_normal_v10_1")
    battle_multi_no_rep = registry.get("battle_multi_no_rep_v10_1")

    assert duel_synergy_strict.rule_set.attack_attempts == 2
    assert duel_synergy_strict.rule_set.defense_attempts == 3
    assert duel_synergy_strict.fine_rules.repetition_mode == "choice"
    assert duel_synergy_strict.fine_rules.repetition_limit == 4
    assert duel_synergy_strict.fine_rules.multiple_attack_enabled is False
    assert duel_synergy_strict.fine_rules.no_repetition is False
    assert duel_synergy_strict.fine_rules.switch_mode == "disabled"

    assert duel_verified_switch.rule_set.letters_word == "BLADE"
    assert duel_verified_switch.rule_set.attack_attempts == 2
    assert duel_verified_switch.fine_rules.uniqueness_enabled is False
    assert duel_verified_switch.fine_rules.repetition_mode == "common"
    assert duel_verified_switch.fine_rules.repetition_limit == 4
    assert duel_verified_switch.fine_rules.switch_mode == "verified"

    assert battle_switch_normal.structure_name == "battle"
    assert battle_switch_normal.rule_set.attack_attempts == 2
    assert battle_switch_normal.rule_set.defense_attempts == 2
    assert battle_switch_normal.fine_rules.uniqueness_enabled is True
    assert battle_switch_normal.fine_rules.repetition_mode == "common"
    assert battle_switch_normal.fine_rules.repetition_limit == 4
    assert battle_switch_normal.fine_rules.switch_mode == "normal"

    assert battle_multi_no_rep.structure_name == "battle"
    assert battle_multi_no_rep.rule_set.attack_attempts == 3
    assert battle_multi_no_rep.rule_set.defense_attempts == 1
    assert battle_multi_no_rep.fine_rules.uniqueness_enabled is False
    assert battle_multi_no_rep.fine_rules.repetition_mode == "common"
    assert battle_multi_no_rep.fine_rules.repetition_limit == 2
    assert battle_multi_no_rep.fine_rules.multiple_attack_enabled is True
    assert battle_multi_no_rep.fine_rules.no_repetition is True
    assert battle_multi_no_rep.fine_rules.switch_mode == "enabled"
