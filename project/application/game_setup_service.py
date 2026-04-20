from config.match_setup import MatchSetup
from config.preset_registry import PresetRegistry
from config.setup_translator import SetupTranslator
from controllers.game_controller import GameController


class GameSetupService:
    def __init__(
        self,
        preset_registry: PresetRegistry | None = None,
        setup_translator: SetupTranslator | None = None,
    ) -> None:
        self.preset_registry = (
            preset_registry if preset_registry is not None else PresetRegistry()
        )
        self.setup_translator = (
            setup_translator if setup_translator is not None else SetupTranslator()
        )

    def list_preset_names(self) -> list[str]:
        return self.preset_registry.list_preset_names()

    def get_preset(self, preset_name: str):
        return self.preset_registry.get(preset_name)

    def create_preset_setup(
        self,
        preset_name: str,
        player_ids: list[str],
    ) -> MatchSetup:
        return self.preset_registry.create_match_setup(preset_name, player_ids)

    def create_custom_setup(
        self,
        player_ids: list[str],
        letters_word: str,
        attack_attempts: int,
        defense_attempts: int,
        elimination_enabled: bool = True,
    ) -> MatchSetup:
        return MatchSetup(
            player_ids=list(player_ids),
            structure_name="one_vs_one" if len(player_ids) == 2 else "battle",
            letters_word=letters_word.strip().upper(),
            attack_attempts=attack_attempts,
            defense_attempts=defense_attempts,
            elimination_enabled=elimination_enabled,
        )

    def create_started_controller_from_preset(
        self,
        preset_name: str,
        player_ids: list[str],
    ) -> GameController:
        setup = self.create_preset_setup(preset_name, player_ids)
        return self.create_started_controller_from_setup(setup)

    def create_started_controller_from_custom_setup(
        self,
        player_ids: list[str],
        letters_word: str,
        attack_attempts: int,
        defense_attempts: int,
        elimination_enabled: bool = True,
    ) -> GameController:
        setup = self.create_custom_setup(
            player_ids=player_ids,
            letters_word=letters_word,
            attack_attempts=attack_attempts,
            defense_attempts=defense_attempts,
            elimination_enabled=elimination_enabled,
        )
        return self.create_started_controller_from_setup(setup)

    def create_started_controller_from_setup(self, setup: MatchSetup) -> GameController:
        controller = GameController(self.setup_translator.to_match_config(setup))
        controller.start_game()
        return controller

    def create_loading_controller(self) -> GameController:
        placeholder_setup = MatchSetup(
            player_ids=["Player 1", "Player 2"],
            structure_name="one_vs_one",
        )
        return GameController(self.setup_translator.to_match_config(placeholder_setup))

    def load_controller(self, filepath: str) -> GameController:
        controller = self.create_loading_controller()
        controller.load_game(filepath)
        return controller
