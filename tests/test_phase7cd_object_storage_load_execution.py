"""Phase 7CD tests for controlled Object Storage load execution."""

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
EXECUTION_DOC = DOCS / "phase7cd_object_storage_load_execution.md"
MODEL_DOC = DOCS / "phase7cd_object_storage_load_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "object_storage_load_execution.py"

FORBIDDEN_IMPORT_PREFIXES = (
    "oci",
    "boto",
    "boto3",
    "botocore",
    "requests",
    "urllib",
    "http.client",
    "httpx",
    "socket",
    "subprocess",
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


class FakeObjectStorageClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def head_object(self, namespace: str, bucket: str, object_name: str) -> dict[str, Any]:
        self.calls.append(("head_object", (namespace, bucket, object_name)))
        return {
            "object_name": object_name,
            "size_bytes": 128,
            "etag": "fake-etag",
            "content_type": "text/html",
        }

    def get_object(self, namespace: str, bucket: str, object_name: str) -> dict[str, Any]:
        self.calls.append(("get_object", (namespace, bucket, object_name)))
        return {
            "object_name": object_name,
            "content": b"fake awr bytes",
            "etag": "fake-get-etag",
            "content_type": "text/html",
        }

    def list_objects(
        self,
        namespace: str,
        bucket: str,
        prefix: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(("list_objects", (namespace, bucket, prefix)))
        base_prefix = prefix or "awr/"
        return [
            {
                "object_name": f"{base_prefix}one.html",
                "size_bytes": 10,
                "etag": "etag-one",
            },
            {
                "object_name": f"{base_prefix}two.html",
                "size_bytes": 20,
                "etag": "etag-two",
            },
        ]


class Phase7CDObjectStorageLoadExecutionTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.object_storage_load_execution")

    @staticmethod
    def config_module():
        return importlib.import_module("src.learning.object_storage_config_validation")

    @staticmethod
    def source_module():
        return importlib.import_module("src.learning.screen3_source_selection")

    @staticmethod
    def repository_module():
        return importlib.import_module("src.learning.governed_workflow_repository")

    def make_config(self, **overrides):
        config_module = self.config_module()
        values = {
            "namespace": "namespace",
            "bucket": "bucket",
            "object_name": "awr/report.html",
            "prefix": None,
            "region": "us-ashburn-1",
            "compartment_id": "ocid1.compartment.oc1..example",
            "credential_mode": "config_file",
            "profile_name": "DEFAULT",
            "uri": "oci://namespace/bucket/awr/report.html",
            "configured_hint": True,
            "notes": "phase 7cd unit test",
        }
        values.update(overrides)
        values["config_id"] = config_module.create_object_storage_config_id(
            namespace=values.get("namespace"),
            bucket=values.get("bucket"),
            object_name=values.get("object_name"),
            prefix=values.get("prefix"),
            region=values.get("region"),
        )
        return config_module.ObjectStorageConfiguration(**values)

    def make_source_selection(self, config=None):
        source_module = self.source_module()
        config = config or self.make_config()
        object_source = source_module.ObjectStorageSourceReference(
            object_source_id=source_module.create_object_source_id(
                namespace=config.namespace,
                bucket=config.bucket,
                object_name=config.object_name,
                region=config.region,
            ),
            namespace=config.namespace,
            bucket=config.bucket,
            object_name=config.object_name or "awr/report.html",
            region=config.region,
            compartment_id=config.compartment_id,
            credential_mode=config.credential_mode,
            uri=config.uri,
            configured_hint=True,
        )
        return source_module.SourceSelection(
            source_selection_id=source_module.create_source_selection_id(
                "object_storage",
                "AWR object",
            ),
            source_mode="object_storage",
            source_label="AWR object",
            object_storage_source=object_source,
            selected_by_actor_id="ACTOR-7CD-TESTER",
            validation_status="VALID_METADATA_ONLY",
            notes="phase 7cd unit test",
        )

    def make_envelope(
        self,
        *,
        suffix: str = "LOCAL",
        load_mode: str = "metadata_only",
        dry_run: bool = False,
        config=None,
        validation=None,
        source_selection=None,
        actor_id: str = "ACTOR-7CD-TESTER",
        idempotency_key: str | None = None,
        transaction_group_id: str | None = None,
        requested_object_name: str | None = "awr/report.html",
        requested_prefix: str | None = None,
    ):
        module = self.module()
        config_module = self.config_module()
        config = config or self.make_config(object_name=requested_object_name)
        validation = validation or config_module.evaluate_object_storage_configuration(config)
        source_selection = source_selection or self.make_source_selection(config)
        idem = f"IDEMP-7CD-{suffix}" if idempotency_key is None else idempotency_key
        tx_id = (
            f"TX-7CD-{suffix}"
            if transaction_group_id is None
            else transaction_group_id
        )
        return module.ObjectStorageLoadRequestEnvelope(
            load_execution_id=module.create_object_storage_load_execution_id(
                idem,
                object_name=requested_object_name,
                prefix=requested_prefix,
            ),
            source_selection=source_selection,
            object_storage_config=config,
            object_storage_validation=validation,
            actor_id=actor_id,
            actor_audit_context={"actor_id": actor_id},
            idempotency_key=idem,
            transaction_group_id=tx_id,
            requested_object_name=requested_object_name,
            requested_prefix=requested_prefix,
            load_mode=load_mode,
            expected_file_type="html",
            validation_reference="VALIDATION-7CD-1",
            rollback_reference=f"ROLLBACK-7CD-{suffix}",
            dry_run=dry_run,
            notes="phase 7cd unit test",
        )

    def repository(self):
        return self.repository_module().GovernedWorkflowRepository(FakeConnection())

    def test_import_safety(self) -> None:
        before_environment = dict(os.environ)
        before_modules = set(sys.modules)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "ObjectStorageLoadRequestEnvelope"))
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
        text = lower_text(EXECUTION_DOC) + "\n" + lower_text(MODEL_DOC) + "\n" + lower_text(README)
        for phrase in (
            "object storage was part of earlier project architecture",
            "project owner already has an object storage bucket",
            "no hard-coded bucket/namespace/credentials",
            "no run_analysis.py call",
            "no parser invocation",
            "no dashboard regeneration",
            "no phase 4i mutation",
            "no file write",
            "no credentials persisted",
            "no oci sdk import required",
            "em extract remains phase 8",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_secret_detection(self) -> None:
        module = self.module()
        payload = {
            "namespace": "namespace",
            "nested": {
                "auth_token": "redacted",
                "key_file_content": "redacted",
            },
            "items": [{"api_key": "redacted"}],
        }
        self.assertEqual(
            ["items[0].api_key", "nested.auth_token", "nested.key_file_content"],
            module.detect_secret_fields(payload),
        )

    def test_envelope_validation_requires_governed_metadata(self) -> None:
        module = self.module()
        envelope = self.make_envelope()
        self.assertIs(module.validate_object_storage_load_envelope(envelope), envelope)
        with self.assertRaises(module.ObjectStorageLoadExecutionError):
            self.make_envelope(actor_id="")
        with self.assertRaises(module.ObjectStorageLoadExecutionError):
            self.make_envelope(idempotency_key="")
        with self.assertRaises(module.ObjectStorageLoadExecutionError):
            self.make_envelope(transaction_group_id="")
        with self.assertRaises(module.ObjectStorageLoadExecutionError):
            module.ObjectStorageLoadRequestEnvelope(
                **{
                    **module.object_storage_load_envelope_to_dict(envelope),
                    "object_storage_config": None,
                    "source_selection": envelope.source_selection,
                    "object_storage_validation": envelope.object_storage_validation,
                }
            )

    def test_invalid_config_blocks_without_client_call(self) -> None:
        config_module = self.config_module()
        config = self.make_config(namespace=None)
        validation = config_module.evaluate_object_storage_configuration(config)
        client = FakeObjectStorageClient()
        result = self.module().execute_object_storage_load(
            self.make_envelope(
                suffix="INVALID",
                config=config,
                validation=validation,
                source_selection=self.make_source_selection(self.make_config()),
            ),
            repository=self.repository(),
            client=client,
        )
        self.assertEqual("blocked_invalid_config", result.load_status)
        self.assertFalse(result.object_storage_call_performed)
        self.assertEqual([], client.calls)

    def test_no_client_blocks_non_metadata_load(self) -> None:
        result = self.module().execute_object_storage_load(
            self.make_envelope(suffix="NO-CLIENT", load_mode="head_object"),
            repository=self.repository(),
            client=None,
        )
        self.assertEqual("blocked_no_client", result.load_status)
        self.assertFalse(result.object_storage_call_performed)

    def test_metadata_only_does_not_call_client(self) -> None:
        client = FakeObjectStorageClient()
        result = self.module().execute_object_storage_load(
            self.make_envelope(suffix="METADATA", load_mode="metadata_only"),
            repository=self.repository(),
            client=client,
        )
        self.assertEqual("metadata_validated", result.load_status)
        self.assertFalse(result.object_storage_call_performed)
        self.assertFalse(result.object_head_performed)
        self.assertFalse(result.object_download_performed)
        self.assertEqual([], client.calls)
        self.assertTrue(result.workflow_request_persisted)

    def test_fake_head_object_client_returns_metadata_reference(self) -> None:
        client = FakeObjectStorageClient()
        result = self.module().execute_object_storage_load(
            self.make_envelope(suffix="HEAD", load_mode="head_object"),
            repository=self.repository(),
            client=client,
        )
        self.assertEqual("object_metadata_loaded", result.load_status)
        self.assertEqual([("head_object", ("namespace", "bucket", "awr/report.html"))], client.calls)
        self.assertTrue(result.object_storage_call_performed)
        self.assertTrue(result.object_head_performed)
        self.assertFalse(result.object_download_performed)
        self.assertEqual(1, len(result.loaded_objects))
        self.assertFalse(result.loaded_objects[0].local_file_written)

    def test_fake_get_object_client_returns_in_memory_reference(self) -> None:
        client = FakeObjectStorageClient()
        result = self.module().execute_object_storage_load(
            self.make_envelope(suffix="GET", load_mode="get_object"),
            repository=self.repository(),
            client=client,
        )
        self.assertEqual("object_content_loaded_in_memory", result.load_status)
        self.assertEqual([("get_object", ("namespace", "bucket", "awr/report.html"))], client.calls)
        self.assertTrue(result.object_download_performed)
        self.assertTrue(result.loaded_objects[0].object_downloaded)
        self.assertFalse(result.loaded_objects[0].local_file_written)
        self.assertFalse(result.loaded_objects[0].object_content_persisted)

    def test_fake_list_prefix_returns_references_without_downloads(self) -> None:
        config = self.make_config(object_name=None, prefix="awr/")
        validation = self.config_module().evaluate_object_storage_configuration(config)
        client = FakeObjectStorageClient()
        result = self.module().execute_object_storage_load(
            self.make_envelope(
                suffix="LIST",
                load_mode="list_prefix",
                config=config,
                validation=validation,
                requested_object_name=None,
                requested_prefix="awr/",
            ),
            repository=self.repository(),
            client=client,
        )
        self.assertEqual("prefix_listed", result.load_status)
        self.assertEqual([("list_objects", ("namespace", "bucket", "awr/"))], client.calls)
        self.assertEqual(2, len(result.loaded_objects))
        self.assertFalse(any(ref.object_downloaded for ref in result.loaded_objects))

    def test_idempotent_replay_avoids_recalling_client(self) -> None:
        repository_module = self.repository_module()
        connection = FakeConnection()
        repository = repository_module.GovernedWorkflowRepository(connection)
        client = FakeObjectStorageClient()
        envelope = self.make_envelope(suffix="IDEMPOTENT", load_mode="head_object")
        first = self.module().execute_object_storage_load(
            envelope,
            repository=repository,
            client=client,
        )
        second = self.module().execute_object_storage_load(
            envelope,
            repository=repository,
            client=client,
        )
        self.assertEqual("object_metadata_loaded", first.load_status)
        self.assertEqual("idempotent_replay", second.load_status)
        self.assertEqual(1, len(client.calls))
        self.assertEqual(1, len(connection.requests))

    def test_repository_integration_with_fake_connection(self) -> None:
        repository_module = self.repository_module()
        connection = FakeConnection()
        repository = repository_module.GovernedWorkflowRepository(connection)
        result = self.module().execute_object_storage_load(
            self.make_envelope(suffix="REPO", load_mode="head_object"),
            repository=repository,
            client=FakeObjectStorageClient(),
        )
        self.assertTrue(result.workflow_request_persisted)
        self.assertTrue(result.workflow_validation_persisted)
        self.assertTrue(result.workflow_audit_persisted)
        self.assertTrue(result.output_artifacts_persisted)
        self.assertEqual(1, len(connection.requests))
        self.assertEqual(1, len(connection.audits))
        self.assertEqual(
            {"source_validation_artifact", "object_storage_load_artifact"},
            {row["ARTIFACT_TYPE"] for row in connection.outputs.values()},
        )

    def test_safety_flags_remain_false(self) -> None:
        result = self.module().execute_object_storage_load(
            self.make_envelope(suffix="SAFETY", load_mode="get_object"),
            repository=self.repository(),
            client=FakeObjectStorageClient(),
        )
        self.assertFalse(result.local_file_written)
        self.assertFalse(result.db_lookup_performed)
        self.assertFalse(result.run_analysis_called)
        self.assertFalse(result.parser_invoked)
        self.assertFalse(result.phase4i_mutated)
        self.assertFalse(result.dashboard_regenerated)

    def test_serialization_round_trips(self) -> None:
        module = self.module()
        envelope = self.make_envelope(suffix="ROUNDTRIP")
        envelope_round_trip = module.object_storage_load_envelope_from_dict(
            module.object_storage_load_envelope_to_dict(envelope)
        )
        self.assertEqual(envelope_round_trip, envelope)

        validation = module.evaluate_object_storage_load_request(envelope, client=None)
        self.assertEqual(
            validation,
            module.object_storage_load_validation_from_dict(
                module.object_storage_load_validation_to_dict(validation)
            ),
        )

        result = module.execute_object_storage_load(
            self.make_envelope(suffix="RESULT-ROUNDTRIP", load_mode="head_object"),
            repository=self.repository(),
            client=FakeObjectStorageClient(),
        )
        self.assertEqual(
            result,
            module.object_storage_load_result_from_dict(
                module.object_storage_load_result_to_dict(result)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        self.assertEqual(
            module.create_object_storage_load_execution_id(
                "IDEMP-7CD",
                object_name="awr/report.html",
            ),
            module.create_object_storage_load_execution_id(
                "IDEMP-7CD",
                object_name="awr/report.html",
            ),
        )
        self.assertNotEqual(
            module.create_object_storage_load_execution_id(
                "IDEMP-7CD",
                object_name="awr/report.html",
            ),
            module.create_object_storage_load_execution_id(
                "IDEMP-7CD",
                object_name="awr/other.html",
            ),
        )

    def test_optional_db_backed_object_storage_load(self) -> None:
        if os.getenv("AWR_PHASE7CD_DB_TEST") != "1":
            self.skipTest("set AWR_PHASE7CD_DB_TEST=1 to run DB-backed Phase 7CD validation")

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
            suffix = uuid.uuid4().hex[:12].upper()
            envelope = self.make_envelope(suffix=f"DB-{suffix}", load_mode="head_object")
            client = FakeObjectStorageClient()
            result = self.module().execute_object_storage_load(
                envelope,
                repository=repository,
                client=client,
            )
            replay = self.module().execute_object_storage_load(
                envelope,
                repository=repository,
                client=client,
            )
            self.assertEqual("object_metadata_loaded", result.load_status)
            self.assertEqual("idempotent_replay", replay.load_status)
            self.assertEqual(1, len(client.calls))
        finally:
            connection.close()

    def test_optional_live_object_storage_validation(self) -> None:
        if os.getenv("AWR_PHASE7CD_OBJECT_STORAGE_TEST") != "1":
            self.skipTest(
                "set AWR_PHASE7CD_OBJECT_STORAGE_TEST=1 to run live Object Storage validation"
            )

        namespace = os.getenv("OCI_NAMESPACE") or os.getenv("OCI_OBJECT_STORAGE_NAMESPACE")
        bucket = os.getenv("OCI_BUCKET_NAME") or os.getenv("OCI_OBJECT_STORAGE_BUCKET")
        object_name = os.getenv("OCI_OBJECT_NAME") or os.getenv("OCI_OBJECT_STORAGE_OBJECT_NAME")
        region = os.getenv("OCI_REGION")
        compartment_id = os.getenv("OCI_COMPARTMENT_ID") or "ocid1.compartment.oc1..metadata-only"
        if not all((namespace, bucket, object_name, region)):
            self.skipTest(
                "live Object Storage metadata unavailable: need namespace, bucket, object name, and region env values"
            )

        try:
            import oci  # noqa: PLC0415
        except Exception as exc:  # noqa: BLE001
            self.skipTest(f"OCI SDK unavailable for opt-in live validation: {type(exc).__name__}: {exc}")

        class LiveClient:
            def __init__(self) -> None:
                config = oci.config.from_file(
                    os.getenv("OCI_CONFIG_FILE", "~/.oci/config"),
                    os.getenv("OCI_CONFIG_PROFILE", "DEFAULT"),
                )
                self.client = oci.object_storage.ObjectStorageClient(config)

            def head_object(self, namespace_arg: str, bucket_arg: str, object_arg: str):
                return self.client.head_object(
                    namespace_name=namespace_arg,
                    bucket_name=bucket_arg,
                    object_name=object_arg,
                )

        config = self.make_config(
            namespace=namespace,
            bucket=bucket,
            object_name=object_name,
            region=region,
            compartment_id=compartment_id,
            credential_mode="config_file",
        )
        validation = self.config_module().evaluate_object_storage_configuration(config)
        result = self.module().execute_object_storage_load(
            self.make_envelope(
                suffix=f"LIVE-{uuid.uuid4().hex[:8].upper()}",
                config=config,
                validation=validation,
                load_mode="head_object",
                requested_object_name=object_name,
            ),
            repository=self.repository(),
            client=LiveClient(),
        )
        self.assertEqual("object_metadata_loaded", result.load_status)
        self.assertTrue(result.object_head_performed)


if __name__ == "__main__":
    unittest.main()
