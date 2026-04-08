from dataclasses import dataclass, field
import uuid

@dataclass
class Player:
    id: str  # ID métier (compte utilisateur)
    name: str
    internal_id: str = field(default_factory=lambda: str(uuid.uuid4())) # ID moteur
    score: int = 0
    is_active: bool = True

    @property
    def is_eliminated(self) -> bool:
        return not self.is_active