from config.match_parameters import MatchParameters
from core.types import DefenseResolutionStatus
from engine.game_engine import GameEngine


class GameController:
    def __init__(self, match_parameters: MatchParameters) -> None:
        self.engine = GameEngine(match_parameters)

    def start_game(self) -> None:
        self.engine.start_game()

    def start_turn(self, trick: str) -> None:
        self.engine.start_turn(trick)

    def resolve_defense(self, success: bool) -> DefenseResolutionStatus:
        return self.engine.resolve_defense(success)

    def get_state(self):
        return self.engine.get_state()
    
    def cancel_turn(self) -> None:
        self.engine.cancel_turn()