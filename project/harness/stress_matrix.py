from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.scenario_loader import YAMLScenarioSource


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRESS_SCENARIOS_DIR = PROJECT_ROOT / "harness" / "scenarios" / "stress"
SETUP_DETAILS_BODY_TARGET = "setup_details.body_label"

STEP_ADD_THIRD_PLAYER = "add third player"
STEP_REMOVE_THIRD_PLAYER = "remove third player"
STEP_UNDO_ROSTER_ROUNDTRIP = "undo roster roundtrip"
STEP_OPEN_SETUP_DETAILS_IN_DUEL = "open setup details in duel"
STEP_ADD_FRANK = "add Frank"
STEP_LOAD_SAVED_TRANSITION = "load saved transition"
STEP_REMOVE_FRANK_AFTER_LOAD = "remove Frank after load"
STEP_OPEN_SETUP_DETAILS_AFTER_LOAD = "open setup details after load"
STEP_OPEN_SETUP_DETAILS_AFTER_REMOVAL = "open setup details after removal"


@dataclass(frozen=True)
class StressMatrixCase:
    case_id: str
    scenario_name: str
    preset_name: str
    player_names: tuple[str, ...]
    variant: str = "duel"
    joined_player_name: str = "Frank"

    @property
    def scenario_path(self) -> Path:
        return STRESS_SCENARIOS_DIR / self.scenario_name


STRESS_MATRIX_CASES: tuple[StressMatrixCase, ...] = (
    StressMatrixCase(
        case_id="load_engaged_turn__classic_skate_v8",
        scenario_name="load_engaged_turn_stress.yaml",
        preset_name="classic_skate_v8",
        player_names=("Stan", "Denise"),
    ),
    StressMatrixCase(
        case_id="load_engaged_turn__duel_long_open_v9_3",
        scenario_name="load_engaged_turn_stress.yaml",
        preset_name="duel_long_open_v9_3",
        player_names=("Stan", "Denise"),
    ),
    StressMatrixCase(
        case_id="load_engaged_turn__duel_synergy_strict_v10_1",
        scenario_name="load_engaged_turn_stress.yaml",
        preset_name="duel_synergy_strict_v10_1",
        player_names=("Stan", "Denise"),
    ),
    StressMatrixCase(
        case_id="load_engaged_turn__duel_verified_switch_v10_1",
        scenario_name="load_engaged_turn_stress.yaml",
        preset_name="duel_verified_switch_v10_1",
        player_names=("Stan", "Denise"),
    ),
    StressMatrixCase(
        case_id="undo_chain_recovery__classic_skate_v8",
        scenario_name="undo_chain_recovery_stress.yaml",
        preset_name="classic_skate_v8",
        player_names=("Stan", "Denise"),
    ),
    StressMatrixCase(
        case_id="undo_chain_recovery__duel_synergy_strict_v10_1",
        scenario_name="undo_chain_recovery_stress.yaml",
        preset_name="duel_synergy_strict_v10_1",
        player_names=("Stan", "Denise"),
    ),
    StressMatrixCase(
        case_id="undo_chain_recovery__duel_verified_switch_v10_1",
        scenario_name="undo_chain_recovery_stress.yaml",
        preset_name="duel_verified_switch_v10_1",
        player_names=("Stan", "Denise"),
    ),
    StressMatrixCase(
        case_id="consultation_undo__duel_short_strict_v9_3",
        scenario_name="consultation_undo_stress.yaml",
        preset_name="duel_short_strict_v9_3",
        player_names=("Stan", "Denise"),
    ),
    StressMatrixCase(
        case_id="roster_transition_roundtrip__battle_balanced_v9_3",
        scenario_name="roster_transition_roundtrip_stress.yaml",
        preset_name="battle_balanced_v9_3",
        player_names=("Stan", "Denise", "Alex"),
        variant="battle_roster",
    ),
    StressMatrixCase(
        case_id="mixed_save_load_roster__battle_long_open_v9_3",
        scenario_name="mixed_save_load_roster_stress.yaml",
        preset_name="battle_long_open_v9_3",
        player_names=("Stan", "Denise", "Alex"),
        variant="battle_mixed",
    ),
    StressMatrixCase(
        case_id="verified_switch_navigation_new_game__duel_verified_switch_v10_1",
        scenario_name="verified_switch_navigation_new_game_stress.yaml",
        preset_name="duel_verified_switch_v10_1",
        player_names=("Stan", "Denise"),
    ),
    StressMatrixCase(
        case_id="battle_multi_no_repetition_roster_navigation__battle_multi_no_rep_v10_1",
        scenario_name="battle_multi_no_repetition_roster_navigation_stress.yaml",
        preset_name="battle_multi_no_rep_v10_1",
        player_names=("Stan", "Denise"),
    ),
)


