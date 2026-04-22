from dataclasses import dataclass

from dictionary.types import TrickType


def _normalize_identifier(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", " ").split())


@dataclass(frozen=True)
class TrickSegment:
    trick_type: TrickType
    base_name: str
    variation: str | None = None
    grab: bool = False
    switch: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.trick_type, TrickType):
            raise ValueError(f"Unsupported trick_type: {self.trick_type}")

        if not self.base_name.strip():
            raise ValueError("base_name is required")

    @property
    def label(self) -> str:
        parts: list[str] = []
        if self.variation:
            parts.append(self.variation.strip())
        if self.trick_type == TrickType.NEGATIVE:
            parts.append("Negative")
        parts.append(self.base_name.strip())
        if self.grab:
            parts.append("Grab")
        if self.switch:
            parts.append("Switch")
        return " ".join(parts)

    @property
    def canonical_key(self) -> str:
        variation_key = (
            _normalize_identifier(self.variation)
            if self.variation is not None
            else "none"
        )
        return (
            f"type={self.trick_type.value};"
            f"variation={variation_key};"
            f"base={_normalize_identifier(self.base_name)};"
            f"grab={int(self.grab)};"
            f"switch={int(self.switch)}"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "trick_type": self.trick_type.value,
            "base_name": self.base_name,
            "variation": self.variation,
            "grab": self.grab,
            "switch": self.switch,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "TrickSegment":
        return cls(
            trick_type=TrickType(str(data["trick_type"])),
            base_name=str(data["base_name"]),
            variation=(
                str(data["variation"]) if data.get("variation") is not None else None
            ),
            grab=bool(data.get("grab", False)),
            switch=bool(data.get("switch", False)),
        )


@dataclass(frozen=True)
class TrickExit:
    degrees: int
    reverse: bool = False

    def __post_init__(self) -> None:
        if self.degrees not in {180, 360, 540}:
            raise ValueError("Exit degrees must be one of 180, 360, or 540")

    @property
    def label(self) -> str:
        if self.reverse:
            return f"Reverse {self.degrees}"
        return str(self.degrees)

    @property
    def canonical_key(self) -> str:
        if self.reverse:
            return f"reverse_{self.degrees}"
        return str(self.degrees)

    def to_dict(self) -> dict[str, object]:
        return {
            "degrees": self.degrees,
            "reverse": self.reverse,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "TrickExit":
        return cls(
            degrees=int(data["degrees"]),
            reverse=bool(data.get("reverse", False)),
        )


@dataclass(frozen=True)
class ConstructedTrick:
    segments: tuple[TrickSegment, ...]
    trick_exit: TrickExit | None = None

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("A trick requires at least one segment")

        if len(self.segments) > 3:
            raise ValueError("A trick can contain at most three segments")

        if len(self.segments) > 1 and any(segment.switch for segment in self.segments):
            raise ValueError("Explicit switch is not allowed on combo segments in V8")

    @property
    def is_combo(self) -> bool:
        return len(self.segments) > 1

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def label(self) -> str:
        label = " to ".join(segment.label for segment in self.segments)
        if self.trick_exit is not None:
            return f"{label} {self.trick_exit.label}"
        return label

    @property
    def canonical_key(self) -> str:
        segments_key = "|".join(segment.canonical_key for segment in self.segments)
        exit_key = (
            self.trick_exit.canonical_key if self.trick_exit is not None else "none"
        )
        return f"segments={segments_key};exit={exit_key}"

    def to_dict(self) -> dict[str, object]:
        return {
            "segments": [segment.to_dict() for segment in self.segments],
            "trick_exit": self.trick_exit.to_dict() if self.trick_exit else None,
            "label": self.label,
            "canonical_key": self.canonical_key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ConstructedTrick":
        return cls(
            segments=tuple(
                TrickSegment.from_dict(segment_data)
                for segment_data in list(data["segments"])
            ),
            trick_exit=(
                TrickExit.from_dict(data["trick_exit"])
                if data.get("trick_exit") is not None
                else None
            ),
        )
