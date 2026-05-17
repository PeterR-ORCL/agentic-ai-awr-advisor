"""Phase 7CA repository tests for governed workflow persistence."""

from __future__ import annotations

import ast
import importlib
import os
import sys
import unittest
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "learning" / "governed_workflow_repository.py"
SCHEMA_PATH = ROOT / "dbschema" / "phase7ca_governed_workflow_persistence.sql"

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

REQUIRED_METHODS = (
    "persist_workflow_request",
    "persist_workflow_validation",
    "persist_workflow_audit",
    "persist_output_artifact",
    "get_workflow_request",
    "get_by_idempotency_key",
    "validate_idempotency_key",
    "create_workflow_transaction",
    "record_workflow_failure",
    "persist_workflow_bundle",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self._result: tuple[Any, ...] | None = None

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def execute(self, statement: str, parameters: dict[str, Any] | None = None) -> None:
        self.connection.calls.append((statement, parameters))
        if parameters is None:
            raise AssertionError("repository SQL must use parameter dictionaries")
        normalized = " ".join(statement.upper().split())
        self._result = None

        if normalized.startswith("SELECT") and "FROM AWR_WORKFLOW_REQUEST" in normalized:
            if "WHERE IDEMPOTENCY_KEY" in normalized:
                row = self.connection.requests_by_idempotency.get(parameters["idempotency_key"])
            else:
                row = self.connection.requests.get(parameters["workflow_request_id"])
            self._result = self.connection.request_tuple(row)
            return

        if normalized.startswith("SELECT") and "FROM AWR_WORKFLOW_TRANSACTION" in normalized:
            if "WHERE IDEMPOTENCY_KEY" in normalized:
                row = self.connection.transactions_by_idempotency.get(
                    parameters["idempotency_key"]
                )
            else:
                row = self.connection.transactions.get(parameters["transaction_group_id"])
            self._result = self.connection.transaction_tuple(row)
            return

        if normalized.startswith("SELECT") and "FROM AWR_WORKFLOW_VALIDATION" in normalized:
            row = self.connection.validations.get(parameters["workflow_validation_id"])
            self._result = self.connection.validation_tuple(row)
            return

        if normalized.startswith("SELECT") and "FROM AWR_WORKFLOW_AUDIT" in normalized:
            row = self.connection.audits.get(parameters["workflow_audit_id"])
            self._result = self.connection.audit_tuple(row)
            return

        if normalized.startswith("SELECT") and "FROM AWR_WORKFLOW_OUTPUT_ARTIFACT" in normalized:
            row = self.connection.outputs.get(parameters["workflow_output_id"])
            self._result = self.connection.output_tuple(row)
            return

        if normalized.startswith("INSERT INTO AWR_WORKFLOW_TRANSACTION"):
            row = {
                "TRANSACTION_GROUP_ID": parameters["transaction_group_id"],
                "IDEMPOTENCY_KEY": parameters["idempotency_key"],
                "TRANSACTION_SCOPE": parameters["transaction_scope"],
                "STATUS": parameters["status"],
                "ROLLBACK_REFERENCE": parameters["rollback_reference"],
                "CREATED_AT": "created",
                "UPDATED_AT": "updated",
                "NOTES": parameters["notes"],
            }
            self.connection.transactions[row["TRANSACTION_GROUP_ID"]] = row
            self.connection.transactions_by_idempotency[row["IDEMPOTENCY_KEY"]] = row
            return

        if normalized.startswith("INSERT INTO AWR_WORKFLOW_REQUEST"):
            row = {
                "WORKFLOW_REQUEST_ID": parameters["workflow_request_id"],
                "TRANSACTION_GROUP_ID": parameters["transaction_group_id"],
                "IDEMPOTENCY_KEY": parameters["idempotency_key"],
                "SOURCE_SCREEN": parameters["source_screen"],
                "WORKFLOW_TYPE": parameters["workflow_type"],
                "REQUESTED_ACTION": parameters["requested_action"],
                "TARGET_TYPE": parameters["target_type"],
                "TARGET_ID": parameters["target_id"],
                "ACTOR_ID": parameters["actor_id"],
                "PAYLOAD_CLOB": parameters["payload_clob"],
                "STATUS": parameters["status"],
                "CREATED_AT": "created",
                "UPDATED_AT": "updated",
                "ERROR_CLOB": parameters["error_clob"],
                "WARNING_CLOB": parameters["warning_clob"],
                "NOTES": parameters["notes"],
            }
            self.connection.requests[row["WORKFLOW_REQUEST_ID"]] = row
            self.connection.requests_by_idempotency[row["IDEMPOTENCY_KEY"]] = row
            return

        if normalized.startswith("INSERT INTO AWR_WORKFLOW_VALIDATION"):
            row = {
                "WORKFLOW_VALIDATION_ID": parameters["workflow_validation_id"],
                "WORKFLOW_REQUEST_ID": parameters["workflow_request_id"],
                "VALIDATION_STATUS": parameters["validation_status"],
                "VALID_FLAG": parameters["valid_flag"],
                "DENIED_REASONS_CLOB": parameters["denied_reasons_clob"],
                "WARNINGS_CLOB": parameters["warnings_clob"],
                "REQUIRED_NEXT_STEPS_CLOB": parameters["required_next_steps_clob"],
                "CREATED_AT": "created",
                "NOTES": parameters["notes"],
            }
            self.connection.validations[row["WORKFLOW_VALIDATION_ID"]] = row
            return

        if normalized.startswith("INSERT INTO AWR_WORKFLOW_AUDIT"):
            row = {
                "WORKFLOW_AUDIT_ID": parameters["workflow_audit_id"],
                "WORKFLOW_REQUEST_ID": parameters["workflow_request_id"],
                "TRANSACTION_GROUP_ID": parameters["transaction_group_id"],
                "ACTOR_ID": parameters["actor_id"],
                "ACTION": parameters["action"],
                "AUDIT_SUMMARY": parameters["audit_summary"],
                "PAYLOAD_HASH": parameters["payload_hash"],
                "CREATED_AT": "created",
                "NOTES": parameters["notes"],
            }
            self.connection.audits[row["WORKFLOW_AUDIT_ID"]] = row
            return

        if normalized.startswith("INSERT INTO AWR_WORKFLOW_OUTPUT_ARTIFACT"):
            row = {
                "WORKFLOW_OUTPUT_ID": parameters["workflow_output_id"],
                "WORKFLOW_REQUEST_ID": parameters["workflow_request_id"],
                "ARTIFACT_TYPE": parameters["artifact_type"],
                "ARTIFACT_REFERENCE": parameters["artifact_reference"],
                "ARTIFACT_SUMMARY": parameters["artifact_summary"],
                "ARTIFACT_METADATA_CLOB": parameters["artifact_metadata_clob"],
                "STATUS": parameters["status"],
                "CREATED_AT": "created",
                "NOTES": parameters["notes"],
            }
            self.connection.outputs[row["WORKFLOW_OUTPUT_ID"]] = row
            return

        if normalized.startswith("UPDATE AWR_WORKFLOW_TRANSACTION"):
            row = self.connection.transactions[parameters["transaction_group_id"]]
            row["STATUS"] = parameters["status"]
            row["NOTES"] = parameters["notes"]
            return

        if normalized.startswith("UPDATE AWR_WORKFLOW_REQUEST"):
            row = self.connection.requests[parameters["workflow_request_id"]]
            row["STATUS"] = "FAILED"
            row["ERROR_CLOB"] = parameters["error_clob"]
            row["NOTES"] = parameters["notes"]
            return

        raise AssertionError(f"unexpected SQL: {statement}")

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._result


class FakeConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any] | None]] = []
        self.commits = 0
        self.rollbacks = 0
        self.transactions: dict[str, dict[str, Any]] = {}
        self.transactions_by_idempotency: dict[str, dict[str, Any]] = {}
        self.requests: dict[str, dict[str, Any]] = {}
        self.requests_by_idempotency: dict[str, dict[str, Any]] = {}
        self.validations: dict[str, dict[str, Any]] = {}
        self.audits: dict[str, dict[str, Any]] = {}
        self.outputs: dict[str, dict[str, Any]] = {}

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    @staticmethod
    def request_tuple(row: dict[str, Any] | None) -> tuple[Any, ...] | None:
        if row is None:
            return None
        module = importlib.import_module("src.learning.governed_workflow_repository")
        return tuple(row[column] for column in module.WORKFLOW_REQUEST_COLUMNS)

    @staticmethod
    def transaction_tuple(row: dict[str, Any] | None) -> tuple[Any, ...] | None:
        if row is None:
            return None
        module = importlib.import_module("src.learning.governed_workflow_repository")
        return tuple(row[column] for column in module.WORKFLOW_TRANSACTION_COLUMNS)

    @staticmethod
    def validation_tuple(row: dict[str, Any] | None) -> tuple[Any, ...] | None:
        if row is None:
            return None
        return (
            row["WORKFLOW_VALIDATION_ID"],
            row["WORKFLOW_REQUEST_ID"],
            row["VALIDATION_STATUS"],
            row["VALID_FLAG"],
            row["DENIED_REASONS_CLOB"],
            row["WARNINGS_CLOB"],
            row["REQUIRED_NEXT_STEPS_CLOB"],
            row["CREATED_AT"],
            row["NOTES"],
        )

    @staticmethod
    def audit_tuple(row: dict[str, Any] | None) -> tuple[Any, ...] | None:
        if row is None:
            return None
        module = importlib.import_module("src.learning.governed_workflow_repository")
        return tuple(row[column] for column in module.WORKFLOW_AUDIT_COLUMNS)

    @staticmethod
    def output_tuple(row: dict[str, Any] | None) -> tuple[Any, ...] | None:
        if row is None:
            return None
        module = importlib.import_module("src.learning.governed_workflow_repository")
        return tuple(row[column] for column in module.WORKFLOW_OUTPUT_COLUMNS)


