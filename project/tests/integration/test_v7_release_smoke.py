import shutil
from pathlib import Path

from application.game_session import GameSession
from application.game_setup_service import GameSetupService
from config.match_parameters import MatchParameters
from config.preset_registry import PresetRegistry
from core.types import AttackResolutionStatus, DefenseResolutionStatus, EventName, Phase, TurnPhase


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "v7_release_smoke"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_v7_release_smoke_can_start_preset_game_with_expected_context() -> None:
    setup_service = GameSetupService()
    controller = setup_service.create_started_controller_from_preset(
        "classic_skate",
        ["Stan", "Denise"],
    )

    state = controller.get_state()
    context = state.history.build_match_context()

    assert controller.match_parameters.preset_name == "classic_skate"
    assert controller.structure_name == "one_vs_one"
    assert state.phase == Phase.TURN
    assert context is not None
    assert context.structure_name == "one_vs_one"
    assert context.preset_name == "classic_skate"


def test_v7_release_smoke_can_finish_and_reload_custom_game() -> None:
    case_dir = _make_case_dir("preset_finish_and_reload")

    try:
        setup_service = GameSetupService()
        controller = setup_service.create_started_controller_from_custom_setup(
            ["Stan", "Denise"],
            letters_word="S",
            attack_attempts=1,
            defense_attempts=1,
        )

        controller.start_turn("soul")
        resolution = controller.resolve_defense(False)

        save_path = case_dir / "finished_game.json"
        controller.save_game(str(save_path))

        reloaded_controller = setup_service.create_loading_controller()
        reloaded_controller.load_game(str(save_path))
        reloaded_state = reloaded_controller.get_state()
        reloaded_context = reloaded_state.history.build_match_context()

        assert resolution == DefenseResolutionStatus.GAME_FINISHED
        assert save_path.exists()
        assert reloaded_state.phase == Phase.END
        assert reloaded_context is not None
        assert reloaded_context.structure_name == "one_vs_one"
        assert reloaded_context.preset_name is None
        assert reloaded_state.history.events[-1].name == EventName.GAME_FINISHED
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_v7_release_smoke_can_run_custom_multi_attempt_attack_flow() -> None:
    setup_service = GameSetupService()
    controller = setup_service.create_started_controller_from_custom_setup(
        player_ids=["Stan", "Denise"],
        letters_word="OUT",
        attack_attempts=2,
        defense_attempts=1,
    )

    controller.start_turn("kickflip")

    first_attack = controller.resolve_attack(False)
    second_attack = controller.resolve_attack(True)
    defense = controller.resolve_defense(True)
    state = controller.get_state()

    assert first_attack == AttackResolutionStatus.ATTACK_CONTINUES
    assert second_attack == AttackResolutionStatus.DEFENSE_READY
    assert defense == DefenseResolutionStatus.TURN_FINISHED
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.current_trick is None
    assert any(event.name == EventName.ATTACK_FAILED_ATTEMPT for event in state.history.events)
    assert any(event.name == EventName.ATTACK_SUCCEEDED for event in state.history.events)


def test_v7_release_smoke_can_preserve_transition_runtime_through_save_load() -> None:
    case_dir = _make_case_dir("transition_runtime_save_load")

    try:
        session = GameSession(
            PresetRegistry().create_match_parameters("classic_skate", ["p1", "p2"])
        )
        session.start_game()
        session.add_player_between_turns("p3")
        session.remove_player_between_turns("p2")

        save_path = case_dir / "after_transitions.json"
        session.save_game(str(save_path))

        reloaded_session = GameSession(MatchParameters(player_ids=["placeholder1", "placeholder2"]))
        reloaded_session.load_game(str(save_path))
        state = reloaded_session.get_state()
        context = state.history.build_match_context()

        assert reloaded_session.structure_name == "one_vs_one"
        assert reloaded_session.match_parameters.player_ids == ["p1", "p3"]
        assert state.turn_phase == TurnPhase.TURN_OPEN
        assert state.turn_order == [0, 1]
        assert context is not None
        assert context.structure_name == "one_vs_one"
        assert context.preset_name is None
        assert context.player_names == ["p1", "p3"]
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_v7_release_smoke_can_undo_transition_chain_back_to_preset_context() -> None:
    session = GameSession(
        PresetRegistry().create_match_parameters("classic_skate", ["p1", "p2"])
    )
    session.start_game()
    session.add_player_between_turns("p3")
    session.remove_player_between_turns("p2")

    assert session.undo() is True
    assert session.undo() is True

    state = session.get_state()
    context = state.history.build_match_context()

    assert session.structure_name == "one_vs_one"
    assert session.match_parameters.preset_name == "classic_skate"
    assert session.match_parameters.player_ids == ["p1", "p2"]
    assert state.history.events[-1].name == EventName.GAME_STARTED
    assert context is not None
    assert context.structure_name == "one_vs_one"
    assert context.preset_name == "classic_skate"
