from __future__ import annotations

import random
from typing import Any


class BoundedRandomScenarioBuilder:
    def __init__(self, *, seed: int, max_steps: int = 20) -> None:
        if max_steps < 6:
            raise ValueError("max_steps must be at least 6 for a bounded random scenario.")
        self.seed = seed
        self.max_steps = max_steps
        self._random = random.Random(seed)

    def build(self) -> dict[str, Any]:
        scenario_kind = self._random.choice(self._available_scenario_kinds())

        steps = [
            {
                "name": "launch app",
                "action": "launch_app",
                "expect": {
                    "view": "setup",
                    "status_text_equals": "Configure the game to begin.",
                },
            }
        ]

        if scenario_kind.startswith("preset"):
            steps.extend(self._preset_setup_steps(scenario_kind))
        else:
            steps.extend(self._custom_setup_steps(scenario_kind))

        steps.append(
            {
                "name": "start game",
                "action": "click",
                "target": "setup.start_game_button",
                "expect": {
                    "view": "match",
                    "status_text_equals": "Game started.",
                    "button_states": {
                        "match.add_player_button": "normal",
                    },
                },
            }
        )

        flow_fragments = [
            self._trick_fragment(),
            self._setup_details_fragment(),
            self._history_fragment(),
            self._save_fragment(),
            self._undo_fragment(),
        ]
        self._random.shuffle(flow_fragments)

        for fragment in flow_fragments:
            if len(steps) + len(fragment) + 1 > self.max_steps:
                continue
            steps.extend(fragment)

        steps.append({"name": "shutdown app", "action": "shutdown_app"})

        return {
            "metadata": {
                "id": f"random_bounded_seed_{self.seed}",
                "title": "Bounded random GUI exploration",
                "tags": ["random", "bounded", "v9_2"],
                "seed": self.seed,
                "kind": scenario_kind,
                "max_steps": self.max_steps,
            },
            "setup": {
                "mode": "preset" if scenario_kind.startswith("preset") else "custom",
            },
            "steps": steps,
        }

    def _preset_setup_steps(self, scenario_kind: str) -> list[dict[str, Any]]:
        preset = (
            self._random.choice(["battle_common_v8", "battle_hardcore_v8"])
            if scenario_kind == "preset_battle"
            else self._random.choice(["classic_skate_v8", "blade_open_v8"])
        )
        player_names = (
            ["Stan", "Denise", "Frank"]
            if scenario_kind == "preset_battle"
            else ["Stan", "Denise"]
        )
        steps = [
            {
                "name": f"select preset {preset}",
                "action": "select_option",
                "target": "setup.preset_combo",
                "value": preset,
                "expect": {
                    "view": "setup",
                    "text_equals": {"setup.preset_combo": preset},
                },
            }
        ]
        if len(player_names) == 3:
            steps.extend(self._set_player_count_steps(3))
        steps.extend(self._player_profile_steps(player_names))
        return steps

    def _available_scenario_kinds(self) -> list[str]:
        kinds = ["preset_one_vs_one"]
        if self.max_steps >= 7:
            kinds.append("custom_one_vs_one")
        if self.max_steps >= 8:
            kinds.append("preset_battle")
        if self.max_steps >= 9:
            kinds.append("custom_battle")
        return kinds

    def _custom_setup_steps(self, scenario_kind: str) -> list[dict[str, Any]]:
        player_names = (
            ["Stan", "Denise", "Frank"]
            if scenario_kind == "custom_battle"
            else ["Stan", "Denise"]
        )
        word = self._random.choice(["SKATE", "BLADE", "OUT"])
        steps = [
            {
                "name": "switch to custom mode",
                "action": "click",
                "target": "setup.mode_custom_radiobutton",
                "expect": {"view": "setup"},
            }
        ]
        if len(player_names) == 3:
            steps.extend(self._set_player_count_steps(3))
        steps.extend(self._player_profile_steps(player_names))
        steps.append(
            {
                "name": f"set word {word}",
                "action": "type",
                "target": "setup.word_entry",
                "value": word,
                "expect": {
                    "view": "setup",
                    "text_equals": {"setup.word_entry": word},
                },
            }
        )
        return steps

    def _set_player_count_steps(self, player_count: int) -> list[dict[str, Any]]:
        return [
            {
                "name": f"set player count {player_count}",
                "action": "type",
                "target": "setup.player_count_spinbox",
                "value": str(player_count),
                "expect": {"view": "setup"},
            }
        ]

    def _player_profile_steps(self, player_names: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "name": f"select player profile {index}",
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
            for index, player_name in enumerate(player_names, start=1)
        ]

    def _trick_fragment(self) -> list[dict[str, Any]]:
        query, label = self._random.choice(
            [
                ("soul", "Soul"),
                ("switch soul", "Soul Switch"),
                ("negative soul", "Negative Soul"),
            ]
        )
        return [
            {
                "name": f"search {label}",
                "action": "type",
                "target": "match.trick_entry",
                "value": query,
                "expect": {
                    "view": "match",
                    "dropdown_contains": [label],
                },
            },
            {
                "name": f"select {label}",
                "action": "select_suggestion",
                "target": "match.trick_suggestions_listbox",
                "value": label,
                "expect": {
                    "view": "match",
                    "status_text_equals": "Valid trick selected.",
                    "button_states": {
                        "match.confirm_trick_button": "normal",
                    },
                },
            },
            {
                "name": f"confirm {label}",
                "action": "click",
                "target": "match.confirm_trick_button",
                "expect": {
                    "view": "match",
                    "text_equals": {"match.trick_label": f"Trick: {label}"},
                },
            },
        ]

    def _setup_details_fragment(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "open setup details",
                "action": "click",
                "target": "match.setup_details_button",
                "expect": {
                    "view": "setup_details",
                    "text_contains": {
                        "setup_details.body_label": "Dictionary profile: inline_primary_grind",
                    },
                },
            },
            {
                "name": "back from setup details",
                "action": "click",
                "target": "setup_details.back_to_game_button",
                "expect": {"view": "match"},
            },
        ]

    def _history_fragment(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "open history",
                "action": "click",
                "target": "match.history_button",
                "expect": {
                    "view": "history",
                    "button_states": {"history.back_to_game_button": "normal"},
                },
            },
            {
                "name": "back from history",
                "action": "click",
                "target": "history.back_to_game_button",
                "expect": {"view": "match"},
            },
        ]

    def _save_fragment(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "save game",
                "action": "click",
                "target": "match.save_button",
                "expect": {
                    "view": "match",
                    "status_text_contains": "Game saved to",
                },
            }
        ]

    def _undo_fragment(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "undo one step",
                "action": "click",
                "target": "match.undo_button",
                "expect": {
                    "status_text_contains": "Undo successful",
                },
            }
        ]
