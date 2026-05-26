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
    "Current Generated Run / Intake Evidence",
    "Generated evidence reflects a generated dashboard artifact.",
    "Browser-side source intake does",
    "not mutate deterministic truth.",
    "data-screen1-artifact-ready-region",
    "data-screen1-artifact-ready-content",
    "data-screen1-artifact-template",
    "data-screen1-artifact-empty-state",
    "screen1-generated-evidence-group",
    "screen1-generated-evidence-info-grid",
    "screen1-generated-evidence-info-box",
    "Intake Result",
    "Generated Time",
    "Files Processed",
    "Result",
    "Dataset Status",
    "Source Database",
    "DB / DBID",
    "Database Version",
    "Database Role",
    "Operating System",
    "Host / Instance",
    "Platform / Topology Evidence",
    "Platform",
    "Selected Scope",
    "Instance Count",
    "RAC / Cluster Evidence",
    "Data Guard / ADG Evidence",
    "Topology Notes",
    "Capacity Snapshot",
    "Cumulative OCPUs / Cores",
    "Memory per Instance",
    "DB Load / Vector Status",
    "Loaded / Reused AWR IDs",
    "Feature Vectors",
    "Similarity Ready",
    "Snapshot Window",
    "Snapshot Start / End",
    "Parser / Source Profile Notes",
    "Parser optional-section notes",
    "Source-profile/parser-expectation review notes",
    "Full File / Report Table",
    "data-screen1-full-report-table",
    "data-screen1-full-report-table-compact",
    "data-screen1-full-report-row",
    "data-screen1-full-report-table-template",
    "Unknown Signals",
    "data-screen1-parser-review-unknown-signals",
    "Parser Governance Backlog Review",
    "Review parser signals for the current generated artifact and submit a",
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
    "Why this matters",
    "How this is implemented",
    "Persistence",
    "What changes",
    "What does not change",
    "Future-run impact",
    "Learning / ML impact",
    "This review turns repeated parser uncertainty into governed parser-improvement input.",
    "This review does not change current or future runs by itself.",
    "should review whether it can be materialized",
    "This action does not directly change ML behavior or train a model.",
    "may become learning/governance input",
    "Submitting a parser governance review records reviewer context as DB-backed governed workflow state",
    "DB-backed governed workflow metadata",
    "does not update AWR_UNKNOWN_SIGNAL_HISTORY",
    "create AWR_PARSER_MAPPING_CANDIDATE rows",
    "screen_6_fleet_overview.html",
    "New AWR Field Mapping Candidates",
    "No new AWR field mapping candidates are available for review.",
    "Field approval will appear here when governed parser mapping candidate records exist.",
    "No fake candidates are shown.",
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
        and "Current Generated Run / Intake Evidence" in primary_text
        and "Generated evidence reflects a generated dashboard artifact." in primary_text
        and "created by the unsent source workflow above" in primary_text
        and 'data-screen1-artifact-ready-region="true"' in primary_text
        and 'data-screen1-generated-artifact-ready="false"' in primary_text
        and 'data-screen1-artifact-ready-content="true"' in primary_text
        and 'data-screen1-generated-evidence-template="true"' in primary_text
        and "No generated run evidence is available yet." in primary_visible_text
        and "screen1GeneratedArtifactReady" in source_text
        and "updateScreen1GeneratedArtifactGate" in source_text
        and "screen1-generated-evidence-group" in primary_text
        and "screen1-generated-evidence-info-grid" in primary_text
        and "screen1-generated-evidence-info-box" in primary_text
        and "info-box screen1-generated-evidence-info-box" in primary_text
        and "Intake Result" in primary_text
        and "Generated Time" in primary_text
        and "Source Mode" in primary_text
        and "Files Processed" in primary_text
        and "Result" in primary_text
        and "Dataset Status" in primary_text
        and "Source Database" in primary_text
        and "DB / DBID" in primary_text
        and "Database Version" in primary_text
        and "Database Role" in primary_text
        and "Operating System" in primary_text
        and "Host / Instance" in primary_text
        and "Platform / Topology Evidence" in primary_text
        and "Platform" in primary_text
        and "Selected Scope" in primary_text
        and "Instance Count" in primary_text
        and "RAC / Cluster Evidence" in primary_text
        and "Data Guard / ADG Evidence" in primary_text
        and "Topology Notes" in primary_text
        and "Capacity Snapshot" in primary_text
        and "Cumulative OCPUs / Cores" in primary_text
        and "Memory per Instance" in primary_text
        and "DB Load / Vector Status" in primary_text
        and "DB Connectivity" in primary_text
        and "DB Load Mode" in primary_text
        and "Loaded / Reused AWR IDs" in primary_text
        and "Feature Vectors" in primary_text
        and "Similarity Ready" in primary_text
        and "Snapshot Window" in primary_text
        and "Snapshot Start / End" in primary_text
        and "Last Snapshot" in primary_text
        and "Parser / Source Profile Notes" in primary_text
        and "Parser optional-section notes" in primary_text
        and "Source-profile/parser-expectation review notes" in primary_text
        and "Topology Detected" not in primary_text
        and "RAC Context" not in primary_text
        and "Version / Platform / Topology Hints" not in primary_text
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
    parser_health_section = (
        generated_text[parser_health_index:parser_review_index]
        if parser_health_index >= 0 and parser_review_index > parser_health_index
        else ""
    )
    parser_review_section = (
        generated_text[parser_review_index:governance_index]
        if parser_review_index >= 0 and governance_index > parser_review_index
        else ""
    )
    governance_section = (
        generated_text[governance_index:field_mapping_index]
        if governance_index >= 0 and field_mapping_index > governance_index
        else ""
    )
    full_report_visible_text = visible_text(full_report_section)
    parser_health_visible_text = visible_text(parser_health_section)
    parser_review_visible_text = visible_text(parser_review_section)
    governance_visible_text = visible_text(governance_section)
    full_report_row_count = full_report_section.count('data-screen1-full-report-row="true"')
    generated_evidence_gated_ready = (
        'data-screen1-artifact-ready-region="true"' in primary_text
        and 'data-screen1-generated-artifact-ready="false"' in primary_text
        and 'data-screen1-artifact-empty-state="true"' in primary_text
        and 'data-screen1-artifact-ready-content="true"' in primary_text
        and 'data-screen1-generated-evidence-template="true"' in primary_text
        and 'data-screen1-full-report-table-template="true"' in primary_text
        and "No generated run evidence is available yet." in primary_visible_text
        and "No generated file/report rows are available yet." in primary_visible_text
        and "screen1GeneratedArtifactReady" in source_text
        and "screen1GeneratedRunExecuted" in source_text
        and "screen1SelectedGeneratedArtifactReady" in source_text
        and "updateScreen1GeneratedArtifactGate" in source_text
        and "screen1GeneratedArtifactReady: screen1GeneratedArtifactReady" in source_text
    )
    generated_values_hidden_before_ready = (
        "Unit run" not in primary_visible_text
        and "AWR ID:" not in full_report_visible_text
        and "data-screen1-full-report-row" not in full_report_visible_text
    )
    parser_dynamic_blocks_gated_before_ready = (
        "data-screen1-parser-health-template" in parser_health_section
        and "data-screen1-parser-review-template" in parser_review_section
        and "data-screen1-backlog-review-template" in governance_section
        and "No parser health is available yet." in parser_health_visible_text
        and "No parser unknown-signal results are available yet." in parser_review_visible_text
        and "No parser governance backlog is available yet." in governance_visible_text
        and "24 validation notes were detected" not in parser_health_visible_text
        and "Persisted Review Records" not in parser_review_visible_text
        and "MISSING_EXPECTED_SECTION" not in parser_review_visible_text
        and "Optional IO section absence" not in governance_visible_text
        and "24 persisted review records" not in governance_visible_text
        and "Current run unknowns: 0" not in governance_visible_text
    )
    compact_full_report_columns_ready = (
        "data-screen1-full-report-table-compact" in full_report_section
        and "File Name" in full_report_section
        and "Parse / DB" in full_report_section
        and "AWR / Vector" in full_report_section
        and "DB / DBID" in full_report_section
        and "Host / Instance" in full_report_section
        and "Snapshot Window" in full_report_section
        and "Parser Notes" in full_report_section
        and 'data-screen3-table-id="screen1-full-report-table"' in full_report_section
        and "data-screen3-table-sort" in full_report_section
        and "data-screen3-table-filter" in full_report_section
        and "data-screen3-table-filter-toggle" in full_report_section
        and "data-screen3-table-count" in full_report_section
        and "data-screen3-table-sort-summary" in full_report_section
        and "data-screen3-table-filter-summary" in full_report_section
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
        and generated_evidence_gated_ready
        and generated_values_hidden_before_ready
        and full_report_row_count >= 24
        and compact_full_report_columns_ready
        and "screen1-full-report-table-wrap" in source_text
        and "max-height: 520px" in source_text
        and "overflow: auto" in source_text
        and "position: sticky" in source_text
        and "table-layout: fixed" in source_text
        and "overflow-wrap: anywhere" in source_text
    )
    parser_review_unknown_signals_visible = (
        parser_review_index >= 0
        and "Unknown Signals" in primary_text
        and "data-screen1-parser-review-unknown-signals" in primary_text
        and "screen1-unknown-signals-compact" in primary_text
        and "Parser Review Status" in primary_text
        and "Dominant Grouped Signal" in primary_text
        and "Current Run Unknowns" in primary_text
        and "Persisted Review Records" in primary_text
        and "New / Classified" in primary_text
        and "Review Status" in primary_text
        and "MISSING_EXPECTED_SECTION" in primary_text
        and "Persisted parser governance backlog item, not a new runtime parser failure." in primary_text
        and "Use Parser Governance Backlog Review below to decide how this" in primary_text
        and "Review Backlog Summary" not in parser_review_section
        and "Grouped Unknown Signals" not in parser_review_section
        and "screen1-parser-review-summary-table" not in parser_review_section
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
        and (historical_index < 0 or historical_index > knowledge_index)
    )
    heading_cleanup_ready = all(
        snippet in primary_text
        for snippet in (
            "<div class=\"section-kicker\">GENERATED EVIDENCE</div>",
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
            "<h2>Run / Intake Report</h2>",
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
            or (
                historical_index >= 0
                and historical_index > review_index
                and historical_index < preview_index
            )
        )
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
    field_mapping_section = (
        generated_text[field_mapping_index:knowledge_index]
        if field_mapping_index >= 0 and knowledge_index > field_mapping_index
        else ""
    )
    field_candidate_empty_state_ready = (
        "New AWR Field Mapping Candidates" in field_mapping_section
        and "No new AWR field mapping candidates are available for review." in field_mapping_section
        and "Field approval will appear here when governed parser mapping candidate records exist." in field_mapping_section
        and "No fake candidates are shown." in field_mapping_section
        and "Optional IO section absence is handled as parser backlog review" not in field_mapping_section
        and "data-screen1-field-submit" not in field_mapping_section
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
            'data-screen1-governance-result="persistence"',
            'data-screen1-governance-result="db_record"',
            'data-screen1-governance-result="decision"',
            'data-screen1-governance-result="runtime_influence"',
            'data-screen1-governance-result="next_step"',
            'data-screen1-governance-result="screen6_status"',
        )
    )
    active_workflow_index = primary_text.find('<div class="screen1-operator-workflow">')
    boundary_index = primary_text.find('<section class="screen1-governance-boundary">')
    explanation_index = primary_text.find('<section class="screen1-governance-explanation-panel">')
    explanation_layout_ready = (
        active_workflow_index >= 0
        and boundary_index > active_workflow_index
        and explanation_index > boundary_index
        and "Parser Governance Explanation" in primary_text
        and "grid-template-columns: 1fr" in source_text
        and ".screen1-governance-explanation-panel" in source_text
    )
    persistence_copy_ready = all(
        snippet in primary_text
        for snippet in (
            "Persistence",
            "DB-backed governed workflow metadata",
            "does not update AWR_UNKNOWN_SIGNAL_HISTORY",
            "create AWR_PARSER_MAPPING_CANDIDATE rows",
            "create Screen 6 learning/materialization/runtime-eligibility candidates",
            "screen_6_fleet_overview.html",
        )
    ) and all(
        snippet in source_text
        for snippet in (
            "persistence_target: 'dashboard_workflow_service_db_backed_governance'",
            "database_persistence_requested: true",
            "browser_database_persistence_performed: false",
            "screen6_candidate_created: false",
            "DB-backed parser governance record persisted",
        )
    )
    parser_governance_explanation_ready = all(
        snippet in primary_text
        for snippet in (
            "Why this matters",
            "How this is implemented",
            "Persistence",
            "What changes",
            "What does not change",
            "Future-run impact",
            "Learning / ML impact",
            "This review turns repeated parser uncertainty into governed parser-improvement input.",
            "This review does not change current or future runs by itself.",
            "should review whether it can be materialized",
            "This action does not directly change ML behavior or train a model.",
            "may become learning/governance input",
            "Submitting a parser governance review records reviewer context as DB-backed governed workflow state",
            "This protects current diagnostic truth while still allowing parser improvements",
        )
    )
    downstream_governance_ready = all(
        snippet in primary_text
        for snippet in (
            "may create governed input for downstream learning/materialization review",
            "Future-run influence is possible only if a later governed",
            "marks a parser change runtime-eligible",
            "Not applied to current run; pending separate materialization/runtime-eligibility approval.",
        )
    ) and "Queued for parser governance review. If accepted for implementation, this should proceed to Screen 6 learning/materialization governance before any future-run influence. No current runtime behavior changed." in source_text
    repeated_sections_absent = primary_text.count('id="screen1-parser-governance-review"') == 1
    screen1_static_export_wording_absent = not any(
        snippet in generated_text
        for snippet in (
            "static export",
            "static report",
            "Knowledge artifact data is not available",
        )
    )
    screen2_diagnostic_explanation_absent = not any(
        snippet in primary_visible_text
        for snippet in (
            "Focused Diagnostic Meaning",
            "mixed CPU",
            "TUNE FIRST",
            "dominance threshold",
            "Screen 4 for historical trend",
        )
    )
    safety_text_ready = all(
        snippet in generated_text
        for snippet in (
            "Submitting a parser governance review records reviewer context as DB-backed governed workflow state",
            "it does not change the current parser output, diagnosis, scoring",
            "runtime eligibility, or dashboard truth",
            "Future-run influence is possible only if a later governed",
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
        and service_smoke.get("db_insert_update_performed") is True
        and service_smoke.get("persistence_mode") == "db_backed_workflow_record_and_json_audit"
        and bool(service_smoke.get("db_record_reference"))
        and service_smoke.get("missing_target_rejected") is True
        and service_smoke.get("unsafe_parser_mutation_rejected") is True
        and service_smoke.get("phase4i_mutation_rejected") is True
    )
    checks = [
        check_result(
            "run_intake_report_artifact_gated",
            run_intake_report_ready,
            "Screen 1 gates generated run/intake evidence before parser governance.",
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
            "Full file/report table is artifact-gated before historical/debug evidence.",
        ),
        check_result(
            "full_report_table_compact_columns_ready",
            compact_full_report_columns_ready,
            "Full file/report table uses compact merged columns instead of the old wide column set.",
        ),
        check_result(
            "full_report_table_all_rows_visible",
            full_report_row_count >= 24,
            "Full file/report table preserves all 24 report rows inside artifact-ready payload.",
        ),
        check_result(
            "parser_dynamic_blocks_artifact_gated",
            parser_dynamic_blocks_gated_before_ready,
            "Parser health, unknown-signal, and governance backlog facts are hidden until artifact-ready state.",
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
            "Full report table is present, artifact-gated, and not buried under historical/debug evidence.",
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
            "Request result, persistence, and audit output state is visible.",
        ),
        check_result(
            "screen1_persistence_truth_ready",
            persistence_copy_ready,
            "Screen 1 states DB-backed governed workflow persistence with JSON audit fallback.",
        ),
        check_result(
            "parser_governance_explanation_ready",
            parser_governance_explanation_ready
            and downstream_governance_ready
            and explanation_layout_ready,
            "Parser governance explains why the backlog matters, what changes, and what remains protected.",
        ),
        check_result(
            "parser_governance_explanation_layout_ready",
            explanation_layout_ready,
            "Parser Governance Explanation appears below Governance Boundary in a vertical secondary layout.",
        ),
        check_result(
            "single_parser_governance_section_ready",
            repeated_sections_absent,
            "Multiple parser unknowns are represented inside one governance section instead of repeated sections.",
        ),
        check_result(
            "screen1_static_export_wording_absent",
            screen1_static_export_wording_absent,
            "Screen 1 product wording avoids static export/static report language.",
        ),
        check_result(
            "screen2_diagnostic_explanation_absent",
            screen2_diagnostic_explanation_absent,
            "Screen 2 diagnostic explanation wording does not leak into Screen 1.",
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
        "parser_governance_explanation_ready": (
            parser_governance_explanation_ready
            and downstream_governance_ready
            and explanation_layout_ready
        ),
        "persistence_mode": service_smoke.get("persistence_mode", "db_backed_workflow_record_and_json_audit"),
        "persistence_copy_ready": persistence_copy_ready,
        "parser_governance_explanation_layout_ready": explanation_layout_ready,
        "single_parser_governance_section_ready": repeated_sections_absent,
        "screen1_static_export_wording_absent": screen1_static_export_wording_absent,
        "screen2_diagnostic_explanation_absent": screen2_diagnostic_explanation_absent,
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
        from tests.test_phase7ca_governed_workflow_repository import FakeConnection

        queue_dir = Path(tempdir)
        fake_connection = FakeConnection()
        valid = process_dashboard_action(
            base_request,
            queue_dir=queue_dir,
            connection_factory=lambda: fake_connection,
            db_persistence_enabled=True,
        )
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
            "persistence_mode": valid.db_persistence_mode,
            "db_insert_update_performed": valid.db_persistence_status == "persisted",
            "db_record_reference": valid.db_record_reference,
            "db_tables_touched": list(valid.db_tables_touched),
            "screen6_candidate_created": False,
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
    text = re.sub(r"<template\b[^>]*>.*?</template>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(
        r"<([a-z][a-z0-9:-]*)\b(?=[^>]*\bhidden\b)[^>]*>.*?</\1>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def print_human_summary(summary: dict[str, Any]) -> None:
    status = "READY" if summary["screen1_parser_governance_ready"] else "BLOCKED"
    print(f"7CN Screen 1 parser governance runtime workflow: {status}")
    for check in summary["checks"]:
        print(f"- {check['name']}: {check['status']} - {check['reason']}")


if __name__ == "__main__":
    raise SystemExit(main())
