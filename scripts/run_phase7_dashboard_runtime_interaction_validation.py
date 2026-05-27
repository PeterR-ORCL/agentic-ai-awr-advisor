#!/usr/bin/env python3
"""Validate Phase 7CM dashboard runtime interaction wiring."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
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
    "screen_1": ("screen1_source_intake_execute",),
    "screen_3": ("screen3_active_reanalysis",),
}

GENERATED_DASHBOARD_FILES: tuple[str, ...] = (
    "awr_dashboard/index.html",
    "awr_dashboard/screen_1_ingestion.html",
    "awr_dashboard/screen_2_control.html",
    "awr_dashboard/screen_3_analysis.html",
    "awr_dashboard/screen_4_historical_review.html",
    "awr_dashboard/screen_5_recommendation_action.html",
    "awr_dashboard/screen_6_fleet_overview.html",
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
    source_text = read_dashboard_source_text()
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


def read_dashboard_source_text() -> str:
    source = read_text(ROOT / "src" / "reporting" / "html_dashboard.py")
    styles_path = ROOT / "src" / "reporting" / "dashboard" / "styles.py"
    if styles_path.is_file():
        source = source + "\n" + read_text(styles_path)
    return source


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
    generated_screen3_result = validate_generated_screen3_control_center(generated_texts)
    screens3_6_copy_result = validate_screens3_6_runtime_explanation_copy(
        generated_texts
    )
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
    generated_default_gating_result = validate_generated_default_evidence_gating(
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
        and service_smoke.get("screen3_runtime_request_processed") is True
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
            "source_screen1_source_intake_execution_action_control",
            all(result["status"] == "passed" for result in source_screen_results.values()),
            "source dashboard contains the required governed Screen 1 source-intake execution action control",
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
            "generated_dashboard_action_controls",
            generated_has_7cm
            and all(result["status"] == "passed" for result in generated_screen_results.values()),
            "generated dashboard contains required governed Screen 1 source-intake and Screen 3 action controls",
        ),
        check_result(
            "generated_screen3_control_center_ready",
            generated_screen3_result["status"] == "passed",
            generated_screen3_result["reason"],
        ),
        check_result(
            "screens3_6_runtime_explanation_copy_ready",
            screens3_6_copy_result["status"] == "passed",
            screens3_6_copy_result["reason"],
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
            "generated_artifact_not_active_evidence_by_default",
            generated_default_gating_result["status"] == "passed",
            generated_default_gating_result["reason"],
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
    if screens3_6_copy_result["status"] != "passed":
        failures.append(screens3_6_copy_result["reason"])
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
    if generated_default_gating_result["status"] != "passed":
        failures.append(generated_default_gating_result["reason"])
    source_ready = not failures
    screen1_actions = source_screen_results["screen_1"]["present_action_types"]
    screen1_source_ready = source_screen_results["screen_1"]["status"] == "passed"
    return {
        "phase": "Phase 7",
        "subphase": "7CM",
        "validation_name": VALIDATION_NAME,
        "scope": "index_source_selection_runtime_workflow",
        "scope_note": (
            "7CM certifies only the index/source-selection runtime workflow. "
            "Screen 2-6 runtime workflows remain pending for 7CO-7CS and "
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
        "generated_screen3_control_center_ready": generated_screen3_result["status"] == "passed",
        "blocker_id": BLOCKER_ID,
        "blocker_active": not source_ready,
        "selection_blocker_id": SELECTION_BLOCKER_ID,
        "selection_blocker_active": False if source_ready else True,
        "screens": source_screen_results,
        "generated_dashboard": {
            "validated": generated_has_7cm,
            "files": sorted(generated_texts),
            "screens": generated_screen_results,
            "screen3_control_center": generated_screen3_result,
            "screens3_6_runtime_explanation_copy": screens3_6_copy_result,
            "default_evidence_gating": generated_default_gating_result,
        },
        "service_bridge": service_smoke,
        "deferred_screen_workflow_blocker_id": SELECTION_BLOCKER_ID,
        "deferred_screens": [
            "7CO Screen 2 diagnostic review runtime workflow",
            "7CP Screen 3 active re-analysis runtime workflow",
            "7CQ Screen 4 historical review runtime workflow",
            "7CR Screen 5 recommendation/action/outcome runtime workflow",
            "7CS Screen 6 governance runtime workflow",
            "7CT cross-screen runtime workflow integration",
        ],
        "remaining_deferred_screens": [
            "7CO Screen 2 diagnostic review runtime workflow",
            "7CP Screen 3 active re-analysis runtime workflow",
            "7CQ Screen 4 historical review runtime workflow",
            "7CR Screen 5 recommendation/action/outcome runtime workflow",
            "7CS Screen 6 governance runtime workflow",
            "7CT cross-screen runtime workflow integration",
        ],
        "screen1_source_intake_status": {
            "ready": screen1_source_ready,
            "present_action_types": screen1_actions,
            "required_action_types": list(REQUIRED_SCREEN_ACTIONS["screen_1"]),
            "screen1_source_intake_execute": "screen1_source_intake_execute" in screen1_actions,
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
        screen_present = (
            f'screen_id="{screen}"' in source_text
            or f"screen_id='{screen}'" in source_text
            or f'"screen_id": "{screen}"' in source_text
            or f"'screen_id': '{screen}'" in source_text
        )
        present = [
            action
            for action in required
            if f'"action_type": "{action}"' in source_text
            or f"'action_type': '{action}'" in source_text
        ]
        missing = [action for action in required if action not in present]
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
        screen3_options_endpoint_path = service_module.SCREEN3_OPTIONS_ENDPOINT_PATH
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
        screen3_payload = screen3_runtime_service_smoke_payload()
        screen3_response, screen3_status_code = invoke_service_handler(
            handler,
            endpoint_path,
            json.dumps(screen3_payload).encode("utf-8"),
            queue_dir,
        )
        screen3_audit_reference = screen3_response.get("audit_reference")
        screen3_runtime_request_processed = (
            screen3_status_code == 202
            and screen3_response.get("status") in {"blocked", "completed", "accepted"}
            and bool(screen3_response.get("queued"))
            and bool(screen3_audit_reference)
            and Path(screen3_audit_reference).is_file()
            and screen3_response.get("source_summary", {}).get("current_run_truth_mutated") is False
            and screen3_response.get("source_summary", {}).get("phase8_started") is False
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
        screen3_options_response, screen3_options_status_code = invoke_service_handler(
            handler,
            screen3_options_endpoint_path,
            json.dumps(screen3_runtime_options_smoke_payload()).encode("utf-8"),
            queue_dir,
            connection_factory=fake_existing_run_connection_factory,
        )
        screen3_runtime_options_tested = (
            screen3_options_status_code == 202
            and screen3_options_response.get("status") == "accepted"
            and screen3_options_response.get("runtime_options_loaded") is True
            and screen3_options_response.get("option_count", 0) >= 1
            and screen3_options_response.get("service_status") == "available"
            and screen3_options_response.get("db_persistence_status") == "available"
            and screen3_options_response.get("options", {}).get("runs")
            and screen3_options_response.get("options", {}).get("databases")
            and screen3_options_response.get("options", {}).get("intervals")
            and screen3_options_response.get("options", {}).get("target_scope_options")
            and screen3_options_response.get("target_resolution", {}).get("target_model")
            == "source_type + scope_type + scope_value + time_window + resolution_state + readiness_state"
            and "both_targets_comparable" in screen3_options_response.get("comparison_readiness", {})
            and "AWR_RUN_HISTORY" in str(screen3_options_response.get("metadata", {}).get("source") or "")
            and screen3_options_response.get("metadata", {}).get("runtime_options_source_tables")
            and screen3_options_response.get("runtime_options_source_tables")
            and "runtime_options_source_note" in screen3_options_response.get("metadata", {})
            and Path(screen3_options_response.get("audit_reference") or "").is_file()
            and screen3_options_response.get("browser_db_query_performed") is False
            and screen3_options_response.get("current_run_truth_mutated") is False
        )
        health_handler = object.__new__(handler)
        health_handler.server = type(
            "Phase7SmokeHealthServer",
            (),
            {"server_address": ("127.0.0.1", 8765)},
        )()
        health_payload = handler._health_payload(health_handler)
        health_exposes_screen3_options_route = (
            screen3_options_endpoint_path
            in set(health_payload.get("supported_endpoints") or [])
        )
        health_exposes_action_status_route = (
            "/phase7/dashboard/actions/status"
            in set(health_payload.get("supported_endpoints") or [])
        )
        health_supported_action_types = set(health_payload.get("supported_action_types") or [])
        health_supported_screen_actions = health_payload.get("supported_screen_action_types") or {}
        health_exposes_screen1_source_intake_action = (
            "screen1_source_intake_execute" in health_supported_action_types
            and "screen1_source_intake_execute"
            in set(health_supported_screen_actions.get("screen_1") or [])
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
            and screen3_runtime_options_tested
            and health_exposes_screen3_options_route
            and health_exposes_action_status_route
            and health_exposes_screen1_source_intake_action
            and object_storage_validation_tested
            and invalid_object_storage_rejected
            and invalid_source_requests_rejected
            and screen3_runtime_request_processed
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
            "screen3_runtime_options_tested": screen3_runtime_options_tested,
            "health_exposes_screen3_options_route": health_exposes_screen3_options_route,
            "health_exposes_action_status_route": health_exposes_action_status_route,
            "health_exposes_screen1_source_intake_action": health_exposes_screen1_source_intake_action,
            "health_supported_endpoints": health_payload.get("supported_endpoints"),
            "health_supported_action_types": health_payload.get("supported_action_types"),
            "health_supported_screen_action_types": health_payload.get("supported_screen_action_types"),
            "screen3_runtime_options_status_code": screen3_options_status_code,
            "screen3_runtime_options_response": screen3_options_response,
            "object_storage_validation_tested": object_storage_validation_tested,
            "object_storage_validation_status_code": object_storage_status_code,
            "object_storage_validation_response": object_storage_response,
            "screen3_runtime_request_processed": screen3_runtime_request_processed,
            "screen3_runtime_status_code": screen3_status_code,
            "screen3_runtime_response": screen3_response,
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
            "screen3_runtime_request_processed": False,
            "screen3_runtime_options_tested": False,
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
                    "next_step": "screen_2_control.html",
                    **source_metadata,
                },
            }
        )
    return payloads


def service_smoke_payloads() -> list[dict[str, Any]]:
    """Return reusable future screen payloads for 7CO-7CS contract tests."""

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
            "execution_mode": "local_backend_execution",
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


def screen3_runtime_service_smoke_payload() -> dict[str, Any]:
    return {
        "screen_id": "screen_3",
        "action_type": "screen3_active_reanalysis",
        "workflow_type": "screen3_runtime_control_center",
        "actor_id": "ACTOR-7CP-VALIDATION",
        "target_type": "backend_execution_request",
        "target_id": "SCREEN3-VALIDATION-ACTIVE-REANALYSIS",
        "execution_mode": "local_backend_execution",
        "runtime_influence_granted": False,
        "phase4i_mutation_allowed": False,
        "phase8_behavior": False,
        "direct_truth_mutation_allowed": False,
        "run_analysis_coupling": False,
        "payload": {
            "validation": "phase7cp_screen3_runtime_control_smoke",
            "requested_screen3_action": "analyze_selection",
            "target_screen": "screen_3",
            "selectedSourceMode": "local_staged",
            "sourceSelectionMethod": "backend_path",
            "selectedSourcePath": "data/input",
            "reviewer_actor_id": "ACTOR-7CP-VALIDATION",
            "current_run_truth_mutated": False,
            "deterministic_truth_changed": False,
            "parser_mutated": False,
            "learning_candidate_created": False,
            "materialization_changed": False,
            "runtime_eligibility_changed": False,
            "phase8_started": False,
            "llm_changed_status": False,
            "llm_changed_validation": False,
            "llm_changed_execution": False,
            "llm_changed_truth": False,
            "browser_file_read_attempted": False,
            "browser_object_storage_access_attempted": False,
            "browser_db_query_attempted": False,
            "run_analysis_coupling": False,
            "phase8_behavior": False,
            "em_extract_attempted": False,
        },
    }


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


def screen3_runtime_options_smoke_payload() -> dict[str, Any]:
    return {
        "screen_id": "screen_3",
        "action_type": "screen3_load_runtime_options",
        "workflow_type": "screen3_runtime_options_lookup",
        "target_screen": "screen3",
        "governance_mode": "governed_request",
        "limit": 10,
        "browser_db_query_attempted": False,
        "browser_object_storage_access_attempted": False,
        "direct_object_storage_execution_attempted": False,
        "direct_truth_mutation_allowed": False,
        "phase4i_mutation_allowed": False,
        "phase8_behavior": False,
        "phase8_started": False,
        "run_analysis_coupling": False,
        "current_run_truth_mutated": False,
        "deterministic_truth_changed": False,
        "parser_mutated": False,
        "learning_candidate_created": False,
        "materialization_changed": False,
        "runtime_eligibility_changed": False,
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
    RUN_HISTORY_DESCRIPTION = (
        ("RUN_HISTORY_ID",),
        ("ANALYSIS_RUN_ID",),
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
    RUN_HISTORY_ROWS = [
        (
            9001,
            "analysis-9001",
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
    REPORT_DESCRIPTION = (
        ("AWR_ID",),
        ("SOURCE_FILE_NAME",),
        ("DB_NAME",),
        ("DBID",),
        ("INSTANCE_NAME",),
        ("HOST_NAME",),
        ("SNAP_TIME_BEGIN",),
        ("SNAP_TIME_END",),
        ("PARSE_STATUS",),
        ("CREATED_AT",),
        ("SNAP_ID_BEGIN",),
        ("SNAP_ID_END",),
        ("APPLICATION_NAME",),
        ("SOURCE_SYSTEM_CODE",),
        ("INGEST_RUN_ID",),
    )
    REPORT_ROWS = [
        (
            108,
            "sprtrn_awr_108.out",
            "SPRTRN",
            "8101005004",
            "sprtrn1",
            "sprtrn-db01",
            "2026-04-02T10:00:00",
            "2026-04-02T11:00:00",
            "parsed",
            "2026-04-02T11:05:00",
            1201,
            1202,
            "OrderService",
            "sprtrn-db01",
            701,
        ),
        (
            107,
            "sprtrn_awr_107.out",
            "SPRTRN",
            "8101005004",
            "sprtrn1",
            "sprtrn-db01",
            "2026-04-02T09:00:00",
            "2026-04-02T10:00:00",
            "parsed",
            "2026-04-02T10:05:00",
            1199,
            1200,
            "OrderService",
            "sprtrn-db01",
            701,
        ),
        (
            106,
            "hrdb_awr_106.out",
            "HRDB",
            "9200200200",
            "hrdb1",
            "hrdb01",
            "2026-04-01T08:00:00",
            "2026-04-01T09:00:00",
            "parsed",
            "2026-04-01T09:05:00",
            501,
            502,
            None,
            "hrdb01",
            702,
        ),
    ]
    TABLE_COUNTS = {
        "AWR_RUN_HISTORY": len(RUN_HISTORY_ROWS),
        "AWR_REPORT": len(REPORT_ROWS),
        "AWR_SNAPSHOT": 0,
        "AWR_INGEST_RUN": 2,
        "AWR_SOURCE_SYSTEM": 3,
        "AWR_RECOMMENDATION_HISTORY": 1,
        "AWR_ACTION_HISTORY": 1,
        "AWR_OUTCOME_HISTORY": 1,
        "AWR_METRIC_FACT": 12,
        "AWR_WAIT_EVENT_FACT": 4,
        "AWR_TOP_SQL_FACT": 3,
        "AWR_FEATURE_VECTOR": 3,
    }
    TABLE_COLUMNS = {
        "AWR_RUN_HISTORY": [item[0] for item in RUN_HISTORY_DESCRIPTION],
        "AWR_REPORT": [
            "AWR_ID",
            "SOURCE_SYSTEM_ID",
            "SOURCE_FILE_NAME",
            "DB_NAME",
            "DBID",
            "INSTANCE_NAME",
            "HOST_NAME",
            "SNAP_ID_BEGIN",
            "SNAP_ID_END",
            "SNAP_TIME_BEGIN",
            "SNAP_TIME_END",
        ],
        "AWR_SNAPSHOT": [],
        "AWR_INGEST_RUN": ["INGEST_RUN_ID", "SOURCE_SYSTEM_ID", "STATUS", "CREATED_AT"],
        "AWR_SOURCE_SYSTEM": [
            "SOURCE_SYSTEM_ID",
            "APPLICATION_NAME",
            "SOURCE_SYSTEM_CODE",
            "PRIMARY_HOST_NAME",
        ],
        "AWR_RECOMMENDATION_HISTORY": [
            "RECOMMENDATION_HISTORY_ID",
            "RUN_HISTORY_ID",
            "RECOMMENDATION_ID",
            "CREATED_AT",
        ],
        "AWR_ACTION_HISTORY": ["ACTION_HISTORY_ID", "RUN_HISTORY_ID", "ACTION_ID", "CREATED_AT"],
        "AWR_OUTCOME_HISTORY": ["OUTCOME_HISTORY_ID", "RUN_HISTORY_ID", "OUTCOME_ID", "CREATED_AT"],
        "AWR_METRIC_FACT": [
            "AWR_ID",
            "SOURCE_SYSTEM_ID",
            "SNAP_TIME_BEGIN",
            "SNAP_TIME_END",
            "METRIC_DOMAIN",
            "METRIC_NAME",
            "METRIC_VALUE_NUM",
        ],
        "AWR_WAIT_EVENT_FACT": [
            "AWR_ID",
            "SOURCE_SYSTEM_ID",
            "SNAP_TIME_BEGIN",
            "SNAP_TIME_END",
            "EVENT_NAME",
            "WAIT_CLASS",
        ],
        "AWR_TOP_SQL_FACT": [
            "AWR_ID",
            "SOURCE_SYSTEM_ID",
            "SNAP_TIME_BEGIN",
            "SNAP_TIME_END",
            "SQL_ID",
            "ELAPSED_TIME_SEC",
        ],
        "AWR_FEATURE_VECTOR": [
            "AWR_ID",
            "SOURCE_SYSTEM_ID",
            "OBSERVED_AT",
            "FEATURE_SET_NAME",
            "VECTOR_STATUS",
        ],
    }

    def __enter__(self) -> "FakeExistingRunCursor":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def execute(self, sql: str, params: dict[str, Any]) -> None:
        normalized_sql = " ".join(str(sql or "").upper().split())
        limit = int(params.get("limit", 100)) if isinstance(params, dict) else 100
        self.description = self.RUN_HISTORY_DESCRIPTION
        self._rows: list[tuple[Any, ...]] = []
        if "USER_TAB_COLUMNS" in normalized_sql:
            table_name = str(params.get("table_name") or "").upper()
            self.description = (("COLUMN_NAME",),)
            self._rows = [(column,) for column in self.TABLE_COLUMNS.get(table_name, [])]
            return None
        if "COUNT(*)" in normalized_sql and "APPLICATION_NAME IS NOT NULL" in normalized_sql:
            self.description = (("COUNT",),)
            self._rows = [(2,)]
            return None
        count_match = re.search(r"COUNT\(\*\)\s+FROM\s+([A-Z0-9_]+)", normalized_sql)
        if count_match:
            table_name = count_match.group(1)
            self.description = (("COUNT",),)
            self._rows = [(self.TABLE_COUNTS.get(table_name, 0),)]
            return None
        if "FROM AWR_REPORT" in normalized_sql:
            self.description = self.REPORT_DESCRIPTION
            self._rows = self.REPORT_ROWS[:limit]
            return None
        if "FROM AWR_RUN_HISTORY" in normalized_sql:
            self.description = self.RUN_HISTORY_DESCRIPTION
            self._rows = self.RUN_HISTORY_ROWS[:limit]
            return None
        self._rows = self.RUN_HISTORY_ROWS[:limit]
        return None

    def fetchone(self) -> tuple[Any, ...] | None:
        rows = getattr(self, "_rows", [])
        return rows[0] if rows else None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(getattr(self, "_rows", self.RUN_HISTORY_ROWS))


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
            "phase7_screen3_options_connection_factory": staticmethod(connection_factory)
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
    """Ensure Index product copy does not contradict the current source workflow."""

    del source_text
    index_text = generated_texts.get("awr_dashboard/index.html", "")
    primary_pos = index_text.find('id="phase7cr-platform-entry-panel"')
    legacy_markers = (
        'id="index-source-mode-entry-panel"',
        'id="index-source-status-panel"',
        'id="index-object-storage-config-panel"',
        'id="index-screen3-handoff-panel"',
        "Legacy 7BQ",
        "Legacy 7BR",
        "Legacy 7BS",
        "Legacy 7BT",
    )
    present_legacy = [marker for marker in legacy_markers if marker in index_text]
    primary_region = visible_text(index_text).lower()
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
    if present_legacy:
        return {
            "status": "failed",
            "reason": "legacy phase-boundary panels remain product-facing: "
            + ", ".join(present_legacy),
        }
    if primary_pos < 0:
        return {
            "status": "failed",
            "reason": "primary Index platform entry panel is missing from generated index.html",
        }
    if present_contradictions:
        return {
            "status": "failed",
            "reason": "contradictory source-selection workflow text remains: "
            + "; ".join(present_contradictions),
        }
    return {
        "status": "passed",
        "reason": "Index product copy uses the current two-path source workflow without legacy contradictions",
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
            if "legacy" not in context and "read-only" not in context and "preview only" not in context:
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
    """Require Index entry choices and Screen 1 source workflow ownership."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    screen1_text = generated_texts.get("awr_dashboard/screen_1_ingestion.html", "")
    index_visible = visible_text(index_text)
    screen1_visible = visible_text(screen1_text)
    offenders: list[str] = []
    if not index_text:
        return {
            "status": "failed",
            "reason": "index source selection validation could not find generated awr_dashboard/index.html",
            "offenders": ["missing index.html"],
        }
    if not screen1_text:
        return {
            "status": "failed",
            "reason": "index source selection validation could not find generated awr_dashboard/screen_1_ingestion.html",
            "offenders": ["missing screen_1_ingestion.html"],
        }
    required_index_markers = (
        'id="phase7cr-platform-entry-panel"',
        'data-phase7-index-source-selection="true"',
        'data-phase7-primary-entry-paths="true"',
        'data-phase7-entry-path="new_source"',
        'data-phase7-entry-path="existing_platform_evidence"',
        'data-phase7-entry-source-modes="local_staged local_file object_storage"',
        'data-phase7-entry-source-modes="existing_run"',
        'data-phase7-current-runtime-pipeline="true"',
        'data-phase7-system-flow-dynamic="true"',
        'screen_1_ingestion.html',
        'screen_2_control.html',
        "Platform Entry / Source Intake",
        "What do you want to work with?",
        "Load / Ingest New Source",
        "Use Existing Platform Evidence",
        "Screen 1 - Ingestion / Parser / Source Governance",
        "Screen 2 - Runtime Scope &amp; Analysis Control",
        "Deterministic Analysis Pipeline",
        "Deterministic Runtime Architecture",
        "Deterministic Truth vs AI Explanation",
        "Governed Memory &amp; Semantic Recall",
        "LLM / Explanation Provider",
        "6-Screen Product Model",
    )
    normalized_index_text = re.sub(r"\s+", " ", index_text)
    missing_index = [
        marker
        for marker in required_index_markers
        if marker not in index_text and marker not in normalized_index_text
    ]
    offenders.extend(f"index missing marker: {marker}" for marker in missing_index)

    forbidden_index_markers = (
        "Selection Workflow",
        "Detailed Source Mode Configuration",
        "Source Mode Configuration",
        "Selected Source Summary",
        "Validation / Handoff Status",
        "Validation / Execution Status",
        "Validate Object Storage Source",
        "Request ID",
        "Audit record",
        'data-phase7-current-source-card="true"',
        'data-dashboard-select-key="selectedSourceMode"',
        'data-required-selection-key="selectedSourceMode"',
        'data-phase7-action-control="true"',
        'data-phase7-action-result-panel="true"',
        'data-phase7-source-configuration="true"',
        'data-phase7-object-storage-validation-control="true"',
        'data-dashboard-select-id="local_staged"',
        'data-dashboard-select-id="local_file"',
        'data-dashboard-select-id="object_storage"',
        'data-dashboard-select-id="existing_run"',
    )
    offenders.extend(
        f"index exposes Screen 1 workflow marker: {marker}"
        for marker in forbidden_index_markers
        if marker in index_visible
    )

    required_screen1_markers = (
        'id="phase7cm-source-intake-panel"',
        'data-phase7-current-source-card="true"',
        'data-dashboard-select-key="selectedSourceMode"',
        'data-required-selection-key="selectedSourceMode"',
        'data-phase7-action-result-panel="true"',
        'data-phase7-request-id-target="true"',
        'data-phase7-audit-status-area="true"',
        'data-phase7-source-configuration="true"',
        'data-dashboard-state-key="selectedSourcePath"',
        'data-dashboard-state-key="objectStorageNamespace"',
        'data-dashboard-state-key="objectStorageBucket"',
        'data-dashboard-state-key="objectStorageObjectName"',
        'data-dashboard-state-key="objectStorageRegion"',
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
        'value="data/input"',
        "New Source Intake / Validation Workflow",
        "Submit a governed backend source intake request",
        "Your browser may label this as Upload",
        "files available for governed validation",
        "governed submit not yet performed",
        "Selected Source Summary",
        "Active Source Selection",
        "Validation / Execution Status",
        "Active Source",
        "Source Metadata",
        "Validation Status",
        "Execution Target",
        "Action State",
        'data-phase7-runtime-source-validation="true"',
        'data-phase7-source-validation-card="local_folder"',
        'data-phase7-source-validation-card="local_file"',
        'data-phase7-source-validation-card="object_storage"',
        'data-phase7-service-availability-status="true"',
        'data-phase7-submit-result-reference="true"',
        "Validate Object Storage Source",
        "Dashboard workflow service is not running. Start the service to use interactive features.",
        "browser does not read local files",
        "never browser-side bucket reads",
        "governed metadata validation only",
        "full load, parse, and",
        "analyze remain backend-gated",
        "backend validation pending",
        "Folder picker metadata.",
        "File picker metadata.",
        "Object Storage metadata. Namespace:",
    )
    normalized_screen1_text = re.sub(r"\s+", " ", screen1_text)
    missing_screen1 = [
        marker
        for marker in required_screen1_markers
        if marker not in screen1_text and marker not in normalized_screen1_text
    ]
    offenders.extend(f"screen1 missing marker: {marker}" for marker in missing_screen1)

    source_modes = ("local_staged", "local_file", "object_storage")
    for source_mode in source_modes:
        if f'data-dashboard-select-id="{source_mode}"' not in screen1_text:
            offenders.append(f"screen1 missing selectable new-source card: {source_mode}")
    if 'data-dashboard-select-id="existing_run"' in screen1_text:
        offenders.append("screen1 exposes existing_run as a new-source selectable card")
    for marker in (
        "Load Existing Runs",
        'data-phase7-existing-run-lookup-control="true"',
        'data-phase7-existing-run-options="true"',
        'data-phase7-source-validation-card="existing_run"',
    ):
        if marker in screen1_visible:
            offenders.append(f"screen1 duplicates Screen 2 existing-evidence lookup marker: {marker}")

    primary_pos = index_text.find('id="phase7cr-platform-entry-panel"')
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
        offenders.append("primary Index platform entry panel missing")
    if legacy_positions:
        offenders.append("legacy source preview panel remains rendered on product Index")

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
        offenders.append("Index still exposes current-source configuration details")
    if "No service-returned runs available" in index_text:
        offenders.append("Index still exposes existing run lookup state")
    if "Default source: data/input" in index_text:
        offenders.append("Index still presents data/input as active default source")
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
    if "Current Mode: Local" in index_text:
        offenders.append("default pipeline reference still claims active Current Mode: Local")
    if "Current mode: local AWR staging" in index_text:
        offenders.append("default pipeline reference still claims active local AWR mode")
    if "System Flow" in primary_region and "Current Mode: Local" in primary_region:
        offenders.append("system flow presents local mode as active source state")
    for dynamic_marker in (
        "if (mode === 'local_staged')",
        "if (mode === 'local_file')",
        "if (mode === 'object_storage')",
    ):
        if dynamic_marker not in screen1_text:
            offenders.append(f"active source configuration missing dynamic branch: {dynamic_marker}")
    if "Advanced Debug State / Browser Selection State" in visible_text(index_text):
        offenders.append("Index still renders raw browser debug state")
    if "Submit Existing Run Source Handoff" in screen1_visible:
        offenders.append("Screen 1 exposes Existing Run source-specific submit label")
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
        if marker.lower() in (index_text + "\n" + screen1_text).lower():
            offenders.append(f"source workflow exposes browser-side source access marker: {marker}")

    if offenders:
        return {
            "status": "failed",
            "reason": "Index/Screen 1 source ownership boundary is not coherent: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "Index shows two entry paths and platform context while Screen 1 owns new-source validation and handoff workflow",
        "offenders": [],
    }


