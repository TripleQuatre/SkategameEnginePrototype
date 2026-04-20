from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.setup_translator import SetupTranslator
from core.snapshots import SnapshotHistory
from core.state import GameState
from core.types import AttackResolutionStatus, DefenseResolutionStatus
from match.transitions import MatchTransitionService
from match.transitions.transition_service import RuntimeSession
from persistence.game_save import GameSave
from persistence.game_save_repository import GameSaveRepository
from validation.config_validator import ConfigValidator
from validation.state_validator import StateValidator


class GameSession:
    def __init__(self, match_config: MatchConfig | MatchParameters) -> None:
        self.setup_translator = SetupTranslator()
        self._match_config = self._coerce_match_config(match_config)
        self.config_validator = ConfigValidator()
        self.state_validator = StateValidator()
        self.snapshot_history = SnapshotHistory()
        self.save_repository = GameSaveRepository()
        self.transition_service = MatchTransitionService(
            config_validator=self.config_validator,
        )
        runtime = self.transition_service.create_initial_runtime(
            self._match_config,
            self.state_validator,
        )
        self._apply_runtime_session(runtime)

    @property
    def structure_name(self) -> str:
        return self.structure.structure_name

    @property
    def match_config(self) -> MatchConfig:
        return self._match_config

    @property
    def match_parameters(self) -> MatchParameters:
        return self.setup_translator.from_match_config(self.match_config)

    def _coerce_match_config(
        self,
        match_config: MatchConfig | MatchParameters,
    ) -> MatchConfig:
        if isinstance(match_config, MatchParameters):
            return self.setup_translator.from_match_parameters(match_config)
        return match_config

    def _save_snapshot(self) -> None:
        self.snapshot_history.push(self.state, self.match_config)

    def _apply_runtime_session(self, runtime: RuntimeSession) -> None:
        self.state = runtime.state
        self._match_config = runtime.match_config
        self.structure = runtime.structure
        self.game_flow = runtime.game_flow

    def _validate_runtime(self) -> None:
        self.state_validator.validate(self.state)
        self.structure.validate(self.state)

    def _run_state_change(self, action):
        self._validate_runtime()
        self._save_snapshot()
        result = action()
        self._validate_runtime()
        return result

    def start_game(self) -> None:
        self._run_state_change(lambda: self.game_flow.start_game(self.state))

    def start_turn(self, trick: str) -> None:
        self._run_state_change(lambda: self.game_flow.start_turn(self.state, trick))

    def resolve_defense(self, success: bool) -> DefenseResolutionStatus:
        return self._run_state_change(
            lambda: self.game_flow.resolve_defense(self.state, success)
        )

    def resolve_attack(self, success: bool) -> AttackResolutionStatus:
        return self._run_state_change(
            lambda: self.game_flow.resolve_attack(self.state, success)
        )

    def get_state(self) -> GameState:
        return self.state

    def cancel_turn(self, trick: str) -> None:
        self._run_state_change(lambda: self.game_flow.cancel_turn(self.state, trick))

    def add_player_between_turns(self, player_id: str) -> None:
        self._execute_roster_transition(
            lambda: self.transition_service.add_player_between_turns(
                self.state,
                self.match_config,
                self.game_flow.action_validator,
                player_id,
            )
        )

    def remove_player_between_turns(self, player_id: str) -> None:
        self._execute_roster_transition(
            lambda: self.transition_service.remove_player_between_turns(
                self.state,
                self.match_config,
                self.game_flow.action_validator,
                player_id,
            )
        )

    def _execute_roster_transition(self, operation) -> None:
        self._validate_runtime()
        self._save_snapshot()
        transition = operation()
        self._apply_runtime_session(
            self.transition_service.apply_transition(
                self.state,
                transition,
                self.state_validator,
            )
        )

    def undo(self) -> bool:
        snapshot = self.snapshot_history.pop()
        if snapshot is None:
            return False

        restored_match_config = snapshot.restore_match_config() or self.match_config
        runtime = self.transition_service.restore_runtime(
            snapshot.restore_state(),
            restored_match_config,
            self.state_validator,
        )
        self._apply_runtime_session(runtime)
        return True

    def save_game(self, filepath: str) -> None:
        self.state_validator.validate(self.state)
        self.structure.validate(self.state)

        game_save = GameSave(
            match_config=self.match_config,
            game_state=self.state,
        )
        self.save_repository.save(game_save, filepath)

    def load_game(self, filepath: str) -> None:
        game_save = self.save_repository.load(filepath)
        runtime = self.transition_service.restore_runtime(
            game_save.game_state,
            game_save.match_config,
            self.state_validator,
        )
        self._apply_runtime_session(runtime)
        self.snapshot_history.clear()
