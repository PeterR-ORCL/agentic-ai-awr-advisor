from __future__ import annotations

import ast
import importlib
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
HANDOFF_DOC = DOCS / "phase7bt_index_screen3_handoff.md"
MODEL_DOC = DOCS / "phase7bt_index_screen3_handoff_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "index_screen3_handoff.py"

FORBIDDEN_IMPORT_PREFIXES = (
    "subprocess",
    "requests",
    "urllib",
    "http.client",
    "httpx",
    "socket",
    "oci",
    "boto",
    "boto3",
    "botocore",
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
    "scripts.awr_memory_cli",
    "scripts.run_analysis",
    "oracle_agent_memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "perform_handoff",
    "execute_handoff",
    "update_screen3_state",
    "write_local_storage",
    "write_location_hash",
    "create_backend_request",
    "call_backend",
    "call_object_storage",
    "read_file",
    "open_file",
    "query_database",
    "run_analysis",
    "execute_source_intake",
    "execute_analysis",
)

SOURCE_MODES = (
    "local_staged",
    "local_file",
    "existing_run",
    "object_storage",
    "future_upload",
    "future_em_extract",
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


def function_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


class Phase7BTIndexScreen3HandoffTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.index_screen3_handoff")

    def handoff(self, source_mode: str = "local_staged", **overrides):
        module = self.module()
        values = {
            "source_mode": source_mode,
            "source_mode_entry_id": f"INDEX-SOURCE-MODE-ENTRY-{source_mode}",
            "source_status_id": f"INDEX-SOURCE-STATUS-{source_mode}",
            "object_storage_config_id": (
                "OBJECT-STORAGE-CONFIG-METADATA"
                if source_mode == "object_storage"
                else None
            ),
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.create_index_screen3_handoff(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "IndexToScreen3Handoff"))
        self.assertTrue(hasattr(module, "IndexToScreen3HandoffValidation"))
        self.assertTrue(hasattr(module, "IndexSourceEntryReadiness"))

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
        self.assertTrue(HANDOFF_DOC.is_file(), HANDOFF_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        text = (
            lower_text(HANDOFF_DOC)
            + "\n"
            + lower_text(MODEL_DOC)
            + "\n"
            + lower_text(README)
        )
        for phrase in (
            "no handoff is performed",
            "no screen 3 state is updated",
            "no backend request is created",
            "no source access occurs",
            "no object storage call occurs",
            "no file read occurs",
            "no db lookup occurs",
            "no run_analysis.py call occurs",
            "future em extract belongs to phase 8",
            "phase 8 sizing/tco is not implemented",
            "can_handoff=false",
            "handoff_blocked=true",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_handoff_validation_metadata_only(self) -> None:
        module = self.module()
        handoff = self.handoff()
        validation = module.evaluate_index_screen3_handoff(handoff)
        self.assertEqual(validation.validation_status, "VALID_METADATA_ONLY")
        self.assertTrue(validation.valid)
        self.assertEqual(validation.target_screen, "screen_3")
        self.assertFalse(validation.can_handoff)
        self.assertTrue(validation.handoff_blocked)
        self.assertFalse(validation.handoff_performed)
        self.assertFalse(validation.screen3_state_updated)
        self.assertFalse(validation.backend_request_created)

    def test_all_source_modes_supported(self) -> None:
        module = self.module()
        for source_mode in SOURCE_MODES:
            with self.subTest(source_mode=source_mode):
                handoff = self.handoff(source_mode)
                validated = module.validate_index_screen3_handoff(handoff)
                self.assertIs(validated, handoff)
                self.assertEqual(handoff.source_mode, source_mode)
                self.assertFalse(handoff.handoff_performed)
                self.assertFalse(handoff.source_access_performed)
                self.assertFalse(handoff.run_analysis_called)

    def test_object_storage_requires_config_metadata(self) -> None:
        module = self.module()
        handoff = self.handoff(
            "object_storage",
            object_storage_config_id=None,
        )
        validation = module.evaluate_index_screen3_handoff(handoff)
        self.assertFalse(validation.valid)
        self.assertEqual(validation.validation_status, "NEEDS_OBJECT_STORAGE_METADATA")
        self.assertFalse(validation.object_storage_metadata_valid)
        self.assertFalse(validation.can_handoff)
        self.assertTrue(validation.handoff_blocked)

    def test_future_em_extract_placeholder(self) -> None:
        module = self.module()
        handoff = self.handoff("future_em_extract", source_status_id=None)
        validation = module.evaluate_index_screen3_handoff(handoff)
        self.assertEqual(validation.validation_status, "FUTURE_EM_EXTRACT_PLACEHOLDER")
        self.assertTrue(validation.future_em_extract_placeholder)
        self.assertFalse(validation.can_handoff)
        self.assertTrue(validation.handoff_blocked)
        self.assertIn("future EM Extract belongs to Phase 8", validation.denied_reasons)

    def test_missing_source_status_rejected_as_validation_status(self) -> None:
        module = self.module()
        handoff = self.handoff("local_file", source_status_id=None)
        validation = module.evaluate_index_screen3_handoff(handoff)
        self.assertFalse(validation.valid)
        self.assertEqual(validation.validation_status, "NEEDS_SOURCE_STATUS")
        self.assertFalse(validation.source_status_ready)

    def test_serialization_round_trip(self) -> None:
        module = self.module()
        handoff = self.handoff("existing_run")
        handoff_round_trip = module.index_screen3_handoff_from_dict(
            module.index_screen3_handoff_to_dict(handoff)
        )
        self.assertEqual(handoff_round_trip, handoff)

        validation = module.evaluate_index_screen3_handoff(handoff)
        validation_round_trip = module.index_screen3_handoff_validation_from_dict(
            module.index_screen3_handoff_validation_to_dict(validation)
        )
        self.assertEqual(validation_round_trip, validation)

        readiness = module.build_index_source_entry_readiness(notes="ready")
        readiness_round_trip = module.index_source_entry_readiness_from_dict(
            module.index_source_entry_readiness_to_dict(readiness)
        )
        self.assertEqual(readiness_round_trip, readiness)

    def test_deterministic_ids(self) -> None:
        module = self.module()
        handoff_id = module.create_index_screen3_handoff_id("local_staged")
        self.assertEqual(handoff_id, module.create_index_screen3_handoff_id("local_staged"))
        self.assertEqual(
            handoff_id,
            "INDEX-SCREEN3-HANDOFF-LOCAL-STAGED-SCREEN-3",
        )
        self.assertEqual(
            module.create_index_screen3_handoff_validation_id(handoff_id),
            "INDEX-SCREEN3-HANDOFF-VALIDATION-INDEX-SCREEN3-HANDOFF-LOCAL-STAGED-SCREEN-3",
        )
        self.assertEqual(
            module.create_index_source_entry_readiness_id("7BQ-7BT"),
            "INDEX-SOURCE-ENTRY-READINESS-7BQ-7BT",
        )

    def test_validation_rejects_unsafe_handoff_flags(self) -> None:
        module = self.module()
        safe = module.index_screen3_handoff_to_dict(self.handoff())
        unsafe_values = {
            "handoff_supported": True,
            "handoff_performed": True,
            "screen3_state_updated": True,
            "backend_request_created": True,
            "source_access_performed": True,
            "run_analysis_called": True,
            "object_storage_called": True,
            "local_file_read_performed": True,
            "db_lookup_performed": True,
        }
        for field_name, value in unsafe_values.items():
            with self.subTest(field_name=field_name):
                data = dict(safe)
                data[field_name] = value
                with self.assertRaises(module.IndexScreen3HandoffError):
                    module.index_screen3_handoff_from_dict(data)

    def test_validation_rejects_unsafe_validation_flags(self) -> None:
        module = self.module()
        safe = module.index_screen3_handoff_validation_to_dict(
            module.evaluate_index_screen3_handoff(self.handoff())
        )
        unsafe_values = {
            "can_handoff": True,
            "handoff_blocked": False,
            "handoff_performed": True,
            "screen3_state_updated": True,
            "backend_request_created": True,
        }
        for field_name, value in unsafe_values.items():
            with self.subTest(field_name=field_name):
                data = dict(safe)
                data[field_name] = value
                with self.assertRaises(module.IndexScreen3HandoffError):
                    module.index_screen3_handoff_validation_from_dict(data)

    def test_readiness_rejects_execution_flags(self) -> None:
        module = self.module()
        safe = module.index_source_entry_readiness_to_dict(
            module.build_index_source_entry_readiness()
        )
        unsafe_values = {
            "handoff_performed": True,
            "execution_performed": True,
            "object_storage_called": True,
            "local_file_read_performed": True,
            "db_lookup_performed": True,
            "run_analysis_called": True,
            "future_em_extract_placeholder": False,
            "phase8_implemented": True,
        }
        for field_name, value in unsafe_values.items():
            with self.subTest(field_name=field_name):
                data = dict(safe)
                data[field_name] = value
                with self.assertRaises(module.IndexScreen3HandoffError):
                    module.index_source_entry_readiness_from_dict(data)

    def test_no_unsafe_functions(self) -> None:
        functions = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, functions)


if __name__ == "__main__":
    unittest.main()
