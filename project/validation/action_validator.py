from core.exceptions import InvalidActionError
from core.state import GameState
from core.types import Phase
from rules.rules_registry import RulesRegistry


class ActionValidator:
    def __init__(self, rules_registry: RulesRegistry) -> None:
        self.rules_registry = rules_registry

    def validate_start_turn(self, state: GameState, trick: str) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError("Cannot start a turn outside TURN phase.")

        if not trick:
            raise InvalidActionError("A trick is required to start a turn.")

        if state.current_trick is not None:
            raise InvalidActionError("Cannot start a new turn while another trick is engaged.")

        if not state.players[state.attacker_index].is_active:
            raise InvalidActionError("Current attacker is not active.")

        if self.rules_registry.special.is_trick_already_validated(state, trick):
            raise InvalidActionError("This trick has already been validated in this game.")

    def validate_resolve_defense(self, state: GameState) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError("Cannot resolve defense outside TURN phase.")

        if state.current_trick is None:
            raise InvalidActionError("No current trick to defend.")

        if state.current_defender_position >= len(state.defender_indices):
            raise InvalidActionError("No current defender to resolve.")
        
    def validate_cancel_turn(self, state: GameState, trick: str) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError("Cannot cancel turn outside TURN phase.")

        if not trick:
            raise InvalidActionError("A trick is required to cancel a turn.")

        if state.current_trick is not None:
            raise InvalidActionError("Cannot cancel turn after a trick has been engaged.")

    def validate_add_player_between_turns(self, state: GameState, player_id: str) -> None:
        if state.phase != Phase.TURN:
            raise InvalidActionError(
                "Cannot add a player outside TURN phase."
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

        if not player_id:
            raise InvalidActionError("A player identifier is required.")

        if state.current_trick is not None:
            raise InvalidActionError(
                "Cannot remove a player while a trick is engaged."
            )
