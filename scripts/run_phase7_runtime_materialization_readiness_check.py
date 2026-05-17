#!/usr/bin/env python3
"""Run local Phase 7BU-7BZ runtime materialization readiness checks."""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]


FOCUSED_TESTS: tuple[tuple[str, str], ...] = (
    ("governed_workflow_persistence", "tests.test_phase7bu_governed_workflow_persistence"),
    ("status_transition_execution", "tests.test_phase7bu_status_transition_execution"),
    ("parser_runtime_update", "tests.test_phase7bv_parser_runtime_update_path"),
    ("scoring_runtime_activation", "tests.test_phase7bw_scoring_runtime_activation"),
    (
        "recommendation_runtime_activation",
        "tests.test_phase7bx_recommendation_runtime_activation",
    ),
    ("ml_runtime_eligibility", "tests.test_phase7by_ml_runtime_eligibility"),
)


READINESS_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7_runtime_materialization_validation_matrix.md",
    "docs/architecture/phase7_runtime_materialization_readiness.md",
    "docs/architecture/phase7_runtime_materialization_release_certification.md",
    "docs/architecture/phase7_runtime_materialization_operational_checklist.md",
)


README_LINKS: tuple[str, ...] = (
    "phase7_runtime_materialization_validation_matrix.md",
    "phase7_runtime_materialization_readiness.md",
    "phase7_runtime_materialization_release_certification.md",
    "phase7_runtime_materialization_operational_checklist.md",
)


FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "oracledb",
    "cx_Oracle",
    "sqlite3",
    "requests",
    "httpx",
    "urllib",
    "socket",
    "http.client",
    "oci",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local-only Phase 7BU-7BZ runtime materialization readiness.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument(
        "--include-phase7",
        action="store_true",
        help="Optionally run the existing Phase 7 final readiness check.",
    )
    parser.add_argument(
        "--include-phase6",
        action="store_true",
        help="Optionally run the existing Phase 6 readiness check.",
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
    checks: list[dict[str, Any]] = [
        run_command_check(
            "runtime_materialization_validation",
            (sys.executable, "scripts/run_phase7_runtime_materialization_validation.py"),
        ),
        run_command_check(
            "runtime_materialization_validation_json",
            (
                sys.executable,
                "scripts/run_phase7_runtime_materialization_validation.py",
                "--json",
            ),
            expect_json=True,
        ),
    ]
    for name, module_name in FOCUSED_TESTS:
        checks.append(
            run_command_check(
                f"{name}_tests",
                (sys.executable, "-m", "unittest", module_name),
            )
        )
    checks.extend(
        [
            check_required_paths("runtime_materialization_readiness_docs", READINESS_DOCS),
            check_readme_links(),
            check_readiness_script_imports(),
        ]
    )
    if include_phase7:
        checks.append(
            run_command_check(
                "phase7_regression",
                (sys.executable, "scripts/run_phase7_final_readiness_check.py"),
            )
        )
    if include_phase6:
        checks.append(
            run_command_check(
                "phase6_regression",
                (sys.executable, "scripts/run_phase6_readiness_check.py"),
            )
        )

    checks_by_name = {check["name"]: check for check in checks}
    validation_json = checks_by_name["runtime_materialization_validation_json"].get(
        "json_payload",
        {},
    )
    validation_groups = {
        group.get("name"): bool(group.get("success"))
        for group in validation_json.get("validation_groups", [])
        if isinstance(group, dict)
    }

    readiness_categories = {
        "governed_workflow_persistence": validation_groups.get(
            "governed_workflow_persistence",
            False,
        )
        and checks_by_name["governed_workflow_persistence_tests"]["success"],
        "status_transition_execution": validation_groups.get(
            "status_transition_execution",
            False,
        )
        and checks_by_name["status_transition_execution_tests"]["success"],
        "parser_runtime_update": validation_groups.get("parser_runtime_update", False)
        and checks_by_name["parser_runtime_update_tests"]["success"],
        "scoring_runtime_activation": validation_groups.get(
            "scoring_runtime_activation",
            False,
        )
        and checks_by_name["scoring_runtime_activation_tests"]["success"],
        "recommendation_runtime_activation": validation_groups.get(
            "recommendation_runtime_activation",
            False,
        )
        and checks_by_name["recommendation_runtime_activation_tests"]["success"],
        "ml_runtime_eligibility": validation_groups.get("ml_runtime_eligibility", False)
        and checks_by_name["ml_runtime_eligibility_tests"]["success"],
        "runtime_isolation": (
            validation_groups.get("import_isolation", False)
            and validation_groups.get("runtime_safety", False)
        ),
        "documentation_complete": (
            validation_groups.get("documentation", False)
            and checks_by_name["runtime_materialization_readiness_docs"]["success"]
            and checks_by_name["readme_links"]["success"]
        ),
        "phase7_regression": None,
        "phase6_regression": None,
    }
    if include_phase7:
        readiness_categories["phase7_regression"] = checks_by_name[
            "phase7_regression"
        ]["success"]
    if include_phase6:
        readiness_categories["phase6_regression"] = checks_by_name[
            "phase6_regression"
        ]["success"]

    required_categories = [
        value
        for key, value in readiness_categories.items()
        if key not in ("phase7_regression", "phase6_regression")
    ]
    if include_phase7:
        required_categories.append(bool(readiness_categories["phase7_regression"]))
    if include_phase6:
        required_categories.append(bool(readiness_categories["phase6_regression"]))

    totals = summarize_checks(checks)
    success = all(check["success"] for check in checks) and all(required_categories)
    return {
        "phase": "Phase 7BU-7BZ",
        "command": "run_phase7_runtime_materialization_readiness_check",
        "runtime_materialization_ready": success,
        "success": success,
        "readiness_categories": readiness_categories,
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "db_persistence_performed": False,
        "status_transition_performed": False,
        "runtime_active": False,
        "phase4i_mutated": False,
        "deterministic_runtime_remains_authoritative": True,
        "database_dependency": False,
        "network_dependency": False,
        "oracle_agent_memory_dependency": False,
        "phase7_regression_included": include_phase7,
        "phase6_regression_included": include_phase6,
        "checks": checks,
    }


def run_command_check(
    name: str,
    args: tuple[str, ...],
    *,
    expect_json: bool = False,
) -> dict[str, Any]:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    check: dict[str, Any] = {
        "name": name,
        "success": completed.returncode == 0,
        "tests_run": 0,
        "checks_run": 1,
        "failures": 0 if completed.returncode == 0 else 1,
        "errors": 0,
        "skipped": 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
    if expect_json and completed.returncode == 0:
        try:
            check["json_payload"] = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            check["success"] = False
            check["failures"] = 1
            check["stderr"] = f"invalid json: {exc}"
    return check


def check_required_paths(name: str, paths: tuple[str, ...]) -> dict[str, Any]:
    missing = [relative_path for relative_path in paths if not (ROOT / relative_path).is_file()]
    return {
        "name": name,
        "success": not missing,
        "tests_run": 0,
        "checks_run": len(paths),
        "failures": len(missing),
        "errors": 0,
        "skipped": 0,
        "details": missing,
    }


def check_readme_links() -> dict[str, Any]:
    readme = ROOT / "docs/architecture/README.md"
    text = readme.read_text(encoding="utf-8", errors="ignore")
    missing = [link for link in README_LINKS if link not in text]
    return {
        "name": "readme_links",
        "success": not missing,
        "tests_run": 0,
        "checks_run": len(README_LINKS),
        "failures": len(missing),
        "errors": 0,
        "skipped": 0,
        "details": missing,
    }


def check_readiness_script_imports() -> dict[str, Any]:
    path = ROOT / "scripts/run_phase7_runtime_materialization_readiness_check.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    unsafe = sorted(
        imported
        for imported in imports
        if any(imported == blocked or imported.startswith(f"{blocked}.") for blocked in FORBIDDEN_IMPORTS)
    )
    return {
        "name": "readiness_script_imports",
        "success": not unsafe,
        "tests_run": 0,
        "checks_run": len(imports),
        "failures": len(unsafe),
        "errors": 0,
        "skipped": 0,
        "details": unsafe,
    }


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
        print("Phase 7 runtime materialization readiness passed.")
    else:
        print("Phase 7 runtime materialization readiness failed.")
    print(f"runtime_materialization_ready={str(summary['runtime_materialization_ready']).lower()}")
    print(f"checks_run={summary['checks_run']}")
    print(f"failures={summary['failures']}")
    print(f"errors={summary['errors']}")
    for category, value in summary["readiness_categories"].items():
        print(f"{category}={value}")


if __name__ == "__main__":
    raise SystemExit(main())
