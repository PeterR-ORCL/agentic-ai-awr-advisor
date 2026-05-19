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
            "Review persisted parser signals and submit a governed backlog review request.",
            source,
        )
        self.assertIn("Optional IO section absence", source)
        self.assertIn("New AWR Field Mapping Candidates", source)
        self.assertIn(
            "No new AWR field mapping candidates are available for review.",
            source,
        )
        self.assertIn("Run / Intake Report", source)
        self.assertNotIn("Report Inventory", source)
        self.assertNotIn("data-screen1-report-inventory-summary", source)
        self.assertNotIn("screen1-report-inventory-preview-wrap", source)
        self.assertIn("<div class=\"section-kicker\">INGESTION</div>", source)
        self.assertIn("<div class=\"section-kicker\">REPORTS</div>", source)
        self.assertIn("<div class=\"section-kicker\">PARSER HEALTH</div>", source)
        self.assertIn("Parse Confidence", source)
        self.assertIn("Full File / Report Table", source)
        self.assertIn("data-screen1-full-report-table", source)
        self.assertIn("data-screen1-full-report-table-compact", source)
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
        self.assertIn("Historical / Debug Evidence", source)
        self.assertIn("Governance Boundary", source)
        self.assertIn("data-screen1-backlog-decision", source)
        self.assertIn("data-screen1-backlog-reviewer", source)
        self.assertIn("data-screen1-backlog-rationale", source)
        self.assertIn("data-screen1-backlog-submit", source)
        self.assertIn("data-screen1-governance-result-panel", source)
        self.assertIn("Submit Governed Backlog Review Request", source)
        self.assertIn("formState.selected", source)
        self.assertIn("formState.decision", source)
        self.assertIn("formState.reviewer", source)
        self.assertIn("formState.rationale", source)
        self.assertIn("parser_unknown_review", source)
        self.assertNotIn("No API calls", source)

    def test_service_accepts_valid_screen1_review_request(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        with tempfile.TemporaryDirectory() as tempdir:
            result = process_dashboard_action(
                valid_screen1_request(),
                queue_dir=Path(tempdir),
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
        self.assertEqual(1, primary.count('data-screen1-backlog-item="true"'))
        self.assertIn("Optional IO section absence", primary)
        self.assertIn("24 persisted review records", primary)
        self.assertIn("Current run unknowns: 0", primary)
        self.assertIn("This is not a new runtime parser failure", primary)
        self.assertIn("How should this persisted parser signal be handled going forward?", primary)
        self.assertIn("Expected source profile", primary)
        self.assertIn("Parser expectation gap", primary)
        self.assertNotIn("Request parser mapping approval", primary)
        self.assertIn("No new AWR field mapping candidates are available for review.", primary)
        self.assertNotIn("data-screen1-field-submit", primary)
        self.assertIn("Run / Intake Report", primary)
        self.assertNotIn("Report Inventory", primary)
        self.assertNotIn("Showing first", primary)
        self.assertNotIn("screen1-report-inventory-preview-wrap", primary)
        self.assertIn("Full File / Report Table", primary)
        self.assertIn("data-screen1-full-report-table-compact", primary)
        self.assertEqual(24, primary.count('data-screen1-full-report-row="true"'))
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
        self.assertIn("Artifact Context", rendered)
        self.assertIn("Runtime influence", primary)
        self.assertIn("Not active", primary)
        self.assertNotIn('data-action-type="knowledge_artifact_review"', primary)
        self.assertNotIn('data-action-type="knowledge_artifact_approve"', primary)
        self.assertNotIn('data-action-type="knowledge_artifact_reject"', primary)
        self.assertNotIn("Phase 7", primary)
        self.assertNotIn("7CN", primary)
        self.assertNotIn("7CM", primary)
        primary_visible = re.sub(r"<[^>]+>", " ", primary)
        primary_visible = " ".join(primary_visible.split()).lower()
        self.assertNotIn("preview only", primary_visible)


if __name__ == "__main__":
    unittest.main()
