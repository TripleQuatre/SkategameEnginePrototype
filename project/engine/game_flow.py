from core.events import Event
from core.state import GameState
from core.types import DefenseResolutionStatus, EventName, Phase
from engine.end_conditions import EndConditions
from engine.turn_resolver import TurnResolver
from rules.rules_registry import RulesRegistry
from validation.action_validator import ActionValidator


class GameFlow:
    def __init__(self) -> None:
        self.rules_registry = RulesRegistry()
        self.turn_resolver = TurnResolver(self.rules_registry)
        self.end_conditions = EndConditions()
        self.action_validator = ActionValidator(self.rules_registry)

    def start_game(self, state: GameState) -> None:
        state.phase = Phase.TURN
        state.attacker_index = 0
        state.current_trick = None
        state.defender_indices = []
        state.current_defender_position = 0
        state.defense_attempts_left = 0
        state.validated_tricks = []

        state.history.add_event(
            Event(
                name=EventName.GAME_STARTED,
                payload={
                    "player_ids": [player.id for player in state.players],
                },
            )
        )

    def start_turn(self, state: GameState, trick: str) -> None:
        self.action_validator.validate_start_turn(state, trick)

        attacker = state.players[state.attacker_index]

        state.current_trick = trick
        state.defender_indices = [
            index
            for index, player in enumerate(state.players)
            if index != state.attacker_index and player.is_active
        ]
        state.current_defender_position = 0
        state.defense_attempts_left = state.rule_set.defense_attempts

        state.history.add_event(
            Event(
                name=EventName.TURN_STARTED,
                payload={
                    "attacker_id": attacker.id,
                    "trick": trick,
                    "defender_ids": [
                        state.players[index].id for index in state.defender_indices
                    ],
                },
            )
        )

    def resolve_defense(
        self, state: GameState, success: bool
    ) -> DefenseResolutionStatus:
        self.action_validator.validate_resolve_defense(state)

        turn_finished = self.turn_resolver.resolve_defense_attempt(state, success)

        eliminated_players = self.end_conditions.apply_eliminations(state)
        for player in eliminated_players:
            state.history.add_event(
                Event(
                    name=EventName.PLAYER_ELIMINATED,
                    payload={
                        "player_id": player.id,
                    },
                )
            )

        if self.end_conditions.is_game_finished(state):
            winner = self.end_conditions.get_winner(state)
            state.phase = Phase.END

            state.history.add_event(
                Event(
                    name=EventName.GAME_FINISHED,
                    payload={
                        "winner_id": winner.id if winner else None,
                    },
                )
            )

            self._consume_current_trick(state)
            return DefenseResolutionStatus.GAME_FINISHED

        if turn_finished:
            self._consume_current_trick(state)
            self._advance_to_next_attacker(state, log_turn_end=True)
            return DefenseResolutionStatus.TURN_FINISHED

        return DefenseResolutionStatus.DEFENSE_CONTINUES

    def _consume_current_trick(self, state: GameState) -> None:
        if state.current_trick is None:
            return

        normalized_trick = self.rules_registry.special.normalize_trick(
            state.current_trick
        )

        if normalized_trick not in state.validated_tricks:
            state.validated_tricks.append(normalized_trick)

    def _advance_to_next_attacker(
        self, state: GameState, log_turn_end: bool = True
    ) -> None:
        active_player_indices = [
            index for index, player in enumerate(state.players) if player.is_active
        ]

        if not active_player_indices:
            state.phase = Phase.END
            return

        current_attacker = state.attacker_index

        for index in active_player_indices:
            if index > current_attacker:
                state.attacker_index = index
                break
        else:
            state.attacker_index = active_player_indices[0]

        state.current_trick = None
        state.defender_indices = []
        state.current_defender_position = 0
        state.defense_attempts_left = 0

        if log_turn_end:
            state.history.add_event(
                Event(
                    name=EventName.TURN_ENDED,
                    payload={
                        "next_attacker_id": state.players[state.attacker_index].id,
                    },
                )
            )

    def cancel_turn(self, state: GameState, trick: str) -> None:
        self.action_validator.validate_cancel_turn(state, trick)

        attacker = state.players[state.attacker_index]

        self._advance_to_next_attacker(state, log_turn_end=False)

        state.history.add_event(
            Event(
                name=EventName.TURN_CANCELLED,
                payload={
                    "attacker_id": attacker.id,
                    "trick": trick,
                    "next_attacker_id": state.players[state.attacker_index].id,
                },
            )
        )