def discover_stress_matrix_cases() -> tuple[StressMatrixCase, ...]:
    return STRESS_MATRIX_CASES


def build_stress_matrix_scenario(
    case: StressMatrixCase,
    *,
    scenario_source: YAMLScenarioSource | None = None,
) -> dict[str, Any]:
    source = scenario_source or YAMLScenarioSource()
    scenario = deepcopy(source.load(case.scenario_path))
    metadata = scenario["metadata"]
    metadata["id"] = case.case_id
    metadata["title"] = f"{metadata['title']} [{case.preset_name}]"
    tags = metadata.setdefault("tags", [])
    if "matrix" not in tags:
        tags.append("matrix")
    if case.preset_name not in tags:
        tags.append(case.preset_name)

    scenario["setup"]["preset"] = case.preset_name
    scenario["setup"]["players"] = list(case.player_names)

    _rewrite_preset_selection(scenario, case.preset_name)
    _rewrite_setup_player_steps(scenario, case.player_names)
    _rewrite_setup_details_preset_expectations(scenario, case.preset_name)

    if case.variant == "battle_roster":
        _apply_battle_roster_variant(scenario, case)
    elif case.variant == "battle_mixed":
        _apply_battle_mixed_variant(scenario, case)

    return scenario


def _rewrite_preset_selection(scenario: dict[str, Any], preset_name: str) -> None:
    for step in scenario["steps"]:
        if (
            step.get("action") == "select_option"
            and step.get("target") == "setup.preset_combo"
        ):
            step["value"] = preset_name
            expect = step.get("expect") or {}
            text_equals = expect.get("text_equals") or {}
            if "setup.preset_combo" in text_equals:
                text_equals["setup.preset_combo"] = preset_name


def _rewrite_setup_player_steps(
    scenario: dict[str, Any],
    player_names: tuple[str, ...],
) -> None:
    steps = scenario["steps"]
    start_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("action") == "click"
        and step.get("target") == "setup.start_game_button"
    )

    retained_steps = [
        step
        for step in steps[:start_index]
        if not (
            step.get("action") in {"type", "select_option"}
            and isinstance(step.get("target"), str)
            and (
                step["target"].startswith("setup.player_name_entry.")
                or step["target"].startswith("setup.player_profile_combo.")
            )
        )
    ]

    player_steps: list[dict[str, Any]] = []
    for index, player_name in enumerate(player_names, start=1):
        ordinal = {
            1: "first",
            2: "second",
            3: "third",
            4: "fourth",
        }.get(index, f"player {index}")
        player_steps.append(
            {
                "name": f"select {ordinal} player profile",
                "action": "select_option",
                "target": f"setup.player_profile_combo.{index}",
                "value": player_name,
                "expect": {
                    "view": "setup",
                    "text_equals": {
                        f"setup.player_name_entry.{index}": player_name,
                    },
                },
            }
        )

    scenario["steps"] = retained_steps + player_steps + steps[start_index:]


def _rewrite_setup_details_preset_expectations(
    scenario: dict[str, Any],
    preset_name: str,
) -> None:
    for step in scenario["steps"]:
        expect = step.get("expect") or {}
        for key in ("text_equals", "text_contains"):
            mapping = expect.get(key) or {}
            body = mapping.get("setup_details.body_label")
            if isinstance(body, str) and "Preset:" in body:
                lines = [
                    f"Preset: {preset_name}" if line.startswith("Preset:") else line
                    for line in body.splitlines()
                ]
                mapping["setup_details.body_label"] = "\n".join(lines)


