from __future__ import annotations

from html import unescape
import importlib
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardIndexSourceModeEntryTests(unittest.TestCase):
    def test_html_dashboard_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_platform_entry_two_primary_paths_exist(self) -> None:
        rendered = self.render_home()
        for phrase in (
            "Platform Entry / Source Intake",
            "What do you want to work with?",
            'data-phase7-primary-entry-paths="true"',
            'data-phase7-entry-path="new_source"',
            'data-phase7-entry-path="existing_platform_evidence"',
            "Load / Ingest New Source",
            "Use Existing Platform Evidence",
            "Screen 1 - Ingestion / Parser / Source Governance",
            "Screen 2 - Runtime Scope &amp; Analysis Control",
            "screen_1_ingestion.html",
            "screen_2_control.html",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_platform_entry_preserves_source_path_explanation_boundaries(self) -> None:
        rendered = " ".join(unescape(self.render_home()).split())

        for phrase in (
            "Start here. Choose whether to begin with a new source on Screen 1 or continue with existing platform evidence on Screen 2.",
            "Home records source-path intent only. It does not validate sources, load runtime options, select scope, assign targets, decide readiness, generate diagnostics, or compare evidence.",
            "Use this when the operator has a new AWR file, local staged folder, selected file, or Object Storage object metadata",
            "Screen 1 - Ingestion / Parser / Source Governance.",
            "Use this when evidence is already available inside the platform. Continue to Screen 2 to load runtime options, select runtime scope, choose target/time window context, and prepare comparison readiness.",
            "Screen 2 - Runtime Scope & Analysis Control. Screen 2 loads runtime options, selects scope/window, and prepares Target A/B comparison readiness.",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        for forbidden in (
            "Run Governed Source Intake",
            "Validate Object Storage Source",
            "Load Runtime Options",
            "Assign Target A",
            "Assign Target B",
            "Decide Comparison Readiness",
            "Generate Focused Explanation",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)

    def test_home_pipeline_copy_preserves_load_parse_analyze_compare_boundary(self) -> None:
        rendered = " ".join(unescape(self.render_home()).split())

        for phrase in (
            "The platform separates entry, intake, runtime scope, deterministic analysis, and downstream review. Home explains the starting path; Screen 1 owns new-source intake and parser governance; Screen 2 owns existing-evidence runtime scope and comparison preparation; deterministic analysis remains the source of dashboard truth.",
            "Deterministic Analysis Pipeline",
            "Authoritative analysis truth",
            "Home records path intent only. Screen 1 or Screen 2 prepares valid evidence context. Deterministic parsing, scoring, decision, and recommendation remain authoritative only after the governed backend workflow processes the selected source or selected existing evidence.",
            "Evidence Context",
            "Prepared by Screen 1 for new sources or Screen 2 for existing evidence.",
            "Parsing",
            "Extracts AWR sections, metrics, discovered elements, and unknowns.",
            "Feature Engineering",
            "Builds structured diagnostic signals.",
            "Scoring",
            "Computes deterministic domain scores.",
            "Decision",
            "Determines posture and issue prioritization.",
            "Recommendation",
            "Produces deterministic action guidance.",
            "Dashboard Truth",
            "Renders deterministic evidence and guidance.",
            "Governed Memory",
            "Persists governed runs, recommendations, actions, outcomes, feedback, unknown signals, approvals, and artifacts without changing deterministic analysis truth.",
            "Parallel Reviewer-Assist Semantic Context",
            "Optional non-authoritative context for review and explanation; it does not change deterministic runtime truth.",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        for old_phrase in (
            "AWR Intelligence Pipeline",
            "Governed source intake flows into deterministic parsing",
            "Deterministic Runtime Pipeline",
            "Authoritative truth generation",
            "without changing runtime decisions",
        ):
            with self.subTest(old_phrase=old_phrase):
                self.assertNotIn(old_phrase, rendered)

    def test_primary_entry_cards_are_full_links(self) -> None:
        rendered = self.render_home()
        expected_cards = (
            (
                'href="screen_1_ingestion.html"',
                'data-phase7-entry-path="new_source"',
                'data-phase7-entry-source-modes="local_staged local_file object_storage"',
            ),
            (
                'href="screen_2_control.html"',
                'data-phase7-entry-path="existing_platform_evidence"',
                'data-phase7-entry-source-modes="existing_run"',
            ),
        )
        for href, path, modes in expected_cards:
            with self.subTest(href=href):
                start = rendered.find(href)
                self.assertGreaterEqual(start, 0)
                context = rendered[max(0, start - 220) : start + 600]
                self.assertIn("phase7cr-entry-card-link", context)
                self.assertIn('data-dashboard-propagate-state="true"', context)
                self.assertIn(path, context)
                self.assertIn(modes, context)

    def test_source_modes_are_lightweight_mapping_only(self) -> None:
        rendered = self.render_home()
        for source_mode in (
            "local_staged",
            "local_file",
            "object_storage",
            "existing_run",
        ):
            with self.subTest(source_mode=source_mode):
                self.assertIn(source_mode, rendered)
        for phrase in (
            "Detailed Source Mode Configuration",
            "Source Mode Configuration",
            'data-dashboard-select-id="local_staged"',
            'data-dashboard-select-id="local_file"',
            'data-dashboard-select-id="object_storage"',
            'data-dashboard-select-id="existing_run"',
            'data-phase7-action-control="true"',
            "Advanced Debug State / Browser Selection State",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, rendered)
        self.assertNotIn("future_upload", rendered)
        self.assertNotIn("future_em_extract", rendered)

    def test_legacy_phase_panels_are_not_rendered_on_index(self) -> None:
        rendered = self.render_home()
        for phrase in (
            'id="index-source-mode-entry-panel"',
            'id="index-source-status-panel"',
            'id="index-object-storage-config-panel"',
            'id="index-screen3-handoff-panel"',
            "Legacy 7BQ",
            "Legacy 7BR",
            "Legacy 7BS",
            "Legacy 7BT",
            "Historical Phase Boundary Evidence",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, rendered)

    def test_index_does_not_expose_browser_side_source_access(self) -> None:
        rendered = self.render_home().lower()
        for phrase in (
            "filereader",
            "readastext",
            "readasarraybuffer",
            "getobject",
            "listobjects",
            "objectstorageclient",
            "oci-sdk",
            "query_database(",
            "run_analysis.py(",
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
