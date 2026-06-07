from __future__ import annotations

import copy
import importlib
import inspect
import unittest


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


def selector_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_visual_selection")


def contract_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_contract")


def visuals_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_visuals")


def mutation_boundaries() -> dict[str, bool]:
    module = contract_module()
    return {flag: False for flag in module.MUTATION_BOUNDARY_FLAGS}


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
        "selected_run_id": "RUN-7CY-H",
        "selected_source_identifier": {"source_artifact_id": "artifact-7cy-h"},
        "selected_snapshot_identifier": {"awr_id": "AWR-7CY-H"},
        "generation_context": {"dashboard_generation_id": "dashboard-7cy-h"},
        "freshness": {"freshness_status": "fresh", "source_payload_hash": "hash-7cy-h"},
        "provenance": {"source_contract_ref": "screen3.normalized_decision"},
        "current_diagnostic_output_ref": {"run_id": "RUN-7CY-H", "diagnostic_output_id": "diag-7cy-h"},
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
            "run_id": "RUN-7CY-H",
            "db_name": "FINDB",
            "dbid": "101",
            "awr_id": "AWR-7CY-H",
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
            "source_payload_hash": "hash-7cy-h",
        },
        "current_diagnostic_output_ref": {
            "run_id": "RUN-7CY-H",
            "diagnostic_output_id": "diag-7cy-h",
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


class Screen4DeepAnalysisVisualRenderingTests(unittest.TestCase):
    def select(self, contract: dict[str, object]):
        validation = contract_module().validate_deep_analysis_contract(contract)
        return selector_module().select_deep_analysis_visualizations(contract, validation)

    def render_contract(self, contract: dict[str, object]) -> str:
        return visuals_module().render_deep_analysis_visualizations(contract, self.select(contract))

    def render_screen4(self, report_data: dict[str, object] | None = None) -> str:
        return dashboard_module()._render_screen_4_page(
            base_screen_model(),
            chart_payload={},
            violin_metric_groups=[],
            time_series_groups=[],
            derived_scalar_metrics={},
            report_data=report_data,
        )

    def test_no_visual_section_renders_without_eligible_candidates(self) -> None:
        detail_section = section(section_id="engineering-detail", title="Engineering Detail", evidence_type="engineering_detail")
        detail_row = row(
            row_id="engineering-row",
            section_id="engineering-detail",
            evidence_type="engineering_detail",
            evidence_name="Trace file",
            deterministic_value="trace-42.trc",
            source_path="report_data.engineering.trace",
        )

        html = self.render_contract(valid_contract(evidence_sections=[detail_section], evidence_rows=[detail_row]))

        self.assertEqual("", html)

    def test_current_scope_contribution_visual_renders_static_markup(self) -> None:
        html = self.render_contract(valid_contract())

        self.assertIn("Contract-Backed Visual Evidence", html)
        self.assertIn('data-screen4-deep-analysis-static-visual="contribution-bars"', html)
        self.assertIn("Current Diagnostic Evidence", html)
        self.assertIn("CPU score", html)
        self.assertIn("72", html)
        self.assert_no_browser_chart_runtime(html)

    def test_generic_topology_visual_renders_without_fixed_bucket_dependency(self) -> None:
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

        html = self.render_contract(valid_contract(evidence_sections=[topology_section], evidence_rows=[topology_row]))

        self.assertIn('data-screen4-deep-analysis-static-visual="topology-fact-map"', html)
        self.assertIn("RAC / ADG Topology", html)
        self.assertIn("Topology Fact Map", html)
        self.assertIn("FIN1", html)

    def test_time_series_visual_requires_multiple_validated_points(self) -> None:
        ts_section = section(
            section_id="time-series-current",
            title="CPU Time Series",
            evidence_type="metric_breakdown",
        )
        rows = [
            row(row_id="ts-1", section_id="time-series-current", timestamp="2026-06-07T10:00:00Z", deterministic_value=72),
            row(row_id="ts-2", section_id="time-series-current", timestamp="2026-06-07T10:05:00Z", deterministic_value=74),
        ]

        html = self.render_contract(valid_contract(evidence_sections=[ts_section], evidence_rows=rows))

        self.assertIn('data-screen4-deep-analysis-static-visual="time-series"', html)
        self.assertIn("<svg", html)
        self.assertIn("<title", html)
        self.assertIn("<desc", html)
        self.assertIn("Static trend from 2 validated time-indexed evidence points.", html)

        one_point = self.render_contract(valid_contract(evidence_sections=[ts_section], evidence_rows=rows[:1]))
        self.assertEqual("", one_point)

    def test_distribution_evidence_visual_uses_conservative_non_violin_wording(self) -> None:
        dist_section = section(
            section_id="distribution-current",
            title="CPU Samples",
            evidence_type="distribution_supporting_context",
        )
        samples_row = row(
            row_id="dist-samples",
            section_id="distribution-current",
            evidence_type="distribution_supporting_context",
            metric_name="CPU sample values",
            deterministic_value=[61.0, 63.0, 65.0, 67.0],
            source_path="report_data.samples.cpu",
            unit="% DB Time",
        )

        html = self.render_contract(valid_contract(evidence_sections=[dist_section], evidence_rows=[samples_row]))

        self.assertIn('data-screen4-deep-analysis-static-visual="distribution-evidence"', html)
        self.assertIn("Distribution Evidence", html)
        self.assertIn("no density curve is estimated", html)
        self.assertIn("sample count 4", html)
        self.assertIn("CPU sample values", html)
        self.assertIn("% DB Time", html)
        self.assertIn("scale 61 to 67", html)
        self.assertIn("report_data.samples.cpu", html)
        self.assertIn("screen3.normalized_decision", html)
        self.assertNotIn("violin", html.lower())

        for bad_value in ([61.0], {"min": 61.0, "max": 67.0, "sample_count": 4}):
            with self.subTest(bad_value=bad_value):
                bad_row = {**samples_row, "deterministic_value": bad_value}
                rendered = self.render_contract(valid_contract(evidence_sections=[dist_section], evidence_rows=[bad_row]))
                self.assertEqual("", rendered)

        synthetic_row = {**samples_row, "synthetic": True}
        rendered = self.render_contract(valid_contract(evidence_sections=[dist_section], evidence_rows=[synthetic_row]))
        self.assertEqual("", rendered)

    def test_duplicate_distribution_candidates_do_not_render_independent_visuals(self) -> None:
        dist_section = section(
            section_id="distribution-current",
            title="CPU Samples",
            evidence_type="distribution_supporting_context",
        )
        samples_row = row(
            row_id="dist-samples",
            section_id="distribution-current",
            evidence_type="distribution_supporting_context",
            metric_name="CPU sample values",
            deterministic_value=[61.0, 63.0, 65.0, 67.0],
            source_path="report_data.samples.cpu",
            unit="% DB Time",
        )
        candidate = {
            "status": "eligible",
            "visualization_family": "distribution_evidence",
            "suggested_title": "CPU Distribution Evidence",
            "scope_classification": "current_scope",
            "evidence_shape": "numeric_samples",
            "section_id": "distribution-current",
            "row_ids": ["dist-samples"],
            "provenance_summary": "screen3.normalized_decision",
            "freshness_summary": "fresh",
            "is_supporting_context": False,
        }
        contract = valid_contract(evidence_sections=[dist_section], evidence_rows=[samples_row])
        html = visuals_module().render_deep_analysis_visualizations(
            contract,
            {
                "eligible_candidates": [
                    {**candidate, "candidate_id": "dist-a"},
                    {**candidate, "candidate_id": "dist-b"},
                ]
            },
        )

        self.assertEqual(1, html.count('data-screen4-deep-analysis-static-visual="distribution-evidence"'))

        duplicate_sections = [
            dist_section,
            section(
                section_id="distribution-reused",
                title="Reused Samples",
                evidence_type="distribution_supporting_context",
            ),
        ]
        duplicate_rows = [
            samples_row,
            row(
                row_id="dist-samples-reused",
                section_id="distribution-reused",
                evidence_type="distribution_supporting_context",
                metric_name="Reused sample values",
                deterministic_value=[61.0, 63.0, 65.0, 67.0],
                source_path="report_data.samples.reused_cpu",
                unit="% DB Time",
            ),
        ]
        duplicate_contract = valid_contract(
            evidence_sections=duplicate_sections,
            evidence_rows=duplicate_rows,
        )
        duplicate_html = visuals_module().render_deep_analysis_visualizations(
            duplicate_contract,
            {
                "eligible_candidates": [
                    {**candidate, "candidate_id": "dist-a"},
                    {
                        **candidate,
                        "candidate_id": "dist-reused",
                        "section_id": "distribution-reused",
                        "row_ids": ["dist-samples-reused"],
                    },
                ]
            },
        )

        self.assertEqual(
            1,
            duplicate_html.count('data-screen4-deep-analysis-static-visual="distribution-evidence"'),
        )

    def test_distinct_distribution_sample_sets_may_render_separately(self) -> None:
        sections = [
            section(
                section_id="distribution-cpu",
                title="CPU Samples",
                evidence_type="distribution_supporting_context",
            ),
            section(
                section_id="distribution-io",
                title="I/O Samples",
                evidence_type="distribution_supporting_context",
            ),
        ]
        rows = [
            row(
                row_id="dist-cpu",
                section_id="distribution-cpu",
                evidence_type="distribution_supporting_context",
                metric_name="CPU sample values",
                deterministic_value=[61.0, 63.0, 65.0, 67.0],
                source_path="report_data.samples.cpu",
                unit="% DB Time",
            ),
            row(
                row_id="dist-io",
                section_id="distribution-io",
                evidence_type="distribution_supporting_context",
                metric_name="I/O sample values",
                deterministic_value=[11.0, 17.0, 23.0, 29.0],
                source_path="report_data.samples.io",
                unit="% DB Time",
            ),
        ]
        contract = valid_contract(evidence_sections=sections, evidence_rows=rows)
        selection = {
            "eligible_candidates": [
                {
                    "candidate_id": "dist-cpu",
                    "status": "eligible",
                    "visualization_family": "distribution_evidence",
                    "suggested_title": "CPU Distribution Evidence",
                    "scope_classification": "current_scope",
                    "evidence_shape": "numeric_samples",
                    "section_id": "distribution-cpu",
                    "row_ids": ["dist-cpu"],
                    "provenance_summary": "screen3.normalized_decision",
                    "freshness_summary": "fresh",
                    "is_supporting_context": False,
                },
                {
                    "candidate_id": "dist-io",
                    "status": "eligible",
                    "visualization_family": "distribution_evidence",
                    "suggested_title": "I/O Distribution Evidence",
                    "scope_classification": "current_scope",
                    "evidence_shape": "numeric_samples",
                    "section_id": "distribution-io",
                    "row_ids": ["dist-io"],
                    "provenance_summary": "screen3.normalized_decision",
                    "freshness_summary": "fresh",
                    "is_supporting_context": False,
                },
            ]
        }

        html = visuals_module().render_deep_analysis_visualizations(contract, selection)

        self.assertEqual(2, html.count('data-screen4-deep-analysis-static-visual="distribution-evidence"'))
        self.assertIn("CPU sample values", html)
        self.assertIn("I/O sample values", html)
        self.assertIn("report_data.samples.cpu", html)
        self.assertIn("report_data.samples.io", html)

    def test_historical_supporting_visual_is_labeled_supporting_only(self) -> None:
        hist_section = section(
            section_id="historical-series",
            title="Historical CPU Trend",
            scope_classification="historical_supporting_context",
            evidence_type="time_series_supporting_context",
        )
        rows = [
            row(
                row_id="hist-1",
                section_id="historical-series",
                scope_classification="historical_supporting_context",
                evidence_type="time_series_supporting_context",
                timestamp="s1",
                deterministic_value=61,
                supports_existing_truth_ref={},
            ),
            row(
                row_id="hist-2",
                section_id="historical-series",
                scope_classification="historical_supporting_context",
                evidence_type="time_series_supporting_context",
                timestamp="s2",
                deterministic_value=64,
                supports_existing_truth_ref={},
            ),
        ]

        html = self.render_contract(valid_contract(evidence_sections=[hist_section], evidence_rows=rows))

        self.assertIn("Historical Supporting Context", html)
        self.assertIn("Supporting visual; does not override selected-scope diagnostic truth.", html)
        self.assertNotIn("current proof", html.lower())

    def test_blocked_omitted_not_supported_and_leakage_candidates_do_not_render(self) -> None:
        for scope in (
            "comparative_output",
            "prepared_only",
            "cache_only",
            "llm_explanation_only",
            "unknown_or_mixed",
            "fleet_population",
        ):
            with self.subTest(scope=scope):
                blocked_section = section(section_id=f"{scope}-section", scope_classification=scope)
                blocked_row = row(
                    row_id=f"{scope}-row",
                    section_id=f"{scope}-section",
                    scope_classification=scope,
                    deterministic_value=[1, 2, 3, 4],
                    supports_existing_truth_ref={},
                )
                rendered = self.render_contract(valid_contract(evidence_sections=[blocked_section], evidence_rows=[blocked_row]))
                self.assertEqual("", rendered)

    def test_screen4_places_visuals_after_guarded_state_and_evidence_sections(self) -> None:
        html = self.render_screen4(valid_report())

        self.assertIn("screen4-deep-analysis-guarded-state", html)
        self.assertIn("screen4-deep-analysis-evidence-sections", html)
        self.assertIn("screen4-deep-analysis-visual-evidence", html)
        self.assertLess(html.index("screen4-deep-analysis-guarded-state"), html.index("screen4-deep-analysis-evidence-sections"))
        self.assertLess(html.index("screen4-deep-analysis-evidence-sections"), html.index("screen4-deep-analysis-visual-evidence"))
        self.assertLess(html.index("screen4-deep-analysis-visual-evidence"), html.index("screen4-comparative-review-guard"))
        self.assert_no_browser_chart_runtime(html)

        blocked_html = self.render_screen4({})
        self.assertNotIn("screen4-deep-analysis-visual-evidence", blocked_html)
        self.assertNotIn("screen4-deep-analysis-static-visual", blocked_html)

    def test_module_has_no_dashboard_import_or_runtime_service_dependency(self) -> None:
        module = visuals_module()
        source = inspect.getsource(module)

        self.assertTrue(hasattr(module, "render_deep_analysis_visualizations"))
        for forbidden in ("html_dashboard", "dashboard_workflow_service", "call_llm", "Chart.js", "Plotly"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def assert_no_browser_chart_runtime(self, html: str) -> None:
        lower = html.lower()
        for forbidden in (
            "<script",
            "<canvas",
            "chart.js",
            "plotly",
            "data-browser-computation",
            "screen4-comparative-visuals",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, lower)


if __name__ == "__main__":
    unittest.main()
