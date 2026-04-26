import pytest

from config.attack_config import AttackConfig
from config.defense_config import DefenseConfig
from config.fine_rules_config import FineRulesConfig
from config.match_config import MatchConfig
from config.scoring_config import ScoringConfig
from config.victory_config import VictoryConfig
from core.exceptions import InvalidActionError
from core.player import Player
from core.state import GameState
from core.types import (
    AttackResolutionStatus,
    DefenseResolutionStatus,
    EventName,
    Phase,
    TurnPhase,
)
from match.flow.turn_flow import TurnFlow as GameFlow
from match.structure.one_vs_one_structure import OneVsOneStructure


def build_game_flow(
    attack_attempts: int = 1,
    defense_attempts: int = 1,
    letters_word: str = "SKATE",
    elimination_enabled: bool = True,
    uniqueness_enabled: bool = True,
    multiple_attack_enabled: bool = False,
    no_repetition: bool = False,
    switch_mode: str = "disabled",
    repetition_mode: str = "choice",
    repetition_limit: int = 3,
) -> GameFlow:
    return GameFlow(
        OneVsOneStructure(),
        MatchConfig(
            attack=AttackConfig(attack_attempts=attack_attempts),
            defense=DefenseConfig(defense_attempts=defense_attempts),
            scoring=ScoringConfig(letters_word=letters_word),
            victory=VictoryConfig(elimination_enabled=elimination_enabled),
            fine_rules=FineRulesConfig(
                uniqueness_enabled=uniqueness_enabled,
                multiple_attack_enabled=multiple_attack_enabled,
                no_repetition=no_repetition,
                switch_mode=switch_mode,
                repetition_mode=repetition_mode,
                repetition_limit=repetition_limit,
            ),
        ),
    )


@pytest.fixture
def game_flow() -> GameFlow:
    return build_game_flow()


@pytest.fixture
def state() -> GameState:
    players = [
        Player(id="p1", name="Player 1"),
        Player(id="p2", name="Player 2"),
    ]
    return GameState(players=players)


def test_start_game_sets_turn_phase(game_flow: GameFlow, state: GameState) -> None:
    game_flow.start_game(state)

    assert state.phase == Phase.TURN
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.turn_order == [0, 1]
    assert state.attacker_index == 0
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 0
    assert state.history.events[-1].name == EventName.GAME_STARTED


def test_start_turn_sets_trick_and_defenders(
    game_flow: GameFlow, state: GameState
) -> None:
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    assert state.turn_phase == TurnPhase.DEFENSE
    assert state.attack_attempts_left == 0
    assert state.current_trick == "kickflip"
    assert state.defender_indices == [1]
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == game_flow.match_config.defense_attempts
    assert state.history.events[-1].name == EventName.TURN_STARTED


def test_start_turn_enters_attack_phase_when_multiple_attack_attempts_are_enabled(
    state: GameState
) -> None:
    game_flow = build_game_flow(attack_attempts=2)
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    assert state.turn_phase == TurnPhase.ATTACK
    assert state.current_trick == "kickflip"
    assert state.attack_attempts_left == 2
    assert state.defender_indices == []


def test_resolve_attack_can_continue_attack_phase_after_failure(
    state: GameState
) -> None:
    game_flow = build_game_flow(attack_attempts=2)
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    result = game_flow.resolve_attack(state, success=False)

    assert result == AttackResolutionStatus.ATTACK_CONTINUES
    assert state.turn_phase == TurnPhase.ATTACK
    assert state.attack_attempts_left == 1
    assert state.history.events[-1].name == EventName.ATTACK_FAILED_ATTEMPT


def test_resolve_attack_can_promote_to_defense(
    state: GameState
) -> None:
    game_flow = build_game_flow(attack_attempts=2)
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    result = game_flow.resolve_attack(state, success=True)

    assert result == AttackResolutionStatus.DEFENSE_READY
    assert state.turn_phase == TurnPhase.DEFENSE
    assert state.attack_attempts_left == 0
    assert state.defender_indices == [1]
    assert state.history.events[-1].name == EventName.ATTACK_SUCCEEDED


def test_resolve_attack_can_fail_turn_when_attempts_are_exhausted(
    state: GameState
) -> None:
    game_flow = build_game_flow(attack_attempts=2)
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")
    game_flow.resolve_attack(state, success=False)

    result = game_flow.resolve_attack(state, success=False)

    assert result == AttackResolutionStatus.TURN_FAILED
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.attacker_index == 1
    assert state.current_trick is None
    assert state.history.events[-1].name == EventName.TURN_FAILED


def test_resolve_defense_returns_defense_continues_on_failed_attempt(
    state: GameState
) -> None:
    game_flow = build_game_flow(defense_attempts=2)
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    result = game_flow.resolve_defense(state, success=False)

    assert result == DefenseResolutionStatus.DEFENSE_CONTINUES
    assert state.players[1].score == 0
    assert state.current_defender_position == 0
    assert state.defense_attempts_left == 1


