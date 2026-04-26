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
        self._expect_core_invariants(visible_state)

        self._expect_view(expectations, visible_state)
        self._expect_status(expectations, visible_state)
        self._expect_button_states(expectations, visible_state)
        self._expect_texts(expectations, visible_state)
        self._expect_score_cells(expectations, visible_state)
        self._expect_dropdown_contains(expectations, visible_state)

    def _expect_core_invariants(self, visible_state: GUIVisibleState) -> None:
        active_view = visible_state.active_view
        if active_view not in {"setup", "match", "history", "setup_details"}:
            raise GUIOracleError(
                "Active view is not a known GUI view.",
                expected=("setup", "match", "history", "setup_details"),
                observed=active_view,
            )

        if active_view == "setup":
            self._expect_setup_invariants(visible_state)
            return
        if active_view == "match":
            self._expect_match_invariants(visible_state)
            return
        if active_view == "history":
            self._expect_history_invariants(visible_state)
            return
        if active_view == "setup_details":
            self._expect_setup_details_invariants(visible_state)
            return

    def _expect_setup_invariants(self, visible_state: GUIVisibleState) -> None:
        self._require_button_state(
            visible_state,
            "setup.start_game_button",
            allowed_states={"normal", "disabled"},
        )
        self._require_button_state(
            visible_state,
            "setup.load_from_setup_button",
            allowed_states={"normal", "disabled"},
        )
        self._require_text_target(visible_state, "setup.preset_combo")
        self._require_text_target(visible_state, "setup.sport_combo")
        self._require_text_target(visible_state, "setup.word_entry")
        self._require_text_target(visible_state, "setup.order_preview_label")
        self._require_text_target(visible_state, "setup.summary_label")

        if visible_state.dropdown_items:
            raise GUIOracleError(
                "Setup view must not expose trick suggestions.",
                expected=(),
                observed=visible_state.dropdown_items,
            )

    def _expect_match_invariants(self, visible_state: GUIVisibleState) -> None:
        required_text_targets = (
            "match.phase_title_label",
            "match.trick_label",
            "match.phase_description_label",
            "match.attempts_label",
        )
        required_button_targets = (
            "match.undo_button",
            "match.save_button",
            "match.load_button",
            "match.history_button",
            "match.setup_details_button",
            "match.add_player_button",
            "match.remove_player_button",
            "match.new_game_button",
            "match.success_button",
            "match.failure_button",
        )

        for target_id in required_text_targets:
            self._require_text_target(visible_state, target_id)
        for target_id in required_button_targets:
            self._require_button_state(
                visible_state,
                target_id,
                allowed_states={"normal", "disabled"},
            )

        if not visible_state.score_cells:
            raise GUIOracleError(
                "Match view must expose score cells.",
                expected="non-empty score_cells",
                observed=visible_state.score_cells,
            )

        phase_title = visible_state.texts["match.phase_title_label"]
        trick_label = visible_state.texts["match.trick_label"]
        phase_description = visible_state.texts["match.phase_description_label"]
        attempts_label = visible_state.texts["match.attempts_label"]
        add_state = visible_state.button_states["match.add_player_button"]
        remove_state = visible_state.button_states["match.remove_player_button"]
        success_state = visible_state.button_states["match.success_button"]
        failure_state = visible_state.button_states["match.failure_button"]

        if phase_title == "Game over":
            if trick_label != "":
                raise GUIOracleError(
                    "Game over view must not display an engaged trick label.",
                    expected="",
                    observed=trick_label,
                )
            if "Consultation mode" not in phase_description:
                raise GUIOracleError(
                    "Game over view must explicitly expose consultation mode.",
                    expected="Consultation mode",
                    observed=phase_description,
                )
            if success_state != "disabled" or failure_state != "disabled":
                raise GUIOracleError(
                    "Game over view must disable defense resolution buttons.",
                    expected={
                        "match.success_button": "disabled",
                        "match.failure_button": "disabled",
                    },
                    observed={
                        "match.success_button": success_state,
                        "match.failure_button": failure_state,
                    },
                )
            if add_state != "disabled" or remove_state != "disabled":
                raise GUIOracleError(
                    "Game over view must disable roster transition buttons.",
                    expected={
                        "match.add_player_button": "disabled",
                        "match.remove_player_button": "disabled",
                    },
                    observed={
                        "match.add_player_button": add_state,
                        "match.remove_player_button": remove_state,
                    },
                )
            return

        if phase_title.endswith("sets the next trick"):
            if trick_label != "":
                raise GUIOracleError(
                    "Open turn must not show a current trick label.",
                    expected="",
                    observed=trick_label,
                )
            if not phase_description.startswith("Defenders:"):
                raise GUIOracleError(
                    "Open turn must expose active defenders.",
                    expected="Defenders: ...",
                    observed=phase_description,
                )
            if attempts_label != "":
                raise GUIOracleError(
                    "Open turn must not display remaining attempt text.",
                    expected="",
                    observed=attempts_label,
                )
            if success_state != "disabled" or failure_state != "disabled":
                raise GUIOracleError(
                    "Open turn must disable defense resolution buttons.",
                    expected={
                        "match.success_button": "disabled",
                        "match.failure_button": "disabled",
                    },
                    observed={
                        "match.success_button": success_state,
                        "match.failure_button": failure_state,
                    },
                )
            if add_state != "normal" or remove_state != "normal":
                raise GUIOracleError(
                    "Open turn must allow roster transitions.",
                    expected={
                        "match.add_player_button": "normal",
                        "match.remove_player_button": "normal",
                    },
                    observed={
                        "match.add_player_button": add_state,
                        "match.remove_player_button": remove_state,
                    },
                )
            return

        if phase_title.endswith("attacks"):
            if not trick_label.startswith("Trick: "):
                raise GUIOracleError(
                    "Attack/defense match view must expose the current trick.",
                    expected="Trick: ...",
                    observed=trick_label,
                )
            if not phase_description.startswith("Pending defenders:") and not phase_description.startswith(
                "Current defender:"
            ):
                raise GUIOracleError(
                    "Attack/defense match view must expose defenders context.",
                    expected=("Pending defenders: ...", "Current defender: ..."),
                    observed=phase_description,
                )
            if attempts_label == "":
                raise GUIOracleError(
                    "Attack/defense match view must expose attempts information.",
                    expected="non-empty attempts label",
                    observed=attempts_label,
                )
            if success_state != "normal" or failure_state != "normal":
                raise GUIOracleError(
                    "Attack/defense match view must enable defense resolution buttons.",
                    expected={
                        "match.success_button": "normal",
                        "match.failure_button": "normal",
                    },
                    observed={
                        "match.success_button": success_state,
                        "match.failure_button": failure_state,
                    },
                )
            if add_state != "disabled" or remove_state != "disabled":
                raise GUIOracleError(
                    "Engaged turns must disable roster transition buttons.",
                    expected={
                        "match.add_player_button": "disabled",
                        "match.remove_player_button": "disabled",
                    },
                    observed={
                        "match.add_player_button": add_state,
                        "match.remove_player_button": remove_state,
                    },
                )
            return

        raise GUIOracleError(
            "Match view exposes an unknown phase title.",
            expected=("Game over", "... sets the next trick", "... attacks"),
            observed=phase_title,
        )

    def _expect_history_invariants(self, visible_state: GUIVisibleState) -> None:
        self._require_button_state(
            visible_state,
            "history.back_to_game_button",
            allowed_states={"normal"},
        )
        if "history.tree" not in visible_state.table_rows:
            raise GUIOracleError(
                "History view must expose the history table.",
                expected="history.tree rows",
                observed=visible_state.table_rows,
            )

    def _expect_setup_details_invariants(self, visible_state: GUIVisibleState) -> None:
        self._require_button_state(
            visible_state,
            "setup_details.back_to_game_button",
            allowed_states={"normal"},
        )
        body = visible_state.texts.get("setup_details.body_label")
        if body is None:
            raise GUIOracleError(
                "Setup details view must expose its main body text.",
                expected="setup_details.body_label",
                observed=visible_state.texts,
            )

        required_fragments = (
            "Preset:",
            "Structure:",
            "Sport:",
            "Players:",
            "Profiles:",
            "Order:",
            "Base order:",
            "Word:",
            "Attack attempts:",
            "Defense attempts:",
            "Uniqueness:",
            "Multiple Attack:",
            "Repetition:",
            "Dictionary sport:",
            "Dictionary profile:",
            "Dictionary max segments:",
        )
        missing_fragments = [
            fragment for fragment in required_fragments if fragment not in body
        ]
        if missing_fragments:
            raise GUIOracleError(
                "Setup details view is missing structured configuration fields.",
                expected=required_fragments,
                observed=body,
            )

    def _require_text_target(
        self,
        visible_state: GUIVisibleState,
        target_id: str,
    ) -> None:
        if target_id not in visible_state.texts:
            raise GUIOracleError(
                f"Visible text target '{target_id}' is missing.",
                expected=target_id,
                observed=visible_state.texts,
            )

    def _require_button_state(
        self,
        visible_state: GUIVisibleState,
        target_id: str,
        *,
        allowed_states: set[str],
    ) -> None:
        observed_state = visible_state.button_states.get(target_id)
        if observed_state not in allowed_states:
            raise GUIOracleError(
                f"Visible button '{target_id}' is missing or in an invalid state.",
                expected={target_id: sorted(allowed_states)},
                observed={target_id: observed_state},
            )

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
