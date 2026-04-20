from dataclasses import dataclass


@dataclass(frozen=True)
class FineRulesConfig:
    uniqueness_enabled: bool = True
