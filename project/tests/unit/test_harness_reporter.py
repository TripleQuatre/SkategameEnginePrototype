from pathlib import Path

from harness import GUIOracleError, GUIVisibleState, StructuredGUIHarnessReporter


def test_structured_harness_reporter_builds_failure_payload() -> None:
    reporter = StructuredGUIHarnessReporter()
    scenario = {
        "metadata": {
            "id": "smoke_match",
            "title": "Smoke match",
            "tags": ["smoke", "gui"],
        }
    }
    visible_state = GUIVisibleState(
        active_view="match",
        status_text="Invalid trick input.",
        button_states={"match.confirm_trick_button": "disabled"},
        texts={"match.phase_title_label": "Stan sets the next trick"},
        score_cells={"1,0": "STAN"},
        table_rows={"history.tree": (("1", "Stan"),)},
        dropdown_items=("Soul",),
    )
    error = GUIOracleError(
        "Dropdown does not contain expected item.",
        expected="Soul Switch",
        observed=("Soul",),
    )

    payload = reporter.build_failure_payload(
        scenario=scenario,
        executed_steps=[
            {
                "index": 1,
                "step": {"name": "type trick", "action": "type"},
                "observed_summary": "view=match",
                "visible_state": visible_state,
            }
        ],
        visible_state=visible_state,
        error=error,
        screenshot_path=Path("artifacts/failure.txt"),
    )

    assert payload["scenario"]["id"] == "smoke_match"
    assert payload["scenario"]["tags"] == ["smoke", "gui"]
    assert payload["failure"]["expected"] == "Soul Switch"
    assert payload["failure"]["observed"] == ("Soul",)
    assert payload["failure"]["screenshot_path"] == "artifacts/failure.txt"
    assert payload["visible_state"]["active_view"] == "match"
    assert payload["visible_state"]["table_rows"]["history.tree"] == [["1", "Stan"]]
    assert payload["steps"][0]["observed_summary"] == "view=match"


def test_structured_harness_reporter_finalizes_success_report() -> None:
    reporter = StructuredGUIHarnessReporter()
    visible_state = GUIVisibleState(active_view="setup")

    report = reporter.finalize(
        scenario={"metadata": {"id": "setup_smoke"}},
        executed_steps=[
            {
                "index": 1,
                "step": {"name": "launch app", "action": "launch_app"},
                "observed_summary": "view=setup",
                "visible_state": visible_state,
            }
        ],
        success=True,
        debug_payload={"status": "ok"},
    )

    assert report.scenario_id == "setup_smoke"
    assert report.success is True
    assert report.failure is None
    assert len(report.steps) == 1
    assert report.steps[0].name == "launch app"
    assert report.steps[0].visible_state == visible_state


def test_structured_harness_reporter_finalizes_failure_report() -> None:
    reporter = StructuredGUIHarnessReporter()
    debug_payload = {
        "failure": {
            "message": "Active view does not match.",
            "expected": "setup",
            "observed": "match",
            "screenshot_path": "artifacts/failure.txt",
        }
    }

    report = reporter.finalize(
        scenario={"metadata": {"id": "view_failure"}},
        executed_steps=[
            {
                "index": 2,
                "step": {"name": "expect setup", "action": "click"},
            }
        ],
        success=False,
        debug_payload=debug_payload,
    )

    assert report.success is False
    assert report.failure is not None
    assert report.failure.step_index == 2
    assert report.failure.step_name == "expect setup"
    assert report.failure.expected == "setup"
    assert report.failure.observed == "match"
    assert report.failure.screenshot_path == Path("artifacts/failure.txt")
