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


class EventName(Enum):
    GAME_STARTED = "game_started"
    PLAYER_JOINED = "player_joined"
    TURN_STARTED = "turn_started"
    DEFENSE_SUCCEEDED = "defense_succeeded"
    DEFENSE_FAILED_ATTEMPT = "defense_failed_attempt"
    LETTER_RECEIVED = "letter_received"
    PLAYER_ELIMINATED = "player_eliminated"
    TURN_ENDED = "turn_ended"
    TURN_FAILED = "turn_failed"
    GAME_FINISHED = "game_finished"