def validate_generated_screen3_control_center(
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Require the runtime-control file to expose the 7CQ visible Screen 2 workflow."""

    screen3_text = generated_texts.get("awr_dashboard/screen_2_control.html", "")
    if not screen3_text:
        return {
            "status": "failed",
            "reason": "generated runtime-control validation could not find awr_dashboard/screen_2_control.html",
            "offenders": ["missing screen_2_control.html"],
        }

    normalized_screen3_text = re.sub(r"\s+", " ", screen3_text)
    required_markers = (
        "Screen 2 - Runtime Scope & Analysis Control",
        "Runtime Evidence Path",
        "Evidence path status",
        "completed artifact state from Screen 1",
        "DB-backed runtime options to select scope, interval, and comparison targets",
        "Work Area 1",
        "Select Runtime Scope",
        "Work Area 2",
        "Resolve Comparison Targets",
        "Target A and Target B identify selected candidate sides for later comparison review",
        "Assignment records selection context only",
        "Work Area 3",
        "Submit Governed Action and Review Result",
        "Load Runtime Options",
        "Runtime Scope Filters",
        "Filtered AWR / Run / Report Results",
        "Selected AWR / Report Row",
        "Snapshot / Interval Selection",
        "Selected Runtime Scope / Assignment Summary",
        "Apply selection to",
        "Runtime Scope",
        "Review Mode",
        "Governed Actions",
        "Request / Result Receipt",
        "Request receipt is not deterministic analysis truth unless a governed deterministic service returns a real output artifact reference",
        "Request ID, transaction ID, audit reference, persistence, and output fields are displayed from the service response only",
        "A governed request/audit record may be created only when the backend returns that state",
        "Backend status is service-returned only. Missing gates mean request receipt, not analysis execution or comparison output",
        "Runtime Safety and Selection Impact",
        "Comparison Request / Handoff Summary",
        "Comparison Readiness / Request Handoff",
        "Readiness is not a comparison result",
        "Comparison &amp; Review Controls",
        "source_type + scope_type + scope_value + time_window + resolution_state + readiness_state",
        "Source Type",
        "Scope Type",
        "Scope Value",
        "Resolution",
        "Readiness",
        "Both Comparable",
        "screen2-control-info-box",
        "screen2-control-card-grid",
        "load_required",
        "Application",
        "DB Name",
        "DBID",
        "Instance",
        "Host/System",
        "AWR / Run",
        "Effective Snapshot / Window",
        "Load available runtime options",
        "phase7cm-service-button screen3-runtime-options-button",
        "screen3-runtime-filter-panel",
        "data-screen3-runtime-options-target=\"runtime-filter-application\"",
        "data-screen3-runtime-options-target=\"runtime-filter-db\"",
        "data-screen3-runtime-options-target=\"runtime-filter-dbid\"",
        "data-screen3-runtime-options-target=\"runtime-filter-instance\"",
        "data-screen3-runtime-options-target=\"runtime-filter-host\"",
        "data-screen3-runtime-options-target=\"runtime-filter-source-type\"",
        "data-screen3-runtime-options-target=\"runtime-filter-time-range\"",
        "screen3-filter-select",
        "screen3RuntimeFilterSearch",
        "Apply Filters",
        "Clear Filters",
        "data-screen3-filtered-result-count",
        "screen3ActiveSelectionTarget",
        "screen3-runtime-scope-table",
        "data-screen3-runtime-options-target=\"runtime-scope-rows\"",
        "data-screen3-runtime-options-target=\"interval-rows\"",
        "screen3-interval-full-width-panel",
        "Apply interval to",
        "Runtime options route unavailable",
        "route available",
        "No runtime options found",
        "Runtime options loaded",
        "/phase7/dashboard/screen3/options",
        "Target A",
        "Target B",
        "Requested Artifact / Reference",
        "Screen 4 Handoff",
        "Target A Resolution",
        "Target B Resolution",
        "Resolved AWRs",
        "Resolved Windows",
        "Current DB history",
        "Similar AWRs",
        "Cluster baseline",
        "Fleet baseline",
        "Diagnosis",
        "Historical proof",
        "Anomaly review",
        "Period comparison",
        "Similarity review",
        "Local selection changes only browser/local request context",
        "Existing run truth unchanged",
        "screen3-governed-actions-card",
        "screen3-result-summary-banner",
        "runtime_options_source_tables",
        "table_exists",
        "key_columns_used",
        "included_in_screen3_runtime_options",
        "screen3RuntimeOptionsCache",
        "screen3-runtime-options-v1",
        "Runtime options restored from browser cache",
        "cached runtime options were not activated",
        "Cached runtime options are available for continuity only; they are not active evidence.",
        "Cache Status",
        "Generated at build time",
        "AI DB:",
        "Workflow:",
        "LLM:",
        "data-dashboard-runtime-badge=\"true\"",
        "data-dashboard-runtime-workflow-status=\"true\"",
        "runtime-badge-hydrated",
        "readStoredWorkflowStatus",
        "Check with Load Options",
        "State source:",
        "screen3RuntimeScopeSelectionSource",
        "screen3TargetASelectionSource",
        "screen3TargetBSelectionSource",
        "data-screen3-runtime-sort",
        "data-screen3-table-sort",
        "data-screen3-table-filter",
        "data-screen3-table-filter-toggle",
        "data-screen3-clear-table-filters",
        "data-screen3-table-count",
        "data-screen3-table-sort-summary",
        "data-screen3-table-filter-summary",
        "data-screen3-table-id=\"screen3-runtime-inventory\"",
        "data-screen3-table-id=\"screen3-intervals\"",
        "data-screen3-table-id=\"screen3-target-a-options\"",
        "data-screen3-table-id=\"screen3-target-b-options\"",
        "screen3-selection-legend",
        "screen3-selected-context-strip",
        "screen3-selected-runtime-row",
        "screen3-selected-interval-row",
        "screen3-selected-advanced-row",
        "initializeScreen3Tables",
        "data-screen3-sort-indicator",
        "screen3SelectedRuntimeScopeRowId",
        "screen3SelectedTargetARowId",
        "screen3SelectedTargetBRowId",
        "screen3RuntimeRowIdentity",
        "screen3IntervalRowIdentity",
        "screen3-table-sort-button",
        "screen3-table-filter-toggle",
        "position: sticky",
        "Only its selected row gets the strong table highlight",
        "Advanced target picker: external / baseline options",
        "screen3_active_reanalysis",
        "screen3_load_runtime_options",
        'data-screen-id="screen_3"',
        'data-action-type="screen3_active_reanalysis"',
        'data-execution-mode="local_backend_execution"',
    )
    offenders = [
        f"missing runtime-control marker: {marker}"
        for marker in required_markers
        if marker not in screen3_text and marker not in normalized_screen3_text
    ]

    primary_region_end_candidates = [
        pos
        for pos in (
            screen3_text.find("Historical Phase Boundary Evidence"),
            screen3_text.find("data-phase7-legacy-context"),
            screen3_text.find("Advanced Debug"),
        )
        if pos >= 0
    ]
    primary_region_end = min(primary_region_end_candidates) if primary_region_end_candidates else len(screen3_text)
    primary_region = screen3_text[:primary_region_end]
    stale_primary_markers = (
        "Phase 7H.2 Screen 3 Control Center: read-only selectors only.",
        '<div class="section-kicker">7CP Governed Runtime</div>',
        '<div class="section-kicker">7CP Runtime Actions</div>',
        '<div class="section-kicker">Phase 7H.2</div>',
        '<div class="section-kicker">Phase 7AN</div>',
        "read-only selectors only",
        "disabled Phase 7AN action wall",
        "execution disabled in this phase",
        "static_read_only / execution disabled in this phase",
        "preview-only/static export",
    )
    lower_primary_region = primary_region.lower()
    for marker in stale_primary_markers:
        if marker.lower() in lower_primary_region:
            offenders.append(
                "stale primary Screen 3 preview marker still present: " + marker
            )

    title_markers = (
        "<title>Screen 3 - History Selector</title>",
        "<h1>Screen 3 - History Selector</h1>",
    )
    for marker in title_markers:
        if marker in screen3_text:
            offenders.append("stale Screen 3 page identity still present: " + marker)
    if "Screen 2 - Runtime Scope & Analysis Control" not in screen3_text:
        offenders.append(
            "generated runtime-control product title is missing: Screen 2 - Runtime Scope & Analysis Control"
        )
    if 'class="inline-action-button' in screen3_text:
        offenders.append(
            "generated Screen 3 Load Runtime Options buttons still use default/unstyled inline-action-button class"
        )
    if "Workflow service does not expose the runtime-control options route. Restart current dashboard_workflow_service.py." not in screen3_text:
        offenders.append(
            "generated runtime-control page missing runtime-options route recovery message"
        )
    if "Not available" not in screen3_text or "Application" not in screen3_text:
        offenders.append(
            "generated Screen 3 does not truthfully mark unavailable application metadata"
        )
    if "Filtered AWR / Run / Report Results" not in screen3_text or "Snapshot / Interval Selection" not in screen3_text:
        offenders.append(
            "generated Screen 3 does not expose DB-backed run and interval selection containers"
        )
    if "Load Runtime Options to select existing DB-backed AWRs" in screen3_text:
        offenders.append(
            "generated Screen 3 uses inconsistent capitalization for runtime option empty state"
        )

    runtime_scope_pos = screen3_text.find("Select Runtime Scope")
    comparison_pos = screen3_text.find("Resolve Comparison Targets")
    submit_pos = screen3_text.find("Submit Governed Action and Review Result")
    safety_impact_pos = screen3_text.find("Runtime Safety and Selection Impact")
    if not (
        0 <= runtime_scope_pos < comparison_pos < submit_pos < safety_impact_pos
    ):
        offenders.append(
            "generated Screen 3 does not use the required primary order: Select Runtime Scope, Resolve Comparison Targets, Submit Governed Action and Review Result, Runtime Safety and Selection Impact"
        )
    detailed_order = [
        "Runtime Evidence Path",
        "Load Runtime Options",
        "Runtime Scope Filters",
        "Filtered AWR / Run / Report Results",
        "Selected AWR / Report Row",
        "Snapshot / Interval Selection",
        "Selected Runtime Scope / Assignment Summary",
        "Resolve Comparison Targets",
        "Comparison Readiness / Request Handoff",
        "Submit Governed Action and Review Result",
    ]
    detailed_positions = [screen3_text.find(marker) for marker in detailed_order]
    if any(position < 0 for position in detailed_positions) or detailed_positions != sorted(detailed_positions):
        offenders.append(
            "generated Screen 2 Control does not use the required detailed order: "
            + " < ".join(detailed_order)
        )

    visible_screen3_text = re.sub(r"<[^>]+>", " ", visible_text(screen3_text))
    for marker in ("7CP", "Phase 7H.2", "Phase 7AN", "Runtime Selection Context"):
        if marker in visible_screen3_text:
            offenders.append(
                "generated Screen 3 exposes forbidden visible product label: " + marker
            )
    misleading_visible_markers = (
        "Selected Issue Domain",
        "Selected Execution Mode",
        "Selected Source Mode",
        "Available Actions",
    )
    for marker in misleading_visible_markers:
        if marker in visible_screen3_text:
            offenders.append(
                "generated Screen 3 still exposes misleading primary operator label: " + marker
            )

    safety_pos = screen3_text.find("Runtime Safety and Selection Impact")
    if "Technical Audit / Debug Details" in visible_text(screen3_text):
        offenders.append(
            "generated Screen 2 still exposes Technical Audit / Debug Details"
        )
    if safety_pos < 0:
        offenders.append("generated Screen 3 does not expose Runtime Safety and Selection Impact")

    result_field_checks = (
        ("Selected source mode", ("Selected source mode", "Source mode", 'data-screen3-result-field="selected_source_mode"')),
        ("Selected application", ("Selected application", "Application", 'data-screen3-result-field="selected_application"')),
        ("Selected DB", ("Selected DB", "DB", 'data-screen3-result-field="selected_db"')),
        ("Selected DBID", ("Selected DBID", "DBID", 'data-screen3-result-field="selected_dbid"')),
        ("Selected host", ("Selected host", "Host", 'data-screen3-result-field="selected_host"')),
        ("Selected instance", ("Selected instance", "Instance", 'data-screen3-result-field="selected_instance"')),
        ("Selected AWR/run", ("Selected AWR/run", "Run/report", 'data-screen3-result-field="selected_awr_run"')),
        ("Selected snapshot/window", ("Selected snapshot/window", "Snapshot/window", 'data-screen3-result-field="selected_snapshot_window"')),
        ("Runtime scope", ("Runtime scope", 'data-screen3-result-field="runtime_scope"')),
        ("Comparison mode", ("Comparison mode", 'data-screen3-result-field="comparison_mode"')),
        ("Comparison Target A", ("Comparison Target A", "Target A", 'data-screen3-result-field="comparison_target_a"', 'data-screen3-result-field="comparison_result_target_a"')),
        ("Comparison Target B", ("Comparison Target B", "Target B", 'data-screen3-result-field="comparison_target_b"', 'data-screen3-result-field="comparison_result_target_b"')),
        ("Target A readiness", ("Target A readiness", 'data-screen3-result-field="comparison_target_a_readiness"')),
        ("Target B readiness", ("Target B readiness", 'data-screen3-result-field="comparison_target_b_readiness"')),
        ("Both targets comparable", ("Both targets comparable", 'data-screen3-result-field="comparison_both_comparable"')),
        ("Review mode", ("Review mode", 'data-screen3-result-field="review_mode"')),
        ("Request ID", ("Request ID", 'data-screen3-result-field="request_id"')),
        ("Transaction ID", ("Transaction ID", 'data-screen3-result-field="transaction_id"')),
        ("Validation status", ("Validation status", "Validation", 'data-screen3-result-field="validation_status"')),
        ("Audit ID/reference", ("Audit ID/reference", "Audit reference", 'data-screen3-result-field="audit_reference"')),
        ("Persistence", ("Persistence", 'data-screen3-result-field="persistence"')),
        ("Backend / Gate Status", ("Backend / Gate Status", 'data-screen3-result-field="execution_status"')),
        ("Output artifact", ("Output artifact", 'data-screen3-result-field="output_artifact"')),
        ("New run/output reference", ("New run/output reference", 'data-screen3-result-field="new_run_output_reference"')),
        ("Existing run truth", ("Existing run truth", 'data-screen3-result-field="existing_run_truth"')),
        ("Next step", ("Next step", 'data-screen3-result-field="next_step"')),
    )
    for field, alternatives in result_field_checks:
        if not any(
            alternative in visible_screen3_text or alternative in screen3_text
            for alternative in alternatives
        ):
            offenders.append(
                "generated Screen 3 Request / Result Receipt field missing: " + field
            )

    action_primary_region_end_candidates = [
        pos
        for pos in (
            screen3_text.find("Technical Audit / Debug Details"),
            screen3_text.find("Runtime Safety and Selection Impact"),
        )
        if pos >= 0
    ]
    action_primary_region_end = (
        min(action_primary_region_end_candidates)
        if action_primary_region_end_candidates
        else primary_region_end
    )
    visible_action_primary_region = re.sub(
        r"<[^>]+>",
        " ",
        visible_text(screen3_text[:action_primary_region_end]),
    )
    for marker in ("analyze_selection", "rerun_analysis", "build_comparison", "load_from_object_storage"):
        if marker in visible_action_primary_region:
            offenders.append(
                "generated Screen 3 exposes technical action key in primary action UI: " + marker
            )
    if "screen3-reanalysis-safety-labels" in screen3_text:
        offenders.append(
            "generated Screen 3 still includes primary safety-pill wall markup"
        )

    if offenders:
        return {
            "status": "failed",
            "reason": "generated Screen 3 is not the 7CP governed runtime Control Center: "
            + "; ".join(offenders[:10]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "generated Screen 3 exposes the 7CP governed runtime Control Center and not the stale preview scaffold",
        "offenders": [],
    }


def validate_screens3_6_runtime_explanation_copy(
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Require generated Screens 3-6 to expose non-mutating explanation boundaries."""

    required_by_path = {
        "awr_dashboard/screen_3_analysis.html": (
            "The Diagnostic Snapshot explains the currently selected deterministic evidence context",
            "If this context is Target A or Target B, Screen 3 explains that target's individual deterministic diagnostic output only",
            "Target labels do not change diagnosis, scores, confidence, severity, recommendations, evidence, or thresholds",
            "Screen 3 does not compare Target A vs Target B, decide improvement/degradation, assign comparison readiness, compute comparison results, render comparison violin panels, or change diagnostic truth",
            "A-vs-B comparison review and future comparison violin panels remain a Screen 4 responsibility once deterministic comparison output exists",
        ),
        "awr_dashboard/screen_4_historical_review.html": (
            "Future A-vs-B comparison violin panels belong on Screen 4 and must render deterministic comparison output",
            "LLM-assisted wording may explain evidence or comparison meaning only after governed comparison context exists",
            "it does not compute comparison meaning or decide improvement/degradation",
        ),
        "awr_dashboard/screen_5_recommendation_action.html": (
            "LLM-assisted wording may explain deterministic recommendation meaning, action rationale, governed action request context, outcome capture meaning, and post-action evidence context when available",
            "Wording-only explanation does not change recommendation truth, action state, owner/status truth, outcome state, validation result, or future-run behavior",
        ),
        "awr_dashboard/screen_6_fleet_overview.html": (
            "LLM-assisted wording may explain learning governance, candidate meaning, materialization meaning, runtime eligibility meaning, model registry/governance state, and why materialization and runtime eligibility are separate",
            "Wording-only explanation does not accept/reject candidates, materialize candidates, activate runtime eligibility, train/activate models, change registry state, or change future-run behavior",
        ),
    }
    offenders: list[str] = []
    for path, markers in required_by_path.items():
        text = generated_texts.get(path, "")
        normalized = re.sub(r"\s+", " ", text)
        if not text:
            offenders.append(f"missing generated artifact: {path}")
            continue
        for marker in markers:
            if marker not in text and marker not in normalized:
                offenders.append(f"{path} missing Screens 3-6 explanation boundary marker: {marker}")
    if offenders:
        return {
            "status": "failed",
            "reason": "generated Screens 3-6 runtime explanation copy is incomplete: "
            + "; ".join(offenders[:8]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "generated Screens 3-6 expose non-mutating explanation ownership and boundary copy",
        "offenders": [],
    }


def validate_selection_workflow_ux(generated_texts: dict[str, str]) -> dict[str, Any]:
    """Require Index entry UX and Screen 1 source workflow landmarks."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    screen1_text = generated_texts.get("awr_dashboard/screen_1_ingestion.html", "")
    index_visible = visible_text(index_text)
    screen1_visible = visible_text(screen1_text)
    normalized_screen1_visible = re.sub(r"\s+", " ", screen1_visible)
    required_index_markers = (
        'data-phase7-primary-entry-paths="true"',
        'data-phase7-entry-path="new_source"',
        'data-phase7-entry-path="existing_platform_evidence"',
        "What do you want to work with?",
        "Load / Ingest New Source",
        "Use Existing Platform Evidence",
        "Open Screen 1 Ingestion",
        "Open Screen 2 Control",
    )
    required_screen1_markers = (
        'data-phase7-selection-workflow="true"',
        "Step 1: Select the new source mode or source context",
        "Step 2: Review source readiness and configure validation through the governed service path",
        "Step 3: Submit a governed backend source intake request",
        "Step 4: Review request state",
        "Step 5: After backend completion",
        'data-phase7-current-selection-panel="true"',
        'data-action-enabled-state="disabled-no-selection"',
        'data-phase7-action-result-panel="true"',
        'data-phase7-request-id-target="true"',
        'data-phase7-audit-status-area="true"',
        'data-entity-type=',
        'data-downstream-action=',
        "Selection state: not selected",
        "Request ID",
        "Audit record",
    )
    missing = [
        f"index:{marker}"
        for marker in required_index_markers
        if marker not in index_text
    ]
    missing.extend(
        f"screen1:{marker}"
        for marker in required_screen1_markers
        if marker not in screen1_text and marker not in normalized_screen1_visible
    )
    generic_only_markers = (
        "Step 1: Select item.",
        "Step 3: Choose governed action.",
        "Step 4: Submit request.",
        "No selection exists yet. Select a card or row to enable governed actions for this screen.",
    )
    generic_found = [
        marker
        for marker in generic_only_markers
        if marker in index_text or marker in screen1_text
    ]
    forbidden_index_markers = (
        'data-phase7-selection-workflow="true"',
        'data-phase7-action-result-panel="true"',
        'data-phase7-request-id-target="true"',
        "Request ID",
        "Audit record",
    )
    index_workflow_found = [
        marker for marker in forbidden_index_markers if marker in index_visible
    ]
    screen_specific = {
        "index_two_path_entry": (
            "what do you want to work with" in index_visible.lower()
            and "load / ingest new source" in index_visible.lower()
            and "use existing platform evidence" in index_visible.lower()
            and "screen 1" in index_visible.lower()
            and "screen 2 control" in index_visible.lower()
        ),
        "screen1_source_workflow": (
            "new source intake / validation workflow" in screen1_visible.lower()
            and "governed backend source intake request" in screen1_visible.lower()
            and "request id" in screen1_visible.lower()
            and "audit record" in screen1_visible.lower()
        ),
    }
    failed_specific = [name for name, passed in screen_specific.items() if not passed]
    if missing or failed_specific or generic_found or index_workflow_found:
        parts = []
        if missing:
            parts.append("missing UX markers: " + ", ".join(missing))
        if failed_specific:
            parts.append("missing screen-specific workflow text: " + ", ".join(failed_specific))
        if generic_found:
            parts.append("generic-only workflow text remains: " + ", ".join(generic_found))
        if index_workflow_found:
            parts.append("Index still exposes Screen 1 workflow UX: " + ", ".join(index_workflow_found))
        return {"status": "failed", "reason": "; ".join(parts)}
    return {
        "status": "passed",
        "reason": "Index entry UX and Screen 1 source workflow/result UX markers are present",
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
    """Validate Screen 1 has enough wiring for new-source click behavior."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    screen1_text = generated_texts.get("awr_dashboard/screen_1_ingestion.html", "")
    index_visible = visible_text(index_text)
    screen1_visible = visible_text(screen1_text)
    offenders: list[str] = []
    source_modes = ("local_staged", "local_file", "object_storage")
    for source_mode in source_modes:
        card_marker = f'data-dashboard-select-id="{source_mode}"'
        if card_marker not in screen1_text:
            offenders.append(f"missing selectable card for {source_mode}")
        card_pos = screen1_text.find(card_marker)
        if card_pos >= 0:
            card_context = screen1_text[max(0, card_pos - 900): card_pos + 1400]
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
        "target_screen: (isScreen1Action || isScreen1SourceAction) ? 'screen_1' : (isScreen3Action ? 'screen_3' : 'screen3')",
        "browser_file_read_attempted: false",
        "browser_object_storage_access_attempted: false",
        "em_extract_attempted: false",
        "PHASE7CM_SOURCE_MODE_REQUIRED_FIELDS",
        "sourceSelectionMissingFields",
        "sourceSubmitLabel",
        "sourceActionStateMessage",
        "Select a source to continue.",
        "Ready to submit governed backend Local Folder source intake.",
        "Ready to submit governed backend Local File source intake.",
        "Ready to submit governed Object Storage source intake metadata.",
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
        'data-phase7-primary-entry-paths="true"',
        'data-phase7-entry-path="new_source"',
        'data-phase7-entry-path="existing_platform_evidence"',
        "Load / Ingest New Source",
        "Use Existing Platform Evidence",
        "screen_1_ingestion.html",
        "screen_2_control.html",
    )
    for marker in required_index_markers:
        if marker not in index_text:
            offenders.append(f"generated index missing entry marker {marker}")

    forbidden_index_markers = (
        'data-dashboard-select-id="local_staged"',
        'data-dashboard-select-id="local_file"',
        'data-dashboard-select-id="object_storage"',
        'data-dashboard-select-id="existing_run"',
        'data-phase7-action-result-panel="true"',
        'data-phase7-source-configuration="true"',
        'data-phase7-object-storage-validation-control="true"',
    )
    for marker in forbidden_index_markers:
        if marker in index_visible:
            offenders.append(f"generated index exposes Screen 1 workflow marker {marker}")

    required_screen1_markers = (
        'data-dashboard-selected-summary',
        'data-required-selection-key="selectedSourceMode"',
        'data-action-enabled-state="disabled-no-selection"',
        'data-phase7-action-result-panel="true"',
        'data-phase7-request-id-target="true"',
        'data-phase7-audit-status-area="true"',
        'data-phase7-source-configuration="true"',
        'data-dashboard-state-input="true"',
        'data-dashboard-state-key="selectedSourcePath"',
        'data-dashboard-state-key="objectStorageNamespace"',
        'data-dashboard-state-key="objectStorageBucket"',
        'data-dashboard-state-key="objectStorageObjectName"',
        'data-dashboard-state-key="objectStorageRegion"',
        'data-phase7-object-storage-validation-control="true"',
        'data-phase7-dynamic-source-summary="true"',
        'data-phase7-source-submit-label="true"',
        "data/input",
        "Request ID",
        "Audit record",
        "success/failure",
    )
    for marker in required_screen1_markers:
        if marker not in screen1_text:
            offenders.append(f"generated Screen 1 missing {marker}")
    for marker in (
        'data-dashboard-select-id="existing_run"',
        'data-phase7-existing-run-lookup-control="true"',
        'data-phase7-existing-run-options="true"',
        'data-phase7-source-validation-card="existing_run"',
        "Load Existing Runs",
    ):
        if marker in screen1_visible:
            offenders.append(f"generated Screen 1 duplicates existing platform evidence marker {marker}")

    if offenders:
        return {
            "status": "failed",
            "reason": "Screen 1 source-selection click/submit behavior contract is incomplete: "
            + ", ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": "Screen 1 source cards select selectedSourceMode, update Current Selection, enable handoff, and include selected source context in governed payload",
        "offenders": [],
    }


def validate_picker_source_selection_support(
    source_text: str,
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Validate OS picker metadata capture for the Screen 1 source workflow."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    screen1_text = generated_texts.get("awr_dashboard/screen_1_ingestion.html", "")
    index_visible = visible_text(index_text)
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
        "AWR signature validation",
        "The current verified parser path supports .out AWR reports",
        "HTML AWR input is planned for a future parser/source adapter",
    )
    for marker in required_generated_markers:
        if marker not in screen1_text:
            offenders.append(f"generated Screen 1 missing picker marker: {marker}")

    for marker in (
        'data-phase7-source-picker="local_folder"',
        'data-phase7-source-picker="local_file"',
        'data-phase7-object-storage-validation-control="true"',
    ):
        if marker in index_visible:
            offenders.append(f"generated index exposes Screen 1 picker/validation marker: {marker}")

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
        "Ready to submit governed source intake",
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
    combined = source_text + "\n" + index_text + "\n" + screen1_text
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
        "reason": "Screen 1 local folder and local file OS pickers capture metadata, update source state, and preserve browser no-parse/no-access boundaries",
        "offenders": [],
    }


