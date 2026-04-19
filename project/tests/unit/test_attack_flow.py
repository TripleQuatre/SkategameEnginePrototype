from core.player import Player
from core.state import GameState
from core.types import AttackResolutionStatus, EventName, Phase, TurnPhase
from match.attack.attack_flow import AttackFlow


def test_attack_flow_start_turn_opens_attack_phase_and_logs_turn_start() -> None:
    attack_flow = AttackFlow()
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

    attack_flow.start_turn(
        state,
        trick="kickflip",
        attack_attempts=2,
        attacker_id="p1",
        attacker_name="Stan",
        defender_ids=["p2"],
        defender_names=["Denise"],
    )

    assert state.turn_phase == TurnPhase.ATTACK
    assert state.current_trick == "kickflip"
    assert state.attack_attempts_left == 2
    assert state.history.events[-1].name == EventName.TURN_STARTED
    assert state.history.events[-1].payload["defender_names"] == ["Denise"]


def test_attack_flow_resolve_attack_success_uses_callback() -> None:
    attack_flow = AttackFlow()
    state = GameState(
        players=[Player(id="p1", name="Stan")],
        phase=Phase.TURN,
        turn_phase=TurnPhase.ATTACK,
        attack_attempts_left=2,
        current_trick="soul",
    )
    promoted = {"called": False}

    result = attack_flow.resolve_attack(
        state,
        success=True,
        attacker_id="p1",
        attacker_name="Stan",
        on_attack_succeeded=lambda: promoted.__setitem__("called", True),
        on_attack_failed=lambda: None,
    )

    assert result == AttackResolutionStatus.DEFENSE_READY
    assert promoted["called"] is True
    assert state.history.events[-1].name == EventName.ATTACK_SUCCEEDED


def test_attack_flow_resolve_attack_failure_can_continue_or_fail() -> None:
    attack_flow = AttackFlow()
    state = GameState(
        players=[Player(id="p1", name="Stan")],
        phase=Phase.TURN,
        turn_phase=TurnPhase.ATTACK,
        attack_attempts_left=2,
        current_trick="soul",
    )
    failed = {"called": False}

    result = attack_flow.resolve_attack(
        state,
        success=False,
        attacker_id="p1",
        attacker_name="Stan",
        on_attack_succeeded=lambda: None,
        on_attack_failed=lambda: failed.__setitem__("called", True),
    )

    assert result == AttackResolutionStatus.ATTACK_CONTINUES
    assert state.attack_attempts_left == 1
    assert state.history.events[-1].name == EventName.ATTACK_FAILED_ATTEMPT
    assert failed["called"] is False

    result = attack_flow.resolve_attack(
        state,
        success=False,
        attacker_id="p1",
        attacker_name="Stan",
        on_attack_succeeded=lambda: None,
        on_attack_failed=lambda: failed.__setitem__("called", True),
    )

    assert result == AttackResolutionStatus.TURN_FAILED
    assert failed["called"] is True
