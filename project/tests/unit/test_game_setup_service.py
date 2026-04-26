import shutil
from pathlib import Path

from application.game_setup_service import GameSetupService
from config.match_policies import InitialTurnOrderPolicy, RelevanceCriterion
from core.types import Phase


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "game_setup_service"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_game_setup_service_can_start_preset_controller() -> None:
    service = GameSetupService()

    controller = service.create_started_controller_from_preset(
        "battle_standard",
        ["Stan", "Denise", "Alex"],
    )

    assert controller.match_parameters.preset_name == "battle_standard"
    assert controller.structure_name == "battle"
    assert controller.get_state().phase == Phase.TURN


def test_game_setup_service_can_start_preset_controller_from_profiles() -> None:
    service = GameSetupService()

    controller = service.create_started_controller_from_preset_profiles(
        "battle_standard",
        ["stan", "denise", "alex"],
    )

    assert controller.match_parameters.player_ids == ["stan", "denise", "alex"]
    assert controller.match_parameters.player_profile_ids == ["stan", "denise", "alex"]
    assert controller.match_parameters.player_display_names == ["Stan", "Denise", "Alex"]
    assert controller.match_parameters.preset_name == "battle_standard"


def test_game_setup_service_can_start_custom_controller() -> None:
    service = GameSetupService()

    controller = service.create_started_controller_from_custom_setup(
        player_ids=["Stan", "Denise"],
        letters_word="out",
        attack_attempts=2,
        defense_attempts=3,
        repetition_limit=4,
    )

    assert controller.match_parameters.preset_name is None
    assert controller.match_parameters.structure_name == "one_vs_one"
    assert controller.match_parameters.rule_set.letters_word == "OUT"
    assert controller.match_parameters.rule_set.attack_attempts == 2
    assert controller.match_parameters.rule_set.defense_attempts == 3
    assert controller.match_parameters.sport == "inline"
    assert controller.get_state().phase == Phase.TURN


def test_game_setup_service_can_start_custom_controller_from_profiles() -> None:
    service = GameSetupService()

    controller = service.create_started_controller_from_custom_setup_profiles(
        player_profile_ids=["stan", "denise"],
        letters_word="out",
        attack_attempts=2,
        defense_attempts=3,
        repetition_limit=4,
    )

    assert controller.match_parameters.player_ids == ["stan", "denise"]
    assert controller.match_parameters.player_profile_ids == ["stan", "denise"]
    assert controller.match_parameters.player_display_names == ["Stan", "Denise"]
    assert controller.match_parameters.preset_name is None


def test_game_setup_service_can_build_choice_order_policies() -> None:
    service = GameSetupService()

    policies = service.build_order_policies(
        order_mode="choice",
        player_ids=["Stan", "Denise", "Alex"],
        explicit_player_order=["Denise", "Alex", "Stan"],
    )

    assert policies.initial_turn_order == InitialTurnOrderPolicy.EXPLICIT_CHOICE
    assert policies.explicit_player_order == ("Denise", "Alex", "Stan")


def test_game_setup_service_can_preview_relevance_order() -> None:
    service = GameSetupService()

    preview = service.preview_order(
        order_mode="relevance",
        player_ids=["Stan", "Denise", "Alex"],
        player_profile_ids=["stan", "denise", "alex"],
        relevance_criterion="local_rank",
    )

    assert preview == ["Denise", "Stan", "Alex"]


def test_game_setup_service_can_build_relevance_order_policies_from_profiles() -> None:
    service = GameSetupService()

    policies = service.build_order_policies(
        order_mode="relevance",
        player_ids=["Stan", "Denise", "Alex"],
        player_profile_ids=["stan", "denise", "alex"],
        relevance_criterion="age",
    )

    assert policies.initial_turn_order == InitialTurnOrderPolicy.RELEVANCE
    assert policies.relevance_criterion == RelevanceCriterion.AGE
    assert policies.explicit_player_order == ("Alex", "Stan", "Denise")


def test_game_setup_service_can_start_custom_controller_with_choice_order() -> None:
    service = GameSetupService()
    policies = service.build_order_policies(
        order_mode="choice",
        player_ids=["stan", "denise"],
        explicit_player_order=["denise", "stan"],
    )

    controller = service.create_started_controller_from_custom_setup_profiles(
        player_profile_ids=["stan", "denise"],
        letters_word="SKATE",
        attack_attempts=1,
        defense_attempts=1,
        policies=policies,
    )

    state = controller.get_state()

    assert state.turn_order == [1, 0]
    assert state.attacker_index == 1


def test_game_setup_service_can_disable_uniqueness_in_custom_setup() -> None:
    service = GameSetupService()

    controller = service.create_started_controller_from_custom_setup(
        player_ids=["Stan", "Denise"],
        letters_word="OUT",
        attack_attempts=1,
        defense_attempts=1,
        uniqueness_enabled=False,
    )

    assert controller.match_parameters.fine_rules.uniqueness_enabled is False
    assert controller.match_config.fine_rules.uniqueness_enabled is False


def test_game_setup_service_can_configure_repetition_in_custom_setup() -> None:
    service = GameSetupService()

    controller = service.create_started_controller_from_custom_setup(
        player_ids=["Stan", "Denise"],
        letters_word="OUT",
        attack_attempts=2,
        defense_attempts=1,
        repetition_mode="common",
        repetition_limit=2,
    )

    assert controller.match_parameters.fine_rules.repetition_mode == "common"
    assert controller.match_parameters.fine_rules.repetition_limit == 2
    assert controller.match_config.fine_rules.repetition_mode == "common"
    assert controller.match_config.fine_rules.repetition_limit == 2


def test_game_setup_service_reports_attack_repetition_synergy_feedback() -> None:
    service = GameSetupService()

    feedback = service.get_attack_repetition_synergy_feedback(
        attack_attempts=2,
        repetition_mode="choice",
        repetition_limit=3,
        max_limit=9,
    )

    assert feedback == (
        "Attack/Repetition synergy active: repetition limit must be a "
        "multiple of Attack. Suggested values: 2, 4, 6."
    )


def test_game_setup_service_can_create_loading_controller() -> None:
    service = GameSetupService()

    controller = service.create_loading_controller()

    assert controller.match_parameters.player_ids == ["Player 1", "Player 2"]
    assert controller.match_parameters.structure_name == "one_vs_one"
    assert controller.match_parameters.sport == "inline"
    assert controller.match_parameters.preset_name is None


def test_game_setup_service_can_load_controller_from_save() -> None:
    case_dir = _make_case_dir("load_controller")

    try:
        service = GameSetupService()
        controller = service.create_started_controller_from_custom_setup(
            player_ids=["Stan", "Denise"],
            letters_word="S",
            attack_attempts=1,
            defense_attempts=1,
        )
        controller.start_turn("soul")
        controller.resolve_defense(False)

        save_path = case_dir / "finished_game.json"
        controller.save_game(str(save_path))

        loaded_controller = service.load_controller(str(save_path))

        assert loaded_controller.get_state().phase == Phase.END
        assert loaded_controller.match_parameters.structure_name == "one_vs_one"
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_game_setup_service_exposes_local_profiles() -> None:
    service = GameSetupService()

    profiles = service.list_local_profiles()

    assert [profile.display_name for profile in profiles] == [
        "Alex",
        "Denise",
        "Frank",
        "Jamie",
        "Margaux",
        "Stan",
    ]
    assert service.get_local_profile("stan").display_name == "Stan"
