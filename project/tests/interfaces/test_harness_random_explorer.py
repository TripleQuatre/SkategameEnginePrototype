from pathlib import Path
import shutil
import tkinter as tk

import pytest

from harness import (
    BoundedRandomScenarioBuilder,
    GUIHarnessRunner,
    GUIHarnessRunConfig,
    GUIHarnessRunLimits,
    GUIOracleEngine,
    StructuredGUIHarnessReporter,
    TkGUIHarnessDriver,
    TkGUIHarnessObserver,
    YAMLScenarioSource,
)
from harness.cli import main
from interfaces.gui.gui_app import GUIApp


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "harness_random"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


@pytest.fixture
def random_runner(monkeypatch) -> GUIHarnessRunner:
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showinfo",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showerror",
        lambda *args, **kwargs: None,
    )

    saves_dir = _make_case_dir("runner_saves") / "saves"
    saves_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(GUIApp, "SAVES_DIR", saves_dir)

    return GUIHarnessRunner(
        scenario_source=YAMLScenarioSource(),
        driver=TkGUIHarnessDriver(withdraw_on_launch=True),
        observer=TkGUIHarnessObserver(),
        oracle_engine=GUIOracleEngine(),
        reporter=StructuredGUIHarnessReporter(),
        run_config=GUIHarnessRunConfig(
            limits=GUIHarnessRunLimits(max_steps=20, timeout_seconds=10.0),
        ),
    )


def test_bounded_random_scenario_builder_is_reproducible() -> None:
    first = BoundedRandomScenarioBuilder(seed=42, max_steps=20).build()
    second = BoundedRandomScenarioBuilder(seed=42, max_steps=20).build()
    third = BoundedRandomScenarioBuilder(seed=43, max_steps=20).build()

    assert first == second
    assert first != third
    assert first["metadata"]["seed"] == 42
    assert len(first["steps"]) <= 20


def test_bounded_random_scenario_builder_respects_small_max_steps() -> None:
    scenario = BoundedRandomScenarioBuilder(seed=7, max_steps=6).build()

    assert len(scenario["steps"]) <= 6
    assert scenario["steps"][0]["action"] == "launch_app"
    assert scenario["steps"][-1]["action"] == "shutdown_app"


def test_bounded_random_scenario_runs_through_harness(
    random_runner: GUIHarnessRunner,
) -> None:
    scenario = BoundedRandomScenarioBuilder(seed=3, max_steps=18).build()

    try:
        report = random_runner.run_scenario(scenario)
    except tk.TclError as error:
        pytest.skip(f"Tk GUI is unavailable in this environment: {error}")

    assert report.success is True, report.debug_payload
    assert report.scenario_id == "random_bounded_seed_3"
    assert report.debug_payload["seed"] == 3
    assert len(report.debug_payload["sequence"]) == len(report.steps)


def test_harness_cli_runs_bounded_random_scenario(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showinfo",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showerror",
        lambda *args, **kwargs: None,
    )
    case_dir = _make_case_dir("cli_random")

    try:
        exit_code = main(
            [
                "--random-bounded",
                "--seed",
                "5",
                "--max-random-steps",
                "18",
                "--saves-dir",
                str(case_dir / "saves"),
            ]
        )
    except tk.TclError as error:
        pytest.skip(f"Tk GUI is unavailable in this environment: {error}")

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[PASS] random_bounded_seed_5" in captured.out
    assert "sequence_length:" in captured.out
