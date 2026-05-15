from __future__ import annotations

import importlib
from pathlib import Path
import py_compile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"
PANEL_DOC = DOCS / "phase7as_screen2_review_panel.md"
PREVIEW_DOC = DOCS / "phase7as_screen2_review_request_preview.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardScreen2ReviewPanelTests(unittest.TestCase):
    def test_dashboard_source_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_screen2_review_panel_exists_with_preview_controls(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen2()
        combined = source + "\n" + rendered

        required = (
            "Screen 2 Diagnostic Review / Approval Panel",
            "Confirm Evidence",
            "Dispute Evidence",
            "Mark Insufficient Evidence",
            "Request Parser Review",
            "Request Scoring Review",
            "Request Recommendation Review",
            "Request Learning Candidate",
            "Add Reviewer Note",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_controls_are_disabled_preview_only(self) -> None:
        rendered = self.render_screen2()

        self.assertIn('aria-disabled="true"', rendered)
        self.assertIn('data-preview-only="true"', rendered)
        self.assertIn("Review action disabled in this phase", rendered)
        self.assertIn("Preview only", rendered)
        self.assertIn("Review is not mutation", rendered)

    def test_required_safety_labels_exist(self) -> None:
        rendered = self.render_screen2()

        for phrase in (
            "Does not change diagnostic truth",
            "Does not change primary issue",
            "Does not change severity",
            "Does not change confidence",
            "Does not change score",
            "Does not change parser output",
            "Does not change recommendation truth",
            "Does not mutate Phase 4I",
            "No backend write",
            "No governed write path invoked",
            "No candidate created automatically",
            "Deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_unsafe_backend_calls_or_submit_controls(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH).lower()
        rendered = self.render_screen2().lower()
        combined = source + "\n" + rendered

        forbidden = (
            "fetch(",
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
            "<button",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)

    def test_review_target_summary_exists_without_submission_claim(self) -> None:
        rendered = self.render_screen2()

        self.assertIn("Review Target Summary", rendered)
        self.assertIn("Review target summary section", rendered)
        self.assertIn("selected diagnostic/evidence context", rendered)
        self.assertIn("selectedDomain", rendered)
        self.assertIn("selectedEvidenceGroup", rendered)
        self.assertIn("selectedMetricGroup", rendered)
        self.assertIn("selectedWaitEventGroup", rendered)
        self.assertIn("selectedSqlSignal", rendered)
        self.assertIn("selectedDiagnosticSection", rendered)
        self.assertIn("safe empty state", rendered.lower())
        self.assertIn("does not imply submission occurred", rendered)
        self.assertNotIn("review submitted", rendered.lower())
        self.assertNotIn("submitted successfully", rendered.lower())

    def test_review_request_preview_exists(self) -> None:
        rendered = self.render_screen2().lower()

        for phrase in (
            "review request preview",
            "target type",
            "review decision",
            "actor required",
            "audit required",
            "governed write path required",
            "governance bridge required",
            "candidate intent possible",
            "write_performed=false",
            "runtime_influence=false",
            "phase4i_mutation_requested=false",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_docs_exist_and_contain_required_boundaries(self) -> None:
        self.assertTrue(PANEL_DOC.is_file(), PANEL_DOC)
        self.assertTrue(PREVIEW_DOC.is_file(), PREVIEW_DOC)

        text = (read_text(PANEL_DOC) + "\n" + read_text(PREVIEW_DOC)).lower()
        for phrase in (
            "no review execution",
            "no diagnostic truth mutation",
            "no governed write path invoked",
            "no candidate created automatically",
            "all controls are disabled/preview-only",
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
