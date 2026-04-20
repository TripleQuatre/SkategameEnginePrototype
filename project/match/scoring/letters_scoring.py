from config.scoring_config import ScoringConfig
from core.player import Player
from core.state import GameState


class LettersScoring:
    def __init__(self, config: ScoringConfig | None = None) -> None:
        self.config = config

    def apply_letter_penalty(self, state: GameState, player: Player) -> None:
        player.score += 1

    def get_penalty_display(self, state: GameState, player: Player) -> str:
        word = (
            state.rule_set.letters_word
            if hasattr(state, "rule_set")
            else self.config.letters_word
        )
        return word[: player.score]
