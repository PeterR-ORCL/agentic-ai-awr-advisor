#!/usr/bin/env python3
"""Run local Phase 7BU-7BZ runtime materialization validation."""

from __future__ import annotations

import argparse
import ast
import io
import json
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class ValidationGroup:
    name: str
    modules: tuple[str, ...]
    description: str


UNITTEST_GROUPS: tuple[ValidationGroup, ...] = (
    ValidationGroup(
        name="governed_workflow_persistence",
        modules=("tests.test_phase7bu_governed_workflow_persistence",),
        description="7BU persistence, audit, transaction, and idempotency metadata.",
    ),
    ValidationGroup(
        name="status_transition_execution",
        modules=("tests.test_phase7bu_status_transition_execution",),
        description="7BU status transition request/result metadata only.",
    ),
    ValidationGroup(
        name="parser_runtime_update",
        modules=("tests.test_phase7bv_parser_runtime_update_path",),
        description="7BV parser runtime update package metadata only.",
    ),
    ValidationGroup(
        name="scoring_runtime_activation",
        modules=("tests.test_phase7bw_scoring_runtime_activation",),
        description="7BW scoring runtime config activation metadata only.",
    ),
    ValidationGroup(
        name="recommendation_runtime_activation",
        modules=("tests.test_phase7bx_recommendation_runtime_activation",),
        description="7BX recommendation runtime rule activation metadata only.",
    ),
    ValidationGroup(
        name="ml_runtime_eligibility",
        modules=("tests.test_phase7by_ml_runtime_eligibility",),
        description="7BY ML runtime eligibility metadata only.",
    ),
)


RUNTIME_MATERIALIZATION_MODULES: tuple[str, ...] = (
    "governed_workflow_persistence",
    "governance_status_transition",
    "parser_runtime_update_path",
    "scoring_runtime_activation",
    "recommendation_runtime_activation",
    "ml_runtime_eligibility",
)


RUNTIME_MATERIALIZATION_SOURCE_PATHS: tuple[str, ...] = (
    "src/learning/governed_workflow_persistence.py",
    "src/learning/governance_status_transition.py",
    "src/learning/parser_runtime_update_path.py",
    "src/learning/scoring_runtime_activation.py",
    "src/learning/recommendation_runtime_activation.py",
    "src/learning/ml_runtime_eligibility.py",
)


RUNTIME_IMPORT_PATHS: tuple[str, ...] = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/parsing",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
    "src/analysis/decision_engine.py",
    "src/analysis/recommendation_engine.py",
    "src/analysis/scoring_adapter.py",
)


REQUIRED_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7bu_runtime_materialization_execution_boundary.md",
    "docs/architecture/phase7bu_governed_workflow_persistence.md",
    "docs/architecture/phase7bu_status_transition_execution_model.md",
    "docs/architecture/phase7bv_parser_runtime_update_path.md",
    "docs/architecture/phase7bv_parser_runtime_update_model.md",
    "docs/architecture/phase7bw_scoring_runtime_config_activation.md",
    "docs/architecture/phase7bw_scoring_runtime_config_model.md",
    "docs/architecture/phase7bx_recommendation_runtime_rule_activation.md",
    "docs/architecture/phase7bx_recommendation_runtime_rule_model.md",
    "docs/architecture/phase7by_ml_runtime_eligibility.md",
    "docs/architecture/phase7by_ml_runtime_manifest_model.md",
    "docs/architecture/phase7_runtime_materialization_validation_matrix.md",
    "docs/architecture/phase7_runtime_materialization_readiness.md",
    "docs/architecture/phase7_runtime_materialization_release_certification.md",
    "docs/architecture/phase7_runtime_materialization_operational_checklist.md",
)


DOCUMENTATION_PHRASES: tuple[str, ...] = (
    "runtime materialization is metadata-only",
    "no db persistence occurs",
    "no status transition occurs",
    "no parser/scoring/recommendation/ml runtime activation occurs",
    "no phase 4i mutation occurs",
    "deterministic runtime remains authoritative",
    "phase 8 is not implemented",
)


