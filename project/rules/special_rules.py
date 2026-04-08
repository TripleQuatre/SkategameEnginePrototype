from core.player import Player
from core.state import GameState


class SpecialRules:
    def can_player_defend(self, state: GameState, player: Player) -> bool:
        return player.is_active

    def can_player_attack(self, state: GameState, player: Player) -> bool:
        return player.is_active