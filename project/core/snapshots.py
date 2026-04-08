from dataclasses import dataclass
from core.state import GameState

@dataclass
class Snapshot:
    state: GameState