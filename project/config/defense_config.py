from dataclasses import dataclass


@dataclass(frozen=True)
class DefenseConfig:
    defense_attempts: int = 1
