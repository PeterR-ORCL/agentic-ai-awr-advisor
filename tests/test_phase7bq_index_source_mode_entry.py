from __future__ import annotations

import ast
import importlib
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
ENTRY_DOC = DOCS / "phase7bq_index_source_mode_entry.md"
MODEL_DOC = DOCS / "phase7bq_source_mode_entry_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "index_source_mode_entry.py"

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
    "call_object_storage",
    "query_database",
    "run_analysis",
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


class Phase7BQIndexSourceModeEntryTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.index_source_mode_entry")

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "IndexSourceModeEntry"))
        self.assertTrue(hasattr(module, "IndexSourceModeEntrySummary"))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_docs_exist(self) -> None:
        self.assertTrue(ENTRY_DOC.is_file(), ENTRY_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        text = (
            lower_text(ENTRY_DOC)
            + "\n"
            + lower_text(MODEL_DOC)
            + "\n"
            + lower_text(README)
        )
        for phrase in (
            "source mode entry is not execution",
            "no files are read",
            "no object storage calls are made",
            "no db lookup is made",
            "no run_analysis.py call is made",
            "no screen 3 handoff is implemented",
            "future_em_extract is placeholder only",
            "em extract implementation belongs to phase 8",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_all_source_modes_supported(self) -> None:
        module = self.module()
        self.assertEqual(
            module.INDEX_SOURCE_MODES,
            (
                "local_staged",
                "local_file",
                "existing_run",
                "object_storage",
                "future_upload",
                "future_em_extract",
            ),
        )
        self.assertEqual(
            module.INDEX_SOURCE_DISPLAY_NAMES,
            {
                "local_staged": "Local Staged AWR",
                "local_file": "Local File",
                "existing_run": "Existing Run",
                "object_storage": "Object Storage",
                "future_upload": "Future Upload",
                "future_em_extract": "Future EM Extract",
            },
        )
        for source_mode in module.INDEX_SOURCE_MODES:
            with self.subTest(source_mode=source_mode):
                entry = module.create_index_source_mode_entry(source_mode)
                self.assertEqual(entry.source_mode, source_mode)
                self.assertEqual(
                    entry.display_name,
                    module.INDEX_SOURCE_DISPLAY_NAMES[source_mode],
                )

    def test_default_entries_include_required_source_modes(self) -> None:
        module = self.module()
        entries = module.create_default_index_source_mode_entries()
        self.assertEqual(
            {entry.source_mode for entry in entries},
            set(module.INDEX_SOURCE_MODES),
        )
        self.assertEqual(len(entries), 6)
        for entry in entries:
            with self.subTest(source_mode=entry.source_mode):
                self.assertTrue(entry.enabled_for_preview)
                self.assertFalse(entry.handoff_supported)
                self.assertFalse(entry.execution_supported)

    def test_summary_validates_expected_counts_and_disabled_execution(self) -> None:
        module = self.module()
        summary = module.create_index_source_mode_summary(notes="unit test")
        self.assertIs(module.validate_index_source_mode_summary(summary), summary)
        self.assertEqual(summary.default_source_mode, "local_staged")
        self.assertEqual(summary.source_mode_count, 6)
        self.assertEqual(summary.implemented_count, 4)
        self.assertEqual(summary.preview_only_count, 6)
        self.assertFalse(summary.handoff_supported)
        self.assertFalse(summary.execution_supported)
        self.assertFalse(summary.object_storage_available_hint)
        self.assertFalse(summary.future_em_extract_available_hint)

    def test_validation_rejects_unsupported_source_mode(self) -> None:
        module = self.module()
        with self.assertRaises(module.IndexSourceModeEntryError):
            module.create_index_source_mode_entry("unsupported")

    def test_validation_rejects_handoff_supported_true(self) -> None:
        module = self.module()
        values = module.index_source_mode_entry_to_dict(
            module.create_index_source_mode_entry("local_staged")
        )
        values["handoff_supported"] = True
        with self.assertRaises(module.IndexSourceModeEntryError):
            module.index_source_mode_entry_from_dict(values)

    def test_validation_rejects_execution_supported_true(self) -> None:
        module = self.module()
        values = module.index_source_mode_entry_to_dict(
            module.create_index_source_mode_entry("object_storage")
        )
        values["execution_supported"] = True
        with self.assertRaises(module.IndexSourceModeEntryError):
            module.index_source_mode_entry_from_dict(values)

    def test_validation_rejects_source_count_mismatch(self) -> None:
        module = self.module()
        summary_data = module.index_source_mode_summary_to_dict(
            module.create_index_source_mode_summary()
        )
        summary_data["source_mode_count"] = 99
        with self.assertRaises(module.IndexSourceModeEntryError):
            module.index_source_mode_summary_from_dict(summary_data)

    def test_serialization_round_trip(self) -> None:
        module = self.module()
        entry = module.create_index_source_mode_entry(
            "future_em_extract",
            notes="placeholder only",
        )
        entry_round_trip = module.index_source_mode_entry_from_dict(
            module.index_source_mode_entry_to_dict(entry)
        )
        self.assertEqual(entry_round_trip, entry)

        summary = module.create_index_source_mode_summary(notes="round trip")
        summary_round_trip = module.index_source_mode_summary_from_dict(
            module.index_source_mode_summary_to_dict(summary)
        )
        self.assertEqual(summary_round_trip, summary)

    def test_no_execution_functions_are_defined(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
