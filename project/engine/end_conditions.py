from core.state import GameState
from core.player import Player

class EndConditions:
    def is_player_eliminated(self, state: GameState, player: Player) -> bool:
        return player.score >= len(state.rule_set.letters_word)

    def apply_eliminations(self, state: GameState) -> list[Player]:
        eliminated_players = []

        if not state.rule_set.elimination_enabled:
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