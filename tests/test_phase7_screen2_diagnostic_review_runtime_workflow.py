"""Tests for the 7CO Screen 2 diagnostic review runtime workflow."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_screen2_validator():
    path = ROOT / "scripts" / "run_phase7_screen2_diagnostic_review_workflow_validation.py"
    spec = importlib.util.spec_from_file_location("phase7_screen2_validator", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load validator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class Phase7Screen2DiagnosticReviewRuntimeWorkflowTest(unittest.TestCase):
    def test_primary_screen2_workflow_markup_exists(self) -> None:
        rendered = self.render_screen2()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for phrase in (
            "Diagnostic Snapshot",
            "Why This Posture",
            "Current Diagnostic Drivers",
            "Visual Summary",
            "Health / Data Completeness",
            "Selected-Scope Explanation",
            "Diagnostic Conclusion",
            "Similarity Context",
            "Interactive Evidence Focus",
            "Focused Diagnostic Meaning",
            "Selected Focus Summary",
            "screen2-focus-summary-compact",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        self.assertLess(rendered.index("Similarity Context"), rendered.index("Interactive Evidence Focus"))
        self.assertLess(
            rendered.index("Interactive Evidence Focus"),
            rendered.index("Focused Diagnostic Meaning"),
        )

    def test_product_copy_locks_deterministic_truth(self) -> None:
        rendered = self.render_screen2()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for phrase in (
            "Purpose",
            "What changes",
            "What does not change",
            "How to use this",
            "For deeper historical evidence, trend, anomaly, and similarity review, continue to Screen 4.",
            "Diagnostic meaning",
            "Deterministic diagnosis, scoring,",
            "Only local explanation focus can change on this screen.",
            "Deterministic output remains authoritative",
            "LLM-style wording may explain",
            "Generate Focused Explanation",
            "No workflow request, audit record, governance record",
            "Provider mode:",
            "Use Domain to choose the high-level diagnostic lens.",
            "Related selections stay grouped",
            "Active domain lens",
            "Active explanation focus",
            "Focus type",
            "href=\"screen_4_historical_review.html\"",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        for phrase in (
            "The selected CPU signal shows CPU pressure",
            "DB CPU % DB Time =",
            "The selected I/O signal shows User I/O Pressure",
            "The selected MEMORY signal shows PGA Spill Pressure",
            "The selected COMMIT signal shows commit latency",
            "The selected RAC signal shows cluster wait context",
            "ADG / redo transport evidence is present as topology/context",
            "Not domain-specific",
            "Explanation provider service is not running. Start the dashboard workflow service and try again. The deterministic explanation remains available.",
            "Explanation endpoint is not available in the dashboard workflow service. The deterministic explanation remains available.",
            "screen2ExplanationViolatesBoundary",
            "/phase7/dashboard/screen2/explanation",
            "screen2_explanation_provider_mode",
            "PHASE7_SCREEN2_EXPLANATION_PROVIDER_MODE",
            "SCREEN2_EXPLANATION_PROVIDER_MODE",
            "provider_mode: providerMode",
            "allowed_screen2_changes",
            "DB/governance/audit state",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)

        self.assertNotIn("Confidence is displayed from the authoritative Phase 4I output", rendered)
        self.assertIn("Deterministic output remains authoritative", rendered)
        self.assertNotIn("Selected Evidence Summary", rendered)
        self.assertNotIn("Current diagnosis", rendered)
        self.assertNotIn("Cross-Screen Selection Propagation", rendered)
        self.assertNotIn("static export", rendered)
        self.assertNotIn("static report", rendered)
        self.assertNotIn("Current AWR / Run Context", rendered)
        self.assertNotIn("<strong>Current AWR</strong>", rendered)
        self.assertNotIn("<strong>Current confidence</strong>", rendered)

    def test_selector_cards_do_not_repeat_identical_labels(self) -> None:
        rendered = self.render_screen2()

        self.assertIn("screen2-selector-kicker", rendered)
        self.assertNotIn("<strong>CPU</strong>\n        <span>CPU</span>", rendered)
        self.assertNotIn("<strong>COMMIT</strong>\n        <span>COMMIT</span>", rendered)

    def test_screen2_does_not_expose_review_submission_controls(self) -> None:
        rendered = self.render_screen2()

        for forbidden in (
            "confirm_evidence_reviewed",
            "flag_insufficient_evidence",
            "dispute_diagnostic_interpretation",
            "add_reviewer_note",
            "request_governed_diagnostic_review",
            "Submit Governed Diagnostic Review Request",
            "Review disposition",
            "Reviewer note / rationale",
            "Request / Audit Result",
            'data-action-type="diagnostic_review"',
            'data-workflow-type="screen2_diagnostic_review_evidence_validation"',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)

        for forbidden in (
            "needs_parser_review",
            "needs_scoring_review",
            "needs_recommendation_review",
            "needs_learning_candidate",
            "execute_reanalysis",
            "promote_candidate",
            "materialize_rule",
            "change_runtime_eligibility",
            "capture_recommendation_outcome",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)

    def test_generation_is_explicit_non_submitting_and_provider_safe(self) -> None:
        rendered = self.render_screen2()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for phrase in (
            'data-screen2-generate-explanation="true"',
            "Generate Focused Explanation",
            "handleScreen2GenerateExplanationClick",
            "screen2GeneratedExplanationText",
            "dashboardScreen2ExplanationProvider",
            "SCREEN2_EXPLANATION_ENDPOINT",
            "window.fetch(SCREEN2_EXPLANATION_ENDPOINT",
            "screen_id: 'screen_2'",
            "provider_mode: providerMode",
            "providerMode === 'off'",
            "screen2ExplanationViolatesBoundary",
            "Only explanatory text changed; platform truth and runtime behavior remain unchanged.",
            "no provider call or platform state change was created.",
            "Explanation provider service is not running. Start the dashboard workflow service and try again. The deterministic explanation remains available.",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered + source)

        for forbidden in (
            "Submit Focused Explanation",
            "Apply Focused Explanation",
            "Approve Focused Explanation",
            "Save Focused Explanation",
            "Queue Focused Explanation",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)

        self.assertIn("SCREEN2_FOCUS_STATE_KEYS", source)
        self.assertIn("SCREEN2_FOCUS_ITEM_STATE_KEYS", source)
        self.assertIn("screen2ActiveFocusKey", source)
        self.assertIn("screen2ActiveFocusLabel", source)
        self.assertIn("screen2ActiveEvidenceGroup", source)
        self.assertIn("screen2ActiveMetric", source)
        self.assertIn("screen2ActiveWaitEvent", source)
        self.assertIn("screen2ActiveDiagnosticSection", source)
        self.assertIn("screen2InferredDomain", source)
        self.assertIn("nextState.selectedDomain = inferredDomain", source)
        self.assertIn("screen2EnsureEvidenceParentForDomain(nextState, inferredDomain)", source)
        self.assertIn("screen2ClearIncompatibleFocusContext(nextState, inferredDomain, key)", source)
        self.assertIn("nextState.screen2InferredDomain = inferredDomain || 'Not domain-specific'", source)
        self.assertIn("key === 'selectedDiagnosticSection'", source)
        self.assertNotIn("SCREEN2_FOCUS_ITEM_STATE_KEYS.forEach(function (focusKey)", source)
        self.assertNotIn("nextState.selectedDomain = ''", source)
        self.assertNotIn("dashboardScreen2ExplanationProvider(context)", source[source.index("function selectDashboardElement"):source.index("function handleDashboardStateInput")])

    def test_generated_provider_mode_is_configurable(self) -> None:
        report_data = self.sample_report_data()
        report_data["screen2_explanation_provider_mode"] = "mock"
        rendered = dashboard_module()._render_screen_2_page(
            self.sample_screen2_model(),
            ai_sections={},
            decision_state={},
            report_data=report_data,
        )

        self.assertIn('data-screen2-explanation-provider-mode="mock"', rendered)
        self.assertIn("Provider mode: MOCK", rendered)

        report_data["screen2_explanation_provider_mode"] = "off"
        rendered_off = dashboard_module()._render_screen_2_page(
            self.sample_screen2_model(),
            ai_sections={},
            decision_state={},
            report_data=report_data,
        )
        self.assertIn('data-screen2-explanation-provider-mode="off"', rendered_off)

    def test_screen2_explanation_backend_endpoint_is_non_mutating(self) -> None:
        service = importlib.import_module("scripts.dashboard_workflow_service")
        payload = {
            "screen_id": "screen_2",
            "request_type": "screen2_focused_explanation",
            "provider_mode": "mock",
            "selected_focus": "COMMIT",
            "target_type": "diagnostic_domain",
            "inferred_domain": "COMMIT",
            "decision_posture": "TUNE FIRST",
            "primary_issue_domain": "No dominant scored domain selected",
            "severity": "OK",
            "confidence": "LOW",
            "deterministic_facts": "log file sync = 8.4",
            "non_mutating_explanation_only": True,
        }

        result = service.generate_screen2_explanation(payload)

        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["provider_mode"], "mock")
        self.assertFalse(result["records_created"])
        self.assertIsNone(result["audit_reference"])
        self.assertIn("COMMIT", result["explanation"])
        self.assertIn("Deterministic values remain unchanged", result["message"])

        rejected = service.generate_screen2_explanation({**payload, "action_type": "diagnostic_review"})
        self.assertEqual(rejected["status"], "rejected")
        self.assertFalse(rejected["records_created"])

        provider_off = service.generate_screen2_explanation({**payload, "provider_mode": "off"})
        self.assertEqual(provider_off["status"], "provider_off")
        self.assertFalse(provider_off["records_created"])

    def test_workflow_service_health_endpoint_metadata_is_read_only(self) -> None:
        service = importlib.import_module("scripts.dashboard_workflow_service")

        self.assertEqual(service.HEALTH_ENDPOINT_PATH, "/phase7/dashboard/health")
        self.assertIn(service.HEALTH_ENDPOINT_PATH, service.SUPPORTED_ENDPOINT_PATHS)
        self.assertIn("off", service.SCREEN2_EXPLANATION_PROVIDER_MODES)
        self.assertIn("mock", service.SCREEN2_EXPLANATION_PROVIDER_MODES)
        self.assertIn("oci", service.SCREEN2_EXPLANATION_PROVIDER_MODES)

        service_source = (ROOT / "scripts" / "dashboard_workflow_service.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        self.assertIn("def do_GET", service_source)
        self.assertIn("mutates_runtime_truth", service_source)
        self.assertIn("creates_screen2_records", service_source)

    def test_old_preview_review_panels_are_not_primary_ui(self) -> None:
        rendered = self.render_screen2()

        for forbidden in (
            "Phase 7H.3",
            "Phase 7AS",
            "Screen 2 Diagnostic Review / Approval Panel",
            "Review Action Preview Controls",
            "Review Request Preview",
            "Preview only. Review action disabled",
            "Request Parser Review",
            "Request Scoring Review",
            "Request Recommendation Review",
            "Request Learning Candidate",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)

    def test_validator_accepts_rendered_screen2_contract(self) -> None:
        validator = load_screen2_validator()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        contract = (ROOT / "src" / "learning" / "dashboard_runtime_interaction.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        service = (ROOT / "scripts" / "dashboard_workflow_service.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        result = validator.validate_screen2_diagnostic_review(
            generated_text=self.render_screen2(),
            source_text=source,
            contract_text=contract,
            service_text=service,
            generated_exists=True,
        )
        self.assertTrue(result["screen2_diagnostic_review_ready"], result["failures"])
        self.assertTrue(result["product_sections_ready"])
        self.assertTrue(result["interactive_evidence_review_ready"])
        self.assertTrue(result["evidence_focus_ready"])
        self.assertTrue(result["screen2_submission_absent_ready"])

    def render_screen2(self) -> str:
        return dashboard_module()._render_screen_2_page(
            self.sample_screen2_model(),
            ai_sections={},
            decision_state={},
            report_data=self.sample_report_data(),
        )

    @staticmethod
    def sample_screen2_model() -> dict[str, object]:
        return {
            "decision_summary": {
                "overall_status": "WARNING",
                "display_severity_label": "High",
                "decision_posture": "TUNE FIRST",
                "primary_issue": "CPU",
                "confidence": 0.82,
                "health_summary": "CPU pressure visible.",
                "historical_posture": "TUNE FIRST",
            },
            "normalized_decision": {
                "primary_issue": "CPU",
                "secondary_issues": ["COMMIT"],
                "overall_status": "WARNING",
                "display_severity_label": "High",
                "confidence": 0.82,
                "domain_scores": {"CPU": 72.0, "IO": 18.0, "COMMIT": 12.0},
            },
            "health_check": {
                "summary_status": "WARNING",
                "rows": [
                    {"check": "DATA COMPLETENESS", "status": "OK", "observed_value": "Signals present"},
                    {"check": "CPU", "status": "OK", "observed_value": "72"},
                ],
            },
            "visual_summary": {
                "cpu": {
                    "card_title": "CPU",
                    "selected_label": "DB CPU % DB Time",
                    "status": "ok",
                    "series": [40.0, 72.0],
                    "labels": ["snap-1", "snap-2"],
                    "reason": "Visible CPU pressure.",
                },
                "io": {
                    "card_title": "IO",
                    "selected_label": "User I/O % DB Time",
                    "status": "weak",
                    "series": [5.0, 8.0],
                    "labels": ["snap-1", "snap-2"],
                    "reason": "Weak I/O signal.",
                },
            },
            "technical_sections": [
                {"title": "Trend Findings", "items": ["CPU remained visible."]},
                {"title": "Latest Snapshot Assessment", "items": ["Latest interval reviewed."]},
            ],
            "root_cause_interpretation": {},
            "trend_context": {},
            "anomaly_context": {"anomaly_summary": {"count": 1}},
            "explanation_panel": {},
        }

    @staticmethod
    def sample_report_data() -> dict[str, object]:
        return {
            "metadata": {"awr_id": 7001, "db_name": "ORCL", "dbid": "123456"},
            "scores": {"domain_scores": {"CPU": 72.0, "IO": 18.0, "COMMIT": 12.0}},
            "time_series_charts": {
                "snapshot_labels": ["snap-1", "snap-2"],
                "log_file_sync_trend": [1.5, 2.4],
            },
            "wait_events": [
                {"event_name": "DB CPU"},
                {"event_name": "log file sync"},
            ],
            "top_sql": [
                {"sql_id": "abc123", "sql_text": "select * from orders"},
            ],
            "decision": {"primary_issue": "CPU"},
        }


if __name__ == "__main__":
    unittest.main()
