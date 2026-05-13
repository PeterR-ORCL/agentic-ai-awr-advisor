#!/usr/bin/env python3
"""Run local Phase 7S-7Z ML / adaptive scoring readiness checks."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]

READINESS_CATEGORY_KEYS: tuple[str, ...] = (
    "ml_boundary",
    "feature_label_dataset",
    "trend_aware_scoring",
    "shadow_ml_model_interface",
    "ml_training_backtesting",
    "ml_explainability",
    "ml_model_registry",
    "runtime_isolation",
    "documentation_complete",
    "materialization_regression",
    "phase7_regression",
    "phase6_regression",
)

ML_GROUPS: tuple[str, ...] = (
    "ml_boundary",
    "feature_label_dataset",
    "trend_aware_scoring",
    "shadow_ml_model_interface",
    "ml_training_backtesting",
    "ml_explainability",
    "ml_model_registry",
)

REQUIRED_READINESS_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7_ml_validation_matrix.md",
    "docs/architecture/phase7_ml_readiness.md",
    "docs/architecture/phase7_ml_release_certification.md",
    "docs/architecture/phase7_ml_operational_checklist.md",
)

REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/run_phase7_ml_validation.py",
    "scripts/run_phase7_ml_readiness_check.py",
    "scripts/run_phase7_materialization_validation.py",
    "scripts/run_phase7_materialization_readiness_check.py",
    "scripts/run_phase7_validation.py",
    "scripts/run_phase7_readiness_check.py",
    "scripts/run_phase7h_dashboard_validation.py",
    "scripts/awr_memory_cli.py",
)

SAFETY_CLAIMS: tuple[str, ...] = (
    "ml_ready=true only when all checks pass",
    "7s-7y are non-runtime-active",
    "no runtime scoring changes are applied",
    "model registry does not deploy models",
    "deterministic scoring remains authoritative",
    "deterministic runtime remains authoritative",
    "runtime_active=false",
    "runtime_influence=false",
    "runtime_influence_granted=false",
    "runtime_eligibility_granted=false",
    "phase 8 is not implemented",
)

FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "oracledb",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "oci",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local-only Phase 7S-7Z ML / adaptive scoring readiness checks.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument(
        "--include-phase6",
        action="store_true",
        help="Also run Phase 6 regression validation when available.",
    )
    parser.add_argument(
        "--include-phase7",
        action="store_true",
        help="Accepted for explicitness; Phase 7 regression checks run by default.",
    )
    parser.add_argument(
        "--include-materialization",
        action="store_true",
        help="Accepted for explicitness; materialization regression checks run by default.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_readiness_check(include_phase6=args.include_phase6)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["success"] else 1


def run_readiness_check(*, include_phase6: bool = False) -> dict[str, Any]:
    checks = run_command_checks(include_phase6=include_phase6)
    checks.extend(
        [
            check_required_paths("required_ml_readiness_docs", REQUIRED_READINESS_DOCS),
            check_required_paths("required_ml_scripts", REQUIRED_SCRIPTS),
            check_safety_claims(),
            check_readiness_script_imports(),
        ]
    )
    checks_by_name = {check["name"]: check for check in checks}

    validation_json = checks_by_name["ml_validation_json"].get("json_payload") or {}
    validation_groups = validation_json.get("validation_groups", [])
    groups_by_name = {
        group.get("name"): group
        for group in validation_groups
        if isinstance(group, dict)
    }

    documentation_complete = (
        group_success(groups_by_name, "documentation")
        and checks_by_name["required_ml_readiness_docs"]["success"]
        and checks_by_name["ml_docs_readiness_tests"]["success"]
        and checks_by_name["required_ml_safety_claims"]["success"]
    )
    runtime_isolation = (
        group_success(groups_by_name, "import_isolation")
        and group_success(groups_by_name, "runtime_safety")
        and checks_by_name["readiness_script_dependency_safety"]["success"]
    )
    materialization_regression = (
        checks_by_name["materialization_validation"]["success"]
        and checks_by_name["materialization_readiness"]["success"]
    )
    phase7_regression = (
        checks_by_name["phase7_validation"]["success"]
        and checks_by_name["phase7_readiness"]["success"]
        and checks_by_name["phase7h_dashboard_validation"]["success"]
        and checks_by_name["phase7i_cli_validation"]["success"]
    )

    phase6_regression = None
    if include_phase6:
        phase6_regression = checks_by_name["phase6_regression"]["success"]

    readiness_categories = {
        "ml_boundary": group_success(groups_by_name, "ml_boundary"),
        "feature_label_dataset": group_success(groups_by_name, "feature_label_dataset"),
        "trend_aware_scoring": group_success(groups_by_name, "trend_aware_scoring"),
        "shadow_ml_model_interface": group_success(groups_by_name, "shadow_ml_model_interface"),
        "ml_training_backtesting": group_success(groups_by_name, "ml_training_backtesting"),
        "ml_explainability": group_success(groups_by_name, "ml_explainability"),
        "ml_model_registry": group_success(groups_by_name, "ml_model_registry"),
        "runtime_isolation": runtime_isolation,
        "documentation_complete": documentation_complete,
        "materialization_regression": materialization_regression,
        "phase7_regression": phase7_regression,
        "phase6_regression": phase6_regression,
    }

    required_categories = [
        value
        for key, value in readiness_categories.items()
        if key != "phase6_regression"
    ]
    if include_phase6:
        required_categories.append(bool(phase6_regression))

    success = all(check["success"] for check in checks) and all(required_categories)
    totals = summarize_checks(checks)

    return {
        "phase": "Phase 7S-7Z",
        "command": "run_phase7_ml_readiness_check",
        "ml_ready": success,
        "success": success,
        "readiness_categories": readiness_categories,
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "runtime_active": False,
        "runtime_influence": False,
        "runtime_influence_granted": False,
        "runtime_eligibility_granted": False,
        "deterministic_runtime_remains_authoritative": True,
        "network_dependency": False,
        "database_dependency": False,
        "oracle_agent_memory_dependency": False,
        "phase6_validation_included": include_phase6,
        "phase7_validation_included": True,
        "materialization_validation_included": True,
        "checks": checks,
    }


def run_command_checks(*, include_phase6: bool) -> list[dict[str, Any]]:
    checks = [
        run_command_check(
            name="ml_validation",
            args=(sys.executable, "scripts/run_phase7_ml_validation.py"),
        ),
        run_command_check(
            name="ml_validation_json",
            args=(sys.executable, "scripts/run_phase7_ml_validation.py", "--json"),
            expect_json=True,
        ),
        run_command_check(
            name="materialization_validation",
            args=(sys.executable, "scripts/run_phase7_materialization_validation.py"),
        ),
        run_command_check(
            name="materialization_readiness",
            args=(phase_python(), "scripts/run_phase7_materialization_readiness_check.py"),
        ),
        run_command_check(
            name="phase7_validation",
            args=(phase_python(), "scripts/run_phase7_validation.py"),
        ),
        run_command_check(
            name="phase7_readiness",
            args=(phase_python(), "scripts/run_phase7_readiness_check.py"),
        ),
        run_command_check(
            name="phase7h_dashboard_validation",
            args=(sys.executable, "scripts/run_phase7h_dashboard_validation.py"),
        ),
        run_command_check(
            name="phase7i_cli_validation",
            args=(phase_python(), "scripts/awr_memory_cli.py", "learning", "validate", "--json"),
            expect_json=True,
        ),
        run_command_check(
            name="ml_docs_readiness_tests",
            args=(
                sys.executable,
                "-m",
                "unittest",
                "tests/test_phase7_ml_validation.py",
                "tests/test_phase7_ml_readiness_check.py",
            ),
            extra_env={"PHASE7_ML_READINESS_SELFTEST": "1"},
        ),
    ]

    if include_phase6:
        checks.append(
            run_command_check(
                name="phase6_regression",
                args=(phase_python(), "scripts/run_phase6_validation.py"),
                extra_env={"PYTHONPATH": phase_pythonpath()},
            )
        )
    return checks


def run_command_check(
    *,
    name: str,
    args: tuple[str, ...],
    expect_json: bool = False,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    env = validation_env()
    if extra_env:
        env.update(extra_env)

    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    counts = parse_counts(output)
    json_payload: dict[str, Any] | None = None
    details: list[str] = []

    success = completed.returncode == 0
    if expect_json:
        try:
            json_payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            success = False
            details.append(f"invalid JSON output: {exc}")
        else:
            success = success and bool(json_payload.get("success"))
            counts["tests_run"] = int(json_payload.get("tests_run", counts["tests_run"]))
            counts["checks_run"] = int(json_payload.get("checks_run", counts["checks_run"]))
            counts["failures"] = int(json_payload.get("failures", counts["failures"]))
            counts["errors"] = int(json_payload.get("errors", counts["errors"]))
            counts["skipped"] = int(json_payload.get("skipped", counts["skipped"]))

    if not success:
        details.extend(concise_output(output))

    failures = counts["failures"]
    errors = counts["errors"]
    if not success and failures == 0 and errors == 0:
        failures = 1

    return {
        "name": name,
        "success": success,
        "returncode": completed.returncode,
        "tests_run": counts["tests_run"],
        "checks_run": counts["checks_run"] + 1,
        "failures": failures,
        "errors": errors,
        "skipped": counts["skipped"],
        "details": details,
        "json_payload": json_payload,
    }


def check_required_paths(name: str, relative_paths: Sequence[str]) -> dict[str, Any]:
    missing = [relative_path for relative_path in relative_paths if not (ROOT / relative_path).is_file()]
    return {
        "name": name,
        "success": not missing,
        "returncode": 0 if not missing else 1,
        "tests_run": 0,
        "checks_run": len(relative_paths),
        "failures": len(missing),
        "errors": 0,
        "skipped": 0,
        "details": [f"missing required path: {relative_path}" for relative_path in missing],
    }


def check_safety_claims() -> dict[str, Any]:
    text = combined_documentation_text()
    missing = [claim for claim in SAFETY_CLAIMS if claim not in text]
    return {
        "name": "required_ml_safety_claims",
        "success": not missing,
        "returncode": 0 if not missing else 1,
        "tests_run": 0,
        "checks_run": len(SAFETY_CLAIMS),
        "failures": len(missing),
        "errors": 0,
        "skipped": 0,
        "details": [f"missing safety claim: {claim}" for claim in missing],
    }


def check_readiness_script_imports() -> dict[str, Any]:
    path = ROOT / "scripts" / "run_phase7_ml_readiness_check.py"
    imports = parse_imports(path)
    unsafe = [
        module_name
        for module_name in sorted(imports)
        if any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORTS
        )
    ]
    return {
        "name": "readiness_script_dependency_safety",
        "success": not unsafe,
        "returncode": 0 if not unsafe else 1,
        "tests_run": 0,
        "checks_run": max(len(imports), 1),
        "failures": len(unsafe),
        "errors": 0,
        "skipped": 0,
        "details": [f"unsafe readiness import: {module_name}" for module_name in unsafe],
    }


def combined_documentation_text() -> str:
    paths = [ROOT / relative_path for relative_path in REQUIRED_READINESS_DOCS]
    paths.append(ROOT / "docs" / "architecture" / "README.md")
    parts = [
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in paths
        if path.is_file()
    ]
    return "\n".join(parts)


def parse_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
            for alias in node.names:
                if alias.name != "*":
                    imports.add(f"{node.module}.{alias.name}")
    return imports


def parse_counts(output: str) -> dict[str, int]:
    counts = {"tests_run": 0, "checks_run": 0, "failures": 0, "errors": 0, "skipped": 0}

    for key in counts:
        matches = re.findall(rf"{key}:\s*(\d+)", output)
        if matches:
            counts[key] = int(matches[-1])

    ran_matches = re.findall(r"Ran (\d+) tests?", output)
    if ran_matches:
        counts["tests_run"] = int(ran_matches[-1])

    failed = re.search(r"FAILED \(([^)]+)\)", output)
    if failed:
        for part in failed.group(1).split(","):
            key, _, value = part.strip().partition("=")
            if key in counts and value.isdigit():
                counts[key] = int(value)
    else:
        skipped_match = re.search(r"OK \(skipped=(\d+)\)", output)
        if skipped_match:
            counts["skipped"] = int(skipped_match.group(1))

    return counts


def summarize_checks(checks: Sequence[dict[str, Any]]) -> dict[str, int]:
    totals = {"tests_run": 0, "checks_run": 0, "failures": 0, "errors": 0, "skipped": 0}
    for check in checks:
        for key in totals:
            totals[key] += int(check.get(key, 0))
    return totals


def group_success(groups_by_name: dict[object, object], name: str) -> bool:
    group = groups_by_name.get(name)
    return isinstance(group, dict) and bool(group.get("success"))


def validation_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def phase_python() -> str:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return str(venv_python)
    return sys.executable


def phase_pythonpath() -> str:
    existing_pythonpath = os.environ.get("PYTHONPATH")
    if existing_pythonpath:
        return os.pathsep.join((str(ROOT), existing_pythonpath))
    return str(ROOT)


def concise_output(output: str, *, limit: int = 12) -> list[str]:
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    return lines[-limit:]


def print_human_summary(summary: dict[str, Any]) -> None:
    status = "passed" if summary["success"] else "failed"
    ml_ready = "true" if summary["ml_ready"] else "false"
    print(f"Phase 7 ML readiness {status}.")
    print(f"ml_ready={ml_ready}")
    print(f"tests_run: {summary['tests_run']}")
    print(f"checks_run: {summary['checks_run']}")
    print(f"failures: {summary['failures']}")
    print(f"errors: {summary['errors']}")
    print(f"skipped: {summary['skipped']}")
    print()
    print("Readiness categories:")
    for key in READINESS_CATEGORY_KEYS:
        value = summary["readiness_categories"][key]
        if value is None:
            printable = "not_run"
        else:
            printable = "PASS" if value else "FAIL"
        print(f"- {key}: {printable}")
    print()
    print("Boundary confirmations:")
    print("runtime_active=false")
    print("runtime_influence=false")
    print("runtime_influence_granted=false")
    print("runtime_eligibility_granted=false")
    print("deterministic runtime remains authoritative")

    if not summary["success"]:
        print()
        print("Failed checks:")
        for check in summary["checks"]:
            if check["success"]:
                continue
            print(f"- {check['name']}: returncode={check['returncode']}")
            for detail in check.get("details", [])[:8]:
                print(f"  {detail}")


if __name__ == "__main__":
    raise SystemExit(main())
