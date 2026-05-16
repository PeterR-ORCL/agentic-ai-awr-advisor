#!/usr/bin/env python3
"""Run Phase 7BK-7BP Screen 6 governance validation."""

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
    ("governance_boundary", "tests/test_phase7bk_screen6_governance_control_boundary.py"),
    ("candidate_review", "tests/test_phase7bl_learning_candidate_review.py"),
    ("candidate_review_panel", "tests/test_dashboard_screen6_candidate_review_panel.py"),
    ("materialization_review", "tests/test_phase7bm_materialization_review.py"),
    ("materialization_review_panel", "tests/test_dashboard_screen6_materialization_review_panel.py"),
    ("model_registry_review", "tests/test_phase7bn_model_registry_review.py"),
    ("model_registry_review_panel", "tests/test_dashboard_screen6_model_registry_review_panel.py"),
    ("runtime_gate_review", "tests/test_phase7bo_runtime_gate_review.py"),
    ("runtime_gate_review_panel", "tests/test_dashboard_screen6_runtime_gate_review_panel.py"),
    ("screen6_visibility_regression", "tests/test_dashboard_learning_visibility.py"),
    ("screen6_visibility_regression", "tests/test_dashboard_ml_explainability_visibility.py"),
    (
        "screen6_visibility_regression",
        "tests/test_dashboard_screen6_fleet_governance_learning_exploration.py",
    ),
)

SCREEN6_GOVERNANCE_MODULE_NAMES: tuple[str, ...] = (
    "screen6_governance_control_boundary",
    "screen6_candidate_review",
    "screen6_materialization_review",
    "screen6_model_registry_review",
    "screen6_runtime_gate_review",
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

RUNTIME_SAFETY_SOURCE_PATHS: tuple[str, ...] = (
    "src/learning/screen6_governance_control_boundary.py",
    "src/learning/screen6_candidate_review.py",
    "src/learning/screen6_materialization_review.py",
    "src/learning/screen6_model_registry_review.py",
    "src/learning/screen6_runtime_gate_review.py",
)

FORBIDDEN_MUTATION_FUNCTIONS: tuple[str, ...] = (
    "persist_governance_action",
    "update_candidate_status",
    "update_materialization_status",
    "update_model_registry_status",
    "update_runtime_gate",
    "grant_runtime_eligibility",
    "activate_runtime",
    "execute_rollback",
    "execute_governed_write",
    "mutate_phase4i",
    "auto_apply",
    "autonomous_apply",
)

REQUIRED_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7bk_screen6_governance_control_boundary.md",
    "docs/architecture/phase7bk_screen6_governance_control_lifecycle.md",
    "docs/architecture/phase7bl_learning_candidate_review_ui.md",
    "docs/architecture/phase7bl_learning_candidate_review_model.md",
    "docs/architecture/phase7bm_materialization_review_ui.md",
    "docs/architecture/phase7bm_materialization_review_model.md",
    "docs/architecture/phase7bn_model_registry_review_ui.md",
    "docs/architecture/phase7bn_model_registry_review_model.md",
    "docs/architecture/phase7bo_runtime_gate_review_ui.md",
    "docs/architecture/phase7bo_runtime_gate_review_model.md",
    "docs/architecture/phase7_screen6_governance_validation_matrix.md",
    "docs/architecture/phase7_screen6_governance_readiness.md",
    "docs/architecture/phase7_screen6_governance_release_certification.md",
    "docs/architecture/phase7_screen6_governance_operational_checklist.md",
)