FORBIDDEN_DB_OR_NETWORK_IMPORTS: tuple[str, ...] = (
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


FORBIDDEN_ACTIVE_FUNCTION_NAMES: tuple[str, ...] = (
    "persist_to_db",
    "perform_status_transition",
    "apply_parser_update",
    "apply_scoring_config",
    "apply_recommendation_rule",
    "deploy_model",
    "load_model",
    "save_model",
    "replace_scoring_engine",
    "grant_runtime_eligibility",
    "activate_runtime",
    "mutate_phase4i",
    "auto_apply",
    "autonomous_apply",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local-only Phase 7BU-7BZ runtime materialization validation.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_validation()
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["success"] else 1


def run_validation() -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    for group in UNITTEST_GROUPS:
        groups.append(run_unittest_group(group))
    groups.append(run_import_isolation_group())
    groups.append(run_runtime_safety_group())
    groups.append(run_documentation_group())

    totals = summarize_groups(groups)
    success = all(group["success"] for group in groups)
    return {
        "phase": "Phase 7BU-7BZ",
        "command": "run_phase7_runtime_materialization_validation",
        "success": success,
        "validation_groups": groups,
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "runtime_materialization_ready": success,
        "db_persistence_performed": False,
        "status_transition_performed": False,
        "parser_update_applied": False,
        "scoring_config_applied": False,
        "recommendation_rule_applied": False,
        "model_deployed": False,
        "model_loaded": False,
        "model_saved": False,
        "runtime_scoring_replaced": False,
        "runtime_eligibility_granted": False,
        "runtime_active": False,
        "phase4i_mutated": False,
        "deterministic_fallback_required": True,
        "deterministic_runtime_remains_authoritative": True,
        "phase8_implemented": False,
        "database_dependency": False,
        "network_dependency": False,
        "oracle_agent_memory_dependency": False,
    }


def run_unittest_group(group: ValidationGroup) -> dict[str, Any]:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for module_name in group.modules:
        suite.addTests(loader.loadTestsFromName(module_name))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    return {
        "name": group.name,
        "description": group.description,
        "success": result.wasSuccessful(),
        "tests_run": result.testsRun,
        "checks_run": 1,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "output": stream.getvalue().strip(),
    }


def run_import_isolation_group() -> dict[str, Any]:
    failures: list[str] = []
    checks_run = 0
    for path in python_files_for_paths(RUNTIME_IMPORT_PATHS):
        checks_run += 1
        imports = imported_modules(path)
        blocked = sorted(
            module
            for module in imports
            if is_runtime_materialization_import(module)
        )
        if blocked:
            failures.append(f"{path.relative_to(ROOT)} imports {', '.join(blocked)}")
    return {
        "name": "import_isolation",
        "description": "Runtime paths do not import 7BU-7BY metadata modules.",
        "success": not failures,
        "tests_run": 0,
        "checks_run": checks_run,
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures,
    }


def run_runtime_safety_group() -> dict[str, Any]:
    failures: list[str] = []
    checks_run = 0
    for path in python_files_for_paths(RUNTIME_MATERIALIZATION_SOURCE_PATHS):
        checks_run += 1
        imports = imported_modules(path)
        forbidden_imports = sorted(
            module
            for module in imports
            if import_matches_any(module, FORBIDDEN_DB_OR_NETWORK_IMPORTS)
        )
        if forbidden_imports:
            failures.append(
                f"{path.relative_to(ROOT)} has forbidden imports: "
                f"{', '.join(forbidden_imports)}"
            )
        functions = function_names(path)
        forbidden_functions = sorted(
            name for name in functions if name in FORBIDDEN_ACTIVE_FUNCTION_NAMES
        )
        if forbidden_functions:
            failures.append(
                f"{path.relative_to(ROOT)} defines forbidden active functions: "
                f"{', '.join(forbidden_functions)}"
            )
    return {
        "name": "runtime_safety",
        "description": "No DB, status, parser, scoring, recommendation, ML, runtime, or Phase 4I mutation functions exist.",
        "success": not failures,
        "tests_run": 0,
        "checks_run": checks_run,
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures,
    }


def run_documentation_group() -> dict[str, Any]:
    failures: list[str] = []
    checks_run = 0
    combined_text = ""
    for relative_path in REQUIRED_DOCS:
        checks_run += 1
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing {relative_path}")
            continue
        combined_text += "\n" + path.read_text(encoding="utf-8", errors="ignore").lower()
    for phrase in DOCUMENTATION_PHRASES:
        checks_run += 1
        if phrase not in combined_text:
            failures.append(f"missing documentation phrase: {phrase}")
    return {
        "name": "documentation",
        "description": "Required 7BU-7BZ docs exist and retain boundary language.",
        "success": not failures,
        "tests_run": 0,
        "checks_run": checks_run,
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures,
    }


def print_human_summary(summary: dict[str, Any]) -> None:
    if summary["success"]:
        print("Phase 7 runtime materialization validation passed.")
    else:
        print("Phase 7 runtime materialization validation failed.")
    print(f"runtime_materialization_ready={str(summary['runtime_materialization_ready']).lower()}")
    print(f"tests_run={summary['tests_run']}")
    print(f"checks_run={summary['checks_run']}")
    print(f"failures={summary['failures']}")
    print(f"errors={summary['errors']}")
    for group in summary["validation_groups"]:
        status = "PASS" if group["success"] else "FAIL"
        print(f"{status} {group['name']}")


def summarize_groups(groups: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "tests_run": sum(int(group.get("tests_run", 0)) for group in groups),
        "checks_run": sum(int(group.get("checks_run", 0)) for group in groups),
        "failures": sum(int(group.get("failures", 0)) for group in groups),
        "errors": sum(int(group.get("errors", 0)) for group in groups),
        "skipped": sum(int(group.get("skipped", 0)) for group in groups),
    }


def python_files_for_paths(paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if not path.exists():
            continue
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
    return files


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
                imports.update(f"{node.module}.{alias.name}" for alias in node.names)
            else:
                imports.update(alias.name for alias in node.names)
    return imports


def function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def is_runtime_materialization_import(module: str) -> bool:
    return any(
        module == name
        or module.endswith(f".{name}")
        or module == f"src.learning.{name}"
        for name in RUNTIME_MATERIALIZATION_MODULES
    )


def import_matches_any(module: str, forbidden: tuple[str, ...]) -> bool:
    return any(
        module == blocked or module.startswith(f"{blocked}.")
        for blocked in forbidden
    )


if __name__ == "__main__":
    raise SystemExit(main())
