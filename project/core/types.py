from enum import Enum


class Phase(Enum):
    SETUP = "setup"
    TURN = "turn"
    END = "end"


class TurnPhase(Enum):
    TURN_OPEN = "turn_open"
    ATTACK = "attack"
    DEFENSE = "defense"
    TURN_FINISHED = "turn_finished"


class Role(Enum):
    ATTACKER = "attacker"
    DEFENDER = "defender"


class DefenseResolutionStatus(Enum):
    DEFENSE_CONTINUES = "defense_continues"
    TURN_FINISHED = "turn_finished"
    GAME_FINISHED = "game_finished"


class AttackResolutionStatus(Enum):
    ATTACK_CONTINUES = "attack_continues"
    DEFENSE_READY = "defense_ready"
    TURN_FAILED = "turn_failed"


class ExchangeStatus(Enum):
    ATTACK_CONTINUES = "attack_continues"
    DEFENSE_READY = "defense_ready"
    DEFENSE_CONTINUES = "defense_continues"
    ATTACKER_FAILED = "attacker_failed"
    ATTACKER_HELD = "attacker_held"
    GAME_FINISHED = "game_finished"


class EventName(Enum):
    GAME_STARTED = "game_started"
    PLAYER_JOINED = "player_joined"
    PLAYER_REMOVED = "player_removed"
    TURN_STARTED = "turn_started"
    ATTACK_TRICK_CHANGED = "attack_trick_changed"
    ATTACK_FAILED_ATTEMPT = "attack_failed_attempt"
    ATTACK_SUCCEEDED = "attack_succeeded"
    DEFENSE_SUCCEEDED = "defense_succeeded"
    DEFENSE_FAILED_ATTEMPT = "defense_failed_attempt"
    LETTER_RECEIVED = "letter_received"
    PLAYER_ELIMINATED = "player_eliminated"
    TURN_ENDED = "turn_ended"
    TURN_FAILED = "turn_failed"
    GAME_FINISHED = "game_finished"
