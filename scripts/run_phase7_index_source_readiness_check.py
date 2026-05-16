#!/usr/bin/env python3
"""Run Phase 7BQ-7BT index/source mode entry readiness checks."""

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

VALIDATION_SCRIPT = ROOT / "scripts" / "run_phase7_index_source_validation.py"

FOCUSED_TESTS: tuple[tuple[str, str], ...] = (
    ("source_mode_entry", "tests/test_phase7bq_index_source_mode_entry.py"),
    ("source_status", "tests/test_phase7br_source_status_panel.py"),
    ("object_storage_config", "tests/test_phase7bs_object_storage_config_validation.py"),
    ("index_screen3_handoff", "tests/test_phase7bt_index_screen3_handoff.py"),
    ("dashboard_panels", "tests/test_dashboard_index_source_mode_entry.py"),
    ("dashboard_panels", "tests/test_dashboard_index_source_status_panel.py"),
    ("dashboard_panels", "tests/test_dashboard_index_object_storage_config_panel.py"),
    ("dashboard_panels", "tests/test_dashboard_index_screen3_handoff_panel.py"),
)

READINESS_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7_index_source_validation_matrix.md",
    "docs/architecture/phase7_index_source_readiness.md",
    "docs/architecture/phase7_index_source_release_certification.md",
    "docs/architecture/phase7_index_source_operational_checklist.md",
)

README_LINKS: tuple[str, ...] = (
    "phase7bt_index_screen3_handoff.md",
    "phase7bt_index_screen3_handoff_model.md",
    "phase7_index_source_validation_matrix.md",
    "phase7_index_source_readiness.md",
    "phase7_index_source_release_certification.md",
    "phase7_index_source_operational_checklist.md",
)

REQUIRED_READINESS_PHRASES: tuple[str, ...] = (
    "index_source_ready=true",
    "index source mode entry is preview-only",
    "source status is metadata-only",
    "object storage config validation is metadata-only",
    "handoff is metadata-only",
    "no source access",
    "no backend execution",
    "future em extract belongs to phase 8",
)

