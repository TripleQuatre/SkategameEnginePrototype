from config.match_parameters import MatchParameters
from controllers.game_controller import GameController
from core.types import Phase, DefenseResolutionStatus


class CLIApp:
    def run(self) -> None:
        print("=== SkateGame Engine Prototype CLI ===")

        player_1 = input("Nom / ID du joueur 1 : ").strip()
        player_2 = input("Nom / ID du joueur 2 : ").strip()

        match_parameters = MatchParameters(
            player_ids=[player_1, player_2],
            mode_name="one_vs_one",
        )

        controller = GameController(match_parameters)
        controller.start_game()

        print("\nPartie démarrée.\n")

        while True:
            state = controller.get_state()

            if state.phase == Phase.END:
                self._display_winner(state)
                break

            self._display_state(state)

            trick = self._ask_non_empty_input("\nTrick imposé par l'attaquant : ")
            controller.start_turn(trick)

            self._display_turn_start(controller)

            while True:
                state = controller.get_state()

                if state.current_defender_position >= len(state.defender_indices):
                    break

                attacker = state.players[state.attacker_index]
                defender_index = state.defender_indices[state.current_defender_position]
                defender = state.players[defender_index]

                print(
                    f"\nDéfenseur : {defender.name}"
                    f" | Trick à reproduire : {state.current_trick}"
                    f" | Essais restants : {state.defense_attempts_left}"
                )

                success = self._ask_yes_no(
                    f"{defender.name} réussit-il le trick imposé par {attacker.name} ? (y/n) : "
                )

                events_before = len(state.history.events)
                resolution_status = controller.resolve_defense(success)
                self._display_new_events(controller, events_before)

                if resolution_status == DefenseResolutionStatus.DEFENSE_CONTINUES:
                    continue

                if resolution_status == DefenseResolutionStatus.TURN_FINISHED:
                    print("\nTour terminé.\n")
                    break

                if resolution_status == DefenseResolutionStatus.GAME_FINISHED:
                    print("\nPartie terminée.\n")
                    break

    def _display_state(self, state) -> None:
        attacker = state.players[state.attacker_index]

        print("\n--- État de la partie ---")
        print(f"Attaquant : {attacker.name}")
        print("Scores :")

        for player in state.players:
            penalty = state.rule_set.letters_word[:player.score]
            status = "actif" if player.is_active else "éliminé"
            print(f"- {player.name} : {penalty or '-'} ({status})")

    def _display_turn_start(self, controller: GameController) -> None:
        state = controller.get_state()
        attacker = state.players[state.attacker_index]

        defender_names = [
            state.players[index].name for index in state.defender_indices
        ]

        print("\n--- Nouveau tour ---")
        print(f"Attaquant : {attacker.name}")
        print(f"Trick imposé : {state.current_trick}")
        print(f"Défenseurs : {', '.join(defender_names)}")

    def _display_new_events(
        self, controller: GameController, events_before: int
    ) -> None:
        state = controller.get_state()
        new_events = state.history.events[events_before:]

        for event in new_events:
            print(self._format_event(event))

    def _format_event(self, event) -> str:
        name = event.name
        payload = event.payload

        if name == "game_started":
            return "\n[Événement] Partie démarrée."

        if name == "turn_started":
            return (
                f"[Événement] Nouveau tour : trick '{payload['trick']}' "
                f"imposé par {payload['attacker_id']}."
            )

        if name == "defense_succeeded":
            return (
                f"[Événement] Le défenseur {payload['player_id']} a réussi "
                f"le trick '{payload['trick']}'."
            )

        if name == "defense_failed_attempt":
            return (
                f"[Événement] Le défenseur {payload['player_id']} a raté "
                f"le trick '{payload['trick']}'. "
                f"Essais restants : {payload['attempts_left']}."
            )

        if name == "letter_received":
            return (
                f"[Événement] Le joueur {payload['player_id']} reçoit une lettre. "
                f"Score actuel : {payload['penalty_display']}."
            )

        if name == "player_eliminated":
            return f"[Événement] Le joueur {payload['player_id']} est éliminé."

        if name == "turn_ended":
            return (
                f"[Événement] Tour terminé. "
                f"Prochain attaquant : {payload['next_attacker_id']}."
            )

        if name == "game_finished":
            winner_id = payload["winner_id"]
            if winner_id is None:
                return "[Événement] Partie terminée sans gagnant."
            return f"[Événement] Partie terminée. Gagnant : {winner_id}."

        return f"[Événement] {name} | {payload}"

    def _display_winner(self, state) -> None:
        active_players = [player for player in state.players if player.is_active]

        print("\n=== Fin de partie ===")
        if len(active_players) == 1:
            print(f"Gagnant : {active_players[0].name}")
        else:
            print("Aucun gagnant déterminé.")

    def _ask_non_empty_input(self, prompt: str) -> str:
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("Entrée invalide. Merci de saisir une valeur non vide.")

    def _ask_yes_no(self, prompt: str) -> bool:
        while True:
            value = input(prompt).strip().lower()
            if value in {"y", "yes", "o", "oui"}:
                return True
            if value in {"n", "no", "non"}:
                return False
            print("Réponse invalide. Tape y ou n.")


if __name__ == "__main__":
    CLIApp().run()