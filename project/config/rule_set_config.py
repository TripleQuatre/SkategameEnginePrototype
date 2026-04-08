from dataclasses import dataclass

@dataclass
class RuleSetConfig:
    letters_word: str = "SKATE"
    elimination_enabled: bool = True
    defense_attempts: int = 1