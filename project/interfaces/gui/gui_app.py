from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont

from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.events import Event
from core.history import HistoryRow
from core.state import GameState
from core.types import DefenseResolutionStatus, EventName, Phase
from core.exceptions import InvalidActionError, InvalidStateError


class GUIApp:
    SAVES_DIR = Path(__file__).resolve().parents[2] / "saves"
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SkateGame Prototype")
        self.root.geometry("720x540")
        self.root.minsize(680, 500)

        self.controller: GameController | None = None

        self.player_1_var = tk.StringVar()
        self.player_2_var = tk.StringVar()
        self.word_var = tk.StringVar(value="SKATE")
        self.defense_attempts_var = tk.IntVar(value=1)
        self.trick_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Configure the game to begin.")

        self.title_font = tkfont.Font(size=18, weight="bold")
        self.subtitle_font = tkfont.Font(size=10)
        self.section_font = tkfont.Font(size=12, weight="bold")
        self.score_name_font = tkfont.Font(size=12, weight="bold")
        self.score_active_font = tkfont.Font(size=18, weight="bold")
        self.score_inactive_font = tkfont.Font(size=18)
        self.body_font = tkfont.Font(size=11)
        self.small_font = tkfont.Font(size=10)

        self.current_view = "setup"

        self.container = ttk.Frame(self.root, padding=16)
        self.container.pack(fill="both", expand=True)

        self.setup_frame = ttk.Frame(self.container)
        self.game_frame = ttk.Frame(self.container)
        self.history_frame = ttk.Frame(self.container)

        self.matchup_label: ttk.Label | None = None
        self.phase_title_label: ttk.Label | None = None
        self.trick_label: ttk.Label | None = None
        self.phase_description_label: ttk.Label | None = None
        self.attempts_label: ttk.Label | None = None
        self.status_label: ttk.Label | None = None

        self.score_text: tk.Text | None = None
        self.trick_entry: ttk.Entry | None = None

        self.confirm_trick_button: ttk.Button | None = None
        self.cancel_trick_button: ttk.Button | None = None
        self.success_button: ttk.Button | None = None
        self.failure_button: ttk.Button | None = None
        self.undo_button: ttk.Button | None = None
        self.save_button: ttk.Button | None = None
        self.load_button: ttk.Button | None = None
        self.history_button: ttk.Button | None = None
        self.back_to_game_button: ttk.Button | None = None

        self.history_tree: ttk.Treeview | None = None

        self._build_setup_view()
        self._build_game_view()
        self._build_history_view()
        self._show_view("setup")

    def run(self) -> None:
        self.root.mainloop()

    def _ensure_saves_dir(self) -> Path:
        self.SAVES_DIR.mkdir(parents=True, exist_ok=True)
        return self.SAVES_DIR

    def _build_save_path(self) -> Path:
        saves_dir = self._ensure_saves_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return saves_dir / f"save_{timestamp}.json"

    def _list_save_files(self) -> list[Path]:
        saves_dir = self._ensure_saves_dir()
        return sorted(saves_dir.glob("*.json"), key=lambda path: path.name)

    # =========================
    # View management
    # =========================

    def _show_view(self, view_name: str) -> None:
        self.setup_frame.pack_forget()
        self.game_frame.pack_forget()
        self.history_frame.pack_forget()

        if view_name == "setup":
            self.setup_frame.pack(fill="both", expand=True)
        elif view_name == "game":
            self.game_frame.pack(fill="both", expand=True)
        elif view_name == "history":
            self.history_frame.pack(fill="both", expand=True)

        self.current_view = view_name

    # =========================
    # Setup view
    # =========================

    def _build_setup_view(self) -> None:
        frame = self.setup_frame

        frame.columnconfigure(0, weight=1)

        title = ttk.Label(frame, text="SkateGame Setup", font=self.title_font)
        title.grid(row=0, column=0, pady=(10, 28))

        form = ttk.Frame(frame)
        form.grid(row=1, column=0, sticky="n")

        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Player 1 name:", font=self.body_font).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        ttk.Entry(form, textvariable=self.player_1_var, width=36).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(0, 18)
        )

        ttk.Label(form, text="Player 2 name:", font=self.body_font).grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )
        ttk.Entry(form, textvariable=self.player_2_var, width=36).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(0, 18)
        )

        ttk.Label(form, text="Word:", font=self.body_font).grid(
            row=4, column=0, sticky="w", pady=(0, 6)
        )
        ttk.Entry(form, textvariable=self.word_var, width=36).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(0, 18)
        )

        ttk.Label(form, text="Defense attempts:", font=self.body_font).grid(
            row=6, column=0, sticky="w", pady=(0, 6)
        )

        attempts_frame = ttk.Frame(form)
        attempts_frame.grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 24))

        ttk.Radiobutton(
            attempts_frame, text="1", variable=self.defense_attempts_var, value=1
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            attempts_frame, text="2", variable=self.defense_attempts_var, value=2
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            attempts_frame, text="3", variable=self.defense_attempts_var, value=3
        ).pack(side="left")

        buttons = ttk.Frame(form)
        buttons.grid(row=8, column=0, columnspan=2, pady=(6, 0))

        ttk.Button(
            buttons,
            text="Start game",
            command=self._start_game,
            width=18,
        ).pack(side="left", padx=6)

        ttk.Button(
            buttons,
            text="Load saved game",
            command=self._load_game_from_setup,
            width=18,
        ).pack(side="left", padx=6)

    # =========================
    # Game view
    # =========================

    def _build_game_view(self) -> None:
        frame = self.game_frame
        frame.columnconfigure(0, weight=1)

        self.matchup_label = ttk.Label(frame, text="", font=self.title_font)
        self.matchup_label.grid(row=0, column=0, pady=(6, 10))

        self.score_text = tk.Text(
            frame,
            height=3,
            width=32,
            relief="flat",
            bd=0,
            highlightthickness=0,
            wrap="none",
            background=self.root.cget("bg"),
        )
        self.score_text.grid(row=1, column=0, pady=(0, 24))
        self.score_text.config(state="disabled")

        self.score_text.tag_configure("score_name", font=self.score_name_font)
        self.score_text.tag_configure("score_separator", font=self.score_active_font)
        self.score_text.tag_configure("score_active", font=self.score_active_font, foreground="black")
        self.score_text.tag_configure("score_inactive", font=self.score_inactive_font, foreground="gray")

        self.phase_title_label = ttk.Label(frame, text="", font=self.section_font)
        self.phase_title_label.grid(row=2, column=0, pady=(0, 14))

        self.trick_label = ttk.Label(frame, text="", font=self.section_font)
        self.trick_label.grid(row=3, column=0, pady=(0, 10))

        self.phase_description_label = ttk.Label(frame, text="", font=self.body_font)
        self.phase_description_label.grid(row=4, column=0, pady=(0, 8))

        self.attempts_label = ttk.Label(frame, text="", font=self.body_font)
        self.attempts_label.grid(row=5, column=0, pady=(0, 18))

        action_buttons = ttk.Frame(frame)
        action_buttons.grid(row=6, column=0, pady=(0, 14))

        self.success_button = ttk.Button(
            action_buttons,
            text="Success",
            command=lambda: self._resolve_defense(True),
            width=14,
        )
        self.success_button.pack(side="left", padx=8)

        self.failure_button = ttk.Button(
            action_buttons,
            text="Failure",
            command=lambda: self._resolve_defense(False),
            width=14,
        )
        self.failure_button.pack(side="left", padx=8)

        session_buttons = ttk.Frame(frame)
        session_buttons.grid(row=7, column=0, pady=(0, 20))

        self.undo_button = ttk.Button(
            session_buttons,
            text="Undo",
            command=self._undo_action,
            width=10,
        )
        self.undo_button.pack(side="left", padx=6)

        self.save_button = ttk.Button(
            session_buttons,
            text="Save",
            command=self._save_game,
            width=10,
        )
        self.save_button.pack(side="left", padx=6)

        self.load_button = ttk.Button(
            session_buttons,
            text="Load",
            command=self._load_game_during_session,
            width=10,
        )
        self.load_button.pack(side="left", padx=6)

        self.history_button = ttk.Button(
            session_buttons,
            text="History",
            command=self._show_history_view,
            width=10,
        )
        self.history_button.pack(side="left", padx=6)

        self.status_label = ttk.Label(
            frame,
            textvariable=self.status_var,
            font=self.small_font,
            justify="center",
        )
        self.status_label.grid(row=8, column=0, pady=(0, 14))

        trick_zone = ttk.Frame(frame)
        trick_zone.grid(row=9, column=0)

        self.trick_entry = ttk.Entry(trick_zone, textvariable=self.trick_var, width=26)
        self.trick_entry.grid(row=0, column=0, pady=(0, 10))

        buttons_row = ttk.Frame(trick_zone)
        buttons_row.grid(row=1, column=0)

        self.confirm_trick_button = ttk.Button(
            buttons_row,
            text="Confirm trick",
            command=self._confirm_trick,
            width=14,
        )
        self.confirm_trick_button.pack(side="left", padx=6)

        self.cancel_trick_button = ttk.Button(
            buttons_row,
            text="Cancel trick",
            command=self._cancel_trick,
            width=14,
        )
        self.cancel_trick_button.pack(side="left", padx=6)

    # =========================
    # History view
    # =========================

    def _build_history_view(self) -> None:
        frame = self.history_frame
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        title = ttk.Label(frame, text="Match history", font=self.title_font)
        title.grid(row=0, column=0, pady=(6, 14))

        columns = ("turn", "attacker", "trick", "valid", "defender", "defense", "letters")
        self.history_tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)

        self.history_tree.heading("turn", text="Turn")
        self.history_tree.heading("attacker", text="Attacker")
        self.history_tree.heading("trick", text="Trick")
        self.history_tree.heading("valid", text="Valid")
        self.history_tree.heading("defender", text="Defender")
        self.history_tree.heading("defense", text="Defense")
        self.history_tree.heading("letters", text="Letters")

        self.history_tree.column("turn", width=55, anchor="center")
        self.history_tree.column("attacker", width=120, anchor="w")
        self.history_tree.column("trick", width=180, anchor="w")
        self.history_tree.column("valid", width=60, anchor="center")
        self.history_tree.column("defender", width=120, anchor="w")
        self.history_tree.column("defense", width=90, anchor="center")
        self.history_tree.column("letters", width=90, anchor="center")

        self.history_tree.grid(row=1, column=0, sticky="nsew")

        controls = ttk.Frame(frame)
        controls.grid(row=2, column=0, pady=(14, 0))

        self.back_to_game_button = ttk.Button(
            controls,
            text="Back to game",
            command=self._show_game_view,
            width=16,
        )
        self.back_to_game_button.pack()

    # =========================
    # Game actions
    # =========================

    def _load_game_into_controller(self, selected_path: Path) -> None:
        placeholder_match_parameters = MatchParameters(
            player_ids=["Player 1", "Player 2"],
            mode_name="one_vs_one",
            rule_set=RuleSetConfig(),
        )

        controller = GameController(placeholder_match_parameters)
        controller.load_game(str(selected_path))
        self.controller = controller
        self.trick_var.set("")

    def _load_game_from_setup(self) -> None:
        save_files = self._list_save_files()

        if not save_files:
            messagebox.showinfo("Load game", "No saved games found.")
            return

        chooser = tk.Toplevel(self.root)
        chooser.title("Load saved game")
        chooser.resizable(False, False)
        chooser.transient(self.root)
        chooser.grab_set()

        ttk.Label(
            chooser,
            text="Choose a saved game:",
            padding=(16, 16, 16, 8),
        ).pack()

        selected_var = tk.StringVar(value=save_files[-1].name)

        combo = ttk.Combobox(
            chooser,
            textvariable=selected_var,
            values=[path.name for path in save_files],
            state="readonly",
            width=30,
        )
        combo.pack(padx=16, pady=(0, 16))
        combo.focus_set()

        buttons = ttk.Frame(chooser, padding=(16, 0, 16, 16))
        buttons.pack()

        def confirm_load() -> None:
            selected_name = selected_var.get()
            selected_path = next(
                (path for path in save_files if path.name == selected_name),
                None,
            )
            if selected_path is None:
                messagebox.showerror("Load game", "Invalid save selection.")
                return

            try:
                self._load_game_into_controller(selected_path)
            except (OSError, ValueError, InvalidStateError) as error:
                messagebox.showerror("Load game", str(error))
                return

            self.status_var.set(f"Game loaded from {selected_path.name}.")

            chooser.destroy()
            self._show_view("game")
            self._refresh_game_view()

        ttk.Button(
            buttons,
            text="Load",
            command=confirm_load,
            width=12,
        ).pack(side="left", padx=6)

        ttk.Button(
            buttons,
            text="Cancel",
            command=chooser.destroy,
            width=12,
        ).pack(side="left", padx=6)

    def _undo_action(self) -> None:
        if self.controller is None:
            return

        if self.controller.undo():
            self.trick_var.set("")
            self.status_var.set("Undo successful.")
        else:
            self.status_var.set("Nothing to undo.")

        self._refresh_game_view()

    def _save_game(self) -> None:
        if self.controller is None:
            return

        filepath = self._build_save_path()

        try:
            self.controller.save_game(str(filepath))
        except (OSError, ValueError, InvalidStateError) as error:
            messagebox.showerror("Save game", str(error))
            return

        self.status_var.set(f"Game saved to {filepath.name}.")

    def _load_game_during_session(self) -> None:
        save_files = self._list_save_files()

        if not save_files:
            messagebox.showinfo("Load game", "No saved games found.")
            return

        chooser = tk.Toplevel(self.root)
        chooser.title("Load saved game")
        chooser.resizable(False, False)
        chooser.transient(self.root)
        chooser.grab_set()

        ttk.Label(
            chooser,
            text="Choose a saved game:",
            padding=(16, 16, 16, 8),
        ).pack()

        selected_var = tk.StringVar(value=save_files[-1].name)

        combo = ttk.Combobox(
            chooser,
            textvariable=selected_var,
            values=[path.name for path in save_files],
            state="readonly",
            width=30,
        )
        combo.pack(padx=16, pady=(0, 16))
        combo.focus_set()

        buttons = ttk.Frame(chooser, padding=(16, 0, 16, 16))
        buttons.pack()

        def confirm_load() -> None:
            selected_name = selected_var.get()
            selected_path = next(
                (path for path in save_files if path.name == selected_name),
                None,
            )
            if selected_path is None:
                messagebox.showerror("Load game", "Invalid save selection.")
                return

            try:
                self._load_game_into_controller(selected_path)
            except (OSError, ValueError, InvalidStateError) as error:
                messagebox.showerror("Load game", str(error))
                return

            self.status_var.set(f"Game loaded from {selected_path.name}.")
            chooser.destroy()
            self._show_view("game")
            self._refresh_game_view()

        ttk.Button(
            buttons,
            text="Load",
            command=confirm_load,
            width=12,
        ).pack(side="left", padx=6)

        ttk.Button(
            buttons,
            text="Cancel",
            command=chooser.destroy,
            width=12,
        ).pack(side="left", padx=6)

    def _start_game(self) -> None:
        player_1 = self.player_1_var.get().strip()
        player_2 = self.player_2_var.get().strip()
        word = self.word_var.get().strip().upper()
        attempts = self.defense_attempts_var.get()

        if not player_1 or not player_2:
            messagebox.showerror("Invalid input", "Both player names are required.")
            return

        try:
            rule_set = RuleSetConfig(
                letters_word=word,
                defense_attempts=attempts,
            )
            match_parameters = MatchParameters(
                player_ids=[player_1, player_2],
                mode_name="one_vs_one",
                rule_set=rule_set,
            )
            self.controller = GameController(match_parameters)
            self.controller.start_game()
        except ValueError as error:
            messagebox.showerror("Invalid setup", str(error))
            return
        except InvalidActionError as error:
            messagebox.showerror("Cannot start game", str(error))
            return

        self.trick_var.set("")
        self.status_var.set("Game started.")
        self._show_view("game")
        self._refresh_game_view()

    def _confirm_trick(self) -> None:
        if self.controller is None:
            return

        trick = self.trick_var.get().strip()
        if not trick:
            messagebox.showerror("Invalid input", "The trick cannot be empty.")
            return

        try:
            self.controller.start_turn(trick)
            self.status_var.set(f"Trick '{trick}' confirmed.")
        except InvalidActionError as error:
            self.status_var.set(f"Invalid action: {error}")

        self._refresh_game_view()

    def _cancel_trick(self) -> None:
        if self.controller is None:
            return

        trick = self.trick_var.get().strip()
        if not trick:
            messagebox.showerror("Invalid input", "Enter a trick before cancelling it.")
            return

        try:
            self.controller.cancel_turn(trick)
            self.trick_var.set("")
            self.status_var.set("Trick cancelled. Next player.")
        except InvalidActionError as error:
            self.status_var.set(f"Invalid action: {error}")

        self._refresh_game_view()

    def _resolve_defense(self, success: bool) -> None:
        if self.controller is None:
            return

        try:
            state_before = self.controller.get_state()
            events_before = len(state_before.history.events)

            resolution_status = self.controller.resolve_defense(success)
            state_after = self.controller.get_state()
            message = self._format_new_events(state_after, events_before)

            if resolution_status == DefenseResolutionStatus.DEFENSE_CONTINUES:
                self.status_var.set(message or "Defense continues.")
            elif resolution_status == DefenseResolutionStatus.TURN_FINISHED:
                self.trick_var.set("")
                self.status_var.set(message or "Turn finished.")
            elif resolution_status == DefenseResolutionStatus.GAME_FINISHED:
                self.trick_var.set("")
                self.status_var.set(message or "Game finished.")
        except InvalidActionError as error:
            self.status_var.set(f"Invalid action: {error}")

        self._refresh_game_view()

        state = self.controller.get_state()
        if state.phase == Phase.END:
            self._show_game_over_message(state)

    # =========================
    # View refresh
    # =========================

    def _refresh_game_view(self) -> None:
        if self.controller is None:
            return

        state = self.controller.get_state()

        assert self.matchup_label is not None
        assert self.score_text is not None
        assert self.phase_title_label is not None
        assert self.trick_label is not None
        assert self.phase_description_label is not None
        assert self.attempts_label is not None

        self.matchup_label.config(
            text=f"{state.players[0].name.upper()} - {state.players[1].name.upper()}"
        )

        self._render_score_text(state)

        if state.phase == Phase.END:
            self.phase_title_label.config(text="Game over")
            self.trick_label.config(text="")
            self.phase_description_label.config(text="The match is finished.")
            self.attempts_label.config(text="")
            self._set_trick_controls_enabled(False)
            self._set_defense_controls_enabled(False)
            return

        attacker = state.players[state.attacker_index]

        if state.current_trick is None:
            defender_name = self._get_next_defender_name(state)
            self.phase_title_label.config(
                text=f"{attacker.name} sets the next trick"
            )
            self.trick_label.config(text="")
            self.phase_description_label.config(
                text=f"{attacker.name} attacks / {defender_name} defends"
            )
            self.attempts_label.config(text="")
            self._set_trick_controls_enabled(True)
            self._set_defense_controls_enabled(False)
        else:
            defender = self._get_current_defender(state)
            defender_name = defender.name if defender is not None else "-"

            self.phase_title_label.config(
                text=f"{attacker.name} attacks / {defender_name} defends"
            )
            self.trick_label.config(text=f"Trick: {state.current_trick}")
            self.phase_description_label.config(
                text=f"Defense phase: {defender_name} tries to reproduce the trick"
            )
            self.attempts_label.config(
                text=f"{defender_name} has {state.defense_attempts_left} defense attempt(s) left"
            )
            self._set_trick_controls_enabled(False)
            self._set_defense_controls_enabled(True)

    def _render_score_text(self, state: GameState) -> None:
        assert self.score_text is not None

        self.score_text.config(state="normal")
        self.score_text.delete("1.0", tk.END)

        if len(state.players) < 2:
            self.score_text.config(state="disabled")
            return

        word = state.rule_set.letters_word
        player_1 = state.players[0]
        player_2 = state.players[1]

        self._insert_score_word(word, player_1.score)
        self.score_text.insert(tk.END, "  -  ", "score_separator")
        self._insert_score_word(word, player_2.score)

        self.score_text.config(state="disabled")

    def _insert_score_word(self, word: str, score: int) -> None:
        assert self.score_text is not None

        active_part = word[:score]
        inactive_part = word[score:]

        if active_part:
            self.score_text.insert(tk.END, active_part, "score_active")
        if inactive_part:
            self.score_text.insert(tk.END, inactive_part, "score_inactive")

    def _set_trick_controls_enabled(self, enabled: bool) -> None:
        assert self.trick_entry is not None
        assert self.confirm_trick_button is not None
        assert self.cancel_trick_button is not None

        state = "normal" if enabled else "disabled"
        self.trick_entry.config(state=state)
        self.confirm_trick_button.config(state=state)
        self.cancel_trick_button.config(state=state)

    def _set_defense_controls_enabled(self, enabled: bool) -> None:
        assert self.success_button is not None
        assert self.failure_button is not None

        state = "normal" if enabled else "disabled"
        self.success_button.config(state=state)
        self.failure_button.config(state=state)

    def _show_history_view(self) -> None:
        if self.controller is None:
            return

        self._refresh_history_view()
        self._show_view("history")

    def _show_game_view(self) -> None:
        self._refresh_game_view()
        self._show_view("game")

    def _refresh_history_view(self) -> None:
        if self.controller is None or self.history_tree is None:
            return

        state = self.controller.get_state()
        rows: list[HistoryRow] = state.history.build_rows()

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for row in rows:
            letters = self._format_letters(row.letters, state.rule_set.letters_word)
            self.history_tree.insert(
                "",
                "end",
                values=(
                    row.turn_number,
                    row.attacker_name,
                    row.trick_name,
                    row.trick_validated,
                    row.defender_name or "-",
                    row.defense_result or "-",
                    letters,
                ),
            )

    # =========================
    # Helpers
    # =========================

    def _get_current_defender(self, state: GameState):
        if state.current_defender_position >= len(state.defender_indices):
            return None

        defender_index = state.defender_indices[state.current_defender_position]
        return state.players[defender_index]

    def _get_next_defender_name(self, state: GameState) -> str:
        for index, player in enumerate(state.players):
            if index != state.attacker_index and player.is_active:
                return player.name
        return "-"

    def _format_letters(self, letters: str, word: str) -> str:
        if not letters:
            return "-"
        if len(letters) >= len(word):
            return f"[{letters}]"
        return letters

    def _format_new_events(self, state: GameState, events_before: int) -> str:
        new_events = state.history.events[events_before:]
        messages: list[str] = []

        for event in new_events:
            message = self._format_event(state, event)
            if message:
                messages.append(message)

        return " ".join(messages)

    def _get_player_name(self, state: GameState, player_id: str) -> str:
        for player in state.players:
            if player.id == player_id:
                return player.name
        return player_id

    def _format_event(self, state: GameState, event: Event) -> str:
        name = event.name
        payload = event.payload

        if name == EventName.DEFENSE_SUCCEEDED:
            player_name = self._get_player_name(state, payload["player_id"])
            return f"{player_name} landed '{payload['trick']}'."

        if name == EventName.DEFENSE_FAILED_ATTEMPT:
            player_name = self._get_player_name(state, payload["player_id"])
            return (
                f"{player_name} missed '{payload['trick']}' "
                f"({payload['attempts_left']} left)."
            )

        if name == EventName.LETTER_RECEIVED:
            player_name = self._get_player_name(state, payload["player_id"])
            return f"{player_name} gets a letter: {payload['penalty_display']}"

        if name == EventName.PLAYER_ELIMINATED:
            player_name = self._get_player_name(state, payload["player_id"])
            return f"{player_name} is eliminated."

        if name == EventName.TURN_ENDED:
            next_attacker_name = self._get_player_name(state, payload["next_attacker_id"])
            return f"Next attacker: {next_attacker_name}"

        if name == EventName.TURN_CANCELLED:
            next_attacker_name = self._get_player_name(state, payload["next_attacker_id"])
            return f"Turn cancelled. Next attacker: {next_attacker_name}"

        if name == EventName.GAME_FINISHED:
            winner_id = payload["winner_id"]
            if winner_id is None:
                return "Game finished."
            winner_name = self._get_player_name(state, winner_id)
            return f"Game finished. Winner: {winner_name}"

        return ""

    def _show_game_over_message(self, state: GameState) -> None:
        active_players = [player for player in state.players if player.is_active]

        if len(active_players) == 1:
            messagebox.showinfo("Game Over", f"Winner: {active_players[0].name}")
        else:
            messagebox.showinfo("Game Over", "No winner determined.")

if __name__ == "__main__":
    GUIApp().run()