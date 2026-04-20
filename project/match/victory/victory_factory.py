from config.scoring_config import ScoringConfig
from config.victory_config import VictoryConfig
from match.victory.last_player_standing import LastPlayerStandingVictory


class VictoryFactory:
    def create(
        self,
        victory_config: VictoryConfig,
        scoring_config: ScoringConfig,
    ):
        if victory_config.victory_type == "last_player_standing":
            return LastPlayerStandingVictory(scoring_config, victory_config)

        raise ValueError(f"Unknown victory type: {victory_config.victory_type}")
