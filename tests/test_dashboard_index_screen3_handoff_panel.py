from __future__ import annotations

import importlib
import inspect
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardIndexScreen3HandoffPanelTests(unittest.TestCase):
    def test_html_dashboard_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_panel_exists(self) -> None:
        rendered = self.render_home()
        self.assertIn('id="index-screen3-handoff-panel"', rendered)
        self.assertIn("Index to Screen 3 Selection Handoff Preview", rendered)
        self.assertIn('data-phase="7BT"', rendered)
        self.assertIn('data-preview-only="true"', rendered)

    def test_safety_labels_exist(self) -> None:
        rendered = self.render_home()
        for phrase in (
            "Preview only",
            "Handoff is not active in this phase",
            "No Screen 3 state update",
            "No backend request created",
            "No object storage call",
            "No local file read",
            "No DB lookup",
            "No run_analysis.py call",
            "Future EM Extract belongs to Phase 8",
            "Phase 8 sizing/TCO not implemented",
            "Screen 3 Control Center",
            "handoff_supported",
            "handoff_performed",
            "screen3_state_updated",
            "backend_request_created",
            "can_handoff",
            "handoff_blocked",
            "<dd>false</dd>",
            "<dd>true</dd>",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_forms_fetch_xhr_or_backend_calls(self) -> None:
        dashboard = dashboard_module()
        panel_source = inspect.getsource(
            dashboard._render_index_screen3_handoff_panel
        ).lower()
        rendered = self.render_home().lower()
        for phrase in (
            "<form",
            "method=\"post\"",
            "action=\"/",
            "fetch(",
            "xmlhttprequest",
            "sendbeacon",
            "/api/",
            "backend_endpoint",
            "execute_handoff(",
            "perform_handoff(",
            "update_screen3_state(",
            "create_backend_request(",
            "run_analysis.py(",
            "download_object(",
            "list_bucket(",
            "call_object_storage(",
            "query_database(",
            "open_file(",
            "read_file(",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, panel_source)
                self.assertNotIn(phrase, rendered)
        for phrase in ("localstorage", "window.location"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, panel_source)

    def render_home(self) -> str:
        return dashboard_module()._render_home_page(
            report_data={
                "metadata": {"db_name": "ORCL"},
                "decision": {"primary_domain": "CPU"},
                "recommendations": [],
                "llm_explanation": {"enabled": False},
            },
            screen_models={},
        )


if __name__ == "__main__":
    unittest.main()
