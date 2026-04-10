from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from controllers.game_controller import GameController
from core.exceptions import InvalidActionError
from core.types import Phase, DefenseResolutionStatus


class CLIApp:
    def run(self) -> None:
        print("=== SkateGame Engine Prototype CLI ===")

        player_1 = self._ask_non_empty_input("Player 1 name: ")
        player_2 = self._ask_non_empty_input("Player 2 name: ")
        letters_word = self._ask_letters_word()
        defense_attempts = self._ask_defense_attempts()

        rule_set = RuleSetConfig(
            letters_word=letters_word,
            defense_attempts=defense_attempts,
        )

        match_parameters = MatchParameters(
            player_ids=[player_1, player_2],
            mode_name="one_vs_one",
            rule_set=rule_set,
        )

        controller = GameController(match_parameters)
        controller.start_game()

        print()

        while True:
            state = controller.get_state()

            if state.phase == Phase.END:
                self._display_winner(state)
                break

            self._display_state(state)

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

                if state.current_defender_position >= len(state.defender_indices):
                    break

                defender_index = state.defender_indices[state.current_defender_position]
                defender = state.players[defender_index]

                print(
                    f"{defender.name} tries '{state.current_trick}' "
                    f"({state.defense_attempts_left} attempt(s) left)"
                )

                success = self._ask_yes_no(f"Success for {defender.name}? (y/n): ")

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

    def _display_state(self, state) -> None:
        print("Score:")
        for player in state.players:
            penalty = self._format_penalty_slots(state.rule_set.letters_word, player.score)
            print(f"{player.name:<10} {penalty}")

        attacker = state.players[state.attacker_index]
        print(f"\n{attacker.name} sets the next trick: ", end="")

    def _display_new_events(self, controller: GameController, events_before: int) -> None:
        state = controller.get_state()
        new_events = state.history.events[events_before:]

        for event in new_events:
            message = self._format_event(event)
            if message:
                print(message)

    def _format_event(self, event) -> str:
        name = event.name
        payload = event.payload

        if name == "defense_succeeded":
            return f"{payload['player_id']} landed '{payload['trick']}'."

        if name == "defense_failed_attempt":
            return (
                f"{payload['player_id']} missed '{payload['trick']}' "
                f"({payload['attempts_left']} left)."
            )

        if name == "letter_received":
            return f"{payload['player_id']} gets a letter: {payload['penalty_display']}"

        if name == "player_eliminated":
            return f"{payload['player_id']} is eliminated."

        if name == "turn_ended":
            return f"Next attacker: {payload['next_attacker_id']}"

        if name == "game_finished":
            winner_id = payload["winner_id"]
            if winner_id is None:
                return "Game finished."
            return f"Game finished. Winner: {winner_id}"

        return ""

    def _display_winner(self, state) -> None:
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

    def _ask_validated_trick_input(self, controller: GameController) -> str:
        while True:
            trick = self._ask_non_empty_input("")
            state = controller.get_state()
            normalized_trick = trick.strip().lower()

            if normalized_trick in state.validated_tricks:
                print("This trick has already been validated in this game.")
                self._display_state(state)
                continue

            confirm = self._ask_yes_no(f"Confirm trick '{trick}'? (y/n): ")
            if confirm:
                return trick

            print("Trick cancelled. Next player.\n")
            controller.cancel_turn(trick)
            return None

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


if __name__ == "__main__":
    CLIApp().run()