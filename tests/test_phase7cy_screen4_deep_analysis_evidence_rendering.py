from __future__ import annotations

import importlib
import unittest


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


def base_screen_model(**overrides) -> dict[str, object]:
    payload = {
        "header": {
            "scope_label": "FINDB / 101",
            "db_name": "FINDB",
            "dbid": "101",
            "instance_name": "FIN1",
            "host_name": "dbhost01",
            "snapshot_begin": "2026-06-06T10:00:00Z",
            "snapshot_end": "2026-06-06T11:00:00Z",
        },
        "current_selection_summary": {
            "current_window": "2026-06-06T10:00:00Z to 2026-06-06T11:00:00Z",
            "comparison_mode": "single-window review",
        },
        "historical_verdict": {},
        "historical_summary": {},
        "trend_review": {},
        "anomaly_review": {},
        "comparison_review": {},
        "visual_analysis": {"story": {"section_order": []}},
        "historical_scope_memory": {},
        "topology_platform_review": {},
        "similarity_evidence": {},
        "explanation_panel": {},
    }
    payload.update(overrides)
    return payload


def immutable_truth_refs() -> dict[str, dict[str, object]]:
    return {
        "primary_domain_ref": {"ref": "truth.primary_domain", "read_only": True, "value": "CPU"},
        "score_ref": {"ref": "truth.score", "read_only": True, "value": {"CPU": 72}},
        "severity_ref": {"ref": "truth.severity", "read_only": True, "value": "WARNING"},
        "confidence_ref": {"ref": "truth.confidence", "read_only": True, "value": 0.91},
        "posture_ref": {"ref": "truth.posture", "read_only": True, "value": "investigate"},
        "recommendation_ref": {"ref": "truth.recommendation", "read_only": True, "value": "Tune SQL"},
        "threshold_refs": {"ref": "truth.thresholds", "read_only": True, "value": {"CPU": 70}},
        "diagnostic_driver_refs": {"ref": "truth.diagnostic_drivers", "read_only": True},
    }


def valid_report(**overrides) -> dict[str, object]:
    payload = {
        "metadata": {
            "run_id": "RUN-7CY-F",
            "db_name": "FINDB",
            "dbid": "101",
            "awr_id": "AWR-7CY-F",
            "snapshot_begin": "2026-06-06T10:00:00Z",
            "snapshot_end": "2026-06-06T11:00:00Z",
        },
        "provenance": {
            "source_contract_ref": "screen3.normalized_decision",
            "deterministic_engine_version": "phase7cy-deep-analysis-v1",
        },
        "freshness": {
            "freshness_status": "fresh",
            "generated_at": "2026-06-06T12:00:00Z",
            "source_payload_hash": "hash-7cy-f",
        },
        "current_diagnostic_output_ref": {
            "run_id": "RUN-7CY-F",
            "diagnostic_output_id": "diag-7cy-f",
        },
        "decision": {
            "primary_issue": "CPU",
            "overall_status": "WARNING",
            "severity_score": 72,
            "confidence": 0.91,
            "decision_posture": "investigate",
            "recommendation": "Tune SQL",
        },
        "scores": {"domain_scores": {"CPU": 72, "IO": 18}},
        "thresholds": {"CPU": 70},
        "issues": [
            {
                "issue_type": "cpu_pressure",
                "evidence": {"pct_db_time": 72},
                "severity": "WARNING",
            }
        ],
        "top_sql": [
            {
                "sql_id": "abc123",
                "pct_total": 44.2,
                "elapsed_time_seconds": 330.5,
            }
        ],
    }
    payload.update(overrides)
    return payload


