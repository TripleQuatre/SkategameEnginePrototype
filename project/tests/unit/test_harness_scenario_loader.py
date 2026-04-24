import shutil
from pathlib import Path

import pytest

from harness import ScenarioValidationError, YAMLScenarioSource, load_yaml_subset


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "harness_scenarios"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_yaml_subset_parser_supports_nested_scenario_shapes() -> None:
    parsed = load_yaml_subset(
        """
metadata:
  id: smoke_custom
  tags:
    - smoke
    - custom
setup:
  mode: custom
  players:
    - Stan
    - Denise
steps:
  - name: launch app
    action: launch_app
    expect:
      view: setup
  - name: start game
    action: click
    target: setup.start_game_button
    expect:
      view: match
      dropdown_contains:
        - Soul Switch
"""
    )

    assert parsed["metadata"]["id"] == "smoke_custom"
    assert parsed["metadata"]["tags"] == ["smoke", "custom"]
    assert parsed["setup"]["players"] == ["Stan", "Denise"]
    assert parsed["steps"][1]["expect"]["dropdown_contains"] == ["Soul Switch"]


def test_yaml_scenario_source_loads_valid_scenario() -> None:
    case_dir = _make_case_dir("valid_load")
    scenario_path = case_dir / "smoke.yaml"
    scenario_path.write_text(
        """
metadata:
  id: smoke_custom_one_vs_one
  title: Custom one versus one smoke flow
setup:
  mode: custom
  players:
    - Stan
    - Denise
  word: SKATE
steps:
  - name: launch app
    action: launch_app
    expect:
      view: setup
  - name: start game
    action: click
    target: setup.start_game_button
    expect:
      view: match
""".strip(),
        encoding="utf-8",
    )

    source = YAMLScenarioSource()
    scenario = source.load(scenario_path)

    assert scenario["metadata"]["id"] == "smoke_custom_one_vs_one"
    assert scenario["steps"][1]["target"] == "setup.start_game_button"


def test_yaml_scenario_source_rejects_unknown_action() -> None:
    case_dir = _make_case_dir("invalid_action")
    scenario_path = case_dir / "invalid.yaml"
    scenario_path.write_text(
        """
metadata:
  id: invalid_action
setup:
  players:
    - Stan
    - Denise
steps:
  - name: invalid
    action: teleport
""".strip(),
        encoding="utf-8",
    )

    source = YAMLScenarioSource()

    with pytest.raises(ScenarioValidationError) as error:
        source.load(scenario_path)

    assert "unsupported action 'teleport'" in str(error.value)


def test_yaml_scenario_source_requires_step_targets_when_needed() -> None:
    case_dir = _make_case_dir("missing_target")
    scenario_path = case_dir / "missing_target.yaml"
    scenario_path.write_text(
        """
metadata:
  id: missing_target
setup:
  players:
    - Stan
    - Denise
steps:
  - name: click start
    action: click
""".strip(),
        encoding="utf-8",
    )

    source = YAMLScenarioSource()

    with pytest.raises(ScenarioValidationError) as error:
        source.load(scenario_path)

    assert "requires a non-empty target" in str(error.value)


def test_yaml_scenario_source_rejects_invalid_setup_mode_and_repetition_mode() -> None:
    case_dir = _make_case_dir("invalid_setup_values")
    scenario_path = case_dir / "invalid_setup.yaml"
    scenario_path.write_text(
        """
metadata:
  id: invalid_setup_values
setup:
  mode: arcade
  repetition_mode: loop
  players:
    - Stan
    - Denise
steps:
  - name: launch app
    action: launch_app
""".strip(),
        encoding="utf-8",
    )

    source = YAMLScenarioSource()

    with pytest.raises(ScenarioValidationError) as error:
        source.load(scenario_path)

    assert "setup.mode must be one of: custom, preset." in str(error.value)


def test_yaml_scenario_source_rejects_invalid_expected_view() -> None:
    case_dir = _make_case_dir("invalid_expect_view")
    scenario_path = case_dir / "invalid_expect_view.yaml"
    scenario_path.write_text(
        """
metadata:
  id: invalid_expect_view
setup:
  mode: custom
  players:
    - Stan
    - Denise
steps:
  - name: launch app
    action: launch_app
    expect:
      view: overlay
""".strip(),
        encoding="utf-8",
    )

    source = YAMLScenarioSource()

    with pytest.raises(ScenarioValidationError) as error:
        source.load(scenario_path)

    assert "must be one of: history, match, setup, setup_details" in str(error.value)