def _apply_battle_roster_variant(
    scenario: dict[str, Any],
    case: StressMatrixCase,
) -> None:
    first_three = case.player_names

    _set_step_expectation(
        scenario,
        STEP_ADD_THIRD_PLAYER,
        "score_cells",
        {
            "1,0": first_three[0].upper(),
            "1,2": first_three[1].upper(),
            "1,4": first_three[2].upper(),
            "1,6": case.joined_player_name.upper(),
        },
    )
    _set_step_expectation(
        scenario,
        STEP_REMOVE_THIRD_PLAYER,
        "score_cells",
        {
            "1,0": first_three[0].upper(),
            "1,2": first_three[1].upper(),
            "1,4": first_three[2].upper(),
        },
    )
    _set_step_expectation(
        scenario,
        STEP_UNDO_ROSTER_ROUNDTRIP,
        "score_cells",
        {
            "1,0": first_three[0].upper(),
            "1,2": first_three[1].upper(),
            "1,4": first_three[2].upper(),
            "1,6": case.joined_player_name.upper(),
        },
    )
    _replace_text_contains(
        scenario,
        STEP_OPEN_SETUP_DETAILS_IN_DUEL,
        SETUP_DETAILS_BODY_TARGET,
        "Structure: one_vs_one",
        "Structure: battle",
    )


def _apply_battle_mixed_variant(
    scenario: dict[str, Any],
    case: StressMatrixCase,
) -> None:
    first_three = case.player_names
    players_after_join = ", ".join(first_three + (case.joined_player_name,))

    _set_step_expectation(
        scenario,
        STEP_ADD_FRANK,
        "score_cells",
        {
            "1,0": first_three[0].upper(),
            "1,2": first_three[1].upper(),
            "1,4": first_three[2].upper(),
            "1,6": case.joined_player_name.upper(),
        },
    )
    _set_step_expectation(
        scenario,
        STEP_LOAD_SAVED_TRANSITION,
        "score_cells",
        {
            "1,0": first_three[0].upper(),
            "1,2": first_three[1].upper(),
            "1,4": first_three[2].upper(),
            "1,6": case.joined_player_name.upper(),
        },
    )
    _set_step_expectation(
        scenario,
        STEP_REMOVE_FRANK_AFTER_LOAD,
        "score_cells",
        {
            "1,0": first_three[0].upper(),
            "1,2": first_three[1].upper(),
            "1,4": first_three[2].upper(),
        },
    )
    _replace_text_contains(
        scenario,
        STEP_OPEN_SETUP_DETAILS_AFTER_LOAD,
        SETUP_DETAILS_BODY_TARGET,
        "Players: Stan, Denise, Frank",
        f"Players: {players_after_join}",
    )
    _replace_text_contains(
        scenario,
        STEP_OPEN_SETUP_DETAILS_AFTER_REMOVAL,
        SETUP_DETAILS_BODY_TARGET,
        "Structure: one_vs_one",
        "Structure: battle",
    )


def _set_step_expectation(
    scenario: dict[str, Any],
    step_name: str,
    expect_key: str,
    value: dict[str, str],
) -> None:
    step = _get_step(scenario, step_name)
    expect = step.setdefault("expect", {})
    expect[expect_key] = value


def _replace_text_contains(
    scenario: dict[str, Any],
    step_name: str,
    target_key: str,
    old_value: str,
    new_value: str,
) -> None:
    step = _get_step(scenario, step_name)
    expect = step.setdefault("expect", {})
    mapping = expect.setdefault("text_contains", {})
    if mapping.get(target_key) == old_value:
        mapping[target_key] = new_value


def _get_step(scenario: dict[str, Any], step_name: str) -> dict[str, Any]:
    for step in scenario["steps"]:
        if step.get("name") == step_name:
            return step
    raise ValueError(f"Unknown matrix step: {step_name}")
