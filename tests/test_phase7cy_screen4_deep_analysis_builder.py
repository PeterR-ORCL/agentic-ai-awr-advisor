from __future__ import annotations

import importlib
import inspect
import unittest


def builder_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_builder")


def contract_module():
    return importlib.import_module("src.reporting.dashboard.screen4.deep_analysis_contract")


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


def selected_scope(**overrides) -> dict[str, object]:
    payload = {
        "source_scope": "current_selected_diagnostic_scope",
        "selected_run_id": "RUN-7CY-D",
        "selected_source_identifier": {
            "source_artifact_id": "artifact-7cy-d",
            "db_name": "FINDB",
            "dbid": "101",
        },
        "selected_snapshot_identifier": {
            "awr_id": "AWR-7CY-D",
            "snapshot_begin": "2026-06-06T10:00:00Z",
            "snapshot_end": "2026-06-06T11:00:00Z",
        },
        "current_diagnostic_output_ref": {
            "run_id": "RUN-7CY-D",
            "diagnostic_output_id": "diag-7cy-d",
        },
    }
    payload.update(overrides)
    return payload


def generation_context(**overrides) -> dict[str, object]:
    payload = {
        "generated_at": "2026-06-06T12:00:00Z",
        "dashboard_generation_id": "dashboard-7cy-d",
        "deterministic_engine_version": "phase7cy-deep-analysis-v1",
        "freshness": {
            "freshness_status": "fresh",
            "source_payload_hash": "hash-7cy-d",
            "generated_at": "2026-06-06T12:00:00Z",
        },
        "provenance": {
            "source_contract_ref": "screen3.normalized_decision",
            "deterministic_engine_version": "phase7cy-deep-analysis-v1",
        },
    }
    payload.update(overrides)
    return payload


