from dataclasses import asdict

from config.attack_config import AttackConfig
from config.defense_config import DefenseConfig
from config.fine_rules_config import FineRulesConfig
from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.match_policies import (
    AttackerRotationPolicy,
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
    MatchPolicies,
    RelevanceCriterion,
)
from config.rule_set_config import RuleSetConfig
from config.scoring_config import ScoringConfig
from config.setup_translator import SetupTranslator
from config.structure_config import StructureConfig
from config.victory_config import VictoryConfig
from core.events import Event
from core.history import History
from core.player import Player
from core.player_score import PlayerScoreState
from core.state import GameState
from core.types import EventName, Phase, TurnPhase
from persistence.game_save import GameSave


class Serializer:
    def __init__(self) -> None:
        self.setup_translator = SetupTranslator()

    def serialize_player(self, player: Player) -> dict:
        return {
            "id": player.id,
            "name": player.name,
            "internal_id": player.internal_id,
            "score_state": {
                "letters": player.score,
                "points": player.points,
            },
            "is_active": player.is_active,
        }

    def deserialize_player(self, data: dict) -> Player:
        score_state_data = data.get("score_state")
        score_state = (
            PlayerScoreState(
                letters=score_state_data.get("letters", 0),
                points=score_state_data.get("points", 0),
            )
            if score_state_data is not None
            else None
        )
        return Player(
            id=data["id"],
            name=data["name"],
            internal_id=data["internal_id"],
            score=data.get("score", 0),
            points=data.get("points", 0),
            score_state=score_state,
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
            "relevance_criterion": (
                policies.relevance_criterion.value
                if policies.relevance_criterion is not None
                else None
            ),
            "explicit_player_order": list(policies.explicit_player_order),
        }

    def deserialize_match_policies(self, data: dict | None) -> MatchPolicies | None:
        if not data:
            return None

        return MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy(data["initial_turn_order"]),
            attacker_rotation=AttackerRotationPolicy(data["attacker_rotation"]),
            defender_order=DefenderOrderPolicy(data["defender_order"]),
            relevance_criterion=(
                RelevanceCriterion(data["relevance_criterion"])
                if data.get("relevance_criterion")
                else None
            ),
            explicit_player_order=tuple(data.get("explicit_player_order", [])),
        )

    def serialize_match_config(self, match_config: MatchConfig) -> dict:
        return {
            "player_ids": list(match_config.player_ids),
            "player_profile_ids": list(match_config.player_profile_ids),
            "structure": {
                "structure_name": match_config.structure_name,
                "policies": self.serialize_match_policies(match_config.policies),
            },
            "sport": match_config.sport,
            "attack": asdict(match_config.attack),
            "defense": asdict(match_config.defense),
            "scoring": asdict(match_config.scoring),
            "victory": asdict(match_config.victory),
            "fine_rules": asdict(match_config.fine_rules),
            "preset_name": match_config.preset_name,
        }

    def deserialize_match_config(self, data: dict) -> MatchConfig:
        if "structure" in data:
            structure_data = data["structure"]
            return MatchConfig(
                player_ids=list(data.get("player_ids", [])),
                player_profile_ids=list(data.get("player_profile_ids", [])),
                structure=StructureConfig(
                    structure_name=structure_data["structure_name"],
                    policies=(
                        self.deserialize_match_policies(structure_data.get("policies"))
                        or MatchPolicies()
                    ),
                ),
                sport=data.get("sport", "inline"),
                attack=AttackConfig(**data.get("attack", {})),
                defense=DefenseConfig(**data.get("defense", {})),
                scoring=ScoringConfig(**data.get("scoring", {})),
                victory=VictoryConfig(**data.get("victory", {})),
                fine_rules=FineRulesConfig(**data.get("fine_rules", {})),
                preset_name=data.get("preset_name"),
            )

        return self.setup_translator.from_match_parameters(
            self.deserialize_match_parameters(data)
        )

    def serialize_match_parameters(self, match_parameters: MatchParameters) -> dict:
        return {
            "player_ids": match_parameters.player_ids,
            "player_profile_ids": list(match_parameters.player_profile_ids),
            "structure_name": match_parameters.structure_name,
            "sport": match_parameters.sport,
            "rule_set": self.serialize_rule_set(match_parameters.rule_set),
            "policies": self.serialize_match_policies(match_parameters.policies),
            "fine_rules": asdict(match_parameters.fine_rules),
            "preset_name": match_parameters.preset_name,
        }

    def deserialize_match_parameters(self, data: dict) -> MatchParameters:
        if "structure" in data:
            return self.setup_translator.from_match_config(
                self.deserialize_match_config(data)
            )

        return MatchParameters(
            player_ids=data["player_ids"],
            player_profile_ids=list(data.get("player_profile_ids", [])),
            structure_name=data["structure_name"],
            sport=data.get("sport", "inline"),
            rule_set=self.deserialize_rule_set(data["rule_set"]),
            policies=self.deserialize_match_policies(data.get("policies")),
            fine_rules=FineRulesConfig(**data.get("fine_rules", {})),
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
            "current_trick_data": state.current_trick_data,
            "history": self.serialize_history(state.history),
            "validated_tricks": state.validated_tricks,
            "validated_trick_data": state.validated_trick_data,
            "failed_attack_trick_data": state.failed_attack_trick_data,
            "failed_attack_turn_trick_keys": state.failed_attack_turn_trick_keys,
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
            current_trick_data=data.get("current_trick_data"),
            history=self.deserialize_history(data["history"]),
            validated_tricks=data.get("validated_tricks", []),
            validated_trick_data=data.get("validated_trick_data", []),
            failed_attack_trick_data=data.get("failed_attack_trick_data", []),
            failed_attack_turn_trick_keys=data.get(
                "failed_attack_turn_trick_keys", []
            ),
        )

    def serialize_game_save(self, game_save: GameSave) -> dict:
        return {
            "match_config": self.serialize_match_config(game_save.match_config),
            "game_state": self.serialize_game_state(game_save.game_state),
        }

    def deserialize_game_save(self, data: dict) -> GameSave:
        match_config_data = data.get("match_config")
        if match_config_data is not None:
            match_config = self.deserialize_match_config(match_config_data)
        else:
            match_config = self.setup_translator.from_match_parameters(
                self.deserialize_match_parameters(data["match_parameters"])
            )

        return GameSave(
            match_config=match_config,
            game_state=self.deserialize_game_state(data["game_state"]),
        )
