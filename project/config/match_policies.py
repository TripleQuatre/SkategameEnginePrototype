from dataclasses import dataclass, field
from enum import Enum


class InitialTurnOrderPolicy(Enum):
    FIXED_PLAYER_ORDER = "fixed_player_order"
    RANDOMIZED = "randomized"
    EXPLICIT_CHOICE = "explicit_choice"
    RELEVANCE = "relevance"


class AttackerRotationPolicy(Enum):
    FOLLOW_TURN_ORDER = "follow_turn_order"


class DefenderOrderPolicy(Enum):
    FOLLOW_TURN_ORDER = "follow_turn_order"
    REVERSE_TURN_ORDER = "reverse_turn_order"


class RelevanceCriterion(Enum):
    ALPHABETICAL = "alphabetical"
    AGE = "age"
    EXPERIENCE_TIME = "experience_time"
    LOCAL_RANK = "local_rank"


@dataclass(frozen=True)
class MatchPolicies:
    initial_turn_order: InitialTurnOrderPolicy = (
        InitialTurnOrderPolicy.FIXED_PLAYER_ORDER
    )
    attacker_rotation: AttackerRotationPolicy = (
        AttackerRotationPolicy.FOLLOW_TURN_ORDER
    )
    defender_order: DefenderOrderPolicy = DefenderOrderPolicy.FOLLOW_TURN_ORDER
    relevance_criterion: RelevanceCriterion | None = None
    explicit_player_order: tuple[str, ...] = field(default_factory=tuple)
