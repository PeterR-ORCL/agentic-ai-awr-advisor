#!/usr/bin/env python3
"""Run Phase 7AD-7AI dashboard workflow infrastructure readiness checks."""

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
    "workflow_boundary",
    "actor_identity",
    "backend_execution_mode",
    "governed_write_path",
    "output_lifecycle",
    "runtime_isolation",
    "documentation_complete",
    "phase7_regression",
    "phase6_regression",
)

REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/run_phase7_dashboard_workflow_validation.py",
    "scripts/run_phase7_dashboard_workflow_readiness_check.py",
)

READINESS_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7_dashboard_workflow_validation_matrix.md",
    "docs/architecture/phase7_dashboard_workflow_readiness.md",
    "docs/architecture/phase7_dashboard_workflow_release_certification.md",
    "docs/architecture/phase7_dashboard_workflow_operational_checklist.md",
)

README_LINKS: tuple[str, ...] = (
    "phase7_dashboard_workflow_validation_matrix.md",
    "phase7_dashboard_workflow_readiness.md",
    "phase7_dashboard_workflow_release_certification.md",
    "phase7_dashboard_workflow_operational_checklist.md",
)

REQUIRED_DOC_PHRASES: tuple[str, ...] = (
    "dashboard_workflow_ready=true only when all checks pass",
    "infrastructure is ready for future screen workflows",
    "no dashboard workflow is activated yet",
    "no backend execution occurs yet",
    "7ad-7ai is certified as workflow infrastructure only",
    "no screen 2/3/5/6 workflows are certified here",
    "no backend execution is certified here",
    "no runtime mutation is certified here",
    "do not certify if validation fails",
    "do not treat infrastructure readiness as workflow activation",
)

FORBIDDEN_SCRIPT_IMPORTS: tuple[str, ...] = (
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
        description="Run local-only Phase 7 dashboard workflow readiness checks.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument(
        "--include-phase6",
        action="store_true",
        help="Also run Phase 6 regression validation.",
    )
    parser.add_argument(
        "--include-phase7",
        action="store_true",
        help="Retained for explicit Phase 7 regression readiness; Phase 7 is included by default.",
    )
    parser.add_argument(
        "--include-runtime-integration",
        action="store_true",
        help="Retained for explicit runtime readiness; runtime integration is included by default.",
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
            check_required_paths("dashboard_workflow_required_scripts", REQUIRED_SCRIPTS),
            check_required_paths("dashboard_workflow_readiness_docs", READINESS_DOCS),
            check_readiness_doc_language(),
            check_readme_links(),
            check_readiness_script_imports(),
        ]
    )
    checks_by_name = {check["name"]: check for check in checks}
    validation_json = checks_by_name["dashboard_workflow_validation_json"].get(
        "json_payload",
        {},
    )
    validation_groups = {
        group.get("name"): bool(group.get("success"))
        for group in validation_json.get("validation_groups", [])
        if isinstance(group, dict)
    }

    readiness_categories = {
        "workflow_boundary": validation_groups.get("workflow_boundary", False),
        "actor_identity": validation_groups.get("actor_identity", False),
        "backend_execution_mode": validation_groups.get("backend_execution_mode", False),
        "governed_write_path": validation_groups.get("governed_write_path", False),
        "output_lifecycle": validation_groups.get("output_lifecycle", False),
        "runtime_isolation": (
            validation_groups.get("import_isolation", False)
            and validation_groups.get("runtime_safety", False)
        ),
        "documentation_complete": (
            validation_groups.get("documentation", False)
            and checks_by_name["dashboard_workflow_readiness_docs"]["success"]
            and checks_by_name["dashboard_workflow_readiness_doc_language"]["success"]
            and checks_by_name["dashboard_workflow_readme_links"]["success"]
        ),
        "phase7_regression": (
            checks_by_name["phase7_final_readiness"]["success"]
            and checks_by_name["phase7aa_runtime_integration_readiness"]["success"]
            and checks_by_name["phase7_validation"]["success"]
            and checks_by_name["phase7h_dashboard_validation"]["success"]
            and checks_by_name["phase7i_cli_validation"]["success"]
        ),
        "phase6_regression": None,
    }
    if include_phase6:
        readiness_categories["phase6_regression"] = checks_by_name[
            "phase6_regression"
        ]["success"]

    required_categories = [
        value for key, value in readiness_categories.items() if key != "phase6_regression"
    ]
    if include_phase6:
        required_categories.append(bool(readiness_categories["phase6_regression"]))

    totals = summarize_checks(checks)
    success = all(check["success"] for check in checks) and all(required_categories)
    return {
        "phase": "Phase 7AD-7AI",
        "command": "run_phase7_dashboard_workflow_readiness_check",
        "dashboard_workflow_ready": success,
        "success": success,
        "readiness_categories": readiness_categories,
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "backend_execution_performed": False,
        "write_performed": False,
        "output_written": False,
        "dashboard_regenerated": False,
        "phase4i_mutated": False,
        "runtime_mutation_performed": False,
        "run_analysis_wired": False,
        "deterministic_runtime_remains_authoritative": True,
        "phase8_implemented": False,
        "network_dependency": False,
        "database_dependency": False,
        "object_storage_dependency": False,
        "oracle_agent_memory_dependency": False,
        "phase6_validation_included": include_phase6,
        "checks": checks,
    }


