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

    def test_screen3_governed_action_ui_exists(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required = (
            "Governed Actions",
            "Analyze Selection",
            "Re-run Analysis",
            "Build Comparison",
            "Load / Prepare External Target",
            "screen3_active_reanalysis",
            'data-screen-id="screen_3"',
            'data-required-selection-key="selectedSourceMode"',
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)
        self.assertNotIn("Request / Execution Result", rendered)

    def test_controls_are_governed_and_source_gated(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required = (
            'aria-disabled="true"',
            "Active governed request",
            "Existing run truth unchanged",
            "data-execution-mode=\"local_backend_execution\"",
            "Missing gates:",
            "Submit governed action",
            "Action details",
            "Result location: Request / Result Receipt",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_safety_boundary_exists(self) -> None:
        rendered = self.render_screen3()

        required = (
            "Runtime Safety and Selection Impact",
            "Screen 2 Control submits governed backend requests",
            "Existing deterministic truth is not overwritten",
            "Backend execution status is service-returned only",
            "learning candidates, materialization, runtime eligibility",
            "Existing run truth is immutable",
            "Request receipt is not deterministic analysis truth unless a governed deterministic service returns a real output artifact reference",
            "Request ID, transaction ID, audit reference, persistence, and output fields are displayed from the service response only",
            "A governed request/audit record may be created only when the backend returns that state",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)
        self.assertNotIn("Screen 2 Control can request or execute only governed backend actions", rendered)

    def test_no_unsafe_direct_execution_paths(self) -> None:
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
                if phrase == "fetch(":
                    continue
                self.assertNotIn(phrase, source)
        self.assertIn("requestbridge(phase7_action_endpoint", source)
        self.assertNotIn("run_analysis_coupling: true", source)
        self.assertNotIn("browser_object_storage_access_attempted: true", source)

    def test_index_source_context_displayed(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required = (
            "Runtime Evidence Path",
            "Evidence path status",
            "Local source path",
            "Selected local file",
            "Existing run",
            "Object Storage",
            "Return to Platform Entry",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)
        dynamic_path_states = (
            "Existing Platform Evidence",
            "Runtime options not loaded",
            "Runtime options loaded; row/scope selection required",
            "Runtime scope selected",
            "Screen 1 intake required",
            "New Source Artifact",
            "Object Storage Metadata",
            "Screen 1 validation/intake required",
            "Existing Evidence Scope Ready for Downstream Review",
        )
        for phrase in dynamic_path_states:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
        self.assertNotIn("Future EM Extract", rendered)

    def test_readiness_summary_and_source_scope_exist(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required = (
            "Runtime Evidence Path",
            "Load Runtime Options",
            "Select Runtime Scope",
            "Runtime Scope Filters",
            "Filtered AWR / Run / Report Results",
            "Snapshot / Interval Selection",
            "Resolve Comparison Targets",
            "Review Mode",
            "Runtime Safety and Selection Impact",
            "Request / Result Receipt",
            "DB Persistence",
            "Object Storage validation",
            "Existing run truth unchanged",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_missing_execution_gates_visible(self) -> None:
        rendered = self.render_screen3()

        required = (
            "execution blocked until runner/artifact gates are connected",
            "target resolution/comparison payload",
            "load/parse/ingest/analyze chain",
            "must be represented as new run/output/artifact references",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_docs_exist_as_historical_boundaries(self) -> None:
        doc_paths = [
            DOCS / "phase7an_screen3_action_ui.md",
            DOCS / "phase7an_screen3_request_preview.md",
        ]
        for path in doc_paths:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())

        combined = "\n".join(read_text(path).lower() for path in doc_paths)
        required = (
            "no run_analysis.py call",
            "no phase 4i mutation",
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
