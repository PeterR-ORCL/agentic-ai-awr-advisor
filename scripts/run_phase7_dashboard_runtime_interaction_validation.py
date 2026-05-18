#!/usr/bin/env python3
"""Validate Phase 7CM dashboard runtime interaction wiring."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]

BLOCKER_ID = "DASHBOARD_RUNTIME_INTERACTION_NOT_WIRED"
SELECTION_BLOCKER_ID = "DASHBOARD_SELECTION_WORKFLOW_UNCLEAR"
VALIDATION_NAME = "Phase 7CM Index Source Selection Runtime Validation"

REQUIRED_SCREEN_ACTIONS: dict[str, tuple[str, ...]] = {
    "index_source_mode": ("source_selection_handoff",),
}

GENERATED_DASHBOARD_FILES: tuple[str, ...] = (
    "awr_dashboard/index.html",
)

TREND_AWARE_SCORING_ARTIFACTS: tuple[str, ...] = (
    "src/learning/trend_aware_scoring.py",
    "tests/test_phase7_trend_aware_scoring.py",
    "docs/architecture/phase7_trend_aware_scoring.md",
    "docs/architecture/phase7_trend_aware_scoring_model.md",
    "scripts/run_phase7_ml_validation.py",
    "scripts/run_phase7_ml_readiness_check.py",
)

INVARIANTS: dict[str, bool] = {
    "phase7_complete": False,
    "phase8_started": False,
    "phase8_behavior_implemented": False,
    "phase4i_contract_protected": True,
    "deterministic_runtime_authoritative": True,
    "ml_scoring_shadow_or_advisory_only": True,
    "trend_aware_scoring_shadow_or_advisory_only": True,
    "uncontrolled_runtime_mutation_allowed": False,
    "adaptive_runtime_default_active": False,
    "runtime_influence_denied_by_default": True,
    "dashboard_workflows_do_not_mutate_truth_directly": True,
    "recommendation_truth_direct_mutation_allowed": False,
    "run_analysis_direct_button_coupling_allowed": False,
    "dashboard_controls_activate_trend_aware_scoring": False,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Phase 7CM dashboard runtime interaction wiring.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument(
        "--generated-dir",
        default="",
        help="Optional directory containing generated dashboard HTML files.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    generated_dir = Path(args.generated_dir).expanduser().resolve() if args.generated_dir else None
    summary = run_validation(generated_dir=generated_dir)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["dashboard_runtime_interaction_ready"] else 1


def run_validation(*, generated_dir: Path | None = None) -> dict[str, Any]:
    source_path = ROOT / "src" / "reporting" / "html_dashboard.py"
    source_text = read_text(source_path)
    generated_paths = dashboard_generated_paths(generated_dir)
    generated_texts = {
        path: read_text(real_path)
        for path, real_path in generated_paths.items()
        if real_path.is_file()
    }
    return validate_dashboard_runtime_interaction(
        source_text=source_text,
        generated_texts=generated_texts,
        service_exists=(ROOT / "scripts" / "dashboard_workflow_service.py").is_file(),
        contract_exists=(ROOT / "src" / "learning" / "dashboard_runtime_interaction.py").is_file(),
    )


def validate_dashboard_runtime_interaction(
    *,
    source_text: str,
    generated_texts: dict[str, str] | None = None,
    service_exists: bool = True,
    contract_exists: bool = True,
) -> dict[str, Any]:
    generated_texts = generated_texts or {}
    source_controls = extract_action_controls(source_text)
    generated_controls = extract_action_controls("\n".join(generated_texts.values()))
    source_screen_results = validate_source_screen_controls(source_text, source_controls)
    generated_has_7cm = any("data-phase7-runtime-interaction-panel" in text for text in generated_texts.values())
    generated_screen_results = validate_screen_controls(generated_controls)
    service_smoke = run_service_smoke_test() if service_exists and contract_exists else {
        "status": "skipped",
        "accepted": False,
        "queued": False,
        "audit_reference_exists": False,
        "index_source_request_accepted": False,
        "invalid_request_rejected": False,
        "reason": "service or contract artifact missing",
    }
    contradictory_text_result = validate_no_contradictory_operational_text(
        source_text,
        generated_texts,
    )
    index_source_result = validate_index_source_selection_workflow(generated_texts)
    preview_context_result = validate_preview_only_context_markers(
        source_text,
        generated_texts,
    )
    selection_ux_result = validate_selection_workflow_ux(generated_texts)
    selection_key_result = validate_required_selection_keys(generated_controls)
    state_key_coverage_result = validate_dashboard_state_key_coverage(
        source_text,
        generated_texts,
    )
    source_selection_behavior_result = validate_index_source_selection_behavior_contract(
        source_text,
        generated_texts,
    )
    picker_support_result = validate_picker_source_selection_support(
        source_text,
        generated_texts,
    )
    current_workflow_text_result = validate_no_current_workflow_preview_text(generated_texts)
    pipeline_source_summary_result = validate_pipeline_source_summary(
        source_text,
        generated_texts,
    )
    governed_memory_result = validate_governed_memory_production_wording(
        generated_texts,
    )
    service_validation_ready = (
        service_smoke.get("status") == "passed"
        and service_smoke.get("accepted_source_modes")
        == ["existing_run", "local_file", "local_staged", "object_storage"]
        and service_smoke.get("invalid_request_rejected") is True
        and service_smoke.get("invalid_source_requests_rejected") is True
        and service_smoke.get("existing_run_lookup_tested") is True
        and service_smoke.get("object_storage_validation_tested") is True
        and service_smoke.get("invalid_object_storage_rejected") is True
    )
    existing_run_lookup_ready = (
        service_smoke.get("existing_run_lookup_tested") is True
        and service_smoke.get("existing_run_lookup_response", {}).get("status") == "accepted"
        and int(service_smoke.get("existing_run_lookup_response", {}).get("run_count") or 0) > 0
    )
    object_storage_validation_ready = (
        service_smoke.get("object_storage_validation_tested") is True
        and service_smoke.get("object_storage_validation_response", {}).get("status") == "accepted"
        and service_smoke.get("object_storage_validation_response", {}).get("validation_status") == "valid"
        and service_smoke.get("invalid_object_storage_rejected") is True
    )
    checks = [
        check_result(
            "source_index_source_selection_action_control",
            all(result["status"] == "passed" for result in source_screen_results.values()),
            "source dashboard contains the required governed index/source-selection action control",
        ),
        check_result(
            "dashboard_js_bridge",
            all(
                phrase in source_text
                for phrase in (
                    "Phase7DashboardRuntimeInteractionBridge",
                    "PHASE7_DASHBOARD_ACTION_ENDPOINT",
                    "window['fetch']",
                    "data-phase7-action-control",
                )
            ),
            "source dashboard includes the governed request bridge",
        ),
        check_result(
            "service_script_exists",
            service_exists,
            "local governed workflow service exists",
        ),
        check_result(
            "action_contract_exists",
            contract_exists,
            "Phase 7CM dashboard action contract exists",
        ),
        check_result(
            "generated_index_source_selection_action_control",
            generated_has_7cm
            and all(result["status"] == "passed" for result in generated_screen_results.values()),
            "generated index dashboard contains the required governed source-selection action control",
        ),
        check_result(
            "service_bridge_accepts_governed_request",
            service_smoke.get("accepted") is True
            and service_smoke.get("queued") is True
            and service_smoke.get("audit_reference_exists") is True,
            "local governed workflow service accepts, validates, and queues an index/source-selection request",
        ),
        check_result(
            "service_bridge_accepts_index_source_request",
            service_smoke.get("index_source_request_accepted") is True,
            "local governed workflow service accepts an index/source-selection handoff request",
        ),
        check_result(
            "service_bridge_accepts_all_source_modes",
            service_smoke.get("accepted_source_modes") == [
                "existing_run",
                "local_file",
                "local_staged",
                "object_storage",
            ],
            "local governed workflow service accepts local folder, local file, existing run, and Object Storage metadata",
        ),
        check_result(
            "service_bridge_rejects_invalid_request",
            service_smoke.get("invalid_request_rejected") is True,
            "local governed workflow service rejects invalid/unsafe requests",
        ),
        check_result(
            "service_bridge_rejects_invalid_source_metadata",
            service_smoke.get("invalid_source_requests_rejected") is True,
            "local governed workflow service rejects missing candidates and invalid local file extensions",
        ),
        check_result(
            "service_bridge_queries_existing_runs",
            service_smoke.get("existing_run_lookup_tested") is True,
            "local governed workflow service performs service-side existing run lookup and returns selectable run options",
        ),
        check_result(
            "service_bridge_validates_object_storage",
            service_smoke.get("object_storage_validation_tested") is True
            and service_smoke.get("invalid_object_storage_rejected") is True,
            "local governed workflow service validates Object Storage metadata and rejects incomplete metadata",
        ),
        check_result(
            "no_contradictory_final_operational_text",
            contradictory_text_result["status"] == "passed",
            contradictory_text_result["reason"],
        ),
        check_result(
            "index_source_selection_workflow_ready",
            index_source_result["status"] == "passed",
            index_source_result["reason"],
        ),
        check_result(
            "preview_only_panels_are_legacy_or_read_only",
            preview_context_result["status"] == "passed",
            preview_context_result["reason"],
        ),
        check_result(
            "selection_workflow_ux_present",
            selection_ux_result["status"] == "passed",
            selection_ux_result["reason"],
        ),
        check_result(
            "required_selection_keys_are_operational",
            selection_key_result["status"] == "passed",
            selection_key_result["reason"],
        ),
        check_result(
            "dashboard_state_allowlist_covers_selection_keys",
            state_key_coverage_result["status"] == "passed",
            state_key_coverage_result["reason"],
        ),
        check_result(
            "index_source_selection_click_path_contract",
            source_selection_behavior_result["status"] == "passed",
            source_selection_behavior_result["reason"],
        ),
        check_result(
            "os_picker_source_selection_support",
            picker_support_result["status"] == "passed",
            picker_support_result["reason"],
        ),
        check_result(
            "preview_no_api_no_write_text_is_legacy_only",
            current_workflow_text_result["status"] == "passed",
            current_workflow_text_result["reason"],
        ),
        check_result(
            "pipeline_source_summary_ready",
            pipeline_source_summary_result["status"] == "passed",
            pipeline_source_summary_result["reason"],
        ),
        check_result(
            "governed_memory_production_wording",
            governed_memory_result["status"] == "passed",
            governed_memory_result["reason"],
        ),
        check_result(
            "no_direct_run_analysis_button_coupling",
            'data-run-analysis-coupling="true"' not in source_text
            and "scripts/run_analysis.py" not in action_control_text(source_text),
            "dashboard action controls do not couple to run_analysis.py",
        ),
        check_result(
            "no_phase4i_mutation_path",
            'data-phase4i-mutation-allowed="true"' not in source_text
            and "phase4i_mutation_allowed: true" not in source_text.lower(),
            "dashboard action controls deny Phase 4I mutation",
        ),
        check_result(
            "no_recommendation_truth_direct_mutation",
            'data-direct-truth-mutation-allowed="true"' not in source_text
            and "recommendation_truth_direct_mutation" not in source_text.lower(),
            "dashboard action controls deny direct recommendation truth mutation",
        ),
        check_result(
            "adaptive_runtime_not_default_active",
            'data-runtime-influence-granted="true"' not in source_text
            and "runtime_influence_granted: true" not in source_text.lower(),
            "runtime influence is denied by default",
        ),
        check_result(
            "no_phase8_behavior",
            'data-phase8-behavior="true"' not in source_text
            and "phase8_behavior: true" not in source_text.lower(),
            "Phase 8 behavior is not exposed by dashboard controls",
        ),
        check_result(
            "trend_aware_scoring_7u_artifacts_present",
            all((ROOT / artifact).is_file() for artifact in TREND_AWARE_SCORING_ARTIFACTS),
            "Phase 7U trend-aware scoring artifacts remain present",
        ),
        check_result(
            "trend_aware_scoring_shadow_only",
            all(
                phrase not in source_text.lower()
                for phrase in (
                    'data-trend-aware-runtime-active="true"',
                    "trend_aware_runtime_activation: true",
                    "trend_aware_scoring_runtime_active: true",
                    "trend_aware_score_runtime_truth",
                    "activate_trend_aware_scoring_runtime",
                )
            ),
            "dashboard controls do not activate trend-aware scoring as runtime truth",
        ),
    ]
    failures = [check["reason"] for check in checks if check["status"] == "failed"]
    for screen, result in source_screen_results.items():
        if result["status"] != "passed":
            failures.append(f"{screen}: {result['reason']}")
    if generated_has_7cm:
        for screen, result in generated_screen_results.items():
            if result["status"] != "passed":
                failures.append(f"generated {screen}: {result['reason']}")
    else:
        failures.append("generated dashboard evidence is missing 7CM runtime interaction markers")
    if service_smoke.get("status") != "passed":
        failures.append(f"service bridge smoke test: {service_smoke.get('reason')}")
    if contradictory_text_result["status"] != "passed":
        failures.append(contradictory_text_result["reason"])
    if index_source_result["status"] != "passed":
        failures.append(index_source_result["reason"])
    if preview_context_result["status"] != "passed":
        failures.append(preview_context_result["reason"])
    if selection_ux_result["status"] != "passed":
        failures.append(selection_ux_result["reason"])
    if selection_key_result["status"] != "passed":
        failures.append(selection_key_result["reason"])
    if state_key_coverage_result["status"] != "passed":
        failures.append(state_key_coverage_result["reason"])
    if source_selection_behavior_result["status"] != "passed":
        failures.append(source_selection_behavior_result["reason"])
    if picker_support_result["status"] != "passed":
        failures.append(picker_support_result["reason"])
    if current_workflow_text_result["status"] != "passed":
        failures.append(current_workflow_text_result["reason"])
    if pipeline_source_summary_result["status"] != "passed":
        failures.append(pipeline_source_summary_result["reason"])
    if governed_memory_result["status"] != "passed":
        failures.append(governed_memory_result["reason"])
    source_ready = not failures
    index_actions = source_screen_results["index_source_mode"]["present_action_types"]
    index_ready = source_screen_results["index_source_mode"]["status"] == "passed"
    return {
        "phase": "Phase 7",
        "subphase": "7CM",
        "validation_name": VALIDATION_NAME,
        "scope": "index_source_selection_runtime_workflow",
        "scope_note": (
            "7CM certifies only the index/source-selection runtime workflow. "
            "Screen 1-6 runtime workflows remain pending for 7CN-7CS and "
            "cross-screen integration remains pending for 7CT."
        ),
        "dashboard_runtime_interaction_ready": source_ready,
        "index_source_selection_ready": source_ready,
        "picker_support_ready": picker_support_result["status"] == "passed",
        "source_validation_ready": (
            picker_support_result["status"] == "passed" and service_validation_ready
        ),
        "service_validation_ready": service_validation_ready,
        "existing_run_lookup_ready": existing_run_lookup_ready,
        "object_storage_validation_ready": object_storage_validation_ready,
        "pipeline_source_summary_ready": pipeline_source_summary_result["status"] == "passed",
        "governed_memory_production_wording_ready": governed_memory_result["status"] == "passed",
        "blocker_id": BLOCKER_ID,
        "blocker_active": not source_ready,
        "selection_blocker_id": SELECTION_BLOCKER_ID,
        "selection_blocker_active": False if source_ready else True,
        "screens": source_screen_results,
        "generated_dashboard": {
            "validated": generated_has_7cm,
            "files": sorted(generated_texts),
            "screens": generated_screen_results,
        },
        "service_bridge": service_smoke,
        "deferred_screen_workflow_blocker_id": SELECTION_BLOCKER_ID,
        "deferred_screens": [
            "7CN Screen 1 parser governance runtime workflow",
            "7CO Screen 2 diagnostic review runtime workflow",
            "7CP Screen 3 active re-analysis runtime workflow",
            "7CQ Screen 4 historical review runtime workflow",
            "7CR Screen 5 recommendation/action/outcome runtime workflow",
            "7CS Screen 6 governance runtime workflow",
            "7CT cross-screen runtime workflow integration",
        ],
        "remaining_deferred_screens": [
            "7CN Screen 1 parser governance runtime workflow",
            "7CO Screen 2 diagnostic review runtime workflow",
            "7CP Screen 3 active re-analysis runtime workflow",
            "7CQ Screen 4 historical review runtime workflow",
            "7CR Screen 5 recommendation/action/outcome runtime workflow",
            "7CS Screen 6 governance runtime workflow",
            "7CT cross-screen runtime workflow integration",
        ],
        "index_source_status": {
            "ready": index_ready,
            "present_action_types": index_actions,
            "required_action_types": list(REQUIRED_SCREEN_ACTIONS["index_source_mode"]),
            "source_selection_handoff": "source_selection_handoff" in index_actions,
        },
        "checks": checks,
        "failures": failures,
        "invariants": dict(INVARIANTS),
    }


def dashboard_generated_paths(generated_dir: Path | None) -> dict[str, Path]:
    if generated_dir is None:
        return {path: ROOT / path for path in GENERATED_DASHBOARD_FILES}
    return {path: generated_dir / Path(path).name for path in GENERATED_DASHBOARD_FILES}


def validate_screen_controls(controls: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    by_screen: dict[str, set[str]] = {screen: set() for screen in REQUIRED_SCREEN_ACTIONS}
    for control in controls:
        screen_id = control.get("screen-id") or ""
        action_type = control.get("action-type") or ""
        if screen_id in by_screen:
            by_screen[screen_id].add(action_type)
    for screen, required in REQUIRED_SCREEN_ACTIONS.items():
        present = sorted(by_screen[screen])
        missing = [action for action in required if action not in by_screen[screen]]
        passed = not missing
        results[screen] = {
            "screen_id": screen,
            "status": "passed" if passed else "failed",
            "required_action_types": list(required),
            "present_action_types": present,
            "missing_action_types": missing,
            "reason": (
                "required governed action controls are present"
                if passed
                else "missing governed action controls: " + ", ".join(missing)
            ),
        }
    return results


def validate_source_screen_controls(
    source_text: str,
    controls: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    rendered_results = validate_screen_controls(controls)
    if any(result["status"] == "passed" for result in rendered_results.values()):
        return rendered_results
    results: dict[str, dict[str, Any]] = {}
    for screen, required in REQUIRED_SCREEN_ACTIONS.items():
        screen_present = f'screen_id="{screen}"' in source_text or f"screen_id='{screen}'" in source_text
        present = [
            action
            for action in required
            if f'"action_type": "{action}"' in source_text
            or f"'action_type': '{action}'" in source_text
        ]
        missing = [action for action in required if action not in present]
        if not screen_present and screen == "index_source_mode":
            screen_present = 'screen_id="index_source_mode"' in source_text
        if not screen_present:
            missing = list(required)
        passed = screen_present and not missing
        results[screen] = {
            "screen_id": screen,
            "status": "passed" if passed else "failed",
            "required_action_types": list(required),
            "present_action_types": sorted(present),
            "missing_action_types": missing,
            "reason": (
                "required governed action registrations are present in dashboard source"
                if passed
                else "missing governed action registrations: " + ", ".join(missing)
            ),
        }
    return results


def run_service_smoke_test() -> dict[str, Any]:
    """Exercise the local service path for 7CM index/source-selection requests."""

    service_path = ROOT / "scripts" / "dashboard_workflow_service.py"
    try:
        service_module = load_module(service_path, "phase7_dashboard_workflow_service_smoke")
        handler = service_module.Phase7DashboardWorkflowHandler
        endpoint_path = service_module.ENDPOINT_PATH
        existing_runs_endpoint_path = service_module.EXISTING_RUNS_ENDPOINT_PATH
        object_storage_validate_endpoint_path = service_module.OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH
    except Exception as exc:  # pragma: no cover - defensive import report
        return {
            "status": "failed",
            "accepted": False,
            "queued": False,
            "audit_reference_exists": False,
            "reason": f"unable to load workflow service: {exc}",
        }
    queue_dir = Path(tempfile.mkdtemp(prefix="phase7cm-dashboard-actions-"))
    try:
        request_results = []
        for payload in index_service_smoke_payloads():
            body = json.dumps(payload).encode("utf-8")
            response_payload, status_code = invoke_service_handler(
                handler,
                endpoint_path,
                body,
                queue_dir,
            )
            audit_reference = response_payload.get("audit_reference")
            audit_reference_exists = bool(
                audit_reference and Path(audit_reference).is_file()
            )
            accepted = (
                status_code == 202
                and response_payload.get("status") == "accepted"
                and bool(response_payload.get("queued"))
                and audit_reference_exists
            )
            request_results.append(
                {
                    "screen_id": payload["screen_id"],
                    "action_type": payload["action_type"],
                    "selectedSourceMode": payload.get("payload", {}).get("selectedSourceMode"),
                    "status_code": status_code,
                    "accepted": accepted,
                    "queued": bool(response_payload.get("queued")),
                    "audit_reference_exists": audit_reference_exists,
                    "audit_reference": audit_reference,
                    "request_id": response_payload.get("request_id"),
                }
            )
        index_source_request_accepted = any(
            result["screen_id"] == "index_source_mode" and result["accepted"]
            for result in request_results
        )
        invalid_response, invalid_status_code = invoke_service_handler(
            handler,
            endpoint_path,
            json.dumps(invalid_service_smoke_payload()).encode("utf-8"),
            queue_dir,
        )
        invalid_request_rejected = (
            invalid_status_code == 400
            and invalid_response.get("status") == "rejected"
            and not invalid_response.get("queued")
        )
        existing_runs_response, existing_runs_status_code = invoke_service_handler(
            handler,
            existing_runs_endpoint_path,
            json.dumps(existing_run_lookup_smoke_payload()).encode("utf-8"),
            queue_dir,
            connection_factory=fake_existing_run_connection_factory,
        )
        existing_run_lookup_tested = (
            existing_runs_status_code == 202
            and existing_runs_response.get("status") == "accepted"
            and existing_runs_response.get("run_count", 0) >= 1
            and existing_runs_response.get("runs")
            and Path(existing_runs_response.get("audit_reference") or "").is_file()
        )
        existing_empty_response, existing_empty_status_code = invoke_service_handler(
            handler,
            existing_runs_endpoint_path,
            json.dumps(existing_run_lookup_smoke_payload()).encode("utf-8"),
            queue_dir,
            connection_factory=fake_empty_existing_run_connection_factory,
        )
        existing_run_empty_state_tested = (
            existing_empty_status_code == 202
            and existing_empty_response.get("status") == "accepted"
            and existing_empty_response.get("validation_status") == "empty"
            and existing_empty_response.get("run_count") == 0
            and "No prior runs found in governed persistence"
            in str(existing_empty_response.get("message") or "")
        )
        existing_unavailable_response, existing_unavailable_status_code = invoke_service_handler(
            handler,
            existing_runs_endpoint_path,
            json.dumps(existing_run_lookup_smoke_payload()).encode("utf-8"),
            queue_dir,
            connection_factory=fake_unavailable_existing_run_connection_factory,
        )
        existing_run_unavailable_state_tested = (
            existing_unavailable_status_code == 503
            and existing_unavailable_response.get("status") == "pending"
            and existing_unavailable_response.get("validation_status") == "unavailable"
            and "Existing run lookup unavailable. Governed workflow service is not connected to DB"
            in str(existing_unavailable_response.get("message") or "")
        )
        object_storage_response, object_storage_status_code = invoke_service_handler(
            handler,
            object_storage_validate_endpoint_path,
            json.dumps(object_storage_validation_smoke_payload()).encode("utf-8"),
            queue_dir,
        )
        object_storage_validation_tested = (
            object_storage_status_code == 202
            and object_storage_response.get("status") == "accepted"
            and object_storage_response.get("validation_status") == "valid"
            and Path(object_storage_response.get("audit_reference") or "").is_file()
        )
        invalid_object_response, invalid_object_status_code = invoke_service_handler(
            handler,
            object_storage_validate_endpoint_path,
            json.dumps(invalid_object_storage_validation_smoke_payload()).encode("utf-8"),
            queue_dir,
        )
        invalid_object_storage_rejected = (
            invalid_object_status_code == 400
            and invalid_object_response.get("status") == "rejected"
        )
        invalid_source_results = []
        for payload in invalid_source_smoke_payloads():
            response_payload, status_code = invoke_service_handler(
                handler,
                endpoint_path,
                json.dumps(payload).encode("utf-8"),
                queue_dir,
            )
            invalid_source_results.append(
                {
                    "selectedSourceMode": payload.get("payload", {}).get("selectedSourceMode"),
                    "case": payload.get("payload", {}).get("validation"),
                    "status_code": status_code,
                    "rejected": status_code == 400
                    and response_payload.get("status") == "rejected",
                }
            )
        invalid_source_requests_rejected = all(
            result["rejected"] for result in invalid_source_results
        )
        accepted = all(result["accepted"] for result in request_results)
        queued = all(result["queued"] for result in request_results)
        accepted_source_modes = sorted(
            result.get("selectedSourceMode", "")
            for result in request_results
            if result["accepted"]
        )
        audit_reference_exists = all(
            result["audit_reference_exists"] for result in request_results
        )
        passed = (
            accepted
            and queued
            and audit_reference_exists
            and index_source_request_accepted
            and invalid_request_rejected
            and existing_run_lookup_tested
            and existing_run_empty_state_tested
            and existing_run_unavailable_state_tested
            and object_storage_validation_tested
            and invalid_object_storage_rejected
            and invalid_source_requests_rejected
        )
        return {
            "status": "passed" if passed else "failed",
            "accepted": accepted,
            "queued": queued,
            "audit_reference_exists": audit_reference_exists,
            "index_source_request_accepted": index_source_request_accepted,
            "accepted_source_modes": accepted_source_modes,
            "invalid_request_rejected": invalid_request_rejected,
            "existing_run_lookup_tested": existing_run_lookup_tested,
            "existing_run_lookup_status_code": existing_runs_status_code,
            "existing_run_lookup_response": existing_runs_response,
            "existing_run_empty_state_tested": existing_run_empty_state_tested,
            "existing_run_empty_status_code": existing_empty_status_code,
            "existing_run_empty_response": existing_empty_response,
            "existing_run_unavailable_state_tested": existing_run_unavailable_state_tested,
            "existing_run_unavailable_status_code": existing_unavailable_status_code,
            "existing_run_unavailable_response": existing_unavailable_response,
            "object_storage_validation_tested": object_storage_validation_tested,
            "object_storage_validation_status_code": object_storage_status_code,
            "object_storage_validation_response": object_storage_response,
            "invalid_object_storage_rejected": invalid_object_storage_rejected,
            "invalid_source_requests_rejected": invalid_source_requests_rejected,
            "invalid_source_results": invalid_source_results,
            "evidence_dir": str(queue_dir),
            "request_results": request_results,
            "reason": (
                "service accepted and queued governed index/source-selection request and rejected an invalid request"
                if passed
                else "service response did not prove required accepted queued audit record and invalid source rejection"
            ),
        }
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "failed",
            "accepted": False,
            "queued": False,
            "audit_reference_exists": False,
            "index_source_request_accepted": False,
            "evidence_dir": str(queue_dir),
            "invalid_request_rejected": False,
            "reason": f"service smoke request failed: {exc}",
        }


def index_service_smoke_payloads() -> list[dict[str, Any]]:
    """Return governed source-selection payloads required for narrowed 7CM proof."""

    common = {
            "actor_id": "ACTOR-7CM-VALIDATION",
            "screen_id": "index_source_mode",
            "action_type": "source_selection_handoff",
            "workflow_type": "index_source_selection_handoff",
            "target_type": "source_selection",
            "runtime_influence_granted": False,
            "phase4i_mutation_allowed": False,
            "phase8_behavior": False,
            "direct_truth_mutation_allowed": False,
            "run_analysis_coupling": False,
        }
    source_payloads = [
        (
            "local_staged",
            {
                "sourceSelectionMethod": "os_folder_picker",
                "selectedLocalFolderFileCount": "3",
                "selectedLocalFolderOutFileCount": "2",
                "selectedLocalFolderSampleFiles": "FINDB/awr_one.out, FINDB/awr_two.out",
                "selectedLocalRelativePaths": "FINDB/awr_one.out, FINDB/awr_two.out, notes.txt",
                "selectedLocalTotalBytes": "4096",
                "selectedLocalFolderCandidateCount": "2",
                "selectedLocalFolderAwrCandidateCount": "2",
                "selectedLocalFolderRejectedCount": "1",
                "selectedLocalFolderValidationStatus": "warning-backend-validation-pending",
                "selectedLocalFolderValidationMessages": "Candidate .out AWR files found by extension; content signature validation is backend-pending.",
                "awr_signature_validation": "backend_validation_pending",
                "selectedSourcePath": "",
            },
        ),
        (
            "local_file",
            {
                "sourceSelectionMethod": "os_file_picker",
                "selectedLocalFileName": "report.out",
                "selectedLocalFileSize": "2048",
                "selectedLocalFileType": "out",
                "selectedLocalFileExtension": "out",
                "selectedLocalFileValidationStatus": "warning-backend-validation-pending",
                "awr_signature_validation": "backend_validation_pending",
                "selectedSourcePath": "",
            },
        ),
        (
            "existing_run",
            {
                "sourceSelectionMethod": "existing_run_reference",
                "selectedRunReference": "RUN_HISTORY_ID:9001",
                "existingRunLookupStatus": "valid",
                "existingRunLookupMessage": "Existing run selected from governed service lookup.",
                "existingRunLookupCount": "1",
            },
        ),
        (
            "object_storage",
            {
                "sourceSelectionMethod": "object_storage_metadata",
                "objectStorageNamespace": "axxduehrw7lz",
                "objectStorageBucket": "agentic-ai-awr-raw",
                "objectStorageObjectName": "awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out",
                "objectStorageRegion": "us-phoenix-1",
                "objectStorageValidationStatus": "valid",
                "objectStorageValidationMessage": "Object Storage metadata accepted by governed backend validation.",
            },
        ),
    ]
    payloads: list[dict[str, Any]] = []
    for mode, source_metadata in source_payloads:
        payloads.append(
            {
                **common,
                "target_id": f"INDEX-SOURCE-SELECTION-{mode.upper()}",
                "payload": {
                    "validation": "phase7cm_index_source_selection_service_bridge_smoke",
                    "selected_source_key": "selectedSourceMode",
                    "selectedSourceMode": mode,
                    "sourceSelectionMethod": "",
                    "selectedSourcePath": "",
                    "selectedLocalFolderFileCount": "",
                    "selectedLocalFolderOutFileCount": "",
                    "selectedLocalFolderSampleFiles": "",
                    "selectedLocalRelativePaths": "",
                    "selectedLocalTotalBytes": "",
                    "selectedLocalFolderCandidateCount": "",
                    "selectedLocalFolderAwrCandidateCount": "",
                    "selectedLocalFolderRejectedCount": "",
                    "selectedLocalFolderValidationStatus": "",
                    "selectedLocalFolderValidationMessages": "",
                    "selectedLocalFileName": "",
                    "selectedLocalFileSize": "",
                    "selectedLocalFileType": "",
                    "selectedLocalFileExtension": "",
                    "selectedLocalFileValidationStatus": "",
                    "selectedRunReference": "",
                    "existingRunLookupStatus": "",
                    "existingRunLookupMessage": "",
                    "existingRunLookupCount": "",
                    "objectStorageNamespace": "",
                    "objectStorageBucket": "",
                    "objectStorageObjectName": "",
                    "objectStorageRegion": "",
                    "objectStorageValidationStatus": "",
                    "objectStorageValidationMessage": "",
                    "target_screen": "screen3",
                    "awr_signature_validation": "",
                    "browser_parsing_performed": False,
                    "browser_file_read_attempted": False,
                    "browser_file_upload_performed": False,
                    "browser_object_storage_access_attempted": False,
                    "em_extract_attempted": False,
                    "next_step": "screen_3_history_selector.html",
                    **source_metadata,
                },
            }
        )
    return payloads


def service_smoke_payloads() -> list[dict[str, Any]]:
    """Return reusable future screen payloads for 7CN-7CS contract tests."""

    base = {
        "actor_id": "ACTOR-7CM-VALIDATION",
        "runtime_influence_granted": False,
        "phase4i_mutation_allowed": False,
        "phase8_behavior": False,
        "direct_truth_mutation_allowed": False,
        "run_analysis_coupling": False,
        "future_run_influence_metadata": {
            "requires_governed_materialization": True,
            "requires_runtime_eligibility": True,
            "future_runs_only": True,
            "runtime_activation_granted": False,
            "trend_aware_runtime_activation": False,
        },
    }
    payloads = [
        {
            **base,
            "screen_id": "screen_1",
            "action_type": "parser_mapping_approval_intent",
            "workflow_type": "screen1_parser_mapping_approval_intent",
            "target_type": "parser_mapping_candidate",
            "target_id": "SCREEN1-VALIDATION-PARSER-MAPPING",
            "payload": {"validation": "phase7cm_screen1_service_bridge_smoke"},
        }
    ]
    for action_type, target_type, target_id in (
        ("parser_unknown_approve", "parser_unknown_signal", "SCREEN1-VALIDATION-UNKNOWN-APPROVE"),
        ("parser_unknown_reject", "parser_unknown_signal", "SCREEN1-VALIDATION-UNKNOWN-REJECT"),
        ("parser_unknown_classify", "parser_unknown_signal", "SCREEN1-VALIDATION-UNKNOWN-CLASSIFY"),
        ("parser_unknown_route", "parser_unknown_signal", "SCREEN1-VALIDATION-UNKNOWN-ROUTE"),
        ("knowledge_artifact_approve", "knowledge_artifact", "SCREEN1-VALIDATION-ARTIFACT-APPROVE"),
        ("knowledge_artifact_reject", "knowledge_artifact", "SCREEN1-VALIDATION-ARTIFACT-REJECT"),
    ):
        payloads.append(
            {
                **base,
                "screen_id": "screen_1",
                "action_type": action_type,
                "workflow_type": f"screen1_{action_type}",
                "target_type": target_type,
                "target_id": target_id,
                "payload": {"validation": f"phase7cm_screen1_{action_type}_smoke"},
            }
        )
    payloads.append(
        {
            **base,
            "screen_id": "screen_3",
            "action_type": "screen3_active_reanalysis",
            "workflow_type": "screen3_active_backend_execution",
            "target_type": "backend_execution_request",
            "target_id": "SCREEN3-VALIDATION-ACTIVE-REANALYSIS",
            "execution_mode": "governed_screen3_execution_request",
            "payload": {"validation": "phase7cm_screen3_service_bridge_smoke"},
        }
    )
    screen5_targets = {
        "recommendation_decision": ("recommendation", "SCREEN5-VALIDATION-RECOMMENDATION"),
        "action_assignment_tracking": ("action", "SCREEN5-VALIDATION-ACTION"),
        "status_update": ("action_status", "SCREEN5-VALIDATION-STATUS"),
        "outcome_capture": ("outcome", "SCREEN5-VALIDATION-OUTCOME"),
        "feedback_learning_intent": ("feedback", "SCREEN5-VALIDATION-FEEDBACK"),
    }
    for action_type, (target_type, target_id) in screen5_targets.items():
        payloads.append(
            {
                **base,
                "screen_id": "screen_5",
                "action_type": action_type,
                "workflow_type": f"screen5_{action_type}",
                "target_type": target_type,
                "target_id": target_id,
                "payload": {"validation": f"phase7cm_screen5_{action_type}_smoke"},
            }
        )
    payloads.append(
        {
            **base,
            "screen_id": "screen_6",
            "action_type": "runtime_eligibility_request",
            "workflow_type": "screen6_runtime_eligibility_request",
            "target_type": "runtime_gate",
            "target_id": "SCREEN6-VALIDATION-RUNTIME-ELIGIBILITY",
            "payload": {"validation": "phase7cm_screen6_service_bridge_smoke"},
        }
    )
    return payloads


def invalid_service_smoke_payload() -> dict[str, Any]:
    return {
        "screen_id": "index_source_mode",
        "action_type": "source_selection_handoff",
        "workflow_type": "index_source_selection_handoff",
        "actor_id": "ACTOR-7CM-VALIDATION",
        "target_type": "source_selection",
        "target_id": "INDEX-SOURCE-SELECTION-INVALID",
        "runtime_influence_granted": False,
        "phase4i_mutation_allowed": False,
        "phase8_behavior": False,
        "direct_truth_mutation_allowed": False,
        "run_analysis_coupling": True,
    }


def invalid_source_smoke_payloads() -> list[dict[str, Any]]:
    base = {
        "screen_id": "index_source_mode",
        "action_type": "source_selection_handoff",
        "workflow_type": "index_source_selection_handoff",
        "actor_id": "ACTOR-7CM-VALIDATION",
        "target_type": "source_selection",
        "runtime_influence_granted": False,
        "phase4i_mutation_allowed": False,
        "phase8_behavior": False,
        "direct_truth_mutation_allowed": False,
        "run_analysis_coupling": False,
    }
    return [
        {
            **base,
            "target_id": "INDEX-SOURCE-SELECTION-NO-CANDIDATES",
            "payload": {
                "validation": "no_awr_candidates",
                "selectedSourceMode": "local_staged",
                "sourceSelectionMethod": "os_folder_picker",
                "selectedLocalFolderFileCount": "2",
                "selectedLocalFolderOutFileCount": "0",
                "selectedLocalFolderCandidateCount": "0",
                "selectedLocalFolderAwrCandidateCount": "0",
                "selectedLocalFolderRejectedCount": "2",
                "selectedLocalFolderSampleFiles": "",
                "selectedLocalRelativePaths": "notes.csv, image.png",
                "selectedLocalFolderValidationStatus": "invalid",
                "target_screen": "screen3",
                "browser_parsing_performed": False,
                "browser_file_read_attempted": False,
                "browser_object_storage_access_attempted": False,
                "em_extract_attempted": False,
            },
        },
        {
            **base,
            "target_id": "INDEX-SOURCE-SELECTION-BAD-EXTENSION",
            "payload": {
                "validation": "html_not_supported_in_phase7",
                "selectedSourceMode": "local_file",
                "sourceSelectionMethod": "os_file_picker",
                "selectedLocalFileName": "report.html",
                "selectedLocalFileSize": "1024",
                "selectedLocalFileType": "html",
                "selectedLocalFileExtension": "html",
                "selectedLocalFileValidationStatus": "invalid-extension",
                "target_screen": "screen3",
                "browser_parsing_performed": False,
                "browser_file_read_attempted": False,
                "browser_object_storage_access_attempted": False,
                "em_extract_attempted": False,
            },
        },
    ]


def existing_run_lookup_smoke_payload() -> dict[str, Any]:
    return {
        "screen_id": "index_source_mode",
        "action_type": "existing_run_lookup",
        "workflow_type": "index_existing_run_lookup",
        "target_screen": "screen3",
        "governance_mode": "governed_request",
        "browser_db_query_attempted": False,
        "direct_truth_mutation_allowed": False,
        "phase4i_mutation_allowed": False,
        "phase8_behavior": False,
        "run_analysis_coupling": False,
    }


def object_storage_validation_smoke_payload() -> dict[str, Any]:
    return {
        "screen_id": "index_source_mode",
        "action_type": "object_storage_source_validation",
        "workflow_type": "index_object_storage_source_validation",
        "target_screen": "screen3",
        "governance_mode": "governed_request",
        "objectStorageNamespace": "axxduehrw7lz",
        "objectStorageBucket": "agentic-ai-awr-raw",
        "objectStorageObjectName": "awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out",
        "objectStorageRegion": "us-phoenix-1",
        "browser_object_storage_access_attempted": False,
        "direct_object_storage_execution_attempted": False,
        "direct_truth_mutation_allowed": False,
        "phase4i_mutation_allowed": False,
        "phase8_behavior": False,
        "run_analysis_coupling": False,
    }


def invalid_object_storage_validation_smoke_payload() -> dict[str, Any]:
    payload = object_storage_validation_smoke_payload()
    payload.pop("objectStorageObjectName", None)
    return payload


class FakeExistingRunCursor:
    description = (
        ("RUN_HISTORY_ID",),
        ("SOURCE_FILE_NAME",),
        ("DB_NAME",),
        ("DBID",),
        ("INSTANCE_NAME",),
        ("AWR_BEGIN_TIME",),
        ("AWR_END_TIME",),
        ("DECISION_POSTURE",),
        ("RISK_LEVEL",),
        ("CREATED_AT",),
    )

    def __enter__(self) -> "FakeExistingRunCursor":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def execute(self, _sql: str, _params: dict[str, Any]) -> None:
        return None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return [
            (
                9001,
                "adg_awr_snap_06_adg_transport_lag.out",
                "FINDB",
                "123456789",
                "FINDB1",
                "2026-03-29T06:00:00",
                "2026-03-29T07:00:00",
                "review",
                "medium",
                "2026-03-29T07:05:00",
            )
        ]


class FakeExistingRunConnection:
    def cursor(self) -> FakeExistingRunCursor:
        return FakeExistingRunCursor()

    def close(self) -> None:
        return None


def fake_existing_run_connection_factory() -> FakeExistingRunConnection:
    return FakeExistingRunConnection()


class FakeEmptyExistingRunCursor(FakeExistingRunCursor):
    def fetchall(self) -> list[tuple[Any, ...]]:
        return []


class FakeEmptyExistingRunConnection:
    def cursor(self) -> FakeEmptyExistingRunCursor:
        return FakeEmptyExistingRunCursor()

    def close(self) -> None:
        return None


def fake_empty_existing_run_connection_factory() -> FakeEmptyExistingRunConnection:
    return FakeEmptyExistingRunConnection()


def fake_unavailable_existing_run_connection_factory() -> Any:
    raise RuntimeError("validation DB connection unavailable")


def invoke_service_handler(
    handler_cls: Any,
    endpoint_path: str,
    body: bytes,
    queue_dir: Path,
    connection_factory: Any | None = None,
) -> tuple[dict[str, Any], int]:
    """Invoke the stdlib service handler without opening a network socket."""

    handler = object.__new__(handler_cls)
    handler.path = endpoint_path
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO()
    handler.server = type(
        "Phase7SmokeServer",
        (),
        {
            "phase7_queue_dir": queue_dir,
            "phase7_existing_run_connection_factory": staticmethod(connection_factory)
            if connection_factory is not None
            else None,
        },
    )()
    response_status: dict[str, int] = {}

    def send_response(status_code: int, *_args: Any, **_kwargs: Any) -> None:
        response_status["status_code"] = status_code

    handler.send_response = send_response
    handler.send_header = lambda *_args, **_kwargs: None
    handler.end_headers = lambda: None
    handler_cls.do_POST(handler)
    response = handler.wfile.getvalue()
    return json.loads(response.decode("utf-8")), response_status.get("status_code", 0)


def validate_no_contradictory_operational_text(
    source_text: str,
    generated_texts: dict[str, str],
) -> dict[str, str]:
    """Ensure index preview language is framed as legacy context, not current workflow."""

    del source_text
    index_text = generated_texts.get("awr_dashboard/index.html", "")
    required_legacy_markers = (
        "data-phase7-legacy-context",
        "Legacy 7BQ Read-Only Context",
        "Legacy 7BR Read-Only Context",
        "Legacy 7BS Read-Only Context",
        "Legacy 7BT Read-Only Context",
        "Historical Phase Boundary Evidence",
    )
    missing_markers = [marker for marker in required_legacy_markers if marker not in index_text]
    primary_pos = index_text.find('id="phase7cm-source-intake-panel"')
    legacy_positions = [
        pos
        for pos in (
            index_text.find('id="index-source-mode-entry-panel"'),
            index_text.find('id="index-source-status-panel"'),
            index_text.find('id="index-object-storage-config-panel"'),
            index_text.find('id="index-screen3-handoff-panel"'),
        )
        if pos >= 0
    ]
    first_legacy = min(legacy_positions) if legacy_positions else len(index_text)
    primary_region = visible_text(index_text[:first_legacy]).lower()
    contradictory_phrases = (
        "screen 3 selection handoff remains a future controlled workflow",
        "active handoff/backend request/source intake are not implemented",
        "active handoff, backend request creation",
        "no handoff is performed",
        "no backend request is created",
        "handoff_blocked=true",
        "future input configuration",
        "future examples:",
    )
    present_contradictions = [
        phrase for phrase in contradictory_phrases if phrase in primary_region
    ]
    if missing_markers:
        return {
            "status": "failed",
            "reason": "legacy preview context markers missing: " + ", ".join(missing_markers),
        }
    if primary_pos < 0:
        return {
            "status": "failed",
            "reason": "primary 7CM source-selection workflow is missing from generated index.html",
        }
    if present_contradictions:
        return {
            "status": "failed",
            "reason": "contradictory source-selection workflow text remains: "
            + "; ".join(present_contradictions),
        }
    return {
        "status": "passed",
        "reason": "legacy preview panels are separated from current 7CM operational controls",
    }


def validate_preview_only_context_markers(
    source_text: str,
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Require generated preview-only controls to be legacy/read-only.

    The rendered dashboard is the final-certification surface. Source generator
    strings can contain preview-only implementation scaffolding outside the
    emitted panel context, so this check intentionally validates generated HTML.
    """

    offenders: list[str] = []
    texts = generated_texts
    for label, text in texts.items():
        for match in re.finditer(r'data-preview-only="true"', text):
            start = max(0, match.start() - 1400)
            end = min(len(text), match.end() + 1400)
            context = text[start:end].lower()
            if "legacy" not in context and "read-only" not in context:
                line = text.count("\n", 0, match.start()) + 1
                offenders.append(f"{label}:{line}")
    if offenders:
        return {
            "status": "failed",
            "reason": "preview-only controls lack nearby legacy/read-only context: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "preview-only controls are marked as legacy/read-only context",
        "offenders": [],
    }


