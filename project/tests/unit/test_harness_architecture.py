import shutil
from pathlib import Path

from harness import (
    GUIHarnessReport,
    GUIHarnessRunConfig,
    GUIHarnessRunner,
    GUIVisibleState,
)


class _DummyScenarioSource:
    def load(self, scenario_path: Path) -> dict[str, object]:
        return {
            "metadata": {"id": "dummy"},
            "steps": [],
            "path": str(scenario_path),
        }


class _DummyDriver:
    def launch(self) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def click(self, target: str) -> None:
        return None

    def type_text(self, target: str, value: str, *, replace: bool = True) -> None:
        return None

    def press_key(self, target: str | None, key: str) -> None:
        return None

    def select_option(self, target: str, value: str) -> None:
        return None

    def select_suggestion(self, target: str, value: str) -> None:
        return None

    def capture_screenshot(self, destination: Path) -> Path:
        return destination


class _DummyObserver:
    def read_visible_state(self, driver: _DummyDriver) -> GUIVisibleState:
        return GUIVisibleState(active_view="setup")


class _DummyOracleEngine:
    def evaluate_step(self, *, scenario, step, visible_state) -> None:
        return None


class _DummyReporter:
    def build_failure_payload(
        self,
        *,
        scenario,
        executed_steps,
        visible_state,
        error,
        screenshot_path,
    ) -> dict[str, object]:
        return {"error": str(error)}

    def finalize(
        self,
        *,
        scenario,
        executed_steps,
        success,
        debug_payload,
    ) -> GUIHarnessReport:
        scenario_id = str(scenario.get("metadata", {}).get("id", "unknown"))
        return GUIHarnessReport(
            scenario_id=scenario_id,
            success=success,
            debug_payload=debug_payload,
        )


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "harness_architecture"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_harness_runner_architecture_executes_empty_scenario() -> None:
    case_dir = _make_case_dir("runner_empty")
    runner = GUIHarnessRunner(
        scenario_source=_DummyScenarioSource(),
        driver=_DummyDriver(),
        observer=_DummyObserver(),
        oracle_engine=_DummyOracleEngine(),
        reporter=_DummyReporter(),
        run_config=GUIHarnessRunConfig(),
    )

    report = runner.run(case_dir / "dummy.yaml")

    assert report.scenario_id == "dummy"
    assert report.success is True
    assert report.debug_payload["status"] == "ok"
    assert report.debug_payload["limits"]["max_steps"] == 200
