from __future__ import annotations

import ast
import importlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"
README_PATH = DOCS / "README.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardScreen3ReAnalysisActionTests(unittest.TestCase):
    def test_01_dashboard_source_compiles(self) -> None:
        ast.parse(read_text(HTML_DASHBOARD_PATH), filename=str(HTML_DASHBOARD_PATH))

    def test_screen3_action_ui_exists(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required = (
            "Screen 3 Backend Re-Analysis Actions",
            "Analyze Selection",
            "Re-run Analysis",
            "Build Comparison",
            "Load From Object Storage",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_controls_are_disabled_preview_only(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required = (
            'aria-disabled="true"',
            "disabled/preview-only",
            "Execution disabled in this phase",
            "Preview only",
            "Selection is not execution",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_safety_labels_exist(self) -> None:
        rendered = self.render_screen3()

        required = (
            "No backend execution",
            "No run_analysis.py call",
            "No object storage call",
            "No local file read",
            "No DB lookup",
            "No Phase 4I mutation",
            "Deterministic runtime remains authoritative",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_unsafe_backend_calls(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH).lower()

        forbidden = (
            "fetch(",
            "xmlhttprequest",
            'method="post"',
            'action="/',
            'href="run_analysis.py',
            'src="run_analysis.py',
            "run_analysis.py(",
            "python scripts/run_analysis.py",
            "python3 scripts/run_analysis.py",
            "object storage execution call",
            "download_object(",
            "list_bucket(",
            "call_object_storage(",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, source)

    def test_source_modes_displayed(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required = (
            "Local staged",
            "Local file",
            "Existing run",
            "Object Storage",
            "Future EM Extract",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_request_preview_exists_and_remains_read_only(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required = (
            "Read-Only Request Preview",
            "Request preview is not execution",
            "Selected state summary remains read-only",
            "Preview does not imply execution",
            "execution_blocked=true",
            "can_execute=false",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_future_requirements_visible(self) -> None:
        rendered = self.render_screen3()

        required = (
            "AWR/report comparison is future 7AM.1 engine only and not triggered here",
            "Missing metric/evidence handling remains future 7AO.1 / 7AQ.1",
            "EM Extract implementation belongs to Phase 8",
            "Controlled adaptive execution requires future validation/gate",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_docs_exist_and_contain_required_boundaries(self) -> None:
        doc_paths = [
            DOCS / "phase7an_screen3_action_ui.md",
            DOCS / "phase7an_screen3_request_preview.md",
        ]
        for path in doc_paths:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())

        combined = "\n".join(read_text(path).lower() for path in doc_paths)
        required = (
            "no backend execution",
            "no run_analysis.py call",
            "no object storage call",
            "no local file read",
            "no db lookup",
            "no phase 4i mutation",
            "disabled/preview-only",
            "phase 8 sizing/tco is not implemented",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_readme_links_phase7an_docs(self) -> None:
        text = read_text(README_PATH)
        self.assertIn("phase7an_screen3_action_ui.md", text)
        self.assertIn("phase7an_screen3_request_preview.md", text)

    def render_screen3(self) -> str:
        return dashboard_module()._render_screen_3_selector_page(
            self.sample_screen3_model(),
            report_data=self.sample_report_data(),
        )

    @staticmethod
    def sample_screen3_model() -> dict[str, object]:
        return {
            "header": {
                "db_name": "ORCL",
                "dbid": "123456",
                "instance_name": "ORCL1",
                "host_name": "dbhost01",
                "window": "4 snapshots / 2 hours",
            },
            "selection_controls": {
                "db_dbid": "ORCL / 123456",
                "host_instance": "dbhost01 / ORCL1",
                "snapshot_window": "4 snapshots / 2 hours",
                "latest_interval": "Latest snapshot (10:00-11:00)",
                "worst_interval": "Worst interval (09:00-10:00)",
                "comparison_modes": ["history", "similar AWRs", "cluster", "fleet"],
                "active_comparison_mode": "history",
                "review_modes": ["diagnosis", "historical proof", "anomaly", "similarity", "fleet"],
                "active_review_mode": "historical proof",
            },
            "scope_selection": {
                "options": ["DBID", "DB name", "INSTANCE_NAME", "HOST_NAME", "fleet/global"],
                "active_scope": "ORCL / 123456",
            },
            "timeframe_selection": {
                "comparison_window": "4 snapshots / 2 hours",
                "start_end_period": "09:00 -> 11:00",
                "window_a": "Latest snapshot (10:00-11:00)",
                "window_b": "Worst interval (09:00-10:00)",
                "comparison_mode": "Latest interval vs broader comparison window",
                "latest_vs_prior": "Latest interval aligns with the broader window.",
            },
            "review_mode": {
                "options": ["diagnosis", "historical proof", "anomaly", "similarity", "fleet"],
                "active_mode": "historical proof",
            },
            "current_selection_summary": {
                "scope": "ORCL / 123456",
                "timeframe": "4 snapshots / 2 hours",
                "review_mode": "historical proof",
            },
        }

    @staticmethod
    def sample_report_data() -> dict[str, object]:
        return {
            "metadata": {
                "awr_id": 7001,
                "db_name": "ORCL",
                "dbid": "123456",
                "instance_name": "ORCL1",
                "host_name": "dbhost01",
            },
            "run_history_id": 42,
            "snapshot_labels": ["snap-1", "snap-2"],
            "screen_models": {
                "screen_2_analysis": {
                    "normalized_decision": {
                        "primary_issue": "CPU",
                        "overall_status": "WARNING",
                        "display_severity_label": "High",
                    },
                    "decision_summary": {
                        "primary_issue": "CPU",
                        "overall_status": "WARNING",
                        "display_severity_label": "High",
                    },
                }
            },
            "comparison_context": {
                "comparison_window": "4 snapshots / 2 hours",
                "latest_snapshot_summary": "Latest snapshot (10:00-11:00)",
                "worst_snapshot_summary": "Worst interval (09:00-10:00)",
                "latest_vs_trend": "Latest interval aligns with the broader window.",
            },
        }


if __name__ == "__main__":
    unittest.main()