FORBIDDEN_SCRIPT_IMPORTS: tuple[str, ...] = (
    "subprocess",
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
    "oracle_agent_memory",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local-only Phase 7 index/source mode entry readiness checks.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_readiness_check()
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["success"] else 1


def run_readiness_check() -> dict[str, Any]:
    validation_summary = load_validation_module().run_validation()
    checks = [
        {
            "name": "index_source_validation",
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
    checks.append(check_readiness_docs())
    checks.append(check_readme_links())
    checks.append(check_readiness_script_imports())

    checks_by_name = {check["name"]: check for check in checks}
    validation_groups = {
        group.get("name"): bool(group.get("success"))
        for group in validation_summary.get("validation_groups", [])
        if isinstance(group, dict)
    }
    readiness_categories = {
        "source_mode_entry": validation_groups.get("source_mode_entry", False),
        "source_status": validation_groups.get("source_status", False),
        "object_storage_config": validation_groups.get("object_storage_config", False),
        "handoff_metadata": validation_groups.get("index_screen3_handoff", False),
        "dashboard_panels": validation_groups.get("dashboard_panels", False),
        "validation_script": checks_by_name["index_source_validation"]["success"],
        "documentation_complete": (
            validation_groups.get("documentation", False)
            and checks_by_name["index_source_readiness_docs"]["success"]
            and checks_by_name["index_source_readme_links"]["success"]
        ),
        "runtime_safety": (
            validation_groups.get("import_isolation", False)
            and validation_groups.get("runtime_safety", False)
            and checks_by_name["index_source_readiness_script_imports"]["success"]
        ),
    }
    success = all(check["success"] for check in checks) and all(
        readiness_categories.values()
    )
    totals = summarize_checks(checks)
    return {
        "phase": "Phase 7BQ-7BT",
        "command": "run_phase7_index_source_readiness_check",
        "success": success,
        "index_source_ready": success,
        "readiness_categories": readiness_categories,
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
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "checks": checks,
    }


def load_validation_module():
    spec = importlib.util.spec_from_file_location(
        "run_phase7_index_source_validation",
        VALIDATION_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Phase 7 index source validation script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_focused_test_checks() -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for name, test_path in FOCUSED_TESTS:
        grouped.setdefault(name, []).append(test_path)
    return [
        run_unittest_check(name, test_paths)
        for name, test_paths in grouped.items()
    ]


def run_unittest_check(name: str, test_paths: list[str]) -> dict[str, Any]:
    suite = unittest.TestSuite()
    missing: list[str] = []
    for index, test_path in enumerate(test_paths):
        path = ROOT / test_path
        if not path.is_file():
            missing.append(test_path)
            continue
        module = load_module_from_path(
            path,
            f"phase7_index_source_readiness_{name}_{index}",
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


def check_readiness_docs() -> dict[str, Any]:
    failures: list[str] = []
    combined = ""
    for relative_path in READINESS_DOCS:
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing document: {relative_path}")
            continue
        combined += "\n" + read_text(path).lower()
    for phrase in REQUIRED_READINESS_PHRASES:
        if phrase not in combined:
            failures.append(f"missing readiness phrase: {phrase}")
    return {
        "name": "index_source_readiness_docs",
        "success": not failures,
        "tests_run": 0,
        "checks_run": len(READINESS_DOCS) + len(REQUIRED_READINESS_PHRASES),
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures or ["index source readiness docs complete"],
    }


def check_readme_links() -> dict[str, Any]:
    readme = ROOT / "docs" / "architecture" / "README.md"
    if not readme.is_file():
        return failed_check("index_source_readme_links", "missing docs/architecture/README.md")
    text = read_text(readme)
    failures = [link for link in README_LINKS if link not in text]
    return {
        "name": "index_source_readme_links",
        "success": not failures,
        "tests_run": 0,
        "checks_run": len(README_LINKS),
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures or ["README links index source docs"],
    }


def check_readiness_script_imports() -> dict[str, Any]:
    failures: list[str] = []
    for path in (Path(__file__).resolve(), VALIDATION_SCRIPT):
        imports = imported_module_names(path)
        for forbidden in FORBIDDEN_SCRIPT_IMPORTS:
            if any(
                imported == forbidden or imported.startswith(f"{forbidden}.")
                for imported in imports
            ):
                failures.append(f"{path.relative_to(ROOT)} imports forbidden module {forbidden}")
    return {
        "name": "index_source_readiness_script_imports",
        "success": not failures,
        "tests_run": 0,
        "checks_run": len(FORBIDDEN_SCRIPT_IMPORTS) * 2,
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures or ["index source scripts use local deterministic imports only"],
    }


def load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def summarize_checks(checks: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "tests_run": sum(int(check.get("tests_run", 0)) for check in checks),
        "checks_run": sum(int(check.get("checks_run", 0)) for check in checks),
        "failures": sum(int(check.get("failures", 0)) for check in checks),
        "errors": sum(int(check.get("errors", 0)) for check in checks),
        "skipped": sum(int(check.get("skipped", 0)) for check in checks),
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
    print(f"Phase 7 index source readiness {status}.")
    print(f"index_source_ready={str(summary['index_source_ready']).lower()}")
    print(
        "checks="
        f"{summary['checks_run']} tests={summary['tests_run']} "
        f"failures={summary['failures']} errors={summary['errors']} "
        f"skipped={summary['skipped']}"
    )
    for check in summary["checks"]:
        check_status = "PASS" if check["success"] else "FAIL"
        print(f"- {check_status} {check['name']}")
        if not check["success"]:
            for detail in check.get("details", [])[:8]:
                print(f"  {detail}")


if __name__ == "__main__":
    raise SystemExit(main())
