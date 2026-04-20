from config.fine_rules_config import FineRulesConfig
from core.player import Player
from core.state import GameState


class TrickRules:
    def __init__(self, config: FineRulesConfig | None = None) -> None:
        self.config = config if config is not None else FineRulesConfig()

    def can_player_defend(self, state: GameState, player: Player) -> bool:
        return player.is_active

    def can_player_attack(self, state: GameState, player: Player) -> bool:
        return player.is_active

    def normalize_trick(self, trick: str) -> str:
        return trick.strip().lower()

    def is_trick_already_validated(self, state: GameState, trick: str) -> bool:
        normalized_trick = self.normalize_trick(trick)
        return normalized_trick in state.validated_tricks

    def uniqueness_blocks_trick(self, state: GameState, trick: str) -> bool:
        if not self.config.uniqueness_enabled:
            return False
        return self.is_trick_already_validated(state, trick)
