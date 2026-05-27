from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"
AI_METADATA_PATH = ROOT / "src" / "reporting" / "ai_display_metadata.py"
RUN_ANALYSIS_PATH = ROOT / "scripts" / "run_analysis.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardScreen3ControlCenterTests(unittest.TestCase):
    def test_01_import_compile_safety(self) -> None:
        ast.parse(read_text(HTML_DASHBOARD_PATH), filename=str(HTML_DASHBOARD_PATH))
        ast.parse(read_text(AI_METADATA_PATH), filename=str(AI_METADATA_PATH))
        dashboard = dashboard_module()

        self.assertTrue(hasattr(dashboard, "_render_screen_3_selector_page"))
        self.assertTrue(hasattr(dashboard, "_build_screen3_control_center_model"))

    def test_screen3_control_center_product_workflow_exists(self) -> None:
        dashboard = dashboard_module()
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        self.assertIn("Screen 2 - Runtime Scope & Analysis Control", source)
        self.assertIn("Screen 2 - Runtime Scope & Analysis Control", rendered)
        self.assertIn(
            '("screen_2", "2 Control", "screen_2_control.html")',
            source,
        )
        self.assertIn(
            '("screen_3", "3 Analysis", "screen_3_analysis.html")',
            source,
        )
        self.assertIn('"screen_2": "Screen 2 - Runtime Scope & Analysis Control"', source)
        self.assertIn('"screen_3": "Screen 3 - Diagnostic Snapshot"', source)
        self.assertIn("Existing run truth unchanged", rendered)
        self.assertIn("Runtime Evidence Path", rendered)
        self.assertIn("Evidence path status", rendered)
        self.assertIn("Load Runtime Options", rendered)
        self.assertIn("Work Area 1", rendered)
        self.assertIn("Select Runtime Scope", rendered)
        self.assertIn("Work Area 2", rendered)
        self.assertIn("Resolve Comparison Targets", rendered)
        self.assertIn("Target A and Target B identify selected candidate sides for later comparison review", rendered)
        self.assertIn("Assignment records selection context only", rendered)
        self.assertIn("Work Area 3", rendered)
        self.assertIn("Submit Governed Action and Review Result", rendered)
        self.assertIn("Runtime Scope Filters", rendered)
        self.assertIn("screen3-filter-select", rendered)
        self.assertIn("screen3RuntimeFilterSearch", rendered)
        self.assertIn("Apply Filters", rendered)
        self.assertIn("Clear Filters", rendered)
        self.assertIn("data-screen3-filtered-result-count", rendered)
        self.assertIn("Filtered AWR / Run / Report Results", rendered)
        self.assertIn("How to use this screen", rendered)
        self.assertIn("Selected Context", rendered)
        self.assertIn("screen3-selected-context-strip", rendered)
        self.assertIn("screen3-selection-legend", rendered)
        self.assertIn("data-screen3-table-id=\"screen3-runtime-inventory\"", rendered)
        self.assertIn("data-screen3-table-id=\"screen3-intervals\"", rendered)
        self.assertIn("data-screen3-table-id=\"screen3-target-a-options\"", rendered)
        self.assertIn("data-screen3-table-id=\"screen3-target-b-options\"", rendered)
        self.assertIn("data-screen3-table-filter", rendered)
        self.assertIn("data-screen3-table-filter-toggle", rendered)
        self.assertIn("data-screen3-clear-table-filters", rendered)
        self.assertIn("data-screen3-table-count", rendered)
        self.assertIn("data-screen3-table-sort-summary", rendered)
        self.assertIn("data-screen3-table-filter-summary", rendered)
        self.assertIn("screen3-table-filter-input", rendered)
        self.assertIn("screen3-table-filter-toggle", rendered)
        self.assertIn("data-screen3-runtime-sort", rendered)
        self.assertIn("data-screen3-table-sort", rendered)
        self.assertIn("data-screen3-sort-indicator", rendered)
        self.assertIn("No DB-backed AWR/run options are loaded yet", rendered)
        self.assertIn("data-screen3-row-id", source)
        self.assertIn("screen3SelectedRuntimeScopeRowId", source)
        self.assertIn("screen3SelectedTargetARowId", source)
        self.assertIn("screen3SelectedTargetBRowId", source)
        self.assertIn("screen3RuntimeOptionsCache", source)
        self.assertIn("screen3-runtime-options-v1", source)
        self.assertIn("Runtime options restored from browser cache", source)
        self.assertIn("Refresh failed; cached runtime options were not activated", source)
        self.assertIn("Cache Status", rendered)
        self.assertIn("screen3RuntimeScopeSelectionSource", source)
        self.assertIn("screen3TargetASelectionSource", source)
        self.assertIn("screen3TargetBSelectionSource", source)
        self.assertIn("screen3RuntimeRowIdentity", source)
        self.assertIn("screen3IntervalRowIdentity", source)
        self.assertIn("screen3-selected-runtime-row", source)
        self.assertIn("screen3-selected-interval-row", source)
        self.assertIn("screen3-selected-advanced-row", source)
        self.assertIn("initializeScreen3Tables", source)
        self.assertIn("position: sticky", source)
        self.assertIn("Check with Load Options", source)
        self.assertIn("The next row click updates only this assignment", rendered)
        self.assertIn("Only its selected row gets the strong table highlight", rendered)
        self.assertIn("Snapshot / Interval Selection", rendered)
        self.assertIn("Apply interval to", rendered)
        self.assertIn("Selected AWR / Report Row", rendered)
        self.assertIn("Selected Runtime Scope / Assignment Summary", rendered)
        self.assertIn("Comparison &amp; Review Controls", rendered)
        self.assertNotIn("<h4>Comparison Controls</h4>", rendered)
        self.assertIn("Review Mode", rendered)
        self.assertIn("Governed Actions", rendered)
        self.assertIn("Request / Execution Result", rendered)
        self.assertIn("Runtime Safety and Selection Impact", rendered)
        self.assertNotIn("Technical Audit / Debug Details", rendered)
        self.assertIn("Generated at build time", source)
        self.assertIn("AI DB:", source)
        self.assertIn("Workflow:", source)
        self.assertIn("LLM:", source)
        self.assertIn("data-dashboard-runtime-badge=\"true\"", source)
        self.assertIn("data-dashboard-runtime-workflow-status=\"true\"", source)
        self.assertIn("runtime-badge-hydrated", source)
        self.assertIn("readStoredWorkflowStatus", source)
        self.assertIn("Local dashboard workflow service status", source)
        self.assertNotIn("Live Service", source)
        self.assertIn("State source:", rendered)
        self.assertNotIn("Runtime Selection Context", rendered)
        self.assertNotIn("Selected Issue Domain", rendered)

        results_index = rendered.find("Filtered AWR / Run / Report Results")
        selected_row_index = rendered.find("Selected AWR / Report Row")
        interval_index = rendered.find("Snapshot / Interval Selection")
        assignment_index = rendered.find("Selected Runtime Scope / Assignment Summary")
        selected_context_index = rendered.find("Selected Context")
        self.assertGreater(selected_row_index, results_index)
        self.assertGreater(interval_index, selected_row_index)
        self.assertGreater(assignment_index, interval_index)
        self.assertGreater(selected_context_index, results_index)
        self.assertGreater(selected_context_index, interval_index)

    def test_selector_metadata_exists_for_domains_and_run_context(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required = (
            'data-dashboard-selectable="true"',
            'data-dashboard-state-key="screen3RuntimeFilterSearch"',
            'data-dashboard-select-type="comparisonMode"',
            'data-dashboard-select-key="selectedComparisonMode"',
            'data-dashboard-select-type="reviewMode"',
            'data-dashboard-select-key="selectedReviewMode"',
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)
        dynamic_required = (
            "data-dashboard-select-type', config.selectType",
            "data-dashboard-select-type', 'runtimeScope'",
            "data-dashboard-select-type', 'snapshot'",
            "data-dashboard-select-key', 'selectedRuntimeScope'",
            "data-dashboard-select-key', 'selectedTimeWindow'",
        )
        for phrase in dynamic_required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
        self.assertIn("No DB-backed AWR/run options are loaded yet", rendered)
        self.assertNotIn("screen3-filter-pill", rendered)

    def test_runtime_scope_table_and_comparison_builder_are_present(self) -> None:
        rendered = self.render_screen3()

        required = (
            "screen3-runtime-scope-table",
            'data-screen3-runtime-options-target="runtime-scope-rows"',
            'data-screen3-runtime-options-target="interval-rows"',
            "Application",
            "DB Name",
            "DBID",
            "Instance",
            "Host/System",
            "AWR / Run",
            "Report ID / Run History ID",
            "Target A",
            "Target B",
            "Source Type",
            "Scope Type",
            "Scope Value",
            "Resolution",
            "Readiness",
            "source_type + scope_type + scope_value + time_window + resolution_state + readiness_state",
            "Comparison Readiness / Request Handoff",
            "Readiness is not a comparison result",
            "Both Comparable",
            "Current DB history",
            "Similar AWRs",
            "Cluster baseline",
            "Fleet baseline",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_screen3_runtime_selection_uses_active_assignment_only(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)

        required = (
            "const isScreen3RuntimeRow = selectType === 'runtimeScope';",
            "const isScreen3IntervalRow = selectType === 'snapshot';",
            "const screen3ContextSelected = selectableMatchesScreen3Context(element, value, safeState);",
            "isSelected = screen3ContextSelected;",
            "return safeValue === safeStateValue(state.screen3SelectedTargetARowId || '');",
            "return safeValue === safeStateValue(state.screen3SelectedTargetBRowId || '');",
            "return safeValue === safeStateValue(state.screen3SelectedRuntimeScopeRowId || '');",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)

    def test_screen3_table_controls_are_icon_based_and_chained(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen3()

        required_source = (
            "data-screen3-table-filter-toggle",
            "screen3-table-filter-toggle",
            "handleScreen3TableFilterToggleClick",
            "headerControl.classList.toggle('is-filter-open')",
            "activeFilters.every(function (key)",
            "No rows match current table filters.",
            "Showing ' + String(visibleCount) + ' of ' + String(baselineCount) + ' row(s) after table filters.",
            "screen3-table-sort-summary",
            "screen3-table-filter-summary",
        )
        for phrase in required_source:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)

        required_rendered = (
            "screen3-table-sort-button",
            "screen3-table-filter-toggle",
            "data-screen3-table-filter-toggle",
            "data-screen3-table-sort-summary",
            "data-screen3-table-filter-summary",
            "Clear table filters",
        )
        for phrase in required_rendered:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_required_safety_wording_is_rendered(self) -> None:
        rendered = self.render_screen3()

        required_phrases = (
            "Local selection changes only browser/local request context",
            "A workflow record is created only after a governed action is submitted",
            "Existing run truth unchanged",
            "Screen 2 Control can request or execute only governed backend actions",
            "New deterministic outputs, when available, must be represented as separate run/output/artifact references",
            "Build Comparison is request-ready only when Target A and Target B resolve to comparable persisted data",
            "learning candidates, materialization, runtime eligibility",
            "LLM/explanatory wording cannot alter validation, status, execution, deterministic truth",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_similarity_unavailable_uses_failure_styling(self) -> None:
        dashboard = dashboard_module()

        self.assertEqual("state-error", dashboard._similarity_runtime_state_class("Unavailable"))

    def test_no_unsafe_direct_runtime_paths_are_introduced(self) -> None:
        dashboard = dashboard_module()
        rendered = self.render_screen3().lower()
        source = read_text(HTML_DASHBOARD_PATH).lower()
        script = dashboard._build_dashboard_interactivity_javascript().lower()

        forbidden_controls = (
            "<form",
            "method=\"post\"",
            "type=\"submit\"",
            "onclick=",
            "data-action=",
            "approval-control",
            "write-control",
            "learning-approval-control",
        )
        for control in forbidden_controls:
            with self.subTest(control=control):
                self.assertNotIn(control, rendered)

        forbidden_writes = (
            "xmlhttprequest",
            "sendbeacon",
            "/api/write",
            "/api/approve",
            "/api/reject",
            "/api/implement",
            "/api/validate",
            "/api/close",
            "/api/activate",
        )
        for phrase in forbidden_writes:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, script)
                self.assertNotIn(phrase, source)
        self.assertIn("requestbridge(phase7_action_endpoint", script)
        self.assertIn("screen3_active_reanalysis", rendered)
        self.assertNotIn("run_analysis_coupling: true", source)

    def test_no_screen2_or_screen5_truth_drift(self) -> None:
        dashboard = dashboard_module()
        screen_2_source = inspect.getsource(dashboard._render_screen_2_page)
        screen_5_source = inspect.getsource(dashboard._render_screen_5_page)

        forbidden = (
            "selectedLearningCandidate",
            "selectedSemanticItem",
            "learning candidate selection",
            "semantic selection",
            "Screen 2 - Runtime Scope & Analysis Control",
        )
        for phrase in forbidden:
            with self.subTest(screen="screen_2", phrase=phrase):
                self.assertNotIn(phrase, screen_2_source)
            with self.subTest(screen="screen_5", phrase=phrase):
                self.assertNotIn(phrase, screen_5_source)

    def test_no_7h8_behavior_yet(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH).lower()

        forbidden_phrases = (
            "cross-screen propagation engine",
            "propagate selection to screen 2",
            "propagate selection to screen 4",
            "propagate selection to screen 5",
            "activatelearningcandidate",
            "approvelearningcandidate",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, source)

    def test_runtime_import_drift_is_absent(self) -> None:
        runtime_paths = [
            RUN_ANALYSIS_PATH,
            ROOT / "src" / "analysis" / "decision_engine.py",
            ROOT / "src" / "analysis" / "recommendation_engine.py",
        ]
        runtime_paths.extend((ROOT / "src" / "parser").glob("*.py"))
        runtime_paths.extend((ROOT / "src" / "analysis").glob("*scoring*.py"))

        for path in sorted(set(runtime_paths)):
            if not path.is_file():
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                self.assert_no_learning_imports(path)
                text = read_text(path)
                self.assertNotIn("Screen 3 Control Center", text)
                self.assertNotIn("DashboardInteractivityFoundation", text)

    def test_documentation_exists_and_contains_historical_boundaries(self) -> None:
        doc_path = DOCS / "phase7_screen3_control_center.md"
        self.assertTrue(doc_path.is_file())
        text = read_text(doc_path).lower()

        required_phrases = (
            "does not change diagnostic truth",
            "does not change recommendation truth",
            "does not change primary issue",
            "does not change severity",
            "full cross-screen propagation remains future 7h.8",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

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

    def assert_no_learning_imports(self, path: Path) -> None:
        tree = ast.parse(read_text(path), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertFalse(
                        self._is_learning_module(alias.name),
                        f"{path} imports learning module {alias.name}",
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                self.assertFalse(
                    self._is_learning_module(module),
                    f"{path} imports learning module {module}",
                )

    @staticmethod
    def _is_learning_module(module_name: str) -> bool:
        return (
            module_name == "learning"
            or module_name.startswith("learning.")
            or module_name == "src.learning"
            or module_name.startswith("src.learning.")
        )


if __name__ == "__main__":
    unittest.main()
