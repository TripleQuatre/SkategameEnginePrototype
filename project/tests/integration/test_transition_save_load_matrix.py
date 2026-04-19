import shutil
from pathlib import Path

from application.game_session import GameSession
from config.match_parameters import MatchParameters
from config.rule_set_config import RuleSetConfig
from core.types import EventName, TurnPhase


def _make_case_dir(test_name: str) -> Path:
    base_dir = (
        Path(__file__).resolve().parents[2]
        / "local_tmp"
        / "transition_matrix"
        / test_name
    )
    shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_game_session_can_save_and_load_one_vs_one_to_battle_transition() -> None:
    case_dir = _make_case_dir("one_vs_one_to_battle")

    try:
        session = GameSession(
            MatchParameters(
                player_ids=["p1", "p2"],
                preset_name="classic_skate",
                rule_set=RuleSetConfig(
                    letters_word="SKATE",
                    elimination_enabled=True,
                    defense_attempts=3,
                ),
            )
        )
        session.start_game()
        session.add_player_between_turns("p3")

        save_path = case_dir / "after_join.json"
        session.save_game(str(save_path))

        reloaded_session = GameSession(MatchParameters(player_ids=["placeholder1", "placeholder2"]))
        reloaded_session.load_game(str(save_path))

        state = reloaded_session.get_state()
        context = state.history.build_match_context()

        assert save_path.exists()
        assert reloaded_session.structure_name == "battle"
        assert reloaded_session.match_parameters.preset_name is None
        assert reloaded_session.match_parameters.player_ids == ["p1", "p2", "p3"]
        assert [player.id for player in state.players] == ["p1", "p2", "p3"]
        assert state.turn_phase == TurnPhase.TURN_OPEN
        assert state.history.events[-1].name == EventName.PLAYER_JOINED
        assert state.history.events[-1].payload["preset_invalidated"] is True
        assert context is not None
        assert context.structure_name == "battle"
        assert context.preset_name is None
        assert context.player_names == ["p1", "p2", "p3"]
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_game_session_can_save_and_load_battle_to_one_vs_one_transition() -> None:
    case_dir = _make_case_dir("battle_to_one_vs_one")

    try:
        session = GameSession(
            MatchParameters(
                player_ids=["p1", "p2", "p3"],
                structure_name="battle",
            )
        )
        session.start_game()
        session.remove_player_between_turns("p2")

        save_path = case_dir / "after_remove.json"
        session.save_game(str(save_path))

        reloaded_session = GameSession(MatchParameters(player_ids=["placeholder1", "placeholder2"]))
        reloaded_session.load_game(str(save_path))

        state = reloaded_session.get_state()
        context = state.history.build_match_context()

        assert save_path.exists()
        assert reloaded_session.structure_name == "one_vs_one"
        assert reloaded_session.match_parameters.preset_name is None
        assert reloaded_session.match_parameters.player_ids == ["p1", "p3"]
        assert [player.id for player in state.players] == ["p1", "p3"]
        assert state.turn_order == [0, 1]
        assert state.turn_phase == TurnPhase.TURN_OPEN
        assert state.history.events[-1].name == EventName.PLAYER_REMOVED
        assert state.history.events[-1].payload["preset_invalidated"] is False
        assert context is not None
        assert context.structure_name == "one_vs_one"
        assert context.preset_name is None
        assert context.player_names == ["p1", "p3"]
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_game_session_undo_after_join_then_remove_restores_previous_structures() -> None:
    session = GameSession(
        MatchParameters(
            player_ids=["p1", "p2"],
            preset_name="classic_skate",
            rule_set=RuleSetConfig(
                letters_word="SKATE",
                elimination_enabled=True,
                defense_attempts=3,
            ),
        )
    )

    session.start_game()
    session.add_player_between_turns("p3")
    session.remove_player_between_turns("p2")

    assert session.undo() is True
    state = session.get_state()
    context = state.history.build_match_context()

    assert session.structure_name == "battle"
    assert session.match_parameters.player_ids == ["p1", "p2", "p3"]
    assert [player.id for player in state.players] == ["p1", "p2", "p3"]
    assert state.history.events[-1].name == EventName.PLAYER_JOINED
    assert state.history.events[-1].payload["preset_invalidated"] is True
    assert context is not None
    assert context.structure_name == "battle"
    assert context.player_names == ["p1", "p2", "p3"]

    assert session.undo() is True
    state = session.get_state()
    context = state.history.build_match_context()

    assert session.structure_name == "one_vs_one"
    assert session.match_parameters.preset_name == "classic_skate"
    assert session.match_parameters.player_ids == ["p1", "p2"]
    assert [player.id for player in state.players] == ["p1", "p2"]
    assert state.turn_order == [0, 1]
    assert state.history.events[-1].name == EventName.GAME_STARTED
    assert context is not None
    assert context.structure_name == "one_vs_one"
    assert context.preset_name == "classic_skate"
