from config.fine_rules_config import FineRulesConfig
from core.player import Player
from core.state import GameState
from dictionary.runtime import resolve_runtime_trick_record


class TrickRules:
    def __init__(self, config: FineRulesConfig | None = None) -> None:
        self.config = config if config is not None else FineRulesConfig()

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

    def record_failed_attack_trick(
        self,
        state: GameState,
        attacker_id: str,
        trick: str,
        trick_data: dict[str, object] | None = None,
    ) -> None:
        trick_key, resolved_trick_data = self._build_trick_key(trick)
        effective_trick_data = trick_data if trick_data is not None else resolved_trick_data

        record: dict[str, object] = {
            "attacker_id": attacker_id,
            "trick": trick,
            "trick_key": trick_key,
        }
        if effective_trick_data is not None:
            record["trick_label"] = effective_trick_data["label"]
            record["trick_data"] = effective_trick_data

        state.failed_attack_trick_data.append(record)

    def repetition_blocks_trick(
        self,
        state: GameState,
        trick: str,
        attacker_id: str,
    ) -> bool:
        if self.config.repetition_mode == "disabled":
            return False

        trick_key, _ = self._build_trick_key(trick)
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

    def repetition_block_message(self) -> str:
        if self.config.repetition_mode == "common":
            return "This trick has reached the shared repetition limit for this game."
        return "This trick has reached the repetition limit for the current attacker."
