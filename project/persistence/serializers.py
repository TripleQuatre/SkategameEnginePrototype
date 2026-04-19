from dataclasses import asdict

from config.match_parameters import MatchParameters
from config.match_policies import (
    AttackerRotationPolicy,
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
    MatchPolicies,
)
from config.rule_set_config import RuleSetConfig
from core.events import Event
from core.history import History
from core.player import Player
from core.state import GameState
from core.types import EventName, Phase, TurnPhase
from persistence.game_save import GameSave


class Serializer:
    def serialize_player(self, player: Player) -> dict:
        return {
            "id": player.id,
            "name": player.name,
            "internal_id": player.internal_id,
            "score": player.score,
            "is_active": player.is_active,
        }

    def deserialize_player(self, data: dict) -> Player:
        return Player(
            id=data["id"],
            name=data["name"],
            internal_id=data["internal_id"],
            score=data["score"],
            is_active=data["is_active"],
        )

    def serialize_event(self, event: Event) -> dict:
        return {
            "name": event.name.value,
            "payload": event.payload,
        }

    def deserialize_event(self, data: dict) -> Event:
        return Event(
            name=EventName(data["name"]),
            payload=data.get("payload", {}),
        )

    def serialize_history(self, history: History) -> dict:
        return {
            "events": [self.serialize_event(event) for event in history.events],
        }

    def deserialize_history(self, data: dict) -> History:
        history = History()
        for event_data in data.get("events", []):
            history.add_event(self.deserialize_event(event_data))
        return history

    def serialize_rule_set(self, rule_set: RuleSetConfig) -> dict:
        return asdict(rule_set)

    def deserialize_rule_set(self, data: dict) -> RuleSetConfig:
        return RuleSetConfig(
            letters_word=data["letters_word"],
            elimination_enabled=data["elimination_enabled"],
            attack_attempts=data.get("attack_attempts", 1),
            defense_attempts=data["defense_attempts"],
        )

    def serialize_match_policies(self, policies: MatchPolicies) -> dict:
        return {
            "initial_turn_order": policies.initial_turn_order.value,
            "attacker_rotation": policies.attacker_rotation.value,
            "defender_order": policies.defender_order.value,
        }

    def deserialize_match_policies(self, data: dict | None) -> MatchPolicies | None:
        if not data:
            return None

        return MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy(data["initial_turn_order"]),
            attacker_rotation=AttackerRotationPolicy(data["attacker_rotation"]),
            defender_order=DefenderOrderPolicy(data["defender_order"]),
        )

    def serialize_match_parameters(self, match_parameters: MatchParameters) -> dict:
        return {
            "player_ids": match_parameters.player_ids,
            "structure_name": match_parameters.structure_name,
            "mode_name": match_parameters.structure_name,
            "rule_set": self.serialize_rule_set(match_parameters.rule_set),
            "policies": self.serialize_match_policies(match_parameters.policies),
            "preset_name": match_parameters.preset_name,
        }

    def deserialize_match_parameters(self, data: dict) -> MatchParameters:
        structure_name = data.get("structure_name", data["mode_name"])

        return MatchParameters(
            player_ids=data["player_ids"],
            structure_name=structure_name,
            rule_set=self.deserialize_rule_set(data["rule_set"]),
            policies=self.deserialize_match_policies(data.get("policies")),
            preset_name=data.get("preset_name"),
        )

    def serialize_game_state(self, state: GameState) -> dict:
        return {
            "players": [self.serialize_player(player) for player in state.players],
            "phase": state.phase.value,
            "turn_phase": state.turn_phase.value,
            "turn_order": state.turn_order,
            "attacker_index": state.attacker_index,
            "attack_attempts_left": state.attack_attempts_left,
            "defender_indices": state.defender_indices,
            "current_defender_position": state.current_defender_position,
            "defense_attempts_left": state.defense_attempts_left,
            "current_trick": state.current_trick,
            "history": self.serialize_history(state.history),
            "rule_set": self.serialize_rule_set(state.rule_set),
            "validated_tricks": state.validated_tricks,
        }

    def deserialize_game_state(self, data: dict) -> GameState:
        turn_phase_value = data.get("turn_phase")
        if turn_phase_value is None:
            turn_phase = (
                TurnPhase.DEFENSE
                if data.get("current_trick") is not None
                else TurnPhase.TURN_OPEN
            )
        else:
            turn_phase = TurnPhase(turn_phase_value)

        return GameState(
            players=[self.deserialize_player(player) for player in data["players"]],
            phase=Phase(data["phase"]),
            turn_phase=turn_phase,
            turn_order=data.get("turn_order", []),
            attacker_index=data["attacker_index"],
            attack_attempts_left=data.get("attack_attempts_left", 0),
            defender_indices=data["defender_indices"],
            current_defender_position=data["current_defender_position"],
            defense_attempts_left=data["defense_attempts_left"],
            current_trick=data.get("current_trick"),
            history=self.deserialize_history(data["history"]),
            rule_set=self.deserialize_rule_set(data["rule_set"]),
            validated_tricks=data.get("validated_tricks", []),
        )

    def serialize_game_save(self, game_save: GameSave) -> dict:
        return {
            "match_parameters": self.serialize_match_parameters(
                game_save.match_parameters
            ),
            "game_state": self.serialize_game_state(game_save.game_state),
        }

    def deserialize_game_save(self, data: dict) -> GameSave:
        return GameSave(
            match_parameters=self.deserialize_match_parameters(
                data["match_parameters"]
            ),
            game_state=self.deserialize_game_state(data["game_state"]),
        )
