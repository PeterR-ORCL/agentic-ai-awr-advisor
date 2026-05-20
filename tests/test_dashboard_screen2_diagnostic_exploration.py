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


class DashboardScreen2DiagnosticExplorationTests(unittest.TestCase):
    def test_01_import_compile_safety(self) -> None:
        ast.parse(read_text(HTML_DASHBOARD_PATH), filename=str(HTML_DASHBOARD_PATH))
        ast.parse(read_text(AI_METADATA_PATH), filename=str(AI_METADATA_PATH))
        dashboard = dashboard_module()

        self.assertTrue(hasattr(dashboard, "_render_screen2_diagnostic_exploration"))
        self.assertTrue(hasattr(dashboard, "_build_screen2_diagnostic_exploration_model"))

    def test_screen2_diagnostic_exploration_exists_with_summary_and_safety_labels(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen2()

        self.assertIn("Interactive Evidence Focus", source)
        self.assertIn("Interactive Evidence Focus", rendered)
        self.assertIn('data-screen2-focus="selected_target"', rendered)
        self.assertIn("Evidence focus only", rendered)
        self.assertIn("Explanation focus", rendered)
        self.assertIn("No truth change", rendered)
        self.assertIn("No runtime action", rendered)

    def test_selector_metadata_exists_for_domain_evidence_metric_wait_and_sql(self) -> None:
        rendered = self.render_screen2()

        required = (
            'data-dashboard-selectable="true"',
            'data-dashboard-select-type="diagnostic-domain"',
            'data-dashboard-select-key="selectedDomain"',
            'data-dashboard-filter-key="selectedDomain"',
            'data-dashboard-filter-value="CPU"',
            'data-dashboard-select-type="evidence-group"',
            'data-dashboard-select-key="selectedEvidenceGroup"',
            'data-dashboard-select-type="metric-group"',
            'data-dashboard-select-key="selectedMetricGroup"',
            'data-dashboard-select-type="wait-event-group"',
            'data-dashboard-select-key="selectedWaitEventGroup"',
            'data-dashboard-select-type="sql-signal"',
            'data-dashboard-select-key="selectedSqlSignal"',
            'data-dashboard-select-type="diagnostic-section"',
            'data-dashboard-select-key="selectedDiagnosticSection"',
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_authoritative_domain_controls_are_case_evidence_backed(self) -> None:
        rendered = self.render_screen2()
        domain_selector = rendered[
            rendered.index("<h3>Diagnostic Domain Selector</h3>"):
            rendered.index("<h3>Evidence Group Selector</h3>")
        ]

        for domain in ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG"):
            with self.subTest(domain=domain):
                self.assertIn(f'data-dashboard-filter-value="{domain}"', domain_selector)
                self.assertIn(f"<strong>{domain}</strong>", domain_selector)
        for evidence_state in ("Evidence present", "No material evidence"):
            with self.subTest(evidence_state=evidence_state):
                self.assertIn(evidence_state, domain_selector)
        self.assertIn("screen2-selector-kicker", domain_selector)

        evidence_selector = rendered[
            rendered.index("<h3>Evidence Group Selector</h3>"):
            rendered.index("<h3>Metric / Score Group Selector</h3>")
        ]
        self.assertIn('data-screen2-domain-scoped="true"', evidence_selector)
        self.assertIn("Select a domain lens to see evidence groups for that domain.", evidence_selector)
        self.assertIn('data-dashboard-select-domain="CPU"', evidence_selector)
        self.assertIn('data-dashboard-select-domain="IO"', evidence_selector)
        self.assertIn('data-dashboard-select-domain="COMMIT"', evidence_selector)
        for label in ("CPU Signal", "I/O Signal", "Commit Signal"):
            with self.subTest(label=label):
                self.assertIn(f"<strong>{label}</strong>", evidence_selector)
        for unavailable_label in ("Memory Signal", "RAC Signal", "ADG Signal"):
            with self.subTest(unavailable_label=unavailable_label):
                self.assertNotIn(f"<strong>{unavailable_label}</strong>", evidence_selector)

        metric_selector = rendered[
            rendered.index("<h3>Metric / Score Group Selector</h3>"):
            rendered.index("<h3>Wait Event Selector</h3>")
        ]
        self.assertIn('data-screen2-domain-scoped="true"', metric_selector)
        self.assertIn("Select a domain lens to see metric focus items for that domain.", metric_selector)
        self.assertIn("No metric focus items are available for the active {domain} lens.", metric_selector)
        self.assertIn('data-dashboard-select-domain="CPU"', metric_selector)
        self.assertIn('data-dashboard-select-domain="IO"', metric_selector)
        for unavailable_score in ("CPU score", "IO score", "MEMORY score", "COMMIT score", "RAC score", "ADG score"):
            with self.subTest(unavailable_score=unavailable_score):
                self.assertNotIn(f"<strong>{unavailable_score}</strong>", metric_selector)
        for metric in ("DB CPU % DB Time", "User I/O % DB Time"):
            with self.subTest(metric=metric):
                self.assertIn(f"<strong>{metric}</strong>", metric_selector)
        for unavailable_metric in ("PGA Spill Pressure", "Cluster Wait %"):
            with self.subTest(unavailable_metric=unavailable_metric):
                self.assertNotIn(f"<strong>{unavailable_metric}</strong>", metric_selector)

        wait_selector = rendered[
            rendered.index("<h3>Wait Event Selector</h3>"):
            rendered.index("<h3>SQL Signal Selector</h3>")
        ]
        self.assertIn('data-screen2-domain-scoped="true"', wait_selector)
        self.assertIn('data-empty-message-cpu="No wait-event focus items are directly associated with the active CPU lens. Select COMMIT or RAC to inspect wait-event evidence."', wait_selector)
        self.assertIn('data-dashboard-select-domain="COMMIT"', wait_selector)

        sql_selector = rendered[
            rendered.index("<h3>SQL Signal Selector</h3>"):
            rendered.index("<h3>Report Section Explanation Focus</h3>")
        ]
        self.assertIn('data-screen2-domain-scoped="true"', sql_selector)
        self.assertIn("No SQL signal groups are available for the active {domain} lens.", sql_selector)

    def test_required_safety_wording_is_rendered(self) -> None:
        rendered = self.render_screen2()

        required_phrases = (
            "Evidence focus only",
            "Explanation focus",
            "No truth change",
            "No runtime action",
            "Use Domain to choose the high-level diagnostic lens.",
            "Related selections stay grouped",
            "active domain lens",
            "Deterministic diagnosis, scoring, recommendations",
            "governed service behavior remain unchanged.",
            "recommendations, parser output",
            "runtime behavior",
            "only changes the local explanation context",
            "Generate Focused Explanation",
            "No workflow request, audit record, governance record",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_unsafe_controls_or_write_runtime_are_introduced(self) -> None:
        dashboard = dashboard_module()
        rendered = self.render_screen2().lower()
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
        self.assertIn('data-screen2-generate-explanation="true"', rendered)

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
        selectable_source = source[
            source.index("function selectdashboardelement"):
            source.index("function handledashboardstateinput")
        ]
        self.assertNotIn("dashboardscreen2explanationprovider", selectable_source)
        self.assertIn("screen2activefocuskey", selectable_source)
        self.assertIn("nextstate.selecteddomain = inferreddomain", selectable_source)
        self.assertIn("screen2ensureevidenceparentfordomain(nextstate, inferreddomain)", selectable_source)
        self.assertIn("screen2clearincompatiblefocuscontext(nextstate, inferreddomain, key)", selectable_source)
        self.assertIn("updatescreen2domainscopedselectors(safestate, root)", source)
        self.assertIn("data-screen2-domain-scoped", source)
        self.assertIn("key === 'selecteddiagnosticsection'", selectable_source)
        self.assertNotIn("screen2_focus_item_state_keys.foreach(function (focuskey)", selectable_source)
        self.assertNotIn("nextstate.selecteddomain = ''", selectable_source)

    def test_no_semantic_learning_or_governance_diagnostic_evidence(self) -> None:
        dashboard = dashboard_module()
        screen_2_source = inspect.getsource(dashboard._render_screen_2_page)
        rendered = self.render_screen2()

        forbidden = (
            "semantic recall as diagnostic evidence",
            "semantic candidate context as diagnostic evidence",
            "learning candidates as diagnostic evidence",
            "governance status as diagnostic evidence",
            "selectedLearningCandidate",
            "selectedSemanticItem",
            "selectedGovernanceItem",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, screen_2_source)
                self.assertNotIn(phrase, rendered)

        self.assertIn("focused diagnostic meaning", rendered.lower())
        self.assertNotIn("governed diagnostic review request", rendered.lower())

    def test_no_screen5_recommendation_truth_drift(self) -> None:
        dashboard = dashboard_module()
        screen_5_source = inspect.getsource(dashboard._render_screen_5_page)

        forbidden = (
            "selectedEvidenceGroup",
            "selectedMetricGroup",
            "selectedWaitEventGroup",
            "selectedSqlSignal",
            "Interactive Evidence Focus",
            "diagnostic exploration as recommendation truth",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
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
                self.assertNotIn("Interactive Evidence Focus", text)
                self.assertNotIn("DashboardInteractivityFoundation", text)

    def test_documentation_exists_and_contains_required_boundaries(self) -> None:
        doc_path = DOCS / "phase7_screen2_diagnostic_exploration.md"
        self.assertTrue(doc_path.is_file())
        text = read_text(doc_path).lower()

        required_phrases = (
            "browser-side selectors",
            "non-mutating",
            "do not submit governed review requests",
            "does not change diagnostic truth",
            "does not change primary issue",
            "does not change severity",
            "does not change confidence",
            "does not change recommendation truth",
            "does not change runtime truth",
            "runtime activation",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def render_screen2(self) -> str:
        return dashboard_module()._render_screen_2_page(
            self.sample_screen2_model(),
            ai_sections={},
            decision_state={},
            report_data=self.sample_report_data(),
        )

    @staticmethod
    def sample_screen2_model() -> dict[str, object]:
        return {
            "decision_summary": {
                "overall_status": "WARNING",
                "display_severity_label": "High",
                "decision_posture": "TUNE FIRST",
                "primary_issue": "CPU",
                "confidence": 0.82,
                "health_summary": "CPU pressure visible.",
                "historical_posture": "TUNE FIRST",
            },
            "normalized_decision": {
                "primary_issue": "CPU",
                "secondary_issues": ["COMMIT"],
                "overall_status": "WARNING",
                "display_severity_label": "High",
                "confidence": 0.82,
                "domain_scores": {"CPU": 72.0, "IO": 18.0, "COMMIT": 12.0},
            },
            "health_check": {
                "summary_status": "WARNING",
                "rows": [
                    {"check": "DATA COMPLETENESS", "status": "OK", "observed_value": "Signals present"},
                    {"check": "CPU", "status": "OK", "observed_value": "72"},
                ],
            },
            "visual_summary": {
                "cpu": {
                    "card_title": "CPU",
                    "selected_label": "DB CPU % DB Time",
                    "status": "ok",
                    "series": [40.0, 72.0],
                    "labels": ["snap-1", "snap-2"],
                    "reason": "Visible CPU pressure.",
                },
                "io": {
                    "card_title": "IO",
                    "selected_label": "User I/O % DB Time",
                    "status": "weak",
                    "series": [5.0, 8.0],
                    "labels": ["snap-1", "snap-2"],
                    "reason": "Weak I/O signal.",
                },
            },
            "technical_sections": [
                {"title": "Trend Findings", "items": ["CPU remained visible."]},
                {"title": "Latest Snapshot Assessment", "items": ["Latest interval reviewed."]},
            ],
            "root_cause_interpretation": {},
            "trend_context": {},
            "anomaly_context": {"anomaly_summary": {"count": 1}},
            "explanation_panel": {},
        }

    @staticmethod
    def sample_report_data() -> dict[str, object]:
        return {
            "metadata": {"awr_id": 7001, "db_name": "ORCL", "dbid": "123456"},
            "scores": {"domain_scores": {"CPU": 72.0, "IO": 18.0, "COMMIT": 12.0}},
            "time_series_charts": {
                "snapshot_labels": ["snap-1", "snap-2"],
                "log_file_sync_trend": [1.5, 2.4],
            },
            "wait_events": [
                {"event_name": "DB CPU"},
                {"event_name": "log file sync"},
            ],
            "top_sql": [
                {"sql_id": "abc123", "sql_text": "select * from orders"},
            ],
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
