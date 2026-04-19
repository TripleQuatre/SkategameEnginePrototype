from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringConfig:
    scoring_type: str = "letters"
    letters_word: str = "SKATE"