def test_resolve_defense_returns_turn_finished_on_success(
    game_flow: GameFlow, state: GameState
) -> None:
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    result = game_flow.resolve_defense(state, success=True)

    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert state.attacker_index == 1
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == EventName.TURN_ENDED


def test_resolve_defense_returns_game_finished_on_final_elimination(
    state: GameState
) -> None:
    game_flow = build_game_flow(letters_word="S")
    game_flow.start_game(state)
    game_flow.start_turn(state, "kickflip")

    result = game_flow.resolve_defense(state, success=False)

    assert result == DefenseResolutionStatus.GAME_FINISHED
    assert state.phase == Phase.END
    assert state.players[1].is_active is False
    assert state.history.events[-1].name == EventName.GAME_FINISHED


def test_cancel_turn_adds_only_turn_failed_event(
    game_flow: GameFlow, state: GameState
) -> None:
    game_flow.start_game(state)

    events_before = len(state.history.events)
    game_flow.cancel_turn(state, "Soul")
    new_events = state.history.events[events_before:]

    assert len(new_events) == 1
    assert new_events[0].name == EventName.TURN_FAILED
    assert new_events[0].payload["attacker_id"] == "p1"
    assert new_events[0].payload["trick"] == "Soul"
    assert new_events[0].payload["next_attacker_id"] == "p2"
    assert state.attacker_index == 1
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.current_trick is None
    assert state.defender_indices == []


def test_cancel_turn_rejects_when_trick_is_already_engaged(
    game_flow: GameFlow, state: GameState
) -> None:
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")

    with pytest.raises(InvalidActionError):
        game_flow.cancel_turn(state, "Soul")


def test_start_turn_does_not_consume_trick_yet(
    game_flow: GameFlow, state: GameState
) -> None:
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")

    assert state.current_trick == "Soul"
    assert "soul" not in state.validated_tricks


def test_start_turn_rejects_already_consumed_trick(
    game_flow: GameFlow, state: GameState
) -> None:
    game_flow.start_game(state)
    state.validated_tricks.append("soul")

    with pytest.raises(InvalidActionError):
        game_flow.start_turn(state, "Soul")


def test_resolve_defense_consumes_trick_when_turn_finishes(
    game_flow: GameFlow, state: GameState
) -> None:
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")

    result = game_flow.resolve_defense(state, success=True)

    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert "soul" in state.validated_tricks


def test_resolve_defense_consumes_trick_when_game_finishes(
    state: GameState
) -> None:
    game_flow = build_game_flow(letters_word="S")
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")

    result = game_flow.resolve_defense(state, success=False)

    assert result == DefenseResolutionStatus.GAME_FINISHED
    assert "soul" in state.validated_tricks


def test_start_turn_rejects_canonically_equivalent_validated_dictionary_trick(
    state: GameState,
) -> None:
    game_flow = build_game_flow(switch_mode="enabled")
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul Switch")
    game_flow.resolve_defense(state, success=True)

    with pytest.raises(InvalidActionError):
        game_flow.start_turn(state, "Switch Soul")


def test_start_turn_allows_reusing_dictionary_trick_when_uniqueness_disabled(
    state: GameState,
) -> None:
    game_flow = build_game_flow(uniqueness_enabled=False, switch_mode="enabled")
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul Switch")
    game_flow.resolve_defense(state, success=True)

    game_flow.start_turn(state, "Switch Soul")

    assert state.current_trick == "Switch Soul"


