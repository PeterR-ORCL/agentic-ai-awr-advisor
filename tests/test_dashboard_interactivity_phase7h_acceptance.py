from __future__ import annotations

import ast
import importlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
TESTS = ROOT / "tests"
SCRIPTS = ROOT / "scripts"
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"
RUN_ANALYSIS_PATH = ROOT / "scripts" / "run_analysis.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardInteractivityPhase7HAcceptanceTests(unittest.TestCase):
    def test_01_required_phase7h_docs_exist(self) -> None:
        required_docs = (
            "phase7_dashboard_interactivity_architecture.md",
            "phase7_dashboard_interactivity_validation_matrix.md",
            "phase7_dashboard_interactivity_acceptance_criteria.md",
            "phase7_dashboard_interactivity_foundation.md",
            "phase7_screen3_control_center.md",
            "phase7_screen2_diagnostic_exploration.md",
            "phase7_screen4_historical_review_exploration.md",
            "phase7_screen5_recommendation_action_exploration.md",
            "phase7_screen1_governance_parser_exploration.md",
            "phase7_screen6_fleet_governance_learning_exploration.md",
            "phase7_cross_screen_selection_propagation.md",
        )
        for filename in required_docs:
            with self.subTest(filename=filename):
                self.assertTrue((DOCS / filename).is_file())

    def test_required_phase7h_test_files_exist(self) -> None:
        required_tests = (
            "test_dashboard_interactivity_foundation.py",
            "test_dashboard_screen3_control_center.py",
            "test_dashboard_screen2_diagnostic_exploration.py",
            "test_dashboard_screen4_historical_review_exploration.py",
            "test_dashboard_screen5_recommendation_action_exploration.py",
            "test_dashboard_screen1_governance_parser_exploration.py",
            "test_dashboard_screen6_fleet_governance_learning_exploration.py",
            "test_dashboard_cross_screen_selection_propagation.py",
        )
        for filename in required_tests:
            with self.subTest(filename=filename):
                self.assertTrue((TESTS / filename).is_file())

    def test_consolidated_docs_contain_required_boundary_phrases(self) -> None:
        doc_text = "\n".join(
            read_text(DOCS / filename).lower()
            for filename in (
                "phase7_dashboard_interactivity_architecture.md",
                "phase7_dashboard_interactivity_validation_matrix.md",
                "phase7_dashboard_interactivity_acceptance_criteria.md",
            )
        )
        required_phrases = (
            "read-only",
            "exploratory only",
            "browser-side only",
            "url hash/localstorage state is not authoritative truth",
            "no backend writes",
            "no api calls",
            "no approval controls",
            "no write controls",
            "no runtime activation",
            "does not change parser output",
            "does not change diagnostic truth",
            "does not change historical truth",
            "does not change recommendation truth",
            "does not change governance state",
            "does not change candidate status",
            "semantic context remains reviewer-assist only",
            "learning candidates remain proposal/review context only",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, doc_text)

    def test_dashboard_source_contains_required_phase7h_markers(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        required_markers = (
            "Dashboard Interactivity Foundation",
            "Screen 3 Control Center",
            "Screen 2 Diagnostic Exploration",
            "Screen 4 Historical Review Exploration",
            "Screen 5 Recommendation/Action Exploration",
            "Screen 1 Governance / Parser Exploration",
            "Screen 6 Fleet / Governance / Semantic / Learning Exploration",
            "Cross-Screen Selection Propagation",
        )
        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, source)

    def test_dashboard_source_contains_browser_side_state_markers(self) -> None:
        dashboard = dashboard_module()
        source = read_text(HTML_DASHBOARD_PATH)
        script = dashboard._build_dashboard_interactivity_javascript()
        combined = source + script
        required_markers = (
            "parseHashState",
            "updateHashState",
            "localStorage",
            "is-selected",
            "aria-selected",
            "data-selected",
            "data-dashboard-selectable",
            "data-dashboard-filter-key",
            "data-dashboard-filter-value",
        )
        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, combined)

    def test_no_backend_or_api_write_behavior(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH).lower()
        forbidden_patterns = (
            "fetch(",
            "xmlhttprequest",
            'method="post"',
            "method='post'",
            'action="/',
            "action='/",
            "api/write",
            "api/approve",
            "api/reject",
            "api/implement",
            "api/validate",
            "api/close",
            "api/activate",
            "api/materialize",
        )
        for pattern in forbidden_patterns:
            with self.subTest(pattern=pattern):
                self.assertNotIn(pattern, source)

    def test_no_approval_or_write_controls(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH).lower()
        forbidden_controls = (
            "approval-control",
            "reject-control",
            "implement-control",
            "validate-control",
            "close-control",
            "materialize-control",
            "activate-control",
            "apply-control",
            "write-control",
            "data-learning-action",
            "candidate-status-mutation-control",
            "governance-status-mutation-control",
            "parser-update-control",
            "knowledge-update-control",
        )
        for control in forbidden_controls:
            with self.subTest(control=control):
                self.assertNotIn(control, source)

    def test_runtime_truth_labels_are_present(self) -> None:
        dashboard = dashboard_module()
        combined = (
            read_text(HTML_DASHBOARD_PATH)
            + dashboard._build_dashboard_interactivity_javascript()
            + dashboard._render_dashboard_interactivity_boundary_comment()
        )
        required_labels = (
            "Does not change parser output",
            "Does not change diagnostic truth",
            "Does not change historical truth",
            "Does not change recommendation truth",
            "Does not change governance state",
            "Does not change candidate status",
        )
        for label in required_labels:
            with self.subTest(label=label):
                self.assertIn(label, combined)

    def test_semantic_and_learning_labels_are_present(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        required_labels = (
            "Semantic context remains reviewer-assist only",
            "Learning candidates remain proposal/review context only",
            "runtime_influence=false",
            "requires_human_review=true",
        )
        for label in required_labels:
            with self.subTest(label=label):
                self.assertIn(label, source)

    def test_runtime_import_isolation(self) -> None:
        runtime_paths = [RUN_ANALYSIS_PATH]
        runtime_paths.extend((ROOT / "src" / "parser").glob("*.py"))
        runtime_paths.extend((ROOT / "src" / "analysis").glob("*.py"))

        for path in sorted(set(runtime_paths)):
            if not path.is_file():
                continue
            text = read_text(path)
            with self.subTest(path=path.relative_to(ROOT)):
                if path != RUN_ANALYSIS_PATH:
                    self.assertNotIn("src.learning", text)
                self.assertNotIn("DashboardInteractivityFoundation", text)
                self.assertNotIn("_build_dashboard_interactivity_javascript", text)

    def test_no_generated_dashboard_dependency_requirement(self) -> None:
        dashboard = dashboard_module()
        script = dashboard._build_dashboard_interactivity_javascript().lower()
        forbidden_dependencies = (
            "<script src=",
            "https://",
            "http://",
            "react",
            "vue",
            "npm",
            "webpack",
            "vite",
            "rollup",
            "import ",
            "require(",
        )
        for dependency in forbidden_dependencies:
            with self.subTest(dependency=dependency):
                self.assertNotIn(dependency, script)

    def test_existing_phase7h_unittest_modules_are_importable(self) -> None:
        modules = (
            "tests.test_dashboard_interactivity_foundation",
            "tests.test_dashboard_screen3_control_center",
            "tests.test_dashboard_screen2_diagnostic_exploration",
            "tests.test_dashboard_screen4_historical_review_exploration",
            "tests.test_dashboard_screen5_recommendation_action_exploration",
            "tests.test_dashboard_screen1_governance_parser_exploration",
            "tests.test_dashboard_screen6_fleet_governance_learning_exploration",
            "tests.test_dashboard_cross_screen_selection_propagation",
        )
        for module_name in modules:
            with self.subTest(module_name=module_name):
                importlib.import_module(module_name)

    def test_readme_includes_final_phase7h_docs(self) -> None:
        readme = read_text(DOCS / "README.md")
        required_links = (
            "phase7_dashboard_interactivity_architecture.md",
            "phase7_dashboard_interactivity_validation_matrix.md",
            "phase7_dashboard_interactivity_acceptance_criteria.md",
        )
        for link in required_links:
            with self.subTest(link=link):
                self.assertIn(link, readme)

    def test_optional_phase7h_validation_script_is_safe_if_present(self) -> None:
        script_path = SCRIPTS / "run_phase7h_dashboard_validation.py"
        if not script_path.exists():
            self.skipTest("Optional Phase 7H validation script was not created.")
        ast.parse(read_text(script_path), filename=str(script_path))
        script = read_text(script_path).lower()
        forbidden_dependencies = (
            "oracledb",
            "cx_oracle",
            "oci.",
            "adb wallet",
            "requests",
            "urllib",
            "socket",
            "http.client",
            "ftplib",
            "smtplib",
            "run_analysis.py",
        )
        for dependency in forbidden_dependencies:
            with self.subTest(dependency=dependency):
                self.assertNotIn(dependency, script)


if __name__ == "__main__":
    unittest.main()
