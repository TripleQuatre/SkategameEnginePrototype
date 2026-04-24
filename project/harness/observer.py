from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from harness.driver import TkGUIHarnessDriver
from harness.models import GUIVisibleState


_VIEW_ALIASES = {
    "game": "match",
}

_BUTTON_TYPES = (ttk.Button, ttk.Checkbutton, ttk.Radiobutton, tk.Button, tk.Checkbutton, tk.Radiobutton)
_TEXT_TYPES = (
    ttk.Label,
    ttk.Button,
    ttk.Checkbutton,
    ttk.Radiobutton,
    tk.Label,
    tk.Button,
    tk.Checkbutton,
    tk.Radiobutton,
)
_VALUE_TYPES = (ttk.Entry, ttk.Combobox, ttk.Spinbox, tk.Entry, tk.Spinbox)


class TkGUIHarnessObserver:
    def read_visible_state(self, driver: TkGUIHarnessDriver) -> GUIVisibleState:
        if driver.app is None:
            raise RuntimeError("GUI harness driver is not launched.")

        app = driver.app
        active_view = _VIEW_ALIASES.get(app.get_harness_active_view(), app.get_harness_active_view())
        visible_prefix = f"{active_view}."

        texts: dict[str, str] = {}
        button_states: dict[str, str] = {}
        score_cells: dict[str, str] = {}
        table_rows: dict[str, tuple[tuple[str, ...], ...]] = {}

        for target_id in app.list_harness_targets():
            if not target_id.startswith(visible_prefix):
                continue

            widget = app.get_harness_target(target_id)
            if widget is None:
                continue

            text_value = self._read_widget_text(widget)
            if text_value is not None:
                texts[target_id] = text_value

            if isinstance(widget, _BUTTON_TYPES):
                state = app.get_harness_target_state(target_id)
                if state is not None:
                    button_states[target_id] = state

            if target_id == "match.score_frame":
                score_cells = self._read_score_cells(widget)

            if isinstance(widget, ttk.Treeview):
                table_rows[target_id] = self._read_tree_rows(widget)

        dropdown_items = ()
        dropdown_frame = app.get_harness_target("match.trick_dropdown_frame")
        dropdown_listbox = app.get_harness_target("match.trick_suggestions_listbox")
        if (
            active_view == "match"
            and isinstance(dropdown_frame, tk.Widget)
            and isinstance(dropdown_listbox, tk.Listbox)
            and dropdown_frame.winfo_manager()
        ):
            dropdown_items = tuple(dropdown_listbox.get(0, tk.END))

        status_text = app.status_var.get() if hasattr(app, "status_var") else None

        return GUIVisibleState(
            active_view=active_view,
            status_text=status_text,
            button_states=button_states,
            texts=texts,
            score_cells=score_cells,
            table_rows=table_rows,
            dropdown_items=dropdown_items,
        )

    def _read_widget_text(self, widget) -> str | None:
        if isinstance(widget, _TEXT_TYPES):
            try:
                return str(widget.cget("text"))
            except tk.TclError:
                return None

        if isinstance(widget, _VALUE_TYPES):
            try:
                return str(widget.get())
            except tk.TclError:
                return None

        return None

    def _read_score_cells(self, widget) -> dict[str, str]:
        cells: dict[str, str] = {}
        for child in widget.winfo_children():
            if not hasattr(child, "grid_info"):
                continue
            grid_info = child.grid_info()
            if "row" not in grid_info or "column" not in grid_info:
                continue

            row = int(grid_info["row"])
            column = int(grid_info["column"])
            try:
                text = str(child.cget("text"))
            except tk.TclError:
                continue
            cells[f"{row},{column}"] = text
        return cells

    def _read_tree_rows(self, widget: ttk.Treeview) -> tuple[tuple[str, ...], ...]:
        rows: list[tuple[str, ...]] = []
        for item_id in widget.get_children():
            values = widget.item(item_id, "values")
            rows.append(tuple(str(value) for value in values))
        return tuple(rows)
