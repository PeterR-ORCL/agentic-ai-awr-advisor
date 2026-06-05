from __future__ import annotations

import importlib
import unittest


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


def reanalysis_module():
    return importlib.import_module("src.learning.screen3_reanalysis_controller")


def adapter_module():
    return importlib.import_module("src.learning.screen4_comparison_contract")


class Screen4ComparativeTablesTests(unittest.TestCase):
    def valid_contract(self) -> dict[str, object]:
        return {
            "screen4_contract_type": "deterministic_comparison_output",
            "contract_version": "7cx.screen4.comparison.v1",
            "adapter_version": "7cx-adapter-v1",
            "comparison_id": "COMPARISON-7CX-F",
            "baseline_run_id": "RUN-7CX-F-A",
            "candidate_run_id": "RUN-7CX-F-B",
            "target_a_identity": {
                "run_id": "RUN-7CX-F-A",
                "awr_id": "AWR-7CX-F-A",
                "db_name": "FINDB",
                "dbid": "101",
                "window": "baseline window",
                "source_type": "existing_run",
                "scope_type": "run",
                "scope_value": "RUN-7CX-F-A",
            },
            "target_b_identity": {
                "run_id": "RUN-7CX-F-B",
                "awr_id": "AWR-7CX-F-B",
                "db_name": "FINDB",
                "dbid": "101",
                "window": "candidate window",
                "source_type": "existing_run",
                "scope_type": "run",
                "scope_value": "RUN-7CX-F-B",
            },
            "target_alignment": {
                "status": "aligned",
                "basis": [
                    "baseline_run_id matches Target A run_id",
                    "candidate_run_id matches Target B run_id",
                ],
            },
            "source_scope": "same_db_historical",
            "comparison_scope": "target_a_vs_target_b",
            "artifact_source": "phase7cc_comparison_execution",
            "workflow_request_id": "WF-REQ-7CX-F",
            "workflow_transaction_id": "WF-TX-7CX-F",
            "generated_by": "deterministic_engine",
            "generated_at": "2026-06-05T12:00:00Z",
            "deterministic_engine_version": "phase7-am-comparison-v1",
            "metric_deltas": [
                {
                    "metric": "scores.cpu",
                    "category": "score",
                    "baseline_value": 70,
                    "candidate_value": 58,
                    "delta": -12,
                    "unit": "score",
                    "evidence_source": "score_differences",
                }
            ],
            "domain_deltas": [
                {
                    "domain": "CPU",
                    "metric_count": 1,
                    "metrics": ["scores.cpu"],
                    "evidence_source": "metric_deltas",
                    "limitations": ["SQL evidence was not present in this contract."],
                }
            ],
            "evidence_rows": [
                {
                    "category": "score",
                    "metric": "scores.cpu",
                    "baseline_run_id": "RUN-7CX-F-A",
                    "candidate_run_id": "RUN-7CX-F-B",
                    "delta": -12,
                    "evidence_source": "score_differences",
                }
            ],
            "confidence_basis": {
                "basis_type": "deterministic_evidence",
                "sample_count": 2,
                "evidence_row_count": 1,
                "missing_evidence_count": 1,
                "limitations": ["SQL evidence was not present in this contract."],
            },
            "missing_evidence": [
                {
                    "category": "sql",
                    "type": "missing_field",
                    "field": "sqlstats",
                    "reference": "RUN-7CX-F-B",
                    "reason": "candidate SQL evidence was unavailable",
                    "impact": "SQL movement table omitted",
                    "blocked_visualization": "top_sql_movement_table",
                }
            ],
            "allowed_visualizations": [
                "metric_delta_table",
                "domain_delta_summary",
                "confidence_basis_panel",
                "missing_evidence_panel",
            ],
            "validation_status": "valid",
            "adapter_validation_messages": [],
        }

    def render_contract(self, contract: dict[str, object]) -> str:
        dashboard = dashboard_module()
        state = dashboard._screen4_build_comparative_review_state(
            {"deterministic_comparison_output": contract}
        )
        return dashboard._render_screen4_comparative_review_panel(state)

    def test_prepared_only_state_renders_no_comparative_tables(self) -> None:
        dashboard = dashboard_module()
        state = dashboard._screen4_build_comparative_review_state(
            {
                "comparison_prepared_context": {
                    "target_a": {"label": "AWR A", "run_id": "RUN-7CX-F-A"},
                    "target_b": {"label": "AWR B", "run_id": "RUN-7CX-F-B"},
                }
            }
        )

        html = dashboard._render_screen4_comparative_review_panel(state)

        self.assertEqual("comparison_prepared_only", state["state"])
        self.assertNotIn("screen4-comparative-output-tables", html)
        self.assertNotIn("screen4-comparative-metric-delta-table", html)
        self.assertNotIn("screen4-comparative-domain-delta-summary", html)

    def test_cache_only_state_renders_no_comparative_tables(self) -> None:
        dashboard = dashboard_module()
        state = dashboard._screen4_build_comparative_review_state(
            {
                "comparison_cache_status": "cached_continuity_only",
                "comparison_artifact_reference": "comparison:cached-only",
            }
        )

        html = dashboard._render_screen4_comparative_review_panel(state)

        self.assertNotEqual("comparison_output_ready", state["state"])
        self.assertNotIn("screen4-comparative-output-tables", html)
        self.assertNotIn("screen4-comparative-readiness-banner", html)

    def test_valid_contract_renders_readiness_banner_and_identity_cards(self) -> None:
        html = self.render_contract(self.valid_contract())

        self.assertIn("screen4-comparative-output-tables", html)
        self.assertIn("screen4-comparative-readiness-banner", html)
        self.assertIn("COMPARISON-7CX-F", html)
        self.assertIn("deterministic_engine", html)
        self.assertIn("7cx-adapter-v1", html)
        self.assertIn("Target A / Baseline", html)
        self.assertIn("Target B / Candidate", html)
        self.assertIn("RUN-7CX-F-A", html)
        self.assertIn("RUN-7CX-F-B", html)
        self.assertNotIn("<span>Host</span>", html)

    def test_metric_delta_table_requires_permission_and_rows(self) -> None:
        html = self.render_contract(self.valid_contract())
        self.assertIn("screen4-comparative-metric-delta-table", html)
        self.assertIn("Metric Differences", html)
        self.assertIn("scores.cpu", html)
        self.assertIn("Target A Value", html)
        self.assertIn("Target B Value", html)
        metric_start = html.index("screen4-comparative-metric-deltas")
        metric_end = html.index("</section>", metric_start)
        metric_fragment = html[metric_start:metric_end]
        self.assertNotIn("Delta Percent", metric_fragment)
        self.assertNotIn("Notes / Limitations", metric_fragment)

        without_permission = {
            **self.valid_contract(),
            "allowed_visualizations": ["domain_delta_summary", "confidence_basis_panel"],
        }
        html = self.render_contract(without_permission)
        self.assertNotIn("screen4-comparative-metric-delta-table", html)

        empty_rows = {**self.valid_contract(), "metric_deltas": []}
        html = self.render_contract(empty_rows)
        self.assertNotIn("screen4-comparative-metric-delta-table", html)
        self.assertNotIn("<tbody></tbody>", html)

    def test_domain_delta_summary_requires_permission_and_rows(self) -> None:
        html = self.render_contract(self.valid_contract())
        self.assertIn("screen4-comparative-domain-delta-summary", html)
        self.assertIn("Domain Differences", html)
        self.assertIn("CPU", html)

        without_permission = {
            **self.valid_contract(),
            "allowed_visualizations": ["metric_delta_table", "confidence_basis_panel"],
        }
        html = self.render_contract(without_permission)
        self.assertNotIn("screen4-comparative-domain-delta-summary", html)

        empty_rows = {**self.valid_contract(), "domain_deltas": []}
        html = self.render_contract(empty_rows)
        self.assertNotIn("screen4-comparative-domain-delta-summary", html)

    def test_comparative_sections_render_in_operator_review_order(self) -> None:
        html = self.render_contract(self.valid_contract())

        expected_order = (
            "screen4-comparative-readiness-banner",
            "screen4-comparative-target-identity",
            "screen4-comparative-metric-deltas",
            "screen4-comparative-domain-delta-summary",
            "screen4-comparative-evidence-completeness",
            "screen4-comparative-visualization-eligibility",
            "screen4-comparative-confidence-basis",
            "screen4-comparative-missing-evidence",
        )
        indexes = [html.index(marker) for marker in expected_order]
        self.assertEqual(sorted(indexes), indexes)

    def test_confidence_and_missing_evidence_panels_render_only_when_useful(self) -> None:
        html = self.render_contract(self.valid_contract())
        self.assertIn("screen4-comparative-confidence-basis", html)
        self.assertIn("Deterministic Confidence Basis", html)
        self.assertIn("screen4-comparative-missing-evidence", html)
        self.assertIn("SQL movement table omitted", html)

        no_missing = {
            **self.valid_contract(),
            "missing_evidence": [],
            "adapter_validation_messages": [],
            "confidence_basis": {
                "basis_type": "deterministic_evidence",
                "sample_count": 2,
                "evidence_row_count": 1,
                "missing_evidence_count": 0,
                "limitations": [],
            },
        }
        html = self.render_contract(no_missing)
        self.assertIn("screen4-comparative-confidence-basis", html)
        self.assertNotIn("screen4-comparative-missing-evidence", html)

    def test_visualization_eligibility_is_text_only_and_useful(self) -> None:
        contract = {
            **self.valid_contract(),
            "allowed_visualizations": [
                "metric_delta_table",
                "domain_delta_summary",
                "distribution_violin",
            ],
        }
        html = self.render_contract(contract)

        self.assertIn("screen4-comparative-visualization-eligibility", html)
        self.assertIn("Rendering Eligibility", html)
        self.assertIn("Metric Differences", html)
        self.assertIn("Distribution violin requires distribution sample rows.", html)
        eligibility_start = html.index("screen4-comparative-visualization-eligibility")
        eligibility_end = html.index("</section>", eligibility_start)
        eligibility_fragment = html[eligibility_start:eligibility_end]
        self.assertNotIn("metric_delta_table", eligibility_fragment)
        self.assertNotIn("domain_delta_summary", eligibility_fragment)
        self.assertNotIn("<canvas", html)
        self.assertNotIn("<svg", html)
        self.assertNotIn("screen4-comparative-distribution-violin", html)
        self.assertNotIn("screen4-comparative-time-series-overlay", html)

    def test_visualization_eligibility_omits_when_no_useful_rows_exist(self) -> None:
        contract = {
            **self.valid_contract(),
            "allowed_visualizations": [],
            "metric_deltas": [],
            "domain_deltas": [],
        }
        html = self.render_contract(contract)

        self.assertNotIn("screen4-comparative-visualization-eligibility", html)
        self.assertNotIn("screen4-comparative-metric-delta-table", html)
        self.assertNotIn("screen4-comparative-domain-delta-summary", html)

    def test_no_empty_shells_sample_rows_or_ui_created_conclusions(self) -> None:
        html = self.render_contract(self.valid_contract()).lower()

        for forbidden in (
            "hard-coded",
            "sample row",
            "fake delta",
            "placeholder graph",
            "coming soon",
            "<canvas",
            "<svg",
            "empty table",
            "improved",
            "degraded",
            "better",
            "worse",
            "winner",
            "loser",
            "regression",
            "improvement",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, html)

    def test_valid_adapter_output_can_feed_comparative_table_rendering_path(self) -> None:
        reanalysis = reanalysis_module()
        adapter = adapter_module()

        artifact = reanalysis.build_awr_report_comparison(
            [
                {
                    "comparison_input_status": "already_loaded",
                    "run_id": "RUN-7CX-F-A",
                    "awr_id": "AWR-7CX-F-A",
                    "dbid": "101",
                    "database_name": "FINDB",
                    "scores": {"overall": 80, "cpu": 70},
                    "waits": {"db file sequential read": 110},
                    "missing_metrics": [],
                },
                {
                    "comparison_input_status": "comparison_ready",
                    "run_id": "RUN-7CX-F-B",
                    "awr_id": "AWR-7CX-F-B",
                    "dbid": "101",
                    "database_name": "FINDB",
                    "scores": {"overall": 74, "cpu": 58},
                    "waits": {"db file sequential read": 145},
                    "missing_metrics": ["sqlstats"],
                },
            ],
            comparison_name="7CX-F rendering contract",
            baseline_reference="RUN-7CX-F-A",
            created_by="operator",
        )
        result = adapter.adapt_screen4_deterministic_comparison_output(
            artifact,
            prepared_target_context={
                "source_scope": "same_db_historical",
                "comparison_scope": "target_a_vs_target_b",
                "target_a": {
                    "run_id": "RUN-7CX-F-A",
                    "awr_id": "AWR-7CX-F-A",
                    "dbid": "101",
                    "db_name": "FINDB",
                },
                "target_b": {
                    "run_id": "RUN-7CX-F-B",
                    "awr_id": "AWR-7CX-F-B",
                    "dbid": "101",
                    "db_name": "FINDB",
                },
            },
            generated_at="2026-06-05T12:00:00Z",
        )
        self.assertTrue(result.output_ready, result.to_dict())

        html = self.render_contract(result.contract)

        self.assertIn("screen4-comparative-output-tables", html)
        self.assertIn("screen4-comparative-metric-delta-table", html)
        self.assertIn("screen4-comparative-confidence-basis", html)


if __name__ == "__main__":
    unittest.main()
