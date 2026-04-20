from dataclasses import dataclass

from core.types import ExchangeStatus


@dataclass(frozen=True)
class ExchangeOutcome:
    status: ExchangeStatus
    exchange_complete: bool = False
    game_complete: bool = False

    @classmethod
    def attack_continues(cls) -> "ExchangeOutcome":
        return cls(status=ExchangeStatus.ATTACK_CONTINUES)

    @classmethod
    def defense_ready(cls) -> "ExchangeOutcome":
        return cls(status=ExchangeStatus.DEFENSE_READY)

    @classmethod
    def defense_continues(cls) -> "ExchangeOutcome":
        return cls(status=ExchangeStatus.DEFENSE_CONTINUES)

    @classmethod
    def attacker_failed(cls) -> "ExchangeOutcome":
        return cls(status=ExchangeStatus.ATTACKER_FAILED, exchange_complete=True)

    @classmethod
    def attacker_held(cls) -> "ExchangeOutcome":
        return cls(status=ExchangeStatus.ATTACKER_HELD, exchange_complete=True)

    @classmethod
    def game_finished(cls) -> "ExchangeOutcome":
        return cls(
            status=ExchangeStatus.GAME_FINISHED,
            exchange_complete=True,
            game_complete=True,
        )