class Screen4DeepAnalysisEvidenceRenderingTests(unittest.TestCase):
    def render_screen4(
        self,
        *,
        screen_model: dict[str, object] | None = None,
        report_data: dict[str, object] | None = None,
        chart_payload: dict[str, object] | None = None,
    ) -> str:
        dashboard = dashboard_module()
        return dashboard._render_screen_4_page(
            screen_model or base_screen_model(),
            chart_payload=chart_payload or {},
            violin_metric_groups=[],
            time_series_groups=[],
            derived_scalar_metrics={},
            report_data=report_data,
        )

    def evidence_fragment(self, html: str) -> str:
        marker = "screen4-deep-analysis-evidence-sections"
        if marker not in html:
            return ""
        start = html.index(marker)
        visual_marker = "screen4-deep-analysis-visual-evidence"
        comparative_marker = "screen4-comparative-review-guard"
        end_marker = visual_marker if visual_marker in html[start:] else comparative_marker
        end = html.index(end_marker, start) if end_marker in html[start:] else len(html)
        return html[start:end]

    def state_fragment(self, html: str) -> str:
        start = html.index("screen4-deep-analysis-guarded-state")
        end_marker = "screen4-deep-analysis-evidence-sections"
        end = html.index(end_marker, start) if end_marker in html[start:] else html.index("screen4-comparative-review-guard", start)
        return html[start:end]

    def test_current_scope_evidence_sections_render_from_ready_contract(self) -> None:
        html = self.render_screen4(report_data=valid_report())
        fragment = self.evidence_fragment(html)

        self.assertIn("Contract-Backed Evidence Sections", fragment)
        self.assertIn("Current Diagnostic Evidence", fragment)
        self.assertIn("Top SQL Detail", fragment)
        self.assertIn("SQL abc123", fragment)
        self.assertIn("44.2", fragment)
        self.assertIn("report_data.top_sql[0]", fragment)
        self.assertIn("screen3.normalized_decision", fragment)
        self.assertIn("fresh", fragment)
        self.assert_no_deep_analysis_visual_markup(fragment)

    def test_generic_scalar_metric_detail_renders_without_fixed_bucket_layout(self) -> None:
        report = valid_report(
            derived_scalar_metrics={
                "parse_cpu_pct": {
                    "deterministic_value": 14.4,
                    "unit": "percent",
                    "display_label": "Parse CPU Percent",
                }
            }
        )

        fragment = self.evidence_fragment(self.render_screen4(report_data=report))

        self.assertIn("Scalar Metric Detail", fragment)
        self.assertIn("Parse CPU Percent", fragment)
        self.assertIn("14.4", fragment)
        self.assertIn("scalar_metric_detail", fragment)

    def test_historical_supporting_context_renders_only_as_supporting(self) -> None:
        report = {
            "metadata": {
                "run_id": "RUN-HIST-F",
                "db_name": "FINDB",
                "dbid": "101",
                "awr_id": "AWR-HIST-F",
            },
            "deep_analysis_generation_context": {
                "generated_at": "2026-06-06T12:00:00Z",
                "freshness": {"freshness_status": "fresh"},
                "provenance": {"source_contract_ref": "historical.time_series"},
                "immutable_truth_refs": immutable_truth_refs(),
            },
            "time_series_charts": {
                "snapshot_labels": ["s1", "s2", "s3"],
                "cpu_trend": [60, 62, 63],
            },
        }

        html = self.render_screen4(report_data=report)
        state = self.state_fragment(html)
        fragment = self.evidence_fragment(html)

        self.assertIn("Deep Analysis: Historical Context Only", state)
        self.assertIn("Historical Supporting Context", fragment)
        self.assertIn("Supporting context only", fragment)
        self.assertIn("sample_count: 3", fragment)
        self.assertNotIn("Current Diagnostic Evidence from the validated deterministic contract.", fragment)

    def test_limitations_and_missing_evidence_render_without_fake_rows(self) -> None:
        report = valid_report(
            top_sql=[],
            llm_explanation={"technical_explanation": "The model says CPU is the cause."},
        )

        fragment = self.evidence_fragment(self.render_screen4(report_data=report))

        self.assertIn("Missing Evidence", fragment)
        self.assertIn("top_sql_missing", fragment)
        self.assertIn("Evidence Limitations", fragment)
        self.assertIn("llm_text_not_evidence", fragment)
        self.assertNotIn("The model says CPU is the cause", fragment)
        self.assertNotIn("SQL abc123", fragment)

    def test_blocked_contract_renders_no_evidence_sections_or_rows(self) -> None:
        report = {
            "decision": {"primary_issue": "CPU", "severity_score": 72},
            "scores": {"domain_scores": {"CPU": 72}},
        }

        html = self.render_screen4(report_data=report)

        self.assertIn("Missing provenance", self.state_fragment(html))
        self.assertEqual("", self.evidence_fragment(html))

    def test_comparative_inputs_do_not_render_in_deep_analysis(self) -> None:
        report = {
            "metadata": {"run_id": "RUN-COMP-F", "db_name": "FINDB", "dbid": "101"},
            "deep_analysis_generation_context": {
                "generated_at": "2026-06-06T12:00:00Z",
                "freshness": {"freshness_status": "fresh"},
                "provenance": {"source_contract_ref": "comparison.output"},
                "immutable_truth_refs": immutable_truth_refs(),
            },
            "comparative_review_state": {"state": "comparison_output_ready"},
            "metric_deltas": [{"metric": "cpu", "delta": -12}],
            "domain_deltas": [{"domain": "CPU"}],
            "evidence_rows": [{"category": "score", "metric": "cpu", "delta": -12}],
            "allowed_visualizations": ["time_series_overlay"],
            "visual_eligibility": [{"status": "eligible"}],
        }

        html = self.render_screen4(report_data=report)
        fragment = self.evidence_fragment(html)

        self.assertEqual("", fragment)
        self.assertIn('data-screen4-comparative-review-state="comparison_unavailable"', html)
        self.assertNotIn("screen4-deep-analysis-evidence-table", fragment)

    def test_prepared_and_cache_only_inputs_do_not_render_deep_analysis_evidence(self) -> None:
        prepared = {
            "metadata": {"run_id": "RUN-PREP-F", "db_name": "FINDB", "dbid": "101"},
            "deep_analysis_generation_context": {
                "freshness": {"freshness_status": "fresh"},
                "provenance": {"source_contract_ref": "screen2.prepared_targets"},
                "immutable_truth_refs": immutable_truth_refs(),
            },
            "comparison_prepared_context": {
                "target_a": {"run_id": "RUN-A"},
                "target_b": {"run_id": "RUN-B"},
            },
        }
        cache_only = {
            "metadata": {"run_id": "RUN-CACHE-F", "db_name": "FINDB", "dbid": "101"},
            "deep_analysis_selected_scope": {"cache_status": "cached_continuity_only"},
            "deep_analysis_generation_context": {
                "freshness": {"freshness_status": "fresh"},
                "provenance": {"source_contract_ref": "browser.cache"},
                "immutable_truth_refs": immutable_truth_refs(),
            },
            "browser_cache_state": {"selected_run_id": "RUN-CACHE-F"},
            "localStorage": {"screen4": "cached"},
        }

        for report in (prepared, cache_only):
            with self.subTest(report=report):
                html = self.render_screen4(report_data=report)
                self.assertEqual("", self.evidence_fragment(html))

    def test_llm_text_does_not_render_as_evidence(self) -> None:
        report = valid_report(
            llm_explanation={
                "technical_explanation": "The LLM claims a definitive cause.",
            }
        )

        fragment = self.evidence_fragment(self.render_screen4(report_data=report))

        self.assertIn("llm_text_not_evidence", fragment)
        self.assertNotIn("The LLM claims a definitive cause", fragment)
        self.assertNotIn("definitive cause", fragment)

    def test_no_empty_panels_or_visual_shells_render(self) -> None:
        html = self.render_screen4(report_data={})

        self.assertEqual(1, html.count("screen4-deep-analysis-guarded-state"))
        self.assertNotIn("screen4-deep-analysis-evidence-sections", html)
        self.assertNotIn("screen4-deep-analysis-evidence-table", html)
        self.assertNotIn("screen4-deep-analysis-visual-evidence", html)

    def test_guarded_state_remains_before_evidence_sections(self) -> None:
        html = self.render_screen4(report_data=valid_report())

        self.assertLess(
            html.index("screen4-deep-analysis-guarded-state"),
            html.index("screen4-deep-analysis-evidence-sections"),
        )

    def assert_no_deep_analysis_visual_markup(self, fragment: str) -> None:
        forbidden = (
            "<canvas",
            "<svg",
            "plotly",
            "chart.js",
            "chart-container",
            "chart-panel",
            "violin-chart",
            "screen4-comparative-visuals",
            "empty-chart",
        )
        lower = fragment.lower()
        for value in forbidden:
            with self.subTest(forbidden=value):
                self.assertNotIn(value, lower)


if __name__ == "__main__":
    unittest.main()
