from config.match_parameters import MatchParameters
from config.match_policies import InitialTurnOrderPolicy, MatchPolicies
from core.player import Player
from core.state import GameState
from core.types import EventName, Phase, TurnPhase
from match.flow.trick_rules import TrickRules
from match.transitions.transition_service import MatchTransitionService
from validation.action_validator import ActionValidator
from validation.config_validator import ConfigValidator
from validation.state_validator import StateValidator


def test_match_transition_service_can_create_initial_runtime() -> None:
    service = MatchTransitionService(
        config_validator=ConfigValidator(),
    )
    match_parameters = MatchParameters(
        player_ids=["p1", "p2"],
        structure_name="one_vs_one",
    )

    runtime = service.create_initial_runtime(match_parameters, StateValidator())

    assert runtime.match_parameters == match_parameters
    assert runtime.structure.structure_name == "one_vs_one"
    assert runtime.game_flow.structure is runtime.structure
    assert [player.id for player in runtime.state.players] == ["p1", "p2"]
    assert runtime.match_config == match_parameters.to_match_config()


def test_match_transition_service_can_add_player_and_rebuild_runtime() -> None:
    service = MatchTransitionService(
        config_validator=ConfigValidator(),
    )
    action_validator = ActionValidator(TrickRules())
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

    transition = service.add_player_between_turns(
        state,
        match_parameters,
        action_validator,
        "p3",
    )

    assert transition.event.name == EventName.PLAYER_JOINED
    assert [player.id for player in state.players] == ["p1", "p2", "p3"]
    assert state.turn_order == [0, 1, 2]
    assert transition.structure.__class__.__name__ == "BattleStructure"
    assert transition.structure_name == "battle"
    assert transition.match_config.structure_name == "battle"
    assert transition.previous_structure_name == "one_vs_one"
    assert transition.structure_changed is True
    assert transition.previous_preset_name == "classic_skate"
    assert transition.preset_name is None
    assert transition.preset_invalidated is True
    assert transition.previous_player_ids == ["p1", "p2"]
    assert transition.player_ids == ["p1", "p2", "p3"]
    assert transition.previous_player_count == 2
    assert transition.player_count == 3
    assert transition.previous_turn_order == [0, 1]
    assert transition.turn_order == [0, 1, 2]
    assert transition.previous_attacker_id == "p1"
    assert transition.previous_attacker_name == "Stan"
    assert transition.attacker_id == "p1"
    assert transition.attacker_name == "Stan"
    assert transition.event.payload["preset_invalidated"] is True
    assert transition.game_flow.structure is transition.structure


def test_match_transition_service_add_player_keeps_explicit_order_coherent() -> None:
    service = MatchTransitionService(
        config_validator=ConfigValidator(),
    )
    action_validator = ActionValidator(TrickRules())
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

    transition = service.add_player_between_turns(
        state,
        match_parameters,
        action_validator,
        "p4",
        player_name="Frank",
    )

    assert transition.match_config.policies.explicit_player_order == (
        "p3",
        "p1",
        "p2",
        "p4",
    )
    assert transition.match_config.player_display_names == [
        "Alex",
        "Stan",
        "Denise",
        "Frank",
    ]


def test_match_transition_service_can_remove_player_and_rebuild_runtime() -> None:
    service = MatchTransitionService(
        config_validator=ConfigValidator(),
    )
    action_validator = ActionValidator(TrickRules())
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

    transition = service.remove_player_between_turns(
        state,
        match_parameters,
        action_validator,
        "p2",
    )

    assert transition.event.name == EventName.PLAYER_REMOVED
    assert [player.id for player in state.players] == ["p1", "p3"]
    assert state.turn_order == [0, 1]
    assert transition.structure.__class__.__name__ == "OneVsOneStructure"
    assert transition.structure_name == "one_vs_one"
    assert transition.match_config.structure_name == "one_vs_one"
    assert transition.previous_structure_name == "battle"
    assert transition.structure_changed is True
    assert transition.previous_preset_name == "battle_standard"
    assert transition.preset_name is None
    assert transition.preset_invalidated is True
    assert transition.previous_player_ids == ["p1", "p2", "p3"]
    assert transition.player_ids == ["p1", "p3"]
    assert transition.previous_player_count == 3
    assert transition.player_count == 2
    assert transition.previous_turn_order == [0, 1, 2]
    assert transition.turn_order == [0, 1]
    assert transition.previous_attacker_id == "p1"
    assert transition.previous_attacker_name == "Stan"
    assert transition.attacker_id == "p1"
    assert transition.attacker_name == "Stan"
    assert transition.event.payload["preset_invalidated"] is True
    assert transition.game_flow.structure is transition.structure


def test_match_transition_service_can_apply_transition_to_runtime_state() -> None:
    service = MatchTransitionService(
        config_validator=ConfigValidator(),
    )
    action_validator = ActionValidator(TrickRules())
    state_validator = StateValidator()
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

    transition = service.add_player_between_turns(
        state,
        match_parameters,
        action_validator,
        "p3",
    )

    runtime = service.apply_transition(
        state,
        transition,
        state_validator,
    )

    assert runtime.structure is transition.structure
    assert runtime.game_flow is transition.game_flow
    assert runtime.state is state
    assert state.history.events[-1] is transition.event


def test_match_transition_service_can_execute_transition_end_to_end() -> None:
    service = MatchTransitionService(
        config_validator=ConfigValidator(),
    )
    action_validator = ActionValidator(TrickRules())
    state_validator = StateValidator()
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

    transition = service.execute_add_player_between_turns(
        state,
        match_parameters,
        action_validator,
        state_validator,
        "p3",
    )

    assert transition.structure_name == "battle"
    assert transition.match_config.structure_name == "battle"
    assert state.history.events[-1] is transition.event


def test_match_transition_service_can_build_runtime_for_match_state() -> None:
    service = MatchTransitionService(
        config_validator=ConfigValidator(),
    )
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
        policies=MatchPolicies(),
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
        attacker_index=1,
    )

    structure, game_flow = service.build_runtime(state, match_parameters)

    assert structure.structure_name == "battle"
    assert game_flow.structure is structure
    assert game_flow.match_parameters == match_parameters


def test_match_transition_service_can_restore_runtime() -> None:
    service = MatchTransitionService(
        config_validator=ConfigValidator(),
    )
    match_parameters = MatchParameters(
        player_ids=["p1", "p2", "p3"],
        structure_name="battle",
        policies=MatchPolicies(),
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
        attacker_index=1,
    )

    runtime = service.restore_runtime(state, match_parameters, StateValidator())

    assert runtime.state is state
    assert runtime.match_parameters == match_parameters
    assert runtime.structure.structure_name == "battle"
    assert runtime.game_flow.structure is runtime.structure
    assert runtime.match_config == match_parameters.to_match_config()
