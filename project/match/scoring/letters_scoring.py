from core.player import Player
from core.state import GameState


class LettersScoring:
    def apply_letter_penalty(self, state: GameState, player: Player) -> None:
        player.score += 1

    def get_penalty_display(self, state: GameState, player: Player) -> str:
        return state.rule_set.letters_word[: player.score]
