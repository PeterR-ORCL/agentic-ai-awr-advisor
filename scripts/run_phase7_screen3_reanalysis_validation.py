#!/usr/bin/env python3
"""Run local Phase 7AJ-7AO Screen 3 re-analysis validation."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from typing import Any, Iterable, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REANALYSIS_TESTS: tuple[tuple[str, str], ...] = (
    ("reanalysis_boundary", "tests/test_phase7aj_screen3_reanalysis_boundary.py"),
    ("source_selection", "tests/test_phase7ak_source_selection_model.py"),
    ("reanalysis_request", "tests/test_phase7al_reanalysis_request_model.py"),
    ("reanalysis_controller", "tests/test_phase7am_reanalysis_execution_controller.py"),
    ("screen3_action_ui", "tests/test_dashboard_screen3_reanalysis_actions.py"),
    ("reanalysis_readiness", "tests/test_phase7ao_reanalysis_readiness.py"),
)

REANALYSIS_MODULE_KEYS: tuple[str, ...] = (
    "screen3_reanalysis_boundary",
    "screen3_source_selection",
    "screen3_reanalysis_request",
    "screen3_reanalysis_controller",
    "reanalysis_readiness",
)

REANALYSIS_SOURCE_PATHS: tuple[str, ...] = (
    "src/learning/screen3_reanalysis_boundary.py",
    "src/learning/screen3_source_selection.py",
    "src/learning/screen3_reanalysis_request.py",
    "src/learning/screen3_reanalysis_controller.py",
    "src/learning/reanalysis_readiness.py",
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
)

PROTECTED_BEHAVIOR_FILES: tuple[str, ...] = (
    "src/reporting/ai_display_metadata.py",
    "scripts/awr_memory_cli.py",
    "scripts/run_analysis.py",
)

REQUIRED_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7aj_screen3_reanalysis_boundary.md",
    "docs/architecture/phase7aj_screen3_reanalysis_lifecycle.md",
    "docs/architecture/phase7ak_source_selection_model.md",
    "docs/architecture/phase7ak_local_object_storage_boundary.md",
    "docs/architecture/phase7al_reanalysis_request_model.md",
    "docs/architecture/phase7al_reanalysis_request_validation.md",
    "docs/architecture/phase7am_reanalysis_execution_controller.md",
    "docs/architecture/phase7am_awr_report_comparison_engine.md",
    "docs/architecture/phase7an_screen3_action_ui.md",
    "docs/architecture/phase7an_screen3_request_preview.md",
    "docs/architecture/phase7ao_reanalysis_validation_readiness.md",
    "docs/architecture/phase7ao_missing_metric_evidence_availability.md",
)

REQUIRED_DOC_PHRASES: tuple[str, ...] = (
    "validation/readiness is not execution",
    "no backend execution",
    "no run_analysis.py call",
    "no object storage call",
    "no file read",
    "no db lookup",
    "no phase 4i mutation",
    "missing metric handling is validation only",
    "screen 2 evidence review model remains future 7aq.1",
    "phase 8 sizing/tco is not implemented",
)

FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "oracledb",
    "cx_Oracle",
    "sqlite3",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "boto3",
    "botocore",
    "src.reporting",
    "src.parser",
    "src.parsing",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.analysis",
    "src.memory",
    "scripts.awr_memory_cli",
    "scripts.run_analysis",
    "oracle_agent_memory",
)

FORBIDDEN_FUNCTION_NAMES: tuple[str, ...] = (
    "execute_analysis",
    "execute_reanalysis",
    "call_object_storage",
    "read_local_file",
    "query_database",
    "regenerate_dashboard",
    "mutate_phase4i",
    "auto_execute",
    "autonomous_execute",
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
        description="Run local-only Phase 7 Screen 3 re-analysis validation.",
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
    groups.extend(run_reanalysis_unittest_groups())
    groups.append(run_import_isolation_group())
    groups.append(run_runtime_safety_group())
    groups.append(run_documentation_group())
    totals = summarize_groups(groups)
    success = all(group["success"] for group in groups)
    return {
        "phase": "Phase 7AJ-7AO",
        "command": "run_phase7_screen3_reanalysis_validation",
        "success": success,
        "validation_groups": groups,
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "screen3_reanalysis_ready": success,
        "missing_metric_handling_ready": group_success(groups, "reanalysis_readiness"),
        "backend_execution_performed": False,
        "run_analysis_called": False,
        "object_storage_called": False,
        "local_file_read_performed": False,
        "db_lookup_performed": False,
        "phase4i_mutated": False,
        "dashboard_regenerated": False,
        "dashboard_truth_mutated": False,
        "deterministic_runtime_remains_authoritative": True,
        "phase8_implemented": False,
    }


def run_reanalysis_unittest_groups() -> list[dict[str, Any]]:
    return [run_unittest_group(name, test_path) for name, test_path in REANALYSIS_TESTS]


def run_unittest_group(name: str, test_path: str) -> dict[str, Any]:
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
    module = load_module_from_path(path, f"phase7_screen3_reanalysis_{name}")
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
        "details": details[-20:] if details else ["unittest group passed"],
    }


def run_import_isolation_group() -> dict[str, Any]:
    details: list[str] = []
    checks_run = 0
    for path in iter_python_files(RUNTIME_IMPORT_PATHS):
        checks_run += 1
        imports = imported_module_names(path)
        source = read_text(path)
        for module_key in REANALYSIS_MODULE_KEYS:
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
        "details": details or ["Screen 3 re-analysis import isolation preserved"],
    }


def load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load test module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_runtime_safety_group() -> dict[str, Any]:
    details: list[str] = []
    checks_run = 0
    for relative_path in REANALYSIS_SOURCE_PATHS:
        path = ROOT / relative_path
        checks_run += 1
        if not path.is_file():
            details.append(f"missing source path: {relative_path}")
            continue
        tree = ast.parse(read_text(path), filename=str(path))
        imports = imported_module_names(path)
        details.extend(import_violations(path, imports))
        details.extend(function_name_violations(path, tree))
        details.extend(true_safety_flag_violations(path, tree))
    details.extend(check_protected_behavior_files_present())
    details.extend(check_phase8_not_implemented())
    return {
        "name": "runtime_safety",
        "success": not details,
        "tests_run": 0,
        "checks_run": checks_run + len(PROTECTED_BEHAVIOR_FILES) + len(PHASE8_IMPLEMENTATION_PATHS),
        "failures": len(details),
        "errors": 0,
        "skipped": 0,
        "details": details or [
            "no backend execution, run_analysis.py call, object storage call, file read, DB lookup, dashboard regeneration, Phase 4I mutation, or Phase 8 implementation detected"
        ],
    }


def run_documentation_group() -> dict[str, Any]:
    details: list[str] = []
    checks_run = len(REQUIRED_DOCS) + len(REQUIRED_DOC_PHRASES)
    missing_docs = [path for path in REQUIRED_DOCS if not (ROOT / path).is_file()]
    details.extend(f"missing doc: {path}" for path in missing_docs)
    combined = "\n".join(
        read_text(ROOT / path).lower()
        for path in REQUIRED_DOCS
        if (ROOT / path).is_file()
    )
    for phrase in REQUIRED_DOC_PHRASES:
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
        "details": details or ["Screen 3 re-analysis documentation complete"],
    }


def import_violations(path: Path, imports: set[str]) -> list[str]:
    return [
        f"{relative(path)} imports forbidden dependency {imported}"
        for imported in sorted(imports)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES
        if imported == forbidden or imported.startswith(f"{forbidden}.")
    ]


def function_name_violations(path: Path, tree: ast.AST) -> list[str]:
    details: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in FORBIDDEN_FUNCTION_NAMES:
                details.append(f"{relative(path)} defines forbidden function {node.name}")
    return details


def true_safety_flag_violations(path: Path, tree: ast.AST) -> list[str]:
    unsafe_names = {
        "backend_execution_performed",
        "runtime_execution_performed",
        "execution_performed",
        "run_analysis_called",
        "object_storage_called",
        "local_file_read_performed",
        "db_lookup_performed",
        "phase4i_mutated",
        "dashboard_regenerated",
        "output_written",
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


def check_protected_behavior_files_present() -> list[str]:
    return [
        f"protected behavior file missing: {path}"
        for path in PROTECTED_BEHAVIOR_FILES
        if not (ROOT / path).is_file()
    ]


def check_phase8_not_implemented() -> list[str]:
    return [
        f"unexpected Phase 8 implementation path: {path}"
        for path in PHASE8_IMPLEMENTATION_PATHS
        if (ROOT / path).exists()
    ]


def iter_python_files(relative_paths: Iterable[str]) -> Iterable[Path]:
    for relative_path in relative_paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            yield from sorted(child for child in path.rglob("*.py") if child.is_file())


def imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def assignment_target_name(target: ast.AST) -> str | None:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def is_true_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


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


def print_human_summary(summary: dict[str, Any]) -> None:
    if summary["success"]:
        print("Phase 7 Screen 3 re-analysis validation passed.")
    else:
        print("Phase 7 Screen 3 re-analysis validation failed.")
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
    print("Validation groups:")
    for group in summary["validation_groups"]:
        print(f"- {group['name']}: {group['success']}")


if __name__ == "__main__":
    raise SystemExit(main())
