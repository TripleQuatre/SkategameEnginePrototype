from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.setup_translator import SetupTranslator
from core.snapshots import SnapshotHistory
from core.state import GameState
from core.types import AttackResolutionStatus, DefenseResolutionStatus, Phase
from dictionary.base import DictionaryResolution, DictionarySuggestion
from dictionary.runtime import get_runtime_dictionary, resolve_runtime_trick_record
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
        self.trick_dictionary = get_runtime_dictionary()
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

    def resolve_attack(
        self,
        success: bool,
        switch_normal_verified: bool | None = None,
    ) -> AttackResolutionStatus:
        return self._run_state_change(
            lambda: self.game_flow.resolve_attack(
                self.state,
                success,
                switch_normal_verified=switch_normal_verified,
            )
        )

    def change_attack_trick(self, trick: str) -> None:
        self._run_state_change(lambda: self.game_flow.change_attack_trick(self.state, trick))

    def get_state(self) -> GameState:
        return self.state

    def cancel_turn(self, trick: str) -> None:
        self._run_state_change(lambda: self.game_flow.cancel_turn(self.state, trick))

    def add_player_between_turns(
        self,
        player_id: str,
        *,
        player_name: str | None = None,
        player_profile_id: str | None = None,
    ) -> None:
        self._execute_roster_transition(
            lambda: self.transition_service.add_player_between_turns(
                self.state,
                self.match_config,
                self.game_flow.action_validator,
                player_id,
                player_name=player_name,
                player_profile_id=player_profile_id,
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

    def suggest_tricks(self, raw_value: str) -> list[DictionarySuggestion]:
        suggestions = self.trick_dictionary.suggest(raw_value)
        return [
            suggestion
            for suggestion in suggestions
            if self._switch_suggestion_is_allowed(suggestion)
        ]

    def resolve_trick_input(self, raw_value: str) -> DictionaryResolution | None:
        resolution = self.trick_dictionary.resolve(raw_value)
        if resolution is None:
            return None
        if not self._switch_candidate_is_allowed(
            resolution.label,
            trick_data=resolution.to_dict(),
        ):
            return None
        return resolution

    def can_change_attack_trick(self) -> bool:
        return self.game_flow.can_change_attack_trick(self.state)

    def current_attack_trick_requires_change(self) -> bool:
        return self.game_flow.current_attack_trick_requires_change(self.state)

    def current_attack_requires_switch_normal_verification(self) -> bool:
        return self.game_flow.current_attack_requires_switch_normal_verification(
            self.state
        )

    def _get_current_attacker_id(self) -> str:
        return self.state.players[self.state.attacker_index].id

    def _switch_candidate_is_allowed(
        self,
        trick: str,
        *,
        trick_data: dict[str, object] | None = None,
    ) -> bool:
        if self.state.phase != Phase.TURN or not self.state.players:
            return True
        attacker_id = self._get_current_attacker_id()
        return not self.game_flow.special_rules.switch_blocks_trick(
            self.state,
            trick,
            attacker_id=attacker_id,
            trick_data=trick_data,
        )

    def _switch_suggestion_is_allowed(self, suggestion: DictionarySuggestion) -> bool:
        candidate = suggestion.completion or suggestion.label
        _, trick_data = resolve_runtime_trick_record(candidate)
        if trick_data is not None:
            return self._switch_candidate_is_allowed(candidate, trick_data=trick_data)

        lowered_candidate = candidate.strip().lower()
        if "switch" not in lowered_candidate:
            return True

        if self.match_config.fine_rules.switch_mode == "disabled":
            return False

        if self.match_config.fine_rules.switch_mode != "normal":
            return True

        normal_candidate = candidate.replace(" Switch", "", 1).replace(" switch", "", 1)
        _, normal_trick_data = resolve_runtime_trick_record(normal_candidate.strip())
        if normal_trick_data is None:
            return True

        return any(
            trick_data.get("canonical_key") == normal_trick_data["canonical_key"]
            for trick_data in self.state.validated_trick_data
        )
