from __future__ import annotations

import importlib
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardIndexSourceStatusPanelTests(unittest.TestCase):
    def test_html_dashboard_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_selected_source_summary_moved_to_screen_1(self) -> None:
        rendered = self.render_screen1()
        self.assertIn("Selected Source Summary", rendered)
        self.assertIn('data-phase7-current-selection-panel="true"', rendered)
        self.assertIn('data-phase7-active-source-configuration="true"', rendered)
        self.assertIn('data-phase7-dynamic-source-summary="true"', rendered)
        self.assertNotIn("Active Source Configuration / Runtime Source State", rendered)
        self.assertNotIn("Selected Source Summary", self.render_home())

    def test_handoff_status_moved_to_screen_1(self) -> None:
        rendered = self.render_screen1()
        self.assertIn("Validation / Execution Status", rendered)
        self.assertIn('data-phase7-runtime-source-validation="true"', rendered)
        self.assertIn('data-phase7-runtime-source-validation-grid="true"', rendered)
        for marker in (
            'data-phase7-source-validation-card="local_folder"',
            'data-phase7-source-validation-card="local_file"',
            'data-phase7-source-validation-card="object_storage"',
            'data-phase7-service-availability-status="true"',
            'data-phase7-submit-result-reference="true"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, rendered)
        self.assertNotIn('data-phase7-source-validation-card="existing_run"', rendered)
        self.assertNotIn("Runtime Source Validation", rendered)
        self.assertNotIn("Validation / Execution Status", self.render_home())

    def test_source_workflow_precedes_run_intake_report(self) -> None:
        rendered = self.render_screen1()
        self.assertLess(
            rendered.find("New Source Intake / Validation Workflow"),
            rendered.find("Current Generated Run / Intake Evidence"),
        )
        self.assertIn("screen1-generated-evidence-empty-state", rendered)
        self.assertIn("Generated evidence reflects a generated dashboard artifact", rendered)
        self.assertIn("No generated run evidence is available yet.", rendered)
        self.assertIn('data-screen1-generated-artifact-ready="false"', rendered)

    def test_status_copy_points_to_screen_1_ownership(self) -> None:
        rendered = " ".join(self.render_screen1().split())
        for phrase in (
            "For new sources, configure and validate source metadata here",
            "continue ingestion, parser review, and source governance on Screen 1",
            "Existing platform evidence runtime scope is controlled on Screen 2",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

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

    def render_screen1(self) -> str:
        return dashboard_module()._render_screen_1_page(
            screen_model={"header": {}, "intake_summary": {}},
            parser_review_payload={},
            parser_governance_payload={},
            report_data={
                "metadata": {"db_name": "ORCL"},
                "decision": {"primary_domain": "CPU"},
                "recommendations": [],
            },
        )


if __name__ == "__main__":
    unittest.main()
