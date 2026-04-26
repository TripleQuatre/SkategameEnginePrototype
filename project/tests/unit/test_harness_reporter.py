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
                "state_delta": {"view_changed": False},
            }
        ],
        visible_state=visible_state,
        error=error,
        screenshot_path=Path("artifacts/failure.txt"),
        scenario_path=Path("harness/scenarios/stress/example.yaml"),
    )

    assert payload["scenario"]["id"] == "smoke_match"
    assert payload["scenario"]["tags"] == ["smoke", "gui"]
    assert payload["scenario"]["family"] == "stress"
    assert payload["scenario"]["scenario_path"] == "harness/scenarios/stress/example.yaml"
    assert payload["scenario"]["step_count"] == 0
    assert payload["failed_step"]["name"] == "type trick"
    assert payload["failure"]["expected"] == "Soul Switch"
    assert payload["failure"]["observed"] == ("Soul",)
    assert payload["failure"]["screenshot_path"] == "artifacts/failure.txt"
    assert payload["visible_state"]["active_view"] == "match"
    assert payload["visible_highlights"]["match.phase_title_label"] == "Stan sets the next trick"
    assert payload["visible_highlights"]["key_button_states"]["match.confirm_trick_button"] == "disabled"
    assert payload["visible_state"]["table_rows"]["history.tree"] == [["1", "Stan"]]
    assert payload["steps"][0]["observed_summary"] == "view=match"
    assert payload["steps"][0]["state_delta"] == {"view_changed": False}
    assert payload["steps"][0]["visible_highlights"]["match.phase_title_label"] == "Stan sets the next trick"


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
                "state_delta": {"view_changed": False},
            }
        ],
        success=True,
        debug_payload={"status": "ok", "scenario": {"setup": {"mode": "preset"}}},
    )

    assert report.scenario_id == "setup_smoke"
    assert report.success is True
    assert report.failure is None
    assert len(report.steps) == 1
    assert report.steps[0].name == "launch app"
    assert report.steps[0].visible_state == visible_state


def test_structured_harness_reporter_summarizes_setup_context() -> None:
    reporter = StructuredGUIHarnessReporter()

    summary = reporter.scenario_summary(
        {
            "metadata": {
                "id": "stress_case",
                "title": "Stress case",
                "tags": ["stress", "roster"],
            },
            "setup": {
                "mode": "preset",
                "preset": "battle_balanced_v9_3",
                "players": ["Stan", "Denise", "Alex"],
                "repetition_mode": "common",
                "repetition_limit": 2,
            },
        },
        scenario_path=Path("harness/scenarios/stress/example.yaml"),
    )

    assert summary["setup"] == {
        "mode": "preset",
        "preset": "battle_balanced_v9_3",
        "players": ["Stan", "Denise", "Alex"],
        "repetition_mode": "common",
        "repetition_limit": 2,
    }
    assert summary["family"] == "stress"
    assert summary["scenario_path"] == "harness/scenarios/stress/example.yaml"
    assert summary["step_count"] == 0


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


def test_structured_harness_reporter_builds_setup_details_and_history_highlights() -> None:
    reporter = StructuredGUIHarnessReporter()

    setup_details_state = GUIVisibleState(
        active_view="setup_details",
        status_text="Viewing setup details.",
        texts={
            "setup_details.body_label": (
                "Preset: custom\n"
                "Structure: battle\n"
                "Sport: inline\n"
                "Players: Stan, Denise, Alex\n"
                "Profiles: stan, denise, alex\n"
                "Order: relevance (age)\n"
                "Base order: Alex, Stan, Denise\n"
                "Word: BLADE\n"
                "Attack attempts: 2"
            )
        },
    )
    history_state = GUIVisibleState(
        active_view="history",
        status_text="Viewing history.",
        table_rows={
            "history.tree": (
                ("1", "Stan", "Soul", "V"),
                ("2", "Denise", "Makio", "X"),
            )
        },
    )

    setup_details_highlights = reporter.visible_highlights(setup_details_state)
    history_highlights = reporter.visible_highlights(history_state)

    assert setup_details_highlights is not None
    assert setup_details_highlights["setup_details_excerpt"][:3] == [
        "Preset: custom",
        "Structure: battle",
        "Sport: inline",
    ]
    assert history_highlights is not None
    assert history_highlights["history_row_count"] == 2
    assert history_highlights["history_first_row"] == ["1", "Stan", "Soul", "V"]
