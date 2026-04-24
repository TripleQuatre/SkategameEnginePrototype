from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from interfaces.gui.gui_app import GUIApp


_KEY_ALIASES = {
    "enter": "Return",
    "return": "Return",
    "down": "Down",
    "up": "Up",
    "left": "Left",
    "right": "Right",
    "escape": "Escape",
    "esc": "Escape",
    "tab": "Tab",
}


class TkGUIHarnessDriver:
    def __init__(
        self,
        *,
        app_factory=GUIApp,
        withdraw_on_launch: bool = True,
    ) -> None:
        self._app_factory = app_factory
        self._withdraw_on_launch = withdraw_on_launch
        self.app: GUIApp | None = None

    def launch(self) -> None:
        if self.app is not None:
            return

        app = self._app_factory()
        if self._withdraw_on_launch:
            app.root.withdraw()
        self.app = app
        self._flush()

    def shutdown(self) -> None:
        if self.app is None:
            return

        root = self.app.root
        self.app = None
        if root.winfo_exists():
            root.update_idletasks()
            root.destroy()

    def click(self, target: str) -> None:
        widget = self._get_target(target)
        self._focus(widget)

        if isinstance(
            widget,
            (ttk.Button, ttk.Radiobutton, ttk.Checkbutton, tk.Button, tk.Radiobutton, tk.Checkbutton),
        ):
            widget.invoke()
            self._flush()
            return

        widget.event_generate("<Button-1>")
        widget.event_generate("<ButtonRelease-1>")
        self._flush()

    def type_text(self, target: str, value: str, *, replace: bool = True) -> None:
        widget = self._get_target(target)

        if not isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Spinbox, tk.Entry, tk.Spinbox)):
            raise TypeError(
                f"Target '{target}' does not support text input: {type(widget).__name__}."
            )

        self._focus(widget)
        if isinstance(widget, ttk.Spinbox):
            widget.set(value)
            self._flush()
            return

        if replace:
            widget.delete(0, tk.END)
        widget.insert(tk.END, value)
        self._flush()

    def press_key(self, target: str | None, key: str) -> None:
        widget = self._get_target(target) if target is not None else self._get_focus_target()
        event_key = _KEY_ALIASES.get(key.lower(), key)
        self._focus(widget)

        if event_key == "Return" and isinstance(widget, (ttk.Button, tk.Button)):
            widget.invoke()
            self._flush()
            return

        widget.event_generate(f"<{event_key}>")
        self._flush()

    def select_option(self, target: str, value: str) -> None:
        widget = self._get_target(target)

        if not isinstance(widget, ttk.Combobox):
            raise TypeError(
                f"Target '{target}' does not support option selection: {type(widget).__name__}."
            )

        self._focus(widget)
        widget.set(value)
        widget.event_generate("<<ComboboxSelected>>")
        self._flush()

    def select_suggestion(self, target: str, value: str) -> None:
        widget = self._get_target(target)

        if not isinstance(widget, tk.Listbox):
            raise TypeError(
                f"Target '{target}' does not support suggestion selection: {type(widget).__name__}."
            )

        items = list(widget.get(0, tk.END))
        try:
            index = next(index for index, item in enumerate(items) if value in item)
        except StopIteration as error:
            raise ValueError(
                f"Suggestion '{value}' was not found in target '{target}'."
            ) from error

        self._focus(widget)
        widget.selection_clear(0, tk.END)
        widget.selection_set(index)
        widget.activate(index)
        widget.see(index)
        widget.event_generate("<<ListboxSelect>>")
        self._flush()

    def capture_screenshot(self, destination: Path) -> Path:
        # Tk does not provide a cross-platform screenshot primitive here.
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            "Screenshot capture is not implemented yet for the Tk harness driver.\n",
            encoding="utf-8",
        )
        return destination

    def _get_target(self, target: str):
        if self.app is None:
            raise RuntimeError("GUI harness driver is not launched.")

        widget = self.app.get_harness_target(target)
        if widget is None:
            raise KeyError(f"Unknown harness target '{target}'.")
        return widget

    def _get_focus_target(self):
        if self.app is None:
            raise RuntimeError("GUI harness driver is not launched.")

        widget = self.app.root.focus_get()
        if widget is None:
            raise RuntimeError("No widget currently has keyboard focus.")
        return widget

    def _focus(self, widget) -> None:
        try:
            widget.focus_set()
        except tk.TclError:
            return
        self._flush()

    def _flush(self) -> None:
        if self.app is None:
            return
        self.app.root.update_idletasks()
        self.app.root.update()
