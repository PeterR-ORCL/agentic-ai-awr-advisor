"""Tests for the 7CN Screen 1 parser governance runtime workflow."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_screen1_validator():
    path = ROOT / "scripts" / "run_phase7_screen1_parser_governance_workflow_validation.py"
    spec = importlib.util.spec_from_file_location("phase7_screen1_validator", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load validator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def visible_screen1_text(html_text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
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


def valid_screen1_request() -> dict:
    return {
        "screen_id": "screen_1",
        "action_type": "parser_unknown_review",
        "workflow_type": "screen1_parser_unknown_review",
        "actor_id": "ACTOR-LOCAL-TEST",
        "target_type": "parser_unknown_signal",
        "target_id": "unknown-test-1",
        "payload": {
            "reviewer_actor_id": "ACTOR-LOCAL-TEST",
            "governance_intent": "review parser unknown signal",
            "governance_status": "review_requested",
            "selected_context_key": "selectedUnknownSignal",
            "selected_context_value": "unknown-test-1",
            "selectedUnknownSignal": "unknown-test-1",
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


class Phase7Screen1ParserGovernanceRuntimeWorkflowTest(unittest.TestCase):
    def test_primary_workflow_markup_exists_in_generator(self) -> None:
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        self.assertIn('data-screen1-backlog-review="true"', source)
        self.assertIn("Parser Governance Backlog Review", source)
        self.assertIn(
            "Review parser signals for the current generated artifact and submit a",
            source,
        )
        self.assertIn("Optional IO section absence", source)
        self.assertIn("New AWR Field Mapping Candidates", source)
        self.assertIn(
            "No new AWR field mapping candidates are available for review.",
            source,
        )
        self.assertIn("Current Generated Run / Intake Evidence", source)
        self.assertIn("Generated evidence reflects a generated dashboard artifact.", source)
        self.assertIn("Browser-side source intake does", source)
        self.assertIn("not mutate deterministic truth.", source)
        self.assertIn("screen1GeneratedArtifactReady", source)
        self.assertIn("screen1GeneratedRunExecuted", source)
        self.assertIn("screen1SelectedGeneratedArtifactReady", source)
        self.assertIn("updateScreen1GeneratedArtifactGate", source)
        self.assertIn("data-screen1-artifact-ready-region", source)
        self.assertIn("data-screen1-artifact-ready-content", source)
        self.assertIn("data-screen1-artifact-template", source)
        self.assertIn("data-screen1-artifact-empty-state", source)
        self.assertIn("Intake Result", source)
        self.assertIn("Files Processed", source)
        self.assertIn("Dataset Status", source)
        self.assertIn("Source Database", source)
        self.assertIn("Database Version", source)
        self.assertIn("Database Role", source)
        self.assertIn("Operating System", source)
        self.assertIn("Host / Instance", source)
        self.assertIn("Platform / Topology Evidence", source)
        self.assertIn("Selected Scope", source)
        self.assertIn("Instance Count", source)
        self.assertIn("RAC / Cluster Evidence", source)
        self.assertIn("Data Guard / ADG Evidence", source)
        self.assertIn("Topology Notes", source)
        self.assertIn("Capacity Snapshot", source)
        self.assertIn("Cumulative OCPUs / Cores", source)
        self.assertIn("Memory per Instance", source)
        self.assertIn("Parser / Source Profile Notes", source)
        self.assertIn("Parser optional-section notes", source)
        self.assertIn("Source-profile/parser-expectation review notes", source)
        self.assertNotIn("Report Inventory", source)
        self.assertNotIn("data-screen1-report-inventory-summary", source)
        self.assertNotIn("screen1-report-inventory-preview-wrap", source)
        self.assertIn("<div class=\"section-kicker\">GENERATED EVIDENCE</div>", source)
        self.assertIn("<div class=\"section-kicker\">REPORTS</div>", source)
        self.assertIn("<div class=\"section-kicker\">PARSER HEALTH</div>", source)
        self.assertIn("Parse Confidence", source)
        self.assertIn("Full File / Report Table", source)
        self.assertIn("data-screen1-full-report-table", source)
        self.assertIn("data-screen1-full-report-table-compact", source)
        self.assertIn("data-screen1-full-report-table-template", source)
        self.assertIn("position: sticky", source)
        self.assertIn("max-height: 520px", source)
        self.assertIn("File Name", source)
        self.assertIn("Parse / DB", source)
        self.assertIn("AWR / Vector", source)
        self.assertIn("DB / DBID", source)
        self.assertIn("Host / Instance", source)
        self.assertIn("Snapshot Window", source)
        self.assertIn("AWR ID:", source)
        self.assertIn("Unknown Signals", source)
        self.assertIn("data-screen1-parser-review-unknown-signals", source)
        self.assertIn("Artifact Context", source)
        self.assertNotIn("Historical / Debug Evidence", source)
        self.assertIn("Governance Boundary", source)
        self.assertIn("data-screen1-backlog-decision", source)
        self.assertIn("data-screen1-backlog-reviewer", source)
        self.assertIn("data-screen1-backlog-rationale", source)
        self.assertIn("data-screen1-backlog-submit", source)
        self.assertIn("data-screen1-governance-result-panel", source)
        self.assertIn("Submit Governed Backlog Review Request", source)
        self.assertIn("Why this matters", source)
        self.assertIn("How this is implemented", source)
        self.assertIn("Persistence", source)
        self.assertIn("What changes", source)
        self.assertIn("What does not change", source)
        self.assertIn("Future-run impact", source)
        self.assertIn("Learning / ML impact", source)
        self.assertIn(
            "This review turns repeated parser uncertainty into governed parser-improvement input.",
            source,
        )
        self.assertIn(
            "This review does not change current or future runs by itself.",
            source,
        )
        self.assertIn(
            "should review whether it can be materialized",
            source,
        )
        self.assertIn(
            "This action does not directly change ML behavior or train a model.",
            source,
        )
        self.assertIn(
            "may become learning/governance input",
            source,
        )
        self.assertIn(
            "Submitting a parser governance review records reviewer context as DB-backed governed workflow state",
            source,
        )
        self.assertIn(
            "DB-backed governed workflow metadata",
            source,
        )
        self.assertIn(
            "does not update AWR_UNKNOWN_SIGNAL_HISTORY",
            source,
        )
        self.assertIn(
            "create AWR_PARSER_MAPPING_CANDIDATE rows",
            source,
        )
        self.assertIn('data-screen1-governance-result="persistence"', source)
        self.assertIn('data-screen1-governance-result="db_record"', source)
        self.assertIn('data-screen1-governance-result="screen6_status"', source)
        self.assertIn("persistence_target: 'dashboard_workflow_service_db_backed_governance'", source)
        self.assertIn("database_persistence_requested: true", source)
        self.assertIn("browser_database_persistence_performed: false", source)
        self.assertIn("screen6_candidate_created: false", source)
        self.assertIn(
            "No knowledge artifacts are available for the current selected run/source context.",
            source,
        )
        self.assertIn("No fake candidates are shown.", source)
        self.assertIn("formState.selected", source)
        self.assertIn("formState.decision", source)
        self.assertIn("formState.reviewer", source)
        self.assertIn("formState.rationale", source)
        self.assertIn("parser_unknown_review", source)
        self.assertNotIn("No API calls", source)

    def test_service_accepts_valid_screen1_review_request(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action
        from tests.test_phase7ca_governed_workflow_repository import FakeConnection

        with tempfile.TemporaryDirectory() as tempdir:
            fake_connection = FakeConnection()
            result = process_dashboard_action(
                valid_screen1_request(),
                queue_dir=Path(tempdir),
                connection_factory=lambda: fake_connection,
                db_persistence_enabled=True,
            )
            self.assertEqual("accepted", result.status)
            self.assertTrue(result.queued)
            self.assertFalse(result.phase4i_mutated)
            self.assertFalse(result.phase8_behavior)
            self.assertFalse(result.direct_truth_mutation_performed)
            self.assertFalse(result.run_analysis_called)
            self.assertTrue(Path(result.audit_reference or "").is_file())
            envelope = json.loads(Path(result.audit_reference or "").read_text())
            self.assertEqual("screen_1", envelope["request"]["screen_id"])
            self.assertEqual("parser_unknown_review", envelope["request"]["action_type"])
            self.assertEqual(
                "governed_dashboard_action_request",
                envelope["record_type"],
            )
            self.assertTrue(str(result.audit_reference or "").endswith(".json"))
            self.assertEqual("persisted", result.db_persistence_status)
            self.assertEqual(
                "db_backed_workflow_record_and_json_audit",
                result.db_persistence_mode,
            )
            self.assertIn("AWR_WORKFLOW_REQUEST:", result.db_record_reference or "")
            self.assertIn("AWR_WORKFLOW_REQUEST", result.db_tables_touched)
            self.assertEqual(1, len(fake_connection.requests))
            self.assertEqual(1, len(fake_connection.audits))
            self.assertEqual("persisted", envelope["persistence"]["status"])
            self.assertFalse(envelope["persistence"].get("screen6_candidate_created"))
            self.assertFalse(result.screen6_candidate_created)
            self.assertFalse(
                envelope["request"]["payload"].get("screen6_candidate_created")
            )

    def test_service_rejects_missing_screen1_target(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        request = valid_screen1_request()
        request["target_id"] = "screen1-parser-governance"
        request["payload"]["selected_context_value"] = ""
        result = process_dashboard_action(request)
        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)

    def test_service_rejects_parser_and_phase4i_mutation_attempts(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        parser_request = valid_screen1_request()
        parser_request["payload"]["parser_output_mutation_requested"] = True
        phase4i_request = valid_screen1_request()
        phase4i_request["payload"]["phase4i_mutation_requested"] = True
        phase4i_request["phase4i_mutation_allowed"] = True
        self.assertEqual("rejected", process_dashboard_action(parser_request).status)
        self.assertEqual("rejected", process_dashboard_action(phase4i_request).status)

    def test_validator_accepts_screen1_workflow_source_contract(self) -> None:
        validator = load_screen1_validator()
        from src.reporting.html_dashboard import _render_screen_1_page

        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        contract = (ROOT / "src" / "learning" / "dashboard_runtime_interaction.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        rendered = _render_screen_1_page(
            {
                "header": {"run_label": "Unit run", "source_mode": "LOCAL"},
                "intake_summary": {
                    "total_files": 24,
                    "processed": 24,
                    "succeeded": 24,
                    "failed": 0,
                    "skipped": 0,
                },
                "environment_context": {
                    "source_database": "FINDB",
                    "dbid": "123456789",
                    "hostname": "host1",
                    "snapshot_start": "2026-03-29 06:00",
                    "snapshot_end": "2026-03-29 07:00",
                    "last_snapshot": "2026-03-29 07:00",
                    "selected_scope_topology": "FINDB / host1",
                },
                "db_ingestion": {
                    "summary": {
                        "db_connectivity": "connected",
                        "db_load_mode": "reuse",
                        "already_loaded": 24,
                        "newly_loaded": 0,
                        "reused_awr_ids": 24,
                        "feature_vectors_existing": 24,
                        "feature_vectors_created_updated": 0,
                        "db_similarity_ready": True,
                    }
                },
                "report_rows": [
                    {
                        "file_name": f"sample_{index:02d}.out",
                        "parse_status": "success",
                        "db_status": "reused",
                        "awr_id": index,
                        "db_name": "FINDB",
                        "dbid": "123456789",
                        "instance_name": "FINDB1",
                        "host_name": "host1",
                        "snapshot_begin": "2026-03-29 06:00",
                        "snapshot_end": "2026-03-29 07:00",
                        "vector_status": "existing",
                        "similarity_eligible": True,
                        "parser_notes": "Optional IO section not present.",
                    }
                    for index in range(1, 25)
                ],
            },
            {
                "pattern_summary": [
                    {
                        "section_name": "io",
                        "unknown_type": "MISSING_EXPECTED_SECTION",
                        "count": 24,
                    }
                ]
            },
            {
                "items": [
                    {
                        "parser_stage": "Section Mapping",
                        "classification_hint": "Top SQL",
                        "review_status": "pending",
                    }
                ],
                "knowledge_artifacts": [
                    {
                        "artifact_id": "ART-1",
                        "title": "Parser review note",
                        "status": "candidate",
                    }
                ],
            },
            {},
        )
        result = validator.validate_screen1_parser_governance(
            source_text=source,
            contract_text=contract,
            generated_text=rendered,
            service_exists=True,
        )
        self.assertTrue(result["screen1_parser_governance_ready"])
        self.assertTrue(result["service_validation_ready"])
        self.assertTrue(result["grouped_governance_queue_ready"])
        self.assertTrue(result["field_mapping_candidates_empty_state_ready"])
        self.assertTrue(result["file_table_visible"])
        self.assertTrue(result["full_report_table_compact_columns_ready"])
        self.assertEqual(24, result["full_report_table_row_count"])
        self.assertTrue(result["screen1_heading_cleanup_ready"])
        self.assertTrue(result["parser_review_unknown_signals_visible"])
        self.assertTrue(result["submit_gating_ready"])
        self.assertFalse(result["blocker_active"])

    def test_operator_workflow_is_single_item_and_product_facing(self) -> None:
        from src.reporting.html_dashboard import _render_screen_1_page

        rendered = _render_screen_1_page(
            {
                "header": {"run_label": "Unit run", "source_mode": "LOCAL"},
                "intake_summary": {
                    "total_files": 24,
                    "processed": 24,
                    "succeeded": 24,
                    "failed": 0,
                    "skipped": 0,
                },
                "environment_context": {
                    "source_database": "FINDB",
                    "dbid": "123456789",
                    "hostname": "host1",
                    "snapshot_start": "2026-03-29 06:00",
                    "snapshot_end": "2026-03-29 07:00",
                    "last_snapshot": "2026-03-29 07:00",
                    "selected_scope_topology": "FINDB / host1",
                },
                "db_ingestion": {
                    "summary": {
                        "db_connectivity": "connected",
                        "db_load_mode": "reuse",
                        "already_loaded": 24,
                        "newly_loaded": 0,
                        "reused_awr_ids": 24,
                        "feature_vectors_existing": 24,
                        "feature_vectors_created_updated": 0,
                        "db_similarity_ready": True,
                    }
                },
                "report_rows": [
                    {
                        "file_name": f"sample_{index:02d}.out",
                        "parse_status": "success",
                        "db_status": "reused",
                        "awr_id": index,
                        "db_name": "FINDB",
                        "dbid": "123456789",
                        "instance_name": "FINDB1",
                        "host_name": "host1",
                        "snapshot_begin": "2026-03-29 06:00",
                        "snapshot_end": "2026-03-29 07:00",
                        "vector_status": "existing",
                        "similarity_eligible": True,
                        "parser_notes": "Optional IO section not present.",
                    }
                    for index in range(1, 25)
                ],
            },
            {
                "pattern_summary": [
                    {
                        "section_name": "io",
                        "unknown_type": "MISSING_EXPECTED_SECTION",
                        "count": 24,
                    }
                ],
                "summary": {"TOTAL": 24, "NEW": 23, "CLASSIFIED": 1},
            },
            {"items": []},
            {},
        )
        primary = rendered.split("screen1-historical-governance-evidence")[0]
        primary_visible = visible_screen1_text(primary)
        self.assertEqual(1, primary.count('data-screen1-backlog-item="true"'))
        self.assertIn("Optional IO section absence", primary)
        self.assertIn("24 persisted review records", primary)
        self.assertIn("Current run unknowns: 0", primary)
        self.assertIn("This is not a new runtime parser failure", primary)
        self.assertIn("How should this persisted parser signal be handled going forward?", primary)
        self.assertIn("Why this matters", primary)
        self.assertIn("How this is implemented", primary)
        self.assertIn("Persistence", primary)
        self.assertIn("What changes", primary)
        self.assertIn("What does not change", primary)
        self.assertIn("Future-run impact", primary)
        self.assertIn("Learning / ML impact", primary)
        self.assertIn(
            "This review turns repeated parser uncertainty into governed parser-improvement input.",
            primary,
        )
        self.assertIn(
            "This review does not change current or future runs by itself.",
            primary,
        )
        self.assertIn(
            "should review whether it can be materialized",
            primary,
        )
        self.assertIn(
            "This action does not directly change ML behavior or train a model.",
            primary,
        )
        self.assertIn(
            "may become learning/governance input",
            primary,
        )
        self.assertIn(
            "Submitting a parser governance review records reviewer context as DB-backed governed workflow state",
            primary,
        )
        self.assertIn(
            "DB-backed governed workflow metadata",
            primary,
        )
        self.assertIn(
            "does not update AWR_UNKNOWN_SIGNAL_HISTORY",
            primary,
        )
        self.assertIn(
            "create AWR_PARSER_MAPPING_CANDIDATE rows",
            primary,
        )
        self.assertIn("screen_6_fleet_overview.html", primary)
        self.assertGreater(
            primary.find("screen1-governance-explanation-panel"),
            primary.find("screen1-governance-boundary"),
        )
        self.assertGreater(
            primary.find("screen1-governance-boundary"),
            primary.find("screen1-operator-workflow"),
        )
        self.assertIn("Expected source profile", primary)
        self.assertIn("Parser expectation gap", primary)
        self.assertNotIn("Request parser mapping approval", primary)
        self.assertIn("No new AWR field mapping candidates are available for review.", primary)
        self.assertIn("No fake candidates are shown.", primary)
        self.assertNotIn("data-screen1-field-submit", primary)
        self.assertIn("Current Generated Run / Intake Evidence", primary)
        self.assertIn("Generated evidence reflects a generated dashboard artifact", primary)
        self.assertIn("No generated run evidence is available yet.", primary_visible)
        self.assertIn("No generated file/report rows are available yet.", primary_visible)
        self.assertIn('data-screen1-artifact-ready-region="true"', primary)
        self.assertIn('data-screen1-generated-artifact-ready="false"', primary)
        self.assertIn('data-screen1-artifact-ready-content="true"', primary)
        self.assertIn('data-screen1-generated-evidence-template="true"', primary)
        self.assertIn('data-screen1-full-report-table-template="true"', primary)
        self.assertIn("screen1-generated-evidence-group", primary)
        self.assertIn("screen1-generated-evidence-info-grid", primary)
        self.assertIn("info-box screen1-generated-evidence-info-box", primary)
        self.assertNotIn("screen1-generated-evidence-chip", primary)
        self.assertIn("Intake Result", primary)
        self.assertIn("Generated Time", primary)
        self.assertIn("Files Processed", primary)
        self.assertIn("Dataset Status", primary)
        self.assertIn("Source Database", primary)
        self.assertIn("DB / DBID", primary)
        self.assertIn("Database Version", primary)
        self.assertIn("Database Role", primary)
        self.assertIn("Operating System", primary)
        self.assertIn("Host / Instance", primary)
        self.assertIn("Platform / Topology Evidence", primary)
        self.assertIn("Platform", primary)
        self.assertIn("Selected Scope", primary)
        self.assertIn("Instance Count", primary)
        self.assertIn("RAC / Cluster Evidence", primary)
        self.assertIn("Data Guard / ADG Evidence", primary)
        self.assertIn("Topology Notes", primary)
        self.assertIn("Capacity Snapshot", primary)
        self.assertIn("Cumulative OCPUs / Cores", primary)
        self.assertIn("Memory per Instance", primary)
        self.assertIn("DB Load / Vector Status", primary)
        self.assertIn("Loaded / Reused AWR IDs", primary)
        self.assertIn("Feature Vectors", primary)
        self.assertIn("Similarity Ready", primary)
        self.assertIn("Snapshot Start / End", primary)
        self.assertIn("Parser / Source Profile Notes", primary)
        self.assertIn("Parser optional-section notes", primary)
        self.assertIn("Source-profile/parser-expectation review notes", primary)
        self.assertNotIn("Topology Detected", primary)
        self.assertNotIn("RAC Context", primary)
        self.assertNotIn("Version / Platform / Topology Hints", primary)
        self.assertNotIn("Report Inventory", primary)
        self.assertNotIn("Showing first", primary)
        self.assertNotIn("screen1-report-inventory-preview-wrap", primary)
        self.assertIn("Full File / Report Table", primary)
        self.assertIn("data-screen1-full-report-table-compact", primary)
        self.assertIn('data-screen3-table-id="screen1-full-report-table"', primary)
        self.assertIn("data-screen3-table-sort", primary)
        self.assertIn("data-screen3-table-filter", primary)
        self.assertIn("data-screen3-table-filter-toggle", primary)
        self.assertIn("data-screen3-table-count", primary)
        self.assertIn("data-screen3-table-sort-summary", primary)
        self.assertIn("data-screen3-table-filter-summary", primary)
        self.assertEqual(24, primary.count('data-screen1-full-report-row="true"'))
        self.assertNotIn("Unit run", primary_visible)
        self.assertNotIn("AWR ID:", primary_visible)
        self.assertIn("File Name", primary)
        self.assertIn("Parse / DB", primary)
        self.assertIn("AWR / Vector", primary)
        self.assertIn("DB / DBID", primary)
        self.assertIn("Host / Instance", primary)
        self.assertIn("Snapshot Window", primary)
        self.assertIn("AWR ID:", primary)
        self.assertNotIn("<th>File</th>", primary)
        self.assertNotIn("<th>DB Status</th>", primary)
        self.assertNotIn("<th>AWR_ID</th>", primary)
        self.assertNotIn("<th>AWR ID</th>", primary)
        self.assertNotIn("<th>Vector / Similarity</th>", primary)
        self.assertIn("Unknown Signals", primary)
        self.assertIn("data-screen1-parser-review-unknown-signals", primary)
        self.assertIn("screen1-unknown-signals-compact", primary)
        self.assertIn("Parser Review Status", primary)
        self.assertIn("Dominant Grouped Signal", primary)
        self.assertIn("New / Classified", primary)
        self.assertIn("Review Status", primary)
        self.assertIn(
            "Persisted parser governance backlog item, not a new runtime parser failure.",
            primary,
        )
        self.assertIn(
            "Use Parser Governance Backlog Review below to decide how this",
            primary,
        )
        self.assertNotIn("Review Backlog Summary", primary)
        self.assertNotIn("Grouped Unknown Signals", primary)
        self.assertNotIn("screen1-parser-review-summary-table", primary)
        self.assertIn("data-screen1-parser-health-template", primary)
        self.assertIn("data-screen1-parser-review-template", primary)
        self.assertIn("data-screen1-backlog-review-template", primary)
        self.assertIn("No parser health is available yet.", primary_visible)
        self.assertIn("No parser unknown-signal results are available yet.", primary_visible)
        self.assertIn("No parser governance backlog is available yet.", primary_visible)
        self.assertNotIn("24 validation notes were detected", primary_visible)
        self.assertNotIn("Persisted Review Records", primary_visible)
        self.assertNotIn("MISSING_EXPECTED_SECTION", primary_visible)
        self.assertNotIn("Optional IO section absence", primary_visible)
        self.assertNotIn("24 persisted review records", primary_visible)
        self.assertNotIn("Current run unknowns: 0", primary_visible)
        self.assertIn("Artifact Context", rendered)
        self.assertIn(
            "No knowledge artifacts are available for the current selected run/source context.",
            rendered,
        )
        self.assertIn("Knowledge artifacts are optional reviewer-assist context.", rendered)
        self.assertNotIn("static export", rendered)
        self.assertNotIn("static report", rendered)
        self.assertNotIn("Knowledge artifact data is not available", rendered)
        self.assertNotIn("Focused Diagnostic Meaning", rendered)
        self.assertNotIn("mixed CPU", rendered)
        self.assertNotIn("dominance threshold", rendered)
        self.assertIn("Runtime influence", primary)
        self.assertIn("Persistence", primary)
        self.assertIn("DB Record", primary)
        self.assertIn("Screen 6 / Learning Governance", primary)
        self.assertNotIn(">Not active<", primary)
        self.assertIn(
            "Not applied to current run; pending separate materialization/runtime-eligibility approval.",
            primary,
        )
        self.assertIn(
            "Queued for parser governance review. If accepted for implementation, this should proceed to Screen 6 learning/materialization governance before any future-run influence. No current runtime behavior changed.",
            (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
                encoding="utf-8",
                errors="ignore",
            ),
        )
        self.assertNotIn('data-action-type="knowledge_artifact_review"', primary)
        self.assertNotIn('data-action-type="knowledge_artifact_approve"', primary)
        self.assertNotIn('data-action-type="knowledge_artifact_reject"', primary)
        primary_visible = re.sub(r"<[^>]+>", " ", primary)
        primary_visible = " ".join(primary_visible.split()).lower()
        self.assertNotIn("phase 7", primary_visible)
        self.assertNotIn("7cn", primary_visible)
        self.assertNotIn("7cm", primary_visible)
        self.assertNotIn("preview only", primary_visible)


if __name__ == "__main__":
    unittest.main()
