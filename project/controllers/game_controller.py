from application.game_session import GameSession
from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from core.state import GameState
from core.types import AttackResolutionStatus, DefenseResolutionStatus
from dictionary.base import DictionaryDefinition
from dictionary.base import DictionaryResolution, DictionarySuggestion
from match.structure.base_structure import BaseStructure


class GameController:
    def __init__(self, match_config: MatchConfig | MatchParameters) -> None:
        self.session = GameSession(match_config)

    @property
    def match_config(self) -> MatchConfig:
        return self.session.match_config

    @property
    def match_parameters(self) -> MatchParameters:
        return self.session.match_parameters

    @property
    def structure(self) -> BaseStructure:
        return self.session.structure

    @property
    def structure_name(self) -> str:
        return self.session.structure_name

    @property
    def dictionary_definition(self) -> DictionaryDefinition:
        return self.session.trick_dictionary.definition

    def start_game(self) -> None:
        self.session.start_game()

    def start_turn(self, trick: str) -> None:
        self.session.start_turn(trick)

    def resolve_defense(self, success: bool) -> DefenseResolutionStatus:
        return self.session.resolve_defense(success)

    def resolve_attack(
        self,
        success: bool,
        switch_normal_verified: bool | None = None,
    ) -> AttackResolutionStatus:
        return self.session.resolve_attack(
            success,
            switch_normal_verified=switch_normal_verified,
        )

    def change_attack_trick(self, trick: str) -> None:
        self.session.change_attack_trick(trick)

    def get_state(self) -> GameState:
        return self.session.get_state()

    def cancel_turn(self, trick: str) -> None:
        self.session.cancel_turn(trick)

    def undo(self) -> bool:
        return self.session.undo()

    def add_player_between_turns(self, player_id: str) -> None:
        self.session.add_player_between_turns(player_id)

    def remove_player_between_turns(self, player_id: str) -> None:
        self.session.remove_player_between_turns(player_id)

    def save_game(self, filepath: str) -> None:
        self.session.save_game(filepath)

    def load_game(self, filepath: str) -> None:
        self.session.load_game(filepath)

    def suggest_tricks(self, raw_value: str) -> list[DictionarySuggestion]:
        return self.session.suggest_tricks(raw_value)

    def resolve_trick_input(self, raw_value: str) -> DictionaryResolution | None:
        return self.session.resolve_trick_input(raw_value)

    def can_change_attack_trick(self) -> bool:
        return self.session.can_change_attack_trick()

    def current_attack_trick_requires_change(self) -> bool:
        return self.session.current_attack_trick_requires_change()

    def current_attack_requires_switch_normal_verification(self) -> bool:
        return self.session.current_attack_requires_switch_normal_verification()