class Phase7CAGovernedWorkflowRepositoryTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.governed_workflow_repository")

    def make_records(self, suffix: str = "LOCAL"):
        module = self.module()
        idempotency_key = f"IDEMP-7CA-{suffix}"
        request_id = module.create_workflow_request_id(
            "screen3_reanalysis_request",
            idempotency_key,
        )
        transaction_group_id = module.create_transaction_group_id(
            idempotency_key,
            "workflow_execution",
        )
        request = module.PersistedWorkflowRequest(
            workflow_request_id=request_id,
            transaction_group_id=transaction_group_id,
            idempotency_key=idempotency_key,
            source_screen="screen_3",
            workflow_type="screen3_reanalysis_request",
            requested_action="submit_reanalysis",
            target_type="analysis_run",
            target_id="RUN-LOCAL-001",
            actor_id="ACTOR-LOCAL-TESTER",
            payload={
                "source_mode": "existing_run",
                "rollback_reference": f"ROLLBACK-7CA-{suffix}",
            },
            notes="test metadata only",
        )
        transaction = module.PersistedWorkflowTransaction(
            transaction_group_id=transaction_group_id,
            idempotency_key=idempotency_key,
            transaction_scope="workflow_execution",
            rollback_reference=f"ROLLBACK-7CA-{suffix}",
            status="IN_PROGRESS",
            notes="test transaction metadata",
        )
        validation = module.PersistedWorkflowValidation(
            workflow_validation_id=module.create_workflow_validation_id(request_id),
            workflow_request_id=request_id,
            validation_status="valid_metadata_only",
            valid_flag=True,
            warnings=["metadata persistence only"],
            required_next_steps=["future 7CB may execute analysis"],
        )
        artifact = module.PersistedWorkflowOutputArtifact(
            workflow_output_id=module.create_workflow_output_id(
                request_id,
                "analysis_run_record",
                "analysis-run-reference-local",
            ),
            workflow_request_id=request_id,
            artifact_type="analysis_run_record",
            artifact_reference="analysis-run-reference-local",
            artifact_summary="analysis run metadata reference only",
            artifact_metadata={"generated": False},
        )
        return request, transaction, validation, artifact

    def test_repository_imports_safely_without_db_connection(self) -> None:
        before_environment = dict(os.environ)
        before_modules = set(sys.modules)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "GovernedWorkflowRepository"))
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

    def test_repository_requires_injected_connection(self) -> None:
        module = self.module()
        with self.assertRaises(module.GovernedWorkflowRepositoryError):
            module.GovernedWorkflowRepository(None)
        with self.assertRaises(module.GovernedWorkflowRepositoryError):
            module.GovernedWorkflowRepository(object())
        self.assertIsNotNone(module.GovernedWorkflowRepository(FakeConnection()))

    def test_required_public_methods_exist(self) -> None:
        module = self.module()
        for method_name in REQUIRED_METHODS:
            with self.subTest(method_name=method_name):
                self.assertTrue(hasattr(module.GovernedWorkflowRepository, method_name))
        self.assertTrue(hasattr(module, "AnalysisExecutionRecord"))
        self.assertTrue(hasattr(module, "WorkflowPersistenceResult"))

    def test_parameterized_sql_and_idempotent_bundle_persistence(self) -> None:
        module = self.module()
        connection = FakeConnection()
        repository = module.GovernedWorkflowRepository(connection)
        request, transaction, validation, artifact = self.make_records()

        result = repository.persist_workflow_bundle(
            request=request,
            transaction=transaction,
            validation=validation,
            output_artifacts=(artifact,),
        )
        self.assertFalse(result.duplicate)
        self.assertEqual("PERSISTED", result.status)
        self.assertEqual(1, len(connection.requests))
        self.assertEqual(1, len(connection.audits))
        self.assertEqual(1, len(connection.outputs))
        self.assertEqual(1, connection.commits)

        replay = repository.persist_workflow_bundle(
            request=request,
            transaction=transaction,
            validation=validation,
            output_artifacts=(artifact,),
        )
        self.assertTrue(replay.duplicate)
        self.assertEqual("DUPLICATE_REPLAY", replay.status)
        self.assertEqual(request.workflow_request_id, replay.workflow_request_id)
        self.assertEqual(1, len(connection.requests))
        self.assertEqual(1, len(connection.audits))

        for statement, parameters in connection.calls:
            with self.subTest(statement=statement.splitlines()[0].strip()):
                self.assertIsInstance(parameters, dict)
                if statement.lstrip().lower().startswith(("select", "insert", "update")):
                    self.assertIn(":", statement)

    def test_lookup_and_failure_recording_methods(self) -> None:
        module = self.module()
        connection = FakeConnection()
        repository = module.GovernedWorkflowRepository(connection)
        request, transaction, validation, _artifact = self.make_records("FAILURE")
        repository.persist_workflow_bundle(
            request=request,
            transaction=transaction,
            validation=validation,
            output_artifacts=(),
        )

        fetched = repository.get_by_idempotency_key(request.idempotency_key)
        self.assertIsNotNone(fetched)
        self.assertEqual(request.workflow_request_id, fetched.workflow_request_id)

        failure = repository.record_workflow_failure(
            transaction_group_id=request.transaction_group_id,
            idempotency_key=request.idempotency_key,
            actor_id=request.actor_id,
            action="workflow_failed",
            error_message="local failure metadata",
            rollback_reference=transaction.rollback_reference,
            workflow_request_id=request.workflow_request_id,
            transaction_scope=transaction.transaction_scope,
            notes="failure test",
        )
        self.assertEqual("FAILED", failure.status)
        self.assertEqual("FAILED", connection.requests[request.workflow_request_id]["STATUS"])
        self.assertTrue(any(row["ARTIFACT_TYPE"] == "error_artifact" for row in connection.outputs.values()))

    def test_analysis_execution_record_persists_metadata_references_only(self) -> None:
        module = self.module()
        connection = FakeConnection()
        repository = module.GovernedWorkflowRepository(connection)
        request, transaction, validation, _artifact = self.make_records("ANALYSIS")
        repository.persist_workflow_bundle(
            request=request,
            transaction=transaction,
            validation=validation,
            output_artifacts=(),
        )
        artifacts = repository.persist_analysis_execution_record(
            module.AnalysisExecutionRecord(
                workflow_request_id=request.workflow_request_id,
                analysis_run_reference="analysis-run-record-only",
                phase4i_payload_reference="phase4i-reference-only",
                dashboard_artifact_reference="dashboard-reference-only",
                comparison_artifact_reference="comparison-reference-only",
                source_validation_reference="source-validation-reference-only",
            )
        )
        self.assertEqual(5, len(artifacts))
        self.assertEqual(
            {
                "analysis_run_record",
                "phase4i_payload_reference",
                "dashboard_artifact_reference",
                "comparison_artifact",
                "source_validation_artifact",
            },
            {artifact.artifact_type for artifact in artifacts},
        )

    def test_no_forbidden_runtime_references_in_repository_source(self) -> None:
        source = read_text(MODULE_PATH)
        forbidden_fragments = (
            "run_analysis.py",
            "scripts.run_analysis",
            "parse_awr_file",
            "build_decision",
            "generate_decision_recommendations",
            "generate_html_dashboard",
            "get_db_connection",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    def test_optional_db_backed_insert_read_idempotency(self) -> None:
        if os.getenv("AWR_PHASE7CA_DB_TEST") != "1":
            self.skipTest("set AWR_PHASE7CA_DB_TEST=1 to run DB-backed Phase 7CA validation")

        try:
            from src.ingest.awr_adb_loader import get_db_connection
        except Exception as exc:  # noqa: BLE001
            self.skipTest(f"project DB connector unavailable: {type(exc).__name__}: {exc}")

        try:
            connection = get_db_connection()
        except Exception as exc:  # noqa: BLE001
            self.skipTest(f"ADB connection unavailable: {type(exc).__name__}: {exc}")

        try:
            _apply_schema(connection)
            module = self.module()
            repository = module.GovernedWorkflowRepository(connection)
            suffix = uuid.uuid4().hex[:12].upper()
            request, transaction, validation, artifact = self.make_records(f"DB-{suffix}")
            result = repository.persist_workflow_bundle(
                request=request,
                transaction=transaction,
                validation=validation,
                output_artifacts=(artifact,),
            )
            replay = repository.persist_workflow_bundle(
                request=request,
                transaction=transaction,
                validation=validation,
                output_artifacts=(artifact,),
            )
            fetched = repository.get_by_idempotency_key(request.idempotency_key)
            self.assertEqual("PERSISTED", result.status)
            self.assertTrue(replay.duplicate)
            self.assertIsNotNone(fetched)
            self.assertEqual(request.workflow_request_id, fetched.workflow_request_id)
        finally:
            connection.close()


def _apply_schema(connection: Any) -> None:
    blocks: list[str] = []
    current: list[str] = []
    for line in SCHEMA_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.upper().startswith("SET "):
            continue
        if stripped == "/":
            block = "\n".join(current).strip()
            if block:
                blocks.append(block)
            current = []
        else:
            current.append(line)
    with connection.cursor() as cursor:
        for block in blocks:
            cursor.execute(block, {})
    connection.commit()


if __name__ == "__main__":
    unittest.main()
