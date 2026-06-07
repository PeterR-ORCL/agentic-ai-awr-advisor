from __future__ import annotations

import copy
import importlib
import unittest


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


def contract_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_contract")


def selector_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_visual_selection")


def visuals_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_visuals")


def base_screen_model() -> dict[str, object]:
    return {
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
            "run_id": "RUN-7CY-I",
            "db_name": "FINDB",
            "dbid": "101",
            "awr_id": "AWR-7CY-I",
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
            "source_payload_hash": "hash-7cy-i",
        },
        "current_diagnostic_output_ref": {
            "run_id": "RUN-7CY-I",
            "diagnostic_output_id": "diag-7cy-i",
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
        "issues": [{"issue_type": "cpu_pressure", "evidence": {"pct_db_time": 72}}],
        "top_sql": [{"sql_id": "abc123", "pct_total": 44.2, "elapsed_time_seconds": 330.5}],
    }
    payload.update(overrides)
    return payload


def section(**overrides) -> dict[str, object]:
    payload = {
        "section_id": "distribution-current",
        "title": "CPU Samples",
        "scope_classification": "current_scope",
        "evidence_type": "distribution_supporting_context",
        "provenance": {"source_contract_ref": "screen3.normalized_decision"},
        "freshness_status": "fresh",
        "rows_present": True,
        "allowed_rendering": "evidence_table",
    }
    payload.update(overrides)
    return payload


def row(**overrides) -> dict[str, object]:
    payload = {
        "row_id": "dist-samples",
        "section_id": "distribution-current",
        "scope_classification": "current_scope",
        "evidence_type": "distribution_supporting_context",
        "evidence_name": "CPU sample values",
        "deterministic_value": [61.0, 63.0, 65.0, 67.0],
        "source_path": "report_data.samples.cpu",
        "provenance": {"source_contract_ref": "screen3.normalized_decision"},
        "freshness_status": "fresh",
        "supports_existing_truth_ref": {"ref": "truth.primary_domain"},
        "render_as": "table_row",
    }
    payload.update(overrides)
    return payload


def valid_contract(**overrides) -> dict[str, object]:
    payload = {
        "contract_type": "screen4_deep_analysis_contract",
        "contract_version": "1.0",
        "generated_by": "deterministic_backend",
        "generated_at": "2026-06-07T12:00:00Z",
        "deterministic_engine_version": "phase7cy-deep-analysis-v1",
        "source_scope": "current_selected_diagnostic_scope",
        "selected_run_id": "RUN-7CY-I",
        "selected_source_identifier": {"source_artifact_id": "artifact-7cy-i"},
        "selected_snapshot_identifier": {"awr_id": "AWR-7CY-I"},
        "generation_context": {"dashboard_generation_id": "dashboard-7cy-i"},
        "freshness": {"freshness_status": "fresh", "source_payload_hash": "hash-7cy-i"},
        "provenance": {"source_contract_ref": "screen3.normalized_decision"},
        "current_diagnostic_output_ref": {"run_id": "RUN-7CY-I", "diagnostic_output_id": "diag-7cy-i"},
        "immutable_truth_refs": immutable_truth_refs(),
        "evidence_sections": [section()],
        "evidence_rows": [row()],
        "chart_eligibility": [],
        "limitations": [],
        "missing_evidence": [],
        "validation_messages": [],
        "llm_explanation_boundary": {"llm_can_create_evidence": False},
        "mutation_boundaries": {flag: False for flag in contract_module().MUTATION_BOUNDARY_FLAGS},
    }
    payload.update(overrides)
    return copy.deepcopy(payload)


