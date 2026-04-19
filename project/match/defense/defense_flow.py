from core.events import Event
from core.state import GameState
from core.types import DefenseResolutionStatus, EventName


class DefenseFlow:
    def __init__(self, turn_resolver, victory) -> None:
        self.turn_resolver = turn_resolver
        self.victory = victory

    def resolve_defense(
        self,
        state: GameState,
        success: bool,
        on_mark_game_finished,
        on_mark_turn_finished,
        on_consume_current_trick,
        on_advance_to_next_attacker,
    ) -> DefenseResolutionStatus:
        turn_finished = self.turn_resolver.resolve_defense_attempt(state, success)

        eliminated_players = self.victory.apply_eliminations(state)
        for player in eliminated_players:
            state.history.add_event(
                Event(
                    name=EventName.PLAYER_ELIMINATED,
                    payload={
                        "player_id": player.id,
                        "player_name": player.name,
                    },
                )
            )

        if self.victory.is_game_finished(state):
            winner = self.victory.get_winner(state)
            on_consume_current_trick()
            on_mark_game_finished()

            state.history.add_event(
                Event(
                    name=EventName.GAME_FINISHED,
                    payload={
                        "winner_id": winner.id if winner else None,
                        "winner_name": winner.name if winner else None,
                    },
                )
            )

            return DefenseResolutionStatus.GAME_FINISHED

        if turn_finished:
            on_consume_current_trick()
            on_mark_turn_finished()
            on_advance_to_next_attacker(log_turn_end=True)
            return DefenseResolutionStatus.TURN_FINISHED

        return DefenseResolutionStatus.DEFENSE_CONTINUES
