import shutil
from pathlib import Path

from core.types import (
    AttackResolutionStatus,
    DefenseResolutionStatus,
    EventName,
    Phase,
    TurnPhase,
)
from tests.support.scenario_runner import (
    ScenarioDefinition,
    ScenarioRunner,
    ScenarioStep,
)


def _make_runner(test_name: str) -> tuple[ScenarioRunner, Path]:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "scenario_runner"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return ScenarioRunner(base_dir), base_dir


def test_scenario_runner_can_play_battle_turn_sequence() -> None:
    runner, base_dir = _make_runner("battle_turn_sequence")

    try:
        result = runner.run(
            ScenarioDefinition(
                player_ids=["Stan", "Denise", "Alex"],
                structure_name="battle",
                fixed_turn_order=[2, 0, 1],
                steps=[
                    ScenarioStep(action="start_turn", trick="kickflip"),
                    ScenarioStep(
                        action="resolve",
                        success=True,
                        expected_status=DefenseResolutionStatus.DEFENSE_CONTINUES,
                    ),
                    ScenarioStep(
                        action="resolve",
                        success=False,
                        expected_status=DefenseResolutionStatus.TURN_FINISHED,
                    ),
                ],
            )
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    state = result.state
    assert state.phase == Phase.TURN
    assert state.turn_order == [2, 0, 1]
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.players[1].score == 1
    assert state.history.events[-1].name == EventName.TURN_ENDED


def test_scenario_runner_accepts_structure_name_alias_for_runtime_scenarios() -> None:
    runner, base_dir = _make_runner("battle_turn_sequence_structure_name")

    try:
        result = runner.run(
            ScenarioDefinition(
                player_ids=["Stan", "Denise", "Alex"],
                structure_name="battle",
                fixed_turn_order=[2, 0, 1],
                steps=[
                    ScenarioStep(action="start_turn", trick="kickflip"),
                    ScenarioStep(
                        action="resolve",
                        success=True,
                        expected_status=DefenseResolutionStatus.DEFENSE_CONTINUES,
                    ),
                ],
            )
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    assert result.controller.structure_name == "battle"
    assert result.state.turn_order == [2, 0, 1]


def test_scenario_runner_can_save_and_load_finished_game() -> None:
    runner, base_dir = _make_runner("save_load_finished_game")

    try:
        result = runner.run(
            ScenarioDefinition(
                player_ids=["p1", "p2"],
                letters_word="S",
                steps=[
                    ScenarioStep(action="start_turn", trick="soul"),
                    ScenarioStep(
                        action="resolve",
                        success=False,
                        expected_status=DefenseResolutionStatus.GAME_FINISHED,
                    ),
                    ScenarioStep(action="save", save_key="finished_game"),
                    ScenarioStep(action="undo", expected_success=True),
                    ScenarioStep(action="load", save_key="finished_game"),
                ],
            )
        )

        state = result.state
        assert result.save_paths["finished_game"].exists()
        assert state.phase == Phase.END
        assert state.current_trick is None
        assert state.players[1].is_active is False
        assert state.history.events[-1].name == EventName.GAME_FINISHED
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_scenario_runner_can_cancel_and_undo() -> None:
    runner, base_dir = _make_runner("cancel_and_undo")

    try:
        result = runner.run(
            ScenarioDefinition(
                player_ids=["p1", "p2"],
                steps=[
                    ScenarioStep(action="cancel_turn", trick="makio"),
                    ScenarioStep(action="undo", expected_success=True),
                ],
            )
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    state = result.state
    assert state.phase == Phase.TURN
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_scenario_runner_can_play_attack_phase_before_defense() -> None:
    runner, base_dir = _make_runner("attack_before_defense")

    try:
        result = runner.run(
            ScenarioDefinition(
                player_ids=["p1", "p2"],
                attack_attempts=2,
                steps=[
                    ScenarioStep(action="start_turn", trick="soul"),
                    ScenarioStep(
                        action="resolve_attack",
                        success=False,
                        expected_attack_status=AttackResolutionStatus.ATTACK_CONTINUES,
                    ),
                    ScenarioStep(
                        action="resolve_attack",
                        success=True,
                        expected_attack_status=AttackResolutionStatus.DEFENSE_READY,
                    ),
                    ScenarioStep(
                        action="resolve",
                        success=True,
                        expected_status=DefenseResolutionStatus.TURN_FINISHED,
                    ),
                ],
            )
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    state = result.state
    assert state.phase == Phase.TURN
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.attacker_index == 1
    assert state.current_trick is None
    assert any(event.name == EventName.ATTACK_FAILED_ATTEMPT for event in state.history.events)
    assert any(event.name == EventName.ATTACK_SUCCEEDED for event in state.history.events)


def test_scenario_runner_can_apply_roster_transitions_between_turns() -> None:
    runner, base_dir = _make_runner("roster_transitions")

    try:
        result = runner.run(
            ScenarioDefinition(
                player_ids=["p1", "p2"],
                steps=[
                    ScenarioStep(action="add_player", player_id="p3"),
                    ScenarioStep(action="remove_player", player_id="p2"),
                    ScenarioStep(action="start_turn", trick="soul"),
                    ScenarioStep(
                        action="resolve",
                        success=True,
                        expected_status=DefenseResolutionStatus.TURN_FINISHED,
                    ),
                ],
            )
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    state = result.state
    assert [player.id for player in state.players] == ["p1", "p3"]
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert result.controller.structure_name == "one_vs_one"
    history_names = [event.name for event in state.history.events]
    assert EventName.PLAYER_JOINED in history_names
    assert EventName.PLAYER_REMOVED in history_names


def test_scenario_runner_can_preserve_structure_context_after_transition_and_load() -> None:
    runner, base_dir = _make_runner("structure_context_after_transition_and_load")

    try:
        result = runner.run(
            ScenarioDefinition(
                player_ids=["p1", "p2"],
                steps=[
                    ScenarioStep(action="add_player", player_id="p3"),
                    ScenarioStep(action="save", save_key="after_join"),
                    ScenarioStep(action="remove_player", player_id="p2"),
                    ScenarioStep(action="load", save_key="after_join"),
                ],
            )
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    state = result.state
    context = state.history.build_match_context()

    assert context is not None
    assert context.structure_name == "battle"
    assert context.structure_name == "battle"
    assert result.controller.match_parameters.structure_name == "battle"
    assert context.player_names == ["p1", "p2", "p3"]
    assert context.preset_name is None
    assert result.controller.structure_name == "battle"
