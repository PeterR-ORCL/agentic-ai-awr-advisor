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


class DashboardScreen4HistoricalReviewExplorationTests(unittest.TestCase):
    def test_01_import_compile_safety(self) -> None:
        ast.parse(read_text(HTML_DASHBOARD_PATH), filename=str(HTML_DASHBOARD_PATH))
        ast.parse(read_text(AI_METADATA_PATH), filename=str(AI_METADATA_PATH))
        dashboard = dashboard_module()

        self.assertTrue(hasattr(dashboard, "_render_screen4_historical_exploration"))
        self.assertTrue(hasattr(dashboard, "_build_screen4_historical_exploration_model"))
        self.assertTrue(hasattr(dashboard, "_render_screen4_mode_selector_shell"))
        self.assertTrue(hasattr(dashboard, "_render_screen4_historical_trend_panels"))
        self.assertTrue(hasattr(dashboard, "_build_screen4_evidence_context"))
        self.assertTrue(hasattr(dashboard, "_screen4_validate_deterministic_comparison_output"))
        self.assertTrue(hasattr(dashboard, "_screen4_build_comparative_review_state"))
        self.assertTrue(hasattr(dashboard, "_screen4_comparison_visualization_allowed"))
        self.assertTrue(hasattr(dashboard, "_render_screen4_comparative_review_panel"))
        self.assertTrue(hasattr(dashboard, "_screen4_graphic_allowed"))
        self.assertTrue(hasattr(dashboard, "_render_screen4_graphic_guard_empty_state"))

    def test_screen4_evidence_context_graphics_guard_summary_exists(self) -> None:
        rendered = self.render_screen4()

        required_phrases = (
            "Evidence Context &amp; Graphics Guard",
            "Screen 4 Graphics Boundary",
            "Screen 4 renders graphics only when deterministic evidence and context alignment allow it.",
            "Selected runtime state does not create historical truth.",
            "Prepared Target A/B state does not create comparison output.",
            "Browser cache does not create evidence.",
            "Selected Context",
            "Generated historical artifact context",
            "Artifact Alignment",
            "Same-DB historical context only",
            "Historical Review Eligibility",
            "Context-only historical evidence",
            "Single-AWR Review Eligibility",
            "Selected-scope graphics not ready for this evidence context",
            "Distribution / Violin Eligibility",
            "Context-only distribution evidence",
            "Fleet / Population",
            "No fleet/population graphics until a fleet evidence contract exists.",
            "Comparison Review Eligibility",
            "No prepared comparison context",
            "Graphics Boundary",
            "Page identity alone cannot select graphics.",
            'data-screen4-evidence-context-guard="true"',
            'data-screen4-graphics-selected-by="evidence-context"',
            'data-screen4-page-identity-alone="blocked"',
            'data-screen4-context-classification="same_db_historical_context"',
            'data-screen4-artifact-alignment-status="same_db_historical_available"',
            'data-screen4-comparison-output="unavailable"',
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_screen4_graphics_guard_marks_existing_graphics_context_only(self) -> None:
        rendered = self.render_screen4()

        for section_id in (
            "screen4-historical-trend-panels",
            "time-series-charts",
            "workload-violin-panel",
        ):
            with self.subTest(section=section_id):
                start = rendered.index(section_id)
                fragment = rendered[start:start + 900]
                self.assertIn('data-screen4-graphic-guard-state="context-only"', fragment)
                self.assertIn(
                    'data-screen4-artifact-alignment-status="same_db_historical_available"',
                    fragment,
                )

    def test_screen4_mode_selector_shell_exists_with_locked_modes(self) -> None:
        rendered = self.render_screen4()

        required_phrases = (
            "Screen 4 Evidence Review Mode Shell",
            "Evidence Review Modes",
            "Historical Review",
            "Comparative Review",
            "Deep Analysis",
            "Historical Review is active.",
            "Comparative Review requires deterministic comparison output before evidence can be reviewed here.",
            "Uses Target A/B context prepared in Screen 2.",
            "Prepared targets are selected context only",
            "Target A/B prepared-only state is not comparison output.",
            "Selected targets and cache-restored state do not create comparison evidence.",
            "Deterministic comparison output is required before comparative graphics can render.",
            "Screen 4 does not compute comparison in the browser.",
            "Deep Analysis is reserved for future structured expert evidence review.",
            "Screen 4 reflects upstream selected source, run, scope, and target context for display only.",
            "Deterministic evidence remains authoritative.",
            "Selected context does not create diagnosis, scores, readiness, comparison output, recommendations, actions, outcomes, or learning state.",
            "Browser state and cache restore display continuity only; they do not create evidence truth.",
            'data-screen4-context-contract="selected-context-display-only"',
            'data-screen4-evidence-context-boundary="true"',
            'data-screen4-mode="historical-review"',
            'data-screen4-mode-state="active"',
            'data-screen4-mode="comparative-review"',
            'data-screen4-mode-state="prepared-only"',
            'data-screen4-screen2-handoff="prepared-context-only"',
            'data-screen4-mode="deep-analysis"',
            'data-screen4-mode-state="reserved"',
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_screen4_fu6_product_wording_replaces_ambiguous_labels(self) -> None:
        rendered = self.render_screen4()

        required = (
            "Historical Artifact Context",
            "Historical Context Summary",
            "Historical Risk Signal",
            "Historical Action Posture",
            "Risk reflects the historical signal level; posture reflects the deterministic diagnostic handling path.",
            "Historical review actions are preview-only",
            "Historical supporting context only; this does not override Screen 3 selected-scope diagnosis.",
        )
        for phrase in required:
            with self.subTest(required=phrase):
                self.assertIn(phrase, rendered)

        forbidden = (
            "Current Selection Summary",
            "Historical Verdict",
            "Historical Posture",
            "Historical Context Posture",
            "Historical review disabled in this phase",
        )
        for phrase in forbidden:
            with self.subTest(forbidden=phrase):
                self.assertNotIn(phrase, rendered)

    def test_screen4_mode_selector_shell_is_static_and_non_mutating(self) -> None:
        rendered = self.render_screen4().lower()

        forbidden = (
            "data-screen4-provider-route",
            "/phase7/dashboard/screen4",
            "comparison-output-created",
            "computed a-vs-b delta",
            "target a improved",
            "target b improved",
            "target a degraded",
            "target b degraded",
            "comparison-violin-panel",
            "materialization approved",
            "runtime eligibility approved",
            "screen 4 assigns readiness",
            "screen 4 computed comparison",
            "screen 4 created workflow record",
            "comparison output exists now",
            "comparison deltas are available",
            "improvement/degradation/stable result",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, rendered)
        self.assertNotIn("period comparison", rendered.lower())

    def test_screen4_evidence_context_contract_doc_locks_handoff_boundaries(self) -> None:
        doc_path = DOCS / "phase7_screen4_evidence_review_mode_shell.md"
        self.assertTrue(doc_path.is_file())
        text = read_text(doc_path).lower()

        required_phrases = (
            "cross-screen runtime rule",
            "screens 3-6 must vary by the source, run, scope, target, and comparison-preparation context selected in screens 1-2",
            "that variation is presentation and context selection only unless a governed backend workflow explicitly owns the behavior",
            "screen 1 may establish new-source intake",
            "screen 2 may establish existing platform evidence",
            "selected runtime context comes from screen 1 source intake/source-governance handoff and screen 2 runtime scope",
            "it is a context selector only",
            "browser cache continuity comes from localstorage",
            "future unavailable output refers to planned deterministic comparison",
            "llm explanatory wording is wording only",
            "screen 1 and screen 2 handoff to screen 4",
            "screen 4 must not treat comparison readiness as comparison evidence",
            "screen 4 uses the handoff to vary the visible review context",
            "prepared targets are selected context only",
            "selected targets and cache-restored state do not create comparison evidence",
            "screen 4 does not compute comparison in the browser",
            "manual generated-html patching must not be the only artifact update",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_screen4_historical_exploration_exists_with_summary_and_safety_labels(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen4()

        self.assertIn("Screen 4 Historical Review Exploration", source)
        self.assertIn("Screen 4 Historical Review Exploration", rendered)
        self.assertIn("data-dashboard-selected-summary", rendered)
        self.assertIn('data-dashboard-selected-summary-kind="screen4-historical"', rendered)
        self.assertIn("Selected Historical Summary", rendered)
        self.assertIn("Read-only historical exploration", rendered)
        self.assertIn("Exploratory only", rendered)
        self.assertIn("No backend writes", rendered)
        self.assertIn("No approval controls", rendered)
        self.assertIn("No runtime activation", rendered)

    def test_screen4_selected_summary_hydration_uses_product_safe_formatter(self) -> None:
        dashboard = dashboard_module()
        rendered = self.render_screen4()
        script = dashboard._build_dashboard_interactivity_javascript()

        summary_start = rendered.index("screen4-selected-historical-summary")
        summary_fragment = rendered[summary_start: rendered.index("</p>", summary_start)]

        self.assertIn('data-dashboard-selected-summary-kind="screen4-historical"', summary_fragment)
        self.assertIn(
            "Read-only historical exploration: no local selection. Historical output remains unchanged.",
            summary_fragment,
        )
        for raw_key in (
            "selectedAwr",
            "selectedRun",
            "selectedDb",
            "selectedDbid",
            "selectedInstance",
            "screen3RuntimeOptionsStatus",
            "screen3LiveServiceStatus",
            "sourceSelectionSessionId",
        ):
            with self.subTest(raw_key=raw_key):
                self.assertNotIn(raw_key, summary_fragment)

        self.assertIn("function buildScreen4HistoricalSelectedSummary", script)
        self.assertIn("data-dashboard-selected-summary-kind", script)
        self.assertIn("Evidence path", script)
        self.assertIn("Runtime Scope", script)
        self.assertIn("Context Status", script)
        self.assertIn("Cached selection restored for UI continuity", script)
        self.assertIn(
            "selection state does not create diagnosis, recommendation, comparison output, action, outcome, learning state, materialization, or runtime eligibility",
            script,
        )
        formatter = script[
            script.index("function buildScreen4HistoricalSelectedSummary"):
            script.index("function buildGenericSelectedSummary")
        ]
        self.assertNotIn("Active selections:", formatter)
        self.assertNotIn("key + ': '", formatter)

    def test_screen4_historical_context_labels_are_product_safe(self) -> None:
        rendered = self.render_screen4()

        required = (
            "Historical Period Context",
            "Latest vs Historical Context",
            "Supporting Memory Context",
            "Memory context is supporting historical evidence only and does not change diagnosis, recommendation",
            "learning state, materialization, or runtime eligibility",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        forbidden = (
            "Period Comparison",
            "Memory Review",
            "Latest vs Trend",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, rendered)

    def test_selector_metadata_exists_for_historical_categories(self) -> None:
        rendered = self.render_screen4()

        required = (
            'data-dashboard-selectable="true"',
            'data-dashboard-select-type="historical-domain"',
            'data-dashboard-select-key="selectedDomain"',
            'data-dashboard-filter-key="selectedDomain"',
            'data-dashboard-filter-value="CPU"',
            'data-dashboard-select-domain="CPU"',
            'data-dashboard-select-type="historical-window"',
            'data-dashboard-select-key="selectedHistoricalWindow"',
            'data-dashboard-select-type="trend-metric"',
            'data-dashboard-select-key="selectedTrendMetric"',
            'data-dashboard-select-type="anomaly-group"',
            'data-dashboard-select-key="selectedAnomalyGroup"',
            'data-dashboard-select-type="distribution"',
            'data-dashboard-select-key="selectedDistribution"',
            'data-dashboard-select-type="similar-case"',
            'data-dashboard-select-key="selectedSimilarCase"',
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_authoritative_domain_controls_are_present(self) -> None:
        rendered = self.render_screen4()

        for domain in ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG"):
            with self.subTest(domain=domain):
                self.assertIn(f'data-dashboard-filter-value="{domain}"', rendered)
                self.assertIn(f">{domain}</span>", rendered)

    def test_required_safety_wording_is_rendered(self) -> None:
        rendered = self.render_screen4()

        required_phrases = (
            "Read-only historical exploration",
            "Exploratory only",
            "No backend writes",
            "Does not change historical truth",
            "Does not recalculate trends",
            "Does not reclassify anomalies",
            "Does not change baseline",
            "Does not change diagnostic truth",
            "Does not change recommendation truth",
            "Semantic/learning context is not historical evidence",
            "Selection only highlights deterministic historical context",
            "Cross-Screen Selection Propagation is browser-side only",
            "URL hash/localStorage state is not authoritative truth",
            "Future A/B comparison violin panels belong on Screen 4 but may render only from validated deterministic comparison output",
            "LLM-assisted wording may explain validated deterministic comparison output only after that output exists",
            "it does not compute comparison meaning or decide outcome direction",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_screen4_comparative_review_guarded_state_panel_exists(self) -> None:
        rendered = self.render_screen4()

        required_phrases = (
            "Comparative Review Guarded State",
            "Comparative Review is not ready yet.",
            "No governed deterministic comparison output has been returned to Screen 4.",
            "Prepared Target A/B context can identify what should be compared, but it does not create comparison evidence.",
            "No prepared comparison context is available for Screen 4.",
            "Target A/B selections are preparation only.",
            "Deterministic comparison output is required before Screen 4 can show comparative evidence.",
            "No comparison graphics are available because no validated deterministic comparison output contract is present.",
            "No comparison visualizations are permitted for this state.",
            "Prepare Target A/B context upstream before comparative review.",
            'data-screen4-mode-section="comparative-review"',
            'data-screen4-comparative-review-state="comparison_unavailable"',
            'data-screen4-comparison-output-ready="false"',
            'data-screen4-comparison-graphics-state="blocked"',
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        comparative_section = rendered[
            rendered.index("screen4-comparative-review-guard"):
            rendered.index("screen4-historical-exploration")
        ].lower()
        for forbidden in (
            "improved",
            "degraded",
            "stable",
            "better",
            "worse",
            "winner",
            "loser",
            "delta conclusion",
            "comparison trend",
            "comparison-violin-panel",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, comparative_section)

    def test_screen4_wording_keeps_historical_context_distinct_from_comparison(self) -> None:
        dashboard = dashboard_module()
        rendered = self.render_screen4()
        gated = dashboard._wrap_downstream_evidence_gate("screen_4", "<div>body</div>")

        self.assertIn(
            "Target A/B preparation alone does not create Screen 4 comparison evidence.",
            gated,
        )
        self.assertIn("Complete source intake or select a runtime scope first.", gated)

        forbidden_historical_phrases = (
            "comparison context only",
            "supporting comparison context",
            "cluster comparison context",
            "historical comparison only",
            "period comparison",
            "historical proof",
            "strongest historical proof",
            "CPU-led historical story",
            "CPU remains dominant across the selected window",
        )
        for phrase in forbidden_historical_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase.lower(), rendered.lower())

    def test_screen4_historical_trend_panels_productize_existing_evidence(self) -> None:
        rendered = self.render_screen4()

        required_phrases = (
            "Historical Trend Panels",
            "Deterministic historical trend evidence for the generated historical artifact.",
            "This is context-only historical evidence, not selected runtime-scope truth unless",
            "artifact alignment is exact or contains the selected scope.",
            "Trend evidence is context only and does not change diagnosis, recommendation, or",
            "runtime behavior.",
            "Source is deterministic/generated trend evidence already present in the dashboard payload.",
            "Graphics are not selected by page identity alone; they require deterministic evidence and context alignment.",
            "Browser cache may restore UI context only; it does not create trend evidence truth.",
            "Trend Evidence Available",
            "Artifact Alignment",
            "Guard State",
            "Historical Samples",
            "Metric Groups",
            "Coverage",
            "Current / Latest Interval",
            "Worst Historical Interval",
            "Trend Direction",
            "Insufficient History",
            "Metric",
            "Domain",
            "Latest",
            "Baseline / Prior",
            "Evidence Note",
            "DB CPU % DB Time",
            "CPU",
            "Upward pressure",
            "Existing deterministic trend evidence; displayed as historical context only.",
            'data-screen4-mode-section="historical-review"',
            'data-screen4-historical-trend-panels="true"',
            'data-screen4-trend-truth-boundary="deterministic-generated-context-only"',
            'data-screen4-graphic-guard-state="context-only"',
            'data-screen4-artifact-alignment-status="same_db_historical_available"',
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        trend_section = rendered[
            rendered.index("screen4-historical-trend-panels"):
            rendered.index("time-series-charts")
        ]
        forbidden = (
            "Target A beat Target B",
            "A/B result",
            "comparison result",
            "recommendation updated",
            "diagnosis changed",
            "LLM found",
            "AI decided",
            "learning candidate created",
            "runtime eligibility approved",
            "comparison-violin-panel",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase.lower(), trend_section.lower())

    def test_screen4_historical_trend_panels_empty_state_is_safe(self) -> None:
        dashboard = dashboard_module()
        rendered = dashboard._render_screen4_historical_trend_panels(
            self.sample_screen4_model(),
            chart_payload={"time_series_charts": {"snapshot_labels": []}},
            time_series_groups=[],
        )

        self.assertIn(
            "No deterministic historical trend evidence is available for this run or selected evidence context.",
            rendered,
        )
        self.assertIn(
            "This does not change the diagnostic snapshot or recommendation output.",
            rendered,
        )
        self.assertIn("No deterministic trend coverage available", rendered)
        self.assertNotIn("data-screen4-provider-route", rendered)
        self.assertNotIn("comparison-violin-panel", rendered)
        self.assertNotIn("learning candidate created", rendered.lower())

    def test_screen4_historical_trend_panels_respect_blocked_guard(self) -> None:
        dashboard = dashboard_module()
        rendered = dashboard._render_screen4_historical_trend_panels(
            self.sample_screen4_model(),
            chart_payload=self.sample_chart_payload(),
            time_series_groups=self.sample_time_series_groups(),
            evidence_context={
                "historical_trend_panels_allowed": False,
                "historical_trend_panels_context_only": False,
                "artifact_alignment_status": "different_artifact",
                "artifact_alignment_label": "Different artifact; context only",
            },
        )

        self.assertIn('data-screen4-graphic-guard-state="blocked"', rendered)
        self.assertIn(
            'data-screen4-artifact-alignment-status="different_artifact"',
            rendered,
        )
        self.assertIn(
            "Historical trend graphics are not rendered because this evidence context is not aligned",
            rendered,
        )
        self.assertNotIn("<th>Metric</th>", rendered)
        self.assertNotIn("Target A beat Target B", rendered)
        self.assertNotIn("comparison-violin-panel", rendered)

    def test_no_unsafe_controls_or_write_runtime_are_introduced(self) -> None:
        dashboard = dashboard_module()
        rendered = self.render_screen4().lower()
        source = read_text(HTML_DASHBOARD_PATH).lower()
        script = dashboard._build_dashboard_interactivity_javascript().lower()

        forbidden_controls = (
            "<button",
            "<form",
            "method=\"post\"",
            "type=\"submit\"",
            "onclick=",
            "data-action=",
            "role=\"button\"",
            "approval-control",
            "write-control",
            "learning-approval-control",
            "apply-control",
        )
        for control in forbidden_controls:
            with self.subTest(control=control):
                self.assertNotIn(control, rendered)

        forbidden_writes = (
            "fetch(",
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
                self.assertNotIn(phrase, rendered)
                if phrase != "fetch(":
                    self.assertNotIn(phrase, script)
                    self.assertNotIn(phrase, source)

    def test_no_semantic_learning_or_governance_historical_evidence(self) -> None:
        dashboard = dashboard_module()
        screen_4_source = inspect.getsource(dashboard._render_screen4_historical_exploration)
        rendered = self.render_screen4()

        forbidden = (
            "semantic recall as historical evidence",
            "semantic candidate context as historical evidence",
            "learning candidates as historical evidence",
            "governance status as historical evidence",
            "selectedLearningCandidate",
            "selectedSemanticItem",
            "selectedGovernanceItem",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, screen_4_source)
                self.assertNotIn(phrase, rendered)

        self.assertIn("Semantic/learning context is not historical evidence", rendered)

    def test_no_screen2_or_screen5_truth_drift(self) -> None:
        dashboard = dashboard_module()
        screen_2_source = inspect.getsource(dashboard._render_screen_2_page)
        screen_5_source = inspect.getsource(dashboard._render_screen_5_page)

        forbidden = (
            "selectedHistoricalWindow",
            "selectedTrendMetric",
            "selectedAnomalyGroup",
            "selectedDistribution",
            "selectedSimilarCase",
            "Screen 4 Historical Review Exploration",
            "historical exploration as recommendation truth",
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
                self.assertNotIn("Screen 4 Historical Review Exploration", text)
                self.assertNotIn("DashboardInteractivityFoundation", text)

    def test_documentation_exists_and_contains_required_boundaries(self) -> None:
        doc_path = DOCS / "phase7_screen4_historical_review_exploration.md"
        self.assertTrue(doc_path.is_file())
        text = read_text(doc_path).lower()

        required_phrases = (
            "read-only",
            "exploratory only",
            "no backend writes",
            "no approval controls",
            "no write controls",
            "does not change historical truth",
            "does not recalculate trends",
            "does not reclassify anomalies",
            "does not change baseline",
            "does not change similarity results",
            "does not change diagnostic truth",
            "does not change recommendation truth",
            "semantic/learning context is not historical evidence",
            "full cross-screen propagation remains future 7h.8",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def render_screen4(self) -> str:
        return dashboard_module()._render_screen_4_page(
            self.sample_screen4_model(),
            chart_payload=self.sample_chart_payload(),
            violin_metric_groups=self.sample_violin_metric_groups(),
            time_series_groups=self.sample_time_series_groups(),
            derived_scalar_metrics={"pga_spill_pressure": 4.5},
        )

    @staticmethod
    def sample_screen4_model() -> dict[str, object]:
        return {
            "header": {
                "scope_label": "ORCL / 123456",
                "instance_name": "ORCL1",
                "host_name": "dbhost01",
                "snapshot_count": 4,
                "comparison_window": "4 snapshots / 2 hours",
            },
            "current_selection_summary": {
                "current_window": "Latest snapshot (10:00-11:00)",
                "comparison_mode": "Latest interval vs broader comparison window",
                "latest_vs_prior": "Latest interval aligns with the broader window.",
            },
            "historical_verdict": {
                "display_severity_label": "High",
                "historical_stability": "Mixed",
                "anomaly_burden": "2 anomaly windows",
                "historical_posture": "TUNE FIRST",
            },
            "normalized_decision": {
                "primary_issue": "CPU",
                "overall_status": "WARNING",
                "display_severity_label": "High",
                "confidence": 0.82,
                "domain_scores": {"CPU": 72.0, "IO": 18.0, "COMMIT": 12.0},
            },
            "historical_summary": {"summary": "CPU remained visible across the window."},
            "trend_review": {
                "trends": {
                    "time_series": {
                        "trend_directions": {
                            "cpu": "degrading",
                        },
                    },
                    "findings": ["CPU stayed visible across snapshots."],
                },
                "trend_summary": {
                    "summary": "CPU trend remained visible.",
                    "findings": ["CPU stayed visible across snapshots."],
                }
            },
            "anomaly_review": {
                "anomalies": {"count": 2},
                "anomaly_summary": {
                    "windows": [
                        {"label": "snap-2 CPU anomaly", "severity": "medium"},
                        {"label": "snap-3 IO anomaly", "severity": "low"},
                    ]
                },
            },
            "comparison_review": {
                "latest_interval": "10:00-11:00",
                "worst_interval": "09:00-10:00",
                "latest_vs_trend": "Latest remains aligned with history.",
                "drift_summary": "No contradictory drift.",
            },
            "similarity_evidence": {
                "enabled": True,
                "similar_cases": [
                    {
                        "awr_id": 7002,
                        "db_name": "ORCL",
                        "similarity_score": 0.91,
                        "distance": 0.09,
                        "primary_signal_domain": "CPU",
                        "risk_level": "High",
                        "workload_class": "OLTP",
                    }
                ],
                "workload_cluster": {"cluster_label": "CPU-led OLTP"},
                "pattern_rarity": {"is_rare_pattern": False, "reason": "Common CPU-led case."},
                "anomaly_validation": {"supports_anomaly": True, "reason": "Similar cases exist."},
            },
            "visual_analysis": {"story": {"section_order": ["time_series", "violin"]}},
            "historical_scope_memory": {},
            "topology_platform_review": {},
            "explanation_panel": {},
        }

    @staticmethod
    def sample_chart_payload() -> dict[str, object]:
        return {
            "time_series_charts": {
                "snapshot_labels": ["snap-1", "snap-2", "snap-3", "snap-4"],
                "cpu_trend": [18.0, 24.0, 31.0, 42.0],
            },
            "violin_panel": {},
        }

    @staticmethod
    def sample_time_series_groups() -> list[dict[str, object]]:
        return [
            {
                "group_key": "cpu",
                "group_title": "CPU Time-Series Charts",
                "charts": [
                    {
                        "key": "cpu_trend",
                        "container_id": "timeSeriesCpuTrend",
                        "title": "DB CPU % DB Time",
                        "label": "DB CPU % DB time",
                        "color": "rgba(255, 107, 107, 0.92)",
                    }
                ],
            }
        ]

    @staticmethod
    def sample_violin_metric_groups() -> list[dict[str, object]]:
        return [
            {
                "group_key": "workload",
                "group_title": "Workload Distributions",
                "group_note": "Cluster-level workload values aggregated per snapshot.",
                "metrics": [
                    {
                        "payload_key": "cluster_cpu_pct_db_time",
                        "container_id": "violinClusterCpuPct",
                        "title": "Cluster CPU % DB Time",
                        "color": "rgba(255, 107, 107, 0.72)",
                    }
                ],
            }
        ]

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
