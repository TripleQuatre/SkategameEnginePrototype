from config.match_setup import MatchSetup
from config.match_policies import (
    InitialTurnOrderPolicy,
    MatchPolicies,
    RelevanceCriterion,
)
from config.preset_registry import PresetRegistry
from config.rule_interactions import (
    is_attack_repetition_synergy_active,
    is_attack_repetition_synergy_compatible,
    suggest_attack_repetition_limits,
)
from config.setup_translator import SetupTranslator
from controllers.game_controller import GameController
from application.player_profile_service import PlayerProfileService


class GameSetupService:
    def __init__(
        self,
        preset_registry: PresetRegistry | None = None,
        setup_translator: SetupTranslator | None = None,
        player_profile_service: PlayerProfileService | None = None,
    ) -> None:
        self.preset_registry = (
            preset_registry if preset_registry is not None else PresetRegistry()
        )
        self.setup_translator = (
            setup_translator if setup_translator is not None else SetupTranslator()
        )
        self.player_profile_service = (
            player_profile_service
            if player_profile_service is not None
            else PlayerProfileService()
        )

    def list_preset_names(self) -> list[str]:
        return self.preset_registry.list_preset_names()

    def get_preset(self, preset_name: str):
        return self.preset_registry.get(preset_name)

    def list_local_profiles(self):
        return self.player_profile_service.list_profiles()

    def list_local_profile_ids(self) -> list[str]:
        return self.player_profile_service.list_profile_ids()

    def get_local_profile(self, profile_id: str):
        return self.player_profile_service.get_profile(profile_id)

    def resolve_local_profile_names(self, profile_ids: list[str]) -> list[str]:
        return [
            self.player_profile_service.get_profile(profile_id).display_name
            for profile_id in profile_ids
        ]

    def is_attack_repetition_synergy_active(
        self,
        *,
        attack_attempts: int,
        repetition_mode: str,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
    ) -> bool:
        return is_attack_repetition_synergy_active(
            attack_attempts,
            repetition_mode,
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
        )

    def is_attack_repetition_synergy_compatible(
        self,
        *,
        attack_attempts: int,
        repetition_mode: str,
        repetition_limit: int,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
    ) -> bool:
        return is_attack_repetition_synergy_compatible(
            attack_attempts,
            repetition_mode,
            repetition_limit,
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
        )

    def suggest_attack_repetition_limits(
        self,
        *,
        attack_attempts: int,
        repetition_mode: str,
        repetition_limit: int | None = None,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
        max_limit: int | None = None,
        count: int = 3,
    ) -> tuple[int, ...]:
        return suggest_attack_repetition_limits(
            attack_attempts,
            repetition_mode,
            repetition_limit,
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
            max_limit=max_limit,
            count=count,
        )

    def get_attack_repetition_synergy_feedback(
        self,
        *,
        attack_attempts: int,
        repetition_mode: str,
        repetition_limit: int,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
        max_limit: int | None = None,
    ) -> str | None:
        if not self.is_attack_repetition_synergy_active(
            attack_attempts=attack_attempts,
            repetition_mode=repetition_mode,
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
        ):
            return None

        if self.is_attack_repetition_synergy_compatible(
            attack_attempts=attack_attempts,
            repetition_mode=repetition_mode,
            repetition_limit=repetition_limit,
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
        ):
            return (
                "Attack/Repetition synergy active: repetition limit aligns with full "
                "attack turns."
            )

        suggestions = self.suggest_attack_repetition_limits(
            attack_attempts=attack_attempts,
            repetition_mode=repetition_mode,
            repetition_limit=repetition_limit,
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
            max_limit=max_limit,
        )
        suggestions_label = ", ".join(str(value) for value in suggestions)
        return (
            "Attack/Repetition synergy active: repetition limit must be a "
            f"multiple of Attack. Suggested values: {suggestions_label}."
        )

    def build_order_policies(
        self,
        *,
        order_mode: str,
        player_ids: list[str],
        player_profile_ids: list[str] | None = None,
        relevance_criterion: str | None = None,
        explicit_player_order: list[str] | None = None,
    ) -> MatchPolicies:
        normalized_mode = order_mode.strip().lower()

        if normalized_mode == "random":
            return MatchPolicies(
                initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
            )

        if normalized_mode == "choice":
            ordered_player_ids = list(explicit_player_order or player_ids)
            return MatchPolicies(
                initial_turn_order=InitialTurnOrderPolicy.EXPLICIT_CHOICE,
                explicit_player_order=tuple(ordered_player_ids),
            )

        if normalized_mode == "relevance":
            if relevance_criterion is None:
                raise ValueError("relevance_criterion is required for Order=Relevance.")
            criterion = RelevanceCriterion(relevance_criterion)
            sorted_profile_ids = self._sort_profile_ids_by_relevance(
                player_profile_ids or [],
                criterion,
            )
            ordered_player_ids = self.resolve_local_profile_names(sorted_profile_ids)
            return MatchPolicies(
                initial_turn_order=InitialTurnOrderPolicy.RELEVANCE,
                relevance_criterion=criterion,
                explicit_player_order=tuple(ordered_player_ids),
            )

        raise ValueError(f"Unknown order mode: {order_mode}")

    def preview_order(
        self,
        *,
        order_mode: str,
        player_ids: list[str],
        player_profile_ids: list[str] | None = None,
        relevance_criterion: str | None = None,
        explicit_player_order: list[str] | None = None,
    ) -> list[str]:
        normalized_mode = order_mode.strip().lower()

        if normalized_mode == "random":
            return []

        if normalized_mode == "choice":
            return list(explicit_player_order or player_ids)

        if normalized_mode == "relevance":
            if relevance_criterion is None:
                raise ValueError("relevance_criterion is required for Order=Relevance.")
            criterion = RelevanceCriterion(relevance_criterion)
            sorted_profile_ids = self._sort_profile_ids_by_relevance(
                player_profile_ids or [],
                criterion,
            )
            return self.resolve_local_profile_names(sorted_profile_ids)

        raise ValueError(f"Unknown order mode: {order_mode}")

    def _sort_profile_ids_by_relevance(
        self,
        profile_ids: list[str],
        criterion: RelevanceCriterion,
    ) -> list[str]:
        profiles = [
            self.player_profile_service.get_profile(profile_id)
            for profile_id in profile_ids
        ]

        if criterion == RelevanceCriterion.ALPHABETICAL:
            key = lambda profile: (profile.display_name.casefold(), profile.profile_id)
        elif criterion == RelevanceCriterion.AGE:
            key = lambda profile: (profile.age, profile.display_name.casefold())
        elif criterion == RelevanceCriterion.EXPERIENCE_TIME:
            key = lambda profile: (
                profile.experience_time,
                profile.display_name.casefold(),
            )
        else:
            key = lambda profile: (profile.local_rank, profile.display_name.casefold())

        return [profile.profile_id for profile in sorted(profiles, key=key)]

    def create_preset_setup(
        self,
        preset_name: str,
        player_ids: list[str],
        player_profile_ids: list[str] | None = None,
    ) -> MatchSetup:
        if (
            player_profile_ids is not None
            and len(player_profile_ids) != len(player_ids)
        ):
            raise ValueError(
                "player_profile_ids must match the number of configured players."
            )
        setup = self.preset_registry.create_match_setup(preset_name, player_ids)
        setup.player_profile_ids = list(player_profile_ids or [])
        return setup

    def create_custom_setup(
        self,
        player_ids: list[str],
        letters_word: str,
        attack_attempts: int,
        defense_attempts: int,
        sport: str = "inline",
        policies: MatchPolicies | None = None,
        elimination_enabled: bool = True,
        uniqueness_enabled: bool = True,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
        switch_mode: str = "disabled",
        repetition_mode: str = "choice",
        repetition_limit: int = 3,
        player_profile_ids: list[str] | None = None,
    ) -> MatchSetup:
        if (
            player_profile_ids is not None
            and len(player_profile_ids) != len(player_ids)
        ):
            raise ValueError(
                "player_profile_ids must match the number of configured players."
            )
        return MatchSetup(
            player_ids=list(player_ids),
            player_profile_ids=list(player_profile_ids or []),
            structure_name="one_vs_one" if len(player_ids) == 2 else "battle",
            sport=sport,
            policies=policies,
            letters_word=letters_word.strip().upper(),
            attack_attempts=attack_attempts,
            defense_attempts=defense_attempts,
            elimination_enabled=elimination_enabled,
            uniqueness_enabled=uniqueness_enabled,
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
            switch_mode=switch_mode,
            repetition_mode=repetition_mode,
            repetition_limit=repetition_limit,
        )

    def create_started_controller_from_preset(
        self,
        preset_name: str,
        player_ids: list[str],
        player_profile_ids: list[str] | None = None,
    ) -> GameController:
        setup = self.create_preset_setup(
            preset_name,
            player_ids,
            player_profile_ids=player_profile_ids,
        )
        return self.create_started_controller_from_setup(setup)

    def create_started_controller_from_custom_setup(
        self,
        player_ids: list[str],
        letters_word: str,
        attack_attempts: int,
        defense_attempts: int,
        sport: str = "inline",
        policies: MatchPolicies | None = None,
        elimination_enabled: bool = True,
        uniqueness_enabled: bool = True,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
        switch_mode: str = "disabled",
        repetition_mode: str = "choice",
        repetition_limit: int = 3,
        player_profile_ids: list[str] | None = None,
    ) -> GameController:
        setup = self.create_custom_setup(
            player_ids=player_ids,
            player_profile_ids=player_profile_ids,
            letters_word=letters_word,
            attack_attempts=attack_attempts,
            defense_attempts=defense_attempts,
            sport=sport,
            policies=policies,
            elimination_enabled=elimination_enabled,
            uniqueness_enabled=uniqueness_enabled,
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
            switch_mode=switch_mode,
            repetition_mode=repetition_mode,
            repetition_limit=repetition_limit,
        )
        return self.create_started_controller_from_setup(setup)

    def create_started_controller_from_setup(self, setup: MatchSetup) -> GameController:
        controller = GameController(self.setup_translator.to_match_config(setup))
        controller.start_game()
        return controller

    def create_loading_controller(self) -> GameController:
        placeholder_setup = MatchSetup(
            player_ids=["Player 1", "Player 2"],
            player_profile_ids=[],
            structure_name="one_vs_one",
            sport="inline",
        )
        return GameController(self.setup_translator.to_match_config(placeholder_setup))

    def create_started_controller_from_preset_profiles(
        self,
        preset_name: str,
        player_profile_ids: list[str],
    ) -> GameController:
        player_ids = self.resolve_local_profile_names(player_profile_ids)
        return self.create_started_controller_from_preset(
            preset_name,
            player_ids,
            player_profile_ids=player_profile_ids,
        )

    def create_started_controller_from_custom_setup_profiles(
        self,
        player_profile_ids: list[str],
        letters_word: str,
        attack_attempts: int,
        defense_attempts: int,
        sport: str = "inline",
        policies: MatchPolicies | None = None,
        elimination_enabled: bool = True,
        uniqueness_enabled: bool = True,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
        switch_mode: str = "disabled",
        repetition_mode: str = "choice",
        repetition_limit: int = 3,
    ) -> GameController:
        player_ids = self.resolve_local_profile_names(player_profile_ids)
        return self.create_started_controller_from_custom_setup(
            player_ids=player_ids,
            player_profile_ids=player_profile_ids,
            letters_word=letters_word,
            attack_attempts=attack_attempts,
            defense_attempts=defense_attempts,
            sport=sport,
            policies=policies,
            elimination_enabled=elimination_enabled,
            uniqueness_enabled=uniqueness_enabled,
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
            switch_mode=switch_mode,
            repetition_mode=repetition_mode,
            repetition_limit=repetition_limit,
        )

    def load_controller(self, filepath: str) -> GameController:
        controller = self.create_loading_controller()
        controller.load_game(filepath)
        return controller
