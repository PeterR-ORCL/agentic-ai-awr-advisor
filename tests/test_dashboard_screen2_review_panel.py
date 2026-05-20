from __future__ import annotations

import importlib
import inspect
from pathlib import Path
import py_compile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"
GENERATED_SCREEN2_PATH = ROOT / "awr_dashboard" / "screen_2_analysis.html"
PANEL_DOC = DOCS / "phase7as_screen2_review_panel.md"
PREVIEW_DOC = DOCS / "phase7as_screen2_review_request_preview.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardScreen2ReviewPanelTests(unittest.TestCase):
    def test_dashboard_source_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_screen2_evidence_focus_panel_exists_without_submit_controls(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen2()
        combined = source + "\n" + rendered

        required = (
            "Focused Diagnostic Meaning",
            "Selected Focus Summary",
            "screen2-focus-summary-compact",
            "Evidence focus only",
            "For deeper historical evidence, trend, anomaly, and similarity review, continue to Screen 4.",
            "Deterministic output remains authoritative",
            "LLM-style wording may explain",
            "Generate Focused Explanation",
            "No workflow request, audit record, governance record",
            "/phase7/dashboard/screen2/explanation",
            "screen2-focused-explanation-panel",
            "screen2-focused-explanation-list",
            "screen2-focused-explanation-item",
            "Use Domain to choose the high-level diagnostic lens.",
            "Active domain lens",
            "Active explanation focus",
            "Focus type",
            "PHASE7_SCREEN2_EXPLANATION_PROVIDER_MODE",
            "provider_mode: providerMode",
            "The selected CPU signal shows CPU pressure",
            "The selected I/O signal shows User I/O Pressure",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

        forbidden = (
            "Submit Governed Diagnostic Review Request",
            "Review disposition",
            "Reviewer note / rationale",
            "request_governed_diagnostic_review",
            'data-action-type="diagnostic_review"',
        )
        for phrase in forbidden:
            with self.subTest(forbidden=phrase):
                self.assertNotIn(phrase, rendered)

    def test_evidence_focus_panel_is_not_submit_form(self) -> None:
        rendered = self.render_screen2()

        self.assertIn("Overall deterministic result", rendered)
        self.assertIn("Evidence focus only", rendered)
        self.assertIn("Deterministic diagnosis, scoring, recommendations", rendered)
        self.assertIn(
            "Selection changes only the local explanation focus. It does not change diagnosis, scoring, recommendations, parser output, runtime behavior, ML behavior, materialization, runtime eligibility, or future-run behavior.",
            rendered,
        )
        self.assertIn("Calls the local dashboard explanation service for wording only", rendered)
        self.assertIn(
            "Generate Focused Explanation refreshes explanatory wording only when the operator explicitly requests it.",
            rendered,
        )
        self.assertIn("Diagnosis, score, confidence, and recommendation changes require deterministic analysis", rendered)
        self.assertNotIn('aria-disabled="true"', rendered)
        self.assertNotIn("Reviewer required before submit.", rendered)
        self.assertNotIn("No reviewer note entered.", rendered)

    def test_required_safety_labels_exist(self) -> None:
        rendered = self.render_screen2()

        for phrase in (
            "The deterministic diagnosis, score, confidence, recommendation",
            "Deterministic diagnosis, scoring, recommendations",
            "runtime eligibility, future-run behavior",
            "governed service behavior remain unchanged",
            "DB/governance/audit state remain unchanged",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_unsafe_backend_calls_or_raw_submit_controls(self) -> None:
        source = inspect.getsource(dashboard_module()._render_screen2_review_panel).lower()
        rendered = self.render_screen2().lower()
        combined = source + "\n" + rendered

        forbidden = (
            "xmlhttprequest",
            'method="post"',
            'action="/"',
            "execute_governance",
            "call_governance",
            "persist_governance",
            "create_candidate(",
            "write_review",
            "type=\"submit\"",
            "<form",
            "submit governed",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)

    def test_screen2_evidence_focus_has_no_governed_submit_control(self) -> None:
        source = inspect.getsource(dashboard_module()._render_screen2_review_panel).lower()
        rendered = self.render_screen2().lower()
        combined = source + "\n" + rendered

        self.assertIn("generate focused explanation", combined)
        self.assertIn('data-screen2-generate-explanation="true"', combined)
        self.assertNotIn('role="button"', rendered)
        self.assertNotIn('data-phase7-action-control="true"', rendered)
        self.assertNotIn('data-action-type="diagnostic_review"', rendered)
        self.assertNotIn('aria-disabled="true"', source)

    def test_review_target_summary_exists_as_explanation_focus(self) -> None:
        rendered = self.render_screen2()
        source = read_text(HTML_DASHBOARD_PATH)

        self.assertIn("Selected Focus Summary", rendered)
        self.assertIn("Overall deterministic result", rendered)
        self.assertIn("Active domain lens", rendered)
        self.assertIn("Active evidence group", rendered)
        self.assertIn("Active metric / wait / SQL", rendered)
        self.assertIn("Active diagnostic section", rendered)
        self.assertIn("Active explanation focus", rendered)
        self.assertIn("Focus type", rendered)
        self.assertIn("screen2-focus-summary-compact", rendered)
        self.assertIn("Deterministic context", rendered)
        self.assertIn("selectedDomain", rendered)
        self.assertIn("selectedEvidenceGroup", rendered)
        self.assertIn("selectedMetricGroup", rendered)
        self.assertIn("selectedWaitEventGroup", rendered)
        self.assertIn("selectedSqlSignal", rendered)
        self.assertIn("selectedDiagnosticSection", rendered)
        self.assertIn("Only local explanation focus can change on this screen.", rendered)
        self.assertIn("Only the local evidence focus and explanation wording change.", source)
        self.assertNotIn("review submitted", rendered.lower())
        self.assertNotIn("submitted successfully", rendered.lower())

    def test_generated_focus_summary_outcome_rows_use_aligned_pills(self) -> None:
        generated = read_text(GENERATED_SCREEN2_PATH)
        source = read_text(HTML_DASHBOARD_PATH)
        combined = generated + "\n" + source

        self.assertIn(
            '<div class="screen2-outcome-row"><dt>Decision posture</dt><dd data-screen2-focus="decision_posture"><span class="status-pill warning">TUNE FIRST</span></dd></div>',
            generated,
        )
        self.assertIn(
            '<div class="screen2-outcome-row"><dt>Severity</dt><dd data-screen2-focus="severity"><span class="status-pill success">OK</span></dd></div>',
            generated,
        )
        self.assertIn(
            '<div class="screen2-outcome-row"><dt>Confidence</dt><dd data-screen2-focus="confidence"><span class="confidence-pill low">LOW</span></dd></div>',
            generated,
        )
        self.assertIn(".screen2-selected-evidence-card .screen2-outcome-row", combined)
        self.assertIn("align-items: center;", combined)
        self.assertIn(".screen2-selected-evidence-card .screen2-outcome-row .status-pill", combined)
        self.assertIn(".screen2-selected-evidence-card .screen2-outcome-row .confidence-pill", combined)
        self.assertIn("min-width: 72px", combined)

    def test_review_request_status_absent(self) -> None:
        rendered = self.render_screen2().lower()
        panel = rendered[rendered.index('id="screen2-evidence-focus-panel"') :]

        for phrase in (
            "request / audit result",
            "review disposition",
            "reviewer required",
            "reviewer note / rationale",
            "accepted/rejected status",
            "request id",
            "technical audit record",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, panel)

        self.assertIn("focus type", panel)
        self.assertNotIn("Current AWR / Run Context", rendered)
        self.assertNotIn("static export", rendered)

    def test_docs_exist_and_contain_required_boundaries(self) -> None:
        self.assertTrue(PANEL_DOC.is_file(), PANEL_DOC)
        self.assertTrue(PREVIEW_DOC.is_file(), PREVIEW_DOC)

        text = (read_text(PANEL_DOC) + "\n" + read_text(PREVIEW_DOC)).lower()
        for phrase in (
            "non-submitting screen 2 evidence-focus workflow",
            "no diagnostic truth mutation",
            "no direct diagnostic truth mutation",
            "no candidate created automatically",
            "deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

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
        }


if __name__ == "__main__":
    unittest.main()
