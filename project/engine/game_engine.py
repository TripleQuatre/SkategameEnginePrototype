from config.match_parameters import MatchParameters
from core.player import Player
from core.snapshots import SnapshotHistory
from core.state import GameState
from core.types import DefenseResolutionStatus
from engine.game_flow import GameFlow
from modes.base_mode import BaseMode
from modes.mode_factory import ModeFactory
from persistence.game_save import GameSave
from persistence.game_save_repository import GameSaveRepository
from validation.config_validator import ConfigValidator
from validation.state_validator import StateValidator


class GameEngine:
    def __init__(self, match_parameters: MatchParameters) -> None:
        self.match_parameters = match_parameters
        self.config_validator = ConfigValidator()
        self.state_validator = StateValidator()
        self.snapshot_history = SnapshotHistory()
        self.save_repository = GameSaveRepository()
        self.mode_factory = ModeFactory()

        self.config_validator.validate_match_parameters(self.match_parameters)

        self.state = self._create_initial_state()
        self.state.rule_set = self.match_parameters.rule_set

        self.config_validator.validate_rule_set(self.state.rule_set)
        self.state_validator.validate(self.state)

        self.mode = self._load_mode()
        self.mode.validate(self.state)
        self.game_flow = GameFlow(self.mode)

    def _create_initial_state(self) -> GameState:
        players = [
            Player(id=player_id, name=player_id)
            for player_id in self.match_parameters.player_ids
        ]
        return GameState(players=players)

    def _save_snapshot(self) -> None:
        self.snapshot_history.push(self.state)

    def start_game(self) -> None:
        self.state_validator.validate(self.state)
        self._save_snapshot()
        self.game_flow.start_game(self.state)
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)

    def start_turn(self, trick: str) -> None:
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)
        self._save_snapshot()
        self.game_flow.start_turn(self.state, trick)
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)

    def resolve_defense(self, success: bool) -> DefenseResolutionStatus:
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)
        self._save_snapshot()
        result = self.game_flow.resolve_defense(self.state, success)
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)
        return result

    def get_state(self) -> GameState:
        return self.state

    def _load_mode(self) -> BaseMode:
        return self.mode_factory.create(self.match_parameters.mode_name)

    def cancel_turn(self, trick: str) -> None:
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)
        self._save_snapshot()
        self.game_flow.cancel_turn(self.state, trick)
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)

    def undo(self) -> bool:
        snapshot = self.snapshot_history.pop()
        if snapshot is None:
            return False

        restored_state = snapshot.restore_state()
        self.state_validator.validate(restored_state)
        self.mode.validate(restored_state)
        self.state = restored_state
        return True

    def save_game(self, filepath: str) -> None:
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)
        self.match_parameters.rule_set = self.state.rule_set

        game_save = GameSave(
            match_parameters=self.match_parameters,
            game_state=self.state,
        )
        self.save_repository.save(game_save, filepath)

    def load_game(self, filepath: str) -> None:
        game_save = self.save_repository.load(filepath)
        game_save.game_state.rule_set = game_save.match_parameters.rule_set

        self.config_validator.validate_match_parameters(game_save.match_parameters)
        self.config_validator.validate_rule_set(game_save.match_parameters.rule_set)
        self.state_validator.validate(game_save.game_state)

        loaded_mode = self.mode_factory.create(game_save.match_parameters.mode_name)
        loaded_mode.validate(game_save.game_state)

        self.match_parameters = game_save.match_parameters
        self.mode = loaded_mode
        self.game_flow = GameFlow(self.mode)
        self.state = game_save.game_state
        self.snapshot_history.clear()
