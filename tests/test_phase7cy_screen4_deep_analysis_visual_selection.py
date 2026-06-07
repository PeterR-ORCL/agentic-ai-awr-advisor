from __future__ import annotations

import copy
import importlib
import inspect
import unittest


def selector_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_visual_selection")


def contract_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_contract")


def mutation_boundaries() -> dict[str, bool]:
    module = contract_module()
    return {flag: False for flag in module.MUTATION_BOUNDARY_FLAGS}


def immutable_truth_refs() -> dict[str, dict[str, object]]:
    return {
        "primary_domain_ref": {"ref": "truth.primary_domain", "read_only": True},
        "score_ref": {"ref": "truth.score", "read_only": True},
        "severity_ref": {"ref": "truth.severity", "read_only": True},
        "confidence_ref": {"ref": "truth.confidence", "read_only": True},
        "posture_ref": {"ref": "truth.posture", "read_only": True},
        "recommendation_ref": {"ref": "truth.recommendation", "read_only": True},
        "threshold_refs": {"ref": "truth.thresholds", "read_only": True},
        "diagnostic_driver_refs": {"ref": "truth.diagnostic_drivers", "read_only": True},
    }


def section(**overrides) -> dict[str, object]:
    payload = {
        "section_id": "current-drivers",
        "title": "Current Diagnostic Evidence",
        "scope_classification": "current_scope",
        "evidence_type": "diagnostic_driver",
        "provenance": {"source_contract_ref": "screen3.normalized_decision"},
        "freshness_status": "fresh",
        "rows_present": True,
        "allowed_rendering": "evidence_table",
    }
    payload.update(overrides)
    return payload


def row(**overrides) -> dict[str, object]:
    payload = {
        "row_id": "row-current-cpu",
        "section_id": "current-drivers",
        "scope_classification": "current_scope",
        "evidence_type": "diagnostic_driver",
        "metric_name": "CPU score",
        "deterministic_value": 72,
        "source_path": "report_data.decision.cpu",
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
        "selected_run_id": "RUN-7CY-G",
        "selected_source_identifier": {"source_artifact_id": "artifact-7cy-g"},
        "selected_snapshot_identifier": {"awr_id": "AWR-7CY-G"},
        "generation_context": {"dashboard_generation_id": "dashboard-7cy-g"},
        "freshness": {"freshness_status": "fresh", "source_payload_hash": "hash-7cy-g"},
        "provenance": {"source_contract_ref": "screen3.normalized_decision"},
        "current_diagnostic_output_ref": {"run_id": "RUN-7CY-G", "diagnostic_output_id": "diag-7cy-g"},
        "immutable_truth_refs": immutable_truth_refs(),
        "evidence_sections": [section()],
        "evidence_rows": [row()],
        "chart_eligibility": [],
        "limitations": [],
        "missing_evidence": [],
        "validation_messages": [],
        "llm_explanation_boundary": {"llm_can_create_evidence": False},
        "mutation_boundaries": mutation_boundaries(),
    }
    payload.update(overrides)
    return copy.deepcopy(payload)


