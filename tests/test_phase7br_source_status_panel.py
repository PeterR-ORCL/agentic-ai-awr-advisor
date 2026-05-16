from __future__ import annotations

import ast
import importlib
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
PANEL_DOC = DOCS / "phase7br_source_status_panel.md"
MODEL_DOC = DOCS / "phase7br_source_status_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "index_source_status.py"

FORBIDDEN_IMPORT_PREFIXES = (
    "subprocess",
    "oracledb",
    "cx_Oracle",
    "sqlite3",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "boto3",
    "botocore",
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
    "read_file",
    "open_file",
    "check_file_exists",
    "call_object_storage",
    "list_bucket",
    "download_object",
    "query_database",
    "query_existing_runs",
    "run_analysis",
    "execute_analysis",
    "execute_source_intake",
    "execute_handoff",
    "fetch",
    "requests",
    "subprocess",
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
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


class Phase7BRSourceStatusPanelTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.index_source_status")

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "SourceModeStatus"))
        self.assertTrue(hasattr(module, "SourceModeStatusSummary"))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_runtime_import_isolation(self) -> None:
        imports = imported_modules(MODULE_PATH)
        self.assertEqual(
            imports,
            {
                "__future__",
                "dataclasses",
                "typing",
                "src.learning.index_source_mode_entry",
            },
        )

    def test_docs_exist(self) -> None:
        self.assertTrue(PANEL_DOC.is_file(), PANEL_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        text = (
            lower_text(PANEL_DOC)
            + "\n"
            + lower_text(MODEL_DOC)
            + "\n"
            + lower_text(README)
        )
        for phrase in (
            "source status is not source access",
            "no files are read",
            "no object storage calls are made",
            "no db lookup is made",
            "no run_analysis.py call is made",
            "execution_supported=false",
            "handoff_supported=false",
            "future_em_extract is phase 8 placeholder",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_all_source_modes_have_statuses(self) -> None:
        module = self.module()
        statuses = module.create_default_source_mode_statuses()
        self.assertEqual(
            {status.source_mode for status in statuses},
            {
                "local_staged",
                "local_file",
                "existing_run",
                "object_storage",
                "future_upload",
                "future_em_extract",
            },
        )
        self.assertEqual(len(statuses), 6)

    def test_local_staged_ready_metadata_only(self) -> None:
        module = self.module()
        status = module.create_source_mode_status(
            "local_staged",
            available_hint=True,
        )
        self.assertEqual(status.status, "ready_metadata_only")
        self.assertEqual(status.readiness_level, "ready_metadata_only")
        self.assertTrue(status.requires_validation)
        self.assertTrue(status.available_hint)
        self.assertFalse(status.execution_supported)
        self.assertFalse(status.handoff_supported)

    def test_object_storage_needs_configuration_unless_configured_hint_true(self) -> None:
        module = self.module()
        status = module.create_source_mode_status("object_storage")
        self.assertEqual(status.status, "needs_configuration")
        self.assertEqual(status.readiness_level, "needs_configuration")
        self.assertTrue(status.requires_configuration)
        self.assertTrue(status.requires_validation)

        configured_status = module.create_source_mode_status(
            "object_storage",
            configured_hint=True,
        )
        self.assertEqual(configured_status.status, "needs_validation")
        self.assertEqual(configured_status.readiness_level, "needs_validation")
        self.assertTrue(configured_status.configured_hint)
        self.assertTrue(configured_status.requires_validation)

    def test_future_em_extract_is_phase8_placeholder(self) -> None:
        module = self.module()
        status = module.create_source_mode_status("future_em_extract")
        self.assertEqual(status.status, "future_not_implemented")
        self.assertEqual(status.readiness_level, "future")
        self.assertEqual(status.future_phase, "Phase 8")
        self.assertFalse(status.execution_supported)
        self.assertFalse(status.handoff_supported)

    def test_validation_rejects_access_and_execution_flags(self) -> None:
        module = self.module()
        safe = module.source_mode_status_to_dict(
            module.create_source_mode_status("local_file")
        )
        unsafe_flags = (
            "source_access_performed",
            "file_read_performed",
            "object_storage_call_performed",
            "db_lookup_performed",
            "run_analysis_called",
            "execution_supported",
            "handoff_supported",
        )
        for flag in unsafe_flags:
            with self.subTest(flag=flag):
                data = dict(safe)
                data[flag] = True
                with self.assertRaises(module.IndexSourceStatusError):
                    module.source_mode_status_from_dict(data)

    def test_validation_rejects_unsupported_source_status_and_readiness(self) -> None:
        module = self.module()
        safe = module.source_mode_status_to_dict(
            module.create_source_mode_status("existing_run")
        )
        data = dict(safe)
        data["source_mode"] = "unsupported"
        with self.assertRaises(module.IndexSourceStatusError):
            module.source_mode_status_from_dict(data)

        data = dict(safe)
        data["status"] = "unsupported"
        with self.assertRaises(module.IndexSourceStatusError):
            module.source_mode_status_from_dict(data)

        data = dict(safe)
        data["readiness_level"] = "unsupported"
        with self.assertRaises(module.IndexSourceStatusError):
            module.source_mode_status_from_dict(data)

    def test_summary_counts_valid(self) -> None:
        module = self.module()
        statuses = module.create_default_source_mode_statuses(
            object_storage_configured_hint=False,
            local_source_available_hint=True,
        )
        summary = module.create_source_mode_status_summary(
            statuses=statuses,
            notes="unit test",
        )
        self.assertIs(module.validate_source_mode_status_summary(summary), summary)
        self.assertEqual(summary.source_count, 6)
        self.assertEqual(summary.ready_count, 1)
        self.assertEqual(summary.needs_configuration_count, 1)
        self.assertEqual(summary.future_count, 2)
        self.assertEqual(summary.blocked_count, 0)
        self.assertEqual(summary.default_source_mode, "local_staged")
        self.assertFalse(summary.execution_supported)
        self.assertFalse(summary.handoff_supported)
        self.assertFalse(summary.source_access_performed)
        self.assertFalse(summary.object_storage_configured_hint)
        self.assertTrue(summary.local_source_available_hint)
        self.assertTrue(summary.future_em_extract_placeholder)

    def test_validation_rejects_source_count_mismatch(self) -> None:
        module = self.module()
        summary_data = module.source_mode_status_summary_to_dict(
            module.create_source_mode_status_summary()
        )
        summary_data["source_count"] = 99
        with self.assertRaises(module.IndexSourceStatusError):
            module.source_mode_status_summary_from_dict(summary_data)

    def test_serialization_round_trip(self) -> None:
        module = self.module()
        status = module.create_source_mode_status(
            "object_storage",
            configured_hint=True,
            notes="metadata only",
        )
        status_round_trip = module.source_mode_status_from_dict(
            module.source_mode_status_to_dict(status)
        )
        self.assertEqual(status_round_trip, status)

        summary = module.create_source_mode_status_summary(notes="round trip")
        summary_round_trip = module.source_mode_status_summary_from_dict(
            module.source_mode_status_summary_to_dict(summary)
        )
        self.assertEqual(summary_round_trip, summary)

    def test_no_access_functions_are_defined(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
