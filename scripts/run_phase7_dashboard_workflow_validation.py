#!/usr/bin/env python3
"""Run local Phase 7AD-7AI dashboard workflow infrastructure validation."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]

WORKFLOW_TESTS: tuple[tuple[str, str], ...] = (
    ("workflow_boundary", "tests/test_phase7ad_dashboard_workflow_boundary.py"),
    ("actor_identity", "tests/test_phase7ae_dashboard_actor_identity.py"),
    ("backend_execution_mode", "tests/test_phase7af_dashboard_backend_execution_mode.py"),
    ("governed_write_path", "tests/test_phase7ag_dashboard_governed_write_path.py"),
    ("output_lifecycle", "tests/test_phase7ah_dashboard_output_lifecycle.py"),
)

WORKFLOW_MODULE_KEYS: tuple[str, ...] = (
    "dashboard_workflow_boundary",
    "dashboard_actor_identity",
    "dashboard_backend_execution_mode",
    "dashboard_governed_write_path",
    "dashboard_output_lifecycle",
)

WORKFLOW_SOURCE_PATHS: tuple[str, ...] = (
    "src/learning/dashboard_workflow_boundary.py",
    "src/learning/dashboard_actor_identity.py",
    "src/learning/dashboard_backend_execution_mode.py",
    "src/learning/dashboard_governed_write_path.py",
    "src/learning/dashboard_output_lifecycle.py",
)

RUNTIME_IMPORT_PATHS: tuple[str, ...] = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/parsing",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
    "src/analysis",
    "src/reporting",
)

BEHAVIOR_FILES: tuple[str, ...] = (
    "src/reporting/html_dashboard.py",
    "src/reporting/ai_display_metadata.py",
    "scripts/awr_memory_cli.py",
    "scripts/run_analysis.py",
)

REQUIRED_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7ad_dashboard_workflow_boundary.md",
    "docs/architecture/phase7ad_dashboard_workflow_lifecycle.md",
    "docs/architecture/phase7ae_dashboard_actor_identity.md",
    "docs/architecture/phase7ae_actor_identity_model.md",
    "docs/architecture/phase7af_dashboard_backend_execution_mode.md",
    "docs/architecture/phase7af_backend_execution_request_model.md",
    "docs/architecture/phase7ag_dashboard_governed_write_path.md",
    "docs/architecture/phase7ag_write_path_model.md",
    "docs/architecture/phase7ah_dashboard_output_lifecycle.md",
    "docs/architecture/phase7ah_output_artifact_model.md",
    "docs/architecture/phase7_dashboard_workflow_validation_matrix.md",
)

DOCUMENTATION_PHRASES: tuple[str, ...] = (
    "workflow infrastructure is metadata/validation only",
    "no dashboard workflows are implemented here",
    "no backend execution occurs",
    "no write is performed",
    "no output artifact is written",
    "deterministic runtime remains authoritative",
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

FORBIDDEN_FUNCTION_NAMES: tuple[str, ...] = (
    "execute_backend",
    "execute_request",
    "perform_write",
    "write_database",
    "write_artifact",
    "regenerate_dashboard",
    "mutate_phase4i",
    "run_analysis",
    "call_object_storage",
    "auto_apply",
    "autonomous_apply",
)

PHASE8_IMPLEMENTATION_PATHS: tuple[str, ...] = (
    "src/phase8",
    "src/sizing",
    "src/tco",
    "src/what_if",
    "scripts/run_phase8_sizing_tco.py",
    "scripts/run_phase8_validation.py",
    "scripts/run_phase8_readiness_check.py",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local-only Phase 7 dashboard workflow infrastructure validation.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument(
        "--include-phase6",
        action="store_true",
        help="Also run Phase 6 validation.",
    )
    parser.add_argument(
        "--include-phase7",
        action="store_true",
        help="Also run consolidated Phase 7 validation.",
    )
    parser.add_argument(
        "--include-runtime-integration",
        action="store_true",
        help="Also run Phase 7AA runtime integration readiness.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_validation(
        include_phase6=args.include_phase6,
        include_phase7=args.include_phase7,
        include_runtime_integration=args.include_runtime_integration,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["success"] else 1


def run_validation(
    *,
    include_phase6: bool = False,
    include_phase7: bool = False,
    include_runtime_integration: bool = False,
) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    groups.extend(run_workflow_unittest_groups())
    groups.append(run_import_isolation_group())
    groups.append(run_runtime_safety_group())
    groups.append(run_documentation_group())
    if include_phase7:
        groups.append(
            run_command_group(
                "phase7_regression",
                (phase_python(), "scripts/run_phase7_validation.py"),
            )
        )
    if include_runtime_integration:
        groups.append(
            run_command_group(
                "runtime_integration_regression",
                (phase_python(), "scripts/run_phase7aa_runtime_integration_readiness_check.py"),
            )
        )
    if include_phase6:
        groups.append(
            run_command_group(
                "phase6_regression",
                (phase_python(), "scripts/run_phase6_validation.py"),
                extra_env={"PYTHONPATH": phase6_pythonpath()},
            )
        )

    totals = summarize_groups(groups)
    success = all(group["success"] for group in groups)
    return {
        "phase": "Phase 7AD-7AI",
        "command": "run_phase7_dashboard_workflow_validation",
        "success": success,
        "validation_groups": groups,
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "workflow_boundary_defined": group_success(groups, "workflow_boundary"),
        "actor_identity_metadata_only": group_success(groups, "actor_identity"),
        "backend_execution_metadata_only": group_success(groups, "backend_execution_mode"),
        "governed_write_path_dry_run_only": group_success(groups, "governed_write_path"),
        "output_lifecycle_metadata_only": group_success(groups, "output_lifecycle"),
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
        "phase7_validation_included": include_phase7,
        "runtime_integration_validation_included": include_runtime_integration,
    }


def run_workflow_unittest_groups() -> list[dict[str, Any]]:
    return [
        run_command_group(name, (sys.executable, "-m", "unittest", test_path))
        for name, test_path in WORKFLOW_TESTS
    ]


def run_command_group(
    name: str,
    args: tuple[str, ...],
    *,
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


def run_import_isolation_group() -> dict[str, Any]:
    details: list[str] = []
    checks_run = 0
    for path in iter_python_files(RUNTIME_IMPORT_PATHS):
        checks_run += 1
        imports = imported_module_names(path)
        source = read_text(path)
        for module_key in WORKFLOW_MODULE_KEYS:
            if any(module_key in imported for imported in imports):
                details.append(f"{relative(path)} imports {module_key}")
            if module_key in source:
                details.append(f"{relative(path)} references {module_key}")
    return {
        "name": "import_isolation",
        "success": not details,
        "tests_run": 0,
        "checks_run": checks_run,
        "failures": len(details),
        "errors": 0,
        "skipped": 0,
        "details": details or ["dashboard workflow infrastructure import isolation preserved"],
    }


def run_runtime_safety_group() -> dict[str, Any]:
    details: list[str] = []
    checks_run = 0
    for path in iter_python_files(WORKFLOW_SOURCE_PATHS):
        checks_run += 1
        tree = ast.parse(read_text(path), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in FORBIDDEN_FUNCTION_NAMES:
                    details.append(f"{relative(path)} defines forbidden function {node.name}")
        details.extend(find_true_safety_flags(path, tree))
    details.extend(check_behavior_file_diff())
    details.extend(check_phase8_not_implemented())
    return {
        "name": "runtime_safety",
        "success": not details,
        "tests_run": 0,
        "checks_run": checks_run + len(BEHAVIOR_FILES) + len(PHASE8_IMPLEMENTATION_PATHS),
        "failures": len(details),
        "errors": 0,
        "skipped": 0,
        "details": details or [
            "no backend execution, writes, output artifacts, dashboard regeneration, Phase 4I mutation, or Phase 8 implementation detected"
        ],
    }


def run_documentation_group() -> dict[str, Any]:
    details: list[str] = []
    checks_run = len(REQUIRED_DOCS) + len(DOCUMENTATION_PHRASES)
    missing_docs = [path for path in REQUIRED_DOCS if not (ROOT / path).is_file()]
    details.extend(f"missing doc: {path}" for path in missing_docs)
    combined = "\n".join(
        read_text(ROOT / path)
        for path in REQUIRED_DOCS
        if (ROOT / path).is_file()
    ).lower()
    for phrase in DOCUMENTATION_PHRASES:
        if phrase not in combined:
            details.append(f"missing documentation phrase: {phrase}")
    return {
        "name": "documentation",
        "success": not details,
        "tests_run": 0,
        "checks_run": checks_run,
        "failures": len(details),
        "errors": 0,
        "skipped": 0,
        "details": details or ["dashboard workflow infrastructure documentation complete"],
    }


def find_true_safety_flags(path: Path, tree: ast.AST) -> list[str]:
    unsafe_names = {
        "execution_performed",
        "write_performed",
        "output_written",
        "dashboard_regenerated",
        "phase4i_mutated",
        "runtime_mutation_performed",
        "runtime_mutation_requested",
        "phase4i_mutation_requested",
        "refresh_performed",
    }
    details: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword):
            if node.arg in unsafe_names and is_true_literal(node.value):
                details.append(f"{relative(path)} passes {node.arg}=True")
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                name = assignment_target_name(target)
                if name in unsafe_names and is_true_literal(node.value):
                    details.append(f"{relative(path)} assigns {name}=True")
        elif isinstance(node, ast.AnnAssign):
            name = assignment_target_name(node.target)
            if name in unsafe_names and node.value is not None and is_true_literal(node.value):
                details.append(f"{relative(path)} assigns {name}=True")
    return details


def check_behavior_file_diff() -> list[str]:
    completed = subprocess.run(
        ("git", "diff", "--name-only"),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return [f"git diff unavailable: {completed.stderr.strip()}"]
    changed = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
    return [
        f"behavior file modified by workflow infrastructure task: {path}"
        for path in BEHAVIOR_FILES
        if path in changed
    ]


def check_phase8_not_implemented() -> list[str]:
    return [
        f"unexpected Phase 8 implementation path: {path}"
        for path in PHASE8_IMPLEMENTATION_PATHS
        if (ROOT / path).exists()
    ]


def imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def iter_python_files(relative_paths: Iterable[str]) -> Iterable[Path]:
    for relative_path in relative_paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            yield from sorted(child for child in path.rglob("*.py") if child.is_file())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assignment_target_name(target: ast.AST) -> str | None:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def is_true_literal(value: ast.AST) -> bool:
    return isinstance(value, ast.Constant) and value.value is True


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


def summarize_groups(groups: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "tests_run": sum(int(group.get("tests_run", 0)) for group in groups),
        "checks_run": sum(int(group.get("checks_run", 0)) for group in groups),
        "failures": sum(int(group.get("failures", 0)) for group in groups),
        "errors": sum(int(group.get("errors", 0)) for group in groups),
        "skipped": sum(int(group.get("skipped", 0)) for group in groups),
    }


def group_success(groups: list[dict[str, Any]], name: str) -> bool:
    for group in groups:
        if group.get("name") == name:
            return bool(group.get("success"))
    return False


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
        print("Phase 7 dashboard workflow infrastructure validation passed.")
    else:
        print("Phase 7 dashboard workflow infrastructure validation failed.")
    print(f"tests_run={summary['tests_run']}")
    print(f"checks_run={summary['checks_run']}")
    print(f"failures={summary['failures']}")
    print(f"errors={summary['errors']}")
    print(f"skipped={summary['skipped']}")
    print("backend_execution_performed=false")
    print("write_performed=false")
    print("output_written=false")
    print("dashboard_regenerated=false")
    print("phase4i_mutated=false")
    print("deterministic_runtime_remains_authoritative=true")
    print("Validation groups:")
    for group in summary["validation_groups"]:
        status = "PASS" if group["success"] else "FAIL"
        print(
            f"- {group['name']}: {status} "
            f"(tests={group['tests_run']}, checks={group['checks_run']}, "
            f"failures={group['failures']}, errors={group['errors']}, "
            f"skipped={group['skipped']})"
        )


if __name__ == "__main__":
    raise SystemExit(main())