class Screen4DeepAnalysisProductPolishTests(unittest.TestCase):
    def render_screen4(self, report_data: dict[str, object] | None = None) -> str:
        return dashboard_module()._render_screen_4_page(
            base_screen_model(),
            chart_payload={},
            violin_metric_groups=[],
            time_series_groups=[],
            derived_scalar_metrics={},
            report_data=report_data,
        )

    def render_contract_visuals(self, contract: dict[str, object]) -> str:
        validation = contract_module().validate_deep_analysis_contract(contract)
        selection = selector_module().select_deep_analysis_visualizations(contract, validation)
        return visuals_module().render_deep_analysis_visualizations(contract, selection)

    def test_lane_order_keeps_deep_analysis_separate_from_comparative_review(self) -> None:
        html = self.render_screen4(valid_report())

        self.assertLess(html.index("screen4-deep-analysis-guarded-state"), html.index("screen4-deep-analysis-evidence-sections"))
        self.assertLess(html.index("screen4-deep-analysis-evidence-sections"), html.index("screen4-deep-analysis-visual-evidence"))
        self.assertLess(html.index("screen4-deep-analysis-visual-evidence"), html.index("screen4-comparative-review-guard"))
        self.assertIn("Comparative Review Guarded State", html)

    def test_operator_mode_labels_are_plain_and_scope_specific(self) -> None:
        html = self.render_screen4(valid_report())

        required = (
            "Evidence Readiness",
            "Evidence Review / Historical Supporting Context",
            "Historical supporting context lane",
            "Current selected diagnostic evidence lane",
            "Current Diagnostic Evidence",
            "Historical Supporting Context",
            "Contract-Backed Evidence",
            "Contract-Backed Visual Evidence",
            "Deep Analysis uses its current-scope evidence contract",
            "Comparative Review uses its own deterministic comparison output contract",
            "No Target A/B context prepared",
            "Every visual is selected by active evidence mode, validated data, validated evidence shape",
            "provenance, freshness, sample identity, sample count, scope classification, and rendering eligibility",
            "Screen 4 visual north star: mode first, validated data second, evidence shape third",
            "Universal Visual Rule",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, html)

    def test_distribution_wording_is_conservative_and_not_true_violin(self) -> None:
        html = self.render_contract_visuals(valid_contract())

        self.assertIn("Distribution Evidence", html)
        self.assertIn("no density curve is estimated", html)
        self.assertNotIn("violin", html.lower())

    def test_visual_wording_stays_dynamic_not_tiny_fixed_bucket(self) -> None:
        topology_contract = valid_contract(
            evidence_sections=[
                section(
                    section_id="topology-detail",
                    title="RAC / ADG Topology",
                    evidence_type="rac_adg_topology_detail",
                )
            ],
            evidence_rows=[
                row(
                    row_id="topology-node-1",
                    section_id="topology-detail",
                    evidence_type="rac_adg_topology_detail",
                    evidence_name="RAC node role",
                    deterministic_value={"instance": "FIN1", "role": "primary"},
                    source_path="report_data.topology.nodes[0]",
                )
            ],
        )

        html = self.render_contract_visuals(topology_contract)

        self.assertIn("Topology Fact Map", html)
        self.assertIn("RAC / ADG Topology", html)
        self.assertNotIn("only DB time", html)
        self.assertNotIn("only waits", html)
        self.assertNotIn("only Top SQL", html)

    def test_no_unsupported_causal_or_diagnostic_wording_is_introduced(self) -> None:
        html = self.render_screen4(valid_report()).lower()

        for phrase in ("root cause", "proven cause", "definitive cause", "new diagnosis"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, html)

    def test_no_empty_deep_analysis_evidence_or_visual_shells_render(self) -> None:
        html = self.render_screen4({})

        self.assertIn("screen4-deep-analysis-guarded-state", html)
        self.assertNotIn("screen4-deep-analysis-evidence-sections", html)
        self.assertNotIn("screen4-deep-analysis-visual-evidence", html)
        self.assertNotIn("screen4-deep-analysis-static-visual", html)

    def test_cache_prepared_llm_and_comparative_boundaries_remain_visible(self) -> None:
        html = self.render_screen4(valid_report())

        required = (
            "Browser cache does not create evidence.",
            "Prepared Target A/B state does not create comparison output.",
            "cache, prepared Target A/B, comparative output, and LLM text do not create Deep Analysis evidence.",
            "No prepared comparison context is available for this Screen 4 export",
            "Screen 4 does not compute comparison or comparative graphics in the browser.",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, html)


if __name__ == "__main__":
    unittest.main()
