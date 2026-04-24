from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GUIHarnessRunLimits:
    max_steps: int = 200
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class GUIHarnessRunConfig:
    capture_on_failure: bool = True
    limits: GUIHarnessRunLimits = field(default_factory=GUIHarnessRunLimits)


@dataclass(frozen=True)
class GUIVisibleState:
    active_view: str | None = None
    status_text: str | None = None
    button_states: dict[str, str] = field(default_factory=dict)
    texts: dict[str, str] = field(default_factory=dict)
    score_cells: dict[str, str] = field(default_factory=dict)
    table_rows: dict[str, tuple[tuple[str, ...], ...]] = field(default_factory=dict)
    dropdown_items: tuple[str, ...] = ()


@dataclass(frozen=True)
class GUIHarnessStepRecord:
    index: int
    name: str
    action: str
    observed_summary: str | None = None
    visible_state: GUIVisibleState | None = None


@dataclass(frozen=True)
class GUIHarnessFailure:
    step_index: int
    step_name: str
    message: str
    expected: Any = None
    observed: Any = None
    screenshot_path: Path | None = None


@dataclass(frozen=True)
class GUIHarnessReport:
    scenario_id: str
    success: bool
    steps: tuple[GUIHarnessStepRecord, ...] = ()
    failure: GUIHarnessFailure | None = None
    debug_payload: dict[str, Any] = field(default_factory=dict)
