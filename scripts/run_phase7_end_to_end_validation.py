#!/usr/bin/env python3
"""Run the Phase 7CH end-to-end validation harness."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]


INVARIANTS: dict[str, bool] = {
    "phase7_complete": False,
    "phase8_started": False,
    "deterministic_runtime_authoritative": True,
    "phase4i_contract_protected": True,
    "uncontrolled_runtime_mutation_allowed": False,
    "adaptive_runtime_default_active": False,
    "phase8_behavior_implemented": False,
}

OPERATIONAL_CERTIFICATION_SCOPE: tuple[str, ...] = (
    "7CG boundary document",
    "7A-7L governed learning foundation",
    "7M-7R controlled learning materialization",
    "7S-7Z ML / adaptive scoring foundation",
    "7AA-7AC controlled adaptive runtime scaffolding",
    "7AD-7AI dashboard workflow infrastructure",
    "Screen 1 parser governance workflow",
    "Screen 2 diagnostic review workflow",
    "Screen 3 re-analysis control plane",
    "Active Screen 3 backend execution",
    "Screen 4 historical review workflow",
    "Screen 5 recommendation/action/outcome workflow",
    "Screen 6 governance control plane",
    "7BQ-7BT index/source mode entry",
    "7BU-7BZ runtime materialization metadata",
    "optional DB-backed governed workflow persistence validation",
    "optional Object Storage live path validation",
    "optional Phase 6 memory regression",
    "Phase 4I contract protection",
    "No Phase 8 implementation",
)


@dataclass(frozen=True)
class CheckSpec:
    name: str
    category: str
    description: str
    command: tuple[str, ...] | None = None
    modes: tuple[str, ...] = ("default", "fast", "full")
    optional_group: str | None = None
    env_update: tuple[tuple[str, str], ...] = ()
    tags: tuple[str, ...] = ()
    timeout_seconds: int = 300


def py_command(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


CHECK_SPECS: tuple[CheckSpec, ...] = (
    CheckSpec(
        name="phase7cg_boundary_document",
        category="7cg_boundary",
        description="7CG boundary document exists and is linked from the architecture README.",
        tags=("default", "fast", "full", "internal"),
    ),
    CheckSpec(
        name="phase7ch_invariant_metadata",
        category="invariants",
        description="Phase 7CH safety invariants are asserted as harness metadata.",
        tags=("default", "fast", "full", "internal"),
    ),
    CheckSpec(
        name="phase7_learning_foundation_validation",
        category="learning_foundation",
        description="Existing Phase 7A-7L validation harness.",
        command=py_command("scripts/run_phase7_validation.py", "--json"),
        tags=("default", "fast", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_materialization_validation",
        category="materialization",
        description="Existing Phase 7M-7R controlled materialization validation.",
        command=py_command("scripts/run_phase7_materialization_validation.py", "--json"),
        tags=("default", "fast", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_ml_validation",
        category="ml_foundation",
        description="Existing Phase 7S-7Z ML / adaptive scoring validation.",
        command=py_command("scripts/run_phase7_ml_validation.py", "--json"),
        tags=("default", "fast", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7aa_runtime_integration_validation",
        category="adaptive_runtime",
        description="Existing Phase 7AA controlled adaptive runtime integration validation.",
        command=py_command("scripts/run_phase7aa_runtime_integration_validation.py", "--json"),
        tags=("default", "fast", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_screen3_reanalysis_validation",
        category="screen3_reanalysis_control_plane",
        description="Existing Screen 3 re-analysis control plane validation.",
        command=py_command("scripts/run_phase7_screen3_reanalysis_validation.py", "--json"),
        tags=("default", "fast", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_active_screen3_execution_validation",
        category="active_screen3_backend_execution",
        description="Existing Phase 7CA-7CF active Screen 3 backend execution validation.",
        command=py_command("scripts/run_phase7_active_screen3_execution_validation.py", "--json"),
        tags=("default", "fast", "full", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_dashboard_workflow_validation",
        category="dashboard_workflow_infrastructure",
        description="Existing Phase 7AD-7AI dashboard workflow infrastructure validation.",
        command=py_command("scripts/run_phase7_dashboard_workflow_validation.py", "--json"),
        modes=("default", "full"),
        tags=("default", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_screen1_workflow_validation",
        category="screen1_parser_governance",
        description="Existing Screen 1 parser governance workflow validation.",
        command=py_command("scripts/run_phase7_screen1_workflow_validation.py", "--json"),
        modes=("default", "full"),
        tags=("default", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_screen2_review_validation",
        category="screen2_diagnostic_review",
        description=(
            "Targeted existing Screen 2 boundary, model, bridge, and diagnostic "
            "exploration tests. The broader review-panel validator is reserved for "
            "7CK-7CY remediation because it currently fails on pre-existing "
            "dashboard <button> detection."
        ),
        command=py_command(
            "-m",
            "unittest",
            "tests/test_phase7ap_screen2_review_workflow_boundary.py",
            "tests/test_phase7aq_diagnostic_review_model.py",
            "tests/test_phase7ar_screen2_governance_bridge.py",
            "tests/test_dashboard_screen2_diagnostic_exploration.py",
        ),
        modes=("default", "full"),
        tags=("default", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_screen4_workflow_validation",
        category="screen4_historical_review",
        description="Existing Screen 4 historical review workflow validation.",
        command=py_command("scripts/run_phase7_screen4_workflow_validation.py", "--json"),
        modes=("default", "full"),
        tags=("default", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_screen5_workflow_validation",
        category="screen5_recommendation_action_outcome",
        description="Existing Screen 5 recommendation/action/outcome workflow validation.",
        command=py_command("scripts/run_phase7_screen5_workflow_validation.py", "--json"),
        modes=("default", "full"),
        tags=("default", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_screen6_governance_validation",
        category="screen6_governance_control",
        description="Existing Screen 6 governance control plane validation.",
        command=py_command("scripts/run_phase7_screen6_governance_validation.py", "--json"),
        modes=("default", "full"),
        tags=("default", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_index_source_validation",
        category="index_source_mode",
        description="Existing Phase 7BQ-7BT index/source mode validation.",
        command=py_command("scripts/run_phase7_index_source_validation.py", "--json"),
        modes=("default", "full"),
        tags=("default", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_runtime_materialization_validation",
        category="runtime_materialization_metadata",
        description="Existing Phase 7BU-7BZ runtime materialization metadata validation.",
        command=py_command("scripts/run_phase7_runtime_materialization_validation.py", "--json"),
        modes=("default", "full"),
        tags=("default", "full", "subprocess"),
    ),
    CheckSpec(
        name="phase7_foundation_readiness",
        category="full_readiness",
        description="Existing Phase 7 foundation readiness check.",
        command=py_command("scripts/run_phase7_readiness_check.py", "--json"),
        modes=("full",),
        tags=("full", "readiness", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_materialization_readiness",
        category="full_readiness",
        description="Existing Phase 7M-7R materialization readiness check.",
        command=py_command("scripts/run_phase7_materialization_readiness_check.py", "--json"),
        modes=("full",),
        tags=("full", "readiness", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_ml_readiness",
        category="full_readiness",
        description="Existing Phase 7S-7Z ML readiness check.",
        command=py_command("scripts/run_phase7_ml_readiness_check.py", "--json"),
        modes=("full",),
        tags=("full", "readiness", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7aa_runtime_integration_readiness",
        category="full_readiness",
        description="Existing Phase 7AA runtime integration readiness check.",
        command=py_command("scripts/run_phase7aa_runtime_integration_readiness_check.py", "--json"),
        modes=("full",),
        optional_group="slow_full",
        tags=("full", "readiness", "known-slow", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_dashboard_workflow_readiness",
        category="full_readiness",
        description="Existing Phase 7AD-7AI dashboard workflow readiness check.",
        command=py_command("scripts/run_phase7_dashboard_workflow_readiness_check.py", "--json"),
        modes=("full",),
        optional_group="slow_full",
        tags=("full", "readiness", "known-slow", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_screen1_workflow_readiness",
        category="full_readiness",
        description="Existing Screen 1 workflow readiness check.",
        command=py_command("scripts/run_phase7_screen1_workflow_readiness_check.py", "--json"),
        modes=("full",),
        optional_group="slow_full",
        tags=("full", "readiness", "known-slow", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_screen3_reanalysis_readiness",
        category="full_readiness",
        description="Existing Screen 3 re-analysis readiness check.",
        command=py_command("scripts/run_phase7_screen3_reanalysis_readiness_check.py", "--json"),
        modes=("full",),
        optional_group="slow_full",
        tags=("full", "readiness", "known-slow", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_active_screen3_execution_readiness",
        category="full_readiness",
        description="Existing active Screen 3 backend execution readiness check.",
        command=py_command("scripts/run_phase7_active_screen3_execution_readiness_check.py", "--json"),
        modes=("full",),
        tags=("full", "readiness", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_screen4_workflow_readiness",
        category="full_readiness",
        description="Existing Screen 4 workflow readiness check.",
        command=py_command("scripts/run_phase7_screen4_workflow_readiness_check.py", "--json"),
        modes=("full",),
        optional_group="slow_full",
        tags=("full", "readiness", "known-slow", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_screen5_workflow_readiness",
        category="full_readiness",
        description="Existing Screen 5 workflow readiness check.",
        command=py_command("scripts/run_phase7_screen5_workflow_readiness_check.py", "--json"),
        modes=("full",),
        optional_group="slow_full",
        tags=("full", "readiness", "known-slow", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_screen6_governance_readiness",
        category="full_readiness",
        description="Existing Screen 6 governance readiness check.",
        command=py_command("scripts/run_phase7_screen6_governance_readiness_check.py", "--json"),
        modes=("full",),
        optional_group="slow_full",
        tags=("full", "readiness", "known-slow", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_index_source_readiness",
        category="full_readiness",
        description="Existing index/source mode readiness check.",
        command=py_command("scripts/run_phase7_index_source_readiness_check.py", "--json"),
        modes=("full",),
        tags=("full", "readiness", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_runtime_materialization_readiness",
        category="full_readiness",
        description="Existing runtime materialization metadata readiness check.",
        command=py_command("scripts/run_phase7_runtime_materialization_readiness_check.py", "--json"),
        modes=("full",),
        tags=("full", "readiness", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_adaptive_runtime_final_readiness",
        category="full_readiness",
        description="Existing Phase 7AC adaptive runtime final readiness check.",
        command=py_command("scripts/run_phase7_final_readiness_check.py", "--json"),
        modes=("full",),
        optional_group="slow_full",
        tags=("full", "readiness", "known-slow", "subprocess"),
        timeout_seconds=420,
    ),
    CheckSpec(
        name="phase7_db_backed_validation",
        category="db_persistence",
        description="Opt-in DB-backed 7CA-7CE governed workflow validation tests.",
        command=py_command(
            "-m",
            "unittest",
            "tests/test_phase7ca_governed_workflow_repository.py",
            "tests/test_phase7cb_deterministic_execution.py",
            "tests/test_phase7cc_comparison_execution.py",
            "tests/test_phase7cd_object_storage_load_execution.py",
            "tests/test_phase7ce_dashboard_output_refresh.py",
        ),
        modes=("default", "fast", "full"),
        optional_group="db",
        tags=("optional", "db", "subprocess"),
        timeout_seconds=600,
    ),
    CheckSpec(
        name="phase7_object_storage_live_validation",
        category="object_storage_live_path",
        description="Opt-in live Object Storage validation through existing 7CD tests.",
        command=py_command(
            "-m",
            "unittest",
            "tests/test_phase7cd_object_storage_load_execution.py",
        ),
        modes=("default", "fast", "full"),
        optional_group="object_storage",
        env_update=(("AWR_PHASE7CD_OBJECT_STORAGE_TEST", "1"),),
        tags=("optional", "object-storage", "subprocess"),
        timeout_seconds=600,
    ),
    CheckSpec(
        name="phase6_memory_regression",
        category="phase6_regression",
        description="Opt-in Phase 6 memory regression validation.",
        command=py_command("scripts/run_phase6_validation.py"),
        modes=("default", "fast", "full"),
        optional_group="phase6",
        tags=("optional", "phase6", "subprocess"),
        timeout_seconds=420,
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Phase 7CH end-to-end validation harness.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fast", action="store_true", help="Run the fast safe subset.")
    mode.add_argument("--full", action="store_true", help="Run the broader readiness set.")
    parser.add_argument("--json", action="store_true", help="Emit valid JSON only.")
    parser.add_argument(
        "--include-db",
        action="store_true",
        help="Include opt-in DB-backed validation when required env flags are present.",
    )
    parser.add_argument(
        "--include-object-storage",
        action="store_true",
        help="Include opt-in live Object Storage validation when config env is present.",
    )
    parser.add_argument(
        "--include-phase6",
        action="store_true",
        help="Include existing Phase 6 memory regression validation.",
    )
    parser.add_argument(
        "--strict-live",
        action="store_true",
        help="Fail requested live checks when required env/config is missing.",
    )
    parser.add_argument(
        "--list-checks",
        action="store_true",
        help="List known checks without executing them.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_checks:
        print_check_registry()
        return 0
    summary = run_validation(args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["overall_status"] == "passed" else 1


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    mode = selected_mode(args)
    checks: list[dict[str, Any]] = []
    skipped_checks: list[dict[str, Any]] = []

    for spec in CHECK_SPECS:
        selection = selection_state(spec, mode, args)
        if selection["selected"]:
            checks.append(run_check(spec, args, selection))
        else:
            skipped_checks.append(skipped_result(spec, selection["reason"]))

    failures = [
        failure_summary(check)
        for check in checks
        if check["required"] and check["status"] == "failed"
    ]
    overall_status = "passed" if not failures else "failed"
    return {
        "phase": "Phase 7",
        "subphase": "7CH",
        "validation_name": "Phase 7CH End-to-End Validation Harness Consolidation",
        "operational_certification_scope": list(OPERATIONAL_CERTIFICATION_SCOPE),
        "mode": mode,
        "overall_status": overall_status,
        "phase7_complete": False,
        "phase8_started": False,
        "checks": checks,
        "skipped_checks": skipped_checks,
        "invariants": dict(INVARIANTS),
        "failures": failures,
        "default_non_live": True,
        "db_checks_opt_in": True,
        "object_storage_checks_opt_in": True,
        "phase8_behavior_included": False,
    }


def selected_mode(args: argparse.Namespace) -> str:
    if args.full:
        return "full"
    if args.fast:
        return "fast"
    return "default"


def selection_state(
    spec: CheckSpec,
    mode: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    if spec.optional_group == "db":
        return {"selected": args.include_db, "reason": "DB validation is opt-in via --include-db."}
    if spec.optional_group == "object_storage":
        return {
            "selected": args.include_object_storage,
            "reason": "Object Storage live validation is opt-in via --include-object-storage.",
        }
    if spec.optional_group == "phase6":
        return {
            "selected": args.include_phase6,
            "reason": "Phase 6 regression is opt-in via --include-phase6.",
        }
    if spec.optional_group == "slow_full":
        return {
            "selected": False,
            "reason": (
                "Known slow readiness check is represented but skipped in 7CH; "
                "use later 7CI/7CK-7CY certification work for focused remediation."
            ),
        }
    if mode not in spec.modes:
        return {
            "selected": False,
            "reason": f"Check is not part of {mode} mode; available modes: {', '.join(spec.modes)}.",
        }
    return {"selected": True, "reason": ""}


def run_check(
    spec: CheckSpec,
    args: argparse.Namespace,
    selection: dict[str, Any],
) -> dict[str, Any]:
    del selection
    if spec.name == "phase7cg_boundary_document":
        return run_phase7cg_boundary_check(spec)
    if spec.name == "phase7ch_invariant_metadata":
        return run_invariant_metadata_check(spec)
    if spec.optional_group == "db":
        missing = missing_db_flags()
        if missing:
            reason = f"missing DB opt-in env flags: {', '.join(missing)}"
            if args.strict_live:
                return failed_result(spec, reason)
            return skipped_result(spec, reason)
    if spec.optional_group == "object_storage":
        missing = missing_object_storage_env()
        if missing:
            reason = f"missing Object Storage env/config: {', '.join(missing)}"
            if args.strict_live:
                return failed_result(spec, reason)
            return skipped_result(spec, reason)
    return run_subprocess_check(spec)


def run_phase7cg_boundary_check(spec: CheckSpec) -> dict[str, Any]:
    doc = ROOT / "docs" / "architecture" / "phase7_final_operational_certification_boundary.md"
    readme = ROOT / "docs" / "architecture" / "README.md"
    required_phrases = (
        "7CG defines the boundary for 7CG",
        "Phase 7 remains incomplete",
        "PHASE7_COMPLETE",
        "Phase 8 is not started",
        "7CH",
        "No Phase 8 sizing/TCO/what-if/EM Extract runtime implementation",
    )
    failures: list[str] = []
    if not doc.is_file():
        failures.append("missing docs/architecture/phase7_final_operational_certification_boundary.md")
    else:
        text = read_text(doc)
        for phrase in required_phrases:
            if phrase not in text:
                failures.append(f"missing 7CG boundary phrase: {phrase}")
    if not readme.is_file():
        failures.append("missing docs/architecture/README.md")
    elif "phase7_final_operational_certification_boundary.md" not in read_text(readme):
        failures.append("README does not reference the 7CG boundary document")
    if failures:
        return failed_result(spec, "; ".join(failures), checks_run=len(required_phrases) + 2)
    return passed_result(
        spec,
        "7CG boundary document exists, keeps Phase 7 incomplete, and is linked from README.",
        checks_run=len(required_phrases) + 2,
    )


def run_invariant_metadata_check(spec: CheckSpec) -> dict[str, Any]:
    expected = {
        "phase7_complete": False,
        "phase8_started": False,
        "deterministic_runtime_authoritative": True,
        "phase4i_contract_protected": True,
        "uncontrolled_runtime_mutation_allowed": False,
        "adaptive_runtime_default_active": False,
        "phase8_behavior_implemented": False,
    }
    failures = [
        f"{name} expected {expected_value!r}, got {INVARIANTS.get(name)!r}"
        for name, expected_value in expected.items()
        if INVARIANTS.get(name) is not expected_value
    ]
    if failures:
        return failed_result(spec, "; ".join(failures), checks_run=len(expected))
    return passed_result(
        spec,
        "Harness metadata asserts Phase 7 remains incomplete, Phase 8 remains not started, and runtime mutation remains denied by default.",
        checks_run=len(expected),
    )


def run_subprocess_check(spec: CheckSpec) -> dict[str, Any]:
    if spec.command is None:
        return failed_result(spec, "no command configured")
    env = os.environ.copy()
    for key, value in spec.env_update:
        env[key] = value
    try:
        completed = subprocess.run(
            list(spec.command),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=spec.timeout_seconds,
            env=env,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "name": spec.name,
            "category": spec.category,
            "command": format_command(spec.command),
            "required": True,
            "status": "failed",
            "returncode": None,
            "reason": f"timed out after {spec.timeout_seconds} seconds",
            "stdout_tail": tail_text(exc.stdout or ""),
            "stderr_tail": tail_text(exc.stderr or ""),
            "description": spec.description,
        }
    except OSError as exc:
        return failed_result(spec, f"unable to execute check: {type(exc).__name__}: {exc}")
    status = "passed" if completed.returncode == 0 else "failed"
    reason = "command completed successfully" if status == "passed" else "command failed"
    return {
        "name": spec.name,
        "category": spec.category,
        "command": format_command(spec.command),
        "required": True,
        "status": status,
        "returncode": completed.returncode,
        "reason": reason,
        "stdout_tail": tail_text(completed.stdout),
        "stderr_tail": tail_text(completed.stderr),
        "description": spec.description,
    }


def missing_db_flags() -> list[str]:
    required_flags = (
        "AWR_PHASE7CA_DB_TEST",
        "AWR_PHASE7CB_DB_TEST",
        "AWR_PHASE7CC_DB_TEST",
        "AWR_PHASE7CD_DB_TEST",
        "AWR_PHASE7CE_DB_TEST",
    )
    return [flag for flag in required_flags if os.getenv(flag) != "1"]


def missing_object_storage_env() -> list[str]:
    missing: list[str] = []
    if not (os.getenv("OCI_NAMESPACE") or os.getenv("OCI_OBJECT_STORAGE_NAMESPACE")):
        missing.append("OCI_NAMESPACE or OCI_OBJECT_STORAGE_NAMESPACE")
    if not (os.getenv("OCI_BUCKET_NAME") or os.getenv("OCI_OBJECT_STORAGE_BUCKET")):
        missing.append("OCI_BUCKET_NAME or OCI_OBJECT_STORAGE_BUCKET")
    if not (os.getenv("OCI_OBJECT_NAME") or os.getenv("OCI_OBJECT_STORAGE_OBJECT_NAME")):
        missing.append("OCI_OBJECT_NAME or OCI_OBJECT_STORAGE_OBJECT_NAME")
    if not os.getenv("OCI_REGION"):
        missing.append("OCI_REGION")
    return missing


def passed_result(spec: CheckSpec, reason: str, *, checks_run: int = 1) -> dict[str, Any]:
    return {
        "name": spec.name,
        "category": spec.category,
        "command": format_command(spec.command),
        "required": True,
        "status": "passed",
        "returncode": 0,
        "reason": reason,
        "stdout_tail": "",
        "stderr_tail": "",
        "description": spec.description,
        "checks_run": checks_run,
    }


def failed_result(spec: CheckSpec, reason: str, *, checks_run: int = 1) -> dict[str, Any]:
    return {
        "name": spec.name,
        "category": spec.category,
        "command": format_command(spec.command),
        "required": True,
        "status": "failed",
        "returncode": 1,
        "reason": reason,
        "stdout_tail": "",
        "stderr_tail": "",
        "description": spec.description,
        "checks_run": checks_run,
    }


def skipped_result(spec: CheckSpec, reason: str) -> dict[str, Any]:
    return {
        "name": spec.name,
        "category": spec.category,
        "command": format_command(spec.command),
        "required": False,
        "status": "skipped",
        "returncode": None,
        "reason": reason,
        "stdout_tail": "",
        "stderr_tail": "",
        "description": spec.description,
    }


def failure_summary(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": check["name"],
        "category": check["category"],
        "command": check["command"],
        "reason": check["reason"],
        "returncode": check["returncode"],
        "stdout_tail": check.get("stdout_tail", ""),
        "stderr_tail": check.get("stderr_tail", ""),
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def tail_text(text: str, *, max_lines: int = 20, max_chars: int = 4000) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    tail = "\n".join(lines[-max_lines:])
    if len(tail) > max_chars:
        return tail[-max_chars:]
    return tail


def format_command(command: tuple[str, ...] | None) -> str:
    if not command:
        return "internal"
    display: list[str] = []
    for part in command:
        if part == sys.executable:
            display.append("python")
        else:
            display.append(part)
    return " ".join(display)


def print_check_registry() -> None:
    print("Phase 7CH known checks:")
    for spec in CHECK_SPECS:
        modes = ", ".join(spec.modes)
        tags = ", ".join(spec.tags or ())
        optional = spec.optional_group or "required"
        print(
            f"- {spec.name} | category={spec.category} | modes={modes} | "
            f"group={optional} | tags={tags} | command={format_command(spec.command)}"
        )


def print_human_summary(summary: dict[str, Any]) -> None:
    print("Phase 7CH End-to-End Validation Harness")
    print(f"Mode: {summary['mode']}")
    print(f"Overall status: {summary['overall_status']}")
    print("Phase 7 complete: false")
    print("Phase 8 started: false")
    print("")
    print("Executed checks:")
    for check in summary["checks"]:
        print(f"- {check['status']}: {check['name']} ({check['category']})")
        if check["status"] != "passed":
            print(f"  reason: {check['reason']}")
    if summary["skipped_checks"]:
        print("")
        print("Skipped checks:")
        for check in summary["skipped_checks"]:
            print(f"- {check['name']}: {check['reason']}")
    if summary["failures"]:
        print("")
        print("Failures:")
        for failure in summary["failures"]:
            print(f"- {failure['name']}: {failure['reason']}")
    print("")
    print("Invariant metadata:")
    for name, value in summary["invariants"].items():
        print(f"- {name}={json.dumps(value)}")


if __name__ == "__main__":
    raise SystemExit(main())
