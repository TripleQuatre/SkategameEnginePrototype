from dataclasses import dataclass

@dataclass
class MatchParameters:
    player_ids: list[str]
    mode_name: str = "one_vs_one"