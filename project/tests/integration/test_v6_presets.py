from application.game_session import GameSession as GameEngine
import shutil
from pathlib import Path

import match.structure.battle_structure as battle_structure_module

from config.match_parameters import MatchParameters
from config.match_policies import (
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
    MatchPolicies,
)
from config.preset_registry import PresetRegistry
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.types import DefenseResolutionStatus, Phase
from tests.support.scenario_runner import (
    ScenarioDefinition,
    ScenarioRunner,
    ScenarioStep,
)


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "v6_presets"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_game_engine_classic_skate_preset_starts_with_expected_configuration() -> None:
    preset = PresetRegistry().get("classic_skate")
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2"],
            structure_name=preset.structure_name,
            rule_set=preset.rule_set,
            policies=preset.policies,
            preset_name=preset.name,
        )
    )

    engine.start_game()
    state = engine.get_state()
    context = state.history.build_match_context()

    assert state.phase == Phase.TURN
    assert state.turn_order == [0, 1]
    assert state.rule_set.letters_word == "SKATE"
    assert state.rule_set.defense_attempts == 3
    assert context is not None
    assert context.structure_name == "one_vs_one"
    assert context.preset_name == "classic_skate"


def test_game_engine_classic_blade_preset_uses_blade_word() -> None:
    preset = PresetRegistry().get("classic_blade")
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2"],
            structure_name=preset.structure_name,
            rule_set=preset.rule_set,
            policies=preset.policies,
            preset_name=preset.name,
        )
    )

    engine.start_game()
    state = engine.get_state()

    assert state.phase == Phase.TURN
    assert state.turn_order == [0, 1]
    assert state.rule_set.letters_word == "BLADE"
    assert state.rule_set.defense_attempts == 1


def test_battle_standard_preset_uses_randomized_order_and_out_word(monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    preset = PresetRegistry().get("battle_standard")
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            structure_name=preset.structure_name,
            rule_set=preset.rule_set,
            policies=preset.policies,
            preset_name=preset.name,
        )
    )

    engine.start_game()
    state = engine.get_state()

    assert state.turn_order == [2, 0, 1]
    assert state.attacker_index == 2
    assert state.rule_set.letters_word == "OUT"
    assert state.rule_set.defense_attempts == 3


def test_battle_hardcore_preset_uses_skate_word_and_one_attempt(monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    preset = PresetRegistry().get("battle_hardcore")
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            structure_name=preset.structure_name,
            rule_set=preset.rule_set,
            policies=preset.policies,
            preset_name=preset.name,
        )
    )

    engine.start_game()
    state = engine.get_state()

    assert state.turn_order == [2, 0, 1]
    assert state.rule_set.letters_word == "SKATE"
    assert state.rule_set.defense_attempts == 1


def test_technical_reverse_defender_order_policy_works(monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            structure_name="battle",
            policies=MatchPolicies(
                initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
                defender_order=DefenderOrderPolicy.REVERSE_TURN_ORDER,
            ),
        )
    )

    engine.start_game()
    engine.start_turn("kickflip")
    state = engine.get_state()

    assert state.turn_order == [2, 0, 1]
    assert state.attacker_index == 2
    assert state.defender_indices == [1, 0]


def test_technical_no_elimination_configuration_keeps_players_active(monkeypatch) -> None:
    def fixed_shuffle(values: list[int]) -> None:
        values[:] = [2, 0, 1]

    monkeypatch.setattr(battle_structure_module.random, "shuffle", fixed_shuffle)

    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            structure_name="battle",
            rule_set=RuleSetConfig(
                letters_word="S",
                elimination_enabled=False,
                defense_attempts=1,
            ),
        )
    )

    engine.start_game()
    engine.start_turn("soul")
    result = engine.resolve_defense(False)

    state = engine.get_state()
    assert result == DefenseResolutionStatus.DEFENSE_CONTINUES
    assert state.phase == Phase.TURN
    assert state.players[0].score == 1
    assert state.players[0].is_active is True


def test_scenario_runner_accepts_official_preset_name_for_v6_scenarios(
) -> None:
    case_dir = _make_case_dir("scenario_runner_preset")

    try:
        runner = ScenarioRunner(case_dir)

        result = runner.run(
            ScenarioDefinition(
                player_ids=["Stan", "Denise", "Alex"],
                preset_name="battle_standard",
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
        shutil.rmtree(case_dir, ignore_errors=True)

    state = result.state
    assert result.controller.match_parameters.preset_name == "battle_standard"
    assert state.defender_indices == [0, 1]


def test_game_controller_save_and_load_preserves_v6_preset_configuration() -> None:
    case_dir = _make_case_dir("controller_save_load_preset")
    preset = PresetRegistry().get("battle_hardcore")
    controller = GameController(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            structure_name=preset.structure_name,
            rule_set=preset.rule_set,
            policies=preset.policies,
            preset_name=preset.name,
        )
    )

    try:
        controller.start_game()
        save_path = case_dir / "v6_preset_save.json"
        controller.save_game(str(save_path))

        reloaded_controller = GameController(MatchParameters(player_ids=["a", "b"]))
        reloaded_controller.load_game(str(save_path))

        reloaded_match_parameters = reloaded_controller.match_parameters
        reloaded_context = reloaded_controller.get_state().history.build_match_context()

        assert reloaded_match_parameters.preset_name == "battle_hardcore"
        assert reloaded_match_parameters.structure_name == "battle"
        assert reloaded_match_parameters.policies == preset.policies
        assert reloaded_match_parameters.rule_set == preset.rule_set
        assert reloaded_context is not None
        assert reloaded_context.structure_name == "battle"
        assert reloaded_context.preset_name == "battle_hardcore"
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)
