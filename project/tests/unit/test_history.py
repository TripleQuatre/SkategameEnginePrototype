from core.events import Event
from core.history import History


def test_build_rows_from_completed_turn() -> None:
    history = History()
    history.add_event(
        Event(
            name="turn_started",
            payload={
                "attacker_id": "Stan",
                "trick": "Soul",
                "defender_ids": ["Denise"],
            },
        )
    )
    history.add_event(
        Event(
            name="defense_failed_attempt",
            payload={
                "player_id": "Denise",
                "trick": "Soul",
                "attempts_left": 2,
            },
        )
    )
    history.add_event(
        Event(
            name="defense_failed_attempt",
            payload={
                "player_id": "Denise",
                "trick": "Soul",
                "attempts_left": 1,
            },
        )
    )
    history.add_event(
        Event(
            name="letter_received",
            payload={
                "player_id": "Denise",
                "trick": "Soul",
                "new_score": 1,
                "penalty_display": "O",
            },
        )
    )
    history.add_event(
        Event(
            name="turn_ended",
            payload={"next_attacker_id": "Denise"},
        )
    )

    rows = history.build_rows()

    assert len(rows) == 1
    assert rows[0].turn_number == 1
    assert rows[0].attacker_name == "Stan"
    assert rows[0].trick_name == "Soul"
    assert rows[0].trick_validated == "V"
    assert rows[0].defender_name == "Denise"
    assert rows[0].defense_result == "XXX"
    assert rows[0].letters == "O"


def test_build_rows_from_cancelled_turn() -> None:
    history = History()
    history.add_event(
        Event(
            name="turn_cancelled",
            payload={
                "attacker_id": "Stan",
                "trick": "Soul",
                "next_attacker_id": "Denise",
            },
        )
    )

    rows = history.build_rows()

    assert len(rows) == 1
    assert rows[0].turn_number == 1
    assert rows[0].attacker_name == "Stan"
    assert rows[0].trick_name == "Soul"
    assert rows[0].trick_validated == "X"
    assert rows[0].defender_name == ""
    assert rows[0].defense_result == ""
    assert rows[0].letters == ""