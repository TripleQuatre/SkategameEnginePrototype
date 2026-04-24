from __future__ import annotations

import argparse
from pathlib import Path
import sys

from interfaces.gui.gui_app import GUIApp
from harness import (
    BoundedRandomScenarioBuilder,
    GUIHarnessRunner,
    GUIOracleEngine,
    StructuredGUIHarnessReporter,
    TkGUIHarnessDriver,
    TkGUIHarnessObserver,
    YAMLScenarioSource,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SCENARIOS_DIR = PROJECT_ROOT / "harness" / "scenarios" / "reference"


def build_runner(*, withdraw_on_launch: bool = True) -> GUIHarnessRunner:
    return GUIHarnessRunner(
        scenario_source=YAMLScenarioSource(),
        driver=TkGUIHarnessDriver(withdraw_on_launch=withdraw_on_launch),
        observer=TkGUIHarnessObserver(),
        oracle_engine=GUIOracleEngine(),
        reporter=StructuredGUIHarnessReporter(),
    )


def discover_reference_scenarios() -> list[Path]:
    return sorted(REFERENCE_SCENARIOS_DIR.glob("*.yaml"))


def run_scenarios(
    scenario_paths: list[Path],
    *,
    withdraw_on_launch: bool = True,
) -> int:
    if not scenario_paths:
        print("No GUI harness scenarios found.")
        return 1

    exit_code = 0
    for scenario_path in scenario_paths:
        runner = build_runner(withdraw_on_launch=withdraw_on_launch)
        report = runner.run(scenario_path)
        status = "PASS" if report.success else "FAIL"
        print(f"[{status}] {report.scenario_id} ({scenario_path})")

        if not report.success:
            exit_code = 1
            if report.failure is not None:
                print(f"  step {report.failure.step_index}: {report.failure.step_name}")
                print(f"  error: {report.failure.message}")
                print(f"  expected: {report.failure.expected}")
                print(f"  observed: {report.failure.observed}")
                if report.failure.screenshot_path is not None:
                    print(f"  artifact: {report.failure.screenshot_path.as_posix()}")

    return exit_code


def run_random_bounded_scenario(
    *,
    seed: int,
    max_steps: int,
    withdraw_on_launch: bool = True,
) -> int:
    runner = build_runner(withdraw_on_launch=withdraw_on_launch)
    scenario = BoundedRandomScenarioBuilder(
        seed=seed,
        max_steps=max_steps,
    ).build()
    report = runner.run_scenario(scenario)
    status = "PASS" if report.success else "FAIL"
    print(f"[{status}] {report.scenario_id} (seed={seed}, max_steps={max_steps})")

    if not report.success and report.failure is not None:
        print(f"  step {report.failure.step_index}: {report.failure.step_name}")
        print(f"  error: {report.failure.message}")
        print(f"  expected: {report.failure.expected}")
        print(f"  observed: {report.failure.observed}")
        if report.failure.screenshot_path is not None:
            print(f"  artifact: {report.failure.screenshot_path.as_posix()}")

    print(f"  sequence_length: {len(report.debug_payload.get('sequence', []))}")
    return 0 if report.success else 1


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Skategame GUI harness scenarios.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--scenario",
        type=Path,
        help="Path to one YAML scenario to run.",
    )
    mode.add_argument(
        "--reference-suite",
        action="store_true",
        help="Run every reference scenario.",
    )
    mode.add_argument(
        "--random-bounded",
        action="store_true",
        help="Run one bounded semi-random scenario.",
    )
    parser.add_argument(
        "--show-window",
        action="store_true",
        help="Do not withdraw the Tk window while running scenarios.",
    )
    parser.add_argument(
        "--saves-dir",
        type=Path,
        default=PROJECT_ROOT / "local_tmp" / "harness_cli_saves",
        help="Directory used by GUI save actions during harness runs.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Seed used by --random-bounded.",
    )
    parser.add_argument(
        "--max-random-steps",
        type=int,
        default=20,
        help="Maximum number of steps for --random-bounded.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    args.saves_dir.mkdir(parents=True, exist_ok=True)
    GUIApp.SAVES_DIR = args.saves_dir

    if args.random_bounded:
        return run_random_bounded_scenario(
            seed=args.seed,
            max_steps=args.max_random_steps,
            withdraw_on_launch=not args.show_window,
        )

    scenario_paths = discover_reference_scenarios() if args.reference_suite else [args.scenario]
    return run_scenarios(
        scenario_paths,
        withdraw_on_launch=not args.show_window,
    )


if __name__ == "__main__":
    raise SystemExit(main())
