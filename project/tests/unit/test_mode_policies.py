from config.match_policies import (
    DefenderOrderPolicy,
    InitialTurnOrderPolicy,
    MatchPolicies,
)
from core.player import Player
from core.state import GameState
from core.types import Phase
from modes.battle import BattleMode
from modes.mode_factory import ModeFactory


def test_mode_factory_passes_policies_to_battle_mode() -> None:
    policies = MatchPolicies(
        initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
        defender_order=DefenderOrderPolicy.REVERSE_TURN_ORDER,
    )

    mode = ModeFactory().create("battle", policies)

    assert mode.policies == policies


def test_battle_mode_uses_fixed_initial_order_when_policy_requires_it() -> None:
    mode = BattleMode(
        MatchPolicies(initial_turn_order=InitialTurnOrderPolicy.FIXED_PLAYER_ORDER)
    )
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
            Player(id="p3", name="Player 3"),
        ]
    )

    mode.initialize_game(state)

    assert state.phase == Phase.TURN
    assert state.turn_order == [0, 1, 2]
    assert state.attacker_index == 0


def test_battle_mode_reverses_defender_order_when_policy_requires_it() -> None:
    mode = BattleMode(
        MatchPolicies(defender_order=DefenderOrderPolicy.REVERSE_TURN_ORDER)
    )
    state = GameState(
        players=[
            Player(id="p1", name="Player 1"),
            Player(id="p2", name="Player 2"),
            Player(id="p3", name="Player 3"),
        ],
        turn_order=[0, 1, 2],
        attacker_index=0,
    )

    defender_indices = mode.build_defender_indices(state)

    assert defender_indices == [2, 1]
