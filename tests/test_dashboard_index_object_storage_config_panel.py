from __future__ import annotations

import importlib
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardIndexObjectStorageConfigPanelTests(unittest.TestCase):
    def test_html_dashboard_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_object_storage_validation_controls_are_on_screen_1(self) -> None:
        rendered = self.render_screen1()
        for phrase in (
            'data-dashboard-select-id="object_storage"',
            "Object Storage",
            "Configuration-dependent source",
            "Submit a governed request for backend-side Object Storage validation using configured environment values.",
            "No browser-side Object Storage access",
            "Validate Object Storage Source",
            "governed metadata validation only",
            "full load, parse, and",
            "analyze remain backend-gated",
            "The browser does not call",
            "OCI APIs",
            "expose credentials",
            "list buckets",
            "read objects",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_index_only_maps_object_storage_to_screen_1(self) -> None:
        rendered = self.render_home()
        for phrase in (
            'data-phase7-entry-source-modes="local_staged local_file object_storage"',
            "Object Storage",
            "Screen 1 - Ingestion / Parser / Source Governance",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)
        for phrase in (
            "Validate Object Storage Source",
            'data-phase7-object-storage-validation-control="true"',
            'data-dashboard-select-id="object_storage"',
            "governed metadata validation only",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, rendered)

    def test_object_storage_legacy_panel_is_not_rendered(self) -> None:
        rendered = self.render_home()
        for phrase in (
            'id="index-object-storage-config-panel"',
            "Object Storage Configuration Status",
            "Legacy 7BS",
            "Phase 8 EM Extract",
            "Phase 8 sizing/TCO",
            "preferred OCI-ready source path",
            "OCI-ready source-selection path",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, rendered)

    def test_no_browser_object_storage_execution_markers(self) -> None:
        rendered = self.render_home().lower()
        for phrase in (
            "download_object(",
            "list_bucket(",
            "call_object_storage(",
            "validate_credentials(",
            "objectstorageclient",
            "oci-sdk",
            "listobjects",
            "getobject",
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
