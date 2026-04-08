from core.state import GameState
from core.exceptions import InvalidStateError


class OneVsOneMode:
    def validate(self, state: GameState) -> None:
        if len(state.players) != 2:
            raise InvalidStateError("One vs one mode requires exactly two players.")