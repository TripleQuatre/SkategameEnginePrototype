from pathlib import Path
from typing import Any, Protocol

from harness.models import GUIHarnessReport, GUIVisibleState


class GUIHarnessDriver(Protocol):
    def launch(self) -> None: ...

    def shutdown(self) -> None: ...

    def queue_prompt_response(self, value: str | None) -> None: ...

    def set_load_selection(self, value: str) -> None: ...

    def click(self, target: str) -> None: ...

    def type_text(self, target: str, value: str, *, replace: bool = True) -> None: ...

    def press_key(self, target: str | None, key: str) -> None: ...

    def select_option(self, target: str, value: str) -> None: ...

    def select_suggestion(self, target: str, value: str) -> None: ...

    def capture_screenshot(self, destination: Path) -> Path: ...


class GUIHarnessObserver(Protocol):
    def read_visible_state(self, driver: GUIHarnessDriver) -> GUIVisibleState: ...


class GUIHarnessScenarioSource(Protocol):
    def load(self, scenario_path: Path) -> dict[str, Any]: ...


class GUIHarnessOracleEngine(Protocol):
    def evaluate_step(
        self,
        *,
        scenario: dict[str, Any],
        step: dict[str, Any],
        visible_state: GUIVisibleState,
    ) -> None: ...


class GUIHarnessReporter(Protocol):
    def scenario_summary(
        self,
        scenario: dict[str, Any],
        *,
        scenario_path: Path | None = None,
    ) -> dict[str, Any]: ...

    def build_failure_payload(
        self,
        *,
        scenario: dict[str, Any],
        executed_steps: list[dict[str, Any]],
        visible_state: GUIVisibleState | None,
        error: Exception,
        screenshot_path: Path | None,
        scenario_path: Path | None = None,
    ) -> dict[str, Any]: ...

    def finalize(
        self,
        *,
        scenario: dict[str, Any],
        executed_steps: list[dict[str, Any]],
        success: bool,
        debug_payload: dict[str, Any],
    ) -> GUIHarnessReport: ...
