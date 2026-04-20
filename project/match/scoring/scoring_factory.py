from config.scoring_config import ScoringConfig
from match.scoring.letters_scoring import LettersScoring


class ScoringFactory:
    def create(self, scoring_config: ScoringConfig):
        if scoring_config.scoring_type == "letters":
            return LettersScoring(scoring_config)

        raise ValueError(f"Unknown scoring type: {scoring_config.scoring_type}")
