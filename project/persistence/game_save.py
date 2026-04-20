from dataclasses import dataclass

from config.match_config import MatchConfig
from config.match_parameters import MatchParameters
from config.setup_translator import SetupTranslator
from core.state import GameState


@dataclass(init=False)
class GameSave:
    match_config: MatchConfig
    game_state: GameState

    def __init__(
        self,
        match_config: MatchConfig | None = None,
        game_state: GameState | None = None,
        match_parameters: MatchParameters | None = None,
    ) -> None:
        translator = SetupTranslator()

        if match_config is None:
            if match_parameters is None:
                raise ValueError("GameSave requires match_config or match_parameters.")
            match_config = translator.from_match_parameters(match_parameters)

        if game_state is None:
            raise ValueError("GameSave requires a game_state.")

        self.match_config = match_config
        self.game_state = game_state

    @property
    def match_parameters(self) -> MatchParameters:
        return SetupTranslator().from_match_config(self.match_config)
