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
    def __init__(self) -> None:
        self.launch_calls = 0
        self.shutdown_calls = 0

    def launch(self) -> None:
        self.launch_calls += 1

    def shutdown(self) -> None:
        self.shutdown_calls += 1

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


class _FailingObserver:
    def read_visible_state(self, driver: _DummyDriver) -> GUIVisibleState:
        raise ValueError("observer exploded")


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
        scenario_path=None,
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
    driver = _DummyDriver()
    runner = GUIHarnessRunner(
        scenario_source=_DummyScenarioSource(),
        driver=driver,
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
    assert driver.shutdown_calls == 1


def test_harness_runner_architecture_fails_when_observer_crashes() -> None:
    class _StepScenarioSource:
        def load(self, scenario_path: Path) -> dict[str, object]:
            return {
                "metadata": {"id": "observer_failure"},
                "steps": [
                    {
                        "name": "launch app",
                        "action": "launch_app",
                    }
                ],
            }

    case_dir = _make_case_dir("runner_observer_failure")
    driver = _DummyDriver()
    runner = GUIHarnessRunner(
        scenario_source=_StepScenarioSource(),
        driver=driver,
        observer=_FailingObserver(),
        oracle_engine=_DummyOracleEngine(),
        reporter=_DummyReporter(),
        run_config=GUIHarnessRunConfig(),
    )

    report = runner.run(case_dir / "dummy.yaml")

    assert report.scenario_id == "observer_failure"
    assert report.success is False
    assert report.debug_payload["error"] == "observer exploded"
    assert driver.shutdown_calls == 1


def test_harness_runner_architecture_shuts_down_driver_after_successful_launch() -> None:
    class _LaunchScenarioSource:
        def load(self, scenario_path: Path) -> dict[str, object]:
            return {
                "metadata": {"id": "launch_then_shutdown"},
                "steps": [
                    {
                        "name": "launch app",
                        "action": "launch_app",
                    }
                ],
            }

    case_dir = _make_case_dir("runner_launch_shutdown")
    driver = _DummyDriver()
    runner = GUIHarnessRunner(
        scenario_source=_LaunchScenarioSource(),
        driver=driver,
        observer=_DummyObserver(),
        oracle_engine=_DummyOracleEngine(),
        reporter=_DummyReporter(),
        run_config=GUIHarnessRunConfig(),
    )

    report = runner.run(case_dir / "dummy.yaml")

    assert report.success is True
    assert driver.launch_calls == 1
    assert driver.shutdown_calls == 1
