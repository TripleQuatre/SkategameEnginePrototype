from enum import Enum

class Phase(Enum):
    SETUP = "setup"
    TURN = "turn"
    END = "end"

class Role(Enum):
    ATTACKER = "attacker"
    DEFENDER = "defender"

class DefenseResolutionStatus(Enum):
    DEFENSE_CONTINUES = "defense_continues"
    TURN_FINISHED = "turn_finished"
    GAME_FINISHED = "game_finished"