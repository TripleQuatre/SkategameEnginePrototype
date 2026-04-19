from core.player import Player
from core.state import GameState
from match.scoring.letters_scoring import LettersScoring
from match.victory.last_player_standing import LastPlayerStandingVictory


def test_letters_scoring_applies_letter_penalty() -> None:
    scoring = LettersScoring()
    player = Player(id="p1", name="Stan", score=1)
    state = GameState(players=[player])

    scoring.apply_letter_penalty(state, player)

    assert player.score == 2
    assert scoring.get_penalty_display(state, player) == "SK"


def test_last_player_standing_eliminates_and_finds_winner() -> None:
    victory = LastPlayerStandingVictory()
    players = [
        Player(id="p1", name="Stan", score=0, is_active=True),
        Player(id="p2", name="Denise", score=5, is_active=True),
    ]
    state = GameState(players=players)

    eliminated_players = victory.apply_eliminations(state)

    assert [player.id for player in eliminated_players] == ["p2"]
    assert victory.is_game_finished(state) is True
    winner = victory.get_winner(state)
    assert winner is not None
    assert winner.id == "p1"
