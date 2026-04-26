from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

import match.structure.battle_structure as battle_structure_module

from config.match_setup import MatchSetup
from config.preset_registry import PresetRegistry
from config.setup_translator import SetupTranslator
from controllers.game_controller import GameController
from core.state import GameState
from core.types import AttackResolutionStatus, DefenseResolutionStatus


@dataclass
class ScenarioStep:
    action: str
    trick: str | None = None
    player_id: str | None = None
    success: bool | None = None
    attack_attempts: int | None = None
    expected_status: DefenseResolutionStatus | None = None
    expected_attack_status: AttackResolutionStatus | None = None
    expected_success: bool | None = None
    save_key: str | None = None


@dataclass
class ScenarioDefinition:
    player_ids: list[str]
    preset_name: str | None = None
    structure_name: str | None = None
    letters_word: str | None = None
    attack_attempts: int | None = None
    defense_attempts: int | None = None
    repetition_mode: str | None = None
    repetition_limit: int | None = None
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
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.preset_registry = PresetRegistry()
        self.setup_translator = SetupTranslator()

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
        if definition.preset_name is not None:
            setup = self.preset_registry.create_match_setup(
                definition.preset_name,
                definition.player_ids,
            )
            if definition.letters_word is not None:
                setup.letters_word = definition.letters_word
            if definition.attack_attempts is not None:
                setup.attack_attempts = definition.attack_attempts
            if definition.defense_attempts is not None:
                setup.defense_attempts = definition.defense_attempts
            if definition.repetition_mode is not None:
                setup.repetition_mode = definition.repetition_mode
            if definition.repetition_limit is not None:
                setup.repetition_limit = definition.repetition_limit
            return GameController(self.setup_translator.to_match_parameters(setup))

        structure_name = definition.structure_name
        if structure_name is None:
            structure_name = (
                "one_vs_one" if len(definition.player_ids) == 2 else "battle"
            )

        setup = MatchSetup(
            player_ids=definition.player_ids,
            structure_name=structure_name,
            letters_word=definition.letters_word or "SKATE",
            attack_attempts=definition.attack_attempts or 1,
            defense_attempts=definition.defense_attempts or 1,
            repetition_mode=definition.repetition_mode or "choice",
            repetition_limit=definition.repetition_limit or 3,
        )
        return GameController(self.setup_translator.to_match_parameters(setup))

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

        if step.action == "resolve_attack":
            if step.success is None:
                raise ValueError("resolve_attack requires a success value.")
            result = controller.resolve_attack(step.success)
            if step.expected_attack_status is not None:
                assert result == step.expected_attack_status
            return result

        if step.action == "cancel_turn":
            if step.trick is None:
                raise ValueError("cancel_turn requires a trick.")
            controller.cancel_turn(step.trick)
            return None

        if step.action == "add_player":
            if step.player_id is None:
                raise ValueError("add_player requires a player_id.")
            controller.add_player_between_turns(step.player_id)
            return None

        if step.action == "remove_player":
            if step.player_id is None:
                raise ValueError("remove_player requires a player_id.")
            controller.remove_player_between_turns(step.player_id)
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

        return patch.object(battle_structure_module.random, "shuffle", fixed_shuffle)


class _NullContext:
    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False
