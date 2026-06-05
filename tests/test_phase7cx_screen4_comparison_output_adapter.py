from __future__ import annotations

import importlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_DOC = ROOT / "docs" / "architecture" / "phase7cx_screen4_comparison_output_adapter.md"
CONTRACT_DOC = ROOT / "docs" / "architecture" / "phase7cx_screen4_comparative_review_contract.md"
EXECUTION_DOC = ROOT / "docs" / "architecture" / "phase7cc_comparison_execution.md"


def adapter_module():
    return importlib.import_module("src.learning.screen4_comparison_contract")


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


def reanalysis_module():
    return importlib.import_module("src.learning.screen3_reanalysis_controller")


def execution_module():
    return importlib.import_module("src.learning.screen3_comparison_execution")


class Screen4ComparisonOutputAdapterTests(unittest.TestCase):
    def make_inputs(self) -> list[dict[str, object]]:
        return [
            {
                "comparison_input_status": "already_loaded",
                "run_id": "RUN-7CX-BASE",
                "awr_id": "AWR-7CX-BASE",
                "dbid": "101",
                "database_name": "BASEDB",
                "snapshot_label": "baseline",
                "scores": {"overall": 82, "cpu": 70},
                "domain_scores": {"io": 64},
                "waits": {"db file sequential read": 110, "log file sync": 12},
                "wait_events": {"CPU": 240},
                "sql_concentration": {"top_sql_elapsed_pct": 41},
                "top_sql_concentration": {"top_sql_count": 8},
                "trends": {"cpu": "baseline-visible", "io": "baseline-flat"},
                "anomalies": {"cpu_spike": False, "io_spike": False},
                "topology": {"instances": 1, "rac": False},
                "platform_target": {"target": "ExaDB-D"},
                "data_availability": {"ash": True, "sqlstats": True},
                "missing_metrics": [],
            },
            {
                "comparison_input_status": "comparison_ready",
                "run_id": "RUN-7CX-CANDIDATE",
                "awr_id": "AWR-7CX-CANDIDATE",
                "dbid": "101",
                "database_name": "BASEDB",
                "snapshot_label": "candidate",
                "scores": {"overall": 76, "cpu": 58},
                "waits": {"db file sequential read": 145, "log file sync": 18},
                "wait_events": {"CPU": 310},
                "sql_concentration": {"top_sql_elapsed_pct": 56},
                "top_sql_concentration": {"top_sql_count": 14},
                "trends": {"cpu": "candidate-visible", "io": "candidate-flat"},
                "anomalies": {"cpu_spike": True, "io_spike": False},
                "topology": {"instances": 2, "rac": True},
                "platform_target": {"target": "ADB-D"},
                "data_availability": {"ash": False},
                "missing_metrics": ["sqlstats"],
            },
        ]

    def make_artifact(self):
        module = reanalysis_module()
        return module.build_awr_report_comparison(
            self.make_inputs(),
            comparison_name="7CX adapter comparison",
            baseline_reference="RUN-7CX-BASE",
            created_by="ACTOR-7CX",
            notes="adapter unit test",
        )

    def make_execution_result(self):
        module = execution_module()
        artifact = self.make_artifact()
        output_reference = module.ComparisonOutputReference(
            output_reference_id="OUTPUT-7CX-COMPARISON",
            comparison_id=artifact.comparison_id,
            artifact_type="comparison_artifact",
            artifact_reference=f"comparison:{artifact.comparison_id}",
            artifact_summary=artifact.difference_summary,
            persisted=True,
            output_written=False,
            dashboard_regenerated=False,
            phase4i_mutated=False,
            notes="adapter unit test",
        )
        return module.ComparisonExecutionResult(
            comparison_execution_id="SCREEN3-COMPARISON-EXECUTION-7CX",
            request_id="REQ-7CX-COMPARISON",
            idempotency_key="IDEMP-7CX-COMPARISON",
            transaction_group_id="TX-7CX-COMPARISON",
            execution_status="comparison_persisted_metadata",
            comparison_built=True,
            comparison_artifact=artifact,
            workflow_request_persisted=True,
            workflow_validation_persisted=True,
            workflow_audit_persisted=True,
            output_artifacts_persisted=True,
            idempotent_replay=False,
            run_analysis_called=False,
            subprocess_called=False,
            object_storage_called=False,
            local_file_read_performed=False,
            parser_called=False,
            db_lookup_performed=False,
            dashboard_regenerated=False,
            phase4i_mutated=False,
            adaptive_runtime_used=False,
            phase8_sizing_tco_used=False,
            output_references=(output_reference,),
            denied_reasons=[],
            warnings=["comparison artifact metadata persisted; no artifact file was written"],
            required_next_steps=["review persisted comparison artifact metadata"],
            notes="adapter unit test",
        )

    def prepared_context(self) -> dict[str, object]:
        return {
            "source_scope": "same_db_historical",
            "comparison_scope": "target_a_vs_target_b",
            "target_a": {
                "run_id": "RUN-7CX-BASE",
                "awr_id": "AWR-7CX-BASE",
                "dbid": "101",
                "db_name": "BASEDB",
                "snapshot_label": "baseline",
                "source_type": "existing_run",
                "scope_type": "run",
                "scope_value": "RUN-7CX-BASE",
                "window": "baseline window",
            },
            "target_b": {
                "run_id": "RUN-7CX-CANDIDATE",
                "awr_id": "AWR-7CX-CANDIDATE",
                "dbid": "101",
                "db_name": "BASEDB",
                "snapshot_label": "candidate",
                "source_type": "existing_run",
                "scope_type": "run",
                "scope_value": "RUN-7CX-CANDIDATE",
                "window": "candidate window",
            },
        }

    def valid_adapter_result(self):
        adapter = adapter_module()
        return adapter.adapt_screen4_deterministic_comparison_output(
            self.make_execution_result(),
            prepared_target_context=self.prepared_context(),
            workflow_metadata={
                "workflow_request_id": "WF-REQ-7CX-COMPARISON",
                "workflow_transaction_id": "TX-7CX-COMPARISON",
                "artifact_source": "phase7cc_comparison_execution",
            },
            generated_at="2026-06-05T12:00:00Z",
        )

    def test_raw_7cc_artifact_is_not_screen4_output_ready(self) -> None:
        adapter = adapter_module()
        dashboard = dashboard_module()
        reanalysis = reanalysis_module()
        artifact_dict = reanalysis.awr_report_comparison_artifact_to_dict(
            self.make_artifact()
        )

        validation = dashboard._screen4_validate_deterministic_comparison_output(
            artifact_dict
        )
        self.assertFalse(validation["valid"])

        result = adapter.adapt_screen4_deterministic_comparison_output(
            artifact_dict,
            generated_at="2026-06-05T12:00:00Z",
        )
        self.assertFalse(result.output_ready)
        self.assertEqual("invalid", result.validation_status)
        self.assertTrue(
            any(message.code == "target_a_identity_missing" for message in result.messages)
        )

    def test_adapter_rejects_missing_target_identity(self) -> None:
        adapter = adapter_module()

        result = adapter.adapt_screen4_deterministic_comparison_output(
            self.make_artifact(),
            prepared_target_context={},
            generated_at="2026-06-05T12:00:00Z",
        )

        self.assertFalse(result.output_ready)
        self.assertIn(
            "target_a_identity_missing",
            {message.code for message in result.messages},
        )
        self.assertIn(
            "target_b_identity_missing",
            {message.code for message in result.messages},
        )

    def test_adapter_rejects_target_ab_mismatch(self) -> None:
        adapter = adapter_module()
        context = self.prepared_context()
        context["target_b"] = {
            **context["target_b"],
            "run_id": "RUN-7CX-OTHER",
        }

        result = adapter.adapt_screen4_deterministic_comparison_output(
            self.make_artifact(),
            prepared_target_context=context,
            generated_at="2026-06-05T12:00:00Z",
        )

        self.assertFalse(result.output_ready)
        self.assertIn("target_b_mismatch", {message.code for message in result.messages})

    def test_adapter_rejects_missing_generated_at(self) -> None:
        adapter = adapter_module()

        result = adapter.adapt_screen4_deterministic_comparison_output(
            self.make_artifact(),
            prepared_target_context=self.prepared_context(),
        )

        self.assertFalse(result.output_ready)
        self.assertIn("generated_at_missing", {message.code for message in result.messages})

    def test_adapter_rejects_missing_deterministic_engine_version(self) -> None:
        adapter = adapter_module()

        result = adapter.adapt_screen4_deterministic_comparison_output(
            self.make_artifact(),
            prepared_target_context=self.prepared_context(),
            generated_at="2026-06-05T12:00:00Z",
            deterministic_engine_version="",
        )

        self.assertFalse(result.output_ready)
        self.assertIn(
            "deterministic_engine_version_missing",
            {message.code for message in result.messages},
        )

    def test_validator_rejects_generated_by_not_deterministic_engine(self) -> None:
        adapter = adapter_module()
        result = self.valid_adapter_result()
        self.assertTrue(result.output_ready)

        validation = adapter.validate_screen4_comparison_contract(
            {**result.contract, "generated_by": "browser"}
        )

        self.assertFalse(validation.output_ready)
        self.assertIn("generated_by_invalid", {message.code for message in validation.messages})

    def test_valid_adapter_output_passes_screen4_validator_and_state(self) -> None:
        dashboard = dashboard_module()
        result = self.valid_adapter_result()

        self.assertTrue(result.output_ready)
        contract = result.contract
        self.assertEqual("deterministic_comparison_output", contract["screen4_contract_type"])
        self.assertEqual("deterministic_engine", contract["generated_by"])
        self.assertIsInstance(contract["metric_deltas"], list)
        self.assertIsInstance(contract["domain_deltas"], list)
        self.assertIsInstance(contract["evidence_rows"], list)
        self.assertEqual(
            "deterministic_evidence",
            contract["confidence_basis"]["basis_type"],
        )
        self.assertIsInstance(contract["missing_evidence"], list)

        validation = dashboard._screen4_validate_deterministic_comparison_output(
            contract,
            selected_context={
                "target_a": {"run_id": "RUN-7CX-BASE"},
                "target_b": {"run_id": "RUN-7CX-CANDIDATE"},
            },
        )
        self.assertTrue(validation["valid"], validation)

        state = dashboard._screen4_build_comparative_review_state(
            {"deterministic_comparison_output": contract}
        )
        self.assertEqual("comparison_output_ready", state["state"])

    def test_adapter_grants_only_conservative_visualizations(self) -> None:
        result = self.valid_adapter_result()

        self.assertIn("metric_delta_table", result.allowed_visualizations)
        self.assertIn("domain_delta_summary", result.allowed_visualizations)
        self.assertIn("confidence_basis_panel", result.allowed_visualizations)
        self.assertIn("missing_evidence_panel", result.allowed_visualizations)
        for visualization in (
            "distribution_violin",
            "time_series_overlay",
            "top_sql_movement_table",
            "top_event_movement_table",
            "wait_class_movement_table",
        ):
            with self.subTest(visualization=visualization):
                self.assertNotIn(visualization, result.allowed_visualizations)

    def test_serialized_repository_output_artifact_can_be_adapted(self) -> None:
        adapter = adapter_module()
        reanalysis = reanalysis_module()
        artifact = reanalysis.awr_report_comparison_artifact_to_dict(
            self.make_artifact()
        )

        result = adapter.adapt_screen4_deterministic_comparison_output(
            {
                "workflow_output_id": "OUTPUT-7CX-REPO",
                "workflow_request_id": "WF-REQ-7CX-REPO",
                "artifact_type": "comparison_artifact",
                "artifact_reference": f"comparison:{artifact['comparison_id']}",
                "artifact_metadata": {"comparison_artifact": artifact},
                "created_at": "2026-06-05T12:00:00Z",
            },
            prepared_target_context=self.prepared_context(),
        )

        self.assertTrue(result.output_ready, result.to_dict())
        self.assertEqual(
            ["OUTPUT-7CX-REPO"],
            result.contract["input_artifact_ids"],
        )

    def test_cache_or_route_artifact_reference_remains_rejected(self) -> None:
        adapter = adapter_module()
        dashboard = dashboard_module()

        result = adapter.adapt_screen4_deterministic_comparison_output(
            {"comparison_artifact_reference": "comparison:cached-only"},
            prepared_target_context=self.prepared_context(),
            generated_at="2026-06-05T12:00:00Z",
        )
        self.assertFalse(result.output_ready)

        state = dashboard._screen4_build_comparative_review_state(
            {
                "comparison_cache_status": "cached_continuity_only",
                "comparison_artifact_reference": "comparison:cached-only",
            }
        )
        self.assertNotEqual("comparison_output_ready", state["state"])

    def test_llm_text_cannot_satisfy_evidence_rows(self) -> None:
        adapter = adapter_module()
        result = self.valid_adapter_result()

        contract = {
            **result.contract,
            "evidence_rows": [
                {
                    "evidence_source": "llm",
                    "llm_explanation": "Generated wording is not evidence.",
                }
            ],
        }
        validation = adapter.validate_screen4_comparison_contract(contract)

        self.assertFalse(validation.output_ready)
        self.assertIn("llm_evidence_rejected", {message.code for message in validation.messages})

    def test_adapter_documentation_records_boundary(self) -> None:
        self.assertTrue(ADAPTER_DOC.is_file())
        text = ADAPTER_DOC.read_text(encoding="utf-8").lower()
        contract_text = CONTRACT_DOC.read_text(encoding="utf-8").lower()
        execution_text = EXECUTION_DOC.read_text(encoding="utf-8").lower()

        for phrase in (
            "backend-only adapter",
            "prepared target a/b context is not comparison output",
            "generated_by",
            "deterministic_engine",
            "allowed_visualizations policy",
            "does not render charts",
            "does not add browser-side comparison computation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertIn("7cx-d introduces a backend-only adapter", contract_text)
        self.assertIn("7cc must not bypass that adapter", execution_text)


if __name__ == "__main__":
    unittest.main()
