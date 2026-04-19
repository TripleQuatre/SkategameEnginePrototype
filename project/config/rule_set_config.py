from dataclasses import dataclass

@dataclass
class RuleSetConfig:
    letters_word: str = "SKATE"
    elimination_enabled: bool = True
    attack_attempts: int = 1
    defense_attempts: int = 1