def run_command_checks(*, include_phase6: bool) -> list[dict[str, Any]]:
    checks = [
        run_command_check(
            name="dashboard_workflow_validation",
            args=(sys.executable, "scripts/run_phase7_dashboard_workflow_validation.py"),
        ),
        run_command_check(
            name="dashboard_workflow_validation_json",
            args=(
                sys.executable,
                "scripts/run_phase7_dashboard_workflow_validation.py",
                "--json",
            ),
            expect_json=True,
        ),
        run_command_check(
            name="phase7_final_readiness",
            args=(phase_python(), "scripts/run_phase7_final_readiness_check.py"),
        ),
        run_command_check(
            name="phase7aa_runtime_integration_readiness",
            args=(phase_python(), "scripts/run_phase7aa_runtime_integration_readiness_check.py"),
        ),
        run_command_check(
            name="phase7_validation",
            args=(phase_python(), "scripts/run_phase7_validation.py"),
        ),
        run_command_check(
            name="phase7h_dashboard_validation",
            args=(phase_python(), "scripts/run_phase7h_dashboard_validation.py"),
        ),
        run_command_check(
            name="phase7i_cli_validation",
            args=(phase_python(), "scripts/awr_memory_cli.py", "learning", "validate", "--json"),
            expect_json=True,
        ),
        run_command_check(
            name="dashboard_workflow_validation_tests",
            args=(
                sys.executable,
                "-m",
                "unittest",
                "tests/test_phase7_dashboard_workflow_validation.py",
            ),
        ),
        run_command_check(
            name="dashboard_workflow_readiness_tests",
            args=(
                sys.executable,
                "-m",
                "unittest",
                "tests/test_phase7_dashboard_workflow_readiness_check.py",
            ),
            extra_env={"PHASE7_DASHBOARD_WORKFLOW_READINESS_SELFTEST": "1"},
        ),
    ]
    if include_phase6:
        checks.append(
            run_command_check(
                name="phase6_regression",
                args=(phase_python(), "scripts/run_phase6_validation.py"),
                extra_env={"PYTHONPATH": phase6_pythonpath()},
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
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
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
    details = normalize_output_lines(output)
    json_payload: dict[str, Any] | None = None
    success = completed.returncode == 0
    if expect_json:
        try:
            json_payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            success = False
            details.append(f"invalid JSON output: {exc}")
    return {
        "name": name,
        "success": success,
        "returncode": completed.returncode,
        "tests_run": counts["tests_run"],
        "checks_run": counts["checks_run"] or 1,
        "failures": counts["failures"] if completed.returncode == 0 else max(1, counts["failures"]),
        "errors": counts["errors"],
        "skipped": counts["skipped"],
        "json_payload": json_payload,
        "details": details,
    }


def check_required_paths(name: str, relative_paths: tuple[str, ...]) -> dict[str, Any]:
    missing = [path for path in relative_paths if not (ROOT / path).is_file()]
    return {
        "name": name,
        "success": not missing,
        "tests_run": 0,
        "checks_run": len(relative_paths),
        "failures": len(missing),
        "errors": 0,
        "skipped": 0,
        "details": [f"missing path: {path}" for path in missing] or ["required paths present"],
    }


def check_readiness_doc_language() -> dict[str, Any]:
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8", errors="ignore").lower()
        for path in READINESS_DOCS
        if (ROOT / path).is_file()
    )
    missing = [phrase for phrase in REQUIRED_DOC_PHRASES if phrase not in combined]
    return {
        "name": "dashboard_workflow_readiness_doc_language",
        "success": not missing,
        "tests_run": 0,
        "checks_run": len(REQUIRED_DOC_PHRASES),
        "failures": len(missing),
        "errors": 0,
        "skipped": 0,
        "details": [f"missing phrase: {phrase}" for phrase in missing]
        or ["dashboard workflow readiness documentation language present"],
    }


def check_readme_links() -> dict[str, Any]:
    readme = ROOT / "docs" / "architecture" / "README.md"
    source = readme.read_text(encoding="utf-8", errors="ignore") if readme.is_file() else ""
    missing = [link for link in README_LINKS if link not in source]
    return {
        "name": "dashboard_workflow_readme_links",
        "success": not missing,
        "tests_run": 0,
        "checks_run": len(README_LINKS),
        "failures": len(missing),
        "errors": 0,
        "skipped": 0,
        "details": [f"missing README link: {link}" for link in missing]
        or ["dashboard workflow readiness README links present"],
    }


def check_readiness_script_imports() -> dict[str, Any]:
    imports = imported_module_names(ROOT / "scripts" / "run_phase7_dashboard_workflow_readiness_check.py")
    violations = [
        imported
        for imported in imports
        for forbidden in FORBIDDEN_SCRIPT_IMPORTS
        if imported == forbidden or imported.startswith(f"{forbidden}.")
    ]
    return {
        "name": "dashboard_workflow_readiness_script_imports",
        "success": not violations,
        "tests_run": 0,
        "checks_run": len(imports),
        "failures": len(violations),
        "errors": 0,
        "skipped": 0,
        "details": [f"unsafe import: {item}" for item in violations]
        or ["dashboard workflow readiness script imports are standard-library only"],
    }


def imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def parse_counts(output: str) -> dict[str, int]:
    tests_run = 0
    checks_run = 0
    failures = 0
    errors = 0
    skipped = 0
    ran_match = re.search(r"Ran\s+(\d+)\s+tests?", output)
    if ran_match:
        tests_run = int(ran_match.group(1))
    for key, target in (
        ("tests_run", "tests_run"),
        ("checks_run", "checks_run"),
        ("failures", "failures"),
        ("errors", "errors"),
        ("skipped", "skipped"),
    ):
        match = re.search(rf"{key}[:=]\s*(\d+)", output)
        if match:
            value = int(match.group(1))
            if target == "tests_run":
                tests_run = max(tests_run, value)
            elif target == "checks_run":
                checks_run = value
            elif target == "failures":
                failures = value
            elif target == "errors":
                errors = value
            elif target == "skipped":
                skipped = value
    if "FAILED" in output and failures == 0 and errors == 0:
        failures = 1
    return {
        "tests_run": tests_run,
        "checks_run": checks_run,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
    }


def normalize_output_lines(output: str) -> list[str]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-20:] if lines else []


