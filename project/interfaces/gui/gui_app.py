import tkinter as tk
from tkinter import ttk, messagebox

from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.events import Event
from core.history import HistoryRow
from core.state import GameState
from core.types import Phase, DefenseResolutionStatus
from core.exceptions import InvalidActionError


class GUIApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SkateGame Engine Prototype")
        self.root.geometry("760x520")

        self.controller: GameController | None = None
        self.setup_frame: ttk.Frame | None = None
        self.game_frame: ttk.Frame | None = None

        self.player_1_var = tk.StringVar()
        self.player_2_var = tk.StringVar()
        self.word_var = tk.StringVar(value="SKATE")
        self.defense_attempts_var = tk.StringVar(value="1")

        self.trick_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Configure the game and click Start Game.")

        self.score_text: tk.Text | None = None
        self.attacker_label: ttk.Label | None = None
        self.phase_label: ttk.Label | None = None
        self.defender_label: ttk.Label | None = None
        self.current_trick_label: ttk.Label | None = None
        self.status_label: ttk.Label | None = None

        self.trick_entry: ttk.Entry | None = None
        self.confirm_trick_button: ttk.Button | None = None
        self.cancel_trick_button: ttk.Button | None = None
        self.success_button: ttk.Button | None = None
        self.fail_button: ttk.Button | None = None
        self.history_button: ttk.Button | None = None

        self._build_setup_frame()
        self._build_game_frame()
        self._show_setup()

    def run(self) -> None:
        self.root.mainloop()

    def _build_setup_frame(self) -> None:
        self.setup_frame = ttk.Frame(self.root, padding=16)

        ttk.Label(self.setup_frame, text="Player 1 name").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(self.setup_frame, textvariable=self.player_1_var, width=30).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(self.setup_frame, text="Player 2 name").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(self.setup_frame, textvariable=self.player_2_var, width=30).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(self.setup_frame, text="Word").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(self.setup_frame, textvariable=self.word_var, width=30).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(self.setup_frame, text="Defense attempts (1-3)").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(self.setup_frame, textvariable=self.defense_attempts_var, width=30).grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Button(
            self.setup_frame,
            text="Start Game",
            command=self._start_game,
        ).grid(row=4, column=0, columnspan=2, pady=(12, 0), sticky="ew")

        self.setup_frame.columnconfigure(1, weight=1)

    def _build_game_frame(self) -> None:
        self.game_frame = ttk.Frame(self.root, padding=16)

        self.score_text = tk.Text(
            self.game_frame,
            height=4,
            width=50,
            relief="flat",
            bd=0,
            highlightthickness=0,
            wrap="none",
        )
        self.score_text.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        self.score_text.config(state="disabled")

        self.score_text.tag_configure("player_name", font=("TkDefaultFont", 10, "normal"))
        self.score_text.tag_configure("word_inactive", foreground="gray")
        self.score_text.tag_configure("word_active", foreground="black", font=("TkDefaultFont", 10, "bold"))

        self.attacker_label = ttk.Label(self.game_frame, text="")
        self.attacker_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=2)

        self.phase_label = ttk.Label(self.game_frame, text="")
        self.phase_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=2)

        self.current_trick_label = ttk.Label(self.game_frame, text="")
        self.current_trick_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=2)

        self.defender_label = ttk.Label(self.game_frame, text="")
        self.defender_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(2, 12))

        ttk.Label(self.game_frame, text="Next trick").grid(row=5, column=0, sticky="w")
        self.trick_entry = ttk.Entry(self.game_frame, textvariable=self.trick_var, width=36)
        self.trick_entry.grid(row=5, column=1, columnspan=2, sticky="ew", pady=4)

        self.confirm_trick_button = ttk.Button(
            self.game_frame,
            text="Confirm Trick",
            command=self._confirm_trick,
        )
        self.confirm_trick_button.grid(row=6, column=0, sticky="ew", pady=4)

        self.cancel_trick_button = ttk.Button(
            self.game_frame,
            text="Cancel Trick",
            command=self._cancel_trick,
        )
        self.cancel_trick_button.grid(row=6, column=1, sticky="ew", pady=4)

        self.history_button = ttk.Button(
            self.game_frame,
            text="History",
            command=self._open_history_window,
        )
        self.history_button.grid(row=6, column=2, sticky="ew", pady=4)

        self.success_button = ttk.Button(
            self.game_frame,
            text="Defense Success",
            command=lambda: self._resolve_defense(True),
        )
        self.success_button.grid(row=7, column=0, sticky="ew", pady=4)

        self.fail_button = ttk.Button(
            self.game_frame,
            text="Defense Fail",
            command=lambda: self._resolve_defense(False),
        )
        self.fail_button.grid(row=7, column=1, sticky="ew", pady=4)

        self.status_label = ttk.Label(
            self.game_frame,
            textvariable=self.status_var,
            wraplength=700,
            justify="left",
        )
        self.status_label.grid(row=8, column=0, columnspan=3, sticky="w", pady=(12, 0))

        self.game_frame.columnconfigure(1, weight=1)
        self.game_frame.columnconfigure(2, weight=1)

    def _show_setup(self) -> None:
        assert self.setup_frame is not None
        assert self.game_frame is not None
        self.game_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)

    def _show_game(self) -> None:
        assert self.setup_frame is not None
        assert self.game_frame is not None
        self.setup_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)

    def _get_player_name(self, state: GameState, player_id: str) -> str:
        for player in state.players:
            if player.id == player_id:
                return player.name
        return player_id

    def _start_game(self) -> None:
        player_1 = self.player_1_var.get().strip()
        player_2 = self.player_2_var.get().strip()
        word = self.word_var.get().strip().upper()
        attempts_text = self.defense_attempts_var.get().strip()

        if not player_1 or not player_2:
            messagebox.showerror("Invalid input", "Both player names are required.")
            return

        if not word:
            messagebox.showerror("Invalid input", "The word is required.")
            return

        if not attempts_text.isdigit():
            messagebox.showerror("Invalid input", "Defense attempts must be a number.")
            return

        attempts = int(attempts_text)

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
        except (ValueError, InvalidActionError) as error:
            messagebox.showerror("Cannot start game", str(error))
            return

        self.status_var.set("Game started.")
        self.trick_var.set("")
        self._show_game()
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
        except InvalidActionError as error:
            self.status_var.set(f"Invalid action: {error}")
            self._refresh_game_view()
            return

        self.status_var.set(f"Trick '{trick}' started.")
        self._refresh_game_view()

    def _cancel_trick(self) -> None:
        if self.controller is None:
            return

        trick = self.trick_var.get().strip()
        if not trick:
            messagebox.showerror("Invalid input", "Enter a trick before cancelling it.")
            return

        self.controller.cancel_turn(trick)
        self.status_var.set("Trick cancelled. Next player.")
        self.trick_var.set("")
        self._refresh_game_view()

    def _resolve_defense(self, success: bool) -> None:
        if self.controller is None:
            return

        try:
            events_before = len(self.controller.get_state().history.events)
            resolution_status = self.controller.resolve_defense(success)
            message = self._format_new_events(self.controller.get_state(), events_before)

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

    def _refresh_game_view(self) -> None:
        if self.controller is None:
            return

        state = self.controller.get_state()

        assert self.score_text is not None
        assert self.attacker_label is not None
        assert self.phase_label is not None
        assert self.current_trick_label is not None
        assert self.defender_label is not None
        assert self.trick_entry is not None
        assert self.confirm_trick_button is not None
        assert self.cancel_trick_button is not None
        assert self.success_button is not None
        assert self.fail_button is not None

        self._render_score_text(state)
        self.phase_label.config(text=f"Phase: {state.phase.value}")

        if state.phase == Phase.END:
            self.attacker_label.config(text="Attacker: -")
            self.current_trick_label.config(text="Current trick: -")
            self.defender_label.config(text="Defender: -")
            self._set_trick_controls_enabled(False)
            self._set_defense_controls_enabled(False)
            return

        attacker = state.players[state.attacker_index]
        self.attacker_label.config(text=f"Attacker: {attacker.name}")

        if state.current_trick is None:
            self.current_trick_label.config(text="Current trick: -")
            self.defender_label.config(text="Defender: -")
            self._set_trick_controls_enabled(True)
            self._set_defense_controls_enabled(False)
        else:
            self.current_trick_label.config(text=f"Current trick: {state.current_trick}")

            if state.current_defender_position < len(state.defender_indices):
                defender_index = state.defender_indices[state.current_defender_position]
                defender = state.players[defender_index]
                self.defender_label.config(
                    text=(
                        f"Defender: {defender.name} "
                        f"({state.defense_attempts_left} attempt(s) left)"
                    )
                )
            else:
                self.defender_label.config(text="Defender: -")

            self._set_trick_controls_enabled(False)
            self._set_defense_controls_enabled(True)

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
        assert self.fail_button is not None

        state = "normal" if enabled else "disabled"
        self.success_button.config(state=state)
        self.fail_button.config(state=state)

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

    def _format_event(self, state: GameState, event: Event) -> str:
        name = event.name
        payload = event.payload

        if name == "defense_succeeded":
            player_name = self._get_player_name(state, payload["player_id"])
            return f"{player_name} landed '{payload['trick']}'."

        if name == "defense_failed_attempt":
            player_name = self._get_player_name(state, payload["player_id"])
            return (
                f"{player_name} missed '{payload['trick']}' "
                f"({payload['attempts_left']} left)."
            )

        if name == "letter_received":
            player_name = self._get_player_name(state, payload["player_id"])
            return f"{player_name} gets a letter: {payload['penalty_display']}"

        if name == "player_eliminated":
            player_name = self._get_player_name(state, payload["player_id"])
            return f"{player_name} is eliminated."

        if name == "turn_ended":
            next_attacker_name = self._get_player_name(state, payload["next_attacker_id"])
            return f"Next attacker: {next_attacker_name}"

        if name == "turn_cancelled":
            next_attacker_name = self._get_player_name(state, payload["next_attacker_id"])
            return f"Turn cancelled. Next attacker: {next_attacker_name}"

        if name == "game_finished":
            winner_id = payload["winner_id"]
            if winner_id is None:
                return "Game finished."
            winner_name = self._get_player_name(state, winner_id)
            return f"Game finished. Winner: {winner_name}"

        return ""

    def _open_history_window(self) -> None:
        if self.controller is None:
            return

        state = self.controller.get_state()
        rows: list[HistoryRow] = state.history.build_rows()

        window = tk.Toplevel(self.root)
        window.title("History")
        window.geometry("860x360")

        columns = ("turn", "attacker", "trick", "valid", "defender", "defense", "letters")
        tree = ttk.Treeview(window, columns=columns, show="headings")

        tree.heading("turn", text="Turn")
        tree.heading("attacker", text="Attacker")
        tree.heading("trick", text="Trick")
        tree.heading("valid", text="Valid")
        tree.heading("defender", text="Defender")
        tree.heading("defense", text="Defense")
        tree.heading("letters", text="Letters")

        tree.column("turn", width=60, anchor="center")
        tree.column("attacker", width=120, anchor="w")
        tree.column("trick", width=180, anchor="w")
        tree.column("valid", width=70, anchor="center")
        tree.column("defender", width=120, anchor="w")
        tree.column("defense", width=100, anchor="center")
        tree.column("letters", width=100, anchor="center")

        for row in rows:
            letters = self._format_letters(row.letters, state.rule_set.letters_word)
            tree.insert(
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

        tree.pack(fill="both", expand=True, padx=12, pady=12)

    def _show_game_over_message(self, state: GameState) -> None:
        active_players = [player for player in state.players if player.is_active]

        if len(active_players) == 1:
            messagebox.showinfo("Game Over", f"Winner: {active_players[0].name}")
        else:
            messagebox.showinfo("Game Over", "No winner determined.")

    def _display_history(self, state: GameState) -> None:
        rows: list[HistoryRow] = state.history.build_rows()

        if not rows:
            return

        print("\nHistory:")
        print(
            f"{'Turn':<6}"
            f"{'Attacker':<12}"
            f"{'Trick':<16}"
            f"{'Valid':<8}"
            f"{'Defender':<12}"
            f"{'Defense':<10}"
            f"{'Letters':<10}"
        )
        print("-" * 74)

        for row in rows:
            letters = self._format_letters(row.letters, state.rule_set.letters_word)

            print(
                f"{row.turn_number:<6}"
                f"{row.attacker_name:<12}"
                f"{row.trick_name:<16}"
                f"{row.trick_validated:<8}"
                f"{row.defender_name:<12}"
                f"{row.defense_result or '-':<10}"
                f"{letters:<10}"
            )

    def _render_score_text(self, state: GameState) -> None:
        assert self.score_text is not None

        self.score_text.config(state="normal")
        self.score_text.delete("1.0", tk.END)

        self.score_text.insert(tk.END, "Score:\n")

        word = state.rule_set.letters_word

        for player in state.players:
            self.score_text.insert(tk.END, f"{player.name:<12}", "player_name")

            taken = word[:player.score]
            remaining = word[player.score:]

            if taken:
                self.score_text.insert(tk.END, taken, "word_active")
            if remaining:
                self.score_text.insert(tk.END, remaining, "word_inactive")

            self.score_text.insert(tk.END, "\n")

        self.score_text.config(state="disabled")

if __name__ == "__main__":
    GUIApp().run()