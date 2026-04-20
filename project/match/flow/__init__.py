"""Turn flow helpers for the V7 match runtime."""

__all__ = ["ExchangeOutcome", "TurnCycle", "TurnFlow"]


def __getattr__(name: str):
    if name == "ExchangeOutcome":
        from match.flow.exchange_outcome import ExchangeOutcome

        return ExchangeOutcome
    if name == "TurnCycle":
        from match.flow.turn_cycle import TurnCycle

        return TurnCycle
    if name == "TurnFlow":
        from match.flow.turn_flow import TurnFlow

        return TurnFlow
    raise AttributeError(name)
