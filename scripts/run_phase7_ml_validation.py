#!/usr/bin/env python3
"""Run local Phase 7S-7Z ML / adaptive scoring validation."""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import subprocess
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class UnittestGroup:
    name: str
    phase: str
    modules: tuple[str, ...]
    description: str


UNITTEST_GROUPS: tuple[UnittestGroup, ...] = (
    UnittestGroup(
        name="ml_boundary",
        phase="7S",
        modules=("tests.test_phase7_ml_adaptive_scoring_boundary",),
        description="ML boundary exists and remains shadow/advisory only.",
    ),
    UnittestGroup(
        name="feature_label_dataset",
        phase="7T",
        modules=("tests.test_phase7_feature_label_dataset",),
        description="Feature / label datasets are governed inputs, not models.",
    ),
    UnittestGroup(
        name="trend_aware_scoring",
        phase="7U",
        modules=("tests.test_phase7_trend_aware_scoring",),
        description="Trend-aware scoring remains advisory and non-runtime-active.",
    ),
    UnittestGroup(
        name="shadow_ml_model_interface",
        phase="7V",
        modules=("tests.test_phase7_shadow_ml_model_interface",),
        description="Shadow ML output remains non-authoritative.",
    ),
    UnittestGroup(
        name="ml_training_backtesting",
        phase="7W",
        modules=("tests.test_phase7_ml_training_backtesting",),
        description="Training/backtesting artifacts remain evaluation records only.",
    ),
    UnittestGroup(
        name="ml_explainability",
        phase="7X",
        modules=("tests.test_phase7_ml_explainability",),
        description="Explainability remains explanation-only and not runtime truth.",
    ),
    UnittestGroup(
        name="ml_model_registry",
        phase="7Y",
        modules=("tests.test_phase7_ml_model_registry",),
        description="Model registry remains governance metadata only.",
    ),
)

ML_SOURCE_PATHS: tuple[str, ...] = (
    "src/learning/ml_boundary.py",
    "src/learning/feature_label_dataset.py",
    "src/learning/trend_aware_scoring.py",
    "src/learning/shadow_ml_model_interface.py",
    "src/learning/ml_training_backtesting.py",
    "src/learning/ml_explainability.py",
    "src/learning/ml_model_registry.py",
)

ML_MODULES: tuple[str, ...] = (
    "ml_boundary",
    "feature_label_dataset",
    "trend_aware_scoring",
    "shadow_ml_model_interface",
    "ml_training_backtesting",
    "ml_explainability",
    "ml_model_registry",
)

IMPORT_ISOLATION_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("run_analysis", ("scripts/run_analysis.py",), ML_MODULES),
    ("parser_runtime", ("src/parser", "src/parsing"), ML_MODULES),
    ("scoring_runtime", ("src/scoring", "src/analysis/scoring_adapter.py"), ML_MODULES),
    ("decision_runtime", ("src/decision", "src/analysis/decision_engine.py"), ML_MODULES),
    (
        "recommendation_runtime",
        (
            "src/recommendation",
            "src/recommendations",
            "src/analysis/recommendation_engine.py",
            "src/analysis/recommendation_catalog.py",
        ),
        ML_MODULES,
    ),
)

FORBIDDEN_ACTIVE_FUNCTIONS: tuple[str, ...] = (
    "deploy_model",
    "activate_model",
    "save_model",
    "load_model",
    "update_runtime_scoring",
    "replace_scoring_engine",
    "apply_ml_score",
    "grant_runtime_eligibility",
    "auto_apply",
    "autonomous_apply",
)

