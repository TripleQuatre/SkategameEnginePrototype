import modes.battle as battle_module

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
from engine.game_engine import GameEngine
from tests.support.scenario_runner import (
    ScenarioDefinition,
    ScenarioRunner,
    ScenarioStep,
)


def test_game_engine_classic_skate_preset_starts_with_expected_configuration() -> None:
    preset = PresetRegistry().get("classic_skate")
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2"],
            mode_name=preset.mode_name,
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
    assert context.preset_name == "classic_skate"
    assert context.mode_name == "one_vs_one"


def test_game_engine_classic_blade_preset_uses_blade_word() -> None:
    preset = PresetRegistry().get("classic_blade")
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2"],
            mode_name=preset.mode_name,
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

    monkeypatch.setattr(battle_module.random, "shuffle", fixed_shuffle)

    preset = PresetRegistry().get("battle_standard")
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            mode_name=preset.mode_name,
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

    monkeypatch.setattr(battle_module.random, "shuffle", fixed_shuffle)

    preset = PresetRegistry().get("battle_hardcore")
    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            mode_name=preset.mode_name,
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

    monkeypatch.setattr(battle_module.random, "shuffle", fixed_shuffle)

    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            mode_name="battle",
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

    monkeypatch.setattr(battle_module.random, "shuffle", fixed_shuffle)

    engine = GameEngine(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            mode_name="battle",
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
    tmp_path,
) -> None:
    runner = ScenarioRunner(tmp_path)

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

    state = result.state
    assert result.controller.engine.match_parameters.preset_name == "battle_standard"
    assert state.defender_indices == [0, 1]


def test_game_controller_save_and_load_preserves_v6_preset_configuration(tmp_path) -> None:
    preset = PresetRegistry().get("battle_hardcore")
    controller = GameController(
        MatchParameters(
            player_ids=["p1", "p2", "p3"],
            mode_name=preset.mode_name,
            rule_set=preset.rule_set,
            policies=preset.policies,
            preset_name=preset.name,
        )
    )

    controller.start_game()
    save_path = tmp_path / "v6_preset_save.json"
    controller.save_game(str(save_path))

    reloaded_controller = GameController(MatchParameters(player_ids=["a", "b"]))
    reloaded_controller.load_game(str(save_path))

    reloaded_match_parameters = reloaded_controller.engine.match_parameters
    reloaded_context = reloaded_controller.get_state().history.build_match_context()

    assert reloaded_match_parameters.preset_name == "battle_hardcore"
    assert reloaded_match_parameters.mode_name == "battle"
    assert reloaded_match_parameters.policies == preset.policies
    assert reloaded_match_parameters.rule_set == preset.rule_set
    assert reloaded_context is not None
    assert reloaded_context.preset_name == "battle_hardcore"
