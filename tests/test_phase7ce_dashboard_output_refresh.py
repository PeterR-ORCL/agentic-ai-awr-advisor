"""Phase 7CE tests for dashboard output refresh metadata handling."""

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
EXECUTION_DOC = DOCS / "phase7ce_dashboard_output_refresh.md"
MODEL_DOC = DOCS / "phase7ce_dashboard_output_refresh_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "dashboard_output_refresh.py"

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


class FakeDashboardRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def validate_render_input(self, payload_reference: Any) -> dict[str, Any]:
        self.calls.append(("validate_render_input", payload_reference.payload_reference))
        return {"valid": True}

    def render_dashboard(
        self,
        payload_reference: Any,
        output_reference: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls.append(("render_dashboard", payload_reference.payload_reference))
        return {
            "artifact_reference": (
                f"dashboard://generated/{output_reference['refresh_execution_id']}"
            ),
            "artifact_summary": "generated dashboard metadata from fake renderer",
            "output_path": "/tmp/fake-dashboard.html",
            "renderer_name": "fake-dashboard-renderer",
            "renderer_version": "7CE-test",
            "dashboard_generated": True,
            "output_written": True,
            "overwrite_performed": False,
            "generated_at": "2026-05-17T00:00:00Z",
            "run_analysis_called": False,
            "parser_invoked": False,
            "scoring_invoked": False,
            "recommendation_invoked": False,
            "object_storage_called": False,
            "phase4i_mutated": False,
        }


class Phase7CEDashboardOutputRefreshTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.dashboard_output_refresh")

    @staticmethod
    def repository_module():
        return importlib.import_module("src.learning.governed_workflow_repository")

    def repository(self):
        return self.repository_module().GovernedWorkflowRepository(FakeConnection())

    def make_envelope(
        self,
        *,
        suffix: str = "LOCAL",
        refresh_mode: str = "metadata_only",
        phase4i_reference: str | None = "phase4i://payload/7ce",
        dashboard_reference: str | None = "dashboard://existing/7ce",
        comparison_reference: str | None = "comparison://artifact/7ce",
        object_storage_reference: str | None = "object-storage://load/7ce",
        dry_run: bool = False,
        actor_id: str = "ACTOR-7CE-TESTER",
        idempotency_key: str | None = None,
        transaction_group_id: str | None = None,
    ):
        module = self.module()
        idem = f"IDEMP-7CE-{suffix}" if idempotency_key is None else idempotency_key
        tx_id = (
            f"TX-7CE-{suffix}"
            if transaction_group_id is None
            else transaction_group_id
        )
        return module.DashboardRefreshRequestEnvelope(
            refresh_execution_id=module.create_dashboard_refresh_execution_id(
                "SOURCE-EXECUTION-7CE",
                idem,
            ),
            source_execution_id="SOURCE-EXECUTION-7CE",
            source_execution_type="deterministic_reanalysis",
            workflow_request_id="WORKFLOW-REQUEST-7CE",
            idempotency_key=idem,
            transaction_group_id=tx_id,
            actor_id=actor_id,
            actor_audit_context={"actor_id": actor_id},
            phase4i_reference=phase4i_reference,
            dashboard_reference=dashboard_reference,
            comparison_reference=comparison_reference,
            object_storage_reference=object_storage_reference,
            refresh_mode=refresh_mode,
            renderer_requested=refresh_mode == "regenerate_with_renderer",
            dry_run=dry_run,
            validation_reference="VALIDATION-7CE-1",
            rollback_reference=f"ROLLBACK-7CE-{suffix}",
            notes="phase 7ce unit test",
        )

    def test_import_safety(self) -> None:
        before_environment = dict(os.environ)
        before_modules = set(sys.modules)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "DashboardRefreshRequestEnvelope"))
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
        text = (
            lower_text(EXECUTION_DOC)
            + "\n"
            + lower_text(MODEL_DOC)
            + "\n"
            + lower_text(README)
        )
        for phrase in (
            "no run_analysis.py call",
            "no parser/scoring/recommendation invocation",
            "no object storage call",
            "no phase 4i mutation",
            "dashboard generation only through injected renderer",
            "default path is metadata-only",
            "no generated dashboard html",
            "phase 8 is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_envelope_validation(self) -> None:
        module = self.module()
        envelope = self.make_envelope()
        self.assertIs(module.validate_dashboard_refresh_envelope(envelope), envelope)
        with self.assertRaises(module.DashboardOutputRefreshError):
            self.make_envelope(actor_id="")
        with self.assertRaises(module.DashboardOutputRefreshError):
            self.make_envelope(idempotency_key="")
        with self.assertRaises(module.DashboardOutputRefreshError):
            self.make_envelope(transaction_group_id="")
        with self.assertRaises(module.DashboardOutputRefreshError):
            module.DashboardRefreshRequestEnvelope(
                **{
                    **module.dashboard_refresh_envelope_to_dict(envelope),
                    "refresh_mode": "unsupported",
                }
            )
        with self.assertRaises(module.DashboardOutputRefreshError):
            module.validate_dashboard_refresh_envelope(
                module.DashboardRefreshRequestEnvelope(
                    **{
                        **module.dashboard_refresh_envelope_to_dict(envelope),
                        "rollback_reference": None,
                    }
                )
            )

    def test_metadata_only_mode_persists_metadata_only(self) -> None:
        repository_module = self.repository_module()
        connection = FakeConnection()
        repository = repository_module.GovernedWorkflowRepository(connection)
        result = self.module().execute_dashboard_output_refresh(
            self.make_envelope(suffix="METADATA"),
            repository=repository,
            renderer=None,
        )
        self.assertEqual("metadata_persisted", result.refresh_status)
        self.assertTrue(result.workflow_request_persisted)
        self.assertTrue(result.workflow_validation_persisted)
        self.assertTrue(result.workflow_audit_persisted)
        self.assertTrue(result.output_artifacts_persisted)
        self.assertFalse(result.dashboard_regenerated)
        self.assertFalse(result.output_written)
        self.assertEqual(1, len(connection.requests))
        self.assertEqual(1, len(connection.audits))
        self.assertEqual(
            {
                "validation_response",
                "phase4i_payload_reference",
                "dashboard_artifact_reference",
                "comparison_artifact",
                "object_storage_load_artifact",
            },
            {row["ARTIFACT_TYPE"] for row in connection.outputs.values()},
        )

    def test_missing_renderer_blocks_regenerate_mode(self) -> None:
        result = self.module().execute_dashboard_output_refresh(
            self.make_envelope(suffix="NO-RENDERER", refresh_mode="regenerate_with_renderer"),
            repository=self.repository(),
            renderer=None,
        )
        self.assertEqual("blocked_no_renderer", result.refresh_status)
        self.assertFalse(result.dashboard_regenerated)
        self.assertFalse(result.output_written)
        self.assertIn("injected dashboard renderer is required", result.denied_reasons)

    def test_missing_phase4i_reference_blocks_required_modes(self) -> None:
        result = self.module().execute_dashboard_output_refresh(
            self.make_envelope(suffix="NO-PHASE4I", phase4i_reference=None),
            repository=self.repository(),
            renderer=None,
        )
        self.assertEqual("blocked_missing_phase4i_reference", result.refresh_status)
        self.assertFalse(result.phase4i_mutated)
        self.assertFalse(result.dashboard_regenerated)

    def test_fake_renderer_can_report_generated_artifact(self) -> None:
        renderer = FakeDashboardRenderer()
        result = self.module().execute_dashboard_output_refresh(
            self.make_envelope(suffix="RENDERER", refresh_mode="regenerate_with_renderer"),
            repository=self.repository(),
            renderer=renderer,
        )
        self.assertEqual("regenerated_with_injected_renderer", result.refresh_status)
        self.assertTrue(result.dashboard_regenerated)
        self.assertTrue(result.output_written)
        self.assertIsNotNone(result.dashboard_artifact_reference)
        self.assertEqual(
            [("validate_render_input", "phase4i://payload/7ce"), ("render_dashboard", "phase4i://payload/7ce")],
            renderer.calls,
        )

    def test_fake_renderer_idempotent_replay_avoids_recalls(self) -> None:
        repository_module = self.repository_module()
        connection = FakeConnection()
        repository = repository_module.GovernedWorkflowRepository(connection)
        renderer = FakeDashboardRenderer()
        envelope = self.make_envelope(
            suffix="IDEMPOTENT",
            refresh_mode="regenerate_with_renderer",
        )
        first = self.module().execute_dashboard_output_refresh(
            envelope,
            repository=repository,
            renderer=renderer,
        )
        second = self.module().execute_dashboard_output_refresh(
            envelope,
            repository=repository,
            renderer=renderer,
        )
        self.assertEqual("regenerated_with_injected_renderer", first.refresh_status)
        self.assertEqual("idempotent_replay", second.refresh_status)
        self.assertEqual(2, len(renderer.calls))
        self.assertEqual(1, len(connection.requests))

    def test_phase4i_reference_validation(self) -> None:
        module = self.module()
        ref = module.Phase4IPayloadReference(
            phase4i_reference_id=module.create_phase4i_payload_reference_id(
                "SOURCE",
                "phase4i://payload",
            ),
            source_execution_id="SOURCE",
            payload_reference="phase4i://payload",
            payload_summary="phase4i reference",
        )
        self.assertIs(module.validate_phase4i_payload_reference(ref), ref)
        with self.assertRaises(module.DashboardOutputRefreshError):
            module.Phase4IPayloadReference(
                phase4i_reference_id="PHASE4I-UNSAFE",
                source_execution_id="SOURCE",
                payload_reference="phase4i://payload",
                payload_summary="phase4i reference",
                phase4i_mutated=True,
            )

    def test_dashboard_artifact_reference_validation(self) -> None:
        module = self.module()
        ref = module.RegeneratedDashboardArtifactReference(
            dashboard_artifact_id=module.create_dashboard_artifact_reference_id(
                "REFRESH",
                "dashboard://artifact",
            ),
            refresh_execution_id="REFRESH",
            artifact_type="dashboard_artifact_reference",
            artifact_reference="dashboard://artifact",
            artifact_summary="dashboard reference",
        )
        self.assertIs(module.validate_dashboard_artifact_reference(ref), ref)
        with self.assertRaises(module.DashboardOutputRefreshError):
            module.RegeneratedDashboardArtifactReference(
                dashboard_artifact_id="DASHBOARD-UNSAFE",
                refresh_execution_id="REFRESH",
                artifact_type="dashboard_artifact_reference",
                artifact_reference="dashboard://artifact",
                artifact_summary="dashboard reference",
                output_written=True,
            )

    def test_repository_integration_with_fake_repo(self) -> None:
        repository_module = self.repository_module()
        connection = FakeConnection()
        repository = repository_module.GovernedWorkflowRepository(connection)
        result = self.module().execute_dashboard_output_refresh(
            self.make_envelope(suffix="REPO", refresh_mode="link_existing_dashboard"),
            repository=repository,
            renderer=None,
        )
        self.assertEqual("linked_existing_dashboard", result.refresh_status)
        self.assertTrue(result.workflow_request_persisted)
        self.assertTrue(result.output_artifacts_persisted)
        self.assertEqual(1, len(connection.requests))
        self.assertEqual(1, len(connection.validations))
        self.assertEqual(1, len(connection.audits))

    def test_safety_flags_remain_false(self) -> None:
        result = self.module().execute_dashboard_output_refresh(
            self.make_envelope(suffix="SAFETY", refresh_mode="metadata_only"),
            repository=self.repository(),
            renderer=None,
        )
        self.assertFalse(result.run_analysis_called)
        self.assertFalse(result.object_storage_called)
        self.assertFalse(result.parser_invoked)
        self.assertFalse(result.scoring_invoked)
        self.assertFalse(result.recommendation_invoked)
        self.assertFalse(result.phase4i_mutated)

    def test_renderer_safety_flags_are_rejected(self) -> None:
        class UnsafeRenderer(FakeDashboardRenderer):
            def render_dashboard(self, payload_reference: Any, output_reference: dict[str, Any]) -> dict[str, Any]:
                output = super().render_dashboard(payload_reference, output_reference)
                output["run_analysis_called"] = True
                return output

        result = self.module().execute_dashboard_output_refresh(
            self.make_envelope(suffix="UNSAFE-RENDERER", refresh_mode="regenerate_with_renderer"),
            repository=self.repository(),
            renderer=UnsafeRenderer(),
        )
        self.assertEqual("failed_safely", result.refresh_status)
        self.assertFalse(result.run_analysis_called)
        self.assertFalse(result.dashboard_regenerated)

    def test_serialization_round_trips(self) -> None:
        module = self.module()
        envelope = self.make_envelope(suffix="ROUNDTRIP")
        envelope_round_trip = module.dashboard_refresh_envelope_from_dict(
            module.dashboard_refresh_envelope_to_dict(envelope)
        )
        self.assertEqual(envelope_round_trip, envelope)

        validation = module.evaluate_dashboard_refresh_request(envelope, renderer=None)
        self.assertEqual(
            validation,
            module.dashboard_refresh_validation_from_dict(
                module.dashboard_refresh_validation_to_dict(validation)
            ),
        )

        result = module.execute_dashboard_output_refresh(
            self.make_envelope(suffix="RESULT-ROUNDTRIP"),
            repository=self.repository(),
            renderer=None,
        )
        self.assertEqual(
            result,
            module.dashboard_refresh_result_from_dict(
                module.dashboard_refresh_result_to_dict(result)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        self.assertEqual(
            module.create_dashboard_refresh_execution_id("SOURCE", "IDEMP"),
            module.create_dashboard_refresh_execution_id("SOURCE", "IDEMP"),
        )
        self.assertNotEqual(
            module.create_dashboard_refresh_execution_id("SOURCE", "IDEMP"),
            module.create_dashboard_refresh_execution_id("SOURCE-OTHER", "IDEMP"),
        )

    def test_optional_db_backed_dashboard_refresh(self) -> None:
        if os.getenv("AWR_PHASE7CE_DB_TEST") != "1":
            self.skipTest("set AWR_PHASE7CE_DB_TEST=1 to run DB-backed Phase 7CE validation")

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
            renderer = FakeDashboardRenderer()
            envelope = self.make_envelope(
                suffix=f"DB-{suffix}",
                refresh_mode="regenerate_with_renderer",
            )
            result = self.module().execute_dashboard_output_refresh(
                envelope,
                repository=repository,
                renderer=renderer,
            )
            replay = self.module().execute_dashboard_output_refresh(
                envelope,
                repository=repository,
                renderer=renderer,
            )
            self.assertEqual("regenerated_with_injected_renderer", result.refresh_status)
            self.assertEqual("idempotent_replay", replay.refresh_status)
            self.assertEqual(2, len(renderer.calls))
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
