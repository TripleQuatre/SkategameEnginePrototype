from core.events import Event
from core.history import History
from core.types import EventName


def test_build_match_context_from_game_started_event() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.GAME_STARTED,
            payload={
                "structure_name": "battle",
                "preset_name": "battle_standard",
                "player_names": ["Stan", "Denise", "Alex"],
                "turn_order": [2, 0, 1],
                "starting_attacker_name": "Alex",
                "initial_turn_order_policy": "randomized",
                "attacker_rotation_policy": "follow_turn_order",
                "defender_order_policy": "follow_turn_order",
            },
        )
    )

    context = history.build_match_context()

    assert context is not None
    assert context.structure_name == "battle"
    assert context.preset_name == "battle_standard"
    assert context.player_names == ["Stan", "Denise", "Alex"]
    assert context.turn_order == [2, 0, 1]
    assert context.starting_attacker_name == "Alex"
    assert context.initial_turn_order_policy == "randomized"
    assert context.attacker_rotation_policy == "follow_turn_order"
    assert context.defender_order_policy == "follow_turn_order"


def test_build_match_context_accepts_v7_structure_only_payload() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.GAME_STARTED,
            payload={
                "structure_name": "battle",
                "player_names": ["Stan", "Denise", "Alex"],
                "turn_order": [2, 0, 1],
                "starting_attacker_name": "Alex",
            },
        )
    )

    context = history.build_match_context()

    assert context is not None
    assert context.structure_name == "battle"
    assert context.player_names == ["Stan", "Denise", "Alex"]
    assert context.turn_order == [2, 0, 1]
    assert context.starting_attacker_name == "Alex"


def test_build_match_context_is_updated_after_player_join_event() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.GAME_STARTED,
            payload={
                "structure_name": "one_vs_one",
                "preset_name": "classic_skate",
                "player_names": ["Stan", "Denise"],
                "turn_order": [0, 1],
                "starting_attacker_name": "Stan",
                "initial_turn_order_policy": "fixed_player_order",
                "attacker_rotation_policy": "follow_turn_order",
                "defender_order_policy": "follow_turn_order",
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.PLAYER_JOINED,
            payload={
                "structure_name": "battle",
                "preset_name": None,
                "player_names": ["Stan", "Denise", "Alex"],
                "turn_order": [0, 1, 2],
            },
        )
    )

    context = history.build_match_context()

    assert context is not None
    assert context.structure_name == "battle"
    assert context.preset_name is None
    assert context.player_names == ["Stan", "Denise", "Alex"]
    assert context.turn_order == [0, 1, 2]


def test_build_match_context_is_updated_after_player_removed_event() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.GAME_STARTED,
            payload={
                "structure_name": "battle",
                "preset_name": "battle_standard",
                "player_names": ["Stan", "Denise", "Alex"],
                "turn_order": [0, 1, 2],
                "starting_attacker_name": "Stan",
                "initial_turn_order_policy": "randomized",
                "attacker_rotation_policy": "follow_turn_order",
                "defender_order_policy": "follow_turn_order",
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.PLAYER_REMOVED,
            payload={
                "structure_name": "one_vs_one",
                "preset_name": None,
                "player_names": ["Stan", "Alex"],
                "turn_order": [0, 1],
            },
        )
    )

    context = history.build_match_context()

    assert context is not None
    assert context.structure_name == "one_vs_one"
    assert context.preset_name is None
    assert context.player_names == ["Stan", "Alex"]
    assert context.turn_order == [0, 1]


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
    assert turns[0].attack_trace == "V"
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
    assert turns[0].attack_trace == "X"
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
    assert turns[0].attack_trace == "V"
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
    assert rows[0].trick_validated == "V"
    assert rows[0].defender_name == "Denise"
    assert rows[0].defense_result == "V"

    assert rows[1].attacker_name == "Stan"
    assert rows[1].trick_validated == "V"
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
    assert turns[0].attack_trace == "V"


def test_build_turns_keeps_attack_trace_before_defense() -> None:
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
            name=EventName.ATTACK_FAILED_ATTEMPT,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul",
                "attempts_left": 1,
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.ATTACK_SUCCEEDED,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul",
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.DEFENSE_SUCCEEDED,
            payload={
                "player_id": "Denise",
                "trick": "Soul",
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
    rows = history.build_rows()

    assert len(turns) == 1
    assert turns[0].trick_status == "validated"
    assert turns[0].attack_trace == "XV"
    assert len(rows) == 1
    assert rows[0].trick_validated == "XV"


def test_build_turns_does_not_duplicate_started_turn_when_attack_fails() -> None:
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
            name=EventName.ATTACK_FAILED_ATTEMPT,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul",
                "attempts_left": 1,
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.ATTACK_FAILED_ATTEMPT,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul",
                "attempts_left": 0,
            },
        )
    )
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
    rows = history.build_rows()

    assert len(turns) == 1
    assert turns[0].trick_status == "failed"
    assert turns[0].attack_trace == "XX"
    assert len(rows) == 1
    assert rows[0].trick_validated == "XX"


def test_build_turns_marks_verified_switch_success_in_attack_trace() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.TURN_STARTED,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul Switch",
                "defender_ids": ["Denise"],
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.ATTACK_SUCCEEDED,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul Switch",
                "switch_normal_verification": "verified",
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
    rows = history.build_rows()

    assert turns[0].attack_trace == "V N(V)"
    assert rows[0].trick_validated == "V N(V)"


def test_build_turns_marks_verified_switch_failure_in_attack_trace() -> None:
    history = History()
    history.add_event(
        Event(
            name=EventName.TURN_STARTED,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul Switch",
                "defender_ids": ["Denise"],
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.ATTACK_FAILED_ATTEMPT,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul Switch",
                "attempts_left": 0,
                "switch_normal_verification": "failed",
            },
        )
    )
    history.add_event(
        Event(
            name=EventName.TURN_FAILED,
            payload={
                "attacker_id": "Stan",
                "trick": "Soul Switch",
                "next_attacker_id": "Denise",
            },
        )
    )

    turns = history.build_turns()
    rows = history.build_rows()

    assert turns[0].attack_trace == "V N(X)"
    assert rows[0].trick_validated == "V N(X)"
