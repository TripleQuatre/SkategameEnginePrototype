from dataclasses import dataclass


@dataclass(frozen=True)
class FineRulesConfig:
    uniqueness_enabled: bool = True
    repetition_mode: str = "choice"
    repetition_limit: int = 3
    multiple_attack_enabled: bool = False
    no_repetition: bool = False
    switch_mode: str = "disabled"

    def __post_init__(self) -> None:
        if self.repetition_mode not in {"choice", "common", "disabled"}:
            raise ValueError(
                "repetition_mode must be one of: choice, common, disabled"
            )

        if self.repetition_limit <= 0:
            raise ValueError("repetition_limit must be greater than 0")

        if not isinstance(self.multiple_attack_enabled, bool):
            raise ValueError("multiple_attack_enabled must be a boolean")

        if not isinstance(self.no_repetition, bool):
            raise ValueError("no_repetition must be a boolean")

        if self.switch_mode not in {"disabled", "enabled", "normal", "verified"}:
            raise ValueError(
                "switch_mode must be one of: disabled, enabled, normal, verified"
            )
