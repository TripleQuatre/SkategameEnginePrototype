import shutil
from pathlib import Path

from application.game_setup_service import GameSetupService
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


def test_game_setup_service_can_start_custom_controller() -> None:
    service = GameSetupService()

    controller = service.create_started_controller_from_custom_setup(
        player_ids=["Stan", "Denise"],
        letters_word="out",
        attack_attempts=2,
        defense_attempts=3,
    )

    assert controller.match_parameters.preset_name is None
    assert controller.match_parameters.structure_name == "one_vs_one"
    assert controller.match_parameters.rule_set.letters_word == "OUT"
    assert controller.match_parameters.rule_set.attack_attempts == 2
    assert controller.match_parameters.rule_set.defense_attempts == 3
    assert controller.get_state().phase == Phase.TURN


def test_game_setup_service_can_create_loading_controller() -> None:
    service = GameSetupService()

    controller = service.create_loading_controller()

    assert controller.match_parameters.player_ids == ["Player 1", "Player 2"]
    assert controller.match_parameters.structure_name == "one_vs_one"
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
