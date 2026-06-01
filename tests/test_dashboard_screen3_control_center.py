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
        self.assertIn(
            "it is not current backend, runtime-options, readiness, request, or evidence truth",
            source,
        )
        self.assertIn("Continuity only; not active backend truth", source)
        self.assertIn("Refresh failed; cached runtime options were not activated", source)
        self.assertIn("Cache Status", rendered)
        self.assertIn(
            "Cached Screen 2 state restores operator context only",
            rendered,
        )
        self.assertIn(
            "failed refresh must remain visible and must not promote cache to current truth",
            rendered,
        )
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
        self.assertIn("Not checked", source)
        self.assertIn("Available (cached)", source)
        self.assertNotIn("Check with Load Options", source)
        self.assertIn("The next row click updates only this assignment", rendered)
        self.assertIn("Only its selected row gets the strong table highlight", rendered)
        self.assertIn("Snapshot / Interval Selection", rendered)
        self.assertIn("Apply interval to", rendered)
        self.assertIn("Selected AWR / Report Row", rendered)
        self.assertIn("Selected Runtime Scope / Assignment Summary", rendered)
        self.assertIn("Comparison &amp; Review Controls", rendered)
        self.assertIn(
            "Cached Target A/B labels restore operator context only",
            rendered,
        )
        self.assertIn(
            "readiness must be confirmed by current governed backend metadata",
            rendered,
        )
        self.assertNotIn("<h4>Comparison Controls</h4>", rendered)
        self.assertIn("Review Mode", rendered)
        self.assertIn("Governed Actions", rendered)
        self.assertIn("Request / Result Receipt", rendered)
        self.assertIn(
            "Request receipt is not deterministic analysis truth unless a governed deterministic service returns a real output artifact reference",
            rendered,
        )
        self.assertIn(
            "Request ID, transaction ID, audit reference, persistence, and output fields are displayed from the service response only",
            rendered,
        )
        self.assertIn(
            "If receipt fields are restored from browser state, they are prior backend-returned context only until a current backend response supersedes them",
            rendered,
        )
        self.assertNotIn("Request / Execution Result", rendered)
        self.assertIn("Runtime Safety and Selection Impact", rendered)
        self.assertNotIn("Technical Audit / Debug Details", rendered)
        self.assertIn("Generated at build time", source)
        self.assertIn("AI DB:", source)
        self.assertIn("Workflow:", source)
        self.assertIn("LLM:", source)
        self.assertIn("data-dashboard-runtime-badge=\"true\"", source)
        self.assertIn("data-runtime-badge-hydration=\"in-place\"", source)
        self.assertIn("data-dashboard-runtime-workflow-status=\"true\"", source)
        self.assertIn("runtime-badge-hydrated", source)
        self.assertIn("readStoredWorkflowStatus", source)
        self.assertIn("screen3LiveServiceStatusSource", source)
        self.assertIn("screen3LiveServiceStatusCheckedAt", source)
        self.assertIn("screen3WorkflowRuntimeFreshChecked", source)
        self.assertIn("dashboardRuntimeModeSuppressesCachedWorkflow", source)
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
            "Screen 2 Control submits governed backend requests",
            "Backend execution status is service-returned only",
            "New deterministic outputs, when available, must be represented as separate run/output/artifact references",
            "Build Comparison is request-ready only when Target A and Target B resolve to comparable persisted data",
            "learning candidates, materialization, runtime eligibility",
            "LLM/explanatory wording cannot alter validation, status, deterministic truth",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_similarity_unavailable_uses_failure_styling(self) -> None:
        dashboard = dashboard_module()

        self.assertEqual("state-error", dashboard._similarity_runtime_state_class("Unavailable"))

    def test_runtime_badge_uses_truthful_build_and_cache_status_wording(self) -> None:
        dashboard = dashboard_module()
        rendered = dashboard._render_runtime_status_badge(
            {
                "ingestion_context": {
                    "db_ingestion": {
                        "summary": {
                            "db_connectivity": "Not checked",
                            "db_similarity_ready": False,
                        }
                    }
                },
                "llm_explanation": {
                    "enabled": True,
                    "provider": "offline",
                    "model": "offline-fixture",
                },
                "memory_runtime": {
                    "enabled": False,
                    "success": True,
                    "state": "Off",
                },
            }
        )

        self.assertIn("Dashboard generated without DB context", rendered)
        self.assertNotIn("GENERATED DB" + " WARNING", rendered)
        self.assertIn('data-runtime-badge-hydration="in-place"', rendered)
        self.assertIn("AI DB:", rendered)
        self.assertIn('<strong class="state-muted">Not checked</strong>', rendered)
        self.assertIn('data-empty-label="Not checked">Not checked</strong>', rendered)
        self.assertIn("LLM:", rendered)
        self.assertIn('<strong class="state-muted">Offline</strong>', rendered)
        self.assertIn("Similarity:", rendered)
        self.assertIn('<strong class="state-error">Unavailable</strong>', rendered)
        self.assertIn("Memory:", rendered)
        self.assertIn('<strong class="state-muted">Off</strong>', rendered)

    def test_runtime_badge_distinguishes_db_connectivity_states(self) -> None:
        dashboard = dashboard_module()

        cases = (
            ("Connected", "Connected", "state-pass"),
            ("Failed", "Connection failed", "state-error"),
            ("Not connected", "Not connected", "state-muted"),
            ("Not checked", "Not checked", "state-muted"),
        )
        for raw_state, display_state, css_class in cases:
            with self.subTest(raw_state=raw_state):
                status = dashboard._runtime_status_from_report(
                    {
                        "ingestion_context": {
                            "db_ingestion": {
                                "summary": {
                                    "db_connectivity": raw_state,
                                    "db_similarity_ready": raw_state == "Connected",
                                }
                            }
                        }
                    }
                )
                self.assertEqual(display_state, status["db_connectivity"])
                self.assertEqual(
                    css_class,
                    dashboard._db_runtime_state_class(status["db_connectivity"]),
                )
        self.assertEqual(
            "state-cached",
            dashboard._runtime_state_class("Available (cached)", "workflow"),
        )

    def test_runtime_badge_visual_stability_and_neutral_styling(self) -> None:
        styles = importlib.import_module("src.reporting.dashboard.styles")._shared_page_styles()
        source = read_text(HTML_DASHBOARD_PATH)

        self.assertIn(".runtime-mini-pill", styles)
        self.assertIn("background: rgba(13, 20, 30, 0.80)", styles)
        self.assertIn("border: 1px solid rgba(183, 192, 204, 0.42)", styles)
        self.assertNotIn(".runtime-mini-pill[data-runtime-badge-kind=\"workflow\"] {\n      min-width:", styles)
        self.assertIn(".state-cached", styles)
        self.assertIn("color: #b5f0bd", styles)
        self.assertIn("color: #cbd5e1", styles)
        self.assertIn("opacity: 1", styles)
        self.assertIn(".runtime-badge .status-pill.warning", styles)
        self.assertIn("border-color: rgba(255, 148, 112, 0.72)", styles)
        self.assertIn("transition: none", styles)
        self.assertIn("data-runtime-badge-hydration=\"in-place\"", source)
        self.assertIn("return 'state-cached'", source)
        self.assertIn("dashboardWorkflowStatusDisplayValue", source)
        self.assertIn("screen3CachedWorkflowStatusLabel(safeValue)", source)
        self.assertIn("screen3RuntimeOptionsLiveLoaded(state)", source)
        self.assertIn("screen3WorkflowRuntimeFreshChecked(state)", source)
        self.assertIn("dashboardRuntimeModeSuppressesCachedWorkflow()", source)
        self.assertIn("return 'Not checked'", source)
        self.assertIn("workflowStatus.textContent !== nextValue", source)
        self.assertIn("element.textContent !== displayValue", source)
        self.assertIn("alreadyStable", source)

    def test_workflow_badge_cache_suppression_semantics_are_explicit(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)

        self.assertIn("function dashboardRuntimeModeSuppressesCachedWorkflow()", source)
        self.assertIn("toLowerCase() === 'full db mode'", source)
        self.assertIn("if (dashboardRuntimeModeSuppressesCachedWorkflow() && !screen3WorkflowRuntimeFreshChecked(state))", source)
        self.assertIn("screen3WorkflowRuntimeFreshChecked(state)", source)
        self.assertIn("return screen3CachedWorkflowStatusLabel(safeValue)", source)
        self.assertNotIn("refreshWorkflowHealthStatusOnPageLoad", source)
        self.assertNotIn("recordWorkflowHealthStatus", source)

    def test_screen2_runtime_options_visible_state_reconciles_with_rows(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)

        for key in (
            "screen3RuntimeOptionsStatus",
            "screen3RuntimeOptionsDbPersistenceStatus",
            "screen3RuntimeOptionsLoadedRows",
            "screen3RuntimeOptionsCount",
            "screen3RuntimeOptionsLoadedAt",
            "screen3RuntimeOptionsIncludedTables",
            "screen3RuntimeOptionsCacheStatus",
            "screen3RuntimeOptionsMessage",
            "screen3RuntimeOptionsSourceTables",
            "screen3RuntimeOptionsCoverageMessage",
            "screen3LiveServiceStatus",
        ):
            with self.subTest(key=key):
                self.assertIn(key, source)

        self.assertIn("function updateScreen3RuntimeOptionPanels(responseBody, stateOverride)", source)
        self.assertIn("const refreshedState = stateOverride", source)
        self.assertIn("? sanitizeDashboardState(stateOverride)", source)
        self.assertIn(": readDashboardState();", source)
        self.assertIn("updateScreen3RuntimeOptionPanels(body, state)", source)
        self.assertIn(
            "updateScreen3RuntimeOptionPanels(screen3RuntimeOptionsBodyFromCache(cache), restoredState)",
            source,
        )
        self.assertIn("screen3LiveServiceStatusSource = 'browser-cache'", source)
        self.assertIn("function screen3RuntimeOptionsRestoredFromCache(state)", source)
        self.assertIn("return screen3RuntimeOptionsLiveLoaded(safeState) ||", source)
        self.assertIn("screen3RuntimeOptionsRestoredFromCache(safeState);", source)
        self.assertIn("screen3WorkflowRuntimeFreshChecked(safeState)", source)
        self.assertIn(
            "Cached runtime options are available for continuity only; they are not active evidence.",
            source,
        )
        self.assertIn("screen2ShouldHydrateFromPersistentState()", source)
        self.assertIn("isScreen2ControlPage() && Boolean(readScreen3RuntimeOptionsCache())", source)
        self.assertIn("readLocalStorageState()", source)
        self.assertIn("parseHashState(window.location.hash)", source)
        self.assertIn("if (!screen3RuntimeOptionsAreLoaded(nextState))", source)
        self.assertNotIn(
            "const refreshedState = readDashboardState();\n"
            "        updateDashboardStateInputs(refreshedState, document);",
            source,
        )

    def test_screen2_target_assignment_preserves_loaded_runtime_options_state(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        select_start = source.index("function selectDashboardElement(element)")
        select_end = source.index("function handleDashboardStateInput(event)")
        select_function = source[select_start:select_end]
        assignment_refresh_start = source.index("function refreshScreen3RuntimeAssignmentUi(root, state)")
        assignment_refresh_end = source.index("function selectDashboardElement(element)")
        assignment_refresh_function = source[assignment_refresh_start:assignment_refresh_end]
        continuity_start = source.index("function copyScreen2RuntimeOptionsContinuityState(target, source)")
        continuity_end = source.index("function readDashboardStateBeforeScreen2EvidenceEnforcement()")
        continuity_function = source[continuity_start:continuity_end]

        self.assertIn("function readDashboardStateBeforeScreen2EvidenceEnforcement()", source)
        self.assertIn("readLocalStorageState()", source)
        self.assertIn("parseHashState(window.location.hash)", source)
        self.assertIn("withoutInactiveSourceSelection(state)", source)
        self.assertIn(
            "['screen3ApplySelectionTarget', 'runtimeScope', 'snapshot'].indexOf(selectType) >= 0",
            select_function,
        )
        self.assertIn("readDashboardStateBeforeScreen2EvidenceEnforcement()", select_function)
        self.assertIn("screen2RuntimeOptionsContinuityStateForSelection(", select_function)
        self.assertNotIn("const nextState = readDashboardState();", select_function)
        self.assertIn("function screen2CurrentActiveSelectionTarget(state)", source)
        self.assertIn("const activeSelectionTarget = screen2CurrentActiveSelectionTarget(nextState)", select_function)
        self.assertIn("nextState.screen3ActiveSelectionTarget = activeSelectionTarget", select_function)
        self.assertIn("function valueForRuntimeScopeRow(element)", source)
        self.assertIn("data-screen3-row-id", source)
        self.assertIn("const selectedRowId = valueForRuntimeScopeRow(element)", select_function)
        self.assertIn("nextState.screen3SelectedTargetARowId = selectedRowId", select_function)
        self.assertIn("nextState.screen3SelectedTargetBRowId = selectedRowId", select_function)
        self.assertIn("nextState.screen3SelectedRuntimeScopeRowId = selectedRowId", select_function)
        self.assertIn("nextState.screen3SelectedTargetAIntervalId = selectedIntervalId", select_function)
        self.assertIn("nextState.screen3SelectedTargetBIntervalId = selectedIntervalId", select_function)
        self.assertIn("data-screen3-runtime-row-apply-button", source)
        self.assertIn("cell.setAttribute('data-screen3-runtime-row-apply-button', 'true')", source)
        self.assertIn("cell.setAttribute('data-screen3-row-id', rowIdentity)", source)
        self.assertIn("cell.setAttribute('data-dashboard-select-type', 'runtimeScope')", source)
        self.assertIn("cell.setAttribute('data-dashboard-select-id', rowIdentity)", source)
        self.assertIn("function screen3RuntimeApplyElement(element)", source)
        self.assertIn(
            "const applyControl = element.closest('[data-screen3-runtime-row-apply-button=\"true\"]')",
            source,
        )
        self.assertIn("const runtimeApplyElement = screen3RuntimeApplyElement(event.target)", source)
        self.assertIn("selectDashboardElement(runtimeApplyElement)", source)
        self.assertIn("function refreshScreen3RuntimeAssignmentUi(root, state)", source)
        self.assertIn("updateDashboardStateInputs(safeState, scope)", assignment_refresh_function)
        self.assertIn("markSelectedElement(safeState, scope)", assignment_refresh_function)
        self.assertIn("updateScreen3RuntimeFilters(safeState, scope)", assignment_refresh_function)
        self.assertIn("updateScreen3RowApplyLabels(safeState, scope)", assignment_refresh_function)
        self.assertIn("const writtenState = writeDashboardState(nextState)", select_function)
        self.assertIn("if (selectType === 'screen3ApplySelectionTarget')", select_function)
        self.assertIn("refreshScreen3RuntimeAssignmentUi(document, nextState)", select_function)
        self.assertNotIn("screen3RuntimeOptionsLoadedRows = '0'", select_function)
        self.assertNotIn("screen3RuntimeOptionsCount = '0'", select_function)

        for key in (
            "screen3RuntimeOptionsStatus",
            "screen3RuntimeOptionsLoadedRows",
            "screen3RuntimeOptionsCount",
            "screen3RuntimeOptionsIncludedTables",
            "screen3RuntimeOptionsLoadedAt",
            "screen3RuntimeOptionsDbPersistenceStatus",
            "screen3RuntimeOptionsCacheStatus",
            "screen3RuntimeOptionsSourceTables",
            "screen3RuntimeOptionsCoverageMessage",
            "screen3LiveServiceStatus",
        ):
            with self.subTest(key=key):
                self.assertIn(key, continuity_function)

        self.assertIn("Object.assign({}, storedState, safeBase)", source)
        self.assertIn("copyScreen2RuntimeOptionsContinuityState(", source)
        self.assertIn("screen3ReconcileCachedSelectionState(restoredState, cache)", source)

    def test_existing_platform_evidence_selected_context_gates_downstream_display(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        styles = read_text(ROOT / "src" / "reporting" / "dashboard" / "styles.py")

        self.assertIn("function screen2ExistingEvidenceContextSelected(state)", source)
        self.assertIn("function screen2ExistingEvidenceFreshReady(state)", source)
        self.assertIn("function dashboardSelectedEvidenceContextAvailable(state)", source)
        self.assertIn("function dashboardEvidenceContextMode(state)", source)
        self.assertIn("screen2_existing_evidence_live", source)
        self.assertIn("screen2_existing_evidence_cached", source)
        self.assertIn("function preserveScreen2ExistingEvidenceContextState(state)", source)
        self.assertIn("SCREEN2_EXISTING_EVIDENCE_CONTEXT_STATE_KEYS", source)
        self.assertIn("screen3SelectedRuntimeScopeRowId", source)
        self.assertIn("screen3SelectedTargetARowId", source)
        self.assertIn("screen3SelectedTargetBRowId", source)
        self.assertIn("selectedRuntimeScope", source)
        self.assertIn("screen3RuntimeOptionsAreLoaded(safeState)", source)
        self.assertIn("screen2ExistingEvidenceContextSelected(safeState)", source)
        self.assertIn(
            "if (!dashboardSelectedEvidenceContextAvailable(safeState) && !sourceSelectionIsCurrent(safeState))",
            source,
        )
        self.assertIn("const contextAvailable = dashboardSelectedEvidenceContextAvailable(safeState)", source)
        self.assertIn("data-dashboard-evidence-context-available", source)
        self.assertIn("body[data-dashboard-evidence-context-available=\"true\"]", styles)
        self.assertIn(
            "Screen 2 selected existing evidence is restored from browser cache for display continuity only.",
            source,
        )
        self.assertIn(
            "Screen 2 selected existing evidence is current from a fresh runtime-options response.",
            source,
        )
        self.assertIn("Target A Context", source)
        self.assertIn("Target B Context", source)
        self.assertIn("Runtime Scope selection required for Diagnostic Snapshot", source)
        self.assertNotIn("comparison output created by selected context", source.lower())

    def test_screen2_runtime_selection_deselect_controls_are_scoped(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        styles = read_text(ROOT / "src" / "reporting" / "dashboard" / "styles.py")
        select_start = source.index("function selectDashboardElement(element)")
        select_end = source.index("function handleDashboardStateInput(event)")
        select_function = source[select_start:select_end]
        clear_start = source.index("function handleScreen3RuntimeSelectionClearClick(event)")
        clear_end = source.index("function handleDashboardSelectableClick(event)")
        clear_handler = source[clear_start:clear_end]

        self.assertIn("SCREEN3_RUNTIME_SCOPE_SELECTION_KEYS", source)
        self.assertIn("SCREEN3_TARGET_A_SELECTION_KEYS", source)
        self.assertIn("SCREEN3_TARGET_B_SELECTION_KEYS", source)
        self.assertIn("function clearScreen3RuntimeScopeSelection(state)", source)
        self.assertIn("function clearScreen3ComparisonTargetSelection(state, targetName)", source)
        self.assertIn("function clearScreen3RuntimeSelection(state, selectionName)", source)
        self.assertIn("function screen3RuntimeRowAlreadySelectedForTarget(state, targetName, rowId)", source)
        self.assertIn(
            "screen3RuntimeRowAlreadySelectedForTarget(previousState, activeSelectionTarget, selectedRowId)",
            select_function,
        )
        self.assertIn("clearScreen3RuntimeSelection(nextState, activeSelectionTarget)", select_function)
        self.assertIn("refreshScreen3RuntimeAssignmentUi(document, nextState)", select_function)

        for value in ("runtime-scope", "target-a", "target-b", "comparison-targets", "all"):
            with self.subTest(value=value):
                self.assertIn(f'data-screen3-clear-runtime-selection="{value}"', source)

        self.assertIn("SCREEN3_RUNTIME_SELECTION_CLEAR_SELECTOR", source)
        self.assertIn("handleScreen3RuntimeSelectionClearClick", source)
        self.assertIn("document.addEventListener('click', handleScreen3RuntimeSelectionClearClick)", source)
        self.assertIn("readDashboardStateBeforeScreen2EvidenceEnforcement()", clear_handler)
        self.assertIn("screen2RuntimeOptionsContinuityStateForSelection(", clear_handler)
        self.assertIn("clearScreen3RuntimeSelection(nextState, clearMode)", clear_handler)
        self.assertIn("updateScreen2ExistingEvidenceReadiness(nextState)", clear_handler)
        self.assertIn("writeDashboardState(nextState)", clear_handler)
        self.assertIn("refreshScreen3RuntimeAssignmentUi(document, nextState)", clear_handler)
        self.assertNotIn("screen3RuntimeOptionsLoadedRows = '0'", clear_handler)
        self.assertNotIn("screen3RuntimeOptionsCount = '0'", clear_handler)
        self.assertIn(".screen3-selection-clear-controls", styles)

        target_a_keys = source[
            source.index("const SCREEN3_TARGET_A_SELECTION_KEYS"):
            source.index("const SCREEN3_TARGET_B_SELECTION_KEYS")
        ]
        target_b_keys = source[
            source.index("const SCREEN3_TARGET_B_SELECTION_KEYS"):
            source.index("function clearDashboardStateKeys")
        ]
        runtime_keys = source[
            source.index("const SCREEN3_RUNTIME_SCOPE_SELECTION_KEYS"):
            source.index("const SCREEN3_TARGET_A_SELECTION_KEYS")
        ]
        self.assertIn("'screen3SelectedRuntimeScopeRowId'", runtime_keys)
        self.assertIn("'selectedRuntimeScope'", runtime_keys)
        self.assertNotIn("'screen3SelectedTargetARowId'", runtime_keys)
        self.assertNotIn("'screen3SelectedTargetBRowId'", runtime_keys)
        self.assertIn("'screen3SelectedTargetARowId'", target_a_keys)
        self.assertIn("'selectedComparisonTargetA'", target_a_keys)
        self.assertNotIn("'screen3SelectedRuntimeScopeRowId'", target_a_keys)
        self.assertNotIn("'screen3SelectedTargetBRowId'", target_a_keys)
        self.assertIn("'screen3SelectedTargetBRowId'", target_b_keys)
        self.assertIn("'selectedComparisonTargetB'", target_b_keys)
        self.assertNotIn("'screen3SelectedRuntimeScopeRowId'", target_b_keys)
        self.assertNotIn("'screen3SelectedTargetARowId'", target_b_keys)

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