class Screen4DeepAnalysisVisualSelectionTests(unittest.TestCase):
    def select(self, contract):
        validation = (
            contract_module().validate_deep_analysis_contract(contract)
            if isinstance(contract, dict)
            else None
        )
        return selector_module().select_deep_analysis_visualizations(
            contract,
            validation,
        )

    def test_missing_or_invalid_contract_produces_no_eligible_candidates(self) -> None:
        for payload in (None, "contract", {}):
            with self.subTest(payload=payload):
                result = selector_module().select_deep_analysis_visualizations(payload)
                self.assertFalse(result.has_eligible_visuals)
                self.assertFalse(result.candidates)
                self.assertIn("contract_missing_or_invalid", result.messages)

    def test_current_scope_categorical_contribution_is_eligible(self) -> None:
        result = self.select(valid_contract())
        module = selector_module()

        self.assertTrue(result.has_eligible_visuals)
        candidate = result.eligible_candidates[0]
        self.assertEqual(module.VisualizationStatus.ELIGIBLE, candidate.status)
        self.assertEqual(module.VisualizationFamily.CONTRIBUTION, candidate.visualization_family)
        self.assertEqual(module.EvidenceShape.CATEGORICAL_CONTRIBUTION, candidate.evidence_shape)
        self.assertFalse(candidate.is_supporting_context)
        self.assertIn("future_deep_analysis_contribution_renderer", candidate.recommended_renderer)

    def test_generic_non_fixed_bucket_evidence_can_select_visual_family(self) -> None:
        topology_section = section(
            section_id="topology-detail",
            title="RAC / ADG Topology",
            evidence_type="rac_adg_topology_detail",
        )
        topology_row = row(
            row_id="topology-node-1",
            section_id="topology-detail",
            evidence_type="rac_adg_topology_detail",
            evidence_name="RAC node role",
            deterministic_value={"instance": "FIN1", "role": "primary"},
            source_path="report_data.topology.nodes[0]",
        )

        result = self.select(valid_contract(evidence_sections=[topology_section], evidence_rows=[topology_row]))
        candidate = result.eligible_candidates[0]

        self.assertEqual(selector_module().VisualizationFamily.TOPOLOGY_FACT_MAP, candidate.visualization_family)
        self.assertEqual(selector_module().EvidenceShape.TOPOLOGY_FACTS, candidate.evidence_shape)
        self.assertIn("RAC / ADG Topology", candidate.suggested_title)

    def test_time_indexed_rows_require_at_least_two_points(self) -> None:
        ts_section = section(
            section_id="time-series-current",
            title="CPU Time Series",
            evidence_type="metric_breakdown",
        )
        rows = [
            row(row_id="ts-1", section_id="time-series-current", timestamp="2026-06-07T10:00:00Z", deterministic_value=72),
            row(row_id="ts-2", section_id="time-series-current", timestamp="2026-06-07T10:05:00Z", deterministic_value=74),
        ]

        ready = self.select(valid_contract(evidence_sections=[ts_section], evidence_rows=rows))
        self.assertEqual(selector_module().VisualizationFamily.TIME_SERIES, ready.eligible_candidates[0].visualization_family)

        one_point = self.select(valid_contract(evidence_sections=[ts_section], evidence_rows=rows[:1]))
        self.assertFalse(one_point.has_eligible_visuals)
        self.assertEqual("time_series_points_below_minimum", one_point.blocked_candidates[0].blocked_reason)

    def test_distribution_evidence_requires_real_samples_and_avoids_true_violin_claims(self) -> None:
        dist_section = section(
            section_id="distribution-current",
            title="CPU Samples",
            evidence_type="distribution_supporting_context",
        )
        samples_row = row(
            row_id="dist-samples",
            section_id="distribution-current",
            evidence_type="distribution_supporting_context",
            deterministic_value=[61.0, 63.0, 65.0, 67.0],
        )

        result = self.select(valid_contract(evidence_sections=[dist_section], evidence_rows=[samples_row]))
        candidate = result.eligible_candidates[0]

        self.assertEqual(selector_module().VisualizationFamily.DISTRIBUTION_EVIDENCE, candidate.visualization_family)
        self.assertIn("Distribution Evidence", candidate.suggested_title)
        self.assertIn("do not claim true violin", candidate.label_guidance)

        one_sample = self.select(
            valid_contract(evidence_sections=[dist_section], evidence_rows=[{**samples_row, "deterministic_value": [61.0]}])
        )
        self.assertFalse(one_sample.has_eligible_visuals)
        self.assertEqual("numeric_samples_below_minimum", one_sample.blocked_candidates[0].blocked_reason)

        summary_only = self.select(
            valid_contract(
                evidence_sections=[dist_section],
                evidence_rows=[{**samples_row, "deterministic_value": {"min": 61.0, "max": 67.0, "sample_count": 4}}],
            )
        )
        self.assertFalse(summary_only.has_eligible_visuals)
        self.assertEqual("numeric_samples_below_minimum", summary_only.blocked_candidates[0].blocked_reason)

    def test_historical_supporting_visuals_are_marked_supporting_only(self) -> None:
        hist_section = section(
            section_id="historical-series",
            title="Historical CPU Trend",
            scope_classification="historical_supporting_context",
            evidence_type="time_series_supporting_context",
        )
        hist_rows = [
            row(row_id="hist-1", section_id="historical-series", scope_classification="historical_supporting_context", evidence_type="time_series_supporting_context", timestamp="s1", deterministic_value=61, supports_existing_truth_ref={}),
            row(row_id="hist-2", section_id="historical-series", scope_classification="historical_supporting_context", evidence_type="time_series_supporting_context", timestamp="s2", deterministic_value=64, supports_existing_truth_ref={}),
        ]

        result = self.select(valid_contract(evidence_sections=[hist_section], evidence_rows=hist_rows))

        self.assertFalse(contract_module().validate_deep_analysis_contract(valid_contract(evidence_sections=[hist_section], evidence_rows=hist_rows)).is_ready)
        candidate = result.eligible_candidates[0]
        self.assertTrue(candidate.is_supporting_context)
        self.assertEqual("historical_supporting_context", candidate.scope_classification)
        self.assertIn("supporting context", candidate.label_guidance.lower())

    def test_comparative_fields_and_rows_are_blocked_for_deep_analysis(self) -> None:
        comp_section = section(
            section_id="comparison-output",
            scope_classification="comparative_output",
            evidence_type="metric_delta",
        )
        comp_row = row(
            row_id="comparison-delta",
            section_id="comparison-output",
            scope_classification="comparative_output",
            evidence_type="metric_delta",
            deterministic_value=-12,
            supports_existing_truth_ref={},
        )
        result = self.select(
            valid_contract(
                evidence_sections=[comp_section],
                evidence_rows=[comp_row],
                allowed_visualizations=["time_series_overlay"],
                visual_eligibility=[{"status": "eligible"}],
            )
        )

        self.assertFalse(result.has_eligible_visuals)
        self.assertTrue(result.blocked_candidates)
        self.assertIn("comparative_output", result.blocked_candidates[0].blocked_reason)

        chart_only = self.select(valid_contract(evidence_sections=[], evidence_rows=[], chart_eligibility=[{"eligibility_status": "eligible", "chart_type": "time_series"}]))
        self.assertFalse(chart_only.has_eligible_visuals)

    def test_prepared_cache_llm_and_unknown_rows_are_blocked(self) -> None:
        for scope in ("prepared_only", "cache_only", "llm_explanation_only", "unknown_or_mixed"):
            with self.subTest(scope=scope):
                blocked_section = section(section_id=f"{scope}-section", scope_classification=scope)
                blocked_row = row(
                    row_id=f"{scope}-row",
                    section_id=f"{scope}-section",
                    scope_classification=scope,
                    supports_existing_truth_ref={},
                )
                result = self.select(valid_contract(evidence_sections=[blocked_section], evidence_rows=[blocked_row]))
                self.assertFalse(result.has_eligible_visuals)
                self.assertTrue(result.blocked_candidates)
                self.assertIn(scope, result.blocked_candidates[0].blocked_reason)

    def test_fleet_population_rows_are_not_supported_until_fleet_contract_exists(self) -> None:
        fleet_section = section(section_id="fleet-section", scope_classification="fleet_population")
        fleet_row = row(
            row_id="fleet-row",
            section_id="fleet-section",
            scope_classification="fleet_population",
            deterministic_value=[1, 2, 3, 4],
            supports_existing_truth_ref={},
        )

        result = self.select(valid_contract(evidence_sections=[fleet_section], evidence_rows=[fleet_row]))

        self.assertFalse(result.has_eligible_visuals)
        candidate = result.blocked_candidates[0]
        self.assertEqual(selector_module().VisualizationStatus.NOT_SUPPORTED, candidate.status)
        self.assertEqual(selector_module().VisualizationFamily.FLEET_POPULATION, candidate.visualization_family)

    def test_chart_eligibility_signal_cannot_create_evidence_or_bypass_flags(self) -> None:
        safe = self.select(
            valid_contract(
                evidence_sections=[],
                evidence_rows=[],
                chart_eligibility=[{"eligibility_status": "eligible", "chart_type": "time_series"}],
            )
        )
        self.assertFalse(safe.has_eligible_visuals)

        for flag in ("browser_computation_allowed", "synthetic_data_allowed", "empty_chart_allowed"):
            with self.subTest(flag=flag):
                unsafe = self.select(
                    valid_contract(
                        evidence_sections=[],
                        evidence_rows=[],
                        chart_eligibility=[{"eligibility_status": "eligible", "chart_type": "time_series", flag: True}],
                    )
                )
                self.assertFalse(unsafe.has_eligible_visuals)
                self.assertIn(flag, unsafe.blocked_candidates[0].blocked_reason)

    def test_table_only_fallback_does_not_create_fake_chart(self) -> None:
        detail_section = section(
            section_id="engineering-detail",
            title="Engineering Detail",
            evidence_type="engineering_detail",
        )
        detail_row = row(
            row_id="engineering-row",
            section_id="engineering-detail",
            evidence_type="engineering_detail",
            evidence_name="Trace file reference",
            deterministic_value="trace-42.trc",
            source_path="report_data.engineering.trace",
        )

        result = self.select(valid_contract(evidence_sections=[detail_section], evidence_rows=[detail_row]))

        self.assertFalse(result.has_eligible_visuals)
        self.assertIn("engineering-detail", result.table_only_sections)
        candidate = result.omitted_candidates[0]
        self.assertEqual(selector_module().VisualizationFamily.TABLE_ONLY, candidate.visualization_family)
        self.assertIn("do not create a chart shell", candidate.label_guidance)

    def test_module_has_no_rendering_or_dashboard_import_side_effects(self) -> None:
        module = selector_module()
        source = inspect.getsource(module)

        self.assertTrue(hasattr(module, "select_deep_analysis_visualizations"))
        for forbidden in ("html_dashboard", "<svg", "Chart.js", "Plotly", "render_html"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
