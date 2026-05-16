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


class DashboardIndexObjectStorageConfigPanelTests(unittest.TestCase):
    def test_html_dashboard_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_panel_exists(self) -> None:
        rendered = self.render_home()
        self.assertIn('id="index-object-storage-config-panel"', rendered)
        self.assertIn("Object Storage Configuration Status", rendered)
        self.assertIn('data-phase="7BS"', rendered)
        self.assertIn('data-preview-only="true"', rendered)

    def test_safety_labels_exist(self) -> None:
        rendered = self.render_home()
        for phrase in (
            "Preview only",
            "Object Storage metadata validation only",
            "No credential validation",
            "No object storage call",
            "No bucket listing",
            "No object download",
            "No Screen 3 handoff in this phase",
            "No run_analysis.py call",
            "Phase 8 EM Extract not implemented",
            "Phase 8 sizing/TCO not implemented",
            "credential_validation_performed",
            "object_storage_call_performed",
            "bucket_list_performed",
            "object_download_performed",
            "execution_blocked",
            "<dd>false</dd>",
            "<dd>true</dd>",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_forms_fetch_xhr_or_backend_calls(self) -> None:
        dashboard = dashboard_module()
        panel_source = inspect.getsource(
            dashboard._render_index_object_storage_config_panel
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
            "submit_object_storage_config(",
            "execute_object_storage_config(",
            "execute_handoff(",
            "run_analysis.py(",
            "download_object(",
            "list_bucket(",
            "call_object_storage(",
            "validate_credentials(",
            "read_config_file(",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, panel_source)
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
