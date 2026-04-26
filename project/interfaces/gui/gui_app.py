from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import font as tkfont

from application.game_setup_service import GameSetupService
from config.match_policies import InitialTurnOrderPolicy, RelevanceCriterion
from controllers.game_controller import GameController
from core.events import Event
from core.history import HistoryTurn
from core.state import GameState
from core.types import AttackResolutionStatus, DefenseResolutionStatus, EventName, Phase, TurnPhase
from core.exceptions import InvalidActionError, InvalidStateError


class GUIApp:
    SAVES_DIR = Path(__file__).resolve().parents[2] / "saves"
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SkateGame Prototype")
        screen_height = self.root.winfo_screenheight()
        window_height = max(720, min(screen_height - 80, 980))
        self.root.geometry(f"860x{window_height}")
        self.root.minsize(760, 640)

        self.controller: GameController | None = None
        self.setup_service = GameSetupService()
        self.available_local_profiles = self.setup_service.list_local_profiles()
        self.profile_id_by_display_name = {
            profile.display_name: profile.profile_id
            for profile in self.available_local_profiles
        }
        self.local_profile_display_names = [
            profile.display_name for profile in self.available_local_profiles
        ]

        self.setup_mode_var = tk.StringVar(value="preset")
        self.player_count_var = tk.IntVar(value=2)
        self.player_profile_vars: list[tk.StringVar] = []
        self.player_name_vars: list[tk.StringVar] = []
        self.sport_var = tk.StringVar(value="inline")
        self.order_mode_var = tk.StringVar(value="choice")
        self.relevance_criterion_var = tk.StringVar(value="alphabetical")
        self.preset_var = tk.StringVar(value="classic_skate")
        self.custom_word_var = tk.StringVar(value="SKATE")
        self.custom_attack_attempts_var = tk.IntVar(value=1)
        self.custom_defense_attempts_var = tk.IntVar(value=1)
        self.custom_uniqueness_var = tk.BooleanVar(value=True)
        self.custom_multiple_attack_enabled_var = tk.BooleanVar(value=False)
        self.custom_no_repetition_var = tk.BooleanVar(value=False)
        self.custom_switch_mode_var = tk.StringVar(value="disabled")
        self.custom_repetition_mode_var = tk.StringVar(value="choice")
        self.custom_repetition_limit_var = tk.IntVar(value=3)
        self.trick_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Configure the game to begin.")
        self._auto_order_mode_value: str | None = None
        self._suppress_trick_updates = False
        self._selected_trick_completion: str | None = None
        self._current_trick_suggestions = []
        self._harness_targets: dict[str, tk.Widget] = {}
        self._harness_prompt_responses: list[str | None] = []
        self._harness_load_selection: str | None = None
        self._refreshing_setup_controls = False

        self.title_font = tkfont.Font(size=18, weight="bold")
        self.subtitle_font = tkfont.Font(size=10)
        self.section_font = tkfont.Font(size=12, weight="bold")
        self.score_name_font = tkfont.Font(size=12, weight="bold")
        self.score_active_font = tkfont.Font(size=18, weight="bold")
        self.score_inactive_font = tkfont.Font(size=18)
        self.score_table_name_font = tkfont.Font(size=10, weight="bold")
        self.score_table_word_font = tkfont.Font(size=16, weight="bold")
        self.score_table_marker_font = tkfont.Font(size=10, weight="bold")
        self.body_font = tkfont.Font(size=11)
        self.small_font = tkfont.Font(size=10)

        self.current_view = "setup"

        self.scroll_host = ttk.Frame(self.root)
        self.scroll_host.pack(fill="both", expand=True)

        self.scroll_canvas = tk.Canvas(
            self.scroll_host,
            highlightthickness=0,
            borderwidth=0,
        )
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        self._register_harness_target("root.scroll_canvas", self.scroll_canvas)

        self.scrollbar = ttk.Scrollbar(
            self.scroll_host,
            orient="vertical",
            command=self.scroll_canvas.yview,
        )
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.container = ttk.Frame(self.scroll_canvas, padding=16)
        self._scroll_window = self.scroll_canvas.create_window(
            (0, 0),
            window=self.container,
            anchor="nw",
        )
        self.container.bind("<Configure>", self._on_container_configure)
        self.scroll_canvas.bind("<Configure>", self._on_canvas_configure)

        self.setup_frame = ttk.Frame(self.container)
        self.game_frame = ttk.Frame(self.container)
        self.history_frame = ttk.Frame(self.container)
        self.setup_details_frame = ttk.Frame(self.container)
        self._register_harness_target("view.setup", self.setup_frame)
        self._register_harness_target("view.match", self.game_frame)
        self._register_harness_target("view.history", self.history_frame)
        self._register_harness_target("view.setup_details", self.setup_details_frame)
        self.players_frame: ttk.Frame | None = None
        self.player_profile_combos: list[ttk.Combobox] = []
        self.player_move_up_buttons: list[ttk.Button] = []
        self.player_move_down_buttons: list[ttk.Button] = []

        self.matchup_label: ttk.Label | None = None
        self.phase_title_label: ttk.Label | None = None
        self.trick_label: ttk.Label | None = None
        self.phase_description_label: ttk.Label | None = None
        self.attempts_label: ttk.Label | None = None
        self.status_label: ttk.Label | None = None
        self.preset_label: ttk.Label | None = None
        self.setup_details_body_label: ttk.Label | None = None
        self.order_preview_label: ttk.Label | None = None
        self.attack_repetition_feedback_label: ttk.Label | None = None
        self.multiple_attack_feedback_label: ttk.Label | None = None
        self.setup_summary_label: ttk.Label | None = None
        self.multiple_attack_frame: ttk.Frame | None = None
        self.multiple_attack_disabled_button: ttk.Radiobutton | None = None
        self.multiple_attack_enabled_button: ttk.Radiobutton | None = None
        self.no_repetition_checkbutton: ttk.Checkbutton | None = None

        self.score_frame: ttk.Frame | None = None
        self.trick_search_frame: ttk.Frame | None = None
        self.trick_entry: ttk.Entry | None = None
        self.trick_dropdown_frame: tk.Frame | None = None
        self.trick_suggestions_listbox: tk.Listbox | None = None

        self.confirm_trick_button: ttk.Button | None = None
        self.cancel_trick_button: ttk.Button | None = None
        self.start_game_button: ttk.Button | None = None
        self.load_from_setup_button: ttk.Button | None = None
        self.success_button: ttk.Button | None = None
        self.failure_button: ttk.Button | None = None
        self.switch_normal_verified_button: ttk.Button | None = None
        self.switch_normal_not_verified_button: ttk.Button | None = None
        self.undo_button: ttk.Button | None = None
        self.save_button: ttk.Button | None = None
        self.load_button: ttk.Button | None = None
        self.history_button: ttk.Button | None = None
        self.setup_details_button: ttk.Button | None = None
        self.add_player_button: ttk.Button | None = None
        self.remove_player_button: ttk.Button | None = None
        self.new_game_button: ttk.Button | None = None
        self.back_to_game_button: ttk.Button | None = None
        self.back_from_setup_details_button: ttk.Button | None = None

        self.history_tree: ttk.Treeview | None = None
        self.preset_combo: ttk.Combobox | None = None
        self.preset_mode_radiobutton: ttk.Radiobutton | None = None
        self.custom_mode_radiobutton: ttk.Radiobutton | None = None
        self.player_count_spinbox: ttk.Spinbox | None = None
        self.sport_combo: ttk.Combobox | None = None
        self.order_mode_combo: ttk.Combobox | None = None
        self.relevance_criterion_combo: ttk.Combobox | None = None
        self.switch_mode_combo: ttk.Combobox | None = None
        self.word_entry: ttk.Entry | None = None
        self.attack_attempts_spinbox: ttk.Spinbox | None = None
        self.attempts_spinbox: ttk.Spinbox | None = None
        self.uniqueness_checkbutton: ttk.Checkbutton | None = None
        self.repetition_mode_combo: ttk.Combobox | None = None
        self.repetition_limit_spinbox: ttk.Spinbox | None = None

        self._build_setup_view()
        self._build_game_view()
        self._build_history_view()
        self._build_setup_details_view()
        self._show_view("setup")

    def run(self) -> None:
        self.root.mainloop()

    def _register_harness_target(self, target_id: str, widget: tk.Widget) -> None:
        self._harness_targets[target_id] = widget

    def get_harness_target(self, target_id: str) -> tk.Widget | None:
        return self._harness_targets.get(target_id)

    def list_harness_targets(self) -> tuple[str, ...]:
        return tuple(sorted(self._harness_targets))

    def get_harness_active_view(self) -> str:
        return self.current_view

    def get_harness_target_state(self, target_id: str) -> str | None:
        widget = self.get_harness_target(target_id)
        if widget is None:
            return None
        try:
            return str(widget.cget("state"))
        except tk.TclError:
            return None

    def queue_harness_prompt_response(self, value: str | None) -> None:
        self._harness_prompt_responses.append(value)

    def set_harness_load_selection(self, value: str) -> None:
        self._harness_load_selection = value

    def _get_default_profile_display_name(self, index: int) -> str:
        if index < len(self.local_profile_display_names):
            return self.local_profile_display_names[index]
        return ""

    def _sync_player_name_from_profile_var(
        self,
        profile_var: tk.StringVar,
        player_name_var: tk.StringVar,
    ) -> None:
        selected_name = profile_var.get().strip()
        player_name_var.set(selected_name)

    def _collect_selected_player_profile_ids(self) -> list[str]:
        profile_names: list[str] = []
        for index, profile_var in enumerate(self.player_profile_vars):
            profile_name = profile_var.get().strip()
            manual_name = (
                self.player_name_vars[index].get().strip()
                if index < len(self.player_name_vars)
                else ""
            )
            if manual_name in self.profile_id_by_display_name:
                profile_name = manual_name
                profile_var.set(manual_name)
            profile_names.append(profile_name)

        if any(not profile_name for profile_name in profile_names):
            raise ValueError("All player profiles are required.")
        if len(set(profile_names)) != len(profile_names):
            raise ValueError("Each player must use a different local profile.")

        try:
            return [
                self.profile_id_by_display_name[profile_name]
                for profile_name in profile_names
            ]
        except KeyError as error:
            raise ValueError("One or more selected player profiles are invalid.") from error

    def _get_effective_order_mode(self) -> str:
        if self.setup_mode_var.get() == "preset":
            preset = self.setup_service.get_preset(self.preset_var.get())
            if preset.policies.initial_turn_order == InitialTurnOrderPolicy.RANDOMIZED:
                return "random"
            if preset.policies.initial_turn_order == InitialTurnOrderPolicy.RELEVANCE:
                return "relevance"
            return "choice"
        return self.order_mode_var.get()

    def _move_player_slot(self, index: int, offset: int) -> None:
        other_index = index + offset
        if not (0 <= index < len(self.player_profile_vars)):
            return
        if not (0 <= other_index < len(self.player_profile_vars)):
            return

        current_value = self.player_profile_vars[index].get()
        other_value = self.player_profile_vars[other_index].get()
        self.player_profile_vars[index].set(other_value)
        self.player_profile_vars[other_index].set(current_value)
        self._refresh_choice_order_buttons()

    def _refresh_choice_order_buttons(self) -> None:
        is_choice_mode = (
            self.setup_mode_var.get() == "custom"
            and self.order_mode_var.get() == "choice"
        )
        for index, button in enumerate(self.player_move_up_buttons):
            button.config(
                state="normal" if is_choice_mode and index > 0 else "disabled"
            )
        for index, button in enumerate(self.player_move_down_buttons):
            button.config(
                state=(
                    "normal"
                    if is_choice_mode and index < len(self.player_move_down_buttons) - 1
                    else "disabled"
                )
            )

    def _refresh_order_preview(self) -> None:
        if self.order_preview_label is None:
            return

        try:
            selected_profile_ids = self._collect_selected_player_profile_ids()
            player_ids, player_profile_ids, player_names = (
                self.setup_service.build_profile_player_slots(selected_profile_ids)
            )
        except ValueError:
            self.order_preview_label.config(
                text="Order preview: select valid local profiles."
            )
            self._refresh_setup_summary()
            return

        order_mode = self._get_effective_order_mode()

        if self.setup_mode_var.get() == "preset":
            preset = self.setup_service.get_preset(self.preset_var.get())
            relevance_criterion = (
                preset.policies.relevance_criterion.value
                if preset.policies.relevance_criterion is not None
                else self.relevance_criterion_var.get()
            )
            explicit_player_order = list(
                preset.policies.explicit_player_order or player_ids
            )
        else:
            relevance_criterion = self.relevance_criterion_var.get()
            explicit_player_order = list(player_ids)

        try:
            preview = self.setup_service.preview_order(
                order_mode=order_mode,
                player_ids=player_ids,
                player_profile_ids=player_profile_ids,
                player_display_names=player_names,
                relevance_criterion=relevance_criterion,
                explicit_player_order=explicit_player_order,
            )
        except ValueError:
            self.order_preview_label.config(
                text="Order preview: unavailable for the current setup."
            )
            self._refresh_setup_summary()
            return

        self.order_preview_label.config(
            text=self.setup_service.build_order_preview_text(
                order_mode=order_mode,
                preview_names=preview,
            )
        )
        self._refresh_setup_summary()

    def _refresh_setup_summary(self) -> None:
        if self.setup_summary_label is None:
            return

        mode_label = "preset" if self.setup_mode_var.get() == "preset" else "custom"
        order_mode = self._get_effective_order_mode()
        attack_attempts = int(self.custom_attack_attempts_var.get())
        defense_attempts = int(self.custom_defense_attempts_var.get())
        selected_names = [
            profile_var.get().strip()
            for profile_var in self.player_profile_vars
            if profile_var.get().strip()
        ]
        if len(selected_names) != len(self.player_profile_vars):
            selected_names = [f"{max(2, self.player_count_var.get())} players"]
        self.setup_summary_label.config(
            text=self.setup_service.build_setup_summary_text(
                mode_label=mode_label,
                sport=self.sport_var.get(),
                player_names=selected_names,
                order_mode=order_mode,
                attack_attempts=attack_attempts,
                defense_attempts=defense_attempts,
                multiple_attack_enabled=bool(
                    self.custom_multiple_attack_enabled_var.get()
                ),
                no_repetition=bool(self.custom_no_repetition_var.get()),
                switch_mode=self.custom_switch_mode_var.get(),
                repetition_mode=self.custom_repetition_mode_var.get(),
                repetition_limit=int(self.custom_repetition_limit_var.get()),
            )
        )

    def _ask_string_dialog(self, title: str, prompt: str) -> str | None:
        if self._harness_prompt_responses:
            return self._harness_prompt_responses.pop(0)

        return simpledialog.askstring(
            title,
            prompt,
            parent=self.root,
        )

    def _resolve_harness_load_selection(
        self, save_files: list[Path]
    ) -> tuple[bool, Path | None]:
        selection = self._harness_load_selection
        if selection is None:
            return False, None

        self._harness_load_selection = None
        normalized = selection.strip().lower()
        if normalized in {"latest", "__latest__"}:
            return True, save_files[-1]

        selected_path = next(
            (path for path in save_files if path.name == selection),
            None,
        )
        return True, selected_path

    def _apply_loaded_controller(self, selected_path: Path) -> None:
        self._load_game_into_controller(selected_path)
        loaded_state = self.controller.get_state()
        if loaded_state.phase == Phase.END:
            self.status_var.set(
                f"Finished game loaded from {selected_path.name}. Consultation mode."
            )
        else:
            self.status_var.set(f"Game loaded from {selected_path.name}.")

        self._show_view("game")
        self._refresh_game_view()

    def _ensure_saves_dir(self) -> Path:
        self.SAVES_DIR.mkdir(parents=True, exist_ok=True)
        return self.SAVES_DIR

    def _build_save_path(self) -> Path:
        saves_dir = self._ensure_saves_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
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
        self.setup_details_frame.pack_forget()

        if view_name == "setup":
            self.setup_frame.pack(fill="both", expand=True)
        elif view_name == "game":
            self.game_frame.pack(fill="both", expand=True)
        elif view_name == "history":
            self.history_frame.pack(fill="both", expand=True)
        elif view_name == "setup_details":
            self.setup_details_frame.pack(fill="both", expand=True)

        self.current_view = view_name
        self._refresh_scroll_layout(reset_position=True)
        if view_name == "setup":
            self._focus_widget(self.preset_combo)
        elif view_name == "history":
            self._focus_widget(self.back_to_game_button)
        elif view_name == "setup_details":
            self._focus_widget(self.back_from_setup_details_button)

    def _on_container_configure(self, _event=None) -> None:
        self._refresh_scroll_layout(reset_position=False)

    def _on_canvas_configure(self, event) -> None:
        self.scroll_canvas.itemconfigure(self._scroll_window, width=event.width)
        self._refresh_scroll_layout(reset_position=False)

    def _refresh_scroll_layout(self, *, reset_position: bool) -> None:
        self.container.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        if reset_position:
            self.scroll_canvas.yview_moveto(0.0)

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

        ttk.Label(form, text="Setup mode:", font=self.body_font).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        setup_mode_frame = ttk.Frame(form)
        setup_mode_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 18))

        self.preset_mode_radiobutton = ttk.Radiobutton(
            setup_mode_frame,
            text="Official preset",
            variable=self.setup_mode_var,
            value="preset",
        )
        self.preset_mode_radiobutton.pack(side="left", padx=(0, 10))
        self._register_harness_target(
            "setup.mode_preset_radiobutton",
            self.preset_mode_radiobutton,
        )

        self.custom_mode_radiobutton = ttk.Radiobutton(
            setup_mode_frame,
            text="No preset",
            variable=self.setup_mode_var,
            value="custom",
        )
        self.custom_mode_radiobutton.pack(side="left")
        self._register_harness_target(
            "setup.mode_custom_radiobutton",
            self.custom_mode_radiobutton,
        )

        ttk.Label(form, text="Preset:", font=self.body_font).grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )

        self.preset_combo = ttk.Combobox(
            form,
            textvariable=self.preset_var,
            values=self._get_official_preset_names(),
            state="readonly",
            width=36,
        )
        self.preset_combo.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        self._register_harness_target("setup.preset_combo", self.preset_combo)

        ttk.Label(form, text="Sport:", font=self.body_font).grid(
            row=4, column=0, sticky="w", pady=(0, 6)
        )

        self.sport_combo = ttk.Combobox(
            form,
            textvariable=self.sport_var,
            values=("inline",),
            state="readonly",
            width=36,
        )
        self.sport_combo.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        self._register_harness_target("setup.sport_combo", self.sport_combo)

        ttk.Label(form, text="Number of players:", font=self.body_font).grid(
            row=6, column=0, sticky="w", pady=(0, 6)
        )

        self.player_count_spinbox = ttk.Spinbox(
            form,
            from_=2,
            to=8,
            textvariable=self.player_count_var,
            width=6,
            command=self._rebuild_player_inputs,
        )
        self.player_count_spinbox.grid(row=7, column=0, sticky="w", pady=(0, 18))
        self.player_count_spinbox.bind("<FocusOut>", lambda _event: self._rebuild_player_inputs())
        self.player_count_spinbox.bind("<Return>", lambda _event: self._rebuild_player_inputs())
        self._register_harness_target("setup.player_count_spinbox", self.player_count_spinbox)

        ttk.Label(form, text="Players:", font=self.body_font).grid(
            row=8, column=0, sticky="w", pady=(0, 6)
        )

        self.players_frame = ttk.Frame(form)
        self.players_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 18))

        ttk.Label(form, text="Order:", font=self.body_font).grid(
            row=10, column=0, sticky="w", pady=(0, 6)
        )
        self.order_mode_combo = ttk.Combobox(
            form,
            textvariable=self.order_mode_var,
            values=("choice", "random", "relevance"),
            state="readonly",
            width=36,
        )
        self.order_mode_combo.grid(
            row=11, column=0, columnspan=2, sticky="ew", pady=(0, 12)
        )
        self._register_harness_target("setup.order_mode_combo", self.order_mode_combo)

        ttk.Label(form, text="Relevance criterion:", font=self.body_font).grid(
            row=12, column=0, sticky="w", pady=(0, 6)
        )
        self.relevance_criterion_combo = ttk.Combobox(
            form,
            textvariable=self.relevance_criterion_var,
            values=("alphabetical", "age", "experience_time", "local_rank"),
            state="readonly",
            width=36,
        )
        self.relevance_criterion_combo.grid(
            row=13, column=0, columnspan=2, sticky="ew", pady=(0, 18)
        )
        self._register_harness_target(
            "setup.relevance_criterion_combo",
            self.relevance_criterion_combo,
        )

        self.order_preview_label = ttk.Label(
            form,
            text="",
            font=self.small_font,
            wraplength=420,
            justify="left",
        )
        self.order_preview_label.grid(
            row=14, column=0, columnspan=2, sticky="w", pady=(0, 18)
        )
        self._register_harness_target("setup.order_preview_label", self.order_preview_label)

        ttk.Label(form, text="Word:", font=self.body_font).grid(
            row=15, column=0, sticky="w", pady=(0, 6)
        )
        self.word_entry = ttk.Entry(
            form,
            width=36,
            textvariable=self.custom_word_var,
        )
        self.word_entry.grid(row=16, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        self._register_harness_target("setup.word_entry", self.word_entry)

        ttk.Label(form, text="Attack attempts:", font=self.body_font).grid(
            row=17, column=0, sticky="w", pady=(0, 6)
        )

        self.attack_attempts_spinbox = ttk.Spinbox(
            form,
            from_=1,
            to=3,
            textvariable=self.custom_attack_attempts_var,
            width=6,
        )
        self.attack_attempts_spinbox.grid(row=18, column=0, sticky="w", pady=(0, 18))
        self._register_harness_target(
            "setup.attack_attempts_spinbox",
            self.attack_attempts_spinbox,
        )

        ttk.Label(form, text="Multiple Attack:", font=self.body_font).grid(
            row=19, column=0, sticky="w", pady=(0, 6)
        )

        self.multiple_attack_frame = ttk.Frame(form)
        self.multiple_attack_frame.grid(
            row=20, column=0, columnspan=2, sticky="w", pady=(0, 18)
        )
        self._register_harness_target(
            "setup.multiple_attack_frame",
            self.multiple_attack_frame,
        )

        self.multiple_attack_disabled_button = ttk.Radiobutton(
            self.multiple_attack_frame,
            text="Disabled",
            variable=self.custom_multiple_attack_enabled_var,
            value=False,
        )
        self.multiple_attack_disabled_button.pack(side="left", padx=(0, 12))
        self._register_harness_target(
            "setup.multiple_attack_disabled_button",
            self.multiple_attack_disabled_button,
        )

        self.no_repetition_checkbutton = ttk.Checkbutton(
            self.multiple_attack_frame,
            text="No Repetition",
            variable=self.custom_no_repetition_var,
            onvalue=True,
            offvalue=False,
        )
        self.no_repetition_checkbutton.pack(side="left", padx=(0, 12))
        self._register_harness_target(
            "setup.no_repetition_checkbutton",
            self.no_repetition_checkbutton,
        )

        self.multiple_attack_enabled_button = ttk.Radiobutton(
            self.multiple_attack_frame,
            text="Enabled",
            variable=self.custom_multiple_attack_enabled_var,
            value=True,
        )
        self.multiple_attack_enabled_button.pack(side="left")
        self._register_harness_target(
            "setup.multiple_attack_enabled_button",
            self.multiple_attack_enabled_button,
        )

        self.multiple_attack_feedback_label = ttk.Label(
            self.multiple_attack_frame,
            text="",
            font=self.small_font,
            justify="left",
            wraplength=520,
        )
        self.multiple_attack_feedback_label.pack(side="left", padx=(12, 0))
        self._register_harness_target(
            "setup.multiple_attack_feedback_label",
            self.multiple_attack_feedback_label,
        )

        ttk.Label(form, text="Defense attempts:", font=self.body_font).grid(
            row=21, column=0, sticky="w", pady=(0, 6)
        )

        self.attempts_spinbox = ttk.Spinbox(
            form,
            from_=1,
            to=3,
            textvariable=self.custom_defense_attempts_var,
            width=6,
        )
        self.attempts_spinbox.grid(row=22, column=0, sticky="w", pady=(0, 24))
        self._register_harness_target(
            "setup.defense_attempts_spinbox",
            self.attempts_spinbox,
        )

        ttk.Label(form, text="Uniqueness:", font=self.body_font).grid(
            row=23, column=0, sticky="w", pady=(0, 6)
        )

        self.uniqueness_checkbutton = ttk.Checkbutton(
            form,
            text="Enabled",
            variable=self.custom_uniqueness_var,
            onvalue=True,
            offvalue=False,
        )
        self.uniqueness_checkbutton.grid(
            row=24, column=0, columnspan=2, sticky="w", pady=(0, 18)
        )
        self._register_harness_target(
            "setup.uniqueness_checkbutton",
            self.uniqueness_checkbutton,
        )

        ttk.Label(form, text="Repetition mode:", font=self.body_font).grid(
            row=25, column=0, sticky="w", pady=(0, 6)
        )

        self.repetition_mode_combo = ttk.Combobox(
            form,
            textvariable=self.custom_repetition_mode_var,
            values=("choice", "common", "disabled"),
            state="readonly",
            width=18,
        )
        self.repetition_mode_combo.grid(
            row=26, column=0, columnspan=2, sticky="w", pady=(0, 18)
        )
        self._register_harness_target(
            "setup.repetition_mode_combo",
            self.repetition_mode_combo,
        )

        ttk.Label(form, text="Repetition limit:", font=self.body_font).grid(
            row=27, column=0, sticky="w", pady=(0, 6)
        )

        self.repetition_limit_spinbox = ttk.Spinbox(
            form,
            from_=1,
            to=9,
            textvariable=self.custom_repetition_limit_var,
            width=6,
        )
        self.repetition_limit_spinbox.grid(
            row=28, column=0, sticky="w", pady=(0, 24)
        )
        self._register_harness_target(
            "setup.repetition_limit_spinbox",
            self.repetition_limit_spinbox,
        )

        self.attack_repetition_feedback_label = ttk.Label(
            form,
            text="",
            font=self.small_font,
            wraplength=520,
            justify="left",
        )
        self.attack_repetition_feedback_label.grid(
            row=29, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        self._register_harness_target(
            "setup.attack_repetition_feedback_label",
            self.attack_repetition_feedback_label,
        )

        ttk.Label(form, text="Switch:", font=self.body_font).grid(
            row=30, column=0, sticky="w", pady=(0, 6)
        )

        self.switch_mode_combo = ttk.Combobox(
            form,
            textvariable=self.custom_switch_mode_var,
            values=("disabled", "enabled", "normal", "verified"),
            state="readonly",
            width=18,
        )
        self.switch_mode_combo.grid(
            row=31, column=0, columnspan=2, sticky="w", pady=(0, 18)
        )
        self._register_harness_target(
            "setup.switch_mode_combo",
            self.switch_mode_combo,
        )

        self.setup_summary_label = ttk.Label(
            form,
            text="",
            font=self.small_font,
            wraplength=520,
            justify="left",
        )
        self.setup_summary_label.grid(
            row=32, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        self._register_harness_target(
            "setup.summary_label",
            self.setup_summary_label,
        )

        def refresh_attack_repetition_feedback() -> bool:
            assert self.repetition_limit_spinbox is not None
            assert self.attack_repetition_feedback_label is not None

            use_preset = self.setup_mode_var.get() == "preset"
            repetition_limit_state = (
                "disabled"
                if self.custom_repetition_mode_var.get() == "disabled"
                else ("normal" if not use_preset else "disabled")
            )
            self.repetition_limit_spinbox.config(state=repetition_limit_state)

            compatible = self.setup_service.is_attack_repetition_synergy_compatible(
                attack_attempts=int(self.custom_attack_attempts_var.get()),
                repetition_mode=self.custom_repetition_mode_var.get(),
                repetition_limit=int(self.custom_repetition_limit_var.get()),
                multiple_attack_enabled=bool(
                    self.custom_multiple_attack_enabled_var.get()
                ),
                no_repetition=bool(self.custom_no_repetition_var.get()),
            )
            feedback = self.setup_service.get_attack_repetition_synergy_feedback(
                attack_attempts=int(self.custom_attack_attempts_var.get()),
                repetition_mode=self.custom_repetition_mode_var.get(),
                repetition_limit=int(self.custom_repetition_limit_var.get()),
                multiple_attack_enabled=bool(
                    self.custom_multiple_attack_enabled_var.get()
                ),
                no_repetition=bool(self.custom_no_repetition_var.get()),
                max_limit=9,
            )
            self.attack_repetition_feedback_label.config(text=feedback or "")
            if self.start_game_button is not None:
                self.start_game_button.config(
                    state="normal" if compatible else "disabled"
                )
            self._refresh_setup_summary()
            return compatible

        def refresh_multiple_attack_feedback() -> None:
            assert self.multiple_attack_feedback_label is not None
            attack_attempts = int(self.custom_attack_attempts_var.get())
            if attack_attempts <= 1:
                self.multiple_attack_feedback_label.config(
                    text="Available only when Attack attempts are greater than 1."
                )
            elif self.custom_multiple_attack_enabled_var.get():
                self.multiple_attack_feedback_label.config(
                    text="Enabled: the attacker may change trick from the second attack attempt."
                )
            elif self.custom_no_repetition_var.get():
                self.multiple_attack_feedback_label.config(
                    text="No Repetition: repeated failures of the same trick count once per attack turn."
                )
            else:
                self.multiple_attack_feedback_label.config(
                    text="Disabled: the attacker keeps the same trick and repetition counts launch by launch."
                )

        def refresh_setup_controls() -> None:
            if self._refreshing_setup_controls:
                return
            self._refreshing_setup_controls = True
            try:
                assert self.preset_combo is not None
                assert self.sport_combo is not None
                assert self.player_count_spinbox is not None
                assert self.order_mode_combo is not None
                assert self.relevance_criterion_combo is not None
                assert self.word_entry is not None
                assert self.attack_attempts_spinbox is not None
                assert self.multiple_attack_frame is not None
                assert self.multiple_attack_disabled_button is not None
                assert self.multiple_attack_enabled_button is not None
                assert self.no_repetition_checkbutton is not None
                assert self.attempts_spinbox is not None
                assert self.uniqueness_checkbutton is not None
                assert self.repetition_mode_combo is not None
                assert self.switch_mode_combo is not None

                use_preset = self.setup_mode_var.get() == "preset"
                preset_names = self._get_official_preset_names()

                if self.preset_var.get() not in preset_names:
                    self.preset_var.set(preset_names[0])

                self.preset_combo.config(values=preset_names)
                self.sport_var.set("inline")
                self.sport_combo.config(values=("inline",), state="disabled")

                if use_preset:
                    preset = self.setup_service.get_preset(self.preset_var.get())
                    self.custom_word_var.set(preset.rule_set.letters_word)
                    self.custom_attack_attempts_var.set(preset.rule_set.attack_attempts)
                    self.custom_defense_attempts_var.set(preset.rule_set.defense_attempts)
                    self.custom_uniqueness_var.set(preset.fine_rules.uniqueness_enabled)
                    self.custom_multiple_attack_enabled_var.set(
                        preset.fine_rules.multiple_attack_enabled
                    )
                    self.custom_no_repetition_var.set(preset.fine_rules.no_repetition)
                    self.custom_switch_mode_var.set(preset.fine_rules.switch_mode)
                    if (
                        self.custom_repetition_mode_var.get()
                        != preset.fine_rules.repetition_mode
                    ):
                        self.custom_repetition_mode_var.set(
                            preset.fine_rules.repetition_mode
                        )
                    self.custom_repetition_limit_var.set(preset.fine_rules.repetition_limit)

                    if preset.structure_name == "one_vs_one":
                        self.player_count_var.set(2)
                        self.player_count_spinbox.config(state="disabled")
                    else:
                        if self.player_count_var.get() < 3:
                            self.player_count_var.set(3)
                        self.player_count_spinbox.config(state="normal")

                    self.preset_combo.config(state="readonly")
                    if preset.policies.initial_turn_order == InitialTurnOrderPolicy.RANDOMIZED:
                        self.order_mode_var.set("random")
                    elif preset.policies.initial_turn_order == InitialTurnOrderPolicy.RELEVANCE:
                        self.order_mode_var.set("relevance")
                        if preset.policies.relevance_criterion is not None:
                            self.relevance_criterion_var.set(
                                preset.policies.relevance_criterion.value
                            )
                    else:
                        self.order_mode_var.set("choice")
                    self.order_mode_combo.config(state="disabled")
                    relevance_state = (
                        "disabled"
                        if preset.policies.initial_turn_order
                        != InitialTurnOrderPolicy.RELEVANCE
                        else "readonly"
                    )
                    self.relevance_criterion_combo.config(state=relevance_state)
                    self._auto_order_mode_value = self.order_mode_var.get()
                    self.word_entry.config(state="readonly")
                    self.attack_attempts_spinbox.config(state="disabled")
                    self.multiple_attack_disabled_button.config(state="disabled")
                    self.multiple_attack_enabled_button.config(state="disabled")
                    self.no_repetition_checkbutton.config(state="disabled")
                    self.attempts_spinbox.config(state="disabled")
                    self.uniqueness_checkbutton.config(state="disabled")
                    self.repetition_mode_combo.config(state="disabled")
                    self.switch_mode_combo.config(state="disabled")
                else:
                    if self.player_count_var.get() < 2:
                        self.player_count_var.set(2)
                    self.preset_combo.config(state="disabled")
                    self.player_count_spinbox.config(state="normal")
                    desired_order_mode = (
                        "choice" if self.player_count_var.get() == 2 else "random"
                    )
                    if (
                        self._auto_order_mode_value is None
                        or self.order_mode_var.get() == self._auto_order_mode_value
                    ):
                        self.order_mode_var.set(desired_order_mode)
                    self._auto_order_mode_value = desired_order_mode
                    self.order_mode_combo.config(state="readonly")
                    relevance_state = (
                        "readonly"
                        if self.order_mode_var.get() == "relevance"
                        else "disabled"
                    )
                    self.relevance_criterion_combo.config(state=relevance_state)
                    self.word_entry.config(state="normal")
                    self.attack_attempts_spinbox.config(state="normal")
                    multiple_attack_available = (
                        int(self.custom_attack_attempts_var.get()) > 1
                    )
                    if multiple_attack_available:
                        self.multiple_attack_frame.grid(
                            row=20,
                            column=0,
                            columnspan=2,
                            sticky="w",
                            pady=(0, 18),
                        )
                    else:
                        self.multiple_attack_frame.grid_remove()
                    self.multiple_attack_disabled_button.config(
                        state="normal" if multiple_attack_available else "disabled"
                    )
                    self.multiple_attack_enabled_button.config(
                        state="normal" if multiple_attack_available else "disabled"
                    )
                    self.no_repetition_checkbutton.config(
                        state="normal" if multiple_attack_available else "disabled"
                    )
                    if not multiple_attack_available:
                        self.custom_multiple_attack_enabled_var.set(False)
                        self.custom_no_repetition_var.set(False)
                    self.attempts_spinbox.config(state="normal")
                    self.uniqueness_checkbutton.config(state="normal")
                    self.repetition_mode_combo.config(state="readonly")
                    self.switch_mode_combo.config(
                        state=(
                            "readonly"
                            if self.sport_var.get() == "inline"
                            else "disabled"
                        )
                    )

                if use_preset and self.multiple_attack_frame is not None:
                    if int(self.custom_attack_attempts_var.get()) > 1:
                        self.multiple_attack_frame.grid(
                            row=20,
                            column=0,
                            columnspan=2,
                            sticky="w",
                            pady=(0, 18),
                        )
                    else:
                        self.multiple_attack_frame.grid_remove()
                        self.custom_multiple_attack_enabled_var.set(False)
                        self.custom_no_repetition_var.set(False)

                refresh_multiple_attack_feedback()
                refresh_attack_repetition_feedback()
                target_player_count = max(2, self.player_count_var.get())
                if len(self.player_profile_vars) != target_player_count:
                    self._rebuild_player_inputs()
                self._refresh_choice_order_buttons()
                self._refresh_order_preview()
            finally:
                self._refreshing_setup_controls = False

        self.setup_mode_var.trace_add("write", lambda *_args: refresh_setup_controls())
        self.preset_var.trace_add("write", lambda *_args: refresh_setup_controls())
        self.order_mode_var.trace_add("write", lambda *_args: refresh_setup_controls())
        self.player_count_var.trace_add(
            "write", lambda *_args: self._rebuild_player_inputs()
        )
        self.relevance_criterion_var.trace_add(
            "write", lambda *_args: self._refresh_order_preview()
        )
        self.custom_repetition_mode_var.trace_add(
            "write", lambda *_args: refresh_setup_controls()
        )
        self.custom_attack_attempts_var.trace_add(
            "write", lambda *_args: refresh_setup_controls()
        )
        self.custom_multiple_attack_enabled_var.trace_add(
            "write", lambda *_args: refresh_setup_controls()
        )
        self.custom_no_repetition_var.trace_add(
            "write", lambda *_args: refresh_setup_controls()
        )
        self.custom_switch_mode_var.trace_add(
            "write", lambda *_args: refresh_setup_controls()
        )
        self.custom_repetition_limit_var.trace_add(
            "write", lambda *_args: refresh_attack_repetition_feedback()
        )
        self.trick_var.trace_add("write", lambda *_args: self._refresh_trick_suggestions())

        buttons = ttk.Frame(form)
        buttons.grid(row=33, column=0, columnspan=2, pady=(6, 0))

        self.start_game_button = ttk.Button(
            buttons,
            text="Start game",
            command=self._start_game,
            width=18,
        )
        self.start_game_button.pack(side="left", padx=6)
        self._bind_button_keyboard_activation(self.start_game_button)
        self._register_harness_target("setup.start_game_button", self.start_game_button)

        self.load_from_setup_button = ttk.Button(
            buttons,
            text="Load saved game",
            command=self._load_game_from_setup,
            width=18,
        )
        self.load_from_setup_button.pack(side="left", padx=6)
        self._bind_button_keyboard_activation(self.load_from_setup_button)
        self._register_harness_target(
            "setup.load_from_setup_button",
            self.load_from_setup_button,
        )

        self._rebuild_player_inputs()
        refresh_setup_controls()

    def _rebuild_player_inputs(self) -> None:
        assert self.players_frame is not None

        existing_profile_values = [var.get() for var in self.player_profile_vars]
        existing_name_values = [var.get() for var in self.player_name_vars]
        for target_id in tuple(self._harness_targets):
            if target_id.startswith("setup.player_name_entry.") or target_id.startswith(
                "setup.player_profile_combo."
            ) or target_id.startswith(
                "setup.player_move_up_button."
            ) or target_id.startswith(
                "setup.player_move_down_button."
            ):
                self._harness_targets.pop(target_id, None)

        for child in self.players_frame.winfo_children():
            child.destroy()

        player_count = max(2, self.player_count_var.get())
        self.player_profile_vars = []
        self.player_name_vars = [
            tk.StringVar()
            for index in range(player_count)
        ]
        self.player_profile_combos = []
        self.player_move_up_buttons = []
        self.player_move_down_buttons = []

        for index, player_var in enumerate(self.player_name_vars, start=1):
            profile_value = (
                existing_name_values[index - 1]
                if index - 1 < len(existing_name_values)
                and existing_name_values[index - 1] in self.profile_id_by_display_name
                else (
                    existing_profile_values[index - 1]
                    if index - 1 < len(existing_profile_values)
                    and existing_profile_values[index - 1] in self.profile_id_by_display_name
                    else self._get_default_profile_display_name(index - 1)
                )
            )
            profile_var = tk.StringVar(value=profile_value)
            profile_var.trace_add(
                "write",
                lambda *_args, profile_var=profile_var, player_var=player_var: (
                    self._sync_player_name_from_profile_var(profile_var, player_var),
                    self._refresh_order_preview(),
                ),
            )
            self.player_profile_vars.append(profile_var)
            self._sync_player_name_from_profile_var(profile_var, player_var)

            ttk.Label(
                self.players_frame,
                text=f"Player {index} profile:",
                font=self.body_font,
            ).grid(row=(index - 1) * 4, column=0, sticky="w", pady=(0, 6))
            profile_combo = ttk.Combobox(
                self.players_frame,
                textvariable=profile_var,
                values=tuple(self.local_profile_display_names),
                state="readonly",
                width=36,
            )
            profile_combo.grid(
                row=(index - 1) * 4 + 1,
                column=0,
                sticky="ew",
                pady=(0, 6),
            )
            self.player_profile_combos.append(profile_combo)
            self._register_harness_target(
                f"setup.player_profile_combo.{index}",
                profile_combo,
            )

            move_frame = ttk.Frame(self.players_frame)
            move_frame.grid(
                row=(index - 1) * 4 + 1,
                column=1,
                sticky="nw",
                padx=(8, 0),
            )
            move_up_button = ttk.Button(
                move_frame,
                text="Up",
                width=6,
                command=lambda index=index - 1: self._move_player_slot(index, -1),
            )
            move_up_button.pack(fill="x", pady=(0, 4))
            move_down_button = ttk.Button(
                move_frame,
                text="Down",
                width=6,
                command=lambda index=index - 1: self._move_player_slot(index, 1),
            )
            move_down_button.pack(fill="x")
            self.player_move_up_buttons.append(move_up_button)
            self.player_move_down_buttons.append(move_down_button)
            self._register_harness_target(
                f"setup.player_move_up_button.{index}",
                move_up_button,
            )
            self._register_harness_target(
                f"setup.player_move_down_button.{index}",
                move_down_button,
            )

            ttk.Label(
                self.players_frame,
                text=f"Player {index} name:",
                font=self.small_font,
            ).grid(row=(index - 1) * 4 + 2, column=0, sticky="w", pady=(0, 4))
            entry = ttk.Entry(
                self.players_frame,
                textvariable=player_var,
                width=36,
                state="readonly",
            )
            entry.grid(
                row=(index - 1) * 4 + 3,
                column=0,
                sticky="ew",
                pady=(0, 12),
            )
            self._register_harness_target(
                f"setup.player_name_entry.{index}",
                entry,
            )

        self._refresh_choice_order_buttons()
        self._refresh_setup_summary()

    # =========================
    # Game view
    # =========================

    def _build_game_view(self) -> None:
        frame = self.game_frame
        frame.columnconfigure(0, weight=1)

        self.matchup_label = ttk.Label(frame, text="", font=self.title_font)
        self.matchup_label.grid(row=0, column=0, pady=(6, 6))

        self.score_frame = ttk.Frame(frame)
        self.score_frame.grid(row=1, column=0, sticky="ew", pady=(0, 24))
        self._register_harness_target("match.score_frame", self.score_frame)

        self.preset_label = ttk.Label(frame, text="", font=self.small_font)
        self.preset_label.grid(row=2, column=0, pady=(0, 10))

        self.phase_title_label = ttk.Label(frame, text="", font=self.section_font)
        self.phase_title_label.grid(row=3, column=0, pady=(0, 14))
        self._register_harness_target("match.phase_title_label", self.phase_title_label)

        self.trick_label = ttk.Label(frame, text="", font=self.section_font)
        self.trick_label.grid(row=4, column=0, pady=(0, 10))
        self._register_harness_target("match.trick_label", self.trick_label)

        self.phase_description_label = ttk.Label(frame, text="", font=self.body_font)
        self.phase_description_label.grid(row=5, column=0, pady=(0, 8))
        self._register_harness_target(
            "match.phase_description_label",
            self.phase_description_label,
        )

        self.attempts_label = ttk.Label(frame, text="", font=self.body_font)
        self.attempts_label.grid(row=6, column=0, pady=(0, 18))
        self._register_harness_target("match.attempts_label", self.attempts_label)

        action_buttons = ttk.Frame(frame)
        action_buttons.grid(row=7, column=0, pady=(0, 14))

        self.success_button = ttk.Button(
            action_buttons,
            text="Landed",
            command=lambda: self._resolve_defense(True),
            width=14,
        )
        self.success_button.pack(side="left", padx=8)
        self._register_harness_target("match.success_button", self.success_button)

        self.failure_button = ttk.Button(
            action_buttons,
            text="Missed",
            command=lambda: self._resolve_defense(False),
            width=14,
        )
        self.failure_button.pack(side="left", padx=8)
        self._register_harness_target("match.failure_button", self.failure_button)

        self.switch_normal_verified_button = ttk.Button(
            action_buttons,
            text="Normal verified",
            command=lambda: self._resolve_verified_switch_attack(True),
            width=16,
        )
        self.switch_normal_verified_button.pack(side="left", padx=8)
        self._register_harness_target(
            "match.switch_normal_verified_button",
            self.switch_normal_verified_button,
        )

        self.switch_normal_not_verified_button = ttk.Button(
            action_buttons,
            text="Normal not verified",
            command=lambda: self._resolve_verified_switch_attack(False),
            width=18,
        )
        self.switch_normal_not_verified_button.pack(side="left", padx=8)
        self._register_harness_target(
            "match.switch_normal_not_verified_button",
            self.switch_normal_not_verified_button,
        )

        session_buttons = ttk.Frame(frame)
        session_buttons.grid(row=8, column=0, pady=(0, 20))

        self.undo_button = ttk.Button(
            session_buttons,
            text="Undo",
            command=self._undo_action,
            width=10,
        )
        self.undo_button.pack(side="left", padx=6)
        self._register_harness_target("match.undo_button", self.undo_button)

        self.save_button = ttk.Button(
            session_buttons,
            text="Save",
            command=self._save_game,
            width=10,
        )
        self.save_button.pack(side="left", padx=6)
        self._register_harness_target("match.save_button", self.save_button)

        self.load_button = ttk.Button(
            session_buttons,
            text="Load",
            command=self._load_game_during_session,
            width=10,
        )
        self.load_button.pack(side="left", padx=6)
        self._register_harness_target("match.load_button", self.load_button)

        self.history_button = ttk.Button(
            session_buttons,
            text="History",
            command=self._show_history_view,
            width=10,
        )
        self.history_button.pack(side="left", padx=6)
        self._bind_button_keyboard_activation(self.history_button)
        self._register_harness_target("match.history_button", self.history_button)

        self.setup_details_button = ttk.Button(
            session_buttons,
            text="Setup details",
            command=self._show_setup_details_view,
            width=12,
        )
        self.setup_details_button.pack(side="left", padx=6)
        self._bind_button_keyboard_activation(self.setup_details_button)
        self._register_harness_target(
            "match.setup_details_button",
            self.setup_details_button,
        )

        self.add_player_button = ttk.Button(
            session_buttons,
            text="Add player",
            command=self._add_player_between_turns,
            width=10,
        )
        self.add_player_button.pack(side="left", padx=6)
        self._bind_button_keyboard_activation(self.add_player_button)
        self._register_harness_target("match.add_player_button", self.add_player_button)

        self.remove_player_button = ttk.Button(
            session_buttons,
            text="Remove player",
            command=self._remove_player_between_turns,
            width=10,
        )
        self.remove_player_button.pack(side="left", padx=6)
        self._bind_button_keyboard_activation(self.remove_player_button)
        self._register_harness_target(
            "match.remove_player_button",
            self.remove_player_button,
        )

        self.new_game_button = ttk.Button(
            session_buttons,
            text="New game",
            command=self._return_to_setup,
            width=10,
        )
        self.new_game_button.pack(side="left", padx=6)
        self._bind_button_keyboard_activation(self.new_game_button)
        self._register_harness_target("match.new_game_button", self.new_game_button)

        self.status_label = ttk.Label(
            frame,
            textvariable=self.status_var,
            font=self.small_font,
            justify="center",
            anchor="center",
            wraplength=760,
        )
        self.status_label.grid(row=9, column=0, sticky="ew", pady=(0, 14))
        self._register_harness_target("match.status_label", self.status_label)

        trick_zone = ttk.Frame(frame)
        trick_zone.grid(row=10, column=0, sticky="ew")
        trick_zone.columnconfigure(0, weight=1)

        ttk.Label(
            trick_zone,
            text="Search trick",
            font=self.section_font,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.trick_search_frame = ttk.Frame(trick_zone)
        self.trick_search_frame.grid(row=1, column=0, sticky="ew")
        self.trick_search_frame.columnconfigure(0, weight=1)

        self.trick_entry = ttk.Entry(
            self.trick_search_frame,
            textvariable=self.trick_var,
            width=40,
        )
        self.trick_entry.grid(row=0, column=0, sticky="ew")
        self._register_harness_target("match.trick_entry", self.trick_entry)
        self.trick_entry.bind(
            "<KeyRelease>",
            lambda _event: self._refresh_trick_suggestions(),
        )
        self.trick_entry.bind("<Down>", self._focus_first_trick_suggestion)
        self.trick_entry.bind("<Return>", self._handle_trick_entry_submit)

        self.trick_dropdown_frame = tk.Frame(
            self.trick_search_frame,
            bd=1,
            relief="solid",
            highlightthickness=0,
        )
        self.trick_dropdown_frame.grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self._register_harness_target(
            "match.trick_dropdown_frame",
            self.trick_dropdown_frame,
        )

        self.trick_suggestions_listbox = tk.Listbox(
            self.trick_dropdown_frame,
            height=6,
            exportselection=False,
            activestyle="none",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
        )
        self.trick_suggestions_listbox.pack(fill="both", expand=True, padx=1, pady=1)
        self._register_harness_target(
            "match.trick_suggestions_listbox",
            self.trick_suggestions_listbox,
        )
        self.trick_suggestions_listbox.bind(
            "<<ListboxSelect>>",
            lambda _event: self._handle_trick_suggestion_selection(),
        )
        self.trick_suggestions_listbox.bind(
            "<Return>",
            self._handle_trick_suggestion_activate,
        )
        self.trick_suggestions_listbox.bind(
            "<Double-Button-1>",
            self._handle_trick_suggestion_activate,
        )
        self.trick_dropdown_frame.grid_remove()

        buttons_row = ttk.Frame(trick_zone)
        buttons_row.grid(row=2, column=0)

        self.confirm_trick_button = ttk.Button(
            buttons_row,
            text="Set trick",
            command=self._confirm_trick,
            width=14,
        )
        self.confirm_trick_button.pack(side="left", padx=6)
        self._bind_button_keyboard_activation(self.confirm_trick_button)
        self._register_harness_target(
            "match.confirm_trick_button",
            self.confirm_trick_button,
        )

        self.cancel_trick_button = ttk.Button(
            buttons_row,
            text="Fail turn",
            command=self._cancel_trick,
            width=14,
        )
        self.cancel_trick_button.pack(side="left", padx=6)
        self._bind_button_keyboard_activation(self.cancel_trick_button)
        self._register_harness_target(
            "match.cancel_trick_button",
            self.cancel_trick_button,
        )

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
        self._register_harness_target("history.tree", self.history_tree)

        controls = ttk.Frame(frame)
        controls.grid(row=2, column=0, pady=(14, 0))

        self.back_to_game_button = ttk.Button(
            controls,
            text="Back to game",
            command=self._show_game_view,
            width=16,
        )
        self.back_to_game_button.pack()
        self._bind_button_keyboard_activation(self.back_to_game_button)
        self._register_harness_target(
            "history.back_to_game_button",
            self.back_to_game_button,
        )

    def _build_setup_details_view(self) -> None:
        frame = self.setup_details_frame
        frame.columnconfigure(0, weight=1)

        title = ttk.Label(frame, text="Setup details", font=self.title_font)
        title.grid(row=0, column=0, pady=(6, 18))

        card = ttk.Frame(frame, padding=18)
        card.grid(row=1, column=0, sticky="ew")
        card.columnconfigure(0, weight=1)

        subtitle = ttk.Label(
            card,
            text="Active match configuration",
            font=self.section_font,
        )
        subtitle.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.setup_details_body_label = ttk.Label(
            card,
            text="",
            font=self.body_font,
            justify="left",
            anchor="w",
            wraplength=760,
        )
        self.setup_details_body_label.grid(row=1, column=0, sticky="ew")
        self._register_harness_target(
            "setup_details.body_label",
            self.setup_details_body_label,
        )

        controls = ttk.Frame(frame)
        controls.grid(row=2, column=0, pady=(18, 0))

        self.back_from_setup_details_button = ttk.Button(
            controls,
            text="Back to game",
            command=self._show_game_view,
            width=16,
        )
        self.back_from_setup_details_button.pack()
        self._bind_button_keyboard_activation(self.back_from_setup_details_button)
        self._register_harness_target(
            "setup_details.back_to_game_button",
            self.back_from_setup_details_button,
        )

    # =========================
    # Game actions
    # =========================

    def _load_game_into_controller(self, selected_path: Path) -> None:
        self.controller = self.setup_service.load_controller(str(selected_path))
        self._clear_trick_selection()

    def _resolve_selected_save_path(
        self,
        save_files: list[Path],
        selected_name: str,
    ) -> Path | None:
        return next(
            (path for path in save_files if path.name == selected_name),
            None,
        )

    def _try_apply_loaded_controller(self, selected_path: Path) -> bool:
        try:
            self._apply_loaded_controller(selected_path)
        except (OSError, ValueError, InvalidStateError) as error:
            messagebox.showerror("Load game", str(error))
            return False
        return True

    def _open_load_game_chooser(self, save_files: list[Path]) -> None:
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
            selected_path = self._resolve_selected_save_path(
                save_files,
                selected_var.get(),
            )
            if selected_path is None:
                messagebox.showerror("Load game", "Invalid save selection.")
                return

            if self._try_apply_loaded_controller(selected_path):
                chooser.destroy()

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

    def _load_game_via_dialog(self) -> None:
        save_files = self._list_save_files()

        if not save_files:
            messagebox.showinfo("Load game", "No saved games found.")
            return

        has_override, selected_path = self._resolve_harness_load_selection(save_files)
        if has_override:
            if selected_path is None:
                messagebox.showerror("Load game", "Invalid save selection.")
                return

            self._try_apply_loaded_controller(selected_path)
            return

        self._open_load_game_chooser(save_files)

    def _load_game_from_setup(self) -> None:
        self._load_game_via_dialog()

    def _undo_action(self) -> None:
        if self.controller is None:
            return

        if self.controller.undo():
            self._clear_trick_selection()
            restored_state = self.controller.get_state()
            if restored_state.phase == Phase.SETUP:
                self.status_var.set("Undo successful. Returned to setup.")
                self._show_view("setup")
                return

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
        self._load_game_via_dialog()

    def _start_game(self) -> None:
        try:
            selected_profile_ids = self._collect_selected_player_profile_ids()
            if self.setup_mode_var.get() == "preset":
                self.controller = self.setup_service.create_started_controller_from_preset_profiles(
                    self.preset_var.get(),
                    selected_profile_ids,
                )
            else:
                player_ids, player_profile_ids, player_display_names = (
                    self.setup_service.build_profile_player_slots(
                        selected_profile_ids
                    )
                )
                order_mode = self.order_mode_var.get()
                explicit_player_order = (
                    list(player_ids) if order_mode == "choice" else None
                )
                policies = self.setup_service.build_order_policies(
                    order_mode=order_mode,
                    player_ids=player_ids,
                    player_profile_ids=player_profile_ids,
                    relevance_criterion=self.relevance_criterion_var.get(),
                    explicit_player_order=explicit_player_order,
                )
                self.controller = self.setup_service.create_started_controller_from_custom_setup_profiles(
                    player_profile_ids=[
                        profile_id
                        for profile_id in player_profile_ids
                        if profile_id is not None
                    ],
                    player_display_names=player_display_names,
                    sport=self.sport_var.get(),
                    letters_word=self.custom_word_var.get(),
                    attack_attempts=int(self.custom_attack_attempts_var.get()),
                    defense_attempts=int(self.custom_defense_attempts_var.get()),
                    policies=policies,
                    elimination_enabled=True,
                    uniqueness_enabled=bool(self.custom_uniqueness_var.get()),
                    multiple_attack_enabled=bool(
                        self.custom_multiple_attack_enabled_var.get()
                    ),
                    no_repetition=bool(self.custom_no_repetition_var.get()),
                    switch_mode=self.custom_switch_mode_var.get(),
                    repetition_mode=self.custom_repetition_mode_var.get(),
                    repetition_limit=int(self.custom_repetition_limit_var.get()),
                )
        except ValueError as error:
            messagebox.showerror("Invalid setup", str(error))
            return
        except InvalidActionError as error:
            messagebox.showerror("Cannot start game", str(error))
            return

        self._clear_trick_selection()
        self.status_var.set("Game started.")
        self._show_view("game")
        self._refresh_game_view()

    def _get_official_preset_names(self) -> list[str]:
        return self.setup_service.list_preset_names()

    def _confirm_trick(self) -> None:
        if self.controller is None:
            return

        trick = self._get_selected_trick_completion()
        if trick is None:
            messagebox.showerror("Invalid input", "Select a valid trick suggestion first.")
            return

        try:
            state = self.controller.get_state()
            if state.turn_phase == TurnPhase.ATTACK and state.current_trick is not None:
                self.controller.change_attack_trick(trick)
                self.status_var.set(f"Attack trick changed to '{trick}'.")
            else:
                self.controller.start_turn(trick)
                self.status_var.set(f"Trick '{trick}' confirmed.")
            self._clear_trick_selection()
        except InvalidActionError as error:
            self.status_var.set(f"Invalid action: {error}")

        self._refresh_game_view()

    def _cancel_trick(self) -> None:
        if self.controller is None:
            return

        trick = self._get_selected_trick_completion()
        if trick is None:
            messagebox.showerror("Invalid input", "Select a valid trick suggestion before cancelling it.")
            return

        try:
            self.controller.cancel_turn(trick)
            self._clear_trick_selection()
            self.status_var.set("Turn failed. Next player.")
        except InvalidActionError as error:
            self.status_var.set(f"Invalid action: {error}")

        self._refresh_game_view()

    def _resolve_defense(self, success: bool) -> None:
        if self.controller is None:
            return

        try:
            state_before = self.controller.get_state()
            events_before = len(state_before.history.events)

            if state_before.turn_phase == TurnPhase.ATTACK:
                resolution_status = self.controller.resolve_attack(success)
            else:
                resolution_status = self.controller.resolve_defense(success)

            state_after = self.controller.get_state()
            message = self._format_new_events(state_after, events_before)

            if isinstance(resolution_status, AttackResolutionStatus):
                if resolution_status == AttackResolutionStatus.ATTACK_CONTINUES:
                    self.status_var.set(message or "Attack continues.")
                elif resolution_status == AttackResolutionStatus.DEFENSE_READY:
                    self.status_var.set(message or "Attack succeeded. Defense begins.")
                elif resolution_status == AttackResolutionStatus.TURN_FAILED:
                    self._clear_trick_selection()
                    self.status_var.set(message or "Turn failed.")
            else:
                if resolution_status == DefenseResolutionStatus.DEFENSE_CONTINUES:
                    self.status_var.set(message or "Defense continues.")
                elif resolution_status == DefenseResolutionStatus.TURN_FINISHED:
                    self._clear_trick_selection()
                    self.status_var.set(message or "Turn finished.")
                elif resolution_status == DefenseResolutionStatus.GAME_FINISHED:
                    self._clear_trick_selection()
                    self.status_var.set(message or "Game finished.")
        except InvalidActionError as error:
            self.status_var.set(f"Invalid action: {error}")

        self._refresh_game_view()

        state = self.controller.get_state()
        if state.phase == Phase.END:
            self._show_game_over_message(state)

    def _resolve_verified_switch_attack(self, normal_verified: bool) -> None:
        if self.controller is None:
            return

        try:
            state_before = self.controller.get_state()
            events_before = len(state_before.history.events)
            resolution_status = self.controller.resolve_attack(
                True,
                switch_normal_verified=normal_verified,
            )

            state_after = self.controller.get_state()
            message = self._format_new_events(state_after, events_before)

            if resolution_status == AttackResolutionStatus.ATTACK_CONTINUES:
                self.status_var.set(message or "Attack continues.")
            elif resolution_status == AttackResolutionStatus.DEFENSE_READY:
                self.status_var.set(message or "Attack succeeded. Defense begins.")
            elif resolution_status == AttackResolutionStatus.TURN_FAILED:
                self._clear_trick_selection()
                self.status_var.set(message or "Turn failed.")
        except InvalidActionError as error:
            self.status_var.set(f"Invalid action: {error}")

        self._refresh_game_view()

        state = self.controller.get_state()
        if state.phase == Phase.END:
            self._show_game_over_message(state)

    def _add_player_between_turns(self) -> None:
        if self.controller is None:
            return

        player_name = self._ask_string_dialog("Add player", "Player name:")

        if player_name is None:
            return

        player_name = player_name.strip()
        if not player_name:
            messagebox.showerror("Invalid input", "The player name cannot be empty.")
            return

        try:
            state_before = self.controller.get_state()
            events_before = len(state_before.history.events)
            player_id, player_display_name = self.setup_service.resolve_player_identity_input(
                player_name,
                prefer_profile_identity=bool(
                    self.controller.match_parameters.player_profile_ids
                ),
            )
            known_profile_ids = set(self.setup_service.list_local_profile_ids())
            self.controller.add_player_between_turns(
                player_id,
                player_name=player_display_name,
                player_profile_id=(
                    player_id if player_id in known_profile_ids else None
                ),
            )
            self.status_var.set(
                self._format_new_events(self.controller.get_state(), events_before)
                or f"{player_display_name} joined the game."
            )
        except (InvalidActionError, ValueError) as error:
            self.status_var.set(f"Invalid action: {error}")

        self._refresh_game_view()

    def _remove_player_between_turns(self) -> None:
        if self.controller is None:
            return

        player_name = self._ask_string_dialog("Remove player", "Player name:")

        if player_name is None:
            return

        player_name = player_name.strip()
        if not player_name:
            messagebox.showerror("Invalid input", "The player name cannot be empty.")
            return

        try:
            state_before = self.controller.get_state()
            events_before = len(state_before.history.events)
            resolved_player_id = self._resolve_player_id_from_input(player_name)
            self.controller.remove_player_between_turns(resolved_player_id)
            self.status_var.set(
                self._format_new_events(self.controller.get_state(), events_before)
                or f"{player_name} left the game."
            )
        except InvalidActionError as error:
            self.status_var.set(f"Invalid action: {error}")

        self._refresh_game_view()

    # =========================
    # View refresh
    # =========================

    def _refresh_game_view(self) -> None:
        if self.controller is None:
            return

        state = self.controller.get_state()

        assert self.matchup_label is not None
        assert self.preset_label is not None
        assert self.score_frame is not None
        assert self.phase_title_label is not None
        assert self.trick_label is not None
        assert self.phase_description_label is not None
        assert self.attempts_label is not None

        self.matchup_label.config(text="")
        context = state.history.build_match_context()
        preset_name = context.preset_name if context is not None else None
        self.preset_label.config(
            text=f"Preset: {preset_name}" if preset_name else ""
        )

        self._render_score_text(state)
        self._set_session_controls_for_state(state)

        if state.phase == Phase.END:
            self.phase_title_label.config(text="Game over")
            self.trick_label.config(text="")
            self.phase_description_label.config(
                text="Consultation mode. Use Undo, Save, Load, History, Setup details or New game."
            )
            self.attempts_label.config(text="")
            self._set_trick_controls_enabled(False)
            self._set_defense_controls_enabled(False)
            self._refresh_trick_suggestions()
            self._focus_widget(self.undo_button)
            return

        attacker = state.players[state.attacker_index]

        if state.current_trick is None:
            defenders = self._format_active_defender_names(state)
            self.phase_title_label.config(
                text=f"{attacker.name} sets the next trick"
            )
            self.trick_label.config(text="")
            self.phase_description_label.config(
                text=f"Defenders: {defenders}"
            )
            self.attempts_label.config(text="")
            self._set_trick_controls_enabled(True)
            self._set_defense_controls_enabled(False)
            self._refresh_trick_suggestions()
            self._focus_widget(self.trick_entry)
        elif state.turn_phase == TurnPhase.ATTACK:
            pending_defenders = self._format_active_defender_names(state)
            can_change_attack_trick = self._can_change_attack_trick()
            requires_change = (
                self.controller.current_attack_trick_requires_change()
                if self.controller is not None
                else False
            )
            requires_switch_normal_verification = (
                self._current_attack_requires_switch_normal_verification()
            )
            self.phase_title_label.config(text=f"{attacker.name} attacks")
            self.trick_label.config(text=f"Trick: {state.current_trick}")
            if requires_change:
                phase_description = (
                    f"Pending defenders: {pending_defenders} | Choose a new trick to continue."
                )
            elif requires_switch_normal_verification:
                phase_description = (
                    f"Pending defenders: {pending_defenders} | Confirm whether the normal version was verified."
                )
            elif can_change_attack_trick:
                phase_description = (
                    f"Pending defenders: {pending_defenders} | You may keep this trick or change it."
                )
            else:
                phase_description = f"Pending defenders: {pending_defenders}"
            self.phase_description_label.config(text=phase_description)
            self.attempts_label.config(
                text=f"{attacker.name} has {state.attack_attempts_left} attack attempt(s) left"
            )
            self._set_trick_controls_enabled(can_change_attack_trick)
            self._set_defense_controls_enabled(
                not requires_change,
                verified_switch_required=(
                    not requires_change and requires_switch_normal_verification
                ),
            )
            self._refresh_trick_suggestions()
            if can_change_attack_trick:
                self._focus_widget(self.trick_entry)
            elif requires_switch_normal_verification:
                self._focus_widget(self.switch_normal_verified_button)
            else:
                self._focus_widget(self.success_button)
        else:
            defender = self._get_current_defender(state)
            defender_name = defender.name if defender is not None else "-"
            remaining = self._get_remaining_defender_names(state)

            self.phase_title_label.config(
                text=f"{attacker.name} attacks"
            )
            self.trick_label.config(text=f"Trick: {state.current_trick}")
            self.phase_description_label.config(
                text=f"Current defender: {defender_name} | Remaining: {remaining}"
            )
            self.attempts_label.config(
                text=f"{defender_name} has {state.defense_attempts_left} defense attempt(s) left"
            )
            self._set_trick_controls_enabled(False)
            self._set_defense_controls_enabled(True)
            self._refresh_trick_suggestions()
            self._focus_widget(self.success_button)

    def _render_score_text(self, state: GameState) -> None:
        assert self.score_frame is not None

        for child in self.score_frame.winfo_children():
            child.destroy()

        word = self._get_letters_word()
        players = state.players
        active_attacker_index = (
            state.attacker_index if state.phase == Phase.TURN else None
        )

        total_columns = max(1, len(players) * 2 - 1)
        for column_index in range(total_columns):
            if column_index % 2 == 0:
                self.score_frame.columnconfigure(column_index, weight=1, uniform="score")
            else:
                self.score_frame.columnconfigure(column_index, weight=0)

        for player_index, player in enumerate(players):
            column_index = player_index * 2

            marker_text = "━━━━" if player_index == active_attacker_index else ""
            marker = ttk.Label(
                self.score_frame,
                text=marker_text,
                font=self.score_table_marker_font,
                anchor="center",
            )
            marker.grid(row=0, column=column_index, padx=10, pady=(0, 2), sticky="ew")

            name_label = ttk.Label(
                self.score_frame,
                text=player.name.upper(),
                font=self.score_table_name_font,
                anchor="center",
                justify="center",
            )
            name_label.grid(row=1, column=column_index, padx=10, pady=(0, 4), sticky="ew")

            score_label = ttk.Label(
                self.score_frame,
                text=self._format_score_progress(word, player.score),
                font=self.score_table_word_font,
                anchor="center",
                justify="center",
            )
            score_label.grid(row=2, column=column_index, padx=10, sticky="ew")

            if player_index < len(players) - 1:
                name_separator = ttk.Label(
                    self.score_frame,
                    text="-",
                    font=self.score_table_name_font,
                    anchor="center",
                )
                name_separator.grid(row=1, column=column_index + 1, padx=2)

                separator = ttk.Label(
                    self.score_frame,
                    text="-",
                    font=self.score_table_word_font,
                    anchor="center",
                )
                separator.grid(row=2, column=column_index + 1, padx=2)

    def _format_score_progress(self, word: str, score: int) -> str:
        if score <= 0:
            return "-"
        return word[: min(score, len(word))]

    def _set_trick_controls_enabled(self, enabled: bool) -> None:
        assert self.trick_entry is not None
        assert self.trick_suggestions_listbox is not None
        assert self.confirm_trick_button is not None
        assert self.cancel_trick_button is not None

        button_text = "Change trick" if self._can_change_attack_trick() else "Set trick"
        self.confirm_trick_button.config(text=button_text)

        state = "normal" if enabled else "disabled"
        self.trick_entry.config(state=state)
        self.trick_suggestions_listbox.config(state=state)

        button_state = (
            state
            if enabled and self._selected_trick_completion is not None
            else "disabled"
        )
        self.confirm_trick_button.config(state=button_state)
        current_state = self.controller.get_state() if self.controller is not None else None
        cancel_enabled = (
            enabled
            and current_state is not None
            and current_state.turn_phase == TurnPhase.TURN_OPEN
            and self._selected_trick_completion is not None
        )
        self.cancel_trick_button.config(state="normal" if cancel_enabled else "disabled")

    def _set_trick_dropdown_visible(self, visible: bool) -> None:
        if self.trick_dropdown_frame is None:
            return

        if visible:
            self.trick_dropdown_frame.grid()
        else:
            self.trick_dropdown_frame.grid_remove()

    def _can_change_attack_trick(self) -> bool:
        if self.controller is None:
            return False
        return self.controller.can_change_attack_trick()

    def _current_attack_requires_switch_normal_verification(self) -> bool:
        if self.controller is None:
            return False
        return self.controller.current_attack_requires_switch_normal_verification()

    def _bind_button_keyboard_activation(self, button: ttk.Button | None) -> None:
        if button is None:
            return

        button.bind("<Return>", lambda _event, target=button: target.invoke())

    def _focus_widget(self, widget) -> None:
        if widget is None:
            return
        try:
            widget.focus_set()
        except tk.TclError:
            return

    def _focus_first_trick_suggestion(self, _event=None):
        if self.trick_suggestions_listbox is None:
            return "break"
        if not self._current_trick_suggestions:
            return "break"

        self.trick_suggestions_listbox.focus_set()
        self.trick_suggestions_listbox.selection_clear(0, tk.END)
        self.trick_suggestions_listbox.selection_set(0)
        self.trick_suggestions_listbox.activate(0)
        self.trick_suggestions_listbox.see(0)
        return "break"

    def _handle_trick_entry_submit(self, _event=None):
        if (
            self.confirm_trick_button is not None
            and str(self.confirm_trick_button.cget("state")) == "normal"
            and self._selected_trick_completion is not None
        ):
            self._confirm_trick()
            return "break"

        return self._focus_first_trick_suggestion()

    def _handle_trick_suggestion_activate(self, _event=None):
        self._handle_trick_suggestion_selection()
        return "break"

    def _set_defense_controls_enabled(
        self,
        enabled: bool,
        *,
        verified_switch_required: bool = False,
    ) -> None:
        assert self.success_button is not None
        assert self.failure_button is not None
        assert self.switch_normal_verified_button is not None
        assert self.switch_normal_not_verified_button is not None

        state = "normal" if enabled else "disabled"
        self.failure_button.config(state=state)
        if enabled and verified_switch_required:
            self.success_button.config(state="disabled")
            self.switch_normal_verified_button.config(state="normal")
            self.switch_normal_not_verified_button.config(state="normal")
        else:
            self.success_button.config(state=state)
            self.switch_normal_verified_button.config(state="disabled")
            self.switch_normal_not_verified_button.config(state="disabled")

    def _set_session_controls_for_state(self, state: GameState) -> None:
        assert self.undo_button is not None
        assert self.save_button is not None
        assert self.load_button is not None
        assert self.history_button is not None
        assert self.setup_details_button is not None
        assert self.add_player_button is not None
        assert self.remove_player_button is not None
        assert self.new_game_button is not None

        persistent_buttons = (
            self.undo_button,
            self.save_button,
            self.load_button,
            self.history_button,
            self.setup_details_button,
            self.new_game_button,
        )
        for button in persistent_buttons:
            button.config(state="normal")

        roster_state = (
            "normal"
            if state.phase == Phase.TURN and state.current_trick is None
            else "disabled"
        )
        self.add_player_button.config(state=roster_state)
        self.remove_player_button.config(state=roster_state)

    def _show_history_view(self) -> None:
        if self.controller is None:
            return

        self._refresh_history_view()
        self._show_view("history")

    def _show_setup_details_view(self) -> None:
        if self.controller is None:
            return

        self._refresh_setup_details_view()
        self._show_view("setup_details")

    def _show_game_view(self) -> None:
        if self.controller is None:
            self._show_view("setup")
            return
        self._refresh_game_view()
        self._show_view("game")

    def _return_to_setup(self) -> None:
        self.controller = None
        self._clear_trick_selection()
        self.status_var.set("Configure the game to begin.")
        self._show_view("setup")

    def _refresh_history_view(self) -> None:
        if self.controller is None or self.history_tree is None:
            return

        state = self.controller.get_state()
        turns: list[HistoryTurn] = state.history.build_turns()

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for turn in turns:
            trick_validated = turn.attack_trace or (
                "V" if turn.trick_status == "validated" else "X"
            )

            if not turn.defenses:
                self.history_tree.insert(
                    "",
                    "end",
                    values=(
                        turn.turn_number,
                        turn.attacker_name,
                        turn.trick_name,
                        trick_validated,
                        "-",
                        "-",
                        "-",
                    ),
                )
                continue

            for index, defense in enumerate(turn.defenses):
                letters = self._format_letters(defense.letters, self._get_letters_word())
                turn_value = turn.turn_number if index == 0 else ""
                attacker_value = turn.attacker_name if index == 0 else ""
                trick_value = turn.trick_name if index == 0 else ""
                valid_value = trick_validated if index == 0 else ""

                self.history_tree.insert(
                    "",
                    "end",
                    values=(
                        turn_value,
                        attacker_value,
                        trick_value,
                        valid_value,
                        defense.defender_name,
                        defense.attempts_trace or "-",
                        letters,
                    ),
                )

    def _refresh_setup_details_view(self) -> None:
        if self.controller is None or self.setup_details_body_label is None:
            return

        match_parameters = self.controller.match_parameters
        fine_rules = match_parameters.fine_rules
        rule_set = match_parameters.rule_set
        policies = match_parameters.policies
        dictionary_definition = self.controller.dictionary_definition

        preset_label = match_parameters.preset_name or "custom"
        players_label = ", ".join(match_parameters.player_display_names)
        profiles_label = ", ".join(
            profile_id
            for profile_id in match_parameters.player_profile_ids
            if profile_id is not None
        )
        order_label = self.setup_service.describe_order_mode_from_policies(policies)
        if policies.initial_turn_order == InitialTurnOrderPolicy.RELEVANCE:
            criterion = (
                policies.relevance_criterion.value
                if policies.relevance_criterion is not None
                else RelevanceCriterion.ALPHABETICAL.value
            )
            order_label = f"relevance ({criterion})"
        if policies.explicit_player_order:
            base_order_label = ", ".join(
                self.setup_service.preview_order(
                    order_mode="choice",
                    player_ids=match_parameters.player_ids,
                    player_profile_ids=match_parameters.player_profile_ids,
                    player_display_names=match_parameters.player_display_names,
                    explicit_player_order=list(policies.explicit_player_order),
                )
            )
        else:
            base_order_label = ", ".join(match_parameters.player_display_names)
        uniqueness_label = "enabled" if fine_rules.uniqueness_enabled else "disabled"
        repetition_label = self.setup_service.format_repetition_label(
            fine_rules.repetition_mode,
            fine_rules.repetition_limit,
        )
        multiple_attack_label = self.setup_service.format_multiple_attack_label(
            multiple_attack_enabled=fine_rules.multiple_attack_enabled,
            no_repetition=fine_rules.no_repetition,
            attack_attempts=rule_set.attack_attempts,
        )
        switch_label = fine_rules.switch_mode

        body = "\n".join(
            [
                f"Preset: {preset_label}",
                f"Structure: {match_parameters.structure_name}",
                f"Sport: {match_parameters.sport}",
                f"Players: {players_label}",
                f"Profiles: {profiles_label or 'none'}",
                f"Order: {order_label}",
                f"Base order: {base_order_label}",
                f"Word: {rule_set.letters_word}",
                f"Attack attempts: {rule_set.attack_attempts}",
                f"Defense attempts: {rule_set.defense_attempts}",
                f"Uniqueness: {uniqueness_label}",
                f"Multiple Attack: {multiple_attack_label}",
                f"Switch: {switch_label}",
                f"Repetition: {repetition_label}",
                f"Dictionary sport: {dictionary_definition.sport.value}",
                f"Dictionary profile: {dictionary_definition.profile}",
                f"Dictionary max segments: {dictionary_definition.max_segments}",
            ]
        )
        self.setup_details_body_label.config(text=body)

    def _get_letters_word(self) -> str:
        if self.controller is None:
            return "SKATE"
        return self.controller.match_config.letters_word

    # =========================
    # Helpers
    # =========================

    def _get_current_defender(self, state: GameState):
        if state.current_defender_position >= len(state.defender_indices):
            return None

        defender_index = state.defender_indices[state.current_defender_position]
        return state.players[defender_index]

    def _format_letters(self, letters: str, word: str) -> str:
        if not letters:
            return "-"
        if len(letters) >= len(word):
            return f"[{letters}]"
        return letters

    def _format_defender_names(
        self, state: GameState, defender_indices: list[int]
    ) -> str:
        if not defender_indices:
            return "-"
        return ", ".join(state.players[index].name for index in defender_indices)

    def _format_active_defender_names(self, state: GameState) -> str:
        defender_indices = [
            index
            for index, player in enumerate(state.players)
            if index != state.attacker_index and player.is_active
        ]
        return self._format_defender_names(state, defender_indices)

    def _get_remaining_defender_names(self, state: GameState) -> str:
        remaining_indices = state.defender_indices[state.current_defender_position + 1 :]
        return self._format_defender_names(state, remaining_indices)

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

    def _resolve_player_id_from_input(self, value: str) -> str:
        assert self.controller is not None
        normalized = value.strip().casefold()
        for player in self.controller.get_state().players:
            if player.id.casefold() == normalized or player.name.casefold() == normalized:
                return player.id
        return value

    def _format_event(self, state: GameState, event: Event) -> str:
        name = event.name
        payload = event.payload
        trick_label = payload.get("trick_label", payload.get("trick"))

        if name == EventName.DEFENSE_SUCCEEDED:
            player_name = self._get_player_name(state, payload["player_id"])
            return f"{player_name} landed '{trick_label}'."

        if name == EventName.ATTACK_FAILED_ATTEMPT:
            attacker_name = self._get_player_name(state, payload["attacker_id"])
            if payload.get("switch_normal_verification") == "failed":
                return (
                    f"{attacker_name} landed '{trick_label}' but failed the normal "
                    f"verification ({payload['attempts_left']} attack attempt(s) left)."
                )
            return (
                f"{attacker_name} missed '{trick_label}' "
                f"({payload['attempts_left']} attack attempt(s) left)."
            )

        if name == EventName.ATTACK_SUCCEEDED:
            attacker_name = self._get_player_name(state, payload["attacker_id"])
            if payload.get("switch_normal_verification") == "verified":
                return (
                    f"{attacker_name} landed '{trick_label}' and verified the normal version "
                    "to set the trick."
                )
            return f"{attacker_name} landed '{trick_label}' to set the trick."

        if name == EventName.DEFENSE_FAILED_ATTEMPT:
            player_name = self._get_player_name(state, payload["player_id"])
            return (
                f"{player_name} missed '{trick_label}' "
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

        if name == EventName.TURN_FAILED:
            next_attacker_name = self._get_player_name(state, payload["next_attacker_id"])
            return f"Turn failed. Next attacker: {next_attacker_name}"

        if name == EventName.GAME_FINISHED:
            winner_id = payload["winner_id"]
            if winner_id is None:
                return "Game finished."
            winner_name = self._get_player_name(state, winner_id)
            return f"Game finished. Winner: {winner_name}"

        if name == EventName.PLAYER_JOINED:
            player_name = payload.get(
                "player_name",
                self._get_player_name(state, payload["player_id"]),
            )
            return self._format_transition_event(
                base_message=f"{player_name} joined the game.",
                payload=payload,
            )

        if name == EventName.PLAYER_REMOVED:
            player_name = payload.get(
                "player_name",
                payload["player_id"],
            )
            return self._format_transition_event(
                base_message=f"{player_name} left the game.",
                payload=payload,
            )

        return ""

    def _format_transition_event(
        self, base_message: str, payload: dict[str, object]
    ) -> str:
        message = base_message

        if payload.get("structure_changed"):
            previous_structure = payload.get("previous_structure_name")
            next_structure = payload.get("structure_name")
            if previous_structure and next_structure:
                message = (
                    f"{base_message} Structure changed: "
                    f"{previous_structure} -> {next_structure}."
                )

        if payload.get("preset_invalidated") or (
            payload.get("previous_preset_name") is not None
            and payload.get("preset_name") is None
        ):
            return f"{message} Preset cleared."

        return message

    def _refresh_trick_suggestions(self) -> None:
        if self._suppress_trick_updates:
            return

        if self.trick_suggestions_listbox is None:
            return

        self.trick_suggestions_listbox.delete(0, tk.END)
        self._set_trick_dropdown_visible(False)
        self._current_trick_suggestions = []

        if self.controller is None:
            self._selected_trick_completion = None
            self._set_trick_controls_enabled(False)
            return

        state = self.controller.get_state()
        can_change_attack_trick = self._can_change_attack_trick()
        if state.phase != Phase.TURN or (
            state.current_trick is not None and not can_change_attack_trick
        ):
            self._selected_trick_completion = None
            self._set_trick_controls_enabled(False)
            return

        raw_value = self.trick_var.get().strip()
        if not raw_value:
            self._selected_trick_completion = None
            self._set_trick_controls_enabled(
                state.current_trick is None or can_change_attack_trick
            )
            if can_change_attack_trick and self.controller.current_attack_trick_requires_change():
                self.status_var.set(
                    "Current trick reached the repetition limit. Choose a new trick."
                )
            return

        suggestions = self.controller.suggest_tricks(raw_value)
        self._current_trick_suggestions = suggestions
        self._selected_trick_completion = None

        for suggestion in suggestions:
            marker = "" if suggestion.is_terminal else " ->"
            self.trick_suggestions_listbox.insert(tk.END, f"{suggestion.label}{marker}")

        if suggestions:
            self.trick_suggestions_listbox.config(height=min(len(suggestions), 6))
            self._set_trick_dropdown_visible(True)
            self.status_var.set("Select a valid suggestion to confirm the trick.")
        else:
            self.status_var.set("Invalid trick input. No suggestion matches.")

        self._set_trick_controls_enabled(True)

    def _handle_trick_suggestion_selection(self) -> None:
        if self.trick_suggestions_listbox is None:
            return

        selection = self.trick_suggestions_listbox.curselection()
        if not selection:
            self._selected_trick_completion = None
            self._set_trick_controls_enabled(True)
            return

        suggestion = self._current_trick_suggestions[selection[0]]
        self._selected_trick_completion = (
            suggestion.completion if suggestion.is_terminal else None
        )

        self._suppress_trick_updates = True
        self.trick_var.set(suggestion.completion or suggestion.label)
        self._suppress_trick_updates = False

        if suggestion.is_terminal:
            self.status_var.set("Valid trick selected.")
            self._set_trick_controls_enabled(True)
            self._focus_widget(self.confirm_trick_button)
            return

        self.status_var.set("Continuation selected. Refine or pick a full trick.")
        self._refresh_trick_suggestions()
        if self.trick_entry is not None:
            self.trick_entry.icursor(tk.END)
        self._focus_widget(self.trick_entry)

    def _get_selected_trick_completion(self) -> str | None:
        return self._selected_trick_completion

    def _clear_trick_selection(self) -> None:
        self._suppress_trick_updates = True
        self.trick_var.set("")
        self._suppress_trick_updates = False
        self._selected_trick_completion = None
        self._current_trick_suggestions = []
        if self.trick_suggestions_listbox is not None:
            self.trick_suggestions_listbox.delete(0, tk.END)
        self._set_trick_dropdown_visible(False)

    def _show_game_over_message(self, state: GameState) -> None:
        active_players = [player for player in state.players if player.is_active]

        if len(active_players) == 1:
            messagebox.showinfo("Game Over", f"Winner: {active_players[0].name}")
        else:
            messagebox.showinfo("Game Over", "No winner determined.")

if __name__ == "__main__":
    GUIApp().run()
