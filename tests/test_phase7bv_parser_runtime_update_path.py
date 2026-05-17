"""Phase 7BV tests for parser runtime update path metadata."""

from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "learning" / "parser_runtime_update_path.py"
DOCS = ROOT / "docs" / "architecture"
PATH_DOC = DOCS / "phase7bv_parser_runtime_update_path.md"
MODEL_DOC = DOCS / "phase7bv_parser_runtime_update_model.md"

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
    "src.parser",
    "src.parsing",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.reporting",
    "scripts.run_analysis",
    "scripts.awr_memory_cli",
)

FORBIDDEN_FUNCTION_NAMES = (
    "apply_parser_update",
    "apply_parser_mapping",
    "activate_parser_update",
    "modify_parser_config",
    "modify_parser_source",
    "mutate_parser_output",
    "invoke_parser_runtime",
    "classify_unknown_signal",
    "create_parser_mapping",
    "create_parser_candidate",
    "run_analysis",
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


def function_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


class Phase7BVParserRuntimeUpdatePathTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.parser_runtime_update_path")

    def make_package(self, **overrides):
        module = self.module()
        evolution_id = overrides.get("source_parser_evolution_id", "PARSER-EVO-001")
        parser_section = overrides.get("parser_section", "SQL Statistics")
        signal_name = overrides.get("signal_name", "elapsed_time")
        values = {
            "package_id": module.create_parser_runtime_package_id(
                evolution_id,
                parser_section,
                signal_name,
            ),
            "source_parser_evolution_id": evolution_id,
            "source_materialization_id": "MAT-PARSER-001",
            "parser_section": parser_section,
            "signal_name": signal_name,
            "update_type": "field_extraction_review",
            "proposed_change_summary": "Review elapsed time extraction metadata",
            "affected_files": ["src/parser/section_registry.py"],
            "affected_patterns": ["Elapsed Time"],
            "validation_requirements": [
                "parser tests",
                "AWR regression validation",
                "Phase 4I contract validation",
                "scoring regression check",
                "rollback plan",
            ],
            "parser_tests_reference": "parser-tests://phase7bv",
            "awr_regression_reference": "awr-regression://phase7bv",
            "phase4i_validation_reference": "phase4i://phase7bv",
            "scoring_regression_reference": "scoring-regression://phase7bv",
            "rollback_reference": "rollback://phase7bv",
            "package_status": "eligible_for_runtime_review",
            "runtime_eligible": False,
            "runtime_active": False,
            "parser_update_applied": False,
            "parser_output_mutation_performed": False,
            "phase4i_mutation_performed": False,
            "created_by": "unit-test",
            "created_at": "2026-05-16T00:00:00Z",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.ParserRuntimeUpdatePackage(**values)

    def make_manifest(self, package_id=None, **overrides):
        module = self.module()
        package_id = package_id or self.make_package().package_id
        manifest_version = overrides.get("manifest_version", "v1")
        values = {
            "manifest_id": module.create_parser_runtime_manifest_id(
                package_id,
                manifest_version,
            ),
            "package_id": package_id,
            "manifest_version": manifest_version,
            "activation_mode": "manual_review_required",
            "explicit_activation_required": True,
            "validation_reference": "manifest-validation://phase7bv",
            "rollback_reference": "rollback://phase7bv",
            "runtime_gate_reference": "runtime-gate://phase7bv",
            "deterministic_fallback_available": True,
            "phase4i_contract_preserved": True,
            "runtime_activation_requested": False,
            "runtime_activation_approved": False,
            "runtime_active": False,
            "parser_update_applied": False,
            "created_by": "unit-test",
            "created_at": "2026-05-16T00:00:00Z",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.ParserRuntimeUpdateManifest(**values)

    def make_rollback(self, package_id=None, **overrides):
        module = self.module()
        package_id = package_id or self.make_package().package_id
        strategy = overrides.get("rollback_strategy", "restore_current_parser")
        values = {
            "rollback_id": module.create_parser_runtime_rollback_id(
                package_id,
                strategy,
            ),
            "package_id": package_id,
            "rollback_strategy": strategy,
            "rollback_reference": "rollback://phase7bv",
            "rollback_validated": True,
            "rollback_executed": False,
            "parser_update_reverted": False,
            "notes": "rollback metadata only",
        }
        values.update(overrides)
        return module.ParserRuntimeRollbackReference(**values)

    def test_import_safety_no_runtime_imports(self) -> None:
        module = self.module()
        self.assertTrue(hasattr(module, "ParserRuntimeUpdatePackage"))
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
        self.assertTrue(PATH_DOC.is_file(), PATH_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        combined = f"{read_text(PATH_DOC)}\n{read_text(MODEL_DOC)}".lower()
        for phrase in (
            "no parser files are modified",
            "no parser update is applied",
            "no parser output is changed",
            "eligible means metadata eligible, not active",
            "runtime_active=false",
            "parser_update_applied=false",
            "deterministic fallback required",
            "phase 4i preserved",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_supported_update_types_statuses_and_activation_modes(self) -> None:
        module = self.module()
        self.assertEqual(
            set(module.PARSER_RUNTIME_UPDATE_TYPES),
            {
                "new_section_mapping",
                "section_mapping_refinement",
                "unknown_signal_mapping",
                "regex_pattern_review",
                "normalization_rule_review",
                "field_extraction_review",
                "unit_conversion_review",
                "parser_confidence_metadata_review",
                "section_registry_review",
                "parser_regression_test_addition",
            },
        )
        self.assertIn("eligible_for_runtime_review", module.PARSER_RUNTIME_PACKAGE_STATUSES)
        self.assertIn("eligible_metadata_only", module.PARSER_RUNTIME_ELIGIBILITY_STATUSES)
        self.assertEqual(
            set(module.PARSER_RUNTIME_ACTIVATION_MODES),
            {
                "disabled",
                "manual_review_required",
                "future_runtime_manifest",
                "emergency_disabled",
            },
        )

    def test_package_validation(self) -> None:
        module = self.module()
        package = self.make_package()
        self.assertIs(module.validate_parser_runtime_update_package(package), package)
        self.assertFalse(package.runtime_eligible)
        self.assertFalse(package.runtime_active)
        self.assertFalse(package.parser_update_applied)

        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_package(package_status="validation_ready", rollback_reference=None)
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_package(update_type="runtime_parser_patch")

    def test_manifest_validation(self) -> None:
        module = self.module()
        manifest = self.make_manifest()
        self.assertIs(module.validate_parser_runtime_update_manifest(manifest), manifest)
        self.assertTrue(manifest.explicit_activation_required)
        self.assertTrue(manifest.deterministic_fallback_available)
        self.assertTrue(manifest.phase4i_contract_preserved)
        self.assertFalse(manifest.runtime_active)

    def test_eligibility_validation(self) -> None:
        module = self.module()
        package = self.make_package()
        manifest = self.make_manifest(package.package_id)
        record = module.evaluate_parser_runtime_eligibility(package, manifest)
        self.assertIs(module.validate_parser_runtime_eligibility_record(record), record)
        self.assertTrue(record.eligible)
        self.assertEqual("eligible_metadata_only", record.eligibility_status)
        self.assertFalse(record.runtime_active)
        self.assertFalse(record.parser_update_applied)

        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            module.ParserRuntimeEligibilityRecord(
                eligibility_id=record.eligibility_id,
                package_id=record.package_id,
                manifest_id=record.manifest_id,
                eligible=True,
                eligibility_status="eligible_metadata_only",
                required_validation_present=True,
                parser_tests_present=False,
                awr_regression_present=True,
                phase4i_validation_present=True,
                scoring_regression_present=True,
                rollback_reference_present=True,
                runtime_gate_reference_present=True,
                deterministic_fallback_available=True,
            )

    def test_rollback_validation(self) -> None:
        module = self.module()
        rollback = self.make_rollback()
        self.assertIs(
            module.validate_parser_runtime_rollback_reference(rollback),
            rollback,
        )
        self.assertFalse(rollback.rollback_executed)
        self.assertFalse(rollback.parser_update_reverted)

    def test_eligibility_evaluation_missing_references(self) -> None:
        module = self.module()
        manifest = self.make_manifest()

        package = self.make_package(parser_tests_reference=None)
        record = module.evaluate_parser_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_parser_tests", record.eligibility_status)

        package = self.make_package(awr_regression_reference=None)
        record = module.evaluate_parser_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_awr_regression", record.eligibility_status)

        package = self.make_package(phase4i_validation_reference=None)
        record = module.evaluate_parser_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_phase4i_validation", record.eligibility_status)

        package = self.make_package(scoring_regression_reference=None)
        record = module.evaluate_parser_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_scoring_regression", record.eligibility_status)

    def test_eligible_metadata_requires_all_validation_refs(self) -> None:
        module = self.module()
        package = self.make_package()
        manifest = self.make_manifest(package.package_id, runtime_gate_reference=None)
        record = module.evaluate_parser_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_runtime_gate", record.eligibility_status)

        manifest = self.make_manifest(package.package_id, rollback_reference=None)
        record = module.evaluate_parser_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_rollback_reference", record.eligibility_status)

    def test_runtime_active_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_package(runtime_active=True)
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_manifest(runtime_active=True)
        record = module.evaluate_parser_runtime_eligibility(
            self.make_package(),
            self.make_manifest(),
        )
        values = module.parser_runtime_eligibility_record_to_dict(record)
        values["runtime_active"] = True
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            module.parser_runtime_eligibility_record_from_dict(values)

    def test_parser_update_applied_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_package(parser_update_applied=True)
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_manifest(parser_update_applied=True)

    def test_parser_output_mutation_performed_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_package(parser_output_mutation_performed=True)

    def test_phase4i_mutation_performed_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_package(phase4i_mutation_performed=True)

    def test_runtime_activation_requested_or_approved_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_manifest(runtime_activation_requested=True)
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_manifest(runtime_activation_approved=True)

    def test_rollback_executed_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_rollback(rollback_executed=True)
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_rollback(parser_update_reverted=True)

    def test_deterministic_fallback_false_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_manifest(deterministic_fallback_available=False)
        record = module.evaluate_parser_runtime_eligibility(
            self.make_package(),
            self.make_manifest(),
        )
        values = module.parser_runtime_eligibility_record_to_dict(record)
        values["deterministic_fallback_available"] = False
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            module.parser_runtime_eligibility_record_from_dict(values)
        with self.assertRaises(module.ParserRuntimeUpdatePathError):
            self.make_manifest(phase4i_contract_preserved=False)

    def test_serialization_round_trip(self) -> None:
        module = self.module()
        package = self.make_package()
        manifest = self.make_manifest(package.package_id)
        record = module.evaluate_parser_runtime_eligibility(package, manifest)
        rollback = self.make_rollback(package.package_id)

        self.assertEqual(
            package,
            module.parser_runtime_update_package_from_dict(
                module.parser_runtime_update_package_to_dict(package)
            ),
        )
        self.assertEqual(
            manifest,
            module.parser_runtime_update_manifest_from_dict(
                module.parser_runtime_update_manifest_to_dict(manifest)
            ),
        )
        self.assertEqual(
            record,
            module.parser_runtime_eligibility_record_from_dict(
                module.parser_runtime_eligibility_record_to_dict(record)
            ),
        )
        self.assertEqual(
            rollback,
            module.parser_runtime_rollback_reference_from_dict(
                module.parser_runtime_rollback_reference_to_dict(rollback)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        self.assertEqual(
            "PARSER-RUNTIME-PACKAGE-PARSER-EVO-1-SQL-STATISTICS-ELAPSED-TIME",
            module.create_parser_runtime_package_id(
                "PARSER-EVO-1",
                "SQL Statistics",
                "elapsed_time",
            ),
        )
        package_id = module.create_parser_runtime_package_id(
            "PARSER-EVO-1",
            "SQL Statistics",
            "elapsed_time",
        )
        self.assertEqual(
            module.create_parser_runtime_manifest_id(package_id, "v1"),
            module.create_parser_runtime_manifest_id(package_id, "v1"),
        )
        manifest_id = module.create_parser_runtime_manifest_id(package_id, "v1")
        self.assertEqual(
            module.create_parser_runtime_eligibility_id(package_id, manifest_id),
            module.create_parser_runtime_eligibility_id(package_id, manifest_id),
        )
        self.assertEqual(
            module.create_parser_runtime_rollback_id(package_id, "restore_current"),
            module.create_parser_runtime_rollback_id(package_id, "restore_current"),
        )

    def test_no_mutation_or_apply_functions(self) -> None:
        functions = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, functions)


if __name__ == "__main__":
    unittest.main()
