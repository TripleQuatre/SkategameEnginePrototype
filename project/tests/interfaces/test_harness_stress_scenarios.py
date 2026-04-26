from pathlib import Path
import shutil
import tkinter as tk

import pytest

from harness import (
    GUIHarnessRunner,
    GUIOracleEngine,
    StructuredGUIHarnessReporter,
    TkGUIHarnessDriver,
    TkGUIHarnessObserver,
    YAMLScenarioSource,
)
from interfaces.gui.gui_app import GUIApp


STRESS_SCENARIOS_DIR = (
    Path(__file__).resolve().parents[2]
    / "harness"
    / "scenarios"
    / "stress"
)


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "harness_stress_scenarios"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _stress_scenarios() -> list[Path]:
    return sorted(STRESS_SCENARIOS_DIR.glob("*.yaml"))


def test_stress_scenarios_exist() -> None:
    scenario_names = {path.name for path in _stress_scenarios()}

    assert scenario_names == {
        "battle_multi_no_repetition_roster_navigation_stress.yaml",
        "consultation_undo_stress.yaml",
        "load_engaged_turn_stress.yaml",
        "mixed_save_load_roster_stress.yaml",
        "multiple_attack_navigation_return_setup_stress.yaml",
        "multiple_attack_no_repetition_load_undo_stress.yaml",
        "random_order_navigation_persistence_stress.yaml",
        "relevance_battle_persistence_stress.yaml",
        "roster_transition_roundtrip_stress.yaml",
        "switch_normal_unlock_persistence_stress.yaml",
        "undo_chain_recovery_stress.yaml",
        "verified_switch_navigation_new_game_stress.yaml",
        "verified_switch_save_load_undo_stress.yaml",
    }


@pytest.mark.parametrize("scenario_path", _stress_scenarios(), ids=lambda path: path.stem)
def test_harness_runner_executes_stress_scenario(
    monkeypatch,
    scenario_path: Path,
) -> None:
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showinfo",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showerror",
        lambda *args, **kwargs: None,
    )

    saves_dir = _make_case_dir(scenario_path.stem) / "saves"
    saves_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(GUIApp, "SAVES_DIR", saves_dir)

    runner = GUIHarnessRunner(
        scenario_source=YAMLScenarioSource(),
        driver=TkGUIHarnessDriver(withdraw_on_launch=True),
        observer=TkGUIHarnessObserver(),
        oracle_engine=GUIOracleEngine(),
        reporter=StructuredGUIHarnessReporter(),
    )

    try:
        report = runner.run(scenario_path)
    except tk.TclError as error:
        pytest.skip(f"Tk GUI is unavailable in this environment: {error}")

    assert report.success is True, report.debug_payload
    assert report.failure is None
    assert report.steps
    assert report.scenario_id == scenario_path.stem
