from __future__ import annotations

from typing import Any

from harness.models import GUIVisibleState


class GUIOracleError(AssertionError):
    def __init__(
        self,
        message: str,
        *,
        expected: Any = None,
        observed: Any = None,
    ) -> None:
        super().__init__(message)
        self.expected = expected
        self.observed = observed


class GUIOracleEngine:
    def evaluate_step(
        self,
        *,
        scenario: dict[str, Any],
        step: dict[str, Any],
        visible_state: GUIVisibleState,
    ) -> None:
        del scenario

        expectations = step.get("expect") or {}
        if not expectations:
            return

        self._expect_view(expectations, visible_state)
        self._expect_status(expectations, visible_state)
        self._expect_button_states(expectations, visible_state)
        self._expect_texts(expectations, visible_state)
        self._expect_score_cells(expectations, visible_state)
        self._expect_dropdown_contains(expectations, visible_state)

    def _expect_view(
        self,
        expectations: dict[str, Any],
        visible_state: GUIVisibleState,
    ) -> None:
        expected_view = expectations.get("view")
        if expected_view is None:
            return

        if visible_state.active_view != expected_view:
            raise GUIOracleError(
                "Active view does not match.",
                expected=expected_view,
                observed=visible_state.active_view,
            )

    def _expect_status(
        self,
        expectations: dict[str, Any],
        visible_state: GUIVisibleState,
    ) -> None:
        expected_status = expectations.get("status_text_equals")
        if expected_status is not None and visible_state.status_text != expected_status:
            raise GUIOracleError(
                "Status text does not match exactly.",
                expected=expected_status,
                observed=visible_state.status_text,
            )

        status_fragment = expectations.get("status_text_contains")
        if status_fragment is not None and status_fragment not in (
            visible_state.status_text or ""
        ):
            raise GUIOracleError(
                "Status text does not contain expected fragment.",
                expected=status_fragment,
                observed=visible_state.status_text,
            )

    def _expect_button_states(
        self,
        expectations: dict[str, Any],
        visible_state: GUIVisibleState,
    ) -> None:
        expected_states = expectations.get("button_states") or {}
        for target_id, expected_state in expected_states.items():
            observed_state = visible_state.button_states.get(target_id)
            if observed_state != expected_state:
                raise GUIOracleError(
                    f"Button state does not match for '{target_id}'.",
                    expected={target_id: expected_state},
                    observed={target_id: observed_state},
                )

    def _expect_texts(
        self,
        expectations: dict[str, Any],
        visible_state: GUIVisibleState,
    ) -> None:
        expected_exact = expectations.get("text_equals") or {}
        for target_id, expected_text in expected_exact.items():
            observed_text = visible_state.texts.get(target_id)
            if observed_text != expected_text:
                raise GUIOracleError(
                    f"Text does not match exactly for '{target_id}'.",
                    expected={target_id: expected_text},
                    observed={target_id: observed_text},
                )

        expected_fragments = expectations.get("text_contains") or {}
        for target_id, expected_fragment in expected_fragments.items():
            observed_text = visible_state.texts.get(target_id)
            if expected_fragment not in (observed_text or ""):
                raise GUIOracleError(
                    f"Text does not contain expected fragment for '{target_id}'.",
                    expected={target_id: expected_fragment},
                    observed={target_id: observed_text},
                )

    def _expect_score_cells(
        self,
        expectations: dict[str, Any],
        visible_state: GUIVisibleState,
    ) -> None:
        expected_cells = expectations.get("score_cells") or {}
        for cell_id, expected_text in expected_cells.items():
            observed_text = visible_state.score_cells.get(cell_id)
            if observed_text != expected_text:
                raise GUIOracleError(
                    f"Score cell does not match for '{cell_id}'.",
                    expected={cell_id: expected_text},
                    observed={cell_id: observed_text},
                )

    def _expect_dropdown_contains(
        self,
        expectations: dict[str, Any],
        visible_state: GUIVisibleState,
    ) -> None:
        expected_items = expectations.get("dropdown_contains") or []
        for expected_item in expected_items:
            if not any(expected_item in item for item in visible_state.dropdown_items):
                raise GUIOracleError(
                    "Dropdown does not contain expected item.",
                    expected=expected_item,
                    observed=visible_state.dropdown_items,
                )
