from dataclasses import dataclass

from config.match_parameters import MatchParameters
from core.state import GameState


@dataclass
class GameSave:
    match_parameters: MatchParameters
    game_state: GameState
