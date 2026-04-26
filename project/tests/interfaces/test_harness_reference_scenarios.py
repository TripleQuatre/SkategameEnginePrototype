from pathlib import Path
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


REFERENCE_SCENARIOS_DIR = (
    Path(__file__).resolve().parents[2]
    / "harness"
    / "scenarios"
    / "reference"
)


@pytest.fixture
def reference_runner(monkeypatch) -> GUIHarnessRunner:
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showinfo",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showerror",
        lambda *args, **kwargs: None,
    )

    saves_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "harness_reference_saves"
    )
    saves_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(GUIApp, "SAVES_DIR", saves_dir)

    driver = TkGUIHarnessDriver(withdraw_on_launch=True)
    return GUIHarnessRunner(
        scenario_source=YAMLScenarioSource(),
        driver=driver,
        observer=TkGUIHarnessObserver(),
        oracle_engine=GUIOracleEngine(),
        reporter=StructuredGUIHarnessReporter(),
    )


def _reference_scenarios() -> list[Path]:
    return sorted(REFERENCE_SCENARIOS_DIR.glob("*.yaml"))


def test_reference_scenarios_exist() -> None:
    scenario_names = {path.name for path in _reference_scenarios()}

    assert scenario_names == {
        "attack_repetition_multiple_attack_interaction_smoke.yaml",
        "attack_repetition_synergy_smoke.yaml",
        "choice_order_profiles_smoke.yaml",
        "custom_battle_smoke.yaml",
        "history_and_setup_details_navigation.yaml",
        "multiple_attack_enabled_smoke.yaml",
        "no_repetition_long_attack_chain_smoke.yaml",
        "preset_one_vs_one_smoke.yaml",
        "relevance_order_setup_details_smoke.yaml",
        "save_smoke.yaml",
        "switch_enabled_smoke.yaml",
        "switch_uniqueness_interaction_smoke.yaml",
        "undo_to_setup_regression.yaml",
    }


@pytest.mark.parametrize("scenario_path", _reference_scenarios(), ids=lambda path: path.stem)
def test_harness_runner_executes_reference_scenario(
    reference_runner: GUIHarnessRunner,
    scenario_path: Path,
) -> None:
    try:
        report = reference_runner.run(scenario_path)
    except tk.TclError as error:
        pytest.skip(f"Tk GUI is unavailable in this environment: {error}")

    assert report.success is True, report.debug_payload
    assert report.failure is None
    assert report.steps
    assert report.scenario_id == scenario_path.stem
