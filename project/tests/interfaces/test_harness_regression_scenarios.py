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


REGRESSION_SCENARIOS_DIR = (
    Path(__file__).resolve().parents[2]
    / "harness"
    / "scenarios"
    / "regression"
)


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "harness_regression_scenarios"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _regression_scenarios() -> list[Path]:
    return sorted(REGRESSION_SCENARIOS_DIR.glob("*.yaml"))


def test_regression_scenarios_exist() -> None:
    scenario_names = {path.name for path in _regression_scenarios()}

    assert scenario_names == {
        "consultation_undo_restores_engaged_turn_regression.yaml",
        "deep_undo_restores_trick_input_regression.yaml",
        "load_restores_engaged_turn_controls_regression.yaml",
        "player_count_rebuilds_fields_regression.yaml",
    }


@pytest.mark.parametrize("scenario_path", _regression_scenarios(), ids=lambda path: path.stem)
def test_harness_runner_executes_regression_scenario(
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