RUNTIME_GUARDED_FIELDS: frozenset[str] = frozenset(
    (
        "runtime_active",
        "runtime_influence",
        "runtime_influence_granted",
        "runtime_eligibility_granted",
    )
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

REQUIRED_ML_DOCS: tuple[str, ...] = (
    "docs/architecture/phase7_ml_adaptive_scoring_boundary.md",
    "docs/architecture/phase7_ml_lifecycle.md",
    "docs/architecture/phase7_feature_label_dataset.md",
    "docs/architecture/phase7_feature_label_schema.md",
    "docs/architecture/phase7_trend_aware_scoring.md",
    "docs/architecture/phase7_trend_aware_scoring_model.md",
    "docs/architecture/phase7_shadow_ml_model_interface.md",
    "docs/architecture/phase7_shadow_ml_output_model.md",
    "docs/architecture/phase7_ml_training_backtesting.md",
    "docs/architecture/phase7_ml_backtesting_model.md",
    "docs/architecture/phase7_ml_explainability.md",
    "docs/architecture/phase7_ml_explainability_model.md",
    "docs/architecture/phase7_ml_model_registry.md",
    "docs/architecture/phase7_ml_governance_model.md",
    "docs/architecture/phase7_ml_validation_matrix.md",
    "docs/architecture/phase7_ml_readiness.md",
    "docs/architecture/phase7_ml_release_certification.md",
    "docs/architecture/phase7_ml_operational_checklist.md",
)

VALIDATION_MATRIX_HEADINGS: tuple[str, ...] = (
    "purpose",
    "scope",
    "non-goals",
    "validation categories",
    "7s ml boundary validation",
    "7t feature / label dataset validation",
    "7u trend-aware scoring validation",
    "7v shadow ml interface validation",
    "7w training / backtesting validation",
    "7x explainability validation",
    "7y model registry validation",
    "import isolation validation",
    "runtime safety validation",
    "deterministic runtime boundary validation",
    "phase 4i contract boundary validation",
    "materialization regression validation",
    "phase 7 foundation regression validation",
    "phase 6 regression validation",
    "acceptance criteria",
)

DOCUMENTATION_PHRASES: tuple[str, ...] = (
    "ml remains shadow/advisory",
    "dataset is not a model",
    "training/backtesting is evaluation only",
    "explainability is not runtime truth",
    "model registry is governance metadata only",
    "no model is runtime active",
    "no runtime scoring changes are applied",
    "deterministic runtime remains authoritative",
    "runtime_active=false",
    "runtime_influence=false",
    "runtime_influence_granted=false",
    "runtime_eligibility_granted=false",
    "phase 4i contract remains protected",
    "phase 8 is not implemented",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local-only Phase 7S-7Z ML / adaptive scoring validation.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument(
        "--include-phase6",
        action="store_true",
        help="Also run Phase 6 validation when available.",
    )
    parser.add_argument(
        "--include-phase7-foundation",
        action="store_true",
        help="Also run scripts/run_phase7_validation.py as a Phase 7 foundation regression.",
    )
    parser.add_argument(
        "--include-materialization",
        action="store_true",
        help="Also run scripts/run_phase7_materialization_validation.py.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_validation(
        include_phase6=args.include_phase6,
        include_phase7_foundation=args.include_phase7_foundation,
        include_materialization=args.include_materialization,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["success"] else 1


def run_validation(
    *,
    include_phase6: bool = False,
    include_phase7_foundation: bool = False,
    include_materialization: bool = False,
) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []

    for group in UNITTEST_GROUPS:
        groups.append(run_unittest_group(group))
    groups.append(run_import_isolation_group())
    groups.append(run_runtime_safety_group())
    groups.append(run_documentation_group())
    if include_materialization:
        groups.append(
            run_command_group(
                "materialization_regression",
                "7M-7R",
                "scripts/run_phase7_materialization_validation.py",
                python=sys.executable,
            )
        )
    if include_phase7_foundation:
        groups.append(
            run_command_group(
                "phase7_foundation_regression",
                "7A-7L",
                "scripts/run_phase7_validation.py",
                python=phase_python(),
            )
        )
    if include_phase6:
        groups.append(run_phase6_group())

    totals = summarize_groups(groups)
    success = all(group["success"] for group in groups)
    return {
        "phase": "Phase 7S-7Z",
        "command": "run_phase7_ml_validation",
        "success": success,
        "validation_groups": groups,
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "ml_shadow_only": True,
        "dataset_is_not_model": True,
        "trend_aware_scoring_advisory_only": True,
        "shadow_ml_non_authoritative": True,
        "training_backtesting_evaluation_only": True,
        "explainability_not_runtime_truth": True,
        "model_registry_governance_only": True,
        "runtime_active": False,
        "runtime_influence": False,
        "runtime_influence_granted": False,
        "runtime_eligibility_granted": False,
        "deterministic_runtime_remains_authoritative": True,
        "network_dependency": False,
        "database_dependency": False,
        "oracle_agent_memory_dependency": False,
        "phase6_validation_included": include_phase6,
        "phase7_foundation_validation_included": include_phase7_foundation,
        "materialization_validation_included": include_materialization,
    }


def run_unittest_group(group: UnittestGroup) -> dict[str, Any]:
    missing = [module for module in group.modules if not module_to_path(module).is_file()]
    if missing:
        return make_group(
            name=group.name,
            phase=group.phase,
            success=False,
            description=group.description,
            failures=len(missing),
            skipped=len(missing),
            details=[f"missing unittest module: {module}" for module in missing],
            modules=list(group.modules),
        )

    suite = unittest.defaultTestLoader.loadTestsFromNames(group.modules)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    return make_group(
        name=group.name,
        phase=group.phase,
        success=result.wasSuccessful(),
        description=group.description,
        tests_run=result.testsRun,
        failures=len(result.failures),
        errors=len(result.errors),
        skipped=len(result.skipped),
        details=validation_summaries(result.failures + result.errors),
        modules=list(group.modules),
    )


def run_import_isolation_group() -> dict[str, Any]:
    failures: list[str] = []
    inspected_files: list[str] = []
    checks_run = 0

    for rule_name, paths, forbidden_modules in IMPORT_ISOLATION_RULES:
        files = collect_python_files(paths)
        if not files:
            failures.append(f"{rule_name}: no runtime files inspected")
            continue
        for path in files:
            inspected_files.append(relative(path))
            imports = parse_imports(path)
            for forbidden in forbidden_modules:
                checks_run += 1
                matches = sorted(
                    imported for imported in imports if import_matches(imported, forbidden)
                )
                for imported in matches:
                    failures.append(
                        f"{relative(path)} imports {imported}; "
                        f"{rule_name} must not import {forbidden}"
                    )

    return make_group(
        name="import_isolation",
        phase="7Z",
        success=not failures,
        description=(
            "run_analysis, parser, scoring, decision, and recommendation paths "
            "do not import Phase 7S-7Y ML/adaptive modules."
        ),
        checks_run=checks_run,
        failures=len(failures),
        details=failures,
        inspected_files=sorted(set(inspected_files)),
    )


def run_runtime_safety_group() -> dict[str, Any]:
    failures: list[str] = []
    checks_run = 0

    for path in ml_source_files():
        tree = parse_ast(path)
        checks_run += 1
        failures.extend(find_true_runtime_field_values(path, tree))

        function_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for forbidden_name in FORBIDDEN_ACTIVE_FUNCTIONS:
            checks_run += 1
            if forbidden_name in function_names:
                failures.append(f"{relative(path)} defines active ML function {forbidden_name}")

        imports = parse_imports(path)
        for imported in imports:
            checks_run += 1
            if is_forbidden_import(imported):
                failures.append(f"{relative(path)} imports unsafe dependency {imported}")

    script_imports = parse_imports(ROOT / "scripts" / "run_phase7_ml_validation.py")
    for imported in script_imports:
        checks_run += 1
        if is_forbidden_import(imported):
            failures.append(f"validation script imports unsafe dependency {imported}")

    return make_group(
        name="runtime_safety",
        phase="7Z",
        success=not failures,
        description=(
            "ML/adaptive modules grant no runtime influence or eligibility, "
            "activate no model, and expose no deployment/scoring replacement functions."
        ),
        checks_run=checks_run,
        failures=len(failures),
        details=failures,
        ml_shadow_only=True,
        dataset_is_not_model=True,
        trend_aware_scoring_advisory_only=True,
        shadow_ml_non_authoritative=True,
        training_backtesting_evaluation_only=True,
        explainability_not_runtime_truth=True,
        model_registry_governance_only=True,
        runtime_active=False,
        runtime_influence=False,
        runtime_influence_granted=False,
        runtime_eligibility_granted=False,
        deterministic_runtime_remains_authoritative=True,
        network_dependency=False,
        database_dependency=False,
        oracle_agent_memory_dependency=False,
    )


def run_documentation_group() -> dict[str, Any]:
    failures: list[str] = []
    checks_run = 0

    for relative_path in REQUIRED_ML_DOCS:
        checks_run += 1
        if not (ROOT / relative_path).is_file():
            failures.append(f"missing documentation: {relative_path}")

    matrix_path = ROOT / "docs" / "architecture" / "phase7_ml_validation_matrix.md"
    matrix_text = read_text(matrix_path).lower() if matrix_path.is_file() else ""
    for heading in VALIDATION_MATRIX_HEADINGS:
        checks_run += 1
        if heading not in matrix_text:
            failures.append(f"validation matrix missing section: {heading}")

    combined_docs = "\n".join(
        read_text(ROOT / relative_path).lower()
        for relative_path in REQUIRED_ML_DOCS
        if (ROOT / relative_path).is_file()
    )
    for phrase in DOCUMENTATION_PHRASES:
        checks_run += 1
        if phrase not in combined_docs:
            failures.append(f"documentation missing boundary phrase: {phrase}")

    return make_group(
        name="documentation",
        phase="7Z",
        success=not failures,
        description="ML validation/readiness/certification documentation is complete.",
        checks_run=checks_run,
        failures=len(failures),
        details=failures,
    )


def run_command_group(name: str, phase: str, script: str, *, python: str) -> dict[str, Any]:
    path = ROOT / script
    if not path.is_file():
        return make_group(
            name=name,
            phase=phase,
            success=False,
            description=f"Optional command regression for {script}.",
            failures=1,
            skipped=1,
            details=[f"missing script: {script}"],
            invoked=False,
        )

    completed = subprocess.run(
        (python, script),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=validation_env(),
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    counts = parse_counts(output)
    return make_group(
        name=name,
        phase=phase,
        success=completed.returncode == 0,
        description=f"Optional command regression for {script}.",
        tests_run=counts["tests_run"],
        checks_run=counts["checks_run"] + 1,
        failures=0 if completed.returncode == 0 else max(counts["failures"], 1),
        errors=counts["errors"],
        skipped=counts["skipped"],
        details=[] if completed.returncode == 0 else concise_output(output),
        runner=script,
        invoked=True,
        returncode=completed.returncode,
    )


def run_phase6_group() -> dict[str, Any]:
    script = ROOT / "scripts" / "run_phase6_validation.py"
    if not script.is_file():
        return make_group(
            name="phase6_regression",
            phase="6",
            success=True,
            description="Optional Phase 6 regression validation.",
            skipped=1,
            details=["scripts/run_phase6_validation.py not found; skipped"],
            invoked=False,
        )

    completed = subprocess.run(
        (phase_python(), "scripts/run_phase6_validation.py"),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**validation_env(), "PYTHONPATH": phase_pythonpath()},
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    counts = parse_counts(output)
    return make_group(
        name="phase6_regression",
        phase="6",
        success=completed.returncode == 0,
        description="Optional Phase 6 regression validation.",
        tests_run=counts["tests_run"],
        checks_run=counts["checks_run"] + 1,
        failures=0 if completed.returncode == 0 else max(counts["failures"], 1),
        errors=counts["errors"],
        skipped=counts["skipped"],
        details=[] if completed.returncode == 0 else concise_output(output),
        runner="scripts/run_phase6_validation.py",
        invoked=True,
        returncode=completed.returncode,
    )


def find_true_runtime_field_values(path: Path, tree: ast.AST) -> list[str]:
    failures: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and is_true_constant(node.value):
            for target in node.targets:
                field_name = assignment_field_name(target)
                if field_name in RUNTIME_GUARDED_FIELDS:
                    failures.append(f"{relative(path)} assigns {field_name}=True")
        elif isinstance(node, ast.AnnAssign) and node.value is not None and is_true_constant(node.value):
            field_name = assignment_field_name(node.target)
            if field_name in RUNTIME_GUARDED_FIELDS:
                failures.append(f"{relative(path)} assigns {field_name}=True")
        elif isinstance(node, ast.keyword) and node.arg in RUNTIME_GUARDED_FIELDS:
            if is_true_constant(node.value):
                failures.append(f"{relative(path)} passes {node.arg}=True")
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                field_name = string_constant(key)
                if field_name in RUNTIME_GUARDED_FIELDS and is_true_constant(value):
                    failures.append(f"{relative(path)} sets {field_name}=True in dict")
    return failures


def assignment_field_name(target: ast.AST) -> str | None:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    if isinstance(target, ast.Subscript):
        return string_constant(target.slice)
    return None


def string_constant(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def is_true_constant(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def collect_python_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(
                sorted(
                    child
                    for child in path.rglob("*.py")
                    if child.is_file() and "__pycache__" not in child.parts
                )
            )
    return files


def ml_source_files() -> list[Path]:
    return [ROOT / relative_path for relative_path in ML_SOURCE_PATHS]


def parse_ast(path: Path) -> ast.AST:
    return ast.parse(read_text(path), filename=str(path))


def parse_imports(path: Path) -> set[str]:
    tree = parse_ast(path)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
            for alias in node.names:
                if alias.name != "*":
                    imports.add(f"{node.module}.{alias.name}")
                    imports.add(alias.name)
    return imports


def import_matches(imported: str, forbidden_short_name: str) -> bool:
    forbidden_full = f"src.learning.{forbidden_short_name}"
    forbidden_learning = f"learning.{forbidden_short_name}"
    return imported in {
        forbidden_short_name,
        forbidden_learning,
        forbidden_full,
    } or imported.startswith(f"{forbidden_full}.") or imported.startswith(f"{forbidden_learning}.")


def is_forbidden_import(imported: str) -> bool:
    return any(
        imported == forbidden or imported.startswith(f"{forbidden}.")
        for forbidden in FORBIDDEN_SCRIPT_IMPORTS
    )


def module_to_path(module_name: str) -> Path:
    return ROOT / (module_name.replace(".", os.sep) + ".py")


def validation_summaries(entries: Sequence[tuple[unittest.case.TestCase, str]]) -> list[str]:
    return [f"{case.id()}: {summary.splitlines()[-1]}" for case, summary in entries]


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


def summarize_groups(groups: Sequence[dict[str, Any]]) -> dict[str, int]:
    totals = {"tests_run": 0, "checks_run": 0, "failures": 0, "errors": 0, "skipped": 0}
    for group in groups:
        for key in totals:
            totals[key] += int(group.get(key, 0))
    return totals


def make_group(
    *,
    name: str,
    phase: str,
    success: bool,
    description: str,
    tests_run: int = 0,
    checks_run: int = 0,
    failures: int = 0,
    errors: int = 0,
    skipped: int = 0,
    details: Sequence[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    group = {
        "name": name,
        "phase": phase,
        "success": success,
        "description": description,
        "tests_run": tests_run,
        "checks_run": checks_run,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "details": list(details or ()),
    }
    group.update(extra)
    return group


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def print_human_summary(summary: dict[str, Any]) -> None:
    status = "passed" if summary["success"] else "failed"
    print(f"Phase 7 ML validation {status}.")
    print(f"tests_run: {summary['tests_run']}")
    print(f"checks_run: {summary['checks_run']}")
    print(f"failures: {summary['failures']}")
    print(f"errors: {summary['errors']}")
    print(f"skipped: {summary['skipped']}")
    print()
    print("Validation groups:")
    for group in summary["validation_groups"]:
        group_status = "PASS" if group["success"] else "FAIL"
        print(f"- {group['name']}: {group_status}")
    print()
    print("Boundary confirmations:")
    print("ml_shadow_only=true")
    print("dataset_is_not_model=true")
    print("trend_aware_scoring_advisory_only=true")
    print("shadow_ml_non_authoritative=true")
    print("training_backtesting_evaluation_only=true")
    print("explainability_not_runtime_truth=true")
    print("model_registry_governance_only=true")
    print("runtime_active=false")
    print("runtime_influence=false")
    print("runtime_influence_granted=false")
    print("runtime_eligibility_granted=false")
    print("deterministic runtime remains authoritative")

    if not summary["success"]:
        print()
        print("Failed groups:")
        for group in summary["validation_groups"]:
            if group["success"]:
                continue
            print(f"- {group['name']}")
            for detail in group.get("details", [])[:8]:
                print(f"  {detail}")


if __name__ == "__main__":
    raise SystemExit(main())
