from dataclasses import dataclass


@dataclass(frozen=True)
class AttackConfig:
    attack_attempts: int = 1
