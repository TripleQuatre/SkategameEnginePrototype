from core.types import DefenseResolutionStatus, EventName, Phase
from tests.support.scenario_runner import (
    ScenarioDefinition,
    ScenarioRunner,
    ScenarioStep,
)


def test_scenario_runner_can_play_battle_turn_sequence(tmp_path) -> None:
    runner = ScenarioRunner(tmp_path)

    result = runner.run(
        ScenarioDefinition(
            player_ids=["Stan", "Denise", "Alex"],
            mode_name="battle",
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

    state = result.state
    assert state.phase == Phase.TURN
    assert state.turn_order == [2, 0, 1]
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.players[1].score == 1
    assert state.history.events[-1].name == EventName.TURN_ENDED


def test_scenario_runner_can_save_and_load_finished_game(tmp_path) -> None:
    runner = ScenarioRunner(tmp_path)

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


def test_scenario_runner_can_cancel_and_undo(tmp_path) -> None:
    runner = ScenarioRunner(tmp_path)

    result = runner.run(
        ScenarioDefinition(
            player_ids=["p1", "p2"],
            steps=[
                ScenarioStep(action="cancel_turn", trick="makio"),
                ScenarioStep(action="undo", expected_success=True),
            ],
        )
    )

    state = result.state
    assert state.phase == Phase.TURN
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == EventName.GAME_STARTED
