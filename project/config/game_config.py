from dataclasses import dataclass

@dataclass
class GameConfig:
    letters_word: str = "SKATE"
    min_players: int = 2
    max_players: int = 2
    elimination_enabled: bool = True