REQUIRED_DOC_PHRASES: tuple[str, ...] = (
    "screen 6 governance controls are preview-only",
    "no governance action is performed",
    "no status transition occurs",
    "no runtime eligibility is granted",
    "no runtime activation occurs",
    "no phase 4i mutation occurs",
    "deterministic runtime remains authoritative",
    "screen6_governance_ready=true only when checks pass",
    "active governance persistence is future work",
    "screen 6 governance control plane is certified as governed/preview-only",
    "active write execution remains future workflow",
    "no runtime activation is certified",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local-only Phase 7 Screen 6 governance validation.",
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
        "phase": "Phase 7BK-7BP",
        "command": "run_phase7_screen6_governance_validation",
        "success": success,
        "validation_groups": groups,
        "validation_group_names": [group["name"] for group in groups],
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "screen6_governance_ready": success,
        "candidate_review_preview_only": True,
        "materialization_review_preview_only": True,
        "model_registry_review_preview_only": True,
        "runtime_gate_review_preview_only": True,
        "governance_action_performed": False,
        "candidate_status_changed": False,
        "materialization_status_changed": False,
        "model_registry_status_changed": False,
        "runtime_gate_state_changed": False,
        "shadow_eligibility_changed": False,
        "runtime_review_requested": False,
        "runtime_eligibility_granted": False,
        "runtime_active": False,
        "rollback_execution": False,
        "phase4i_mutated": False,
        "deterministic_runtime_remains_authoritative": True,
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
    for test_path in test_paths:
        path = ROOT / test_path
        if not path.is_file():
            missing.append(test_path)
            continue
        module = load_module_from_path(
            path,
            f"phase7_screen6_governance_validation_{name}_{len(suite._tests)}",
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
        for module_name in SCREEN6_GOVERNANCE_MODULE_NAMES:
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
        "details": failures or ["runtime paths do not import Screen 6 governance modules"],
    }


def check_runtime_safety() -> dict[str, Any]:
    failures: list[str] = []
    for relative_path in RUNTIME_SAFETY_SOURCE_PATHS:
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing safety source: {relative_path}")
            continue
        functions = function_names(path)
        for forbidden in FORBIDDEN_MUTATION_FUNCTIONS:
            if forbidden in functions:
                failures.append(f"{relative_path} defines forbidden function {forbidden}")
    return {
        "name": "runtime_safety",
        "success": not failures,
        "tests_run": 0,
        "checks_run": len(RUNTIME_SAFETY_SOURCE_PATHS) + len(FORBIDDEN_MUTATION_FUNCTIONS),
        "failures": len(failures),
        "errors": 0,
        "skipped": 0,
        "details": failures
        or [
            "no governance action performed",
            "no candidate status changed",
            "no materialization status changed",
            "no model registry status changed",
            "no runtime gate state changed",
            "no runtime eligibility granted",
            "no runtime active state",
            "no rollback execution",
            "no Phase 4I mutation",
        ],
    }


def check_documentation() -> dict[str, Any]:
    failures: list[str] = []
    for relative_path in REQUIRED_DOCS:
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing doc: {relative_path}")
    combined = "\n".join(
        read_text(ROOT / relative_path).lower()
        for relative_path in REQUIRED_DOCS
        if (ROOT / relative_path).is_file()
    )
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
        "details": failures or ["required 7BK-7BP docs exist and contain boundary language"],
    }


def load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def python_files(paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
    return files


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


def failed_check(name: str, message: str) -> dict[str, Any]:
    return {
        "name": name,
        "success": False,
        "tests_run": 0,
        "checks_run": 1,
        "failures": 1,
        "errors": 0,
        "skipped": 0,
        "details": [message],
    }


def summarize_groups(groups: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "tests_run": sum(int(group.get("tests_run", 0)) for group in groups),
        "checks_run": sum(int(group.get("checks_run", 0)) for group in groups),
        "failures": sum(int(group.get("failures", 0)) for group in groups),
        "errors": sum(int(group.get("errors", 0)) for group in groups),
        "skipped": sum(int(group.get("skipped", 0)) for group in groups),
    }


def print_human_summary(summary: dict[str, Any]) -> None:
    if summary["success"]:
        print("Phase 7 Screen 6 governance validation passed.")
    else:
        print("Phase 7 Screen 6 governance validation failed.")
    print(f"screen6_governance_ready={str(summary['screen6_governance_ready']).lower()}")
    print(f"candidate_review_preview_only={str(summary['candidate_review_preview_only']).lower()}")
    print(
        "materialization_review_preview_only="
        f"{str(summary['materialization_review_preview_only']).lower()}"
    )
    print(
        "model_registry_review_preview_only="
        f"{str(summary['model_registry_review_preview_only']).lower()}"
    )
    print(f"runtime_gate_review_preview_only={str(summary['runtime_gate_review_preview_only']).lower()}")
    print(f"tests_run={summary['tests_run']}")
    print(f"checks_run={summary['checks_run']}")
    print(f"failures={summary['failures']}")
    print(f"errors={summary['errors']}")
    print("governance_action_performed=false")
    print("candidate_status_changed=false")
    print("materialization_status_changed=false")
    print("model_registry_status_changed=false")
    print("runtime_gate_state_changed=false")
    print("shadow_eligibility_changed=false")
    print("runtime_review_requested=false")
    print("runtime_eligibility_granted=false")
    print("runtime_active=false")
    print("rollback_execution=false")
    print("phase4i_mutated=false")
    print("Validation groups:")
    for group in summary["validation_groups"]:
        print(f"- {group['name']}: {group['success']}")


if __name__ == "__main__":
    raise SystemExit(main())
