"""Phase 7CB tests for deterministic Screen 3 re-analysis execution."""

from __future__ import annotations

import ast
import importlib
import os
import sys
import unittest
import uuid
from pathlib import Path
from typing import Any

from tests.test_phase7ca_governed_workflow_repository import FakeConnection


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
EXECUTION_DOC = DOCS / "phase7cb_deterministic_reanalysis_execution.md"
MODEL_DOC = DOCS / "phase7cb_deterministic_execution_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen3_deterministic_execution.py"

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


class Phase7CBDeterministicExecutionTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen3_deterministic_execution")

    @staticmethod
    def request_module():
        return importlib.import_module("src.learning.screen3_reanalysis_request")

    @staticmethod
    def repository_module():
        return importlib.import_module("src.learning.governed_workflow_repository")

    def make_reanalysis_request(
        self,
        *,
        requested_action: str = "analyze_selection",
        source_mode: str = "existing_run",
    ):
        request_module = self.request_module()
        state = request_module.Screen3SelectedState(
            selected_state_id=request_module.create_selected_state_id(
                selected_run="RUN-7CB-1",
                selected_snapshot="SNAP-7CB-1",
            ),
            selected_run="RUN-7CB-1",
            selected_snapshot="SNAP-7CB-1",
            selected_issue_domain="CPU",
            selected_source_mode=source_mode,
            selected_execution_mode="local_backend_execution",
            selected_existing_run_reference=(
                "RUN-7CB-1" if source_mode == "existing_run" else None
            ),
            selected_local_source_reference=(
                "LOCAL-SOURCE-7CB-1" if source_mode == "local_file" else None
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
            actor_audit_context={"actor_id": "ACTOR-7CB-TESTER"},
            execution_mode="local_backend_execution",
            adaptive_runtime_requested=False,
            deterministic_default=True,
            notes="phase 7cb unit test",
        )

    def make_envelope(
        self,
        *,
        suffix: str = "LOCAL",
        dry_run: bool = True,
        requested_action: str = "analyze_selection",
        source_mode: str = "existing_run",
        actor_id: str = "ACTOR-7CB-TESTER",
        idempotency_key: str | None = None,
        transaction_group_id: str | None = None,
    ):
        module = self.module()
        request = self.make_reanalysis_request(
            requested_action=requested_action,
            source_mode=source_mode,
        )
        idem = f"IDEMP-7CB-{suffix}" if idempotency_key is None else idempotency_key
        tx_id = (
            f"TX-7CB-{suffix}"
            if transaction_group_id is None
            else transaction_group_id
        )
        return module.DeterministicExecutionRequestEnvelope(
            execution_id=module.create_deterministic_execution_id(
                request.request_id,
                idem,
            ),
            reanalysis_request=request,
            actor_id=actor_id,
            actor_audit_context={"actor_id": actor_id},
            idempotency_key=idem,
            transaction_group_id=tx_id,
            source_mode=source_mode,
            requested_action=requested_action,
            deterministic_default=True,
            adaptive_runtime_requested=False,
            dry_run=dry_run,
            validation_reference="VALIDATION-7CB-1",
            rollback_reference=f"ROLLBACK-7CB-{suffix}",
            notes="phase 7cb unit test",
        )

    def repository(self):
        return self.repository_module().GovernedWorkflowRepository(FakeConnection())

    def test_import_safety(self) -> None:
        before_environment = dict(os.environ)
        before_modules = set(sys.modules)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "DeterministicExecutionRequestEnvelope"))
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
            "no subprocess",
            "no direct run_analysis.py call",
            "no adaptive runtime",
            "no object storage",
            "no dashboard regeneration",
            "deterministic runtime remains authoritative",
            "phase 4i is not mutated",
            "phase 8 is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_envelope_validation_requires_actor_idempotency_and_transaction(self) -> None:
        module = self.module()
        envelope = self.make_envelope()
        self.assertIs(module.validate_deterministic_execution_envelope(envelope), envelope)

        with self.assertRaises(module.Screen3DeterministicExecutionError):
            self.make_envelope(actor_id="")
        with self.assertRaises(module.Screen3DeterministicExecutionError):
            self.make_envelope(idempotency_key="")
        with self.assertRaises(module.Screen3DeterministicExecutionError):
            self.make_envelope(transaction_group_id="")
        with self.assertRaises(module.Screen3DeterministicExecutionError):
            module.validate_deterministic_execution_envelope(
                self.make_envelope(source_mode="object_storage")
            )
        with self.assertRaises(module.Screen3DeterministicExecutionError):
            module.DeterministicExecutionRequestEnvelope(
                **{
                    **module.envelope_to_dict(envelope),
                    "adaptive_runtime_requested": True,
                    "reanalysis_request": envelope.reanalysis_request,
                }
            )

    def test_runner_none_produces_blocked_or_dry_run_result(self) -> None:
        module = self.module()
        result = module.execute_deterministic_reanalysis(
            self.make_envelope(dry_run=True),
            self.repository(),
            runner=None,
        )
        self.assertEqual("dry_run_only", result.execution_status)
        self.assertFalse(result.deterministic_execution_performed)
        self.assertFalse(result.runner_invoked)
        self.assertFalse(result.run_analysis_called)
        self.assertFalse(result.subprocess_called)
        self.assertFalse(result.adaptive_runtime_used)
        self.assertFalse(result.object_storage_called)
        self.assertFalse(result.dashboard_regenerated)
        self.assertFalse(result.phase4i_mutated)
        self.assertTrue(result.workflow_request_persisted)
        self.assertTrue(result.workflow_validation_persisted)
        self.assertTrue(result.workflow_audit_persisted)

        blocked = module.execute_deterministic_reanalysis(
            self.make_envelope(suffix="NO-RUNNER", dry_run=False),
            self.repository(),
            runner=None,
        )
        self.assertEqual("blocked_no_runner", blocked.execution_status)
        self.assertFalse(blocked.runner_invoked)

    def test_fake_runner_produces_deterministic_execution_result(self) -> None:
        module = self.module()
        calls: list[str] = []

        def fake_runner(envelope):
            calls.append(envelope.execution_id)
            return {
                "analysis_run_reference": "analysis-run-7cb-fake",
                "phase4i_reference": "phase4i-ref-7cb-fake",
                "dashboard_reference": "dashboard-ref-7cb-fake",
                "artifact_summary": "fake deterministic runner output",
                "warnings": ["fake runner used"],
            }

        result = module.execute_deterministic_reanalysis(
            self.make_envelope(suffix="RUNNER", dry_run=False),
            self.repository(),
            runner=fake_runner,
        )
        self.assertEqual("deterministic_runner_completed", result.execution_status)
        self.assertEqual(1, len(calls))
        self.assertTrue(result.deterministic_execution_performed)
        self.assertTrue(result.runner_invoked)
        self.assertTrue(result.output_artifacts_persisted)
        self.assertTrue(all(reference.persisted for reference in result.output_references))
        self.assertEqual(
            {
                "analysis_run_record",
                "phase4i_payload_reference",
                "dashboard_artifact_reference",
            },
            {reference.artifact_type for reference in result.output_references},
        )
        self.assertFalse(result.run_analysis_called)
        self.assertFalse(result.subprocess_called)
        self.assertFalse(result.adaptive_runtime_used)
        self.assertFalse(result.object_storage_called)
        self.assertFalse(result.dashboard_regenerated)
        self.assertFalse(result.phase4i_mutated)

    def test_output_reference_and_result_serialize_round_trip(self) -> None:
        module = self.module()
        reference = module.DeterministicExecutionOutputReference(
            output_reference_id="OUTPUT-7CB-1",
            artifact_type="phase4i_payload_reference",
            artifact_reference="phase4i-ref",
            artifact_summary="metadata reference",
            phase4i_reference="phase4i-ref",
            persisted=True,
        )
        self.assertEqual(
            reference,
            module.output_reference_from_dict(module.output_reference_to_dict(reference)),
        )

        result = module.DeterministicExecutionResult(
            execution_id="EXEC-7CB-1",
            request_id="REQ-7CB-1",
            idempotency_key="IDEMP-7CB-ROUNDTRIP",
            transaction_group_id="TX-7CB-ROUNDTRIP",
            execution_status="deterministic_runner_completed",
            deterministic_execution_performed=True,
            runner_invoked=True,
            run_analysis_called=False,
            subprocess_called=False,
            adaptive_runtime_used=False,
            object_storage_called=False,
            dashboard_regenerated=False,
            phase4i_mutated=False,
            workflow_request_persisted=True,
            workflow_validation_persisted=True,
            workflow_audit_persisted=True,
            output_artifacts_persisted=True,
            output_references=(reference,),
            warnings=["ok"],
            required_next_steps=["review"],
        )
        self.assertEqual(
            result,
            module.deterministic_execution_result_from_dict(
                module.deterministic_execution_result_to_dict(result)
            ),
        )

    def test_idempotent_replay_with_fake_repository(self) -> None:
        module = self.module()
        repository_module = self.repository_module()
        connection = FakeConnection()
        repository = repository_module.GovernedWorkflowRepository(connection)
        envelope = self.make_envelope(suffix="IDEMPOTENT", dry_run=False)
        calls = 0

        def fake_runner(_envelope):
            nonlocal calls
            calls += 1
            return {"analysis_run_reference": "analysis-run-idempotent"}

        first = module.execute_deterministic_reanalysis(
            envelope,
            repository,
            runner=fake_runner,
        )
        second = module.execute_deterministic_reanalysis(
            envelope,
            repository,
            runner=fake_runner,
        )
        self.assertEqual("deterministic_runner_completed", first.execution_status)
        self.assertEqual("idempotent_replay", second.execution_status)
        self.assertEqual(1, calls)
        self.assertEqual(1, len(connection.requests))

    def test_repository_integration_with_fake_connection(self) -> None:
        module = self.module()
        repository_module = self.repository_module()
        connection = FakeConnection()
        repository = repository_module.GovernedWorkflowRepository(connection)
        result = module.execute_deterministic_reanalysis(
            self.make_envelope(suffix="REPO", dry_run=False),
            repository,
            runner=lambda _envelope: {
                "analysis_run_reference": "analysis-run-repo",
                "phase4i_reference": "phase4i-repo",
            },
        )
        self.assertTrue(result.workflow_request_persisted)
        self.assertTrue(result.workflow_validation_persisted)
        self.assertTrue(result.workflow_audit_persisted)
        self.assertTrue(result.output_artifacts_persisted)
        self.assertEqual(1, len(connection.requests))
        self.assertEqual(1, len(connection.audits))
        self.assertGreaterEqual(len(connection.outputs), 2)

    def test_runner_safety_flags_are_enforced(self) -> None:
        module = self.module()
        for field_name in (
            "run_analysis_called",
            "subprocess_called",
            "adaptive_runtime_used",
            "object_storage_called",
            "dashboard_regenerated",
            "phase4i_mutated",
        ):
            with self.subTest(field_name=field_name):
                result = module.execute_deterministic_reanalysis(
                    self.make_envelope(suffix=field_name.upper(), dry_run=False),
                    self.repository(),
                    runner=lambda _envelope, name=field_name: {name: True},
                )
                self.assertEqual("failed_safely", result.execution_status)
                self.assertFalse(result.deterministic_execution_performed)
                self.assertFalse(result.run_analysis_called)
                self.assertFalse(result.subprocess_called)
                self.assertFalse(result.adaptive_runtime_used)
                self.assertFalse(result.object_storage_called)
                self.assertFalse(result.dashboard_regenerated)
                self.assertFalse(result.phase4i_mutated)

    def test_optional_db_backed_deterministic_execution(self) -> None:
        if os.getenv("AWR_PHASE7CB_DB_TEST") != "1":
            self.skipTest("set AWR_PHASE7CB_DB_TEST=1 to run DB-backed Phase 7CB validation")

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
            envelope = self.make_envelope(suffix=f"DB-{suffix}", dry_run=False)
            result = module.execute_deterministic_reanalysis(
                envelope,
                repository,
                runner=lambda _envelope: {
                    "analysis_run_reference": f"analysis-run-db-{suffix}",
                    "phase4i_reference": f"phase4i-db-{suffix}",
                    "dashboard_reference": f"dashboard-db-{suffix}",
                },
            )
            replay = module.execute_deterministic_reanalysis(
                envelope,
                repository,
                runner=lambda _envelope: {"analysis_run_reference": "should-not-run"},
            )
            self.assertEqual("deterministic_runner_completed", result.execution_status)
            self.assertEqual("idempotent_replay", replay.execution_status)
            self.assertTrue(result.workflow_request_persisted)
            self.assertTrue(result.output_artifacts_persisted)
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
