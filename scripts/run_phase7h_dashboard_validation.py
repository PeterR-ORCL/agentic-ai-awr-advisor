#!/usr/bin/env python3
"""Run local Phase 7H dashboard interactivity validation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PY_COMPILE_TARGETS = (
    "src/reporting/html_dashboard.py",
    "tests/test_dashboard_interactivity_phase7h_acceptance.py",
    "tests/test_dashboard_cross_screen_selection_propagation.py",
    "tests/test_dashboard_screen6_fleet_governance_learning_exploration.py",
    "tests/test_dashboard_screen1_governance_parser_exploration.py",
    "tests/test_dashboard_screen5_recommendation_action_exploration.py",
    "tests/test_dashboard_screen4_historical_review_exploration.py",
    "tests/test_dashboard_screen2_diagnostic_exploration.py",
    "tests/test_dashboard_screen3_control_center.py",
    "tests/test_dashboard_interactivity_foundation.py",
)

UNITTEST_MODULES = (
    "tests.test_dashboard_interactivity_phase7h_acceptance",
    "tests.test_dashboard_cross_screen_selection_propagation",
    "tests.test_dashboard_screen6_fleet_governance_learning_exploration",
    "tests.test_dashboard_screen1_governance_parser_exploration",
    "tests.test_dashboard_screen5_recommendation_action_exploration",
    "tests.test_dashboard_screen4_historical_review_exploration",
    "tests.test_dashboard_screen2_diagnostic_exploration",
    "tests.test_dashboard_screen3_control_center",
    "tests.test_dashboard_interactivity_foundation",
    "tests.test_dashboard_learning_visibility",
    "tests.test_learning_governance_bridge",
    "tests.test_semantic_candidate_context",
    "tests.test_learning_candidate_engine",
    "tests.test_learning_candidate_model",
    "tests.test_outcome_pattern_miner",
    "tests.test_phase7_learning_boundary",
)


def run_command(args: tuple[str, ...]) -> int:
    print("$ " + " ".join(args))
    completed = subprocess.run(args, cwd=ROOT, check=False)
    return completed.returncode


def main() -> int:
    failures: list[tuple[str, int]] = []

    for target in PY_COMPILE_TARGETS:
        path = ROOT / target
        if not path.exists():
            failures.append((f"missing: {target}", 1))
            continue
        return_code = run_command((sys.executable, "-m", "py_compile", target))
        if return_code:
            failures.append((f"py_compile {target}", return_code))

    return_code = run_command((sys.executable, "-m", "unittest", *UNITTEST_MODULES))
    if return_code:
        failures.append(("phase7h unittest suite", return_code))

    print()
    if failures:
        print("Phase 7H dashboard validation failed:")
        for label, return_code in failures:
            print(f"- {label}: {return_code}")
        return 1

    print("Phase 7H dashboard validation passed.")
    print(f"Compiled files: {len(PY_COMPILE_TARGETS)}")
    print(f"Unittest modules: {len(UNITTEST_MODULES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
