from pathlib import Path
import shutil
import tkinter as tk

import pytest

from harness.cli import (
    REFERENCE_SCENARIOS_DIR,
    _parse_args,
    discover_reference_scenarios,
    main,
)


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "harness_cli"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_harness_cli_discovers_reference_scenarios() -> None:
    scenarios = discover_reference_scenarios()

    assert len(scenarios) == 9
    assert all(path.parent == REFERENCE_SCENARIOS_DIR for path in scenarios)
    assert {path.name for path in scenarios} == {
        "attack_repetition_synergy_smoke.yaml",
        "custom_battle_smoke.yaml",
        "history_and_setup_details_navigation.yaml",
        "multiple_attack_enabled_smoke.yaml",
        "preset_one_vs_one_smoke.yaml",
        "relevance_order_setup_details_smoke.yaml",
        "save_smoke.yaml",
        "switch_enabled_smoke.yaml",
        "undo_to_setup_regression.yaml",
    }


def test_harness_cli_parse_single_scenario_mode() -> None:
    args = _parse_args(["--scenario", "harness/scenarios/reference/save_smoke.yaml"])

    assert args.scenario == Path("harness/scenarios/reference/save_smoke.yaml")
    assert args.reference_suite is False
    assert args.show_window is False


def test_harness_cli_runs_single_reference_scenario(capsys) -> None:
    scenario_path = REFERENCE_SCENARIOS_DIR / "preset_one_vs_one_smoke.yaml"
    case_dir = _make_case_dir("single_reference_scenario")

    try:
        exit_code = main(
            [
                "--scenario",
                str(scenario_path),
                "--saves-dir",
                str(case_dir / "saves"),
            ]
        )
    except tk.TclError as error:
        pytest.skip(f"Tk GUI is unavailable in this environment: {error}")

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[PASS] preset_one_vs_one_smoke" in captured.out
