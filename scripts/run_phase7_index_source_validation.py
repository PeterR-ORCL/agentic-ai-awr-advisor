#!/usr/bin/env python3
"""Run Phase 7BQ-7BT index/source mode entry validation."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_GROUPS: tuple[tuple[str, str], ...] = (
    ("source_mode_entry", "tests/test_phase7bq_index_source_mode_entry.py"),
    ("source_status", "tests/test_phase7br_source_status_panel.py"),
    ("object_storage_config", "tests/test_phase7bs_object_storage_config_validation.py"),
    ("index_screen3_handoff", "tests/test_phase7bt_index_screen3_handoff.py"),
    ("dashboard_panels", "tests/test_dashboard_index_source_mode_entry.py"),
    ("dashboard_panels", "tests/test_dashboard_index_source_status_panel.py"),
    ("dashboard_panels", "tests/test_dashboard_index_object_storage_config_panel.py"),
    ("dashboard_panels", "tests/test_dashboard_index_screen3_handoff_panel.py"),
)

REQUIRED_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7bq_index_source_mode_entry.md",
    "docs/architecture/phase7bq_source_mode_entry_model.md",
    "docs/architecture/phase7br_source_status_panel.md",
    "docs/architecture/phase7br_source_status_model.md",
    "docs/architecture/phase7bs_object_storage_config_validation.md",
    "docs/architecture/phase7bs_object_storage_config_model.md",
    "docs/architecture/phase7bt_index_screen3_handoff.md",
    "docs/architecture/phase7bt_index_screen3_handoff_model.md",
    "docs/architecture/phase7_index_source_validation_matrix.md",
    "docs/architecture/phase7_index_source_readiness.md",
    "docs/architecture/phase7_index_source_release_certification.md",
    "docs/architecture/phase7_index_source_operational_checklist.md",
)

REQUIRED_DOC_PHRASES: tuple[str, ...] = (
    "index source mode entry is preview-only",
    "source status is metadata-only",
    "object storage config validation is metadata-only",
    "handoff is metadata-only",
    "no source access",
    "no backend execution",
    "no handoff is performed",
    "no screen 3 state is updated",
    "no backend request is created",
    "no object storage call occurs",
    "no local file read occurs",
    "no db lookup occurs",
    "no run_analysis.py call occurs",
    "future em extract belongs to phase 8",
    "phase 8 sizing/tco is not implemented",
)

SOURCE_MODULES: tuple[str, ...] = (
    "src/learning/index_source_mode_entry.py",
    "src/learning/index_source_status.py",
    "src/learning/object_storage_config_validation.py",
    "src/learning/index_screen3_handoff.py",
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

FORBIDDEN_SOURCE_IMPORTS: tuple[str, ...] = (
    "subprocess",
    "requests",
    "urllib",
    "http.client",
    "httpx",
    "socket",
    "oci",
    "boto3",
    "botocore",
    "oracledb",
    "cx_Oracle",
    "sqlite3",
    "src.reporting",
    "scripts.run_analysis",
    "scripts.awr_memory_cli",
    "oracle_agent_memory",
)

FORBIDDEN_FUNCTION_NAMES: tuple[str, ...] = (
    "perform_handoff",
    "execute_handoff",
    "update_screen3_state",
    "write_local_storage",
    "write_location_hash",
    "create_backend_request",
    "call_backend",
    "call_object_storage",
    "read_file",
    "open_file",
    "query_database",
    "run_analysis",
    "execute_source_intake",
    "execute_analysis",
)

SOURCE_MODULE_IMPORT_NAMES: tuple[str, ...] = (
    "index_source_mode_entry",
    "index_source_status",
    "object_storage_config_validation",
    "index_screen3_handoff",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local-only Phase 7 index/source mode entry validation.",
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
    grouped_tests = collect_test_groups()
    groups = [
        run_unittest_group(name, test_paths)
        for name, test_paths in grouped_tests.items()
    ]
    groups.append(check_import_isolation())
    groups.append(check_runtime_safety())
    groups.append(check_documentation())

    totals = summarize_groups(groups)
    success = all(group["success"] for group in groups)
    return {
        "phase": "Phase 7BQ-7BT",
        "command": "run_phase7_index_source_validation",
        "success": success,
        "index_source_ready": success,
        "validation_groups": groups,
        "validation_group_names": [group["name"] for group in groups],
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "source_mode_entry_preview_only": True,
        "source_status_metadata_only": True,
        "object_storage_config_metadata_only": True,
        "handoff_metadata_only": True,
        "handoff_performed": False,
        "screen3_state_updated": False,
        "backend_request_created": False,
        "source_access_performed": False,
        "object_storage_called": False,
        "local_file_read_performed": False,
        "db_lookup_performed": False,
        "run_analysis_called": False,
        "future_em_extract_placeholder": True,
        "phase8_implemented": False,
    }


def collect_test_groups() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for name, test_path in TEST_GROUPS:
        grouped.setdefault(name, []).append(test_path)
    return grouped


def run_unittest_group(name: str, test_paths: list[str]) -> dict[str, Any]:
    suite = unittest.TestSuite()
    missing: list[str] = []
    for index, test_path in enumerate(test_paths):
        path = ROOT / test_path
        if not path.is_file():
            missing.append(test_path)
            continue
        module = load_module_from_path(
            path,
            f"phase7_index_source_validation_{name}_{index}",
        )
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    if missing:
        return failed_check(name, f"missing test path(s): {', '.join(missing)}")
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
        "details": details[-24:] if details else ["unittest check passed"],
    }


def check_import_isolation() -> dict[str, Any]:
    failures: list[str] = []
    checked_paths = list(python_files(RUNTIME_IMPORT_PATHS))
    for path in checked_paths:
        source = read_text(path)
        imports = imported_module_names(path)
        for module_name in SOURCE_MODULE_IMPORT_NAMES:
            forbidden_names = (
                module_name,
                f"learning.{module_name}",
                f"src.learning.{module_name}",
            )
            if any(name in imports for name in forbidden_names) or module_name in source:
                failures.append(f"{path.relative_to(ROOT)} imports or references {module_name}")
    return {
        "name": "import_isolation",
        "success": not failures,
        "tests_run": 0,
        "checks_run": max(1, len(checked_paths)),
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures or ["runtime paths do not import index source modules"],
    }


def check_runtime_safety() -> dict[str, Any]:
    failures: list[str] = []
    for relative_path in SOURCE_MODULES:
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing safety source: {relative_path}")
            continue
        imports = imported_module_names(path)
        functions = function_names(path)
        for forbidden in FORBIDDEN_SOURCE_IMPORTS:
            if any(
                imported == forbidden or imported.startswith(f"{forbidden}.")
                for imported in imports
            ):
                failures.append(f"{relative_path} imports forbidden module {forbidden}")
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            if forbidden in functions:
                failures.append(f"{relative_path} defines forbidden function {forbidden}")
    return {
        "name": "runtime_safety",
        "success": not failures,
        "tests_run": 0,
        "checks_run": len(SOURCE_MODULES) + len(FORBIDDEN_FUNCTION_NAMES),
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures or ["index source modules remain metadata-only"],
    }


def check_documentation() -> dict[str, Any]:
    failures: list[str] = []
    combined = ""
    for relative_path in REQUIRED_DOCS:
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing document: {relative_path}")
            continue
        combined += "\n" + read_text(path).lower()
    readme = ROOT / "docs" / "architecture" / "README.md"
    if readme.is_file():
        combined += "\n" + read_text(readme).lower()
    else:
        failures.append("missing document: docs/architecture/README.md")
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in combined:
            failures.append(f"missing documentation phrase: {phrase}")
    return {
        "name": "documentation",
        "success": not failures,
        "tests_run": 0,
        "checks_run": len(REQUIRED_DOCS) + len(REQUIRED_DOC_PHRASES),
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures or ["7BQ-7BT documentation complete"],
    }


def load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def python_files(paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
    return files


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def function_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def summarize_groups(groups: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "tests_run": sum(int(group.get("tests_run", 0)) for group in groups),
        "checks_run": sum(int(group.get("checks_run", 0)) for group in groups),
        "failures": sum(int(group.get("failures", 0)) for group in groups),
        "errors": sum(int(group.get("errors", 0)) for group in groups),
        "skipped": sum(int(group.get("skipped", 0)) for group in groups),
    }


def failed_check(name: str, detail: str) -> dict[str, Any]:
    return {
        "name": name,
        "success": False,
        "tests_run": 0,
        "checks_run": 1,
        "failures": 1,
        "errors": 0,
        "skipped": 0,
        "details": [detail],
    }


def print_human_summary(summary: dict[str, Any]) -> None:
    status = "passed" if summary["success"] else "failed"
    print(f"Phase 7 index source validation {status}.")
    print(f"index_source_ready={str(summary['index_source_ready']).lower()}")
    print(
        "checks="
        f"{summary['checks_run']} tests={summary['tests_run']} "
        f"failures={summary['failures']} errors={summary['errors']} "
        f"skipped={summary['skipped']}"
    )
    for group in summary["validation_groups"]:
        group_status = "PASS" if group["success"] else "FAIL"
        print(f"- {group_status} {group['name']}")
        if not group["success"]:
            for detail in group.get("details", [])[:8]:
                print(f"  {detail}")


if __name__ == "__main__":
    raise SystemExit(main())
