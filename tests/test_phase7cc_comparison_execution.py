"""Phase 7CC tests for active Screen 3 AWR/report comparison execution."""

from __future__ import annotations

import ast
import importlib
import os
import sys
import unittest
import uuid
from pathlib import Path

from tests.test_phase7ca_governed_workflow_repository import FakeConnection


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
EXECUTION_DOC = DOCS / "phase7cc_comparison_execution.md"
MODEL_DOC = DOCS / "phase7cc_comparison_execution_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen3_comparison_execution.py"

FORBIDDEN_IMPORT_PREFIXES = (
    "subprocess",
    "requests",
    "httpx",
    "urllib",
    "socket",
    "http.client",
    "oci",
    "oracledb",
    "cx_Oracle",
    "sqlite3",
    "src.reporting",
    "src.parser",
    "src.parsing",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.analysis",
    "src.memory",
    "scripts.run_analysis",
    "scripts.awr_memory_cli",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


class Phase7CCComparisonExecutionTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen3_comparison_execution")

    @staticmethod
    def request_module():
        return importlib.import_module("src.learning.screen3_reanalysis_request")

    @staticmethod
    def repository_module():
        return importlib.import_module("src.learning.governed_workflow_repository")

    def make_reanalysis_request(
        self,
        *,
        requested_action: str = "build_comparison",
        source_mode: str = "existing_run",
    ):
        request_module = self.request_module()
        state = request_module.Screen3SelectedState(
            selected_state_id=request_module.create_selected_state_id(
                selected_run="RUN-7CC-BASE",
                selected_snapshot="SNAP-7CC-BASE",
            ),
            selected_run="RUN-7CC-BASE",
            selected_snapshot="SNAP-7CC-BASE",
            selected_comparison_baseline="RUN-7CC-BASE",
            selected_issue_domain="CPU",
            selected_source_mode=source_mode,
            selected_execution_mode="local_backend_execution",
            selected_existing_run_reference=(
                "RUN-7CC-BASE" if source_mode == "existing_run" else None
            ),
            selected_object_storage_reference=(
                "OBJECT-STORAGE-7CC" if source_mode == "object_storage" else None
            ),
        )
        return request_module.BackendReAnalysisRequest(
            request_id=request_module.create_reanalysis_request_id(
                requested_action,
                state.selected_state_id,
                "local_backend_execution",
            ),
            requested_action=requested_action,
            selected_state=state,
            source_selection={"validation_status": "VALID_METADATA_ONLY"},
            backend_execution_request={"validation_status": "VALID_METADATA_ONLY"},
            actor_audit_context={"actor_id": "ACTOR-7CC-TESTER"},
            execution_mode="local_backend_execution",
            adaptive_runtime_requested=False,
            deterministic_default=True,
            notes="phase 7cc unit test",
        )

    def make_inputs(self) -> list[dict[str, object]]:
        return [
            {
                "comparison_input_status": "already_loaded",
                "run_id": "RUN-7CC-BASE",
                "awr_id": "AWR-7CC-BASE",
                "dbid": "101",
                "database_name": "BASEDB",
                "snapshot_label": "baseline",
                "scores": {"overall": 82, "cpu": 70},
                "domain_scores": {"io": 64},
                "waits": {"db file sequential read": 110, "log file sync": 12},
                "wait_events": {"CPU": 240},
                "sql_concentration": {"top_sql_elapsed_pct": 41},
                "top_sql_concentration": {"top_sql_count": 8},
                "trends": {"cpu": "stable", "io": "improving"},
                "anomalies": {"cpu_spike": False, "io_spike": False},
                "topology": {"instances": 1, "rac": False},
                "platform_target": {"target": "ExaDB-D"},
                "target_platform": "ExaDB-D",
                "source_options": {"partitioning": "disabled"},
                "data_availability": {"ash": True, "sqlstats": True},
                "missing_metrics": [],
            },
            {
                "comparison_input_status": "comparison_ready",
                "run_id": "RUN-7CC-TARGET",
                "awr_id": "AWR-7CC-TARGET",
                "dbid": "101",
                "database_name": "BASEDB",
                "snapshot_label": "target",
                "scores": {"overall": 76, "cpu": 58},
                "waits": {"db file sequential read": 145, "log file sync": 18},
                "wait_events": {"CPU": 310},
                "sql_concentration": {"top_sql_elapsed_pct": 56},
                "top_sql_concentration": {"top_sql_count": 14},
                "trends": {"cpu": "rising", "io": "flat"},
                "anomalies": {"cpu_spike": True, "io_spike": False},
                "topology": {"instances": 2, "rac": True},
                "platform_target": {"target": "ADB-D"},
                "target_platform": "ADB-D",
                "source_options": {"partitioning": "enabled"},
                "data_availability": {"ash": False},
                "missing_metrics": ["sqlstats"],
            },
        ]

    def make_envelope(
        self,
        *,
        suffix: str = "LOCAL",
        requested_action: str = "build_comparison",
        source_mode: str = "existing_run",
        actor_id: str = "ACTOR-7CC-TESTER",
        idempotency_key: str | None = None,
        transaction_group_id: str | None = None,
        comparison_inputs: list[dict[str, object]] | None = None,
    ):
        module = self.module()
        request = self.make_reanalysis_request(
            requested_action=requested_action,
            source_mode=source_mode,
        )
        idem = f"IDEMP-7CC-{suffix}" if idempotency_key is None else idempotency_key
        tx_id = (
            f"TX-7CC-{suffix}"
            if transaction_group_id is None
            else transaction_group_id
        )
        return module.ComparisonExecutionRequestEnvelope(
            comparison_execution_id=module.create_comparison_execution_id(
                request.request_id,
                idem,
            ),
            reanalysis_request=request,
            actor_id=actor_id,
            actor_audit_context={"actor_id": actor_id},
            idempotency_key=idem,
            transaction_group_id=tx_id,
            comparison_name="Phase 7CC comparison",
            comparison_inputs=(
                self.make_inputs() if comparison_inputs is None else comparison_inputs
            ),
            baseline_reference="RUN-7CC-BASE",
            requested_action=requested_action,
            source_mode=source_mode,
            deterministic_default=True,
            adaptive_runtime_requested=False,
            dry_run=False,
            validation_reference="VALIDATION-7CC-1",
            rollback_reference=f"ROLLBACK-7CC-{suffix}",
            notes="phase 7cc unit test",
        )

    def repository(self):
        return self.repository_module().GovernedWorkflowRepository(FakeConnection())

    def test_import_safety(self) -> None:
        before_environment = dict(os.environ)
        before_modules = set(sys.modules)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "ComparisonExecutionRequestEnvelope"))
        self.assertNotIn("scripts.run_analysis", set(sys.modules) - before_modules)

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_docs_exist_and_contain_boundary_phrases(self) -> None:
        self.assertTrue(EXECUTION_DOC.is_file(), EXECUTION_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        text = lower_text(EXECUTION_DOC) + "\n" + lower_text(MODEL_DOC)
        for phrase in (
            "comparison uses supplied in-memory payloads only",
            "no awr files are read",
            "no parser is called",
            "no db report lookup occurs",
            "no object storage call occurs",
            "no run_analysis.py call occurs",
            "no dashboard regeneration occurs",
            "no phase 4i mutation occurs",
            "phase 8 sizing/tco comparison remains future",
            "staged_needs_load",
            "missing_structured_payload",
            "already_loaded",
            "do not implement load-and-compare",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_envelope_validation_requires_governed_metadata(self) -> None:
        module = self.module()
        envelope = self.make_envelope()
        self.assertIs(module.validate_comparison_execution_envelope(envelope), envelope)

        with self.assertRaises(module.Screen3ComparisonExecutionError):
            self.make_envelope(actor_id="")
        with self.assertRaises(module.Screen3ComparisonExecutionError):
            self.make_envelope(idempotency_key="")
        with self.assertRaises(module.Screen3ComparisonExecutionError):
            self.make_envelope(transaction_group_id="")
        with self.assertRaises(module.Screen3ComparisonExecutionError):
            module.validate_comparison_execution_envelope(
                self.make_envelope(requested_action="analyze_selection")
            )
        with self.assertRaises(module.Screen3ComparisonExecutionError):
            module.validate_comparison_execution_envelope(
                self.make_envelope(source_mode="object_storage")
            )
        with self.assertRaises(module.Screen3ComparisonExecutionError):
            module.ComparisonExecutionRequestEnvelope(
                **{
                    **module.comparison_execution_envelope_to_dict(envelope),
                    "adaptive_runtime_requested": True,
                    "reanalysis_request": envelope.reanalysis_request,
                }
            )

    def test_insufficient_comparison_inputs_blocked(self) -> None:
        module = self.module()
        result = module.execute_awr_report_comparison(
            self.make_envelope(
                suffix="INSUFFICIENT",
                comparison_inputs=[self.make_inputs()[0]],
            ),
            repository=None,
        )
        self.assertEqual("blocked_insufficient_inputs", result.execution_status)
        self.assertFalse(result.comparison_built)
        self.assertFalse(result.workflow_request_persisted)

    def test_staged_only_input_blocks_comparison_without_runtime_work(self) -> None:
        module = self.module()
        inputs = [
            self.make_inputs()[0],
            {
                "comparison_input_status": "staged_needs_load",
                "run_id": "RUN-7CC-STAGED",
                "awr_id": "AWR-7CC-STAGED",
                "staged_only": True,
                "staged_file_reference": "staged/awr-7cc-staged.html",
            },
        ]
        result = module.execute_awr_report_comparison(
            self.make_envelope(suffix="STAGED", comparison_inputs=inputs),
            repository=None,
        )
        self.assertEqual("blocked_invalid_request", result.execution_status)
        self.assertFalse(result.comparison_built)
        self.assertIn(
            "Selected AWR is staged but not loaded; run deterministic load/re-analysis before comparison.",
            result.denied_reasons,
        )
        self.assert_blocked_safety_flags(result)

    def test_missing_structured_payload_blocks_comparison(self) -> None:
        module = self.module()
        inputs = [
            self.make_inputs()[0],
            {
                "comparison_input_status": "already_loaded",
                "run_id": "RUN-7CC-NO-PAYLOAD",
                "awr_id": "AWR-7CC-NO-PAYLOAD",
            },
        ]
        result = module.execute_awr_report_comparison(
            self.make_envelope(suffix="MISSING-PAYLOAD", comparison_inputs=inputs),
            repository=None,
        )
        self.assertEqual("blocked_invalid_request", result.execution_status)
        self.assertFalse(result.comparison_built)
        self.assertIn(
            "Selected AWR lacks a structured comparison-ready payload; run deterministic load/re-analysis before comparison.",
            result.denied_reasons,
        )
        self.assert_blocked_safety_flags(result)

    def test_already_loaded_structured_payload_can_compare(self) -> None:
        module = self.module()
        base, target = self.make_inputs()
        inputs = [
            {
                "comparison_input_status": "already_loaded",
                "structured_payload": base,
            },
            {
                "comparison_input_status": "comparison_ready",
                "structured_payload": target,
            },
        ]
        result = module.execute_awr_report_comparison(
            self.make_envelope(suffix="LOADED-STRUCTURED", comparison_inputs=inputs),
            repository=None,
        )
        self.assertEqual("comparison_built_in_memory", result.execution_status)
        self.assertTrue(result.comparison_built)
        self.assertIsNotNone(result.comparison_artifact)
        self.assertTrue(result.comparison_artifact.score_differences)

    def test_valid_comparison_builds_in_memory_without_persistence(self) -> None:
        module = self.module()
        result = module.execute_awr_report_comparison(
            self.make_envelope(suffix="MEMORY"),
            repository=None,
        )
        self.assertEqual("comparison_built_in_memory", result.execution_status)
        self.assertTrue(result.comparison_built)
        self.assertIsNotNone(result.comparison_artifact)
        self.assertFalse(result.workflow_request_persisted)
        self.assertFalse(result.output_artifacts_persisted)
        self.assertTrue(result.output_references)
        self.assertFalse(result.output_references[0].persisted)

    def test_comparison_includes_expected_difference_categories(self) -> None:
        module = self.module()
        result = module.execute_awr_report_comparison(
            self.make_envelope(suffix="DIFFS"),
            repository=None,
        )
        artifact = result.comparison_artifact
        self.assertIsNotNone(artifact)
        self.assertTrue(artifact.score_differences)
        self.assertTrue(artifact.wait_event_differences)
        self.assertTrue(artifact.sql_concentration_differences)
        self.assertTrue(artifact.trend_differences)
        self.assertTrue(artifact.anomaly_differences)
        self.assertTrue(artifact.topology_differences)
        self.assertTrue(artifact.platform_target_differences)
        self.assertTrue(artifact.data_availability_differences)
        self.assertTrue(artifact.data_availability_differences["missing_values"])
        self.assertTrue(artifact.comparison_limitations)

    def test_repository_integration_persists_metadata_flags(self) -> None:
        module = self.module()
        repository_module = self.repository_module()
        connection = FakeConnection()
        repository = repository_module.GovernedWorkflowRepository(connection)
        result = module.execute_awr_report_comparison(
            self.make_envelope(suffix="REPO"),
            repository=repository,
        )
        self.assertEqual("comparison_persisted_metadata", result.execution_status)
        self.assertTrue(result.workflow_request_persisted)
        self.assertTrue(result.workflow_validation_persisted)
        self.assertTrue(result.workflow_audit_persisted)
        self.assertTrue(result.output_artifacts_persisted)
        self.assertTrue(all(reference.persisted for reference in result.output_references))
        self.assertEqual(1, len(connection.requests))
        self.assertEqual(1, len(connection.audits))
        self.assertEqual(1, len(connection.outputs))
        self.assertEqual({"comparison_artifact"}, {row["ARTIFACT_TYPE"] for row in connection.outputs.values()})

    def test_idempotent_replay_with_repository(self) -> None:
        module = self.module()
        repository_module = self.repository_module()
        connection = FakeConnection()
        repository = repository_module.GovernedWorkflowRepository(connection)
        envelope = self.make_envelope(suffix="IDEMPOTENT")

        first = module.execute_awr_report_comparison(envelope, repository=repository)
        second = module.execute_awr_report_comparison(envelope, repository=repository)
        self.assertEqual("comparison_persisted_metadata", first.execution_status)
        self.assertEqual("idempotent_replay", second.execution_status)
        self.assertTrue(second.idempotent_replay)
        self.assertFalse(second.comparison_built)
        self.assertEqual(1, len(connection.requests))
        self.assertEqual(1, len(connection.outputs))

    def test_safety_flags_remain_false_and_are_enforced(self) -> None:
        module = self.module()
        result = module.execute_awr_report_comparison(
            self.make_envelope(suffix="SAFETY"),
            repository=None,
        )
        self.assertFalse(result.run_analysis_called)
        self.assertFalse(result.subprocess_called)
        self.assertFalse(result.object_storage_called)
        self.assertFalse(result.local_file_read_performed)
        self.assertFalse(result.parser_called)
        self.assertFalse(result.db_lookup_performed)
        self.assertFalse(result.dashboard_regenerated)
        self.assertFalse(result.phase4i_mutated)
        self.assertFalse(result.adaptive_runtime_used)
        self.assertFalse(result.phase8_sizing_tco_used)

        base = module.comparison_execution_result_to_dict(result)
        for field_name in (
            "run_analysis_called",
            "subprocess_called",
            "object_storage_called",
            "local_file_read_performed",
            "parser_called",
            "db_lookup_performed",
            "dashboard_regenerated",
            "phase4i_mutated",
            "adaptive_runtime_used",
            "phase8_sizing_tco_used",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(module.Screen3ComparisonExecutionError):
                    module.comparison_execution_result_from_dict(
                        {**base, field_name: True}
                    )

    def test_serialization_round_trips(self) -> None:
        module = self.module()
        result = module.execute_awr_report_comparison(
            self.make_envelope(suffix="ROUNDTRIP"),
            repository=None,
        )
        reference = result.output_references[0]
        self.assertEqual(
            reference,
            module.comparison_output_reference_from_dict(
                module.comparison_output_reference_to_dict(reference)
            ),
        )
        self.assertEqual(
            result,
            module.comparison_execution_result_from_dict(
                module.comparison_execution_result_to_dict(result)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        self.assertEqual(
            module.create_comparison_execution_id("REQ-7CC", "IDEMP-7CC"),
            module.create_comparison_execution_id("REQ-7CC", "IDEMP-7CC"),
        )
        self.assertNotEqual(
            module.create_comparison_execution_id("REQ-7CC", "IDEMP-7CC"),
            module.create_comparison_execution_id("REQ-7CC", "IDEMP-OTHER"),
        )

    def test_optional_db_backed_comparison_execution(self) -> None:
        if os.getenv("AWR_PHASE7CC_DB_TEST") != "1":
            self.skipTest("set AWR_PHASE7CC_DB_TEST=1 to run DB-backed Phase 7CC validation")

        try:
            from src.ingest.awr_adb_loader import get_db_connection
            from tests.test_phase7ca_governed_workflow_repository import _apply_schema
        except Exception as exc:  # noqa: BLE001
            self.skipTest(f"project DB connector unavailable: {type(exc).__name__}: {exc}")

        try:
            connection = get_db_connection()
        except Exception as exc:  # noqa: BLE001
            self.skipTest(f"ADB connection unavailable: {type(exc).__name__}: {exc}")

        try:
            _apply_schema(connection)
            repository = self.repository_module().GovernedWorkflowRepository(connection)
            module = self.module()
            suffix = uuid.uuid4().hex[:12].upper()
            envelope = self.make_envelope(suffix=f"DB-{suffix}")
            result = module.execute_awr_report_comparison(envelope, repository=repository)
            replay = module.execute_awr_report_comparison(envelope, repository=repository)
            self.assertEqual("comparison_persisted_metadata", result.execution_status)
            self.assertEqual("idempotent_replay", replay.execution_status)
            self.assertTrue(result.workflow_request_persisted)
            self.assertTrue(result.output_artifacts_persisted)
        finally:
            connection.close()

    def assert_blocked_safety_flags(self, result) -> None:
        self.assertFalse(result.run_analysis_called)
        self.assertFalse(result.subprocess_called)
        self.assertFalse(result.object_storage_called)
        self.assertFalse(result.local_file_read_performed)
        self.assertFalse(result.parser_called)
        self.assertFalse(result.db_lookup_performed)
        self.assertFalse(result.dashboard_regenerated)
        self.assertFalse(result.phase4i_mutated)
        self.assertFalse(result.adaptive_runtime_used)
        self.assertFalse(result.phase8_sizing_tco_used)


if __name__ == "__main__":
    unittest.main()