def validate_pipeline_source_summary(
    source_text: str,
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Require visible Index pipeline context without operational source state."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    offenders: list[str] = []
    pipeline_start = index_text.find('data-phase7-current-runtime-pipeline="true"')
    source_context_start = index_text.find("Deterministic Runtime Architecture")
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
        "Deterministic Analysis Pipeline",
        "The platform separates entry, intake, runtime scope, deterministic",
        "Screen 1 owns new-source intake and parser governance",
        "Screen 2 owns existing-evidence runtime scope and comparison preparation",
        "Authoritative analysis truth",
        "Deterministic Runtime Architecture",
        "Deterministic Truth vs AI Explanation",
        "Governed Memory &amp; Semantic Recall",
        "LLM / Explanation Provider",
        'data-phase7-current-runtime-pipeline="true"',
        'data-phase7-system-flow-dynamic="true"',
        ".pipeline-node small",
        ".phase7cm-source-summary-card p",
        "overflow-wrap: anywhere",
        "word-break: break-word",
        "min-width: 0",
    )
    combined = source_text + "\n" + index_text
    normalized_combined = re.sub(r"\s+", " ", combined)
    for marker in required_generated_markers:
        if marker not in combined and marker not in normalized_combined:
            offenders.append(f"generated/source dashboard missing compact pipeline marker: {marker}")

    if pipeline_region:
        full_object_path = "awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out"
        if full_object_path in pipeline_region:
            offenders.append("pipeline region renders full Object Storage object path instead of compact basename")
        if "Current source context:" in pipeline_region:
            offenders.append("pipeline ingestion node still uses generic current-source-context wording")
        if "Current source mode:" in pipeline_region or "Active source:" in pipeline_region:
            offenders.append("Index pipeline region exposes active source workflow state")
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
        "reason": "Index pipeline remains visible as platform context without exposing source workflow execution state",
        "offenders": [],
    }


