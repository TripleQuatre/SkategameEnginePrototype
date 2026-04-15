from config.match_parameters import MatchParameters
from core.state import GameState
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

    def get_state(self) -> GameState:
        return self.engine.get_state()

    def cancel_turn(self, trick: str) -> None:
        self.engine.cancel_turn(trick)

    def undo(self) -> bool:
        return self.engine.undo()

    def add_player_between_turns(self, player_id: str) -> None:
        self.engine.add_player_between_turns(player_id)

    def save_game(self, filepath: str) -> None:
        self.engine.save_game(filepath)

    def load_game(self, filepath: str) -> None:
        self.engine.load_game(filepath)