def validate_index_source_selection_workflow(
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Require index.html to expose a coherent current 7CM source selection workflow."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    offenders: list[str] = []
    if not index_text:
        return {
            "status": "failed",
            "reason": "index source selection validation could not find generated awr_dashboard/index.html",
            "offenders": ["missing index.html"],
        }
    required_markers = (
        'id="phase7cm-source-intake-panel"',
        'data-phase7-index-source-selection="true"',
        'data-phase7-current-source-card="true"',
        'data-dashboard-select-key="selectedSourceMode"',
        'data-required-selection-key="selectedSourceMode"',
        'data-phase7-action-result-panel="true"',
        'data-phase7-request-id-target="true"',
        'data-phase7-audit-status-area="true"',
        'data-phase7-source-configuration="true"',
        'data-dashboard-state-key="selectedSourcePath"',
        'data-dashboard-state-key="selectedRunReference"',
        'data-dashboard-state-key="objectStorageNamespace"',
        'data-dashboard-state-key="objectStorageBucket"',
        'data-dashboard-state-key="objectStorageObjectName"',
        'data-dashboard-state-key="objectStorageRegion"',
        'data-dashboard-state-key="existingRunLookupStatus"',
        'data-dashboard-state-key="objectStorageValidationStatus"',
        'data-phase7-existing-run-lookup-control="true"',
        'data-phase7-existing-run-options="true"',
        'data-phase7-object-storage-validation-control="true"',
        'data-phase7-dynamic-source-summary="true"',
        'data-phase7-active-source-configuration="true"',
        'data-phase7-source-summary-card="active"',
        'data-phase7-source-summary-card="metadata"',
        'data-phase7-source-summary-card="validation"',
        'data-phase7-source-summary-card="missing"',
        'data-phase7-source-summary-card="handoff"',
        'data-phase7-source-summary-card="action"',
        'data-phase7-source-summary-card="next_step"',
        'data-phase7-source-submit-label="true"',
        'data-phase7-advanced-debug-state="true"',
        'value="data/input"',
        'data-dashboard-state-key="selectedLocalFolderAwrCandidateCount"',
        'data-dashboard-state-key="selectedLocalFolderValidationStatus"',
        'data-dashboard-state-key="selectedLocalFileValidationStatus"',
        'data-dashboard-state-key="awrSignatureValidation"',
        'screen_3_history_selector.html',
        "Choose the input source context",
        "Submit governed source handoff request",
        "Your browser may label this as Upload",
        "files available for governed validation",
        "governed submit not yet performed",
        "Active Source Configuration / Runtime Source State",
        "Active Source Selection",
        "Runtime Source Validation",
        "Active Source",
        "Source Metadata",
        "Validation Status",
        "Handoff Target",
        "Action State",
        'data-phase7-runtime-source-validation="true"',
        'data-phase7-source-validation-card="local_folder"',
        'data-phase7-source-validation-card="local_file"',
        'data-phase7-source-validation-card="existing_run"',
        'data-phase7-source-validation-card="object_storage"',
        'data-phase7-service-availability-status="true"',
        'data-phase7-submit-result-reference="true"',
        "Load Existing Runs",
        "No prior runs found in governed persistence.",
        "Existing run lookup unavailable. Governed workflow service is not connected to DB or returned no runs.",
        "Validate Object Storage Source",
        "Governed workflow service unavailable. Start scripts/dashboard_workflow_service.py and retry.",
        "System Flow",
        "AWR Intelligence Pipeline",
        'data-phase7-current-runtime-pipeline="true"',
        'data-phase7-system-flow-dynamic="true"',
        'data-phase7-source-summary-card="pipeline_mode"',
        'data-phase7-source-summary-card="pipeline_active"',
        'data-phase7-source-summary-card="pipeline_validation"',
        'data-phase7-source-summary-card="pipeline_handoff"',
        "Current source mode",
        "Active source",
        "Current source validation",
        "Current handoff target",
        "Source Configuration Reference / Staging Context",
        'data-phase7-current-source-context="true"',
        'data-phase7-source-configuration-reference="true"',
        'data-phase7-source-summary-card="config_type"',
        'data-phase7-source-summary-card="config_location"',
        'data-phase7-source-summary-card="config_candidates"',
        'data-phase7-source-summary-card="config_validation"',
        'data-phase7-source-summary-card="config_handoff"',
        "Current Source Type",
        "Current Source Location",
        "Current Source Metadata",
        "Current Source Validation",
        "Current Handoff Status",
        "Active Source Configuration / Runtime Source State",
        "Local development fallback",
        "browser does not read local files",
        "never browser-side bucket reads",
        "backend validation pending",
        "Folder picker metadata.",
        "File picker metadata.",
        "Service-selected persisted run reference:",
        "Object Storage metadata. Namespace:",
    )
    normalized_index_text = re.sub(r"\s+", " ", index_text)
    missing = [
        marker
        for marker in required_markers
        if marker not in index_text and marker not in normalized_index_text
    ]
    offenders.extend(f"missing marker: {marker}" for marker in missing)

    source_modes = ("local_staged", "local_file", "existing_run", "object_storage")
    for source_mode in source_modes:
        if f'data-dashboard-select-id="{source_mode}"' not in index_text:
            offenders.append(f"missing current selectable source card: {source_mode}")

    primary_pos = index_text.find('id="phase7cm-source-intake-panel"')
    legacy_positions = [
        pos
        for pos in (
            index_text.find('id="index-source-mode-entry-panel"'),
            index_text.find('id="index-source-status-panel"'),
            index_text.find('id="index-object-storage-config-panel"'),
            index_text.find('id="index-screen3-handoff-panel"'),
        )
        if pos >= 0
    ]
    if primary_pos < 0:
        offenders.append("primary 7CM source intake panel missing")
    elif legacy_positions and min(legacy_positions) < primary_pos:
        offenders.append("legacy source preview panel appears before primary 7CM source intake panel")
    reference_positions = [
        pos
        for pos in (
            index_text.find("data-phase7-default-runtime-pipeline-reference"),
            index_text.find("data-phase7-default-local-staging-reference"),
        )
        if pos >= 0
    ]
    if primary_pos >= 0 and reference_positions and min(reference_positions) < primary_pos:
        offenders.append("default/reference source panels appear before Active Source Configuration")

    for panel_id in (
        "index-source-mode-entry-panel",
        "index-source-status-panel",
        "index-object-storage-config-panel",
        "index-screen3-handoff-panel",
    ):
        marker = f'id="{panel_id}"'
        pos = index_text.find(marker)
        if pos < 0:
            continue
        tag_start = index_text.rfind("<", 0, pos)
        tag_end = index_text.find(">", pos)
        tag = index_text[tag_start: tag_end + 1].lower() if tag_start >= 0 and tag_end >= 0 else ""
        if not tag.startswith("<details"):
            offenders.append(f"legacy panel is not collapsed details: {panel_id}")
        if "phase7-legacy-boundary-details" not in tag:
            offenders.append(f"legacy panel missing historical boundary class: {panel_id}")

    first_legacy = min(legacy_positions) if legacy_positions else len(index_text)
    primary_region = visible_text(index_text[:first_legacy]).lower()
    contradictory_primary_phrases = (
        "future input configuration",
        "future examples:",
        "no handoff is performed",
        "no backend request is created",
        "handoff_blocked=true",
        "screen 3 selection handoff remains a future controlled workflow",
        "active handoff, backend request creation",
        "no screen 3 handoff in this phase",
    )
    for phrase in contradictory_primary_phrases:
        if phrase in primary_region:
            offenders.append(f"primary source workflow contains contradictory phrase: {phrase}")

    if "data-required-selection-key=\"insufficient data" in index_text.lower():
        offenders.append("index source handoff required-selection-key contains fallback/error text")
    if "Current Source Configuration / Staging Context" in index_text:
        offenders.append("static local source reference still uses current-source title")
    if "No service-returned runs available" in index_text:
        offenders.append("existing run empty/unavailable state is generic and not actionable")
    if "Default source: data/input" in index_text:
        offenders.append("local source card presents data/input as active default source instead of reference/fallback")
    disallowed_active_labels = (
        "Default local development mode",
        "Default source",
        "Default Reference Source Types",
        "Default Local Development Staging Path",
        "Current source type: Local Path",
    )
    for phrase in disallowed_active_labels:
        if phrase in index_text:
            offenders.append(f"active source-facing label still uses default/local wording: {phrase}")
    if "Validation Status unavailable: Governed workflow service unavailable for Object Storage validation" in index_text:
        offenders.append("Object Storage unavailable state uses stale non-actionable text")
    if '<span class="source-option active">Local Path</span>' in index_text:
        offenders.append("Default Local Staging Reference visually marks local path as active source")
    for stale_attr in (
        "data-phase7-default-runtime-pipeline-reference",
        "data-phase7-default-local-staging-reference",
        "data-phase7-reference-only",
    ):
        if stale_attr in primary_region:
            offenders.append(f"primary source workflow still uses stale reference-only marker: {stale_attr}")
    for required_dynamic_attr in (
        'data-phase7-current-runtime-pipeline="true"',
        'data-phase7-current-source-context="true"',
    ):
        attr_pos = index_text.find(required_dynamic_attr)
        if attr_pos < 0:
            continue
        tag_start = index_text.rfind("<", 0, attr_pos)
        tag_end = index_text.find(">", attr_pos)
        tag = index_text[tag_start: tag_end + 1].lower() if tag_start >= 0 and tag_end >= 0 else ""
        if tag.startswith("<details"):
            offenders.append(f"{required_dynamic_attr} must remain visible and not be collapsed")
    if "Current Mode: Local" in index_text:
        offenders.append("default pipeline reference still claims active Current Mode: Local")
    if "Current mode: local AWR staging" in index_text:
        offenders.append("default pipeline reference still claims active local AWR mode")
    if "System Flow" in primary_region and "Current Mode: Local" in primary_region:
        offenders.append("system flow presents local mode as active source state")
    for dynamic_marker in (
        "if (mode === 'local_staged')",
        "if (mode === 'local_file')",
        "if (mode === 'existing_run')",
        "if (mode === 'object_storage')",
    ):
        if dynamic_marker not in index_text:
            offenders.append(f"active source configuration missing dynamic branch: {dynamic_marker}")
    if "Advanced Debug State / Browser Selection State" not in index_text:
        offenders.append("raw browser state is not collapsed into Advanced Debug State")
    if "Submit Object Storage Source Handoff" not in index_text:
        offenders.append("shared submit path does not expose Object Storage source-specific label")
    if "Submit Existing Run Source Handoff" not in index_text:
        offenders.append("shared submit path does not expose Existing Run source-specific label")
    if "Submit Local Folder Source Handoff" not in index_text:
        offenders.append("shared submit path does not expose Local Folder source-specific label")
    if "Submit Local File Source Handoff" not in index_text:
        offenders.append("shared submit path does not expose Local File source-specific label")
    forbidden_browser_execution_markers = (
        "FileReader",
        "readAsText",
        "readAsArrayBuffer",
        "readAsDataURL",
        "getObject",
        "listObjects",
        "objectStorageClient",
        "oci-sdk",
    )
    for marker in forbidden_browser_execution_markers:
        if marker.lower() in index_text.lower():
            offenders.append(f"index source workflow exposes browser-side source access marker: {marker}")

    if offenders:
        return {
            "status": "failed",
            "reason": "index source-selection workflow is not operationally coherent: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "index source-selection workflow has current selectable source cards, governed handoff action, result panel, and collapsed historical boundary evidence",
        "offenders": [],
    }


def validate_selection_workflow_ux(generated_texts: dict[str, str]) -> dict[str, Any]:
    """Require index UX landmarks that explain source selection-to-action flow."""

    combined = generated_texts.get("awr_dashboard/index.html", "")
    required_markers = (
        'data-phase7-selection-workflow="true"',
        "Step 1: Select source mode or source context",
        "Step 2: Review source readiness",
        "Step 3: Choose governed source-selection handoff",
        "Step 4: Submit governed source handoff request",
        "Step 5: Review result",
        'data-phase7-current-selection-panel="true"',
        'data-phase7-current-selection-summary="true"',
        'data-action-enabled-state="disabled-no-selection"',
        'data-phase7-action-result-panel="true"',
        'data-phase7-request-id-target="true"',
        'data-phase7-audit-status-area="true"',
        'data-entity-type=',
        'data-downstream-action=',
        "Selection state: not selected",
        "Request ID",
        "Audit record",
        "Open Screen 3",
    )
    missing = [marker for marker in required_markers if marker not in combined]
    generic_only_markers = (
        "Step 1: Select item.",
        "Step 3: Choose governed action.",
        "Step 4: Submit request.",
        "No selection exists yet. Select a card or row to enable governed actions for this screen.",
    )
    generic_found = [marker for marker in generic_only_markers if marker in combined]
    index_text = generated_texts.get("awr_dashboard/index.html", "")
    screen_specific = {
        "index_source_selection_workflow": (
            "select source mode or source context" in visible_text(index_text).lower()
            and "governed source handoff request" in visible_text(index_text).lower()
            and "screen 3" in visible_text(index_text).lower()
        ),
    }
    failed_specific = [name for name, passed in screen_specific.items() if not passed]
    if missing or failed_specific or generic_found:
        parts = []
        if missing:
            parts.append("missing UX markers: " + ", ".join(missing))
        if failed_specific:
            parts.append("missing screen-specific workflow text: " + ", ".join(failed_specific))
        if generic_found:
            parts.append("generic-only workflow text remains: " + ", ".join(generic_found))
        return {"status": "failed", "reason": "; ".join(parts)}
    return {
        "status": "passed",
        "reason": "selection workflow, current selection, enablement, and result/audit UX markers are present",
    }


def validate_required_selection_keys(controls: list[dict[str, str]]) -> dict[str, Any]:
    """Reject fallback/error phrases in operational required-selection metadata."""

    offenders: list[str] = []
    invalid_phrases = (
        "insufficient data",
        "reliable conclusion",
        "unavailable",
        "unknown",
        "n/a",
        "none",
    )
    for index, attrs in enumerate(controls, start=1):
        action = attrs.get("action-type", "unknown-action")
        screen = attrs.get("screen-id", "unknown-screen")
        key = attrs.get("required-selection-key", "")
        normalized = key.strip().lower()
        if not normalized:
            offenders.append(f"{screen}:{action}:missing required-selection-key")
            continue
        if any(phrase in normalized for phrase in invalid_phrases):
            offenders.append(f"{screen}:{action}:invalid required-selection-key={key!r}")
        if screen == "index_source_mode" and key not in {"selectedSourceMode", "selectedSourceContext"}:
            offenders.append(f"{screen}:{action}:expected source selection key, got {key!r}")
        if normalized.startswith("no "):
            offenders.append(f"{screen}:{action}:fallback required-selection-key={key!r}")
    if offenders:
        return {
            "status": "failed",
            "reason": "invalid governed action required-selection-key metadata: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "governed action required-selection-key metadata uses operational state keys",
        "offenders": [],
    }


def validate_dashboard_state_key_coverage(
    source_text: str,
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Ensure generated selection/action keys are allowed dashboard state keys."""

    supported = extract_dashboard_state_keys(source_text)
    offenders: list[str] = []
    if not supported:
        offenders.append("unable to extract DASHBOARD_INTERACTIVITY_STATE_KEYS")

    combined_texts = {"src/reporting/html_dashboard.py": source_text}
    combined_texts.update(generated_texts)
    for label, text in combined_texts.items():
        for attr_name in (
            "data-dashboard-select-key",
            "data-required-selection-key",
            "data-dashboard-state-key",
        ):
            for key in re.findall(rf'{attr_name}="([^"]*)"', text):
                if not key or "{" in key or "}" in key:
                    continue
                if key not in supported:
                    offenders.append(f"{label}:{attr_name}={key!r}")

    source_mode_mapping_required = (
        'sourceMode: \'selectedSourceMode\'' in source_text
        or 'sourceMode: "selectedSourceMode"' in source_text
        or '"sourceMode": "selectedSourceMode"' in source_text
    )
    source_dash_mapping_required = (
        '\'source-mode\': \'selectedSourceMode\'' in source_text
        or 'source-mode: \'selectedSourceMode\'' in source_text
        or '"source-mode": "selectedSourceMode"' in source_text
    )
    if "selectedSourceMode" not in supported:
        offenders.append("selectedSourceMode missing from DASHBOARD_INTERACTIVITY_STATE_KEYS")
    if not source_mode_mapping_required:
        offenders.append("sourceMode mapping to selectedSourceMode missing from DASHBOARD_TYPE_TO_STATE_KEY")
    if not source_dash_mapping_required:
        offenders.append("source-mode mapping to selectedSourceMode missing from DASHBOARD_TYPE_TO_STATE_KEY")

    if offenders:
        return {
            "status": "failed",
            "reason": "dashboard selection keys are not covered by the supported state key allowlist: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
            "supported_state_keys": sorted(supported),
        }
    return {
        "status": "passed",
        "reason": "all generated dashboard select/action keys are present in DASHBOARD_INTERACTIVITY_STATE_KEYS",
        "offenders": [],
        "supported_state_keys": sorted(supported),
    }


def validate_index_source_selection_behavior_contract(
    source_text: str,
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Validate the generated index has enough wiring for source-card click behavior."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    offenders: list[str] = []
    source_modes = ("local_staged", "local_file", "existing_run", "object_storage")
    for source_mode in source_modes:
        card_marker = f'data-dashboard-select-id="{source_mode}"'
        if card_marker not in index_text:
            offenders.append(f"missing selectable card for {source_mode}")
        card_pos = index_text.find(card_marker)
        if card_pos >= 0:
            card_context = index_text[max(0, card_pos - 900): card_pos + 1400]
            for marker in (
                'data-dashboard-selectable="true"',
                'data-dashboard-select-key="selectedSourceMode"',
                'data-dashboard-filter-key="selectedSourceMode"',
                'data-entity-type="source_mode"',
                "Selection state: not selected",
            ):
                if marker not in card_context:
                    offenders.append(f"{source_mode} card missing {marker}")

    required_source_markers = (
        '"selectedSourceMode"',
        '"selectedSourceContext"',
        "'source-mode': 'selectedSourceMode'",
        "sourceMode: 'selectedSourceMode'",
        "function selectDashboardElement",
        "writeDashboardState(nextState)",
        "markSelectedElement(safeState, root)",
        "updateSelectedSummary(safeState, root)",
        "updatePhase7ActionEnablement(safeState, root)",
        "data-action-enabled-state",
        "selectionValueForAction(element, dashboardState)",
        "selected_context_key: selectedContextKey",
        "selected_context_value: selectedContextValue",
        "dashboard_state: dashboardState",
        "selectedSourceMode: dashboardState.selectedSourceMode",
        "source_mode: dashboardState.selectedSourceMode",
        "selectedSourcePath: dashboardState.selectedSourcePath",
        "backend_visible_path: dashboardState.selectedSourcePath",
        "selectedRunReference: dashboardState.selectedRunReference",
        "existingRunLookupStatus: dashboardState.existingRunLookupStatus",
        "objectStorageValidationStatus: dashboardState.objectStorageValidationStatus",
        "objectStorageNamespace: dashboardState.objectStorageNamespace",
        "objectStorageBucket: dashboardState.objectStorageBucket",
        "objectStorageObjectName: dashboardState.objectStorageObjectName",
        "objectStorageRegion: dashboardState.objectStorageRegion",
        "object_storage_namespace: dashboardState.objectStorageNamespace",
        "picker_file_manifest",
        "uploaded_file_manifest",
        "selectedLocalFolderAwrCandidateCount: dashboardState.selectedLocalFolderAwrCandidateCount",
        "selectedLocalFileValidationStatus: dashboardState.selectedLocalFileValidationStatus",
        "awr_signature_validation: dashboardState.awrSignatureValidation",
        "target_screen: 'screen3'",
        "browser_file_read_attempted: false",
        "browser_object_storage_access_attempted: false",
        "em_extract_attempted: false",
        "PHASE7CM_SOURCE_MODE_REQUIRED_FIELDS",
        "sourceSelectionMissingFields",
        "sourceSubmitLabel",
        "sourceActionStateMessage",
        "Select a source to continue.",
        "Ready to submit Local Folder source handoff.",
        "Ready to submit Local File source handoff.",
        "Ready to submit Existing Run source handoff.",
        "Ready to submit Object Storage source handoff.",
        "updateSourceWorkflowSummary",
        "handleExistingRunLookupClick",
        "handleObjectStorageValidationClick",
        "derivePhase7Endpoint",
        "PHASE7_EXISTING_RUN_LOOKUP_ENDPOINT",
        "PHASE7_OBJECT_STORAGE_VALIDATE_ENDPOINT",
        "handleDashboardStateInput",
    )
    for marker in required_source_markers:
        if marker not in source_text:
            offenders.append(f"source JS missing {marker}")

    required_index_markers = (
        'data-phase7-current-selection-summary="true"',
        'data-dashboard-selected-summary',
        'data-required-selection-key="selectedSourceMode"',
        'data-action-enabled-state="disabled-no-selection"',
        'data-phase7-action-result-panel="true"',
        'data-phase7-request-id-target="true"',
        'data-phase7-audit-status-area="true"',
        'data-phase7-source-configuration="true"',
        'data-dashboard-state-input="true"',
        'data-dashboard-state-key="selectedSourcePath"',
        'data-dashboard-state-key="selectedRunReference"',
        'data-dashboard-state-key="objectStorageNamespace"',
        'data-dashboard-state-key="objectStorageBucket"',
        'data-dashboard-state-key="objectStorageObjectName"',
        'data-dashboard-state-key="objectStorageRegion"',
        'data-dashboard-state-key="existingRunLookupStatus"',
        'data-dashboard-state-key="objectStorageValidationStatus"',
        'data-phase7-existing-run-lookup-control="true"',
        'data-phase7-existing-run-options="true"',
        'data-phase7-object-storage-validation-control="true"',
        'data-phase7-dynamic-source-summary="true"',
        'data-phase7-source-submit-label="true"',
        "data/input",
        "Request ID",
        "Audit record",
        "success/failure",
    )
    for marker in required_index_markers:
        if marker not in index_text:
            offenders.append(f"generated index missing {marker}")

    if offenders:
        return {
            "status": "failed",
            "reason": "index source-selection click/submit behavior contract is incomplete: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "index source cards select selectedSourceMode, update Current Selection, enable handoff, and include selected source context in governed payload",
        "offenders": [],
    }


def validate_picker_source_selection_support(
    source_text: str,
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Validate OS picker metadata capture for the narrowed index source workflow."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    offenders: list[str] = []
    required_generated_markers = (
        'data-phase7-source-picker="local_folder"',
        'type="file"',
        "webkitdirectory",
        "multiple",
        "Choose Folder",
        "Folder selected. ",
        "Nothing has been submitted yet",
        'data-phase7-source-picker="local_file"',
        'accept=".out"',
        "Choose File",
        'data-phase7-picker-summary="local_folder"',
        'data-phase7-picker-summary="local_file"',
        'data-dashboard-state-key="selectedLocalFolderFileCount"',
        'data-dashboard-state-key="selectedLocalFolderOutFileCount"',
        'data-dashboard-state-key="selectedLocalFolderCandidateCount"',
        'data-dashboard-state-key="selectedLocalFolderAwrCandidateCount"',
        'data-dashboard-state-key="selectedLocalFolderRejectedCount"',
        'data-dashboard-state-key="selectedLocalFolderValidationStatus"',
        'data-dashboard-state-key="selectedLocalFolderSampleFiles"',
        'data-dashboard-state-key="selectedLocalFolderValidationMessages"',
        'data-dashboard-state-key="selectedLocalFileName"',
        'data-dashboard-state-key="selectedLocalFileSize"',
        'data-dashboard-state-key="selectedLocalFileType"',
        'data-dashboard-state-key="selectedLocalFileExtension"',
        'data-dashboard-state-key="selectedLocalFileValidationStatus"',
        'data-dashboard-state-key="awrSignatureValidation"',
        "AWR signature validation",
        "The current verified parser path supports .out AWR reports",
        "HTML AWR input is planned for a future parser/source adapter",
    )
    for marker in required_generated_markers:
        if marker not in index_text:
            offenders.append(f"generated index missing picker marker: {marker}")

    required_source_markers = (
        "handlePhase7SourcePickerChange",
        "data-phase7-source-picker",
        "sourceSelectionMethod = 'os_folder_picker'",
        "sourceSelectionMethod = 'os_file_picker'",
        "selectedLocalFolderFileCount",
        "selectedLocalFolderOutFileCount",
        "selectedLocalFolderCandidateCount",
        "selectedLocalFolderAwrCandidateCount",
        "selectedLocalFolderRejectedCount",
        "selectedLocalFolderValidationStatus",
        "selectedLocalFolderValidationMessages",
        "selectedLocalFolderSampleFiles",
        "selectedLocalRelativePaths",
        "selectedLocalTotalBytes",
        "selectedLocalFileName",
        "selectedLocalFileSize",
        "selectedLocalFileType",
        "selectedLocalFileExtension",
        "selectedLocalFileValidationStatus",
        "awrSignatureValidation",
        "isAwrCandidateFileName",
        "Ready to submit governed source handoff",
        "Nothing has been submitted yet",
        "governed request/audit record is created only after this submit action",
        "warning-backend-validation-pending",
        "browser_parsing_performed: false",
        "browser_file_upload_performed: false",
        "browser_object_storage_access_attempted: false",
        "em_extract_attempted: false",
    )
    for marker in required_source_markers:
        if marker not in source_text:
            offenders.append(f"dashboard source missing picker behavior marker: {marker}")

    forbidden_markers = (
        "FileReader",
        "readAsText",
        "readAsArrayBuffer",
        "readAsDataURL",
        "browser_parsing_performed: true",
        "browser_file_read_attempted: true",
        "browser_object_storage_access_attempted: true",
        "objectStorageClient",
        "oci-sdk",
    )
    combined = source_text + "\n" + index_text
    unsupported_support_markers = (
        'accept=".out,.txt',
        'accept=".out,.html',
        'accept=".out,.awr',
        'accept=".out,.txt,.html',
        'accept=".out,.txt,.html,.awr"',
        "Object.freeze(['out', 'txt'",
        "Object.freeze(['out', 'html'",
        "Object.freeze(['out', 'awr'",
        "Object.freeze(['out', 'txt', 'html'",
        "Object.freeze(['out', 'txt', 'html', 'awr'",
    )
    for marker in unsupported_support_markers:
        if marker in combined:
            offenders.append(
                "unsupported Phase 7 local input extension is shown as accepted: "
                f"{marker}"
            )
    for marker in forbidden_markers:
        if marker in combined:
            offenders.append(f"browser-side parsing/access marker is not allowed: {marker}")

    if offenders:
        return {
            "status": "failed",
            "reason": "OS picker source-selection support is incomplete: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "local folder and local file OS pickers capture metadata, update source state, and preserve browser no-parse/no-access boundaries",
        "offenders": [],
    }


def validate_pipeline_source_summary(
    source_text: str,
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Require compact selected-source text in the deterministic pipeline."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    offenders: list[str] = []
    pipeline_start = index_text.find('data-phase7-current-runtime-pipeline="true"')
    source_context_start = index_text.find('data-phase7-current-source-context="true"')
    pipeline_region = (
        index_text[pipeline_start:source_context_start]
        if pipeline_start >= 0 and source_context_start > pipeline_start
        else ""
    )

    required_source_markers = (
        "function sourcePathBasename",
        "function sourcePipelineActiveSummary",
        "function sourcePipelineNodeSummary",
        "pipeline_active: 'Active source: ' + pipelineActive",
        "pipeline_node_source: pipelineNode",
        "Object Storage source selected. Object:",
        "Object Storage: ' + bucket + ' / ... / ' + objectBase",
        "Existing run selected. Run:",
        "Local file source selected. File:",
        "Local staged AWR source. Path:",
        "element.setAttribute('title', sourceMetadataSummary(safeState))",
    )
    for marker in required_source_markers:
        if marker not in source_text:
            offenders.append(f"dashboard source missing compact pipeline marker: {marker}")

    required_generated_markers = (
        'data-phase7-source-summary-card="pipeline_node_source"',
        "Local staged AWR source. Path: data/input.",
        "Source selection changes the governed handoff context only.",
        "Deterministic parsing, scoring, decision, and recommendation remain",
        ".pipeline-node small",
        ".pipeline-mode-badge .meta",
        ".phase7cm-source-summary-card p",
        "overflow-wrap: anywhere",
        "word-break: break-word",
        "min-width: 0",
    )
    combined = source_text + "\n" + index_text
    for marker in required_generated_markers:
        if marker not in combined:
            offenders.append(f"generated/source dashboard missing compact pipeline marker: {marker}")

    if pipeline_region:
        full_object_path = "awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out"
        if full_object_path in pipeline_region:
            offenders.append("pipeline region renders full Object Storage object path instead of compact basename")
        if "Current source context:" in pipeline_region:
            offenders.append("pipeline ingestion node still uses generic current-source-context wording")
    else:
        offenders.append("generated index missing visible deterministic runtime pipeline region")

    if "pipeline_node_source: 'Current source context: ' + activeLocation" in source_text:
        offenders.append("pipeline ingestion node is still fed by full active source location")

    if offenders:
        return {
            "status": "failed",
            "reason": "deterministic pipeline source summary is not compact or overflow-safe: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "deterministic pipeline uses compact selected-source summaries and preserves full details in Source Configuration",
        "offenders": [],
    }


def validate_governed_memory_production_wording(
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Reject phase-number project wording in the Governed Memory product block."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    offenders: list[str] = []
    block_start = index_text.find('class="card secondary memory-explainer-card"')
    block_end = index_text.find("</section>", block_start)
    memory_block = (
        index_text[block_start:block_end]
        if block_start >= 0 and block_end > block_start
        else ""
    )
    if not memory_block:
        offenders.append("Governed Memory & Semantic Recall block is missing")
    required_markers = (
        "Governed Memory",
        "Governed Memory &amp; Semantic Recall",
        "Governed memory preserves analysis runs, recommendations, actions",
        "Semantic recall provides optional reviewer-assist context",
        "Run Tracking",
        "Recommendation Tracking",
        "Action Tracking",
        "Outcome Tracking",
        "Feedback Capture",
        "Parser Unknowns",
        "Runtime influence remains gated, auditable, and denied by default",
    )
    for marker in required_markers:
        if marker not in memory_block:
            offenders.append(f"Governed Memory block missing production marker: {marker}")
    forbidden_markers = (
        "Phase 6",
        "Phase 7",
        "future Phase 7",
        "Phase 7 research",
        "Phase 7 builds on this",
        "Phase 4I output",
    )
    for marker in forbidden_markers:
        if marker in memory_block:
            offenders.append(f"Governed Memory block contains phase reference: {marker}")
    if offenders:
        return {
            "status": "failed",
            "reason": "Governed Memory block is not production-worded: "
            + ", ".join(offenders[:10]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "Governed Memory block uses production wording without phase-number references",
        "offenders": [],
    }


def extract_dashboard_state_keys(source_text: str) -> set[str]:
    match = re.search(
        r"DASHBOARD_INTERACTIVITY_STATE_KEYS\s*=\s*\((.*?)\)",
        source_text,
        flags=re.DOTALL,
    )
    if not match:
        return set()
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def validate_no_current_workflow_preview_text(
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Reject preview/no-write/no-API language when it is not framed as legacy."""

    offenders: list[str] = []
    phrases = (
        "Selected State Summary",
        "Future Input Configuration",
        "Future examples:",
        "No API calls",
        "URL hash/localStorage",
        "No backend write; No governed write path",
        "No action record persisted",
        "No outcome record persisted",
        "No feedback created",
        "write_performed=false",
        "outcome_created=false",
        "feedback_created=false",
    )
    for label, raw_text in generated_texts.items():
        text = visible_text(raw_text)
        for phrase in phrases:
            search_start = 0
            while True:
                match_at = text.find(phrase, search_start)
                if match_at < 0:
                    break
                context = text[max(0, match_at - 900): match_at + len(phrase) + 900].lower()
                if not any(
                    marker in context
                    for marker in (
                        "legacy",
                        "historical",
                        "read-only",
                        "technical detail",
                        "not the current operational path",
                    )
                ):
                    line = text.count("\n", 0, match_at) + 1
                    offenders.append(f"{label}:{line}:{phrase}")
                search_start = match_at + len(phrase)
    if offenders:
        return {
            "status": "failed",
            "reason": "current workflow still presents preview/no-write/no-API text without legacy framing: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "preview/no-write/no-API language is framed as legacy/read-only or technical detail",
        "offenders": [],
    }


def visible_text(html: str) -> str:
    without_scripts = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    without_comments = re.sub(r"<!--.*?-->", "", without_scripts, flags=re.DOTALL)
    return without_comments


def load_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def extract_action_controls(text: str) -> list[dict[str, str]]:
    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    controls: list[dict[str, str]] = []
    for match in re.finditer(r"data-phase7-action-control=\"true\"", text):
        start = text.rfind("<", 0, match.start())
        end = text.find(">", match.end())
        if start < 0 or end < 0:
            start = max(0, match.start() - 300)
            end = min(len(text), match.end() + 900)
        else:
            end += 1
        snippet = text[start:end]
        attrs = {
            key: value
            for key, value in re.findall(r"data-([a-z0-9-]+)=\"([^\"]*)\"", snippet)
        }
        if attrs:
            controls.append(attrs)
    return controls


def action_control_text(text: str) -> str:
    snippets = []
    for match in re.finditer(r"data-phase7-action-control=\"true\"", text):
        snippets.append(text[max(0, match.start() - 900): match.end() + 1800])
    return "\n".join(snippets)


def check_result(name: str, passed: bool, reason: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": "passed" if passed else "failed",
        "reason": reason,
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def print_human_summary(summary: dict[str, Any]) -> None:
    if summary["dashboard_runtime_interaction_ready"]:
        print("Phase 7CM index/source-selection runtime validation passed.")
    else:
        print("Phase 7CM index/source-selection runtime validation failed.")
    print(f"blocker_id={summary['blocker_id']}")
    print(f"blocker_active={str(summary['blocker_active']).lower()}")
    print(f"dashboard_runtime_interaction_ready={str(summary['dashboard_runtime_interaction_ready']).lower()}")
    print(f"scope={summary['scope']}")
    print("Screens:")
    for screen_id, result in summary["screens"].items():
        print(f"- {screen_id}: {result['status']} ({result['reason']})")
    if summary["failures"]:
        print("Failures:")
        for failure in summary["failures"]:
            print(f"- {failure}")


if __name__ == "__main__":
    raise SystemExit(main())
