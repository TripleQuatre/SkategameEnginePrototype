from config.scoring_config import ScoringConfig
from config.victory_config import VictoryConfig
from core.player import Player
from core.state import GameState


class LastPlayerStandingVictory:
    def __init__(
        self,
        scoring_config: ScoringConfig | None = None,
        victory_config: VictoryConfig | None = None,
    ) -> None:
        self.scoring_config = scoring_config
        self.victory_config = victory_config

    def is_player_eliminated(self, state: GameState, player: Player) -> bool:
        word = (
            state.rule_set.letters_word
            if hasattr(state, "rule_set")
            else self.scoring_config.letters_word
        )
        return player.score >= len(word)

    def apply_eliminations(self, state: GameState) -> list[Player]:
        eliminated_players = []

        elimination_enabled = (
            state.rule_set.elimination_enabled
            if hasattr(state, "rule_set")
            else self.victory_config.elimination_enabled
        )
        if not elimination_enabled:
            return eliminated_players

        for player in state.players:
            if player.is_active and self.is_player_eliminated(state, player):
                player.is_active = False
                eliminated_players.append(player)

        return eliminated_players

    def get_active_players(self, state: GameState) -> list[Player]:
        return [player for player in state.players if player.is_active]

    def is_game_finished(self, state: GameState) -> bool:
        return len(self.get_active_players(state)) <= 1

    def get_winner(self, state: GameState) -> Player | None:
        active_players = self.get_active_players(state)

        if len(active_players) == 1:
            return active_players[0]

        return None
