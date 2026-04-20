from dataclasses import dataclass, field
import uuid

from core.player_score import PlayerScoreState


@dataclass(init=False)
class Player:
    id: str  # ID metier (compte utilisateur)
    name: str
    internal_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # ID moteur
    score_state: PlayerScoreState = field(default_factory=PlayerScoreState)
    is_active: bool = True

    def __init__(
        self,
        id: str,
        name: str,
        internal_id: str | None = None,
        score: int = 0,
        points: int = 0,
        score_state: PlayerScoreState | None = None,
        is_active: bool = True,
    ) -> None:
        self.id = id
        self.name = name
        self.internal_id = internal_id or str(uuid.uuid4())
        self.score_state = (
            score_state
            if score_state is not None
            else PlayerScoreState(letters=score, points=points)
        )
        self.is_active = is_active

    @property
    def score(self) -> int:
        return self.score_state.letters

    @score.setter
    def score(self, value: int) -> None:
        self.score_state.letters = value

    @property
    def points(self) -> int:
        return self.score_state.points

    @points.setter
    def points(self, value: int) -> None:
        self.score_state.points = value

    @property
    def is_eliminated(self) -> bool:
        return not self.is_active
