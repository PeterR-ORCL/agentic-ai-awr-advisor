#!/usr/bin/env python3
"""Run the consolidated local Phase 7 validation harness."""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


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
        name="phase7_boundary",
        phase="7A",
        modules=("tests.test_phase7_learning_boundary",),
        description="Learning boundary and runtime isolation validation.",
    ),
    UnittestGroup(
        name="outcome_pattern_mining",
        phase="7B",
        modules=("tests.test_outcome_pattern_miner",),
        description="Outcome pattern mining remains observational only.",
    ),
    UnittestGroup(
        name="candidate_model",
        phase="7C",
        modules=("tests.test_learning_candidate_model",),
        description="Learning candidate records remain proposal-only.",
    ),
    UnittestGroup(
        name="candidate_generation",
        phase="7D",
        modules=("tests.test_learning_candidate_engine",),
        description="Candidate generation remains deterministic and proposal-only.",
    ),
    UnittestGroup(
        name="semantic_candidate_context",
        phase="7E",
        modules=("tests.test_semantic_candidate_context",),
        description="Semantic candidate context remains reviewer-assist only.",
    ),
    UnittestGroup(
        name="learning_governance_bridge",
        phase="7F",
        modules=("tests.test_learning_governance_bridge",),
        description="Learning governance transitions remain actor-gated and non-runtime-mutating.",
    ),
    UnittestGroup(
        name="dashboard_learning_visibility",
        phase="7G",
        modules=("tests.test_dashboard_learning_visibility",),
        description="Dashboard learning visibility remains read-only.",
    ),
    UnittestGroup(
        name="learning_cli",
        phase="7I",
        modules=("tests.test_learning_cli_commands", "tests.test_awr_memory_cli"),
        description="Learning CLI commands remain local, deterministic, and actor-gated.",
    ),
)


DASHBOARD_INTERACTIVITY_MODULES: tuple[str, ...] = (
    "tests.test_dashboard_interactivity_phase7h_acceptance",
    "tests.test_dashboard_cross_screen_selection_propagation",
    "tests.test_dashboard_screen6_fleet_governance_learning_exploration",
    "tests.test_dashboard_screen1_governance_parser_exploration",
    "tests.test_dashboard_screen5_recommendation_action_exploration",
    "tests.test_dashboard_screen4_historical_review_exploration",
    "tests.test_dashboard_screen2_diagnostic_exploration",
    "tests.test_dashboard_screen3_control_center",
    "tests.test_dashboard_interactivity_foundation",
)


STATIC_COMPILE_TARGETS: tuple[str, ...] = (
    "src/learning/outcome_pattern_miner.py",
    "src/learning/learning_candidate_model.py",
    "src/learning/learning_candidate_engine.py",
    "src/learning/semantic_candidate_context.py",
    "src/learning/learning_governance_bridge.py",
    "src/reporting/html_dashboard.py",
    "src/reporting/ai_display_metadata.py",
    "scripts/awr_memory_cli.py",
)


RUNTIME_PATHS: tuple[str, ...] = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/parsing",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
    "src/analysis",
)


