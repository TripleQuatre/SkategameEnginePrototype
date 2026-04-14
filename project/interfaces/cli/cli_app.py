from datetime import datetime
from pathlib import Path

from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.events import Event
from core.exceptions import InvalidActionError, InvalidStateError
from core.history import HistoryTurn
from core.state import GameState
from core.types import DefenseResolutionStatus, EventName, Phase


class CLIApp:
    SAVES_DIR = Path(__file__).resolve().parents[2] / "saves"
    def run(self) -> None:
        print("=== SkateGame Engine Prototype CLI ===")

        controller = self._setup_or_load_game()

        print()

        while True:
            state = controller.get_state()

            if state.phase == Phase.END:
                controller = self._run_end_of_game_loop(controller)
                print()
                continue

            self._display_state(state)

            if state.current_trick is None:
                trick = self._ask_validated_trick_input(controller)

                if trick is None:
                    continue

                try:
                    controller.start_turn(trick)
                except InvalidActionError as error:
                    print(f"\nAction invalide: {error}\n")
                    continue

            while True:
                state = controller.get_state()

                if state.phase == Phase.END:
                    break

                if state.current_trick is None:
                    break

                if state.current_defender_position >= len(state.defender_indices):
                    break


                defender_index = state.defender_indices[state.current_defender_position]
                defender = state.players[defender_index]

                print(
                    f"{defender.name} tries '{state.current_trick}' "
                    f"({state.defense_attempts_left} attempt(s) left)"
                )

                success = self._ask_defense_action(controller, defender.name)

                if success is None:
                    print()
                    break

                events_before = len(state.history.events)
                resolution_status = controller.resolve_defense(success)
                self._display_new_events(controller, events_before)

                if resolution_status == DefenseResolutionStatus.DEFENSE_CONTINUES:
                    continue

                if resolution_status == DefenseResolutionStatus.TURN_FINISHED:
                    print()
                    break

                if resolution_status == DefenseResolutionStatus.GAME_FINISHED:
                    print()
                    break

    def _setup_or_load_game(self) -> GameController:
        while True:
            print("1. Start new game")
            print("2. Load saved game")

            choice = input("Choose an option (1/2): ").strip()

            if choice == "1":
                controller = self._create_new_game_controller()
                print()
                return controller

            if choice == "2":
                controller = self._load_saved_game_controller()
                if controller is not None:
                    return controller
                continue

            print("Invalid choice.\n")

    def _create_new_game_controller(self) -> GameController:
        player_count = self._ask_player_count()
        player_ids = [
            self._ask_non_empty_input(f"Player {index} name: ")
            for index in range(1, player_count + 1)
        ]
        letters_word = self._ask_letters_word()
        defense_attempts = self._ask_defense_attempts()

        rule_set = RuleSetConfig(
            letters_word=letters_word,
            defense_attempts=defense_attempts,
        )

        mode_name = "one_vs_one" if player_count == 2 else "battle"

        match_parameters = MatchParameters(
            player_ids=player_ids,
            mode_name=mode_name,
            rule_set=rule_set,
        )

        controller = GameController(match_parameters)
        controller.start_game()
        return controller

    def _load_saved_game_controller(self) -> GameController | None:
        filepath = self._choose_save_file()
        if filepath is None:
            return None

        placeholder_match_parameters = MatchParameters(
            player_ids=["Player 1", "Player 2"],
            mode_name="one_vs_one",
            rule_set=RuleSetConfig(),
        )

        controller = GameController(placeholder_match_parameters)

        try:
            controller.load_game(str(filepath))
        except (OSError, ValueError, InvalidStateError) as error:
            print(f"Load failed: {error}\n")
            return None

        loaded_state = controller.get_state()
        if loaded_state.phase == Phase.END:
            print(f"Finished game loaded from {filepath.name}. Consultation mode.\n")
        else:
            print(f"Game loaded from {filepath.name}.\n")
        return controller

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

    def _choose_save_file(self) -> Path | None:
        save_files = self._list_save_files()

        if not save_files:
            print("No saved games found.\n")
            return None

        print("\nSaved games:")
        for index, path in enumerate(save_files, start=1):
            print(f"{index}. {path.name}")

        while True:
            value = input("Choose a save number (or press Enter to cancel): ").strip()

            if not value:
                print()
                return None

            if value.isdigit():
                selected_index = int(value)
                if 1 <= selected_index <= len(save_files):
                    print()
                    return save_files[selected_index - 1]

            print("Invalid choice.")

    def _display_help(self) -> None:
        print("\nAvailable commands:")
        print("/help    Show available commands")
        print("/undo    Undo the previous action")
        print("/save    Save the current game")
        print("/load    Load a saved game")
        print("/history Show match history")
        print("/quit    Quit the CLI")
        print()

    def _handle_global_command(
        self, controller: GameController, raw_value: str
    ) -> bool | None:
        command = raw_value.strip().lower()

        if command == "/help":
            self._display_help()
            return None

        if command == "/undo":
            if controller.undo():
                print("Undo successful.\n")
            else:
                print("Nothing to undo.\n")
            return None

        if command == "/save":
            filepath = self._build_save_path()
            try:
                controller.save_game(str(filepath))
                print(f"Game saved to {filepath.name}.\n")
            except OSError as error:
                print(f"Save failed: {error}\n")
            return None

        if command == "/load":
            filepath = self._choose_save_file()
            if filepath is None:
                return None

            try:
                controller.load_game(str(filepath))
                print(f"Game loaded from {filepath.name}.\n")
            except (
                OSError,
                ValueError,
                InvalidActionError,
                InvalidStateError,
            ) as error:
                print(f"Load failed: {error}\n")
            return None

        if command == "/history":
            self._display_history(controller.get_state())
            print()
            return None

        if command == "/quit":
            raise SystemExit(0)

        return True

    def _read_input_with_commands(
        self, controller: GameController, prompt: str
    ) -> str | None:
        while True:
            value = input(prompt).strip()

            if not value:
                print("Invalid input.")
                continue

            command_result = self._handle_global_command(controller, value)
            if command_result is None:
                return None

            return value

    def _display_state(self, state: GameState) -> None:
        print("Score:")
        for player in state.players:
            penalty = self._format_penalty_slots(state.rule_set.letters_word, player.score)
            status = "" if player.is_active else " (OUT)"
            print(f"{player.name:<10} {penalty}{status}")

        attacker = state.players[state.attacker_index]

        if state.current_trick is None:
            defenders = self._format_active_defenders_for_attacker(state)
            print(f"\n{attacker.name} sets the next trick")
            print(f"Defenders: {defenders}")
            return

        if state.current_defender_position < len(state.defender_indices):
            defender_index = state.defender_indices[state.current_defender_position]
            defender = state.players[defender_index]
            remaining = self._format_remaining_defenders(state)
            print(
                f"\n{attacker.name} attacks"
            )
            print(f"Current defender: {defender.name}")
            print(f"Remaining defenders: {remaining}")
            print(
                f"Current trick: {state.current_trick} "
                f"({state.defense_attempts_left} attempt(s) left)"
            )
        else:
            print(f"\n{attacker.name} is resolving the current turn.")

    def _display_new_events(self, controller: GameController, events_before: int) -> None:
        state = controller.get_state()
        new_events = state.history.events[events_before:]

        for event in new_events:
            message = self._format_event(event)
            if message:
                print(message)

    def _format_event(self, event: Event) -> str:
        name = event.name
        payload = event.payload

        if name == EventName.DEFENSE_SUCCEEDED:
            return f"{payload['player_id']} landed '{payload['trick']}'."

        if name == EventName.DEFENSE_FAILED_ATTEMPT:
            return (
                f"{payload['player_id']} missed '{payload['trick']}' "
                f"({payload['attempts_left']} left)."
            )

        if name == EventName.LETTER_RECEIVED:
            return f"{payload['player_id']} gets a letter: {payload['penalty_display']}"

        if name == EventName.PLAYER_ELIMINATED:
            return f"{payload['player_id']} is eliminated."

        if name == EventName.TURN_ENDED:
            return f"Next attacker: {payload['next_attacker_id']}"

        if name == EventName.TURN_FAILED:
            return f"Turn failed. Next attacker: {payload['next_attacker_id']}"

        if name == EventName.GAME_FINISHED:
            winner_id = payload["winner_id"]
            if winner_id is None:
                return "Game finished."
            return f"Game finished. Winner: {winner_id}"

        return ""

    def _display_winner(self, state: GameState) -> None:
        active_players = [player for player in state.players if player.is_active]

        print("Final score:")
        for player in state.players:
            penalty = self._format_penalty_slots(state.rule_set.letters_word, player.score)
            print(f"{player.name:<10} {penalty}")

        print()
        if len(active_players) == 1:
            print(f"Winner: {active_players[0].name}")
        else:
            print("No winner determined.")

    def _run_end_of_game_loop(self, controller: GameController) -> GameController:
        while True:
            state = controller.get_state()

            print()
            self._display_winner(state)
            print("Consultation mode:")
            print("1. Undo")
            print("2. Save")
            print("3. History")
            print("4. Load saved game")
            print("5. New game")
            print("6. Quit")

            choice = input("Choose an option (1-6): ").strip()

            if choice == "1":
                if controller.undo():
                    print("Undo successful.")
                    return controller

                print("Nothing to undo.")
                continue

            if choice == "2":
                filepath = self._build_save_path()
                try:
                    controller.save_game(str(filepath))
                    print(f"Game saved to {filepath.name}.")
                except OSError as error:
                    print(f"Save failed: {error}")
                continue

            if choice == "3":
                self._display_history(state)
                continue

            if choice == "4":
                loaded_controller = self._load_saved_game_controller()
                if loaded_controller is not None:
                    return loaded_controller
                continue

            if choice == "5":
                new_controller = self._create_new_game_controller()
                print()
                return new_controller

            if choice == "6":
                raise SystemExit(0)

            print("Invalid choice.")

    def _ask_validated_trick_input(self, controller: GameController) -> str | None:
        while True:
            trick = self._read_input_with_commands(controller, "")
            if trick is None:
                return None

            state = controller.get_state()
            normalized_trick = trick.lower()

            if normalized_trick in state.validated_tricks:
                print("This trick has already been validated in this game.")
                self._display_state(state)
                continue

            confirm = self._ask_yes_no_with_commands(
                controller,
                f"Confirm trick '{trick}'? (y/n): ",
            )

            if confirm is None:
                return None

            if confirm:
                return trick

            print("Turn failed. Next player.\n")
            try:
                controller.cancel_turn(trick)
            except InvalidActionError as error:
                print(f"Action invalide: {error}\n")
            return None

    def _ask_defense_action(
        self, controller: GameController, defender_name: str
    ) -> bool | None:
        while True:
            value = self._read_input_with_commands(
                controller,
                f"Success for {defender_name}? (y/n): ",
            )

            if value is None:
                return None

            command = value.lower()

            if command in {"y", "yes"}:
                return True

            if command in {"n", "no"}:
                return False

            print("Type y or n.")

    def _ask_yes_no_with_commands(
        self, controller: GameController, prompt: str
    ) -> bool | None:
        while True:
            value = self._read_input_with_commands(controller, prompt)

            if value is None:
                return None

            command = value.lower()

            if command in {"y", "yes"}:
                return True

            if command in {"n", "no"}:
                return False

            print("Type y or n.")

    def _format_penalty_slots(self, word: str, score: int) -> str:
        letters = list(word[:score])
        missing = ["_"] * (len(word) - score)
        return " ".join(letters + missing)

    def _ask_non_empty_input(self, prompt: str) -> str:
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("Invalid input.")

    def _ask_player_count(self) -> int:
        while True:
            value = input("Number of players (2+): ").strip()
            if value.isdigit():
                player_count = int(value)
                if player_count >= 2:
                    return player_count
            print("Player count must be at least 2.")

    def _ask_letters_word(self) -> str:
        while True:
            value = input("Word: ").strip().upper()
            if 1 <= len(value) <= 10:
                return value
            print("Word must contain between 1 and 10 characters.")

    def _ask_defense_attempts(self) -> int:
        while True:
            value = input("Defense attempts (1-3): ").strip()
            if value.isdigit():
                attempts = int(value)
                if 1 <= attempts <= 3:
                    return attempts
            print("Defense attempts must be between 1 and 3.")

    def _ask_yes_no(self, prompt: str) -> bool:
        while True:
            value = input(prompt).strip().lower()
            if value in {"y", "yes"}:
                return True
            if value in {"n", "no"}:
                return False
            print("Type y or n.")

    def _display_history(self, state: GameState) -> None:
            turns: list[HistoryTurn] = state.history.build_turns()

            if not turns:
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

            for turn in turns:
                trick_validated = "V" if turn.trick_status == "validated" else "X"

                if not turn.defenses:
                    print(
                        f"{turn.turn_number:<6}"
                        f"{turn.attacker_name:<12}"
                        f"{turn.trick_name:<16}"
                        f"{trick_validated:<8}"
                        f"{'-':<12}"
                        f"{'-':<10}"
                        f"{'-':<10}"
                    )
                    continue

                for index, defense in enumerate(turn.defenses):
                    letters = self._format_letters(
                        defense.letters, state.rule_set.letters_word
                    )
                    turn_value = str(turn.turn_number) if index == 0 else ""
                    attacker_value = turn.attacker_name if index == 0 else ""
                    trick_value = turn.trick_name if index == 0 else ""
                    valid_value = trick_validated if index == 0 else ""

                    print(
                        f"{turn_value:<6}"
                        f"{attacker_value:<12}"
                        f"{trick_value:<16}"
                        f"{valid_value:<8}"
                        f"{defense.defender_name:<12}"
                        f"{(defense.attempts_trace or '-'): <10}"
                        f"{letters:<10}"
                    )

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

    def _format_active_defenders_for_attacker(self, state: GameState) -> str:
        defender_indices = [
            index
            for index, player in enumerate(state.players)
            if index != state.attacker_index and player.is_active
        ]
        return self._format_defender_names(state, defender_indices)

    def _format_remaining_defenders(self, state: GameState) -> str:
        remaining_indices = state.defender_indices[state.current_defender_position + 1 :]
        return self._format_defender_names(state, remaining_indices)

if __name__ == "__main__":
    CLIApp().run()
