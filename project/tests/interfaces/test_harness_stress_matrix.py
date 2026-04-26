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
    build_stress_matrix_scenario,
    discover_stress_matrix_cases,
)
from interfaces.gui.gui_app import GUIApp


def _make_case_dir(case_id: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "harness_stress_matrix"
        / case_id
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_stress_matrix_cases_exist() -> None:
    case_ids = {case.case_id for case in discover_stress_matrix_cases()}

    assert case_ids == {
        "battle_multi_no_repetition_roster_navigation__battle_multi_no_rep_v10_1",
        "consultation_undo__duel_short_strict_v9_3",
        "load_engaged_turn__classic_skate_v8",
        "load_engaged_turn__duel_synergy_strict_v10_1",
        "load_engaged_turn__duel_verified_switch_v10_1",
        "load_engaged_turn__duel_long_open_v9_3",
        "mixed_save_load_roster__battle_long_open_v9_3",
        "roster_transition_roundtrip__battle_balanced_v9_3",
        "undo_chain_recovery__classic_skate_v8",
        "undo_chain_recovery__duel_synergy_strict_v10_1",
        "undo_chain_recovery__duel_verified_switch_v10_1",
        "verified_switch_navigation_new_game__duel_verified_switch_v10_1",
    }


@pytest.mark.parametrize(
    "case",
    discover_stress_matrix_cases(),
    ids=lambda case: case.case_id,
)
def test_harness_runner_executes_stress_matrix_case(monkeypatch, case) -> None:
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showinfo",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "interfaces.gui.gui_app.messagebox.showerror",
        lambda *args, **kwargs: None,
    )

    saves_dir = _make_case_dir(case.case_id) / "saves"
    saves_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(GUIApp, "SAVES_DIR", saves_dir)

    runner = GUIHarnessRunner(
        scenario_source=YAMLScenarioSource(),
        driver=TkGUIHarnessDriver(withdraw_on_launch=True),
        observer=TkGUIHarnessObserver(),
        oracle_engine=GUIOracleEngine(),
        reporter=StructuredGUIHarnessReporter(),
    )
    scenario = build_stress_matrix_scenario(case, scenario_source=YAMLScenarioSource())

    try:
        report = runner.run_scenario(scenario, scenario_path=case.scenario_path)
    except tk.TclError as error:
        pytest.skip(f"Tk GUI is unavailable in this environment: {error}")

    assert report.success is True, report.debug_payload
    assert report.failure is None
    assert report.steps
    assert report.scenario_id == case.case_id
