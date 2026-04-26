from config.match_parameters import MatchParameters
from config.match_policies import (
    InitialTurnOrderPolicy,
    MatchPolicies,
    RelevanceCriterion,
)
from core.exceptions import InvalidActionError
from core.player import Player
from core.state import GameState
from core.types import EventName, Phase, TurnPhase
from match.transitions.roster_transitions import RosterTransitions
from validation.config_validator import ConfigValidator


def test_roster_transitions_can_add_player_and_switch_to_battle() -> None:
    transitions = RosterTransitions()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        structure_name="one_vs_one",
        preset_name="classic_skate",
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[0, 1],
        attacker_index=0,
    )

    event = transitions.add_player_between_turns(state, match_parameters, "p3")

    assert [player.id for player in state.players] == ["p1", "p2", "p3"]
    assert state.turn_order == [0, 1, 2]
    assert event.match_config.player_ids == ["p1", "p2", "p3"]
    assert event.match_config.structure_name == "battle"
    assert event.match_config.preset_name is None
    assert event.name == EventName.PLAYER_JOINED
    assert event.payload["previous_structure_name"] == "one_vs_one"
    assert event.payload["structure_name"] == "battle"
    assert event.payload["structure_changed"] is True
    assert event.payload["previous_structure_name"] == "one_vs_one"
    assert event.payload["structure_name"] == "battle"
    assert event.payload["preset_invalidated"] is True
    assert event.payload["previous_player_ids"] == ["p1", "p2"]
    assert event.payload["player_ids"] == ["p1", "p2", "p3"]
    assert event.payload["previous_player_names"] == ["Stan", "Denise"]
    assert event.payload["player_names"] == ["Stan", "Denise", "p3"]
    assert event.payload["previous_player_count"] == 2
    assert event.payload["player_count"] == 3
    assert event.payload["previous_turn_order"] == [0, 1]
    assert event.payload["turn_order"] == [0, 1, 2]
    assert event.payload["previous_attacker_id"] == "p1"
    assert event.payload["previous_attacker_name"] == "Stan"
    assert event.payload["attacker_id"] == "p1"
    assert event.payload["attacker_name"] == "Stan"


def test_roster_transitions_reject_duplicate_player_addition() -> None:
    transitions = RosterTransitions()
    match_parameters = MatchParameters(player_ids=["p1", "p2"])
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[0, 1],
        attacker_index=0,
    )

    try:
        transitions.add_player_between_turns(state, match_parameters, "p2")
        assert False, "Expected InvalidActionError"
    except InvalidActionError:
        pass


def test_roster_transitions_can_remove_player_and_switch_to_one_vs_one() -> None:
    transitions = RosterTransitions()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
        policies=MatchPolicies(),
        preset_name="battle_standard",
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
            Player(id="p3", name="Alex"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[0, 1, 2],
        attacker_index=0,
    )

    event = transitions.remove_player_between_turns(state, match_parameters, "p2")

    assert [player.id for player in state.players] == ["p1", "p3"]
    assert state.turn_order == [0, 1]
    assert state.attacker_index == 0
    assert event.match_config.player_ids == ["p1", "p3"]
    assert event.match_config.structure_name == "one_vs_one"
    assert event.match_config.preset_name is None
    assert event.match_config.policies == MatchPolicies()
    assert event.name == EventName.PLAYER_REMOVED
    assert event.payload["previous_structure_name"] == "battle"
    assert event.payload["structure_name"] == "one_vs_one"
    assert event.payload["structure_changed"] is True
    assert event.payload["previous_structure_name"] == "battle"
    assert event.payload["structure_name"] == "one_vs_one"
    assert event.payload["preset_invalidated"] is True
    assert event.payload["previous_player_ids"] == ["p1", "p2", "p3"]
    assert event.payload["player_ids"] == ["p1", "p3"]
    assert event.payload["previous_player_names"] == ["Stan", "Denise", "Alex"]
    assert event.payload["player_names"] == ["Stan", "Alex"]
    assert event.payload["previous_player_count"] == 3
    assert event.payload["player_count"] == 2
    assert event.payload["previous_turn_order"] == [0, 1, 2]
    assert event.payload["turn_order"] == [0, 1]
    assert event.payload["previous_attacker_id"] == "p1"
    assert event.payload["previous_attacker_name"] == "Stan"
    assert event.payload["attacker_id"] == "p1"
    assert event.payload["attacker_name"] == "Stan"


def test_roster_transitions_reassign_attacker_when_current_attacker_is_removed() -> None:
    transitions = RosterTransitions()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
            Player(id="p3", name="Alex"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[2, 0, 1],
        attacker_index=2,
    )

    event = transitions.remove_player_between_turns(state, match_parameters, "p3")

    assert [player.id for player in state.players] == ["p1", "p2"]
    assert state.turn_order == [0, 1]
    assert state.attacker_index == 0
    assert event.payload["previous_turn_order"] == [2, 0, 1]
    assert event.payload["turn_order"] == [0, 1]
    assert event.payload["previous_attacker_id"] == "p3"
    assert event.payload["previous_attacker_name"] == "Alex"
    assert event.payload["attacker_id"] == "p1"
    assert event.payload["attacker_name"] == "Stan"


