from core.player import Player
from core.state import GameState


class TrickRules:
    def can_player_defend(self, state: GameState, player: Player) -> bool:
        return player.is_active

    def can_player_attack(self, state: GameState, player: Player) -> bool:
        return player.is_active

    def normalize_trick(self, trick: str) -> str:
        return trick.strip().lower()

    def is_trick_already_validated(self, state: GameState, trick: str) -> bool:
        normalized_trick = self.normalize_trick(trick)
        return normalized_trick in state.validated_tricks
