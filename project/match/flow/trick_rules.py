from config.fine_rules_config import FineRulesConfig
from core.player import Player
from core.state import GameState
from core.types import TurnPhase
from dictionary.models import ConstructedTrick
from dictionary.runtime import resolve_runtime_trick_record


class TrickRules:
    def __init__(self, config: FineRulesConfig | None = None) -> None:
        self.config = config if config is not None else FineRulesConfig()

    @property
    def multiple_attack_enabled(self) -> bool:
        return self.config.multiple_attack_enabled

    @property
    def no_repetition_enabled(self) -> bool:
        return self.config.no_repetition

    @property
    def switch_mode(self) -> str:
        return self.config.switch_mode

    def can_player_defend(self, state: GameState, player: Player) -> bool:
        return player.is_active

    def can_player_attack(self, state: GameState, player: Player) -> bool:
        return player.is_active

    def normalize_trick(self, trick: str) -> str:
        return trick.strip().lower()

    def _build_trick_key(self, trick: str) -> tuple[str, dict[str, object] | None]:
        _, resolved_trick_data = resolve_runtime_trick_record(trick)
        if resolved_trick_data is not None:
            return str(resolved_trick_data["canonical_key"]), resolved_trick_data
        return self.normalize_trick(trick), None

    def _build_switch_descriptor(
        self,
        trick: str,
        *,
        trick_data: dict[str, object] | None = None,
    ) -> dict[str, object] | None:
        resolved_trick_data = trick_data
        if resolved_trick_data is None:
            _, resolved_trick_data = resolve_runtime_trick_record(trick)
        if resolved_trick_data is None:
            return None

        trick_payload = resolved_trick_data.get("trick")
        if not isinstance(trick_payload, dict):
            return None

        raw_segments = trick_payload.get("segments")
        if not isinstance(raw_segments, list) or len(raw_segments) != 1:
            return None

        segment = raw_segments[0]
        if not isinstance(segment, dict) or not bool(segment.get("switch", False)):
            return None

        normal_segment = dict(segment)
        normal_segment["switch"] = False
        normal_trick = ConstructedTrick.from_dict(
            {
                "segments": [normal_segment],
                "trick_exit": trick_payload.get("trick_exit"),
            }
        )
        normal_trick_data = normal_trick.to_dict()

        return {
            "switch_trick_data": resolved_trick_data,
            "switch_key": str(resolved_trick_data["canonical_key"]),
            "switch_label": str(resolved_trick_data["label"]),
            "normal_trick_data": normal_trick_data,
            "normal_key": str(normal_trick_data["canonical_key"]),
            "normal_label": str(normal_trick_data["label"]),
        }

    def is_switch_trick(
        self,
        trick: str | None,
        *,
        trick_data: dict[str, object] | None = None,
    ) -> bool:
        if trick is None:
            return False
        return self._build_switch_descriptor(trick, trick_data=trick_data) is not None

    def _attacker_validated_trick_key(
        self,
        state: GameState,
        *,
        attacker_id: str,
        trick_key: str,
    ) -> bool:
        return any(
            trick_data.get("canonical_key") == trick_key
            and trick_data.get("validated_by_attacker_id") == attacker_id
            for trick_data in state.validated_trick_data
        )

    def _any_attacker_validated_trick_key(
        self,
        state: GameState,
        *,
        trick_key: str,
    ) -> bool:
        return any(
            trick_data.get("canonical_key") == trick_key
            for trick_data in state.validated_trick_data
        )

    def current_attack_requires_switch_normal_verification(
        self,
        state: GameState,
    ) -> bool:
        return (
            self.config.switch_mode == "verified"
            and state.current_trick is not None
            and state.turn_phase == TurnPhase.ATTACK
            and self.is_switch_trick(
                state.current_trick,
                trick_data=state.current_trick_data,
            )
        )

    def is_trick_already_validated(self, state: GameState, trick: str) -> bool:
        _, resolved_trick_data = resolve_runtime_trick_record(trick)
        if resolved_trick_data is not None:
            trick_key = resolved_trick_data["canonical_key"]
            if any(
                trick_data.get("canonical_key") == trick_key
                for trick_data in state.validated_trick_data
            ):
                return True

        normalized_trick = self.normalize_trick(trick)
        return normalized_trick in state.validated_tricks

    def uniqueness_blocks_trick(self, state: GameState, trick: str) -> bool:
        if not self.config.uniqueness_enabled:
            return False
        return self.is_trick_already_validated(state, trick)

    def switch_blocks_trick(
        self,
        state: GameState,
        trick: str,
        *,
        attacker_id: str,
        trick_data: dict[str, object] | None = None,
    ) -> bool:
        descriptor = self._build_switch_descriptor(trick, trick_data=trick_data)
        if descriptor is None:
            return False

        if self.config.switch_mode == "disabled":
            return True
        if self.config.switch_mode == "enabled":
            return False
        if self.config.switch_mode == "normal":
            return not self._any_attacker_validated_trick_key(
                state,
                trick_key=str(descriptor["normal_key"]),
            )
        if self.config.switch_mode == "verified":
            return False

        return not self._attacker_validated_trick_key(
            state,
            attacker_id=attacker_id,
            trick_key=str(descriptor["normal_key"]),
        )

    def switch_block_message(
        self,
        trick: str,
        *,
        trick_data: dict[str, object] | None = None,
    ) -> str:
        descriptor = self._build_switch_descriptor(trick, trick_data=trick_data)
        if descriptor is None:
            return "This trick is not allowed by the current switch rule."

        if self.config.switch_mode == "disabled":
            return "Switch tricks are disabled for this match."

        normal_label = str(descriptor["normal_label"])
        if self.config.switch_mode == "verified":
            return (
                "Verified switch rule: validate the switch, then confirm whether the normal "
                f"version ('{normal_label}') was successfully demonstrated."
            )
        return (
            "Normal switch rule: you must first validate the normal version "
            f"('{normal_label}') during the match before using this switch trick."
        )

    def build_consumed_trick_record(
        self,
        state: GameState,
        *,
        attacker_id: str,
        attacker_name: str,
    ) -> dict[str, object] | None:
        if state.current_trick is None:
            return None

        _, current_trick_data = resolve_runtime_trick_record(state.current_trick)
        effective_trick_data = (
            state.current_trick_data
            if state.current_trick_data is not None
            else current_trick_data
        )
        if effective_trick_data is None:
            return None

        record = dict(effective_trick_data)
        record["validated_by_attacker_id"] = attacker_id
        record["validated_by_attacker_name"] = attacker_name

        if (
            self.config.switch_mode == "verified"
            and self._build_switch_descriptor(
                state.current_trick,
                trick_data=effective_trick_data,
            )
            is not None
        ):
            record["switch_verified"] = True

        return record

    def record_failed_attack_trick(
        self,
        state: GameState,
        attacker_id: str,
        trick: str,
        trick_data: dict[str, object] | None = None,
    ) -> bool:
        trick_key, resolved_trick_data = self._build_trick_key(trick)
        effective_trick_data = trick_data if trick_data is not None else resolved_trick_data

        if self.config.no_repetition and trick_key in state.failed_attack_turn_trick_keys:
            return False

        record: dict[str, object] = {
            "attacker_id": attacker_id,
            "trick": trick,
            "trick_key": trick_key,
        }
        if effective_trick_data is not None:
            record["trick_label"] = effective_trick_data["label"]
            record["trick_data"] = effective_trick_data

        state.failed_attack_trick_data.append(record)
        if self.config.no_repetition:
            state.failed_attack_turn_trick_keys.append(trick_key)
        return True

    def can_change_attack_trick(
        self,
        state: GameState,
        *,
        attack_attempts: int,
    ) -> bool:
        return (
            self.config.multiple_attack_enabled
            and state.current_trick is not None
            and state.attack_attempts_left > 0
            and state.attack_attempts_left < attack_attempts
        )

    def repetition_blocks_trick(
        self,
        state: GameState,
        trick: str,
        attacker_id: str,
    ) -> bool:
        if self.config.repetition_mode == "disabled":
            return False

        trick_key, _ = self._build_trick_key(trick)
        if self.config.no_repetition and trick_key in state.failed_attack_turn_trick_keys:
            return False

        failed_attempts = [
            record
            for record in state.failed_attack_trick_data
            if record.get("trick_key") == trick_key
        ]

        if self.config.repetition_mode == "choice":
            failed_attempts = [
                record
                for record in failed_attempts
                if record.get("attacker_id") == attacker_id
            ]

        return len(failed_attempts) >= self.config.repetition_limit

    def current_attack_trick_requires_change(
        self,
        state: GameState,
        *,
        attacker_id: str,
        attack_attempts: int,
    ) -> bool:
        if state.current_trick is None:
            return False
        if not self.can_change_attack_trick(state, attack_attempts=attack_attempts):
            return False
        return self.repetition_blocks_trick(state, state.current_trick, attacker_id)

    def repetition_block_message(self) -> str:
        if self.config.repetition_mode == "common":
            return "This trick has reached the shared repetition limit for this game."
        return "This trick has reached the repetition limit for the current attacker."