def test_roster_transitions_preserve_profile_alignment_and_display_names() -> None:
    transitions = RosterTransitions()
    match_parameters = MatchParameters(
        player_ids=["stan", "denise"],
        player_profile_ids=["stan", "denise"],
        player_display_names=["Stan", "Denise"],
        structure_name="one_vs_one",
    )
    state = GameState(
        players=[
            Player(id="stan", name="Stan"),
            Player(id="denise", name="Denise"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[0, 1],
        attacker_index=0,
    )

    joined = transitions.add_player_between_turns(
        state,
        match_parameters,
        "alex",
        player_name="Alex",
    )

    assert joined.match_config.player_ids == ["stan", "denise", "alex"]
    assert joined.match_config.player_profile_ids == ["stan", "denise", None]
    assert joined.match_config.player_display_names == ["Stan", "Denise", "Alex"]

    removed = transitions.remove_player_between_turns(
        state,
        joined.match_config,
        "denise",
    )

    assert removed.match_config.player_ids == ["stan", "alex"]
    assert removed.match_config.player_profile_ids == ["stan", None]
    assert removed.match_config.player_display_names == ["Stan", "Alex"]


def test_roster_transitions_extend_explicit_choice_order_when_adding_player() -> None:
    transitions = RosterTransitions()
    validator = ConfigValidator()
    match_parameters = MatchParameters(
        player_ids=["p3", "p1", "p2"],
        player_display_names=["Alex", "Stan", "Denise"],
        structure_name="battle",
        policies=MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy.EXPLICIT_CHOICE,
            explicit_player_order=("p3", "p1", "p2"),
        ),
    )
    state = GameState(
        players=[
            Player(id="p3", name="Alex"),
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[0, 1, 2],
        attacker_index=0,
    )

    joined = transitions.add_player_between_turns(
        state,
        match_parameters,
        "p4",
        player_name="Frank",
    )

    assert joined.match_config.policies.initial_turn_order == InitialTurnOrderPolicy.EXPLICIT_CHOICE
    assert joined.match_config.policies.explicit_player_order == ("p3", "p1", "p2", "p4")
    validator.validate_match_config(joined.match_config)


def test_roster_transitions_remove_player_from_explicit_choice_order() -> None:
    transitions = RosterTransitions()
    validator = ConfigValidator()
    match_parameters = MatchParameters(
        player_ids=["p3", "p1", "p2", "p4"],
        player_display_names=["Alex", "Stan", "Denise", "Frank"],
        structure_name="battle",
        policies=MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy.EXPLICIT_CHOICE,
            explicit_player_order=("p3", "p1", "p2", "p4"),
        ),
    )
    state = GameState(
        players=[
            Player(id="p3", name="Alex"),
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
            Player(id="p4", name="Frank"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[0, 1, 2, 3],
        attacker_index=0,
    )

    removed = transitions.remove_player_between_turns(
        state,
        match_parameters,
        "p2",
    )

    assert removed.match_config.policies.initial_turn_order == InitialTurnOrderPolicy.EXPLICIT_CHOICE
    assert removed.match_config.policies.explicit_player_order == ("p3", "p1", "p4")
    validator.validate_match_config(removed.match_config)


def test_roster_transitions_fallback_from_relevance_to_choice_when_adding_non_profile_player() -> None:
    transitions = RosterTransitions()
    validator = ConfigValidator()
    match_parameters = MatchParameters(
        player_ids=["stan", "alex", "denise"],
        player_profile_ids=["stan", "alex", "denise"],
        player_display_names=["Stan", "Alex", "Denise"],
        structure_name="battle",
        policies=MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy.RELEVANCE,
            relevance_criterion=RelevanceCriterion.AGE,
            explicit_player_order=("alex", "stan", "denise"),
        ),
    )
    state = GameState(
        players=[
            Player(id="stan", name="Stan"),
            Player(id="alex", name="Alex"),
            Player(id="denise", name="Denise"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[0, 1, 2],
        attacker_index=0,
    )

    joined = transitions.add_player_between_turns(
        state,
        match_parameters,
        "frank",
        player_name="Frank",
    )

    assert joined.match_config.policies.initial_turn_order == InitialTurnOrderPolicy.EXPLICIT_CHOICE
    assert joined.match_config.policies.relevance_criterion is None
    assert joined.match_config.policies.explicit_player_order == (
        "alex",
        "stan",
        "denise",
        "frank",
    )
    validator.validate_match_config(joined.match_config)


def test_roster_transitions_reject_unknown_player_removal() -> None:
    transitions = RosterTransitions()
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
            Player(id="p3", name="Alex"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.TURN_OPEN,
        turn_order=[0, 1, 2],
        attacker_index=0,
    )

    try:
        transitions.remove_player_between_turns(state, match_parameters, "p4")
        assert False, "Expected InvalidActionError"
    except InvalidActionError:
        pass
