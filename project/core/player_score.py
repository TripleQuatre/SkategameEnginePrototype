from dataclasses import dataclass


@dataclass
class PlayerScoreState:
    letters: int = 0
    points: int = 0
