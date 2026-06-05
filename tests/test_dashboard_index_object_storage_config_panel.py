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
            "Source Channel Model",
            "Cloud metadata channel",
            "Capture namespace, bucket, object or prefix, and region for governed metadata validation.",
            "Metadata validation only today; future backend source-loader contract is required for load-to-staging.",
            "Validate Object Storage Source",
            "governed metadata validation only",
            "full load, parse, and",
            "analyze remain backend-gated",
            "Future governed backend load-to-staging",
            "The browser does not call",
            "OCI APIs",
            "expose credentials",
            "list buckets",
            "read objects",
            "claim artifact readiness",
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

    def test_screen1_source_channel_model_is_product_oriented(self) -> None:
        rendered = self.render_screen1()
        for phrase in (
            'data-phase7-source-channel-model="true"',
            "Source Channel Model",
            'data-phase7-source-channel-card="local_staged"',
            "Local Staged / Local Folder",
            "Current most complete governed path",
            'data-phase7-source-channel-card="local_file"',
            "Local File",
            "Future governed upload or staging",
            'data-phase7-source-channel-card="object_storage"',
            "Metadata validation only",
            'data-phase7-existing-evidence-handoff-reference="true"',
            "Existing platform evidence is not a Screen 1 source card",
            "Screen 2 Runtime Scope &amp; Analysis Control",
            'data-phase7-future-source-channel="enterprise_manager_oem"',
            "Enterprise Manager / OEM",
            'data-phase7-future-source-channel="file_system"',
            "File System",
            'data-phase7-future-source-channel="catalog_repository"',
            "Catalog / Repository",
            'data-phase7-future-source-channel="ai_source"',
            "AI Source",
            "Future governed source",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        self.assertNotIn('data-dashboard-select-id="existing_run"', rendered)

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
