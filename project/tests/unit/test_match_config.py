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
        structure_name="one_vs_one",
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
    assert match_config.preset_name == "classic_skate"


def test_setup_translator_can_build_legacy_match_parameters_from_setup() -> None:
    setup = MatchSetup(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
        letters_word="OUT",
        attack_attempts=2,
        defense_attempts=3,
        elimination_enabled=True,
        preset_name="battle_standard",
    )

    match_parameters = SetupTranslator().to_match_parameters(setup)

    assert match_parameters.player_ids == ["p1", "p2", "p3"]
    assert match_parameters.structure_name == "battle"
    assert match_parameters.rule_set.letters_word == "OUT"
    assert match_parameters.rule_set.attack_attempts == 2
    assert match_parameters.rule_set.defense_attempts == 3
    assert match_parameters.rule_set.elimination_enabled is True
    assert match_parameters.preset_name == "battle_standard"


def test_setup_translator_preserves_v6_match_parameters_shape() -> None:
    match_parameters = MatchParameters(player_ids=["p1", "p2"], preset_name="classic_skate")

    match_config = SetupTranslator().from_match_parameters(match_parameters)

    assert match_config.structure.structure_name == "one_vs_one"
    assert match_config.attack.attack_attempts == 1
    assert match_config.defense.defense_attempts == 1
    assert match_config.scoring.letters_word == "SKATE"
    assert match_config.victory.elimination_enabled is True
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
    assert match_config.preset_name == "battle_hardcore"


def test_preset_registry_can_build_legacy_match_parameters_from_official_preset() -> None:
    registry = PresetRegistry()

    match_parameters = registry.create_match_parameters(
        "classic_skate",
        ["Stan", "Denise"],
    )

    assert match_parameters.player_ids == ["Stan", "Denise"]
    assert match_parameters.structure_name == "one_vs_one"
    assert match_parameters.rule_set.letters_word == "SKATE"
    assert match_parameters.rule_set.attack_attempts == 1
    assert match_parameters.rule_set.defense_attempts == 3
    assert match_parameters.preset_name == "classic_skate"


def test_match_config_structure_name_comes_from_structure_config() -> None:
    match_config = MatchConfig(
        structure=StructureConfig(structure_name="battle"),
    )

    assert match_config.structure_name == "battle"