def summarize_checks(checks: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "tests_run": sum(int(check.get("tests_run", 0)) for check in checks),
        "checks_run": sum(int(check.get("checks_run", 0)) for check in checks),
        "failures": sum(int(check.get("failures", 0)) for check in checks),
        "errors": sum(int(check.get("errors", 0)) for check in checks),
        "skipped": sum(int(check.get("skipped", 0)) for check in checks),
    }


def phase_python() -> str:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def phase6_pythonpath() -> str:
    existing = os.environ.get("PYTHONPATH")
    return f"{ROOT}{os.pathsep}{existing}" if existing else str(ROOT)


def print_human_summary(summary: dict[str, Any]) -> None:
    if summary["success"]:
        print("Phase 7 dashboard workflow infrastructure readiness passed.")
    else:
        print("Phase 7 dashboard workflow infrastructure readiness failed.")
    print(f"dashboard_workflow_ready={str(summary['dashboard_workflow_ready']).lower()}")
    print(f"tests_run={summary['tests_run']}")
    print(f"checks_run={summary['checks_run']}")
    print(f"failures={summary['failures']}")
    print(f"errors={summary['errors']}")
    print("backend_execution_performed=false")
    print("write_performed=false")
    print("output_written=false")
    print("dashboard_regenerated=false")
    print("phase4i_mutated=false")
    print("deterministic_runtime_remains_authoritative=true")
    print("Readiness categories:")
    for category, value in summary["readiness_categories"].items():
        print(f"- {category}: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