def current_report(**overrides) -> dict[str, object]:
    payload = {
        "metadata": {
            "run_id": "RUN-7CY-D",
            "db_name": "FINDB",
            "dbid": "101",
            "awr_id": "AWR-7CY-D",
            "snapshot_begin": "2026-06-06T10:00:00Z",
            "snapshot_end": "2026-06-06T11:00:00Z",
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


class Screen4DeepAnalysisBuilderTests(unittest.TestCase):
    def build(self, **overrides):
        module = builder_module()
        kwargs = {
            "report_data": current_report(),
            "selected_scope": selected_scope(),
            "screen_model": {},
            "chart_payload": {},
            "generation_context": generation_context(),
        }
        kwargs.update(overrides)
        return module.build_deep_analysis_contract(**kwargs)

    def build_and_validate(self, **overrides):
        module = builder_module()
        kwargs = {
            "report_data": current_report(),
            "selected_scope": selected_scope(),
            "screen_model": {},
            "chart_payload": {},
            "generation_context": generation_context(),
        }
        kwargs.update(overrides)
        return module.build_and_validate_deep_analysis_contract(**kwargs)

    def codes(self, result) -> set[str]:
        return {message.code for message in result.messages}

    def test_minimal_valid_build_is_ready(self) -> None:
        contract, result = self.build_and_validate()

        self.assertTrue(result.is_ready)
        self.assertEqual(contract_module().DeepAnalysisState.READY, result.state)
        self.assertEqual("screen4_deep_analysis_contract", contract["contract_type"])
        self.assertEqual("deterministic_backend", contract["generated_by"])
        self.assertEqual("current_selected_diagnostic_scope", contract["source_scope"])
        self.assertTrue(contract["evidence_sections"])
        self.assertTrue(contract["evidence_rows"])
        self.assertIn("current-diagnostic-truth", result.allowed_section_ids)

    def test_missing_source_identity_does_not_produce_ready_contract(self) -> None:
        report = {
            "decision": {"primary_issue": "CPU", "severity_score": 72},
            "scores": {"domain_scores": {"CPU": 72}},
        }

        contract, result = self.build_and_validate(
            report_data=report,
            selected_scope={},
        )

        self.assertFalse(result.is_ready)
        self.assertIn("selected_identifier_missing", self.codes(result))
        self.assertFalse(contract["selected_run_id"])
        self.assertIsNone(contract["selected_source_identifier"])
        self.assertIsNone(contract["selected_snapshot_identifier"])

    def test_missing_provenance_and_freshness_are_not_faked(self) -> None:
        contract, result = self.build_and_validate(generation_context={})

        self.assertFalse(result.is_ready)
        self.assertEqual({}, contract["provenance"])
        self.assertEqual({}, contract["freshness"])
        self.assertIn("provenance_missing", self.codes(result))
        self.assertIn("freshness_missing", self.codes(result))

    def test_immutable_truth_refs_preserve_read_only_current_truth(self) -> None:
        contract = self.build()

        refs = contract["immutable_truth_refs"]
        self.assertEqual("CPU", refs["primary_domain_ref"]["value"])
        self.assertEqual({"CPU": 72, "IO": 18}, refs["score_ref"]["value"])
        self.assertEqual("WARNING", refs["severity_ref"]["value"])
        self.assertEqual(0.91, refs["confidence_ref"]["value"])
        self.assertEqual("investigate", refs["posture_ref"]["value"])
        self.assertEqual("Tune SQL", refs["recommendation_ref"]["value"])
        self.assertTrue(all(ref["read_only"] for ref in refs.values()))
        self.assertTrue(all(value is False for value in contract["mutation_boundaries"].values()))

    def test_current_diagnostics_become_current_scope_rows_only(self) -> None:
        contract = self.build()

        rows = contract["evidence_rows"]
        current_rows = [row for row in rows if row["scope_classification"] == "current_scope"]
        self.assertTrue(current_rows)
        self.assertTrue(all(row["provenance"] for row in current_rows))
        self.assertTrue(all(row["freshness_status"] == "fresh" for row in current_rows))
        self.assertTrue(all(row["supports_existing_truth_ref"] for row in current_rows))
        self.assertTrue(any(row.get("evidence_type") == "top_sql_detail" for row in current_rows))
        self.assertFalse(any(row.get("synthetic") or row.get("llm_generated") for row in current_rows))

    def test_historical_support_is_supporting_only_and_not_ready_by_itself(self) -> None:
        report = {
            "time_series_charts": {
                "snapshot_labels": ["s1", "s2", "s3"],
                "cpu_trend": [60, 62, 63],
            },
            "violin_panel": {"workload": {"cluster_cpu_pct_db_time": [60, 62, 63]}},
        }
        context = generation_context(immutable_truth_refs=immutable_truth_refs())

        contract, result = self.build_and_validate(
            report_data=report,
            selected_scope=selected_scope(),
            generation_context=context,
        )

        self.assertFalse(result.is_ready)
        self.assertEqual(
            contract_module().DeepAnalysisState.HISTORICAL_SUPPORTING_CONTEXT,
            result.state,
        )
        self.assertTrue(result.supporting_section_ids)
        self.assertFalse(
            any(row["scope_classification"] == "current_scope" for row in contract["evidence_rows"])
        )

    def test_comparative_inputs_do_not_create_deep_analysis_evidence_or_readiness(self) -> None:
        report = {
            "comparative_review_state": {"state": "comparison_output_ready"},
            "metric_deltas": [{"metric": "cpu", "delta": -12}],
            "domain_deltas": [{"domain": "CPU"}],
            "evidence_rows": [{"category": "score", "metric": "cpu", "delta": -12}],
            "allowed_visualizations": ["time_series_overlay"],
            "visual_eligibility": [{"visualization_name": "time_series_overlay", "status": "eligible"}],
        }
        context = generation_context(immutable_truth_refs=immutable_truth_refs())

        contract, result = self.build_and_validate(
            report_data=report,
            selected_scope=selected_scope(),
            generation_context=context,
        )

        self.assertFalse(result.is_ready)
        self.assertFalse(contract["evidence_rows"])
        self.assertFalse(any("metric_deltas" in row.get("source_path", "") for row in contract["evidence_rows"]))
        self.assertTrue(any(item["type"] == "comparative_output_blocked" for item in contract["limitations"]))
        self.assertNotIn("metric_deltas", contract)
        self.assertNotIn("allowed_visualizations", contract)

    def test_prepared_and_cache_inputs_do_not_create_deep_analysis_evidence(self) -> None:
        prepared_report = {
            "comparison_prepared_context": {
                "target_a": {"run_id": "RUN-A"},
                "target_b": {"run_id": "RUN-B"},
            }
        }
        cache_report = {
            "browser_cache_state": {"selected_run_id": "RUN-CACHED"},
            "localStorage": {"screen4": "cached"},
            "hash_state": {"screen": "4"},
        }
        context = generation_context(immutable_truth_refs=immutable_truth_refs())

        for report in (prepared_report, cache_report):
            with self.subTest(report=report):
                contract, result = self.build_and_validate(
                    report_data=report,
                    selected_scope=selected_scope(),
                    generation_context=context,
                )
                self.assertFalse(result.is_ready)
                self.assertFalse(contract["evidence_rows"])

        cache_scope_contract, cache_scope_result = self.build_and_validate(
            report_data=current_report(),
            selected_scope=selected_scope(cache_status="cached_continuity_only"),
        )
        self.assertFalse(cache_scope_result.is_ready)
        self.assertEqual("cache_only", cache_scope_contract["source_scope"])

    def test_llm_text_is_not_evidence_and_generator_stays_backend(self) -> None:
        contract, result = self.build_and_validate(
            report_data=current_report(
                llm_explanation={
                    "technical_explanation": "An LLM says CPU is the cause.",
                }
            )
        )

        self.assertTrue(result.is_ready)
        self.assertEqual("deterministic_backend", contract["generated_by"])
        self.assertFalse(
            any("llm" in str(row.get("source_path", "")).lower() for row in contract["evidence_rows"])
        )
        self.assertTrue(any(item["type"] == "llm_text_not_evidence" for item in contract["limitations"]))

    def test_missing_optional_evidence_is_reported_without_fake_rows(self) -> None:
        report = current_report(top_sql=[])

        contract, result = self.build_and_validate(report_data=report)

        self.assertTrue(result.is_ready)
        self.assertFalse(any(row.get("evidence_type") == "top_sql_detail" for row in contract["evidence_rows"]))
        self.assertTrue(any(item["type"] == "top_sql_missing" for item in contract["missing_evidence"]))

    def test_chart_eligibility_is_validation_only_and_conservative(self) -> None:
        chart_only_context = generation_context(
            immutable_truth_refs=immutable_truth_refs(),
            chart_eligibility=[
                {
                    "chart_type": "wait_breakdown",
                    "required_evidence_shape": "current_scope_wait_rows",
                    "source_paths": ["evidence_rows"],
                    "eligibility_status": "eligible",
                }
            ],
        )
        chart_only_contract, chart_only_result = self.build_and_validate(
            report_data={},
            selected_scope=selected_scope(),
            generation_context=chart_only_context,
        )
        self.assertFalse(chart_only_result.is_ready)
        self.assertFalse(chart_only_contract["evidence_rows"])
        self.assertEqual(False, chart_only_contract["chart_eligibility"][0]["browser_computation_allowed"])
        self.assertEqual(False, chart_only_contract["chart_eligibility"][0]["synthetic_data_allowed"])
        self.assertEqual(False, chart_only_contract["chart_eligibility"][0]["empty_chart_allowed"])

        unsafe_contract, unsafe_result = self.build_and_validate(
            generation_context=generation_context(
                chart_eligibility=[
                    {
                        "chart_type": "wait_breakdown",
                        "required_evidence_shape": "current_scope_wait_rows",
                        "source_paths": ["evidence_rows"],
                        "eligibility_status": "eligible",
                        "browser_computation_allowed": True,
                    }
                ]
            )
        )
        self.assertFalse(unsafe_result.is_ready)
        self.assertIn("chart_browser_computation_allowed", self.codes(unsafe_result))
        self.assertEqual(True, unsafe_contract["chart_eligibility"][0]["browser_computation_allowed"])

    def test_builder_uses_validator_for_readiness(self) -> None:
        module = builder_module()
        contract, result = self.build_and_validate()
        direct_result = module.validate_deep_analysis_contract(contract)

        self.assertEqual(direct_result.to_dict(), result.to_dict())

    def test_import_has_no_rendering_side_effects(self) -> None:
        module = builder_module()
        source = inspect.getsource(module)

        self.assertTrue(hasattr(module, "build_deep_analysis_contract"))
        self.assertNotIn("html_dashboard", source)
        self.assertNotIn("comparative_visuals", source)
        self.assertNotIn("dashboard_workflow_service", source)


if __name__ == "__main__":
    unittest.main()
