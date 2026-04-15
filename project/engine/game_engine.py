from config.match_parameters import MatchParameters
from config.match_policies import MatchPolicies
from core.events import Event
from core.exceptions import InvalidActionError
from core.player import Player
from core.snapshots import SnapshotHistory
from core.state import GameState
from core.types import DefenseResolutionStatus, EventName
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
        self.game_flow = GameFlow(self.mode, self.match_parameters)

    def _create_initial_state(self) -> GameState:
        players = [
            Player(id=player_id, name=player_id)
            for player_id in self.match_parameters.player_ids
        ]
        return GameState(players=players)

    def _save_snapshot(self) -> None:
        self.snapshot_history.push(self.state, self.match_parameters)

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
        return self.mode_factory.create(
            self.match_parameters.mode_name,
            self.match_parameters.policies,
        )

    def cancel_turn(self, trick: str) -> None:
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)
        self._save_snapshot()
        self.game_flow.cancel_turn(self.state, trick)
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)

    def add_player_between_turns(self, player_id: str) -> None:
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)
        self.game_flow.action_validator.validate_add_player_between_turns(
            self.state,
            player_id,
        )

        if any(player.id == player_id for player in self.state.players):
            raise InvalidActionError("This player already exists in the game.")

        previous_mode_name = self.match_parameters.mode_name
        previous_preset_name = self.match_parameters.preset_name

        self._save_snapshot()

        new_player = Player(id=player_id, name=player_id)
        self.state.players.append(new_player)
        self.state.turn_order.append(len(self.state.players) - 1)

        self.match_parameters.player_ids = [player.id for player in self.state.players]
        self.match_parameters.preset_name = None

        if self.match_parameters.mode_name == "one_vs_one":
            self.match_parameters.mode_name = "battle"

        self.config_validator.validate_match_parameters(self.match_parameters)
        self.mode = self._load_mode()
        self.game_flow = GameFlow(self.mode, self.match_parameters)

        self.state.history.add_event(
            Event(
                name=EventName.PLAYER_JOINED,
                payload={
                    "player_id": new_player.id,
                    "player_name": new_player.name,
                    "previous_mode_name": previous_mode_name,
                    "mode_name": self.match_parameters.mode_name,
                    "previous_preset_name": previous_preset_name,
                    "preset_name": self.match_parameters.preset_name,
                    "player_names": [player.name for player in self.state.players],
                    "turn_order": list(self.state.turn_order),
                    "attacker_id": self.state.players[self.state.attacker_index].id,
                    "attacker_name": self.state.players[self.state.attacker_index].name,
                },
            )
        )

        self.state_validator.validate(self.state)
        self.mode.validate(self.state)

    def remove_player_between_turns(self, player_id: str) -> None:
        self.state_validator.validate(self.state)
        self.mode.validate(self.state)
        self.game_flow.action_validator.validate_remove_player_between_turns(
            self.state,
            player_id,
        )

        removed_index = self._find_player_index(player_id)
        if removed_index is None:
            raise InvalidActionError("This player does not exist in the game.")

        if len(self.state.players) <= 2:
            raise InvalidActionError(
                "Cannot remove a player if fewer than two players would remain."
            )

        previous_mode_name = self.match_parameters.mode_name
        previous_preset_name = self.match_parameters.preset_name
        removed_player = self.state.players[removed_index]

        self._save_snapshot()

        new_attacker_index = self._compute_attacker_after_removal(removed_index)
        remaining_players = [
            player for index, player in enumerate(self.state.players) if index != removed_index
        ]
        remapped_turn_order = self._remap_turn_order_after_removal(removed_index)

        self.state.players = remaining_players
        self.state.turn_order = remapped_turn_order
        self.state.attacker_index = new_attacker_index

        self.match_parameters.player_ids = [player.id for player in self.state.players]
        self.match_parameters.preset_name = None

        if len(self.state.players) == 2 and self.match_parameters.mode_name == "battle":
            self.match_parameters.mode_name = "one_vs_one"
            self.match_parameters.policies = MatchPolicies()
            self.state.turn_order = [0, 1]

        self.config_validator.validate_match_parameters(self.match_parameters)
        self.mode = self._load_mode()
        self.game_flow = GameFlow(self.mode, self.match_parameters)

        self.state.history.add_event(
            Event(
                name=EventName.PLAYER_REMOVED,
                payload={
                    "player_id": removed_player.id,
                    "player_name": removed_player.name,
                    "previous_mode_name": previous_mode_name,
                    "mode_name": self.match_parameters.mode_name,
                    "previous_preset_name": previous_preset_name,
                    "preset_name": self.match_parameters.preset_name,
                    "player_names": [player.name for player in self.state.players],
                    "turn_order": list(self.state.turn_order),
                    "attacker_id": self.state.players[self.state.attacker_index].id,
                    "attacker_name": self.state.players[self.state.attacker_index].name,
                },
            )
        )

        self.state_validator.validate(self.state)
        self.mode.validate(self.state)

    def undo(self) -> bool:
        snapshot = self.snapshot_history.pop()
        if snapshot is None:
            return False

        restored_state = snapshot.restore_state()
        restored_match_parameters = snapshot.restore_match_parameters()

        if restored_match_parameters is not None:
            self.match_parameters = restored_match_parameters
            self.mode = self._load_mode()
            self.game_flow = GameFlow(self.mode, self.match_parameters)
            restored_state.rule_set = self.match_parameters.rule_set

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

        loaded_mode = self.mode_factory.create(
            game_save.match_parameters.mode_name,
            game_save.match_parameters.policies,
        )
        loaded_mode.validate(game_save.game_state)

        self.match_parameters = game_save.match_parameters
        self.mode = loaded_mode
        self.game_flow = GameFlow(self.mode, self.match_parameters)
        self.state = game_save.game_state
        self.snapshot_history.clear()

    def _find_player_index(self, player_id: str) -> int | None:
        for index, player in enumerate(self.state.players):
            if player.id == player_id:
                return index
        return None

    def _remap_turn_order_after_removal(self, removed_index: int) -> list[int]:
        old_to_new: dict[int, int] = {}
        next_index = 0

        for index in range(len(self.state.players)):
            if index == removed_index:
                continue
            old_to_new[index] = next_index
            next_index += 1

        return [
            old_to_new[index]
            for index in self.state.turn_order
            if index != removed_index
        ]

    def _compute_attacker_after_removal(self, removed_index: int) -> int:
        if self.state.attacker_index != removed_index:
            old_to_new = {
                old_index: new_index
                for new_index, old_index in enumerate(
                    index
                    for index in range(len(self.state.players))
                    if index != removed_index
                )
            }
            return old_to_new[self.state.attacker_index]

        current_position = self.state.turn_order.index(removed_index)
        turn_order_length = len(self.state.turn_order)

        for offset in range(1, turn_order_length + 1):
            candidate_index = self.state.turn_order[
                (current_position + offset) % turn_order_length
            ]
            if candidate_index == removed_index:
                continue
            if not self.state.players[candidate_index].is_active:
                continue

            old_to_new = {
                old_index: new_index
                for new_index, old_index in enumerate(
                    index
                    for index in range(len(self.state.players))
                    if index != removed_index
                )
            }
            return old_to_new[candidate_index]

        raise InvalidActionError("No valid attacker can be assigned after removal.")
