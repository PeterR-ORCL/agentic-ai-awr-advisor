from __future__ import annotations

import copy
import importlib
import unittest


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
    }


def evidence_section(**overrides) -> dict[str, object]:
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


def evidence_row(**overrides) -> dict[str, object]:
    payload = {
        "row_id": "row-current-cpu",
        "section_id": "current-drivers",
        "scope_classification": "current_scope",
        "evidence_type": "diagnostic_driver",
        "metric_name": "CPU score",
        "deterministic_value": 72,
        "source_path": "report_data.decision.evidence.feature_evidence.cpu",
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
        "generated_at": "2026-06-06T12:00:00Z",
        "deterministic_engine_version": "phase7cy-deep-analysis-v1",
        "source_scope": "current_selected_diagnostic_scope",
        "selected_run_id": "RUN-7CY-C",
        "selected_source_identifier": {"source_artifact_id": "artifact-7cy-c"},
        "selected_snapshot_identifier": {"awr_id": "AWR-7CY-C"},
        "generation_context": {"dashboard_generation_id": "dashboard-7cy-c"},
        "freshness": {"freshness_status": "fresh", "source_payload_hash": "hash-7cy-c"},
        "provenance": {"source_contract_ref": "screen3.normalized_decision"},
        "current_diagnostic_output_ref": {"run_id": "RUN-7CY-C", "diagnostic_output_id": "diag-7cy-c"},
        "immutable_truth_refs": immutable_truth_refs(),
        "evidence_sections": [evidence_section()],
        "evidence_rows": [evidence_row()],
        "chart_eligibility": [],
        "limitations": [],
        "missing_evidence": [],
        "validation_messages": [],
        "llm_explanation_boundary": {"llm_can_create_evidence": False},
        "mutation_boundaries": mutation_boundaries(),
    }
    payload.update(overrides)
    return copy.deepcopy(payload)


