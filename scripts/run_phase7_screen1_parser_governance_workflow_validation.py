#!/usr/bin/env python3
"""Validate the 7CN Screen 1 parser governance runtime workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BLOCKER_ID = "SCREEN1_PARSER_GOVERNANCE_RUNTIME_WORKFLOW_NOT_WIRED"

REQUIRED_SCREEN1_ACTIONS: tuple[str, ...] = (
    "parser_unknown_review",
)

REQUIRED_OPERATOR_WORKFLOW_SNIPPETS: tuple[str, ...] = (
    "Run / Intake Report",
    "Full File / Report Table",
    "data-screen1-full-report-table",
    "data-screen1-full-report-table-compact",
    "data-screen1-full-report-row",
    "Unknown Signals",
    "data-screen1-parser-review-unknown-signals",
    "Parser Governance Backlog Review",
    "Review persisted parser signals and submit a governed backlog review request.",
    "Optional IO section absence",
    "24 persisted review records",
    "Current run unknowns: 0",
    "This is not a new runtime parser failure",
    "data-screen1-backlog-item",
    "data-screen1-backlog-decision",
    "data-screen1-backlog-reviewer",
    "data-screen1-backlog-rationale",
    "data-screen1-backlog-submit",
    "data-screen1-governance-result-panel",
    "Submit Governed Backlog Review Request",
    "New AWR Field Mapping Candidates",
    "No new AWR field mapping candidates are available for review.",
    "Field approval will appear here when governed parser mapping candidate records exist.",
)

FORBIDDEN_SCREEN1_SNIPPETS: tuple[str, ...] = (
    'data-preview-only="true" data-phase7cn-parser-governance-workflow="true"',
    'data-phase4i-mutation-allowed="true"',
    'data-phase8-behavior="true"',
    'data-runtime-influence-granted="true"',
    "scripts/run_analysis.py",
    "browser_db_query_attempted: true",
    "browser_object_storage_access_attempted: true",
    "browser_file_read_attempted: true",
    "browser_parsing_performed: true",
    "No API calls",
    "No network calls",
)

VISIBLE_PHASE_PREVIEW_SNIPPETS: tuple[str, ...] = (
    "Phase 7",
    "Phase 7AW Preview",
    "Phase 7AX Preview",
    "Phase 6 Parser Review",
    "Phase 7CN",
    "7CN",
    "7CM",
    "7AW",
    "7AX",
    "preview",
    "certification",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the 7CN Screen 1 parser governance runtime workflow.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument(
        "--generated-dir",
        default="",
        help="Optional generated dashboard directory.",
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
    return 0 if summary["screen1_parser_governance_ready"] else 1


def run_validation(*, generated_dir: Path | None = None) -> dict[str, Any]:
    source = read_text(ROOT / "src" / "reporting" / "html_dashboard.py")
    contract = read_text(ROOT / "src" / "learning" / "dashboard_runtime_interaction.py")
    service_exists = (ROOT / "scripts" / "dashboard_workflow_service.py").is_file()
    generated_root = generated_dir or ROOT / "awr_dashboard"
    generated_screen1 = read_text(generated_root / "screen_1_ingestion.html")
    return validate_screen1_parser_governance(
        source_text=source,
        contract_text=contract,
        generated_text=generated_screen1,
        service_exists=service_exists,
    )


def validate_screen1_parser_governance(
    *,
    source_text: str,
    contract_text: str,
    generated_text: str,
    service_exists: bool,
) -> dict[str, Any]:
    historical_index = generated_text.find("screen1-historical-governance-evidence")
    primary_text = (
        generated_text[:historical_index]
        if historical_index >= 0
        else generated_text
    )
    primary_visible_text = visible_text(primary_text)
    run_report_index = generated_text.find('id="screen1-run-intake-report"')
    full_report_index = generated_text.find('id="screen1-full-report-table"')
    parser_health_index = generated_text.find('id="screen1-parser-health"')
    parser_review_index = generated_text.find('id="screen1-parser-review-unknown-signals"')
    governance_index = generated_text.find('id="screen1-parser-governance-review"')
    field_mapping_index = generated_text.find('id="screen1-field-mapping-candidates"')
    knowledge_index = generated_text.find('id="screen1-knowledge-artifact-context"')
    run_intake_report_ready = (
        run_report_index >= 0
        and "Run / Intake Report" in primary_text
        and "Run Label / Generated Time" in primary_text
        and "Source Mode" in primary_text
        and "Total Files" in primary_text
        and "Processed" in primary_text
        and "Succeeded" in primary_text
        and "Failed" in primary_text
        and "Skipped" in primary_text
        and "DB Connectivity" in primary_text
        and "DB Load Mode" in primary_text
        and "Already Loaded" in primary_text
        and "Newly Loaded" in primary_text
        and "Reused AWR IDs" in primary_text
        and "Feature Vectors Existing" in primary_text
        and "Feature Vectors Created/Updated" in primary_text
        and "DB Similarity Ready" in primary_text
        and "Selected Database / DBID" in primary_text
        and "Host" in primary_text
        and "Snapshot Start" in primary_text
        and "Snapshot End" in primary_text
        and "Last Snapshot" in primary_text
        and "Current Selected Scope" in primary_text
    )
    report_inventory_removed = (
        "Report Inventory" not in primary_text
        and "Showing first" not in primary_text
        and "data-screen1-report-inventory-summary" not in primary_text
        and "screen1-report-inventory-preview-wrap" not in primary_text
        and "screen1-report-inventory-table" not in source_text
    )
    parser_governance_secondary_to_ingestion = (
        run_report_index >= 0
        and full_report_index > run_report_index
        and parser_health_index > full_report_index
        and parser_review_index > parser_health_index
        and governance_index > parser_review_index
    )
    full_report_context = (
        generated_text[max(0, full_report_index - 200): full_report_index + 300]
        if full_report_index >= 0
        else ""
    )
    full_report_section = (
        generated_text[full_report_index:parser_health_index]
        if full_report_index >= 0 and parser_health_index > full_report_index
        else ""
    )
    full_report_row_count = full_report_section.count('data-screen1-full-report-row="true"')
    compact_full_report_columns_ready = (
        "data-screen1-full-report-table-compact" in full_report_section
        and "<th>File Name</th>" in full_report_section
        and "<th>Parse / DB</th>" in full_report_section
        and "<th>AWR / Vector</th>" in full_report_section
        and "<th>DB / DBID</th>" in full_report_section
        and "<th>Host / Instance</th>" in full_report_section
        and "<th>Snapshot Window</th>" in full_report_section
        and "<th>Parser Notes</th>" in full_report_section
        and "AWR ID:" in full_report_section
        and "<th>File</th>" not in full_report_section
        and "<th>Parse</th>" not in full_report_section
        and "<th>DB Status</th>" not in full_report_section
        and "<th>AWR_ID</th>" not in full_report_section
        and "<th>AWR ID</th>" not in full_report_section
        and "<th>DB Name</th>" not in full_report_section
        and "<th>DBID</th>" not in full_report_section
        and "<th>Instance</th>" not in full_report_section
        and "<th>Host</th>" not in full_report_section
        and "<th>Snapshot Begin</th>" not in full_report_section
        and "<th>Snapshot End</th>" not in full_report_section
        and "<th>Vector Status</th>" not in full_report_section
        and "<th>Similarity Eligible</th>" not in full_report_section
        and "<th>Vector / Similarity</th>" not in full_report_section
    )
    full_report_table_visible = (
        full_report_index >= 0
        and "Full File / Report Table" in primary_text
        and "data-screen1-full-report-table" in primary_text
        and "<details" not in full_report_context
        and (historical_index < 0 or full_report_index < historical_index)
        and full_report_row_count >= 24
        and compact_full_report_columns_ready
        and "screen1-full-report-table-wrap" in source_text
        and "overflow-x: visible" in source_text
        and "table-layout: fixed" in source_text
        and "overflow-wrap: anywhere" in source_text
    )
    parser_review_unknown_signals_visible = (
        parser_review_index >= 0
        and "Unknown Signals" in primary_text
        and "data-screen1-parser-review-unknown-signals" in primary_text
        and "Current Run Unknowns" in primary_text
        and "Persisted Review Records" in primary_text
        and "MISSING_EXPECTED_SECTION" in primary_text
        and (historical_index < 0 or parser_review_index < historical_index)
    )
    section_order_ready = (
        run_report_index >= 0
        and full_report_index > run_report_index
        and parser_health_index > full_report_index
        and parser_review_index > parser_health_index
        and governance_index > parser_review_index
        and field_mapping_index > governance_index
        and knowledge_index > field_mapping_index
        and historical_index > knowledge_index
    )
    heading_cleanup_ready = all(
        snippet in primary_text
        for snippet in (
            "<div class=\"section-kicker\">INGESTION</div>",
            "<div class=\"section-kicker\">REPORTS</div>",
            "<div class=\"section-kicker\">PARSER HEALTH</div>",
            "<h2>Parse Confidence</h2>",
            "<div class=\"section-kicker\">PARSER REVIEW</div>",
            "<h2>Unknown Signals</h2>",
            "<div class=\"section-kicker\">GOVERNANCE</div>",
            "<div class=\"section-kicker\">PARSER MAPPING</div>",
            "<div class=\"section-kicker\">KNOWLEDGE CONTEXT</div>",
            "<h2>Artifact Context</h2>",
        )
    ) and not any(
        duplicate in primary_text
        for duplicate in (
            "<div class=\"section-kicker\">Run / Intake Report</div>",
            "<div class=\"section-kicker\">Full File / Report Table</div>",
            "<h2>Parser Health / Parse Confidence</h2>",
            "<h2>Parser Review / Unknown Signals</h2>",
            "<h3>Parse Confidence</h3>",
            "<h3>Unknown Signal Summary</h3>",
            "<h2>Knowledge Artifact Context</h2>",
            "<div class=\"section-kicker\">Knowledge Artifact Context</div>",
        )
    )
    primary_workflow_ready = all(
        snippet in source_text and snippet in generated_text
        for snippet in REQUIRED_OPERATOR_WORKFLOW_SNIPPETS
    )
    preview_index = generated_text.find("screen1-parser-unknown-review-preview-panel")
    primary_index = generated_text.find("screen1-parser-governance-runtime-workflow")
    review_index = generated_text.find("screen1-parser-governance-review")
    legacy_preview_not_primary = bool(
        review_index >= 0
        and (
            preview_index < 0
            or (historical_index > review_index and historical_index < preview_index)
        )
        and "Historical / Debug Evidence" in generated_text
        or (review_index >= 0 and preview_index < 0)
    )
    action_controls_ready = all(
        action in source_text
        for action in REQUIRED_SCREEN1_ACTIONS
    ) and "buildScreen1GovernanceReviewRequest" in source_text
    knowledge_empty_state_ready = (
        "No knowledge artifacts are currently available for review." not in primary_text
        or all(
            f'data-action-type="{action}"' not in primary_text
            for action in (
                "knowledge_artifact_review",
                "knowledge_artifact_approve",
                "knowledge_artifact_reject",
            )
        )
    )
    grouped_queue_ready = (
        "Current run unknowns: 0" in primary_text
        and "persisted parser governance backlog item" in primary_text
        and "Current run parser unknowns" not in primary_visible_text.replace("Current run unknowns", "")
        and primary_text.count('data-screen1-backlog-item="true"') == 1
        and "Request parser mapping approval" not in primary_text
    )
    field_candidate_empty_state_ready = (
        "New AWR Field Mapping Candidates" in primary_text
        and "No new AWR field mapping candidates are available for review." in primary_text
        and "Field approval will appear here when governed parser mapping candidate records exist." in primary_text
        and "Optional IO section absence is handled as parser backlog review" not in primary_text
        and "data-screen1-field-submit" not in primary_text
    )
    optional_absence_raw_present = (
        "Optional IO section not present" in generated_text
        or "MISSING_EXPECTED_SECTION" in generated_text
    )
    optional_absence_ready = (
        not optional_absence_raw_present
        or (
            "Repeated optional-section absence detected. Candidate for source-profile/parser-expectation review."
            in generated_text
        )
    )
    visible_phase_labels_not_primary = not any(
        snippet in primary_visible_text for snippet in VISIBLE_PHASE_PREVIEW_SNIPPETS
    )
    file_table_visible = full_report_table_visible
    submit_gating_ready = all(
        snippet in source_text
        for snippet in (
            "formState.selected",
            "formState.decision",
            "formState.reviewer",
            "formState.rationale",
            "disabled-missing-required-fields",
        )
    )
    request_result_ready = all(
        snippet in generated_text
        for snippet in (
            'data-screen1-governance-result="status"',
            'data-screen1-governance-result="request_id"',
            'data-screen1-governance-result="audit_id"',
            'data-screen1-governance-result="decision"',
            'data-screen1-governance-result="runtime_influence"',
            'data-screen1-governance-result="next_step"',
        )
    )
    safety_text_ready = all(
        snippet in generated_text
        for snippet in (
            "Review requests are queued and audited",
            "Parser behavior, runtime decisions",
            "dashboard truth remain unchanged",
        )
    )
    contract_validation_ready = all(
        snippet in contract_text
        for snippet in (
            "_validate_screen1_parser_governance_payload",
            "SCREEN1_PARSER_GOVERNANCE_TARGETS",
            "future_run_influence_gated",
            "parser_output_mutation_requested",
        )
    )
    browser_safety_ready = not any(
        snippet in generated_text for snippet in FORBIDDEN_SCREEN1_SNIPPETS
    )
    service_smoke = run_service_smoke_test() if service_exists else {
        "status": "skipped",
        "reason": "scripts/dashboard_workflow_service.py is missing",
    }
    service_validation_ready = (
        service_smoke.get("valid_request_accepted") is True
        and service_smoke.get("audit_reference_exists") is True
        and service_smoke.get("missing_target_rejected") is True
        and service_smoke.get("unsafe_parser_mutation_rejected") is True
        and service_smoke.get("phase4i_mutation_rejected") is True
    )
    checks = [
        check_result(
            "run_intake_report_visible",
            run_intake_report_ready,
            "Screen 1 shows a visible run/intake report before parser governance.",
        ),
        check_result(
            "report_inventory_removed",
            report_inventory_removed,
            "Screen 1 no longer renders a duplicate Report Inventory preview.",
        ),
        check_result(
            "parser_governance_secondary_to_ingestion",
            parser_governance_secondary_to_ingestion and section_order_ready,
            "Parser governance follows the visible ingestion report and parser health sections.",
        ),
        check_result(
            "screen1_primary_section_order_ready",
            section_order_ready,
            "Screen 1 primary sections appear in the required operator order.",
        ),
        check_result(
            "screen1_heading_cleanup_ready",
            heading_cleanup_ready,
            "Section kickers and H2 titles do not repeat the same phrase in primary UI.",
        ),
        check_result(
            "full_report_table_visible_not_historical",
            full_report_table_visible,
            "Full file/report table is visible by default before historical/debug evidence.",
        ),
        check_result(
            "full_report_table_compact_columns_ready",
            compact_full_report_columns_ready,
            "Full file/report table uses compact merged columns instead of the old wide column set.",
        ),
        check_result(
            "full_report_table_all_rows_visible",
            full_report_row_count >= 24,
            "Full file/report table renders all 24 report rows.",
        ),
        check_result(
            "parser_review_unknown_signals_visible",
            parser_review_unknown_signals_visible,
            "Parser review / unknown signals is visible in the operational page.",
        ),
        check_result(
            "primary_parser_governance_workflow_exists",
            primary_workflow_ready,
            "Screen 1 has a primary governed parser review workflow panel.",
        ),
        check_result(
            "legacy_preview_not_primary",
            legacy_preview_not_primary,
            "Historical preview/read-only panels are collapsed below the primary workflow.",
        ),
        check_result(
            "operator_decision_form_exists",
            primary_workflow_ready,
            "Clickable item, decision field, reviewer field, rationale field, submit button, and result panel exist.",
        ),
        check_result(
            "governed_action_controls_exist",
            action_controls_ready,
            "Screen 1 governed action controls are present.",
        ),
        check_result(
            "knowledge_artifact_actions_hidden_when_empty",
            knowledge_empty_state_ready,
            "Knowledge artifact actions are hidden when no artifacts are available.",
        ),
        check_result(
            "grouped_governance_queue_ready",
            grouped_queue_ready,
            "Current runtime unknown count and persisted backlog item are distinguished.",
        ),
        check_result(
            "field_mapping_candidates_empty_state_ready",
            field_candidate_empty_state_ready,
            "New AWR field mapping candidates show an empty state when no persisted candidates exist.",
        ),
        check_result(
            "file_table_visible",
            file_table_visible,
            "Full report table is visible and not buried under historical/debug evidence.",
        ),
        check_result(
            "submit_button_gated_by_required_fields",
            submit_gating_ready,
            "Submit requires selected item, decision, reviewer, and rationale.",
        ),
        check_result(
            "optional_section_absence_not_parser_failure",
            optional_absence_ready,
            "Optional-section absence is framed as source-profile/parser-expectation review.",
        ),
        check_result(
            "visible_phase_preview_labels_not_primary",
            visible_phase_labels_not_primary,
            "Phase preview labels are not primary visible Screen 1 workflow content.",
        ),
        check_result(
            "request_result_audit_state_exists",
            request_result_ready,
            "Request result and audit output state is visible.",
        ),
        check_result(
            "future_run_influence_gated",
            safety_text_ready,
            "Future-run influence is visibly gated and not active by default.",
        ),
        check_result(
            "screen1_payload_validation_exists",
            contract_validation_ready,
            "Screen 1-specific service payload validation exists.",
        ),
        check_result(
            "browser_safety_boundaries_preserved",
            browser_safety_ready,
            "No browser-side DB/Object Storage/file read, AWR parsing, Phase 8, or run_analysis coupling appears in Screen 1.",
        ),
        check_result(
            "service_accepts_and_rejects_screen1_requests",
            service_validation_ready,
            "The governed service accepts valid Screen 1 requests and rejects invalid/unsafe requests.",
        ),
    ]
    ready = all(check["status"] == "passed" for check in checks)
    return {
        "phase": "Phase 7",
        "subphase": "7CN",
        "scope": "screen1_parser_governance_runtime_workflow",
        "screen1_parser_governance_ready": ready,
        "run_intake_report_ready": run_intake_report_ready,
        "report_inventory_removed": report_inventory_removed,
        "primary_workflow_ready": primary_workflow_ready,
        "action_controls_ready": action_controls_ready,
        "service_validation_ready": service_validation_ready,
        "legacy_preview_not_primary": legacy_preview_not_primary,
        "grouped_governance_queue_ready": grouped_queue_ready,
        "field_mapping_candidates_empty_state_ready": field_candidate_empty_state_ready,
        "parser_governance_secondary_to_ingestion": parser_governance_secondary_to_ingestion,
        "screen1_primary_section_order_ready": section_order_ready,
        "screen1_heading_cleanup_ready": heading_cleanup_ready,
        "full_report_table_visible": full_report_table_visible,
        "full_report_table_compact_columns_ready": compact_full_report_columns_ready,
        "full_report_table_row_count": full_report_row_count,
        "parser_review_unknown_signals_visible": parser_review_unknown_signals_visible,
        "file_table_visible": file_table_visible,
        "submit_gating_ready": submit_gating_ready,
        "knowledge_artifact_actions_hidden_when_empty": knowledge_empty_state_ready,
        "visible_phase_preview_labels_not_primary": visible_phase_labels_not_primary,
        "future_run_influence_gated": safety_text_ready,
        "blocker_active": not ready,
        "blocker_id": "" if ready else BLOCKER_ID,
        "remaining_deferred_screens": [
            "7CO Screen 2 Diagnostic Review Runtime Workflow",
            "7CP Screen 3 Active Re-Analysis Runtime Workflow",
            "7CQ Screen 4 Historical Review Runtime Workflow",
            "7CR Screen 5 Recommendation / Action / Outcome Runtime Workflow",
            "7CS Screen 6 Governance Runtime Workflow",
            "7CT Cross-Screen Runtime Workflow Integration",
        ],
        "service_smoke": service_smoke,
        "checks": checks,
    }


def run_service_smoke_test() -> dict[str, Any]:
    from src.learning.dashboard_runtime_interaction import process_dashboard_action

    base_request: dict[str, Any] = {
        "screen_id": "screen_1",
        "action_type": "parser_unknown_review",
        "workflow_type": "screen1_parser_unknown_review",
        "actor_id": "ACTOR-LOCAL-VALIDATOR",
        "target_type": "parser_unknown_signal",
        "target_id": "unknown-validator-1",
        "payload": {
            "reviewer_actor_id": "ACTOR-LOCAL-VALIDATOR",
            "governance_intent": "review parser unknown signal",
            "governance_status": "review_requested",
            "selected_context_key": "selectedUnknownSignal",
            "selected_context_value": "unknown-validator-1",
            "selectedUnknownSignal": "unknown-validator-1",
            "target_screen": "screen_1",
            "future_run_influence_gated": True,
            "future_run_influence_granted": False,
            "future_run_influence_active": False,
            "runtime_activation_requested": False,
            "runtime_activation_granted": False,
            "parser_output_mutation_requested": False,
            "parser_output_mutation_allowed": False,
            "direct_parser_mutation_allowed": False,
            "phase4i_mutation_allowed": False,
            "phase4i_mutation_requested": False,
            "phase8_behavior": False,
            "browser_db_query_attempted": False,
            "browser_object_storage_access_attempted": False,
            "browser_file_read_attempted": False,
            "browser_parsing_performed": False,
            "run_analysis_coupling": False,
            "em_extract_attempted": False,
        },
        "runtime_influence_granted": False,
        "phase4i_mutation_allowed": False,
        "phase8_behavior": False,
        "direct_truth_mutation_allowed": False,
        "run_analysis_coupling": False,
    }
    with tempfile.TemporaryDirectory() as tempdir:
        queue_dir = Path(tempdir)
        valid = process_dashboard_action(base_request, queue_dir=queue_dir)
        missing_target = json.loads(json.dumps(base_request))
        missing_target["target_id"] = "screen1-parser-governance"
        missing_target["payload"]["selected_context_value"] = ""
        unsafe_parser = json.loads(json.dumps(base_request))
        unsafe_parser["payload"]["parser_output_mutation_requested"] = True
        unsafe_phase4i = json.loads(json.dumps(base_request))
        unsafe_phase4i["payload"]["phase4i_mutation_requested"] = True
        unsafe_phase4i["phase4i_mutation_allowed"] = True
        missing = process_dashboard_action(missing_target, queue_dir=queue_dir)
        parser_mutation = process_dashboard_action(unsafe_parser, queue_dir=queue_dir)
        phase4i_mutation = process_dashboard_action(unsafe_phase4i, queue_dir=queue_dir)
        audit_path = Path(valid.audit_reference or "")
        return {
            "status": "passed" if valid.status == "accepted" else "failed",
            "valid_request_accepted": valid.status == "accepted",
            "queued": valid.queued,
            "audit_reference": valid.audit_reference,
            "audit_reference_exists": audit_path.is_file(),
            "missing_target_rejected": missing.status == "rejected",
            "unsafe_parser_mutation_rejected": parser_mutation.status == "rejected",
            "phase4i_mutation_rejected": phase4i_mutation.status == "rejected",
            "parser_output_mutated": valid.source_summary.get("parser_output_mutation_allowed") is True,
            "phase4i_mutated": valid.phase4i_mutated,
        }


def check_result(name: str, passed: bool, reason: str) -> dict[str, str]:
    return {
        "name": name,
        "status": "passed" if passed else "failed",
        "reason": reason,
    }


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def visible_text(html_text: str) -> str:
    text = html_text
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def print_human_summary(summary: dict[str, Any]) -> None:
    status = "READY" if summary["screen1_parser_governance_ready"] else "BLOCKED"
    print(f"7CN Screen 1 parser governance runtime workflow: {status}")
    for check in summary["checks"]:
        print(f"- {check['name']}: {check['status']} - {check['reason']}")


if __name__ == "__main__":
    raise SystemExit(main())
