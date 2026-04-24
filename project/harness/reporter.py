from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.models import (
    GUIHarnessFailure,
    GUIHarnessReport,
    GUIHarnessStepRecord,
    GUIVisibleState,
)


class StructuredGUIHarnessReporter:
    def build_failure_payload(
        self,
        *,
        scenario: dict[str, Any],
        executed_steps: list[dict[str, Any]],
        visible_state: GUIVisibleState | None,
        error: Exception,
        screenshot_path: Path | None,
    ) -> dict[str, Any]:
        return {
            "scenario": self._scenario_summary(scenario),
            "steps": [self._step_payload(step) for step in executed_steps],
            "failure": {
                "message": str(error),
                "error_type": type(error).__name__,
                "expected": getattr(error, "expected", None),
                "observed": getattr(error, "observed", None),
                "screenshot_path": screenshot_path.as_posix() if screenshot_path else None,
            },
            "visible_state": self.visible_state_to_payload(visible_state),
        }

    def finalize(
        self,
        *,
        scenario: dict[str, Any],
        executed_steps: list[dict[str, Any]],
        success: bool,
        debug_payload: dict[str, Any],
    ) -> GUIHarnessReport:
        failure_payload = debug_payload.get("failure")
        failure = None
        if not success and isinstance(failure_payload, dict):
            failure = self._failure_from_payload(executed_steps, failure_payload)

        return GUIHarnessReport(
            scenario_id=self._scenario_id(scenario),
            success=success,
            steps=tuple(
                self._step_record(index=index, executed_step=executed_step)
                for index, executed_step in enumerate(executed_steps, start=1)
            ),
            failure=failure,
            debug_payload=debug_payload,
        )

    def visible_state_to_payload(
        self,
        visible_state: GUIVisibleState | None,
    ) -> dict[str, Any] | None:
        if visible_state is None:
            return None

        return {
            "active_view": visible_state.active_view,
            "status_text": visible_state.status_text,
            "button_states": dict(visible_state.button_states),
            "texts": dict(visible_state.texts),
            "score_cells": dict(visible_state.score_cells),
            "table_rows": {
                target_id: [list(row) for row in rows]
                for target_id, rows in visible_state.table_rows.items()
            },
            "dropdown_items": list(visible_state.dropdown_items),
        }

    def _scenario_summary(self, scenario: dict[str, Any]) -> dict[str, Any]:
        metadata = scenario.get("metadata") or {}
        summary = {
            "id": self._scenario_id(scenario),
            "title": metadata.get("title"),
            "tags": list(metadata.get("tags") or []),
        }
        for optional_key in ("seed", "kind", "max_steps"):
            if optional_key in metadata:
                summary[optional_key] = metadata[optional_key]
        return summary

    def _scenario_id(self, scenario: dict[str, Any]) -> str:
        metadata = scenario.get("metadata") or {}
        scenario_id = metadata.get("id")
        return scenario_id if isinstance(scenario_id, str) else "unknown"

    def _step_payload(self, executed_step: dict[str, Any]) -> dict[str, Any]:
        step = executed_step.get("step") or executed_step
        visible_state = executed_step.get("visible_state")
        return {
            "index": executed_step.get("index"),
            "name": step.get("name"),
            "action": step.get("action"),
            "target": step.get("target"),
            "value": step.get("value"),
            "key": step.get("key"),
            "observed_summary": executed_step.get("observed_summary"),
            "visible_state": self.visible_state_to_payload(visible_state),
        }

    def _step_record(
        self,
        *,
        index: int,
        executed_step: dict[str, Any],
    ) -> GUIHarnessStepRecord:
        step = executed_step.get("step") or executed_step
        visible_state = executed_step.get("visible_state")
        return GUIHarnessStepRecord(
            index=int(executed_step.get("index") or index),
            name=str(step.get("name") or ""),
            action=str(step.get("action") or ""),
            observed_summary=executed_step.get("observed_summary"),
            visible_state=visible_state if isinstance(visible_state, GUIVisibleState) else None,
        )

    def _failure_from_payload(
        self,
        executed_steps: list[dict[str, Any]],
        failure_payload: dict[str, Any],
    ) -> GUIHarnessFailure:
        step_index = len(executed_steps)
        step_name = ""
        if executed_steps:
            last_step = executed_steps[-1].get("step") or executed_steps[-1]
            step_index = int(executed_steps[-1].get("index") or len(executed_steps))
            step_name = str(last_step.get("name") or "")

        screenshot_path = failure_payload.get("screenshot_path")
        return GUIHarnessFailure(
            step_index=step_index,
            step_name=step_name,
            message=str(failure_payload.get("message") or ""),
            expected=failure_payload.get("expected"),
            observed=failure_payload.get("observed"),
            screenshot_path=Path(screenshot_path) if screenshot_path else None,
        )
