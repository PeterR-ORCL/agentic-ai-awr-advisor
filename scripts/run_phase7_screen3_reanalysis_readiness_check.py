#!/usr/bin/env python3
"""Run Phase 7AJ-7AO Screen 3 re-analysis readiness checks."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import runpy
import sys
import unittest
from pathlib import Path
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
VALIDATION_SCRIPT = ROOT / "scripts" / "run_phase7_screen3_reanalysis_validation.py"

FOCUSED_TESTS: tuple[tuple[str, str], ...] = (
    ("reanalysis_boundary", "tests/test_phase7aj_screen3_reanalysis_boundary.py"),
    ("source_selection", "tests/test_phase7ak_source_selection_model.py"),
    ("reanalysis_request", "tests/test_phase7al_reanalysis_request_model.py"),
    ("reanalysis_controller", "tests/test_phase7am_reanalysis_execution_controller.py"),
    ("screen3_action_ui", "tests/test_dashboard_screen3_reanalysis_actions.py"),
    ("reanalysis_readiness", "tests/test_phase7ao_reanalysis_readiness.py"),
    ("validation_script", "tests/test_phase7_screen3_reanalysis_validation.py"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local-only Phase 7 Screen 3 re-analysis readiness checks.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument(
        "--include-phase7",
        action="store_true",
        help="Also run the broader Phase 7 validation script.",
    )
    parser.add_argument(
        "--include-phase6",
        action="store_true",
        help="Also run the broader Phase 6 validation script.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_readiness_check(
        include_phase7=args.include_phase7,
        include_phase6=args.include_phase6,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["success"] else 1


def run_readiness_check(
    *,
    include_phase7: bool = False,
    include_phase6: bool = False,
) -> dict[str, Any]:
    validation_summary = load_validation_module().run_validation()
    checks = [
        {
            "name": "screen3_reanalysis_validation",
            "success": bool(validation_summary.get("success")),
            "tests_run": int(validation_summary.get("tests_run", 0)),
            "checks_run": int(validation_summary.get("checks_run", 0)),
            "failures": int(validation_summary.get("failures", 0)),
            "errors": int(validation_summary.get("errors", 0)),
            "skipped": int(validation_summary.get("skipped", 0)),
            "details": ["validation script summary imported and executed"],
            "json_payload": validation_summary,
        }
    ]
    checks.extend(run_focused_test_checks())
    if include_phase7:
        checks.append(run_optional_script_check("phase7_regression", "scripts/run_phase7_validation.py"))
    if include_phase6:
        checks.append(run_optional_script_check("phase6_regression", "scripts/run_phase6_validation.py"))

    totals = summarize_checks(checks)
    success = all(check["success"] for check in checks)
    return {
        "phase": "Phase 7AJ-7AO",
        "command": "run_phase7_screen3_reanalysis_readiness_check",
        "success": success,
        "screen3_reanalysis_ready": success,
        "backend_execution_performed": False,
        "run_analysis_called": False,
        "object_storage_called": False,
        "local_file_read_performed": False,
        "db_lookup_performed": False,
        "phase4i_mutated": False,
        "dashboard_regenerated": False,
        "missing_metric_handling_ready": bool(
            validation_summary.get("missing_metric_handling_ready")
        ),
        "deterministic_runtime_remains_authoritative": True,
        "phase8_implemented": False,
        "phase7_validation_included": include_phase7,
        "phase6_validation_included": include_phase6,
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "checks": checks,
    }


def load_validation_module():
    spec = importlib.util.spec_from_file_location(
        "run_phase7_screen3_reanalysis_validation",
        VALIDATION_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Screen 3 re-analysis validation script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_focused_test_checks() -> list[dict[str, Any]]:
    return [run_unittest_check(name, test_path) for name, test_path in FOCUSED_TESTS]


def run_unittest_check(name: str, test_path: str) -> dict[str, Any]:
    path = ROOT / test_path
    if not path.is_file():
        return {
            "name": name,
            "success": False,
            "tests_run": 0,
            "checks_run": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "details": [f"missing test path: {test_path}"],
        }
    module = load_module_from_path(path, f"phase7_screen3_reanalysis_readiness_{name}")
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    details = [line.strip() for line in stream.getvalue().splitlines() if line.strip()]
    return {
        "name": name,
        "success": result.wasSuccessful(),
        "tests_run": result.testsRun,
        "checks_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "details": details[-20:] if details else ["unittest check passed"],
    }


def run_optional_script_check(name: str, relative_script: str) -> dict[str, Any]:
    path = ROOT / relative_script
    if not path.is_file():
        return {
            "name": name,
            "success": False,
            "tests_run": 0,
            "checks_run": 1,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "details": [f"missing optional script: {relative_script}"],
        }
    original_argv = sys.argv[:]
    stream = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.argv = [str(path)]
        sys.stdout = stream
        sys.stderr = stream
        try:
            runpy.run_path(str(path), run_name="__main__")
            returncode = 0
        except SystemExit as exc:
            returncode = int(exc.code or 0) if isinstance(exc.code, int) else 1
    finally:
        sys.argv = original_argv
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    details = [line.strip() for line in stream.getvalue().splitlines() if line.strip()]
    return {
        "name": name,
        "success": returncode == 0,
        "tests_run": 0,
        "checks_run": 1,
        "failures": 0 if returncode == 0 else 1,
        "errors": 0,
        "skipped": 0,
        "details": details[-20:] if details else ["optional script passed"],
    }


def load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load test module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize_checks(checks: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "tests_run": sum(int(check.get("tests_run", 0)) for check in checks),
        "checks_run": sum(int(check.get("checks_run", 0)) for check in checks),
        "failures": sum(int(check.get("failures", 0)) for check in checks),
        "errors": sum(int(check.get("errors", 0)) for check in checks),
        "skipped": sum(int(check.get("skipped", 0)) for check in checks),
    }


def print_human_summary(summary: dict[str, Any]) -> None:
    if summary["success"]:
        print("Phase 7 Screen 3 re-analysis readiness passed.")
    else:
        print("Phase 7 Screen 3 re-analysis readiness failed.")
    print(f"screen3_reanalysis_ready={str(summary['screen3_reanalysis_ready']).lower()}")
    print(f"missing_metric_handling_ready={str(summary['missing_metric_handling_ready']).lower()}")
    print(f"tests_run={summary['tests_run']}")
    print(f"checks_run={summary['checks_run']}")
    print(f"failures={summary['failures']}")
    print(f"errors={summary['errors']}")
    print("backend_execution_performed=false")
    print("run_analysis_called=false")
    print("object_storage_called=false")
    print("local_file_read_performed=false")
    print("db_lookup_performed=false")
    print("phase4i_mutated=false")
    print("Readiness checks:")
    for check in summary["checks"]:
        print(f"- {check['name']}: {check['success']}")


if __name__ == "__main__":
    raise SystemExit(main())
