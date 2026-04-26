from pathlib import Path
from typing import Any

from harness.yaml_subset import YAMLSubsetError, load_yaml_subset


class ScenarioValidationError(ValueError):
    pass


class YAMLScenarioSource:
    ALLOWED_SETUP_MODES = {"preset", "custom"}
    ALLOWED_STRUCTURES = {"one_vs_one", "battle"}
    ALLOWED_REPETITION_MODES = {"choice", "common", "disabled"}
    ALLOWED_VIEWS = {"setup", "match", "history", "setup_details"}
    ALLOWED_METADATA_KEYS = {"id", "title", "tags"}
    ALLOWED_SETUP_KEYS = {
        "mode",
        "preset",
        "structure",
        "players",
        "word",
        "attack_attempts",
        "defense_attempts",
        "uniqueness",
        "repetition_mode",
        "repetition_limit",
    }
    ALLOWED_STEP_KEYS = {"name", "action", "target", "value", "key", "expect"}
    ALLOWED_ACTIONS = {
        "launch_app",
        "shutdown_app",
        "queue_prompt_response",
        "set_load_selection",
        "click",
        "type",
        "press_key",
        "select_option",
        "select_suggestion",
    }
    ALLOWED_EXPECT_KEYS = {
        "view",
        "status_text_equals",
        "status_text_contains",
        "button_states",
        "text_equals",
        "text_contains",
        "score_cells",
        "dropdown_contains",
        "dropdown_equals",
        "dropdown_empty",
    }

    def load(self, scenario_path: Path) -> dict[str, Any]:
        raw_text = scenario_path.read_text(encoding="utf-8")
        try:
            data = load_yaml_subset(raw_text)
        except YAMLSubsetError as error:
            raise ScenarioValidationError(str(error)) from error

        self._validate_scenario(data)
        return data

    def _validate_scenario(self, data: object) -> None:
        if not isinstance(data, dict):
            raise ScenarioValidationError("Scenario root must be a mapping.")

        metadata = data.get("metadata")
        setup = data.get("setup")
        steps = data.get("steps")

        if not isinstance(metadata, dict):
            raise ScenarioValidationError("Scenario must define a 'metadata' mapping.")
        if not isinstance(setup, dict):
            raise ScenarioValidationError("Scenario must define a 'setup' mapping.")
        if not isinstance(steps, list):
            raise ScenarioValidationError("Scenario must define a 'steps' list.")
        if not steps:
            raise ScenarioValidationError("Scenario 'steps' cannot be empty.")

        self._validate_metadata(metadata)
        self._validate_setup(setup)
        self._validate_steps(steps)

    def _validate_metadata(self, metadata: dict[str, Any]) -> None:
        unknown_keys = set(metadata) - self.ALLOWED_METADATA_KEYS
        if unknown_keys:
            raise ScenarioValidationError(
                f"Unknown metadata keys: {sorted(unknown_keys)}"
            )

        scenario_id = metadata.get("id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise ScenarioValidationError("metadata.id must be a non-empty string.")

        title = metadata.get("title")
        if title is not None and not isinstance(title, str):
            raise ScenarioValidationError("metadata.title must be a string.")

        tags = metadata.get("tags")
        if tags is not None:
            if not isinstance(tags, list) or not all(
                isinstance(tag, str) for tag in tags
            ):
                raise ScenarioValidationError("metadata.tags must be a list of strings.")

    def _validate_setup(self, setup: dict[str, Any]) -> None:
        unknown_keys = set(setup) - self.ALLOWED_SETUP_KEYS
        if unknown_keys:
            raise ScenarioValidationError(
                f"Unknown setup keys: {sorted(unknown_keys)}"
            )

        mode = setup.get("mode")
        if mode is not None and mode not in self.ALLOWED_SETUP_MODES:
            raise ScenarioValidationError(
                "setup.mode must be one of: custom, preset."
            )

        preset = setup.get("preset")
        if preset is not None and (not isinstance(preset, str) or not preset.strip()):
            raise ScenarioValidationError("setup.preset must be a non-empty string.")

        structure = setup.get("structure")
        if structure is not None and structure not in self.ALLOWED_STRUCTURES:
            raise ScenarioValidationError(
                "setup.structure must be one of: battle, one_vs_one."
            )

        players = setup.get("players")
        if players is not None:
            if not isinstance(players, list) or not all(
                isinstance(player, str) and player.strip() for player in players
            ):
                raise ScenarioValidationError("setup.players must be a list of names.")

        word = setup.get("word")
        if word is not None and (not isinstance(word, str) or not word.strip()):
            raise ScenarioValidationError("setup.word must be a non-empty string.")

        for int_key in ("attack_attempts", "defense_attempts", "repetition_limit"):
            value = setup.get(int_key)
            if value is not None:
                if not isinstance(value, int):
                    raise ScenarioValidationError(
                        f"setup.{int_key} must be an integer."
                    )
                if value < 1:
                    raise ScenarioValidationError(
                        f"setup.{int_key} must be greater than or equal to 1."
                    )

        uniqueness = setup.get("uniqueness")
        if uniqueness is not None and not isinstance(uniqueness, bool):
            raise ScenarioValidationError("setup.uniqueness must be a boolean.")

        repetition_mode = setup.get("repetition_mode")
        if (
            repetition_mode is not None
            and repetition_mode not in self.ALLOWED_REPETITION_MODES
        ):
            raise ScenarioValidationError(
                "setup.repetition_mode must be one of: choice, common, disabled."
            )

    def _validate_steps(self, steps: list[Any]) -> None:
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                raise ScenarioValidationError(
                    f"Step {index} must be a mapping, got {type(step).__name__}."
                )

            unknown_keys = set(step) - self.ALLOWED_STEP_KEYS
            if unknown_keys:
                raise ScenarioValidationError(
                    f"Unknown step keys at step {index}: {sorted(unknown_keys)}"
                )

            name = step.get("name")
            action = step.get("action")
            expect = step.get("expect", {})

            if not isinstance(name, str) or not name.strip():
                raise ScenarioValidationError(
                    f"Step {index} requires a non-empty string 'name'."
                )
            if action not in self.ALLOWED_ACTIONS:
                raise ScenarioValidationError(
                    f"Step {index} uses unsupported action '{action}'."
                )
            if expect is not None and not isinstance(expect, dict):
                raise ScenarioValidationError(f"Step {index} expect must be a mapping.")

            if action in {"click", "type", "press_key", "select_option", "select_suggestion"}:
                target = step.get("target")
                if not isinstance(target, str) or not target.strip():
                    raise ScenarioValidationError(
                        f"Step {index} action '{action}' requires a non-empty target."
                    )

            if action in {
                "type",
                "select_option",
                "select_suggestion",
                "queue_prompt_response",
                "set_load_selection",
            }:
                value = step.get("value")
                if not isinstance(value, str):
                    raise ScenarioValidationError(
                        f"Step {index} action '{action}' requires a string value."
                    )

            if action == "press_key":
                key = step.get("key")
                if not isinstance(key, str) or not key.strip():
                    raise ScenarioValidationError(
                        f"Step {index} action 'press_key' requires a non-empty key."
                    )

            self._validate_expectations(index, expect)

    def _validate_expectations(self, step_index: int, expect: dict[str, Any]) -> None:
        unknown_keys = set(expect) - self.ALLOWED_EXPECT_KEYS
        if unknown_keys:
            raise ScenarioValidationError(
                f"Unknown expectation keys at step {step_index}: {sorted(unknown_keys)}"
            )

        for string_key in ("view", "status_text_equals", "status_text_contains"):
            value = expect.get(string_key)
            if value is not None and not isinstance(value, str):
                raise ScenarioValidationError(
                    f"Expectation '{string_key}' at step {step_index} must be a string."
                )

        expected_view = expect.get("view")
        if expected_view is not None and expected_view not in self.ALLOWED_VIEWS:
            raise ScenarioValidationError(
                "Expectation 'view' at step "
                f"{step_index} must be one of: history, match, setup, setup_details."
            )

        for mapping_key in ("button_states", "text_equals", "text_contains", "score_cells"):
            value = expect.get(mapping_key)
            if value is not None:
                if not isinstance(value, dict) or not all(
                    isinstance(map_key, str) for map_key in value
                ):
                    raise ScenarioValidationError(
                        f"Expectation '{mapping_key}' at step {step_index} must be a mapping."
                    )

        for dropdown_key in ("dropdown_contains", "dropdown_equals"):
            dropdown_value = expect.get(dropdown_key)
            if dropdown_value is None:
                continue
            if not isinstance(dropdown_value, list) or not all(
                isinstance(item, str) for item in dropdown_value
            ):
                raise ScenarioValidationError(
                    f"Expectation '{dropdown_key}' at step {step_index} must be a list of strings."
                )

        dropdown_empty = expect.get("dropdown_empty")
        if dropdown_empty is not None and not isinstance(dropdown_empty, bool):
            raise ScenarioValidationError(
                f"Expectation 'dropdown_empty' at step {step_index} must be a boolean."
            )
