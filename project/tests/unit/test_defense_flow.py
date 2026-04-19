from core.player import Player
from core.state import GameState
from core.types import DefenseResolutionStatus, EventName, Phase, TurnPhase
from match.defense.defense_attempt_resolver import DefenseAttemptResolver
from match.defense.defense_flow import DefenseFlow
from match.scoring.letters_scoring import LettersScoring
from match.victory.last_player_standing import LastPlayerStandingVictory


def test_defense_flow_can_continue_after_failed_attempt() -> None:
    flow = DefenseFlow(
        DefenseAttemptResolver(LettersScoring()),
        LastPlayerStandingVictory(),
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        attacker_index=0,
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=2,
        current_trick="kickflip",
    )

    result = flow.resolve_defense(
        state,
        success=False,
        on_mark_game_finished=lambda: None,
        on_mark_turn_finished=lambda: None,
        on_consume_current_trick=lambda: None,
        on_advance_to_next_attacker=lambda log_turn_end: None,
    )

    assert result == DefenseResolutionStatus.DEFENSE_CONTINUES
    assert state.defense_attempts_left == 1
    assert state.history.events[-1].name == EventName.DEFENSE_FAILED_ATTEMPT


def test_defense_flow_can_finish_turn() -> None:
    flow = DefenseFlow(
        DefenseAttemptResolver(LettersScoring()),
        LastPlayerStandingVictory(),
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan"),
            Player(id="p2", name="Denise"),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        attacker_index=0,
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
        current_trick="kickflip",
    )
    consumed = {"called": False}
    marked = {"called": False}
    advanced = {"called": False}

    result = flow.resolve_defense(
        state,
        success=True,
        on_mark_game_finished=lambda: None,
        on_mark_turn_finished=lambda: marked.__setitem__("called", True),
        on_consume_current_trick=lambda: consumed.__setitem__("called", True),
        on_advance_to_next_attacker=lambda log_turn_end: advanced.__setitem__(
            "called", log_turn_end
        ),
    )

    assert result == DefenseResolutionStatus.TURN_FINISHED
    assert consumed["called"] is True
    assert marked["called"] is True
    assert advanced["called"] is True
    assert state.history.events[-1].name == EventName.DEFENSE_SUCCEEDED


def test_defense_flow_can_finish_game_after_elimination() -> None:
    flow = DefenseFlow(
        DefenseAttemptResolver(LettersScoring()),
        LastPlayerStandingVictory(),
    )
    state = GameState(
        players=[
            Player(id="p1", name="Stan", score=0, is_active=True),
            Player(id="p2", name="Denise", score=0, is_active=True),
        ],
        phase=Phase.TURN,
        turn_phase=TurnPhase.DEFENSE,
        attacker_index=0,
        defender_indices=[1],
        current_defender_position=0,
        defense_attempts_left=1,
        current_trick="kickflip",
    )
    state.rule_set.letters_word = "S"
    finished = {"called": False}
    consumed = {"called": False}

    result = flow.resolve_defense(
        state,
        success=False,
        on_mark_game_finished=lambda: finished.__setitem__("called", True),
        on_mark_turn_finished=lambda: None,
        on_consume_current_trick=lambda: consumed.__setitem__("called", True),
        on_advance_to_next_attacker=lambda log_turn_end: None,
    )

    assert result == DefenseResolutionStatus.GAME_FINISHED
    assert finished["called"] is True
    assert consumed["called"] is True
    history_names = [event.name for event in state.history.events]
    assert EventName.LETTER_RECEIVED in history_names
    assert EventName.PLAYER_ELIMINATED in history_names
    assert EventName.GAME_FINISHED in history_names