class Screen4DeepAnalysisContractTests(unittest.TestCase):
    def validate(self, payload):
        return contract_module().validate_deep_analysis_contract(payload)

    def codes(self, result) -> set[str]:
        return {message.code for message in result.messages}

    def test_valid_current_scope_contract_is_ready(self) -> None:
        module = contract_module()

        result = self.validate(valid_contract())

        self.assertTrue(result.is_ready)
        self.assertEqual(module.ValidationStatus.VALID, result.status)
        self.assertEqual(module.DeepAnalysisState.READY, result.state)
        self.assertEqual(("current-drivers",), result.allowed_section_ids)
        self.assertEqual(module.DeepAnalysisState.READY, module.determine_deep_analysis_state(valid_contract()))

    def test_contract_identity_is_required(self) -> None:
        module = contract_module()
        cases = (
            (None, "contract_not_mapping"),
            ("contract", "contract_not_mapping"),
            ({}, "contract_missing"),
            ({**valid_contract(), "contract_type": "other"}, "contract_type_invalid"),
            ({**valid_contract(), "contract_version": "0.0"}, "contract_version_unsupported"),
        )

        for payload, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                result = self.validate(payload)
                self.assertFalse(result.is_ready)
                self.assertIn(expected_code, self.codes(result))

        accepted = self.validate({**valid_contract(), "contract_version": "7cy.screen4.deep_analysis.v1"})
        self.assertTrue(accepted.is_ready)
        self.assertEqual("1.0", module.SUPPORTED_CONTRACT_VERSION)

    def test_generator_boundary_rejects_llm_and_browser(self) -> None:
        for generated_by, expected_code in (
            ("llm", "generated_by_llm_blocked"),
            ("browser", "generated_by_browser_blocked"),
            ("operator", "generated_by_not_deterministic_backend"),
        ):
            with self.subTest(generated_by=generated_by):
                result = self.validate({**valid_contract(), "generated_by": generated_by})
                self.assertFalse(result.is_ready)
                self.assertIn(expected_code, self.codes(result))

        self.assertTrue(self.validate({**valid_contract(), "generated_by": "deterministic_engine"}).is_ready)

    def test_scope_source_identity_and_truth_refs_are_required(self) -> None:
        cases = (
            ({k: v for k, v in valid_contract().items() if k not in {"selected_run_id", "selected_source_identifier", "selected_snapshot_identifier"}}, "selected_identifier_missing"),
            ({**valid_contract(), "source_scope": "cache_only"}, "source_scope_not_current_selected_scope"),
            ({k: v for k, v in valid_contract().items() if k != "current_diagnostic_output_ref"}, "current_diagnostic_output_ref_missing"),
            ({k: v for k, v in valid_contract().items() if k != "immutable_truth_refs"}, "immutable_truth_refs_missing"),
            ({**valid_contract(), "immutable_truth_refs": {"score_ref": {"ref": "truth.score", "read_only": False}}}, "immutable_truth_ref_not_read_only"),
        )

        for payload, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                result = self.validate(payload)
                self.assertFalse(result.is_ready)
                self.assertIn(expected_code, self.codes(result))

    def test_provenance_and_freshness_are_required_and_current(self) -> None:
        cases = (
            ({k: v for k, v in valid_contract().items() if k != "provenance"}, "provenance_missing"),
            ({k: v for k, v in valid_contract().items() if k != "freshness"}, "freshness_missing"),
            ({**valid_contract(), "freshness": {"freshness_status": "stale"}}, "freshness_stale"),
            ({**valid_contract(), "freshness": {"freshness_status": "cache_only"}}, "freshness_stale"),
        )

        for payload, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                result = self.validate(payload)
                self.assertFalse(result.is_ready)
                self.assertIn(expected_code, self.codes(result))

    def test_mutation_boundaries_are_required_and_false(self) -> None:
        missing = {k: v for k, v in valid_contract().items() if k != "mutation_boundaries"}
        missing_result = self.validate(missing)
        self.assertFalse(missing_result.is_ready)
        self.assertIn("mutation_boundaries_missing", self.codes(missing_result))

        for flag in contract_module().MUTATION_BOUNDARY_FLAGS:
            with self.subTest(flag=flag):
                boundaries = mutation_boundaries()
                boundaries[flag] = True
                result = self.validate({**valid_contract(), "mutation_boundaries": boundaries})
                self.assertFalse(result.is_ready)
                self.assertIn("mutation_boundary_true", self.codes(result))

    def test_evidence_scope_misuse_blocks_readiness(self) -> None:
        cases = (
            ("cache_only", "row_scope_blocked"),
            ("prepared_only", "row_scope_blocked"),
            ("comparative_output", "row_comparative_output_blocked"),
            ("fleet_population", "row_fleet_population_blocked"),
            ("llm_explanation_only", "row_scope_blocked"),
            ("unknown_or_mixed", "row_scope_blocked"),
        )

        for scope, expected_code in cases:
            with self.subTest(scope=scope):
                row = evidence_row(scope_classification=scope)
                section = evidence_section(scope_classification=scope)
                result = self.validate(valid_contract(evidence_rows=[row], evidence_sections=[section]))
                self.assertFalse(result.is_ready)
                self.assertIn(expected_code, self.codes(result))

    def test_historical_support_is_supporting_only(self) -> None:
        module = contract_module()
        section = evidence_section(
            section_id="historical-context",
            scope_classification="historical_supporting_context",
            evidence_type="time_series_supporting_context",
        )
        row = evidence_row(
            row_id="historical-row",
            section_id="historical-context",
            scope_classification="historical_supporting_context",
            evidence_type="time_series_supporting_context",
            supports_existing_truth_ref={},
        )

        result = self.validate(valid_contract(evidence_sections=[section], evidence_rows=[row]))

        self.assertFalse(result.is_ready)
        self.assertEqual(module.DeepAnalysisState.HISTORICAL_SUPPORTING_CONTEXT, result.state)
        self.assertEqual(("historical-context",), result.supporting_section_ids)

        primary = self.validate(valid_contract(evidence_sections=[section], evidence_rows=[{**row, "primary_evidence": True}]))
        self.assertFalse(primary.is_ready)
        self.assertIn("row_historical_primary_blocked", self.codes(primary))

    def test_row_integrity_blocks_invalid_rows(self) -> None:
        cases = (
            ({**evidence_row(), "synthetic": True}, "row_placeholder_or_synthetic"),
            ({**evidence_row(), "demo": True}, "row_placeholder_or_synthetic"),
            ({**evidence_row(), "placeholder": True}, "row_placeholder_or_synthetic"),
            ({**evidence_row(), "hard_coded": True}, "row_placeholder_or_synthetic"),
            ({**evidence_row(), "llm_generated": True}, "row_llm_generated"),
            ({k: v for k, v in evidence_row().items() if k != "supports_existing_truth_ref"}, "row_truth_ref_missing"),
            ({**evidence_row(), "freshness_status": "stale"}, "row_freshness_stale"),
            ({k: v for k, v in evidence_row().items() if k != "provenance"}, "row_provenance_missing"),
        )

        for row, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                result = self.validate(valid_contract(evidence_rows=[row]))
                self.assertFalse(result.is_ready)
                self.assertIn(expected_code, self.codes(result))

    def test_section_integrity_blocks_empty_normal_sections(self) -> None:
        empty_normal = evidence_section(rows_present=False, allowed_rendering="evidence_table")

        result = self.validate(valid_contract(evidence_sections=[empty_normal]))

        self.assertFalse(result.is_ready)
        self.assertIn("section_empty_without_blocked_state", self.codes(result))
        self.assertIn("current-drivers", result.omitted_section_ids)

        blocked_section = evidence_section(
            evidence_type="limitation",
            rows_present=False,
            allowed_rendering="blocked_state",
        )
        blocked_result = self.validate(valid_contract(evidence_sections=[blocked_section], evidence_rows=[]))
        self.assertFalse(blocked_result.is_ready)
        self.assertEqual(set(), self.codes(blocked_result))

    def test_chart_eligibility_does_not_create_evidence_or_allow_unsafe_charts(self) -> None:
        module = contract_module()
        chart = {
            "chart_type": "wait_breakdown",
            "required_evidence_shape": "current_scope_wait_rows",
            "source_paths": ["evidence_rows"],
            "eligibility_status": "eligible",
            "browser_computation_allowed": False,
            "synthetic_data_allowed": False,
            "empty_chart_allowed": False,
        }
        blocked_section = evidence_section(
            evidence_type="limitation",
            rows_present=False,
            allowed_rendering="blocked_state",
        )
        chart_only = self.validate(
            valid_contract(evidence_sections=[blocked_section], evidence_rows=[], chart_eligibility=[chart])
        )

        self.assertFalse(chart_only.is_ready)
        self.assertEqual(module.DeepAnalysisState.CURRENT_SCOPE, chart_only.state)

        for field, expected_code in (
            ("browser_computation_allowed", "chart_browser_computation_allowed"),
            ("synthetic_data_allowed", "chart_synthetic_data_allowed"),
            ("empty_chart_allowed", "chart_empty_chart_allowed"),
        ):
            with self.subTest(field=field):
                unsafe_chart = {**chart, field: True}
                result = self.validate(valid_contract(chart_eligibility=[unsafe_chart]))
                self.assertFalse(result.is_ready)
                self.assertIn(expected_code, self.codes(result))

        missing_shape = self.validate(valid_contract(chart_eligibility=[{"chart_type": "waits", "eligibility_status": "eligible"}]))
        self.assertFalse(missing_shape.is_ready)
        self.assertIn("chart_eligible_missing_evidence_shape", self.codes(missing_shape))

    def test_7cx_fields_do_not_create_deep_analysis_readiness(self) -> None:
        comparative_row = evidence_row(
            scope_classification="comparative_output",
            evidence_type="metric_delta",
            evidence_name="CPU delta",
            deterministic_value=-12,
        )
        payload = valid_contract(
            evidence_rows=[comparative_row],
            metric_deltas=[{"metric": "cpu", "delta": -12}],
            domain_deltas=[{"domain": "CPU"}],
            allowed_visualizations=["metric_delta_table"],
            visual_eligibility=[{"visualization_name": "time_series_overlay", "status": "eligible"}],
        )

        result = self.validate(payload)

        self.assertFalse(result.is_ready)
        self.assertIn("row_comparative_output_blocked", self.codes(result))
        self.assertIn("comparative_delta_fields_not_deep_analysis_evidence", self.codes(result))
        self.assertIn("comparative_allowed_visualizations_not_evidence", self.codes(result))
        self.assertIn("comparative_visual_eligibility_not_evidence", self.codes(result))

    def test_section_llm_generated_is_blocked(self) -> None:
        result = self.validate(
            valid_contract(evidence_sections=[evidence_section(llm_generated=True)])
        )

        self.assertFalse(result.is_ready)
        self.assertIn("section_llm_generated", self.codes(result))


if __name__ == "__main__":
    unittest.main()
