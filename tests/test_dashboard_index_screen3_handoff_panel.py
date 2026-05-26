from __future__ import annotations

import importlib
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

    def test_existing_platform_evidence_path_points_to_screen_2_control(self) -> None:
        rendered = self.render_home()
        for phrase in (
            "Use Existing Platform Evidence",
            'data-phase7-entry-path="existing_platform_evidence"',
            'data-phase7-entry-source-modes="existing_run"',
            "Screen 2 - Runtime Scope &amp; Analysis Control",
            "screen_2_control.html",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)
        for phrase in (
            'data-dashboard-select-id="existing_run"',
            "Load Existing Runs",
            "Governed existing run lookup",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, rendered)

    def test_new_source_path_points_to_screen_1_ingestion(self) -> None:
        rendered = self.render_home()
        for phrase in (
            "Load / Ingest New Source",
            'data-phase7-entry-path="new_source"',
            'data-phase7-entry-source-modes="local_staged local_file object_storage"',
            "Screen 1 - Ingestion / Parser / Source Governance",
            "screen_1_ingestion.html",
            "Open Screen 1 Ingestion",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_legacy_handoff_preview_panel_is_not_rendered(self) -> None:
        rendered = self.render_home()
        for phrase in (
            'id="index-screen3-handoff-panel"',
            "Index to Screen 2 Control Selection Handoff Preview",
            "Legacy 7BT",
            "Handoff is not active in this phase",
            "No backend request created",
            "handoff_blocked",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, rendered)

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
