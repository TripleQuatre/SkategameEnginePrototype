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

    def resolve_player_identity_input(
        self,
        raw_value: str,
        *,
        prefer_profile_identity: bool = True,
    ) -> tuple[str, str]:
        normalized = raw_value.strip()
        if not normalized:
            raise ValueError("Player identity input cannot be empty.")

        if not prefer_profile_identity:
            return normalized, normalized

        for profile in self.list_local_profiles():
            if profile.profile_id.casefold() == normalized.casefold():
                return profile.profile_id, profile.display_name
            if profile.display_name.casefold() == normalized.casefold():
                return profile.profile_id, profile.display_name

        return normalized, normalized

    def build_profile_player_slots(
        self,
        profile_ids: list[str],
    ) -> tuple[list[str], list[str | None], list[str]]:
        display_names = self.resolve_local_profile_names(profile_ids)
        return list(profile_ids), list(profile_ids), display_names

    def resolve_player_display_names(
        self,
        *,
        player_ids: list[str],
        player_display_names: list[str] | None = None,
    ) -> list[str]:
        resolved_names = list(player_display_names or player_ids)
        if len(resolved_names) != len(player_ids):
            raise ValueError(
                "player_display_names must match the number of configured players."
            )
        return resolved_names

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
        player_profile_ids: list[str | None] | None = None,
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
            player_id_by_profile_id = self._build_player_id_by_profile_id(
                player_ids,
                player_profile_ids or [],
            )
            sorted_profile_ids = self._sort_profile_ids_by_relevance(
                self._require_profile_ids_for_relevance(player_profile_ids or []),
                criterion,
            )
            ordered_player_ids = [
                player_id_by_profile_id[profile_id] for profile_id in sorted_profile_ids
            ]
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
        player_profile_ids: list[str | None] | None = None,
        player_display_names: list[str] | None = None,
        relevance_criterion: str | None = None,
        explicit_player_order: list[str] | None = None,
    ) -> list[str]:
        normalized_mode = order_mode.strip().lower()
        player_name_by_id = self._build_player_name_by_id(
            player_ids,
            player_display_names,
        )

        if normalized_mode == "random":
            return []

        if normalized_mode == "choice":
            ordered_player_ids = list(explicit_player_order or player_ids)
            return [player_name_by_id[player_id] for player_id in ordered_player_ids]

        if normalized_mode == "relevance":
            if relevance_criterion is None:
                raise ValueError("relevance_criterion is required for Order=Relevance.")
            criterion = RelevanceCriterion(relevance_criterion)
            player_id_by_profile_id = self._build_player_id_by_profile_id(
                player_ids,
                player_profile_ids or [],
            )
            sorted_profile_ids = self._sort_profile_ids_by_relevance(
                self._require_profile_ids_for_relevance(player_profile_ids or []),
                criterion,
            )
            return [
                player_name_by_id[player_id_by_profile_id[profile_id]]
                for profile_id in sorted_profile_ids
            ]

        raise ValueError(f"Unknown order mode: {order_mode}")

    def build_order_preview_text(
        self,
        *,
        order_mode: str,
        preview_names: list[str],
    ) -> str:
        if order_mode == "random":
            return "Order preview: randomized at game start."
        return f"Order preview: {' -> '.join(preview_names)}"

    def describe_order_mode_from_policies(self, policies: MatchPolicies) -> str:
        if policies.initial_turn_order == InitialTurnOrderPolicy.RANDOMIZED:
            return "random"
        if policies.initial_turn_order == InitialTurnOrderPolicy.RELEVANCE:
            return "relevance"
        return "choice"

    def format_multiple_attack_label(
        self,
        *,
        multiple_attack_enabled: bool,
        no_repetition: bool,
        attack_attempts: int,
    ) -> str:
        if multiple_attack_enabled and no_repetition:
            return "enabled + no repetition"
        if multiple_attack_enabled:
            return "enabled"
        if no_repetition:
            return "no repetition"
        return "disabled"

    def format_repetition_label(
        self,
        repetition_mode: str,
        repetition_limit: int,
    ) -> str:
        if repetition_mode == "disabled":
            return "disabled"
        return f"{repetition_mode} (limit {repetition_limit})"

    def build_setup_summary_text(
        self,
        *,
        mode_label: str,
        sport: str,
        player_names: list[str],
        order_mode: str,
        attack_attempts: int,
        defense_attempts: int,
        multiple_attack_enabled: bool,
        no_repetition: bool,
        switch_mode: str,
        repetition_mode: str,
        repetition_limit: int,
    ) -> str:
        multiple_attack_label = self.format_multiple_attack_label(
            multiple_attack_enabled=multiple_attack_enabled,
            no_repetition=no_repetition,
            attack_attempts=attack_attempts,
        )
        repetition_label = self.format_repetition_label(
            repetition_mode,
            repetition_limit,
        )
        return (
            "Setup summary: "
            f"{mode_label} | sport={sport} | players={', '.join(player_names)} | "
            f"order={order_mode} | attack={attack_attempts} | defense={defense_attempts} | "
            f"multiple attack={multiple_attack_label} | switch={switch_mode} | "
            f"repetition={repetition_label}"
        )

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

    def _build_player_name_by_id(
        self,
        player_ids: list[str],
        player_display_names: list[str] | None = None,
    ) -> dict[str, str]:
        display_names = self.resolve_player_display_names(
            player_ids=player_ids,
            player_display_names=player_display_names,
        )
        return dict(zip(player_ids, display_names, strict=True))

    def _build_player_id_by_profile_id(
        self,
        player_ids: list[str],
        player_profile_ids: list[str | None],
    ) -> dict[str, str]:
        if len(player_profile_ids) != len(player_ids):
            raise ValueError(
                "player_profile_ids must match the number of configured players."
            )
        mapping: dict[str, str] = {}
        for player_id, profile_id in zip(player_ids, player_profile_ids, strict=True):
            if profile_id is None:
                continue
            mapping[profile_id] = player_id
        return mapping

    def _require_profile_ids_for_relevance(
        self,
        player_profile_ids: list[str | None],
    ) -> list[str]:
        if not player_profile_ids or any(profile_id is None for profile_id in player_profile_ids):
            raise ValueError("Profile-backed players are required for Order=Relevance.")
        return [profile_id for profile_id in player_profile_ids if profile_id is not None]

    def create_preset_setup(
        self,
        preset_name: str,
        player_ids: list[str],
        player_profile_ids: list[str | None] | None = None,
        player_display_names: list[str] | None = None,
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
        setup.player_display_names = self.resolve_player_display_names(
            player_ids=player_ids,
            player_display_names=player_display_names,
        )
        return setup

    def create_custom_setup(
        self,
        player_ids: list[str],
        letters_word: str,
        attack_attempts: int,
        defense_attempts: int,
        player_display_names: list[str] | None = None,
        sport: str = "inline",
        policies: MatchPolicies | None = None,
        elimination_enabled: bool = True,
        uniqueness_enabled: bool = True,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
        switch_mode: str = "disabled",
        repetition_mode: str = "choice",
        repetition_limit: int = 3,
        player_profile_ids: list[str | None] | None = None,
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
            player_display_names=self.resolve_player_display_names(
                player_ids=player_ids,
                player_display_names=player_display_names,
            ),
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
        player_profile_ids: list[str | None] | None = None,
        player_display_names: list[str] | None = None,
    ) -> GameController:
        setup = self.create_preset_setup(
            preset_name,
            player_ids,
            player_profile_ids=player_profile_ids,
            player_display_names=player_display_names,
        )
        return self.create_started_controller_from_setup(setup)

    def create_started_controller_from_custom_setup(
        self,
        player_ids: list[str],
        letters_word: str,
        attack_attempts: int,
        defense_attempts: int,
        player_display_names: list[str] | None = None,
        sport: str = "inline",
        policies: MatchPolicies | None = None,
        elimination_enabled: bool = True,
        uniqueness_enabled: bool = True,
        multiple_attack_enabled: bool = False,
        no_repetition: bool = False,
        switch_mode: str = "disabled",
        repetition_mode: str = "choice",
        repetition_limit: int = 3,
        player_profile_ids: list[str | None] | None = None,
    ) -> GameController:
        setup = self.create_custom_setup(
            player_ids=player_ids,
            player_profile_ids=player_profile_ids,
            player_display_names=player_display_names,
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
            player_display_names=["Player 1", "Player 2"],
            structure_name="one_vs_one",
            sport="inline",
        )
        return GameController(self.setup_translator.to_match_config(placeholder_setup))

    def create_started_controller_from_preset_profiles(
        self,
        preset_name: str,
        player_profile_ids: list[str],
    ) -> GameController:
        player_ids, resolved_profile_ids, player_display_names = (
            self.build_profile_player_slots(player_profile_ids)
        )
        return self.create_started_controller_from_preset(
            preset_name,
            player_ids,
            player_profile_ids=resolved_profile_ids,
            player_display_names=player_display_names,
        )

    def create_started_controller_from_custom_setup_profiles(
        self,
        player_profile_ids: list[str],
        letters_word: str,
        attack_attempts: int,
        defense_attempts: int,
        player_display_names: list[str] | None = None,
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
        player_ids, resolved_profile_ids, resolved_display_names = (
            self.build_profile_player_slots(player_profile_ids)
        )
        return self.create_started_controller_from_custom_setup(
            player_ids=player_ids,
            player_profile_ids=resolved_profile_ids,
            player_display_names=(
                player_display_names
                if player_display_names is not None
                else resolved_display_names
            ),
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
