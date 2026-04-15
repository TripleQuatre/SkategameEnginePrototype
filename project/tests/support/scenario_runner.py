from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

import modes.battle as battle_module

from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.state import GameState
from core.types import DefenseResolutionStatus


@dataclass
class ScenarioStep:
    action: str
    trick: str | None = None
    success: bool | None = None
    expected_status: DefenseResolutionStatus | None = None
    expected_success: bool | None = None
    save_key: str | None = None


@dataclass
class ScenarioDefinition:
    player_ids: list[str]
    mode_name: str | None = None
    letters_word: str = "SKATE"
    defense_attempts: int = 1
    fixed_turn_order: list[int] | None = None
    steps: list[ScenarioStep] = field(default_factory=list)


@dataclass
class ScenarioResult:
    controller: GameController
    state: GameState
    action_results: list[Any]
    save_paths: dict[str, Path]


class ScenarioRunner:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def run(self, definition: ScenarioDefinition) -> ScenarioResult:
        save_paths: dict[str, Path] = {}
        action_results: list[Any] = []

        with self._patch_battle_shuffle(definition.fixed_turn_order):
            controller = self._create_controller(definition)
            controller.start_game()

            for step in definition.steps:
                result = self._apply_step(controller, step, save_paths)
                action_results.append(result)

        return ScenarioResult(
            controller=controller,
            state=controller.get_state(),
            action_results=action_results,
            save_paths=save_paths,
        )

    def _create_controller(self, definition: ScenarioDefinition) -> GameController:
        mode_name = definition.mode_name
        if mode_name is None:
            mode_name = "one_vs_one" if len(definition.player_ids) == 2 else "battle"

        match_parameters = MatchParameters(
            player_ids=definition.player_ids,
            mode_name=mode_name,
            rule_set=RuleSetConfig(
                letters_word=definition.letters_word,
                defense_attempts=definition.defense_attempts,
            ),
        )

        return GameController(match_parameters)

    def _apply_step(
        self,
        controller: GameController,
        step: ScenarioStep,
        save_paths: dict[str, Path],
    ) -> Any:
        if step.action == "start_turn":
            if step.trick is None:
                raise ValueError("start_turn requires a trick.")
            controller.start_turn(step.trick)
            return None

        if step.action == "resolve":
            if step.success is None:
                raise ValueError("resolve requires a success value.")
            result = controller.resolve_defense(step.success)
            if step.expected_status is not None:
                assert result == step.expected_status
            return result

        if step.action == "cancel_turn":
            if step.trick is None:
                raise ValueError("cancel_turn requires a trick.")
            controller.cancel_turn(step.trick)
            return None

        if step.action == "undo":
            undone = controller.undo()
            if step.expected_success is not None:
                assert undone == step.expected_success
            return undone

        if step.action == "save":
            if not step.save_key:
                raise ValueError("save requires a save_key.")
            save_path = self.base_dir / f"{step.save_key}.json"
            controller.save_game(str(save_path))
            save_paths[step.save_key] = save_path
            return save_path

        if step.action == "load":
            if not step.save_key:
                raise ValueError("load requires a save_key.")
            save_path = save_paths.get(step.save_key)
            if save_path is None:
                raise ValueError(f"Unknown save_key: {step.save_key}")
            controller.load_game(str(save_path))
            return save_path

        raise ValueError(f"Unknown scenario action: {step.action}")

    def _patch_battle_shuffle(self, fixed_turn_order: list[int] | None):
        if fixed_turn_order is None:
            return _NullContext()

        def fixed_shuffle(values: list[int]) -> None:
            values[:] = list(fixed_turn_order)

        return patch.object(battle_module.random, "shuffle", fixed_shuffle)


class _NullContext:
    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False
