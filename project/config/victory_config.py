from dataclasses import dataclass


@dataclass(frozen=True)
class VictoryConfig:
    victory_type: str = "last_player_standing"
    elimination_enabled: bool = True
