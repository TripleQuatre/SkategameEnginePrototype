from core.player import Player
from core.state import GameState
from core.types import EventName, Phase, TurnPhase
from match.flow.turn_cycle import TurnCycle
from match.flow.trick_rules import TrickRules
from match.structure.one_vs_one_structure import OneVsOneStructure


def test_turn_cycle_can_consume_current_trick_once() -> None:
    cycle = TurnCycle(OneVsOneStructure(), TrickRules())
    state = GameState(
        players=[Player(id="p1", name="Stan"), Player(id="p2", name="Denise")],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        current_trick="Soul",
        validated_tricks=["kickflip"],
    )

    cycle.consume_current_trick(state)
    cycle.consume_current_trick(state)

    assert state.validated_tricks == ["kickflip", "soul"]


def test_turn_cycle_can_store_validated_trick_dictionary_data() -> None:
    cycle = TurnCycle(OneVsOneStructure(), TrickRules())
    state = GameState(
        players=[Player(id="p1", name="Stan"), Player(id="p2", name="Denise")],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        current_trick="Switch Soul",
    )

    cycle.consume_current_trick(state)
    cycle.consume_current_trick(state)

    assert state.current_trick == "Switch Soul"
    assert state.validated_tricks == ["switch soul"]
    assert len(state.validated_trick_data) == 1
    assert state.validated_trick_data[0]["label"] == "Soul Switch"
    assert state.validated_trick_data[0]["validated_by_attacker_id"] == "p1"
    assert state.validated_trick_data[0]["validated_by_attacker_name"] == "Stan"


def test_turn_cycle_can_advance_to_next_attacker_and_open_turn() -> None:
    cycle = TurnCycle(OneVsOneStructure(), TrickRules())
    state = GameState(
        players=[Player(id="p1", name="Stan"), Player(id="p2", name="Denise")],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        turn_order=[0, 1],
        attacker_index=0,
        current_trick="Soul",
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
    )

    cycle.advance_to_next_attacker(state, log_turn_end=True)

    assert state.attacker_index == 1
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.current_trick is None
    assert state.defender_indices == []
    assert state.history.events[-1].name == EventName.TURN_ENDED


def test_turn_cycle_can_fail_current_turn() -> None:
    cycle = TurnCycle(OneVsOneStructure(), TrickRules())
    state = GameState(
        players=[Player(id="p1", name="Stan"), Player(id="p2", name="Denise")],
        phase=Phase.TURN,
        turn_phase=TurnPhase.ATTACK,
        turn_order=[0, 1],
        attacker_index=0,
        current_trick="Soul",
        attack_attempts_left=1,
    )

    cycle.fail_current_turn(
        state,
        attacker_id="p1",
        attacker_name="Stan",
        trick="Soul",
    )

    assert state.attacker_index == 1
    assert state.turn_phase == TurnPhase.TURN_OPEN
    assert state.current_trick is None
    assert state.history.events[-1].name == EventName.TURN_FAILED


def test_turn_cycle_can_finish_game_runtime() -> None:
    cycle = TurnCycle(OneVsOneStructure(), TrickRules())
    state = GameState(
        players=[Player(id="p1", name="Stan"), Player(id="p2", name="Denise")],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        current_trick="Soul",
        defense_attempts_left=1,
        defender_indices=[1],
    )

    cycle.finish_game_runtime(state)

    assert state.phase == Phase.END
    assert state.turn_phase == TurnPhase.TURN_FINISHED
    assert state.current_trick is None
    assert state.defender_indices == []
