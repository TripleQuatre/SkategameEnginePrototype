from dataclasses import dataclass


@dataclass(frozen=True)
class FineRulesConfig:
    uniqueness_enabled: bool = True
    repetition_mode: str = "choice"
    repetition_limit: int = 3

    def __post_init__(self) -> None:
        if self.repetition_mode not in {"choice", "common", "disabled"}:
            raise ValueError(
                "repetition_mode must be one of: choice, common, disabled"
            )

        if self.repetition_limit <= 0:
            raise ValueError("repetition_limit must be greater than 0")
