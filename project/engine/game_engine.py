from config.match_parameters import MatchParameters
from core.player import Player
from core.state import GameState
from core.types import DefenseResolutionStatus
from engine.game_flow import GameFlow
from validation.config_validator import ConfigValidator
from validation.state_validator import StateValidator
from modes.one_vs_one import OneVsOneMode
from modes.base_mode import BaseMode
from modes.one_vs_one import OneVsOneMode


class GameEngine:
    def __init__(self, match_parameters: MatchParameters) -> None:
        self.match_parameters = match_parameters
        self.config_validator = ConfigValidator()
        self.state_validator = StateValidator()
        self.game_flow = GameFlow()

        self.config_validator.validate_match_parameters(self.match_parameters)

        self.state = self._create_initial_state()
        self.state.rule_set = self.match_parameters.rule_set

        self.config_validator.validate_rule_set(self.state.rule_set)
        self.state_validator.validate(self.state)

        self.mode = self._load_mode()
        self.mode.validate(self.state)

    def _create_initial_state(self) -> GameState:
        players = [
            Player(id=player_id, name=player_id)
            for player_id in self.match_parameters.player_ids
        ]
        return GameState(players=players)

    def start_game(self) -> None:
        self.state_validator.validate(self.state)
        self.game_flow.start_game(self.state)

    def start_turn(self, trick: str) -> None:
        self.state_validator.validate(self.state)
        self.game_flow.start_turn(self.state, trick)

    def resolve_defense(self, success: bool) -> DefenseResolutionStatus:
        self.state_validator.validate(self.state)
        return self.game_flow.resolve_defense(self.state, success)

    def get_state(self) -> GameState:
        return self.state

    def _load_mode(self, mode_name: str) -> BaseMode:
        if mode_name == "one_vs_one":
            return OneVsOneMode()

        raise ValueError(f"Unknown mode: {mode_name}")
    
    def cancel_turn(self, trick: str) -> None:
        self.state_validator.validate(self.state)
        self.game_flow.cancel_turn(self.state, trick)