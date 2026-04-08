from core.player import Player
from core.state import GameState
from engine.end_conditions import EndConditions


def test_is_player_eliminated_returns_true_when_score_reaches_word_length() -> None:
    player = Player(id="p1", name="Player 1", score=5)
    state = GameState(players=[player])

    end_conditions = EndConditions()

    assert end_conditions.is_player_eliminated(state, player) is True


def test_apply_eliminations_disables_eliminated_players() -> None:
    players = [
        Player(id="p1", name="Player 1", score=5),
        Player(id="p2", name="Player 2", score=2),
    ]
    state = GameState(players=players)

    end_conditions = EndConditions()
    eliminated_players = end_conditions.apply_eliminations(state)

    assert len(eliminated_players) == 1
    assert eliminated_players[0].id == "p1"
    assert players[0].is_active is False
    assert players[1].is_active is True


def test_is_game_finished_returns_true_when_only_one_active_player_remains() -> None:
    players = [
        Player(id="p1", name="Player 1", is_active=True),
        Player(id="p2", name="Player 2", is_active=False),
    ]
    state = GameState(players=players)

    end_conditions = EndConditions()

    assert end_conditions.is_game_finished(state) is True


def test_get_winner_returns_only_active_player() -> None:
    players = [
        Player(id="p1", name="Player 1", is_active=True),
        Player(id="p2", name="Player 2", is_active=False),
    ]
    state = GameState(players=players)

    end_conditions = EndConditions()
    winner = end_conditions.get_winner(state)

    assert winner is not None
    assert winner.id == "p1"