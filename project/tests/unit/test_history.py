from core.events import Event
from core.history import History
from core.types import EventName


def test_build_turns_from_completed_one_vs_one_turn() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.TURN_STARTED,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul",
                "defender_ids": ["Denise"],
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.DEFENSE_FAILED_ATTEMPT,
            payload={
                "player_id": "Denise",
                "trick": "Soul",
                "attempts_left": 2,
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.DEFENSE_FAILED_ATTEMPT,
            payload={
                "player_id": "Denise",
                "trick": "Soul",
                "attempts_left": 1,
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.LETTER_RECEIVED,
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
            name=EventName.TURN_ENDED,
            payload={"next_attacker_id": "Denise"},
        )
    )

    turns = history.build_turns()

    assert len(turns) == 1
    assert turns[0].turn_number == 1
    assert turns[0].attacker_name == "Stan"
    assert turns[0].trick_name == "Soul"
    assert turns[0].trick_status == "validated"
    assert len(turns[0].defenses) == 1
    assert turns[0].defenses[0].defender_name == "Denise"
    assert turns[0].defenses[0].attempts_trace == "XXX"
    assert turns[0].defenses[0].result == "letter"
    assert turns[0].defenses[0].letters == "O"


def test_build_turns_from_failed_turn() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.TURN_FAILED,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul",
                "next_attacker_id": "Denise",
            },
        )
    )

    turns = history.build_turns()

    assert len(turns) == 1
    assert turns[0].turn_number == 1
    assert turns[0].attacker_name == "Stan"
    assert turns[0].trick_name == "Soul"
    assert turns[0].trick_status == "failed"
    assert turns[0].defenses == []


def test_build_turns_from_battle_turn_with_multiple_defenders() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.TURN_STARTED,
            payload={
                "attacker_id": "Stan",
                "trick": "Kickflip",
                "defender_ids": ["Denise", "Alex"],
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.DEFENSE_SUCCEEDED,
            payload={
                "player_id": "Denise",
                "trick": "Kickflip",
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.DEFENSE_FAILED_ATTEMPT,
            payload={
                "player_id": "Alex",
                "trick": "Kickflip",
                "attempts_left": 1,
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.LETTER_RECEIVED,
            payload={
                "player_id": "Alex",
                "trick": "Kickflip",
                "new_score": 1,
                "penalty_display": "S",
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.TURN_ENDED,
            payload={"next_attacker_id": "Denise"},
        )
    )

    turns = history.build_turns()

    assert len(turns) == 1
    assert turns[0].turn_number == 1
    assert turns[0].attacker_name == "Stan"
    assert turns[0].trick_name == "Kickflip"
    assert turns[0].trick_status == "validated"
    assert len(turns[0].defenses) == 2

    assert turns[0].defenses[0].defender_name == "Denise"
    assert turns[0].defenses[0].attempts_trace == "V"
    assert turns[0].defenses[0].result == "success"
    assert turns[0].defenses[0].letters == ""

    assert turns[0].defenses[1].defender_name == "Alex"
    assert turns[0].defenses[1].attempts_trace == "XX"
    assert turns[0].defenses[1].result == "letter"
    assert turns[0].defenses[1].letters == "S"


def test_build_rows_keeps_flat_compatibility() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.TURN_STARTED,
            payload={
                "attacker_id": "Stan",
                "trick": "Kickflip",
                "defender_ids": ["Denise", "Alex"],
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.DEFENSE_SUCCEEDED,
            payload={
                "player_id": "Denise",
                "trick": "Kickflip",
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.LETTER_RECEIVED,
            payload={
                "player_id": "Alex",
                "trick": "Kickflip",
                "new_score": 1,
                "penalty_display": "S",
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.TURN_ENDED,
            payload={"next_attacker_id": "Denise"},
        )
    )

    rows = history.build_rows()

    assert len(rows) == 2
    assert rows[0].attacker_name == "Stan"
    assert rows[0].defender_name == "Denise"
    assert rows[0].defense_result == "V"

    assert rows[1].attacker_name == "Stan"
    assert rows[1].defender_name == "Alex"
    assert rows[1].defense_result == "X"
    assert rows[1].letters == "S"


def test_build_turns_prefers_display_names_over_ids() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.TURN_STARTED,
            payload={
                "attacker_id": "user_1",
                "attacker_name": "Stan",
                "trick": "Soul",
                "defender_ids": ["user_2"],
                "defender_names": ["Denise"],
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.DEFENSE_SUCCEEDED,
            payload={
                "player_id": "user_2",
                "player_name": "Denise",
                "trick": "Soul",
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.TURN_ENDED,
            payload={
                "next_attacker_id": "user_2",
                "next_attacker_name": "Denise",
            },
        )
    )

    turns = history.build_turns()

    assert len(turns) == 1
    assert turns[0].attacker_name == "Stan"
    assert turns[0].defenses[0].defender_name == "Denise"
