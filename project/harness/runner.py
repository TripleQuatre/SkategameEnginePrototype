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
        previous_visible_state: GUIVisibleState | None = None
        report: GUIHarnessReport | None = None

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

                if visible_state is None:
                    if step.get("expect"):
                        raise RuntimeError(
                            f"Step {index} defines expectations but no GUI state is readable."
                        )
                else:
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
                        "state_delta": self._summarize_state_delta(
                            previous_visible_state,
                            visible_state,
                        ),
                    }
                )
                previous_visible_state = visible_state
        except Exception as error:
            visible_state = self._read_visible_state_for_failure()
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
                    "state_delta": self._summarize_state_delta(
                        previous_visible_state,
                        visible_state,
                    ),
                }
            ]
            debug_payload = self.reporter.build_failure_payload(
                scenario=scenario,
                executed_steps=failed_steps,
                visible_state=visible_state,
                error=error,
                screenshot_path=screenshot_path,
                scenario_path=scenario_path,
            )
            report = self.reporter.finalize(
                scenario=scenario,
                executed_steps=failed_steps,
                success=False,
                debug_payload=debug_payload,
            )
        else:
            report = self.reporter.finalize(
                scenario=scenario,
                executed_steps=executed_steps,
                success=True,
                debug_payload={
                    "status": "ok",
                    "scenario": self._reporter_scenario_summary(
                        scenario,
                        scenario_path=scenario_path,
                    ),
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
        finally:
            try:
                self.driver.shutdown()
            except Exception:
                pass

        assert report is not None
        return report

    def _reporter_scenario_summary(
        self,
        scenario: dict[str, Any],
        *,
        scenario_path: Path | None,
    ) -> dict[str, Any]:
        scenario_summary = getattr(self.reporter, "scenario_summary", None)
        if callable(scenario_summary):
            return scenario_summary(scenario, scenario_path=scenario_path)

        metadata = scenario.get("metadata") or {}
        return {
            "id": metadata.get("id"),
            "title": metadata.get("title"),
            "tags": list(metadata.get("tags") or []),
            "scenario_path": scenario_path.as_posix() if scenario_path else None,
        }

    def _execute_step_action(self, step: dict[str, Any]) -> None:
        action = step.get("action")

        if action == "launch_app":
            self.driver.launch()
            return
        if action == "shutdown_app":
            self.driver.shutdown()
            return
        if action == "queue_prompt_response":
            self.driver.queue_prompt_response(step["value"])
            return
        if action == "set_load_selection":
            self.driver.set_load_selection(step["value"])
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
        if getattr(self.driver, "app", object()) is None:
            return None
        return self.observer.read_visible_state(self.driver)

    def _read_visible_state_for_failure(self) -> GUIVisibleState | None:
        try:
            return self._read_visible_state_or_none()
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
            "expect": step.get("expect"),
            "observed_summary": executed_step.get("observed_summary"),
            "state_delta": executed_step.get("state_delta"),
        }

    def _summarize_state_delta(
        self,
        previous_state: GUIVisibleState | None,
        current_state: GUIVisibleState | None,
    ) -> dict[str, Any] | None:
        if previous_state is None and current_state is None:
            return None
        if current_state is None:
            return {
                "view_changed": False,
                "status_changed": False,
                "button_changes": [],
                "text_changes": [],
                "score_changes": [],
                "dropdown_changed": False,
            }

        button_changes = self._mapping_changes(
            previous_state.button_states if previous_state else {},
            current_state.button_states,
        )
        text_changes = self._mapping_changes(
            previous_state.texts if previous_state else {},
            current_state.texts,
            interesting_keys={
                "setup.order_preview_label",
                "setup.summary_label",
                "setup.attack_repetition_feedback_label",
                "setup.multiple_attack_feedback_label",
                "match.phase_title_label",
                "match.trick_label",
                "match.phase_description_label",
                "match.attempts_label",
                "setup_details.body_label",
            },
        )
        score_changes = self._mapping_changes(
            previous_state.score_cells if previous_state else {},
            current_state.score_cells,
        )
        previous_dropdown = previous_state.dropdown_items if previous_state else ()
        current_dropdown = current_state.dropdown_items
        return {
            "view_changed": (
                previous_state is not None
                and previous_state.active_view != current_state.active_view
            ),
            "status_changed": (
                previous_state is not None
                and previous_state.status_text != current_state.status_text
            ),
            "button_changes": button_changes,
            "text_changes": text_changes,
            "score_changes": score_changes,
            "dropdown_changed": previous_dropdown != current_dropdown,
        }

    def _mapping_changes(
        self,
        previous_mapping: dict[str, str],
        current_mapping: dict[str, str],
        *,
        interesting_keys: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        changed_keys = sorted(set(previous_mapping) | set(current_mapping))
        if interesting_keys is not None:
            changed_keys = [key for key in changed_keys if key in interesting_keys]

        changes: list[dict[str, Any]] = []
        for key in changed_keys:
            previous_value = previous_mapping.get(key)
            current_value = current_mapping.get(key)
            if previous_value == current_value:
                continue
            changes.append(
                {
                    "target": key,
                    "previous": previous_value,
                    "current": current_value,
                }
            )
        return changes

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