PARSER_SCORING_DECISION_RECOMMENDATION_PATHS: tuple[str, ...] = (
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


PHASE7_SAFETY_SOURCE_PATHS: tuple[str, ...] = (
    "src/learning",
    "src/reporting/ai_display_metadata.py",
    "src/reporting/html_dashboard.py",
    "scripts/awr_memory_cli.py",
)


DOCUMENTATION_PATHS: tuple[str, ...] = (
    "docs/architecture/phase7_validation_matrix.md",
    "docs/architecture/phase7_validation_harness.md",
)


DOCUMENTATION_PHRASES: tuple[str, ...] = (
    "local and deterministic",
    "no runtime activation",
    "deterministic runtime remains authoritative",
    "semantic context remains reviewer-assist only",
    "dashboard interactivity remains read-only",
    "cli learning commands are local and actor-gated",
    "no parser/scoring/decision/recommendation behavior change",
)


RUNTIME_SAFETY_PHRASES: tuple[str, ...] = (
    "runtime_influence=false",
    "requires_human_review=true",
    "no runtime activation",
    "deterministic runtime remains authoritative",
    "semantic context remains reviewer-assist only",
    "learning candidates remain proposal/review context only",
    "dashboard interactivity is read-only",
    "cli learning commands are local and deterministic",
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
        description="Run local-only Phase 7 validation for Agentic AI AWR Advisor.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON only.")
    parser.add_argument(
        "--include-phase6",
        action="store_true",
        help="Also run scripts/run_phase6_validation.py when it is available.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_validation(include_phase6=args.include_phase6)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["success"] else 1


def run_validation(*, include_phase6: bool = False) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []

    groups.append(run_static_compile_group())
    for group in UNITTEST_GROUPS:
        groups.append(run_unittest_group(group))
    groups.append(run_dashboard_interactivity_group())
    groups.append(run_import_isolation_group())
    groups.append(run_runtime_safety_group())
    groups.append(run_documentation_group())
    if include_phase6:
        groups.append(run_phase6_group())

    totals = summarize_groups(groups)
    success = all(group["success"] for group in groups)
    return {
        "phase": "Phase 7",
        "command": "run_phase7_validation",
        "success": success,
        "validation_groups": groups,
        "tests_run": totals["tests_run"],
        "checks_run": totals["checks_run"],
        "failures": totals["failures"],
        "errors": totals["errors"],
        "skipped": totals["skipped"],
        "runtime_influence": False,
        "deterministic_runtime_remains_authoritative": True,
        "semantic_context_non_authoritative": True,
        "learning_candidates_proposal_only": True,
        "dashboard_interactivity_read_only": True,
        "cli_learning_local_only": True,
        "network_dependency": False,
        "database_dependency": False,
        "oracle_agent_memory_dependency": False,
        "phase6_validation_included": include_phase6,
    }


def run_static_compile_group() -> dict[str, Any]:
    failures: list[str] = []
    skipped = 0
    checks_run = 0

    with tempfile.TemporaryDirectory() as tempdir:
        temp_path = Path(tempdir)
        for index, relative_path in enumerate(STATIC_COMPILE_TARGETS):
            path = ROOT / relative_path
            if not path.exists():
                skipped += 1
                failures.append(f"missing compile target: {relative_path}")
                continue
            checks_run += 1
            cfile = temp_path / f"phase7_compile_{index}.pyc"
            try:
                py_compile.compile(str(path), cfile=str(cfile), doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append(f"{relative_path}: {exc.msg}")

    return make_group(
        name="static_compile",
        phase="7A-7I",
        success=not failures,
        description="Optional static compile checks for Phase 7 modules.",
        checks_run=checks_run,
        failures=len(failures),
        skipped=skipped,
        details=failures,
    )


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


def run_dashboard_interactivity_group() -> dict[str, Any]:
    script = ROOT / "scripts" / "run_phase7h_dashboard_validation.py"
    if script.is_file():
        command = (sys.executable, str(script.relative_to(ROOT)))
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        output = f"{completed.stdout}\n{completed.stderr}"
        counts = parse_unittest_counts(output)
        return make_group(
            name="dashboard_interactivity",
            phase="7H",
            success=completed.returncode == 0,
            description="Phase 7H dashboard interactivity remains browser-side and read-only.",
            tests_run=counts["tests_run"],
            failures=counts["failures"] if completed.returncode else 0,
            errors=counts["errors"] if completed.returncode else 0,
            skipped=counts["skipped"],
            details=[] if completed.returncode == 0 else concise_output(output),
            runner="scripts/run_phase7h_dashboard_validation.py",
            invoked=True,
            returncode=completed.returncode,
        )

    fallback_group = UnittestGroup(
        name="dashboard_interactivity",
        phase="7H",
        modules=DASHBOARD_INTERACTIVITY_MODULES,
        description="Phase 7H dashboard interactivity remains browser-side and read-only.",
    )
    result = run_unittest_group(fallback_group)
    result["runner"] = "unittest_fallback"
    result["invoked"] = False
    return result


def run_import_isolation_group() -> dict[str, Any]:
    inspected_files = collect_python_files(RUNTIME_PATHS)
    failures: list[str] = []
    checks_run = 0

    for path in inspected_files:
        imports = parse_imports(path)
        for module_name in imports:
            checks_run += 1
            if is_learning_module(module_name):
                failures.append(f"{relative(path)} imports learning module {module_name}")
            if is_learning_cli_module(module_name):
                failures.append(f"{relative(path)} imports learning CLI module {module_name}")

    dashboard_paths = collect_python_files(PARSER_SCORING_DECISION_RECOMMENDATION_PATHS)
    for path in dashboard_paths:
        imports = parse_imports(path)
        for module_name in imports:
            checks_run += 1
            if is_dashboard_interactivity_module(module_name):
                failures.append(
                    f"{relative(path)} imports dashboard interactivity module {module_name}"
                )

    return make_group(
        name="import_isolation",
        phase="7A-7J",
        success=not failures and bool(inspected_files),
        description="Runtime parser/scoring/decision/recommendation paths do not import learning.",
        checks_run=checks_run,
        failures=len(failures) + (0 if inspected_files else 1),
        details=failures or ([] if inspected_files else ["no runtime files inspected"]),
        inspected_files=[relative(path) for path in inspected_files],
    )


def run_runtime_safety_group() -> dict[str, Any]:
    failures: list[str] = []
    checks_run = 0

    for path in collect_python_files(PHASE7_SAFETY_SOURCE_PATHS):
        checks_run += 1
        failures.extend(find_runtime_influence_true_assignments(path))

    source_text = "\n".join(
        read_lower(path)
        for path in (
            ROOT / "docs" / "architecture" / "phase7_validation_matrix.md",
            ROOT / "docs" / "architecture" / "phase7_validation_harness.md",
            ROOT / "docs" / "architecture" / "phase7_learning_cli_operations.md",
            ROOT / "docs" / "architecture" / "phase7_cross_screen_selection_propagation.md",
            ROOT / "docs" / "architecture" / "phase7_dashboard_learning_visibility.md",
            ROOT / "scripts" / "awr_memory_cli.py",
        )
        if path.is_file()
    )
    for phrase in RUNTIME_SAFETY_PHRASES:
        checks_run += 1
        if phrase not in source_text:
            failures.append(f"missing runtime safety phrase: {phrase}")

    script_imports = parse_imports(ROOT / "scripts" / "run_phase7_validation.py")
    for module_name in script_imports:
        checks_run += 1
        if any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_SCRIPT_IMPORTS
        ):
            failures.append(f"validation harness imports unsafe dependency: {module_name}")

    return make_group(
        name="runtime_safety",
        phase="7A-7J",
        success=not failures,
        description="No runtime activation, DB, network, OCI, or authoritative semantic drift.",
        checks_run=checks_run,
        failures=len(failures),
        details=failures,
        runtime_influence=False,
        no_runtime_activation=True,
        deterministic_runtime_remains_authoritative=True,
        semantic_context_non_authoritative=True,
        learning_candidates_proposal_only=True,
        dashboard_interactivity_read_only=True,
        cli_learning_local_only=True,
        network_dependency=False,
        database_dependency=False,
        oracle_agent_memory_dependency=False,
    )


def run_documentation_group() -> dict[str, Any]:
    failures: list[str] = []
    checks_run = 0

    for relative_path in DOCUMENTATION_PATHS:
        checks_run += 1
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing documentation: {relative_path}")

    matrix_path = ROOT / "docs" / "architecture" / "phase7_validation_matrix.md"
    matrix_text = read_lower(matrix_path) if matrix_path.is_file() else ""
    for phrase in DOCUMENTATION_PHRASES:
        checks_run += 1
        if phrase not in matrix_text:
            failures.append(f"validation matrix missing phrase: {phrase}")

    required_headings = (
        "purpose",
        "scope",
        "non-goals",
        "validation groups",
        "phase 7a boundary validation",
        "phase 7b outcome pattern mining validation",
        "phase 7c candidate model validation",
        "phase 7d candidate generation validation",
        "phase 7e semantic candidate context validation",
        "phase 7f governance bridge validation",
        "phase 7g dashboard learning visibility validation",
        "phase 7h dashboard interactivity validation",
        "phase 7i learning cli validation",
        "import isolation validation",
        "runtime safety validation",
        "semantic boundary validation",
        "dashboard boundary validation",
        "cli boundary validation",
        "phase 6 regression validation",
        "validation commands",
        "acceptance criteria",
    )
    for heading in required_headings:
        checks_run += 1
        if heading not in matrix_text:
            failures.append(f"validation matrix missing section: {heading}")

    return make_group(
        name="documentation",
        phase="7J",
        success=not failures,
        description="Phase 7 validation documentation exists and preserves boundary language.",
        checks_run=checks_run,
        failures=len(failures),
        details=failures,
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

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(ROOT)
        if not existing_pythonpath
        else os.pathsep.join((str(ROOT), existing_pythonpath))
    )
    completed = subprocess.run(
        (sys.executable, str(script.relative_to(ROOT))),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    counts = parse_phase6_counts(output)
    return make_group(
        name="phase6_regression",
        phase="6",
        success=completed.returncode == 0,
        description="Optional Phase 6 regression validation.",
        tests_run=counts["tests_run"],
        failures=counts["failures"] if completed.returncode else 0,
        errors=counts["errors"] if completed.returncode else 0,
        details=[] if completed.returncode == 0 else concise_output(output),
        invoked=True,
        returncode=completed.returncode,
    )


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
    details: list[str] | None = None,
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
        "details": details or [],
    }
    group.update(extra)
    return group


def summarize_groups(groups: Iterable[dict[str, Any]]) -> dict[str, int]:
    totals = {"tests_run": 0, "checks_run": 0, "failures": 0, "errors": 0, "skipped": 0}
    for group in groups:
        for key in totals:
            totals[key] += int(group.get(key, 0))
    return totals


def module_to_path(module_name: str) -> Path:
    return ROOT / (module_name.replace(".", "/") + ".py")


def validation_summaries(entries: Sequence[tuple[unittest.case.TestCase, str]]) -> list[str]:
    summaries: list[str] = []
    for test_case, traceback_text in entries:
        lines = [line.strip() for line in traceback_text.strip().splitlines() if line.strip()]
        tail = lines[-1] if lines else "no traceback available"
        summaries.append(f"{test_case.id()}: {tail}")
    return summaries


def parse_unittest_counts(output: str) -> dict[str, int]:
    tests_run = 0
    failures = 0
    errors = 0
    skipped = 0

    matches = re.findall(r"Ran (\d+) tests?", output)
    if matches:
        tests_run = int(matches[-1])

    failed = re.search(r"FAILED \(([^)]+)\)", output)
    if failed:
        for part in failed.group(1).split(","):
            key, _, value = part.strip().partition("=")
            if key == "failures" and value.isdigit():
                failures = int(value)
            elif key == "errors" and value.isdigit():
                errors = int(value)
            elif key == "skipped" and value.isdigit():
                skipped = int(value)
    else:
        skipped_match = re.search(r"OK \(skipped=(\d+)\)", output)
        if skipped_match:
            skipped = int(skipped_match.group(1))

    return {
        "tests_run": tests_run,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
    }


def parse_phase6_counts(output: str) -> dict[str, int]:
    try:
        start = output.index("{")
        end = output.rindex("}") + 1
        data = json.loads(output[start:end])
    except (ValueError, json.JSONDecodeError):
        return parse_unittest_counts(output)
    return {
        "tests_run": int(data.get("tests_run", 0)),
        "failures": int(data.get("failures", 0)),
        "errors": int(data.get("errors", 0)),
        "skipped": 0,
    }


def concise_output(output: str, *, limit: int = 20) -> list[str]:
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    return lines[-limit:]


def collect_python_files(paths: Sequence[str]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
    return sorted(set(files))


def parse_imports(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def is_learning_module(module_name: str) -> bool:
    return (
        module_name == "learning"
        or module_name.startswith("learning.")
        or module_name == "src.learning"
        or module_name.startswith("src.learning.")
    )


def is_learning_cli_module(module_name: str) -> bool:
    return (
        module_name == "awr_memory_cli"
        or module_name.startswith("awr_memory_cli.")
        or module_name == "scripts.awr_memory_cli"
        or module_name.startswith("scripts.awr_memory_cli.")
    )


def is_dashboard_interactivity_module(module_name: str) -> bool:
    return (
        module_name == "html_dashboard"
        or module_name.startswith("html_dashboard.")
        or module_name == "src.reporting.html_dashboard"
        or module_name.startswith("src.reporting.html_dashboard.")
        or module_name == "src.reporting.ai_display_metadata"
        or module_name.startswith("src.reporting.ai_display_metadata.")
    )


def find_runtime_influence_true_assignments(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
    failures: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and is_true_constant(node.value):
            for target in node.targets:
                if assignment_targets_runtime_influence(target):
                    failures.append(f"{relative(path)}:{node.lineno} assigns runtime_influence=True")
        elif isinstance(node, ast.AnnAssign) and node.value and is_true_constant(node.value):
            if assignment_targets_runtime_influence(node.target):
                failures.append(f"{relative(path)}:{node.lineno} assigns runtime_influence=True")
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if is_runtime_influence_key(key) and is_true_constant(value):
                    failures.append(f"{relative(path)}:{node.lineno} sets runtime_influence to true")
        elif isinstance(node, ast.keyword):
            if node.arg == "runtime_influence" and is_true_constant(node.value):
                failures.append(f"{relative(path)}:{node.lineno} passes runtime_influence=True")
    return failures


def assignment_targets_runtime_influence(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "runtime_influence"
    if isinstance(node, ast.Attribute):
        return node.attr == "runtime_influence"
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(assignment_targets_runtime_influence(child) for child in node.elts)
    return False


def is_runtime_influence_key(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value == "runtime_influence"


def is_true_constant(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def read_lower(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").lower()


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def print_human_summary(summary: dict[str, Any]) -> None:
    status = "passed" if summary["success"] else "failed"
    print(f"Phase 7 validation {status}.")
    print(f"tests_run: {summary['tests_run']}")
    print(f"checks_run: {summary['checks_run']}")
    print(f"failures: {summary['failures']}")
    print(f"errors: {summary['errors']}")
    print(f"skipped: {summary['skipped']}")
    print()
    print("Boundary confirmations:")
    print("runtime_influence=false")
    print("requires_human_review=true")
    print("no runtime activation")
    print("deterministic runtime remains authoritative")
    print("semantic context remains reviewer-assist only")
    print("learning candidates remain proposal/review context only")
    print("dashboard interactivity is read-only")
    print("CLI learning commands are local and deterministic")
    print()
    print("Validation groups:")
    for group in summary["validation_groups"]:
        group_status = "PASS" if group["success"] else "FAIL"
        print(
            f"- {group['name']}: {group_status} "
            f"(tests={group['tests_run']}, checks={group['checks_run']}, "
            f"failures={group['failures']}, errors={group['errors']}, skipped={group['skipped']})"
        )
        if not group["success"]:
            for detail in group.get("details", [])[:8]:
                print(f"  {detail}")


if __name__ == "__main__":
    raise SystemExit(main())