def validate_governed_memory_production_wording(
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Reject phase-number project wording in the Governed Memory product block."""

    index_text = generated_texts.get("awr_dashboard/index.html", "")
    offenders: list[str] = []
    block_start = index_text.find("memory-explainer-card")
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


def validate_generated_default_evidence_gating(
    generated_texts: dict[str, str],
) -> dict[str, Any]:
    """Require generated artifacts to remain inert until an operator handoff exists."""

    required_files = GENERATED_DASHBOARD_FILES
    missing_files = [path for path in required_files if path not in generated_texts]
    offenders: list[str] = []
    if missing_files:
        offenders.extend(f"missing generated dashboard file: {path}" for path in missing_files)

    visible_by_path = {
        path: generated_default_visible_text(generated_texts.get(path, ""))
        for path in required_files
    }

    index_visible = visible_by_path.get("awr_dashboard/index.html", "")
    for marker in (
        "What do you want to work with?",
        "Load / Ingest New Source",
        "Use Existing Platform Evidence",
        "Deterministic Analysis Pipeline",
    ):
        if marker not in index_visible:
            offenders.append(f"index missing default entry/platform marker: {marker}")
    for marker in (
        "Total Files: 24",
        "Succeeded: 24",
        "Source Mode: LOCAL",
        "Overall Status:",
        "Confidence: LOW",
        "Scope: SPRTRN / 8101005004",
        "Snapshot Count: 24",
        "Comparison Window: 24 / 106h",
        "Recommendation Count:",
        "DB Name: SPRTRN",
        "Similar AWRs:",
        "Cluster:",
        "Rarity:",
    ):
        if marker in index_visible:
            offenders.append(f"index exposes generated summary by default: {marker}")

    screen1_visible = visible_by_path.get("awr_dashboard/screen_1_ingestion.html", "")
    for marker in (
        "No source selected",
        "Select a source mode or choose a folder/file before submitting.",
        "No generated run evidence is available yet.",
        "No generated file/report rows are available yet.",
        "No parser health is available yet.",
        "No parser unknown-signal results are available yet.",
        "No parser governance backlog is available yet.",
    ):
        if marker not in screen1_visible:
            offenders.append(f"screen1 missing default empty-state marker: {marker}")
    for marker in (
        "AWR candidates: 24",
        "Ready to submit governed backend Local Folder",
        "Generated Time",
        "Files Processed",
        "SPRTRN / 8101005004",
        "Runtime Parser Unknowns",
        "24 validation notes",
        "Optional IO section absence",
        "MISSING_EXPECTED_SECTION",
    ):
        if marker in screen1_visible:
            offenders.append(f"screen1 exposes generated/source evidence by default: {marker}")

    screen2_visible = visible_by_path.get("awr_dashboard/screen_2_control.html", "")
    for marker in (
        "Runtime Evidence Path",
        "None selected",
        "No valid runtime evidence path yet",
        "Choose a path from Platform Entry",
        "Load Runtime Options",
    ):
        if marker not in screen2_visible:
            offenders.append(f"screen2 missing default runtime-path marker: {marker}")
    for marker in (
        "Showing 25 of 27",
        "Use row for Target",
        "Runtime options loaded",
        "27 DB-backed row(s)",
        "AWR_RUN_HISTORY",
        "AWR_REPORT",
        "SPRTRN / 8101005004",
        "Pending comparison request",
    ):
        if marker in screen2_visible:
            offenders.append(f"screen2 exposes runtime evidence by default: {marker}")

    downstream_expectations = {
        "awr_dashboard/screen_3_analysis.html": (
            "No diagnostic evidence is selected yet.",
            ("Why This Posture", "CPU Signal:", "TUNE FIRST", "No dominant scored domain selected"),
        ),
        "awr_dashboard/screen_4_historical_review.html": (
            "No review evidence is selected yet.",
            ("Evidence Review / Historical &amp; Comparison Context", "Historical Verdict", "Anomaly Burden", "SPRTRN / 8101005004"),
        ),
        "awr_dashboard/screen_5_recommendation_action.html": (
            "No recommendation/action context is selected yet.",
            ("No Immediate Scaling Action Recommended", "Action Rationale", "Evidence Checklist", "db file sequential read"),
        ),
        "awr_dashboard/screen_6_fleet_overview.html": (
            "No learning governance context is selected yet.",
            ("Learning Governance Context Preview", "Nearest Similar AWRs", "Similar AWRs", "SPRTRN / 8101005004"),
        ),
    }
    for path, (required_empty_marker, forbidden_markers) in downstream_expectations.items():
        text = visible_by_path.get(path, "")
        if "Evidence Handoff Required" not in text or required_empty_marker not in text:
            offenders.append(f"{path} missing Evidence Handoff Required empty state")
        for marker in forbidden_markers:
            if marker in text:
                offenders.append(f"{path} exposes generated downstream evidence by default: {marker}")

    if offenders:
        return {
            "status": "failed",
            "reason": "fresh generated dashboard still exposes generated artifacts as active evidence: "
            + "; ".join(offenders[:12]),
            "offenders": offenders,
        }
    return {
        "status": "passed",
        "reason": (
            "fresh generated dashboard keeps generated artifact payloads inert until a current "
            "Screen 1 artifact-ready handoff or Screen 2 runtime-scope handoff exists"
        ),
        "offenders": [],
    }


class GeneratedDefaultVisibleTextParser(HTMLParser):
    """Extract static product-visible text while ignoring hidden payloads/templates."""

    _VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
    _BLOCK_TAGS = {
        "article",
        "br",
        "dd",
        "div",
        "dt",
        "h1",
        "h2",
        "h3",
        "h4",
        "li",
        "p",
        "section",
        "td",
        "th",
        "tr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        attr_map = {name.lower(): value for name, value in attrs}
        skip_this = self._should_skip(normalized_tag, attr_map)
        if self._skip_depth:
            if normalized_tag not in self._VOID_TAGS:
                self._skip_depth += 1
            return
        if skip_this:
            if normalized_tag not in self._VOID_TAGS:
                self._skip_depth = 1
            return
        if normalized_tag in self._BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        attr_map = {name.lower(): value for name, value in attrs}
        if self._skip_depth or self._should_skip(normalized_tag, attr_map):
            return
        if normalized_tag in self._BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if tag.lower() in self._BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self._chunks.append(data)

    def get_text(self) -> str:
        return re.sub(r"[ \t\r\f\v]+", " ", "".join(self._chunks)).strip()

    @staticmethod
    def _should_skip(tag: str, attrs: dict[str, str | None]) -> bool:
        if tag in {"script", "style", "template", "noscript"}:
            return True
        if tag == "details" and "open" not in attrs:
            return True
        if "hidden" in attrs:
            return True
        if attrs.get("aria-hidden") == "true":
            return True
        gated_attributes = (
            "data-dashboard-evidence-gated-content",
            "data-screen1-artifact-ready-content",
            "data-screen3-source-handoff-content",
            "data-screen3-technical-source-state",
        )
        return any(attrs.get(attribute) == "true" for attribute in gated_attributes)


def generated_default_visible_text(html: str) -> str:
    parser = GeneratedDefaultVisibleTextParser()
    parser.feed(html)
    return parser.get_text()


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
        text = generated_default_visible_text(raw_text)
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
                        "preview only",
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
