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


def valid_report(**overrides) -> dict[str, object]:
    payload = {
        "metadata": {
            "run_id": "RUN-7CY-E",
            "db_name": "FINDB",
            "dbid": "101",
            "awr_id": "AWR-7CY-E",
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
            "source_payload_hash": "hash-7cy-e",
        },
        "current_diagnostic_output_ref": {
            "run_id": "RUN-7CY-E",
            "diagnostic_output_id": "diag-7cy-e",
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


def immutable_truth_refs() -> dict[str, dict[str, object]]:
    return {
        "primary_domain_ref": {"ref": "truth.primary_domain", "read_only": True, "value": "CPU"},
        "score_ref": {"ref": "truth.score", "read_only": True, "value": {"CPU": 72}},
        "severity_ref": {"ref": "truth.severity", "read_only": True, "value": "WARNING"},
        "confidence_ref": {"ref": "truth.confidence", "read_only": True, "value": 0.91},
        "posture_ref": {"ref": "truth.posture", "read_only": True, "value": "investigate"},
        "recommendation_ref": {"ref": "truth.recommendation", "read_only": True, "value": "Tune SQL"},
        "threshold_refs": {"ref": "truth.thresholds", "read_only": True, "value": {"CPU": 70}},
    }


class Screen4DeepAnalysisGuardedStateTests(unittest.TestCase):
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

    def deep_fragment(self, html: str) -> str:
        start = html.index("screen4-deep-analysis-guarded-state")
        end = html.index("</section>", start) + len("</section>")
        return html[start:end]

    def test_ready_state_renders_metadata_only(self) -> None:
        html = self.render_screen4(report_data=valid_report())
        fragment = self.deep_fragment(html)

        self.assertIn('data-screen4-deep-analysis-state="deep_analysis_ready"', fragment)
        self.assertIn('data-screen4-deep-analysis-ready="true"', fragment)
        self.assertIn("Deep Analysis: Contract Ready", fragment)
        self.assertIn("Current-Scope Rows", fragment)
        self.assertIn("Provenance", fragment)
        self.assertIn("Freshness", fragment)
        self.assertNotIn("abc123", fragment)
        self.assertNotIn("cpu_pressure", fragment)
        self.assertNotIn("top_sql_detail", fragment)
        self.assert_no_deep_analysis_visual_or_table_markup(fragment)

    def test_missing_contract_metadata_renders_output_required(self) -> None:
        report = {
            "decision": {"primary_issue": "CPU", "severity_score": 72},
            "scores": {"domain_scores": {"CPU": 72}},
        }

        fragment = self.deep_fragment(self.render_screen4(report_data=report))

        self.assertIn('data-screen4-deep-analysis-ready="false"', fragment)
        self.assertIn("Deep Analysis: Evidence Contract Required", fragment)
        self.assertIn(
            "Candidate evidence rows were detected, but Deep Analysis proof is blocked until deterministic provenance and freshness metadata validate.",
            fragment,
        )
        self.assertIn("Missing provenance", fragment)
        self.assertIn("Missing freshness", fragment)
        self.assertNotIn("Deep Analysis: Contract Ready", fragment)
        self.assert_no_deep_analysis_visual_or_table_markup(fragment)

    def test_historical_support_only_is_not_current_scope_ready(self) -> None:
        report = {
            "metadata": {
                "run_id": "RUN-HIST",
                "db_name": "FINDB",
                "dbid": "101",
                "awr_id": "AWR-HIST",
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
            "violin_panel": {"workload": {"cluster_cpu_pct_db_time": [60, 62, 63]}},
        }

        fragment = self.deep_fragment(
            self.render_screen4(
                screen_model=base_screen_model(header={"scope_label": "FINDB / 101"}),
                report_data=report,
            )
        )

        self.assertIn(
            'data-screen4-deep-analysis-state="deep_analysis_historical_supporting_context"',
            fragment,
        )
        self.assertIn("Deep Analysis: Historical Context Only", fragment)
        self.assertIn("Historical Context Only", fragment)
        self.assertNotIn('data-screen4-deep-analysis-ready="true"', fragment)

    def test_comparative_fields_do_not_create_deep_analysis_ready_state(self) -> None:
        report = {
            "metadata": {"run_id": "RUN-COMP", "db_name": "FINDB", "dbid": "101"},
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
        fragment = self.deep_fragment(html)

        self.assertIn('data-screen4-deep-analysis-ready="false"', fragment)
        self.assertIn("comparative_output_blocked", fragment)
        self.assertNotIn("Deep Analysis: Contract Ready", fragment)
        self.assertIn('data-screen4-comparative-review-state="comparison_unavailable"', html)

    def test_prepared_and_cache_only_inputs_do_not_create_ready_state(self) -> None:
        prepared = {
            "metadata": {"run_id": "RUN-PREP", "db_name": "FINDB", "dbid": "101"},
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
            "metadata": {"run_id": "RUN-CACHE", "db_name": "FINDB", "dbid": "101"},
            "deep_analysis_selected_scope": {"cache_status": "cached_continuity_only"},
            "deep_analysis_generation_context": {
                "freshness": {"freshness_status": "fresh"},
                "provenance": {"source_contract_ref": "browser.cache"},
                "immutable_truth_refs": immutable_truth_refs(),
            },
            "browser_cache_state": {"selected_run_id": "RUN-CACHE"},
            "localStorage": {"screen4": "cached"},
        }

        for report in (prepared, cache_only):
            with self.subTest(report=report):
                fragment = self.deep_fragment(self.render_screen4(report_data=report))
                self.assertIn('data-screen4-deep-analysis-ready="false"', fragment)
                self.assertNotIn("Deep Analysis: Contract Ready", fragment)

    def test_llm_text_does_not_create_ready_state(self) -> None:
        report = {
            "metadata": {"run_id": "RUN-LLM", "db_name": "FINDB", "dbid": "101"},
            "deep_analysis_generation_context": {
                "freshness": {"freshness_status": "fresh"},
                "provenance": {"source_contract_ref": "llm.explanation"},
                "immutable_truth_refs": immutable_truth_refs(),
            },
            "llm_explanation": {
                "technical_explanation": "The model says CPU is the cause.",
            },
        }

        fragment = self.deep_fragment(self.render_screen4(report_data=report))

        self.assertIn('data-screen4-deep-analysis-ready="false"', fragment)
        self.assertIn("llm_text_not_evidence", fragment)
        self.assertNotIn("Deep Analysis: Contract Ready", fragment)

    def test_no_empty_deep_analysis_evidence_shells_are_rendered(self) -> None:
        html = self.render_screen4(report_data={})
        fragment = self.deep_fragment(html)

        self.assertEqual(1, html.count("screen4-deep-analysis-guarded-state"))
        self.assertIn("Deep Analysis: Evidence Contract Required", fragment)
        self.assertNotIn("screen4-deep-analysis-evidence", fragment)
        self.assertNotIn("screen4-deep-analysis-table", fragment)
        self.assert_no_deep_analysis_visual_or_table_markup(fragment)

    def assert_no_deep_analysis_visual_or_table_markup(self, fragment: str) -> None:
        forbidden = (
            "<table",
            "<canvas",
            "<svg",
            "chart-container",
            "chart-panel",
            "plotly",
            "violin-chart",
            "screen4-comparative-visuals",
        )
        for value in forbidden:
            with self.subTest(forbidden=value):
                self.assertNotIn(value, fragment.lower())


if __name__ == "__main__":
    unittest.main()
