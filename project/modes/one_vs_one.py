from core.state import GameState
from core.exceptions import InvalidStateError

from modes.base_mode import BaseMode

class OneVsOneMode(BaseMode):
    def validate(self, state: GameState) -> None:
        if len(state.players) != 2:
            raise InvalidStateError("One vs one mode requires exactly two players.")