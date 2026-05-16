from __future__ import annotations

import importlib
import inspect
import py_compile
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardIndexSourceStatusPanelTests(unittest.TestCase):
    def test_html_dashboard_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_source_status_section_exists(self) -> None:
        rendered = self.render_home()
        self.assertIn('id="index-source-status-panel"', rendered)
        self.assertIn("Source Status", rendered)
        self.assertIn('data-phase="7BR"', rendered)
        self.assertIn('data-preview-only="true"', rendered)

    def test_all_source_modes_are_visible(self) -> None:
        rendered = self.render_home()
        for phrase in (
            "Local Staged AWR",
            "Local File",
            "Existing Run",
            "Object Storage",
            "Future Upload",
            "Future EM Extract",
            "local_staged",
            "local_file",
            "existing_run",
            "object_storage",
            "future_upload",
            "future_em_extract",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_safety_labels_present(self) -> None:
        rendered = self.render_home()
        for phrase in (
            "Preview only",
            "Source status is not source access",
            "No local file read",
            "No object storage call",
            "No DB lookup",
            "No run_analysis.py call",
            "No Screen 3 handoff in this phase",
            "Future EM Extract belongs to Phase 8",
            "Phase 8 sizing/TCO is not implemented",
            "execution_supported",
            "handoff_supported",
            "source_access_performed",
            "<dd>false</dd>",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_forms_fetch_xhr_or_backend_calls(self) -> None:
        dashboard = dashboard_module()
        panel_source = inspect.getsource(
            dashboard._render_index_source_status_panel
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
            "submit_source_status(",
            "execute_source_status(",
            "execute_handoff(",
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

    def test_existing_index_source_mode_entry_test_still_passes(self) -> None:
        completed = subprocess.run(
            ("python3", "-m", "unittest", "tests/test_dashboard_index_source_mode_entry.py"),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )

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