def test_repetition_blocks_same_attacker_after_failed_launch(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=2,
        uniqueness_enabled=False,
        switch_mode="enabled",
        repetition_mode="choice",
        repetition_limit=1,
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul Switch")
    game_flow.resolve_attack(state, success=False)
    game_flow.resolve_attack(state, success=False)

    assert state.failed_attack_trick_data[0]["trick_key"]

    game_flow.cancel_turn(state, "Makio")

    with pytest.raises(InvalidActionError):
        game_flow.start_turn(state, "Switch Soul")


def test_repetition_common_blocks_other_attacker_after_failed_launch(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=2,
        repetition_mode="common",
        repetition_limit=1,
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")
    game_flow.resolve_attack(state, success=False)
    game_flow.resolve_attack(state, success=False)

    with pytest.raises(InvalidActionError):
        game_flow.start_turn(state, "Soul")


def test_repetition_disabled_allows_retry_after_failed_launch(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=2,
        uniqueness_enabled=False,
        repetition_mode="disabled",
        repetition_limit=1,
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")
    game_flow.resolve_attack(state, success=False)
    game_flow.resolve_attack(state, success=False)

    game_flow.cancel_turn(state, "Makio")
    game_flow.start_turn(state, "Soul")

    assert state.current_trick == "Soul"


def test_repetition_counts_failed_attack_attempt_even_if_turn_eventually_succeeds(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=2,
        uniqueness_enabled=False,
        repetition_mode="choice",
        repetition_limit=1,
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")
    game_flow.resolve_attack(state, success=False)
    game_flow.resolve_attack(state, success=True)
    game_flow.resolve_defense(state, success=True)

    assert len(state.failed_attack_trick_data) == 1

    game_flow.cancel_turn(state, "Makio")
    with pytest.raises(InvalidActionError):
        game_flow.start_turn(state, "Soul")


def test_cancelled_turn_does_not_count_for_repetition(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=2,
        repetition_mode="choice",
        repetition_limit=1,
    )
    game_flow.start_game(state)
    game_flow.cancel_turn(state, "Soul")

    assert state.failed_attack_trick_data == []
    game_flow.cancel_turn(state, "Makio")
    game_flow.start_turn(state, "Soul")

    assert state.current_trick == "Soul"


def test_multiple_attack_can_change_trick_from_second_attempt(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=2,
        multiple_attack_enabled=True,
        uniqueness_enabled=False,
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")
    game_flow.resolve_attack(state, success=False)

    game_flow.change_attack_trick(state, "Makio")

    assert state.current_trick == "Makio"
    assert state.history.events[-1].name == EventName.ATTACK_TRICK_CHANGED


def test_no_repetition_counts_same_trick_once_per_attack_turn(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=3,
        no_repetition=True,
        repetition_mode="choice",
        repetition_limit=1,
        uniqueness_enabled=False,
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")
    game_flow.resolve_attack(state, success=False)
    game_flow.resolve_attack(state, success=False)
    game_flow.resolve_attack(state, success=False)

    assert len(state.failed_attack_trick_data) == 1


def test_no_repetition_does_not_force_a_trick_change_mid_turn(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=3,
        no_repetition=True,
        multiple_attack_enabled=True,
        repetition_mode="choice",
        repetition_limit=1,
        uniqueness_enabled=False,
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")
    game_flow.resolve_attack(state, success=False)

    assert (
        game_flow.current_attack_trick_requires_change(state)
        is False
    )


def test_repetition_without_no_repetition_can_force_a_trick_change_mid_turn(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=2,
        no_repetition=False,
        multiple_attack_enabled=True,
        repetition_mode="choice",
        repetition_limit=1,
        uniqueness_enabled=False,
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")
    game_flow.resolve_attack(state, success=False)

    assert game_flow.current_attack_trick_requires_change(state) is True


def test_switch_rule_blocks_switch_trick_when_disabled(
    state: GameState,
) -> None:
    game_flow = build_game_flow()
    game_flow.start_game(state)

    with pytest.raises(InvalidActionError):
        game_flow.start_turn(state, "Switch Soul")


def test_switch_rule_allows_switch_after_normal_form_is_validated_during_match(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        uniqueness_enabled=False,
        repetition_mode="disabled",
        switch_mode="normal",
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Soul")
    game_flow.resolve_defense(state, success=True)
    game_flow.cancel_turn(state, "Makio")

    game_flow.start_turn(state, "Switch Soul")

    assert state.current_trick == "Switch Soul"


def test_verified_switch_rule_allows_switch_without_prior_normal_validation(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        uniqueness_enabled=False,
        repetition_mode="disabled",
        switch_mode="verified",
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Switch Soul")

    assert state.current_trick == "Switch Soul"


def test_verified_switch_rule_requires_normal_confirmation_on_attack_success(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=2,
        uniqueness_enabled=False,
        repetition_mode="disabled",
        switch_mode="verified",
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Switch Soul")

    assert game_flow.current_attack_requires_switch_normal_verification(state) is True

    result = game_flow.resolve_attack(
        state,
        success=True,
        switch_normal_verified=False,
    )

    assert result == AttackResolutionStatus.ATTACK_CONTINUES
    assert state.attack_attempts_left == 1
    assert state.history.events[-1].payload["switch_normal_verification"] == "failed"


def test_verified_switch_rule_can_promote_to_defense_after_normal_confirmation(
    state: GameState,
) -> None:
    game_flow = build_game_flow(
        attack_attempts=2,
        uniqueness_enabled=False,
        repetition_mode="disabled",
        switch_mode="verified",
    )
    game_flow.start_game(state)
    game_flow.start_turn(state, "Switch Soul")

    result = game_flow.resolve_attack(
        state,
        success=True,
        switch_normal_verified=True,
    )

    assert result == AttackResolutionStatus.DEFENSE_READY
    assert state.turn_phase == TurnPhase.DEFENSE
    assert state.history.events[-1].payload["switch_normal_verification"] == "verified"
