from pathlib import Path
import time
from typing import Any

from harness.contracts import (
    GUIHarnessDriver,
    GUIHarnessObserver,
    GUIHarnessOracleEngine,
    GUIHarnessReporter,
    GUIHarnessScenarioSource,
)
from harness.models import GUIHarnessReport, GUIHarnessRunConfig, GUIVisibleState


class GUIHarnessRunner:
    def __init__(
        self,
        *,
        scenario_source: GUIHarnessScenarioSource,
        driver: GUIHarnessDriver,
        observer: GUIHarnessObserver,
        oracle_engine: GUIHarnessOracleEngine,
        reporter: GUIHarnessReporter,
        run_config: GUIHarnessRunConfig | None = None,
    ) -> None:
        self.scenario_source = scenario_source
        self.driver = driver
        self.observer = observer
        self.oracle_engine = oracle_engine
        self.reporter = reporter
        self.run_config = run_config or GUIHarnessRunConfig()

    def run(self, scenario_path: Path) -> GUIHarnessReport:
        scenario = self.scenario_source.load(scenario_path)
        return self.run_scenario(scenario, scenario_path=scenario_path)

    def run_scenario(
        self,
        scenario: dict[str, Any],
        *,
        scenario_path: Path | None = None,
    ) -> GUIHarnessReport:
        steps = scenario.get("steps") or []
        executed_steps: list[dict[str, Any]] = []
        started_at = time.monotonic()

        try:
            if len(steps) > self.run_config.limits.max_steps:
                raise RuntimeError(
                    "Scenario exceeds max_steps "
                    f"({len(steps)} > {self.run_config.limits.max_steps})."
                )

            for index, step in enumerate(steps, start=1):
                elapsed = time.monotonic() - started_at
                if elapsed > self.run_config.limits.timeout_seconds:
                    raise RuntimeError(
                        "Scenario exceeded timeout_seconds "
                        f"({elapsed:.2f} > {self.run_config.limits.timeout_seconds})."
                    )

                self._execute_step_action(step)
                visible_state = self._read_visible_state_or_none()

                if step.get("expect"):
                    if visible_state is None:
                        raise RuntimeError(
                            f"Step {index} defines expectations but no GUI state is readable."
                        )
                    self.oracle_engine.evaluate_step(
                        scenario=scenario,
                        step=step,
                        visible_state=visible_state,
                    )

                executed_steps.append(
                    {
                        "index": index,
                        "step": step,
                        "observed_summary": self._summarize_visible_state(visible_state),
                        "visible_state": visible_state,
                    }
                )
        except Exception as error:
            visible_state = self._read_visible_state_or_none()
            screenshot_path = self._capture_failure_screenshot(
                scenario=scenario,
                step_index=len(executed_steps) + 1,
            )
            failed_steps = executed_steps + [
                {
                    "index": len(executed_steps) + 1,
                    "step": steps[len(executed_steps)] if len(executed_steps) < len(steps) else {},
                    "observed_summary": self._summarize_visible_state(visible_state),
                    "visible_state": visible_state,
                }
            ]
            debug_payload = self.reporter.build_failure_payload(
                scenario=scenario,
                executed_steps=failed_steps,
                visible_state=visible_state,
                error=error,
                screenshot_path=screenshot_path,
            )
            report = self.reporter.finalize(
                scenario=scenario,
                executed_steps=failed_steps,
                success=False,
                debug_payload=debug_payload,
            )
            try:
                self.driver.shutdown()
            except Exception:
                pass
            return report

        return self.reporter.finalize(
            scenario=scenario,
            executed_steps=executed_steps,
            success=True,
            debug_payload={
                "status": "ok",
                "scenario_path": scenario_path.as_posix() if scenario_path else None,
                "limits": {
                    "max_steps": self.run_config.limits.max_steps,
                    "timeout_seconds": self.run_config.limits.timeout_seconds,
                },
                "seed": (scenario.get("metadata") or {}).get("seed"),
                "sequence": [
                    self._step_sequence_payload(executed_step)
                    for executed_step in executed_steps
                ],
            },
        )

    def _execute_step_action(self, step: dict[str, Any]) -> None:
        action = step.get("action")

        if action == "launch_app":
            self.driver.launch()
            return
        if action == "shutdown_app":
            self.driver.shutdown()
            return
        if action == "click":
            self.driver.click(step["target"])
            return
        if action == "type":
            self.driver.type_text(step["target"], step["value"])
            return
        if action == "press_key":
            self.driver.press_key(step.get("target"), step["key"])
            return
        if action == "select_option":
            self.driver.select_option(step["target"], step["value"])
            return
        if action == "select_suggestion":
            self.driver.select_suggestion(step["target"], step["value"])
            return

        raise RuntimeError(f"Unsupported runner action: {action}")

    def _read_visible_state_or_none(self) -> GUIVisibleState | None:
        try:
            return self.observer.read_visible_state(self.driver)
        except Exception:
            return None

    def _summarize_visible_state(self, visible_state: GUIVisibleState | None) -> str | None:
        if visible_state is None:
            return None
        return (
            f"view={visible_state.active_view}; "
            f"status={visible_state.status_text!r}; "
            f"buttons={len(visible_state.button_states)}; "
            f"texts={len(visible_state.texts)}"
        )

    def _step_sequence_payload(self, executed_step: dict[str, Any]) -> dict[str, Any]:
        step = executed_step.get("step") or executed_step
        return {
            "index": executed_step.get("index"),
            "name": step.get("name"),
            "action": step.get("action"),
            "target": step.get("target"),
            "value": step.get("value"),
            "key": step.get("key"),
            "observed_summary": executed_step.get("observed_summary"),
        }

    def _capture_failure_screenshot(
        self,
        *,
        scenario: dict[str, Any],
        step_index: int,
    ) -> Path | None:
        if not self.run_config.capture_on_failure:
            return None

        metadata = scenario.get("metadata") or {}
        scenario_id = metadata.get("id") if isinstance(metadata.get("id"), str) else "scenario"
        destination = (
            Path("local_tmp")
            / "harness_artifacts"
            / f"{scenario_id}_step_{step_index}.txt"
        )
        try:
            return self.driver.capture_screenshot(destination)
        except Exception:
            return None
