from core.exceptions import InvalidActionError
from core.state import GameState
from core.types import Phase, TurnPhase


class ActionValidator:
    def __init__(self, special_rules) -> None:
        self.special_rules = special_rules

    def validate_start_turn(self, state: GameState, trick: str) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError("Cannot start a turn outside TURN phase.")

        if state.turn_phase != TurnPhase.TURN_OPEN:
            raise InvalidActionError("Cannot start a turn unless the turn is open.")

        if not trick:
            raise InvalidActionError("A trick is required to start a turn.")

        if state.current_trick is not None:
            raise InvalidActionError("Cannot start a new turn while another trick is engaged.")

        if not state.players[state.attacker_index].is_active:
            raise InvalidActionError("Current attacker is not active.")

        if self.special_rules.uniqueness_blocks_trick(state, trick):
            raise InvalidActionError("This trick has already been validated in this game.")

    def validate_resolve_defense(self, state: GameState) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError("Cannot resolve defense outside TURN phase.")

        if state.turn_phase != TurnPhase.DEFENSE:
            raise InvalidActionError("Cannot resolve defense outside DEFENSE phase.")

        if state.current_trick is None:
            raise InvalidActionError("No current trick to defend.")

        if state.current_defender_position >= len(state.defender_indices):
            raise InvalidActionError("No current defender to resolve.")

    def validate_resolve_attack(self, state: GameState) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError("Cannot resolve attack outside TURN phase.")

        if state.turn_phase != TurnPhase.ATTACK:
            raise InvalidActionError("Cannot resolve attack outside ATTACK phase.")

        if state.current_trick is None:
            raise InvalidActionError("No current trick to attack.")
        
    def validate_cancel_turn(self, state: GameState, trick: str) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError("Cannot cancel turn outside TURN phase.")

        if state.turn_phase != TurnPhase.TURN_OPEN:
            raise InvalidActionError("Cannot cancel turn unless the turn is open.")

        if not trick:
            raise InvalidActionError("A trick is required to cancel a turn.")

        if state.current_trick is not None:
            raise InvalidActionError("Cannot cancel turn after a trick has been engaged.")

    def validate_add_player_between_turns(self, state: GameState, player_id: str) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError(
                "Cannot add a player outside TURN phase."
            )

        if state.turn_phase != TurnPhase.TURN_OPEN:
            raise InvalidActionError(
                "Cannot add a player unless the turn is open."
            )

        if not player_id:
            raise InvalidActionError("A player identifier is required.")

        if state.current_trick is not None:
            raise InvalidActionError(
                "Cannot add a player while a trick is engaged."
            )

    def validate_remove_player_between_turns(
        self, state: GameState, player_id: str
    ) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError(
                "Cannot remove a player outside TURN phase."
            )

        if state.turn_phase != TurnPhase.TURN_OPEN:
            raise InvalidActionError(
                "Cannot remove a player unless the turn is open."
            )

        if not player_id:
            raise InvalidActionError("A player identifier is required.")

        if state.current_trick is not None:
            raise InvalidActionError(
                "Cannot remove a player while a trick is engaged."
            )
