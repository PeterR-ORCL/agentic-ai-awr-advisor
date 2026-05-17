#!/usr/bin/env python3
"""Evaluate the Phase 7CI operational readiness gate."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]

READINESS_NAME = "Phase 7 Operational Readiness Check"
SCREEN2_BLOCKER_ID = "SCREEN2_BROAD_VALIDATOR_FAILURE"

DB_FLAGS: tuple[str, ...] = (
    "AWR_PHASE7CA_DB_TEST",
    "AWR_PHASE7CB_DB_TEST",
    "AWR_PHASE7CC_DB_TEST",
    "AWR_PHASE7CD_DB_TEST",
    "AWR_PHASE7CE_DB_TEST",
)

OBJECT_STORAGE_ENV_GROUPS: tuple[tuple[str, ...], ...] = (
    ("OCI_NAMESPACE", "OCI_OBJECT_STORAGE_NAMESPACE"),
    ("OCI_BUCKET_NAME", "OCI_OBJECT_STORAGE_BUCKET"),
    ("OCI_OBJECT_NAME", "OCI_OBJECT_STORAGE_OBJECT_NAME"),
    ("OCI_REGION",),
)

RELEASE_CERTIFICATION_DOCS: tuple[str, ...] = (
    "phase7_final_release_certification.md",
    "phase7_final_validation_matrix.md",
    "phase7_final_operational_checklist.md",
    "phase7_final_certification_runbook.md",
)

INVARIANTS: dict[str, bool] = {
    "deterministic_runtime_authoritative": True,
    "phase4i_contract_protected": True,
    "phase7_complete": False,
    "phase8_started": False,
    "phase8_behavior_implemented": False,
    "uncontrolled_runtime_mutation_allowed": False,
    "adaptive_runtime_default_active": False,
    "runtime_influence_denied_by_default": True,
    "candidate_approval_is_not_runtime_activation": True,
    "materialization_is_not_runtime_activation": True,
    "ml_scoring_shadow_or_advisory_only": True,
    "dashboard_workflows_do_not_mutate_truth_directly": True,
    "screen_wiring_required_for_final_certification": True,
    "db_validation_required_for_final_certification": True,
    "object_storage_validation_required_for_final_certification": True,
}


@dataclass(frozen=True)
class RequirementSpec:
    id: str
    name: str
    category: str
    required_for_final_certification: bool
    evidence_source: str
    remediation_subphase: str = ""
    command: tuple[str, ...] | None = None
    timeout_seconds: int = 300


def py_command(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


SCREEN_COMMANDS: dict[str, RequirementSpec] = {
    "dashboard_workflow_infrastructure": RequirementSpec(
        id="dashboard_workflow_infrastructure",
        name="Dashboard workflow infrastructure represented",
        category="dashboard_workflow",
        required_for_final_certification=True,
        evidence_source="readiness script",
        command=py_command("scripts/run_phase7_dashboard_workflow_validation.py", "--json"),
        timeout_seconds=420,
    ),
    "screen1_operational_wiring": RequirementSpec(
        id="screen1_operational_wiring",
        name="Screen 1 parser governance workflow operational wiring validated",
        category="screen_operational_wiring",
        required_for_final_certification=True,
        evidence_source="screen validation script",
        remediation_subphase="7CK-7CY",
        command=py_command("scripts/run_phase7_screen1_workflow_validation.py", "--json"),
        timeout_seconds=420,
    ),
    "screen2_operational_wiring": RequirementSpec(
        id="screen2_operational_wiring",
        name="Screen 2 diagnostic review workflow operational wiring validated",
        category="screen_operational_wiring",
        required_for_final_certification=True,
        evidence_source="broad Screen 2 validation script",
        remediation_subphase="7CK-7CY",
        command=py_command("scripts/run_phase7_screen2_review_validation.py", "--json"),
        timeout_seconds=420,
    ),
    "screen3_active_backend_execution": RequirementSpec(
        id="screen3_active_backend_execution",
        name="Screen 3 active backend execution operational wiring validated",
        category="screen_operational_wiring",
        required_for_final_certification=True,
        evidence_source="active Screen 3 validation script",
        command=py_command("scripts/run_phase7_active_screen3_execution_validation.py", "--json"),
        timeout_seconds=420,
    ),
    "screen4_operational_wiring": RequirementSpec(
        id="screen4_operational_wiring",
        name="Screen 4 historical review workflow operational wiring validated",
        category="screen_operational_wiring",
        required_for_final_certification=True,
        evidence_source="screen validation script",
        remediation_subphase="7CK-7CY",
        command=py_command("scripts/run_phase7_screen4_workflow_validation.py", "--json"),
        timeout_seconds=420,
    ),
    "screen5_operational_wiring": RequirementSpec(
        id="screen5_operational_wiring",
        name="Screen 5 recommendation/action/outcome workflow operational wiring validated",
        category="screen_operational_wiring",
        required_for_final_certification=True,
        evidence_source="screen validation script",
        remediation_subphase="7CK-7CY",
        command=py_command("scripts/run_phase7_screen5_workflow_validation.py", "--json"),
        timeout_seconds=420,
    ),
    "screen6_operational_wiring": RequirementSpec(
        id="screen6_operational_wiring",
        name="Screen 6 governance control plane operational wiring validated",
        category="screen_operational_wiring",
        required_for_final_certification=True,
        evidence_source="screen validation script",
        remediation_subphase="7CK-7CY",
        command=py_command("scripts/run_phase7_screen6_governance_validation.py", "--json"),
        timeout_seconds=420,
    ),
    "index_source_handoff": RequirementSpec(
        id="index_source_handoff",
        name="Index/source mode entry and Screen 3 handoff validated",
        category="index_source_mode",
        required_for_final_certification=True,
        evidence_source="index/source validation script",
        command=py_command("scripts/run_phase7_index_source_validation.py", "--json"),
        timeout_seconds=420,
    ),
    "runtime_materialization_metadata": RequirementSpec(
        id="runtime_materialization_metadata",
        name="Runtime materialization metadata validated without activation",
        category="runtime_materialization",
        required_for_final_certification=True,
        evidence_source="runtime materialization validation script",
        command=py_command("scripts/run_phase7_runtime_materialization_validation.py", "--json"),
        timeout_seconds=420,
    ),
}

LISTED_REQUIREMENTS: tuple[RequirementSpec, ...] = (
    RequirementSpec(
        id="phase7cg_boundary",
        name="7CG final operational certification boundary exists and is referenced",
        category="documentation_boundary",
        required_for_final_certification=True,
        evidence_source="direct doc check",
    ),
    RequirementSpec(
        id="phase7ch_harness_safe_validation",
        name="7CH end-to-end validation harness exists and passes safe validation",
        category="validation_harness",
        required_for_final_certification=True,
        evidence_source="7CH harness subprocess",
        command=py_command("scripts/run_phase7_end_to_end_validation.py", "--fast", "--json"),
        timeout_seconds=420,
    ),
    RequirementSpec(
        id="learning_foundation_shadow_boundary",
        name="Phase 7 learning foundation represented and not runtime-active by default",
        category="learning_foundation",
        required_for_final_certification=True,
        evidence_source="7CH safe harness and invariant metadata",
    ),
    RequirementSpec(
        id="controlled_materialization_shadow_boundary",
        name="Controlled learning materialization represented and not runtime-active by default",
        category="materialization",
        required_for_final_certification=True,
        evidence_source="7CH safe harness and invariant metadata",
    ),
    RequirementSpec(
        id="ml_adaptive_shadow_boundary",
        name="ML/adaptive scoring foundation represented and shadow/advisory only",
        category="ml_adaptive",
        required_for_final_certification=True,
        evidence_source="7CH safe harness and invariant metadata",
    ),
    RequirementSpec(
        id="adaptive_runtime_denied_by_default",
        name="Controlled adaptive runtime integration represented and denied by default",
        category="adaptive_runtime",
        required_for_final_certification=True,
        evidence_source="7CH safe harness and invariant metadata",
    ),
    SCREEN_COMMANDS["dashboard_workflow_infrastructure"],
    SCREEN_COMMANDS["screen1_operational_wiring"],
    SCREEN_COMMANDS["screen2_operational_wiring"],
    SCREEN_COMMANDS["screen3_active_backend_execution"],
    SCREEN_COMMANDS["screen4_operational_wiring"],
    SCREEN_COMMANDS["screen5_operational_wiring"],
    SCREEN_COMMANDS["screen6_operational_wiring"],
    SCREEN_COMMANDS["index_source_handoff"],
    SCREEN_COMMANDS["runtime_materialization_metadata"],
    RequirementSpec(
        id="db_persistence_validation",
        name="DB persistence validation passed",
        category="db_persistence",
        required_for_final_certification=True,
        evidence_source="DB-backed validation",
        remediation_subphase="7CK-7CY",
        command=py_command(
            "-m",
            "unittest",
            "tests.test_phase7ca_governed_workflow_repository.Phase7CAGovernedWorkflowRepositoryTests.test_optional_db_backed_insert_read_idempotency",
            "tests.test_phase7cb_deterministic_execution.Phase7CBDeterministicExecutionTests.test_optional_db_backed_deterministic_execution",
            "tests.test_phase7cc_comparison_execution.Phase7CCComparisonExecutionTests.test_optional_db_backed_comparison_execution",
            "tests.test_phase7cd_object_storage_load_execution.Phase7CDObjectStorageLoadExecutionTests.test_optional_db_backed_object_storage_load",
            "tests.test_phase7ce_dashboard_output_refresh.Phase7CEDashboardOutputRefreshTests.test_optional_db_backed_dashboard_refresh",
        ),
        timeout_seconds=600,
    ),
    RequirementSpec(
        id="object_storage_live_validation",
        name="Object Storage live path validation passed",
        category="object_storage_live_path",
        required_for_final_certification=True,
        evidence_source="Object Storage live validation",
        remediation_subphase="7CK-7CY",
        command=py_command("-m", "unittest", "tests/test_phase7cd_object_storage_load_execution.py"),
        timeout_seconds=600,
    ),
    RequirementSpec(
        id="deterministic_fallback_rollback",
        name="Deterministic fallback/rollback behavior validated",
        category="runtime_safety",
        required_for_final_certification=True,
        evidence_source="invariant metadata and existing validation boundaries",
    ),
    RequirementSpec(
        id="phase4i_contract_protected",
        name="Phase 4I output contract protected",
        category="phase4i_contract",
        required_for_final_certification=True,
        evidence_source="invariant metadata",
    ),
    RequirementSpec(
        id="no_uncontrolled_runtime_mutation",
        name="No uncontrolled runtime mutation",
        category="runtime_safety",
        required_for_final_certification=True,
        evidence_source="invariant metadata",
    ),
    RequirementSpec(
        id="no_uncontrolled_subprocess",
        name="No direct uncontrolled subprocess execution",
        category="runtime_safety",
        required_for_final_certification=True,
        evidence_source="allowlisted subprocess model",
    ),
    RequirementSpec(
        id="no_run_analysis_coupling",
        name="No direct governed workflow coupling to run_analysis.py",
        category="runtime_safety",
        required_for_final_certification=True,
        evidence_source="invariant metadata and validation boundaries",
    ),
    RequirementSpec(
        id="no_adaptive_runtime_default_activation",
        name="No adaptive runtime activation by default",
        category="adaptive_runtime",
        required_for_final_certification=True,
        evidence_source="invariant metadata",
    ),
    RequirementSpec(
        id="no_phase8_implementation",
        name="No Phase 8 implementation",
        category="phase_boundary",
        required_for_final_certification=True,
        evidence_source="invariant metadata",
    ),
    RequirementSpec(
        id="known_blockers_resolved",
        name="Known blockers resolved",
        category="blocker_resolution",
        required_for_final_certification=True,
        evidence_source="readiness blocker registry",
        remediation_subphase="7CK-7CY",
    ),
    RequirementSpec(
        id="final_release_documentation_pending",
        name="Final release documentation complete for 7CJ",
        category="release_documentation",
        required_for_final_certification=True,
        evidence_source="7CJ release certification documentation",
        remediation_subphase="7CJ",
    ),
    RequirementSpec(
        id="final_certification_tag_pending",
        name="Final certification/tag still pending until 7CZ",
        category="final_certification",
        required_for_final_certification=True,
        evidence_source="7CZ final certification and PHASE7_COMPLETE tag",
        remediation_subphase="7CZ",
    ),
    RequirementSpec(
        id="phase6_regression_optional",
        name="Phase 6 memory regression boundary optionally validated",
        category="phase6_regression",
        required_for_final_certification=False,
        evidence_source="optional Phase 6 validation",
        command=py_command("scripts/run_phase6_validation.py"),
        timeout_seconds=420,
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate the strict Phase 7CI operational readiness gate.",
    )
    parser.add_argument("--json", action="store_true", help="Emit valid JSON only.")
    parser.add_argument(
        "--final-certification",
        action="store_true",
        help="Evaluate strict final-certification readiness semantics.",
    )
    parser.add_argument(
        "--fail-on-not-ready",
        action="store_true",
        help="Exit non-zero when phase7_operational_ready is false.",
    )
    parser.add_argument(
        "--include-db",
        action="store_true",
        help="Include DB-backed validation when opt-in env flags are present.",
    )
    parser.add_argument(
        "--include-object-storage",
        action="store_true",
        help="Include live Object Storage validation when env/config is present.",
    )
    parser.add_argument(
        "--include-phase6",
        action="store_true",
        help="Include optional Phase 6 regression validation.",
    )
    parser.add_argument(
        "--list-requirements",
        action="store_true",
        help="List final certification requirements without executing checks.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_requirements:
        print_requirements()
        return 0

    summary = evaluate_readiness(args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)

    if args.fail_on_not_ready and not summary["phase7_operational_ready"]:
        return 1
    return 0


def evaluate_readiness(args: argparse.Namespace) -> dict[str, Any]:
    harness_result = run_harness_safe_validation()
    requirements: list[dict[str, Any]] = []

    requirements.append(evaluate_7cg_boundary())
    requirements.append(evaluate_7ch_harness(harness_result))
    requirements.extend(evaluate_metadata_requirements(harness_result))
    requirements.append(evaluate_dashboard_requirement(args))
    requirements.extend(evaluate_screen_and_operational_wiring(args))
    requirements.append(evaluate_db_requirement(args))
    requirements.append(evaluate_object_storage_requirement(args))
    requirements.extend(evaluate_runtime_invariant_requirements())
    requirements.append(evaluate_known_blockers_requirement(requirements))
    requirements.append(evaluate_release_documentation_requirement())
    requirements.append(pending_requirement("final_certification_tag_pending"))
    requirements.append(evaluate_phase6_requirement(args))

    known_blockers = build_known_blockers(requirements)
    required_checks = [
        req for req in requirements if req["required_for_final_certification"]
    ]
    satisfied_checks = [req for req in requirements if req["status"] == "satisfied"]
    blocked_checks = [req for req in requirements if req["status"] == "blocked"]
    skipped_checks = [req for req in requirements if req["status"] == "skipped"]
    pending_checks = [req for req in requirements if req["status"] == "pending"]

    all_required_satisfied = all(
        req["status"] == "satisfied" for req in required_checks
    )
    phase7_operational_ready = (
        args.final_certification
        and all_required_satisfied
        and not known_blockers
        and INVARIANTS["phase7_complete"] is False
        and INVARIANTS["phase8_started"] is False
    )
    recommended_next = recommended_next_subphase(known_blockers, blocked_checks, pending_checks)

    return {
        "phase": "Phase 7",
        "subphase": "7CI",
        "readiness_name": READINESS_NAME,
        "phase7_operational_ready": phase7_operational_ready,
        "phase7_complete": False,
        "phase8_started": False,
        "final_certification_mode": bool(args.final_certification),
        "safe_local_mode": not bool(args.final_certification),
        "required_final_certification_checks": required_checks,
        "satisfied_checks": satisfied_checks,
        "blocked_checks": blocked_checks,
        "skipped_checks": skipped_checks,
        "pending_checks": pending_checks,
        "known_blockers": known_blockers,
        "requirements": requirements,
        "invariants": dict(INVARIANTS),
        "next_subphase": "7CJ or 7CK depending on readiness gaps",
        "recommended_next_subphase": recommended_next,
        "final_certification_requires_db": True,
        "final_certification_requires_object_storage": True,
        "final_certification_requires_screen_wiring": True,
        "phase8_behavior_included": False,
    }


def run_harness_safe_validation() -> dict[str, Any]:
    spec = next(
        req for req in LISTED_REQUIREMENTS if req.id == "phase7ch_harness_safe_validation"
    )
    result = run_command(spec)
    payload = parse_json_payload(result.get("stdout_tail", ""))
    result["parsed_json"] = payload
    if payload and payload.get("overall_status") != "passed":
        result["status"] = "failed"
        result["reason"] = "7CH harness JSON did not report overall_status=passed"
    return result


def evaluate_7cg_boundary() -> dict[str, Any]:
    spec = spec_by_id("phase7cg_boundary")
    doc = ROOT / "docs" / "architecture" / "phase7_final_operational_certification_boundary.md"
    readme = ROOT / "docs" / "architecture" / "README.md"
    failures: list[str] = []
    if not doc.is_file():
        failures.append("missing docs/architecture/phase7_final_operational_certification_boundary.md")
    if not readme.is_file():
        failures.append("missing docs/architecture/README.md")
    elif "phase7_final_operational_certification_boundary.md" not in read_text(readme):
        failures.append("README does not reference the 7CG boundary document")
    if failures:
        return requirement_result(spec, "blocked", "; ".join(failures), evidence="")
    return requirement_result(
        spec,
        "satisfied",
        "7CG boundary document exists and is referenced from README.",
        evidence="docs/architecture/phase7_final_operational_certification_boundary.md",
    )


def evaluate_7ch_harness(harness_result: dict[str, Any]) -> dict[str, Any]:
    spec = spec_by_id("phase7ch_harness_safe_validation")
    script = ROOT / "scripts" / "run_phase7_end_to_end_validation.py"
    doc = ROOT / "docs" / "architecture" / "phase7_end_to_end_validation_harness.md"
    missing = [
        str(path.relative_to(ROOT))
        for path in (script, doc)
        if not path.is_file()
    ]
    if missing:
        return requirement_result(
            spec,
            "blocked",
            f"missing 7CH artifact(s): {', '.join(missing)}",
            evidence="",
            command=harness_result.get("command", ""),
            returncode=harness_result.get("returncode"),
            stdout_tail=harness_result.get("stdout_tail", ""),
            stderr_tail=harness_result.get("stderr_tail", ""),
        )
    status = "satisfied" if harness_result["status"] == "passed" else "blocked"
    reason = (
        "7CH fast safe harness passed."
        if status == "satisfied"
        else f"7CH fast safe harness failed: {harness_result['reason']}"
    )
    return requirement_result(
        spec,
        status,
        reason,
        evidence="scripts/run_phase7_end_to_end_validation.py --fast --json",
        command=harness_result.get("command", ""),
        returncode=harness_result.get("returncode"),
        stdout_tail=harness_result.get("stdout_tail", ""),
        stderr_tail=harness_result.get("stderr_tail", ""),
    )


def evaluate_metadata_requirements(
    harness_result: dict[str, Any],
) -> list[dict[str, Any]]:
    ids = (
        "learning_foundation_shadow_boundary",
        "controlled_materialization_shadow_boundary",
        "ml_adaptive_shadow_boundary",
        "adaptive_runtime_denied_by_default",
    )
    status = "satisfied" if harness_result["status"] == "passed" else "blocked"
    reason = (
        "Represented by the 7CH safe harness and constrained by 7CI invariant metadata."
        if status == "satisfied"
        else "Cannot satisfy representation while the 7CH safe harness is failing."
    )
    return [
        requirement_result(spec_by_id(req_id), status, reason, evidence="7CH safe harness")
        for req_id in ids
    ]


def evaluate_dashboard_requirement(args: argparse.Namespace) -> dict[str, Any]:
    spec = spec_by_id("dashboard_workflow_infrastructure")
    if args.final_certification:
        result = run_command(spec)
        return command_requirement_result(
            spec,
            result,
            passed_reason="Dashboard workflow validation passed for final-certification mode.",
            failed_reason="Dashboard workflow validation failed in final-certification mode.",
        )
    script = ROOT / "scripts" / "run_phase7_dashboard_workflow_validation.py"
    if not script.is_file():
        return requirement_result(
            spec,
            "blocked",
            "Dashboard workflow validation script is missing.",
            evidence="",
        )
    return requirement_result(
        spec,
        "satisfied",
        "Dashboard workflow infrastructure is represented; final wiring validation runs in final-certification mode.",
        evidence="scripts/run_phase7_dashboard_workflow_validation.py",
    )


def evaluate_screen_and_operational_wiring(
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for req_id in (
        "screen1_operational_wiring",
        "screen2_operational_wiring",
        "screen3_active_backend_execution",
        "screen4_operational_wiring",
        "screen5_operational_wiring",
        "screen6_operational_wiring",
        "index_source_handoff",
        "runtime_materialization_metadata",
    ):
        spec = spec_by_id(req_id)
        if req_id == "screen2_operational_wiring":
            result = run_command(spec)
            results.append(
                command_requirement_result(
                    spec,
                    result,
                    passed_reason=(
                        "Broad Screen 2 validation passed; "
                        "SCREEN2_BROAD_VALIDATOR_FAILURE is resolved."
                    ),
                    failed_reason=(
                        "Broad Screen 2 validation failed; "
                        "SCREEN2_BROAD_VALIDATOR_FAILURE remains a readiness blocker."
                    ),
                    remediation_subphase="7CK-7CY",
                )
            )
            continue
        if not args.final_certification:
            results.append(
                requirement_result(
                    spec,
                    "skipped",
                    "Screen operational wiring validation is required for final-certification mode and is not run in safe local mode.",
                    evidence=format_command(spec.command),
                    remediation_subphase=spec.remediation_subphase,
                )
            )
            continue
        result = run_command(spec)
        failed_reason = (
            "Broad Screen 2 validation failed; SCREEN2_BROAD_VALIDATOR_FAILURE remains a readiness blocker."
            if req_id == "screen2_operational_wiring"
            else "Required operational wiring validation failed in final-certification mode."
        )
        results.append(
            command_requirement_result(
                spec,
                result,
                passed_reason="Required operational wiring validation passed in final-certification mode.",
                failed_reason=failed_reason,
                remediation_subphase=spec.remediation_subphase,
            )
        )
    return results


def evaluate_db_requirement(args: argparse.Namespace) -> dict[str, Any]:
    spec = spec_by_id("db_persistence_validation")
    missing = missing_db_flags()
    if not args.include_db:
        status = "blocked" if args.final_certification else "skipped"
        return requirement_result(
            spec,
            status,
            (
                "DB persistence validation is required for final certification; rerun with --include-db after env/config is prepared."
                if args.final_certification
                else "DB validation is not run in safe local mode unless --include-db is provided."
            ),
            evidence="DB opt-in flags",
            remediation_subphase="7CK-7CY",
        )
    if missing:
        status = "blocked" if args.final_certification else "skipped"
        return requirement_result(
            spec,
            status,
            f"missing DB opt-in env flags: {', '.join(missing)}",
            evidence="DB opt-in flags",
            remediation_subphase="7CK-7CY",
        )
    result = run_command(spec)
    return live_command_requirement_result(
        spec,
        result,
        passed_reason="DB-backed governed workflow persistence validation passed.",
        failed_reason="DB-backed governed workflow persistence validation failed.",
        skipped_reason="DB-backed governed workflow persistence validation did not execute live DB checks because one or more opt-in tests were skipped.",
        remediation_subphase="7CK-7CY",
    )


def evaluate_object_storage_requirement(args: argparse.Namespace) -> dict[str, Any]:
    spec = spec_by_id("object_storage_live_validation")
    missing = missing_object_storage_env()
    if not args.include_object_storage:
        status = "blocked" if args.final_certification else "skipped"
        return requirement_result(
            spec,
            status,
            (
                "Object Storage live path validation is required for final certification; rerun with --include-object-storage after env/config is prepared."
                if args.final_certification
                else "Object Storage live validation is not run in safe local mode unless --include-object-storage is provided."
            ),
            evidence="Object Storage env/config",
            remediation_subphase="7CK-7CY",
        )
    if missing:
        status = "blocked" if args.final_certification else "skipped"
        return requirement_result(
            spec,
            status,
            f"missing Object Storage env/config: {', '.join(missing)}",
            evidence="Object Storage env/config",
            remediation_subphase="7CK-7CY",
        )
    result = run_command(spec, env_update={"AWR_PHASE7CD_OBJECT_STORAGE_TEST": "1"})
    return live_command_requirement_result(
        spec,
        result,
        passed_reason="Live Object Storage path validation passed.",
        failed_reason="Live Object Storage path validation failed.",
        skipped_reason="Live Object Storage path validation did not execute because the opt-in live test was skipped.",
        remediation_subphase="7CK-7CY",
    )


def evaluate_runtime_invariant_requirements() -> list[dict[str, Any]]:
    invariant_map = {
        "deterministic_fallback_rollback": "deterministic_runtime_authoritative",
        "phase4i_contract_protected": "phase4i_contract_protected",
        "no_uncontrolled_runtime_mutation": "uncontrolled_runtime_mutation_allowed",
        "no_uncontrolled_subprocess": "uncontrolled_runtime_mutation_allowed",
        "no_run_analysis_coupling": "uncontrolled_runtime_mutation_allowed",
        "no_adaptive_runtime_default_activation": "adaptive_runtime_default_active",
        "no_phase8_implementation": "phase8_behavior_implemented",
    }
    expected_values = {
        "deterministic_runtime_authoritative": True,
        "phase4i_contract_protected": True,
        "uncontrolled_runtime_mutation_allowed": False,
        "adaptive_runtime_default_active": False,
        "phase8_behavior_implemented": False,
    }
    results: list[dict[str, Any]] = []
    for req_id, invariant_name in invariant_map.items():
        spec = spec_by_id(req_id)
        expected = expected_values[invariant_name]
        actual = INVARIANTS[invariant_name]
        if actual is expected:
            results.append(
                requirement_result(
                    spec,
                    "satisfied",
                    f"7CI invariant metadata asserts {invariant_name}={json.dumps(actual)}.",
                    evidence=f"invariant:{invariant_name}",
                )
            )
        else:
            results.append(
                requirement_result(
                    spec,
                    "blocked",
                    f"invariant {invariant_name} expected {expected!r}, got {actual!r}",
                    evidence=f"invariant:{invariant_name}",
                    remediation_subphase="7CK-7CY",
                )
            )
    return results


def evaluate_known_blockers_requirement(
    requirements: list[dict[str, Any]],
) -> dict[str, Any]:
    spec = spec_by_id("known_blockers_resolved")
    screen2 = next(
        (req for req in requirements if req["id"] == "screen2_operational_wiring"),
        None,
    )
    if screen2 and screen2["status"] != "satisfied":
        return requirement_result(
            spec,
            "blocked",
            "Known blocker SCREEN2_BROAD_VALIDATOR_FAILURE is unresolved.",
            evidence="screen2_operational_wiring",
            remediation_subphase="7CK-7CY",
        )
    return requirement_result(
        spec,
        "satisfied",
        "No known readiness blockers remain open.",
        evidence="readiness blocker registry",
    )


def evaluate_release_documentation_requirement() -> dict[str, Any]:
    spec = spec_by_id("final_release_documentation_pending")
    docs_dir = ROOT / "docs" / "architecture"
    readme = docs_dir / "README.md"
    missing = [
        f"docs/architecture/{name}"
        for name in RELEASE_CERTIFICATION_DOCS
        if not (docs_dir / name).is_file()
    ]
    if readme.is_file():
        readme_text = read_text(readme)
        missing_refs = [
            name for name in RELEASE_CERTIFICATION_DOCS if name not in readme_text
        ]
    else:
        missing_refs = list(RELEASE_CERTIFICATION_DOCS)
    if missing or missing_refs:
        details: list[str] = []
        if missing:
            details.append("missing release doc(s): " + ", ".join(missing))
        if missing_refs:
            details.append(
                "README missing release doc reference(s): " + ", ".join(missing_refs)
            )
        return requirement_result(
            spec,
            "pending",
            "; ".join(details),
            evidence="7CJ release certification documentation",
            remediation_subphase="7CJ",
        )
    return requirement_result(
        spec,
        "satisfied",
        "7CJ final release certification documentation exists and is referenced from README.",
        evidence="docs/architecture/phase7_final_release_certification.md",
        remediation_subphase="",
    )


def evaluate_phase6_requirement(args: argparse.Namespace) -> dict[str, Any]:
    spec = spec_by_id("phase6_regression_optional")
    if not args.include_phase6:
        return requirement_result(
            spec,
            "skipped",
            "Phase 6 regression validation is optional in 7CI and runs only with --include-phase6.",
            evidence=format_command(spec.command),
        )
    script = ROOT / "scripts" / "run_phase6_validation.py"
    if not script.is_file():
        return requirement_result(
            spec,
            "skipped",
            "No clear Phase 6 validation script exists.",
            evidence="scripts/run_phase6_validation.py",
        )
    result = run_command(spec)
    return command_requirement_result(
        spec,
        result,
        passed_reason="Optional Phase 6 regression validation passed.",
        failed_reason="Optional Phase 6 regression validation failed.",
        remediation_subphase="7CK-7CY",
    )


def pending_requirement(req_id: str) -> dict[str, Any]:
    spec = spec_by_id(req_id)
    return requirement_result(
        spec,
        "pending",
        (
            "7CJ release certification documentation has not been completed in 7CI."
            if req_id == "final_release_documentation_pending"
            else "7CZ final certification and PHASE7_COMPLETE tag are not allowed in 7CI."
        ),
        evidence=spec.evidence_source,
        remediation_subphase=spec.remediation_subphase,
    )


def command_requirement_result(
    spec: RequirementSpec,
    command_result: dict[str, Any],
    *,
    passed_reason: str,
    failed_reason: str,
    remediation_subphase: str = "",
) -> dict[str, Any]:
    status = "satisfied" if command_result["status"] == "passed" else "blocked"
    reason = passed_reason if status == "satisfied" else f"{failed_reason} {command_result['reason']}"
    return requirement_result(
        spec,
        status,
        reason,
        evidence=format_command(spec.command),
        remediation_subphase=remediation_subphase or spec.remediation_subphase,
        command=command_result.get("command", ""),
        returncode=command_result.get("returncode"),
        stdout_tail=command_result.get("stdout_tail", ""),
        stderr_tail=command_result.get("stderr_tail", ""),
    )


def live_command_requirement_result(
    spec: RequirementSpec,
    command_result: dict[str, Any],
    *,
    passed_reason: str,
    failed_reason: str,
    skipped_reason: str,
    remediation_subphase: str = "",
) -> dict[str, Any]:
    if command_result["status"] == "passed" and not command_result_reports_skips(command_result):
        status = "satisfied"
        reason = passed_reason
    elif command_result["status"] == "passed":
        status = "blocked"
        reason = skipped_reason
    else:
        status = "blocked"
        reason = f"{failed_reason} {command_result['reason']}"
    return requirement_result(
        spec,
        status,
        reason,
        evidence=format_command(spec.command),
        remediation_subphase=remediation_subphase or spec.remediation_subphase,
        command=command_result.get("command", ""),
        returncode=command_result.get("returncode"),
        stdout_tail=command_result.get("stdout_tail", ""),
        stderr_tail=command_result.get("stderr_tail", ""),
    )


def requirement_result(
    spec: RequirementSpec,
    status: str,
    reason: str,
    *,
    evidence: str,
    remediation_subphase: str = "",
    command: str = "",
    returncode: int | None = None,
    stdout_tail: str = "",
    stderr_tail: str = "",
) -> dict[str, Any]:
    return {
        "id": spec.id,
        "name": spec.name,
        "category": spec.category,
        "required_for_final_certification": spec.required_for_final_certification,
        "status": status,
        "evidence": evidence,
        "reason": reason,
        "remediation_subphase": remediation_subphase or spec.remediation_subphase,
        "evidence_source": spec.evidence_source,
        "command": command or format_command(spec.command),
        "returncode": returncode,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }


def run_command(
    spec: RequirementSpec,
    *,
    env_update: dict[str, str] | None = None,
) -> dict[str, Any]:
    if spec.command is None:
        return {
            "status": "failed",
            "reason": "no command configured",
            "returncode": 1,
            "command": "internal",
            "stdout_tail": "",
            "stderr_tail": "",
        }
    env = os.environ.copy()
    if env_update:
        env.update(env_update)
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
            "status": "failed",
            "reason": f"timed out after {spec.timeout_seconds} seconds",
            "returncode": None,
            "command": format_command(spec.command),
            "stdout_tail": tail_text(exc.stdout or ""),
            "stderr_tail": tail_text(exc.stderr or ""),
        }
    except OSError as exc:
        return {
            "status": "failed",
            "reason": f"unable to execute check: {type(exc).__name__}: {exc}",
            "returncode": 1,
            "command": format_command(spec.command),
            "stdout_tail": "",
            "stderr_tail": "",
        }
    status = "passed" if completed.returncode == 0 else "failed"
    return {
        "status": status,
        "reason": "command completed successfully" if status == "passed" else "command failed",
        "returncode": completed.returncode,
        "command": format_command(spec.command),
        "stdout_tail": tail_text(completed.stdout),
        "stderr_tail": tail_text(completed.stderr),
    }


def build_known_blockers(requirements: list[dict[str, Any]]) -> list[dict[str, str]]:
    screen2 = next(
        (req for req in requirements if req["id"] == "screen2_operational_wiring"),
        None,
    )
    if not screen2 or screen2["status"] == "satisfied":
        return []
    return [
        {
            "id": SCREEN2_BLOCKER_ID,
            "description": (
                "The broader Screen 2 validation script previously failed due to a "
                "dashboard/button wiring issue involving <button> in the broader "
                "dashboard source. 7CH used targeted passing Screen 2 boundary, "
                "model, bridge, and diagnostic tests, but final Phase 7 certification "
                "requires broader Screen 2 operational wiring validation to pass."
            ),
            "impact": "phase7_operational_ready=false until resolved.",
            "expected_remediation": "Use reserved fix range 7CK-7CY if not resolved by 7CI validation work.",
            "requirement_id": "screen2_operational_wiring",
            "requirement_status": screen2["status"],
            "reason": screen2["reason"],
        }
    ]


def recommended_next_subphase(
    known_blockers: list[dict[str, str]],
    blocked_checks: list[dict[str, Any]],
    pending_checks: list[dict[str, Any]],
) -> str:
    if known_blockers:
        return "7CK - remediation before release certification"
    if blocked_checks:
        return "7CL - remaining certification gap closure before release certification"
    pending_ids = {check["id"] for check in pending_checks}
    if "final_release_documentation_pending" in pending_ids:
        return "7CJ - release certification documentation"
    if "final_certification_tag_pending" in pending_ids:
        return "7CZ - final Phase 7 certification / tag readiness"
    return "7CZ - final Phase 7 certification / tag readiness"


def missing_db_flags() -> list[str]:
    return [flag for flag in DB_FLAGS if os.getenv(flag) != "1"]


def missing_object_storage_env() -> list[str]:
    missing: list[str] = []
    for names in OBJECT_STORAGE_ENV_GROUPS:
        if not any(os.getenv(name) for name in names):
            missing.append(" or ".join(names))
    return missing


def command_result_reports_skips(command_result: dict[str, Any]) -> bool:
    combined = "\n".join(
        str(command_result.get(key, ""))
        for key in ("stdout_tail", "stderr_tail")
        if command_result.get(key)
    ).lower()
    for match in re.finditer(r"skipped=(\d+)", combined):
        if int(match.group(1)) > 0:
            return True
    return False


def spec_by_id(req_id: str) -> RequirementSpec:
    for spec in LISTED_REQUIREMENTS:
        if spec.id == req_id:
            return spec
    raise KeyError(req_id)


def parse_json_payload(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def tail_text(text: str, *, max_lines: int = 12, max_chars: int = 1200) -> str:
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
        display.append("python" if part == sys.executable else part)
    return " ".join(display)


def print_requirements() -> None:
    print("Phase 7CI final certification requirements:")
    for spec in LISTED_REQUIREMENTS:
        required = "true" if spec.required_for_final_certification else "false"
        source = spec.evidence_source
        command = format_command(spec.command)
        print(
            f"- {spec.id} | required_for_final_certification={required} | "
            f"category={spec.category} | source={source} | command={command}"
        )
    print("")
    print("Final certification mode requires DB validation, Object Storage live validation, and screen operational wiring validation.")
    print("List mode does not execute checks and does not create PHASE7_COMPLETE.")


def print_human_summary(summary: dict[str, Any]) -> None:
    print("Phase 7CI Operational Readiness Check")
    print(f"Final certification mode: {json.dumps(summary['final_certification_mode'])}")
    print(f"Safe local mode: {json.dumps(summary['safe_local_mode'])}")
    print(f"Phase 7 operational ready: {json.dumps(summary['phase7_operational_ready'])}")
    print("Phase 7 complete: false")
    print("Phase 8 started: false")
    print("")
    print("Satisfied checks:")
    for check in summary["satisfied_checks"]:
        print(f"- {check['id']}: {check['name']}")
    if summary["blocked_checks"]:
        print("")
        print("Blocked checks:")
        for check in summary["blocked_checks"]:
            print(f"- {check['id']}: {check['reason']}")
    if summary["skipped_checks"]:
        print("")
        print("Skipped checks:")
        for check in summary["skipped_checks"]:
            print(f"- {check['id']}: {check['reason']}")
    if summary["pending_checks"]:
        print("")
        print("Pending checks:")
        for check in summary["pending_checks"]:
            print(f"- {check['id']}: {check['reason']}")
    if summary["known_blockers"]:
        print("")
        print("Known blockers:")
        for blocker in summary["known_blockers"]:
            print(f"- {blocker['id']}: {blocker['impact']}")
    print("")
    print(f"Recommended next subphase: {summary['recommended_next_subphase']}")
    print("")
    print("Invariant metadata:")
    for name, value in summary["invariants"].items():
        print(f"- {name}={json.dumps(value)}")


if __name__ == "__main__":
    raise SystemExit(main())
