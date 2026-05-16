from __future__ import annotations

import ast
import importlib
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
VALIDATION_DOC = DOCS / "phase7bs_object_storage_config_validation.md"
MODEL_DOC = DOCS / "phase7bs_object_storage_config_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "object_storage_config_validation.py"

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
    "scripts.awr_memory_cli",
    "scripts.run_analysis",
    "oracle_agent_memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "call_object_storage",
    "list_bucket",
    "download_object",
    "validate_credentials",
    "read_config_file",
    "execute_source",
    "run_analysis",
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


class Phase7BSObjectStorageConfigValidationTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.object_storage_config_validation")

    def complete_config(self, **overrides):
        module = self.module()
        values = {
            "config_id": module.create_object_storage_config_id(
                namespace="namespace",
                bucket="bucket",
                object_name="awr/report.html",
                region="us-ashburn-1",
            ),
            "namespace": "namespace",
            "bucket": "bucket",
            "object_name": "awr/report.html",
            "prefix": None,
            "region": "us-ashburn-1",
            "compartment_id": "ocid1.compartment.oc1..example",
            "credential_mode": "config_file",
            "profile_name": "DEFAULT",
            "uri": "oci://bucket/awr/report.html",
            "configured_hint": True,
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.ObjectStorageConfiguration(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "ObjectStorageConfiguration"))
        self.assertTrue(hasattr(module, "ObjectStorageConfigurationValidation"))
        self.assertTrue(hasattr(module, "ObjectStorageConfigurationSummary"))

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
        self.assertTrue(VALIDATION_DOC.is_file(), VALIDATION_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        text = (
            lower_text(VALIDATION_DOC)
            + "\n"
            + lower_text(MODEL_DOC)
            + "\n"
            + lower_text(README)
        )
        for phrase in (
            "no object storage call is made",
            "no credential validation is performed",
            "no bucket listing occurs",
            "no object download occurs",
            "execution_blocked=true in 7bs",
            "credential_validation_performed=false",
            "object_storage_call_performed=false",
            "bucket_list_performed=false",
            "object_download_performed=false",
            "execution_supported=false",
            "handoff_supported=false",
            "em extract belongs to phase 8",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_credential_modes(self) -> None:
        module = self.module()
        self.assertEqual(
            module.OBJECT_STORAGE_CREDENTIAL_MODES,
            (
                "env",
                "instance_principal",
                "resource_principal",
                "config_file",
                "unknown",
            ),
        )
        for credential_mode in module.OBJECT_STORAGE_CREDENTIAL_MODES:
            with self.subTest(credential_mode=credential_mode):
                config = self.complete_config(credential_mode=credential_mode)
                self.assertIs(module.validate_object_storage_configuration(config), config)

        unsupported = self.complete_config(credential_mode="unsupported")
        with self.assertRaises(module.ObjectStorageConfigValidationError):
            module.validate_object_storage_configuration(unsupported)

    def test_secret_field_rejection(self) -> None:
        module = self.module()
        base = module.object_storage_configuration_to_dict(self.complete_config())
        for field_name in module.SECRET_FIELD_NAMES:
            with self.subTest(field_name=field_name):
                data = dict(base)
                data[field_name] = "should-not-be-stored"
                with self.assertRaises(module.ObjectStorageConfigValidationError):
                    module.object_storage_configuration_from_dict(data)

    def test_missing_metadata_status_behavior(self) -> None:
        module = self.module()
        scenarios = (
            ("namespace", None, "MISSING_NAMESPACE"),
            ("bucket", None, "MISSING_BUCKET"),
            ("object_name", None, "MISSING_OBJECT_OR_PREFIX"),
            ("region", None, "MISSING_REGION"),
            ("compartment_id", None, "MISSING_COMPARTMENT"),
        )
        for field_name, value, expected_status in scenarios:
            with self.subTest(field_name=field_name):
                config = self.complete_config(**{field_name: value})
                validation = module.evaluate_object_storage_configuration(config)
                self.assertFalse(validation.valid_metadata)
                self.assertEqual(validation.validation_status, expected_status)
                self.assertTrue(validation.execution_blocked)
                self.assertFalse(validation.can_attempt_future_access)

        prefix_config = self.complete_config(object_name=None, prefix="awr/")
        prefix_validation = module.evaluate_object_storage_configuration(prefix_config)
        self.assertEqual(prefix_validation.validation_status, "VALID_METADATA_ONLY")
        self.assertTrue(prefix_validation.object_or_prefix_present)

    def test_unsupported_credential_mode_status_behavior(self) -> None:
        module = self.module()
        config = self.complete_config(credential_mode="unsupported")
        validation = module.evaluate_object_storage_configuration(config)
        self.assertFalse(validation.valid_metadata)
        self.assertEqual(validation.validation_status, "UNSUPPORTED_CREDENTIAL_MODE")
        self.assertFalse(validation.credential_mode_supported)
        self.assertFalse(validation.can_attempt_future_access)
        self.assertTrue(validation.execution_blocked)

    def test_complete_metadata_valid_metadata_only(self) -> None:
        module = self.module()
        validation = module.evaluate_object_storage_configuration(self.complete_config())
        self.assertTrue(validation.valid_metadata)
        self.assertEqual(validation.validation_status, "VALID_METADATA_ONLY")
        self.assertTrue(validation.namespace_present)
        self.assertTrue(validation.bucket_present)
        self.assertTrue(validation.object_or_prefix_present)
        self.assertTrue(validation.region_present)
        self.assertTrue(validation.compartment_present)
        self.assertTrue(validation.credential_mode_supported)
        self.assertTrue(validation.can_attempt_future_access)
        self.assertTrue(validation.execution_blocked)

    def test_no_real_validation_or_access_flags_are_set(self) -> None:
        module = self.module()
        validation = module.evaluate_object_storage_configuration(self.complete_config())
        self.assertFalse(validation.credential_validation_performed)
        self.assertFalse(validation.object_storage_call_performed)
        self.assertFalse(validation.bucket_list_performed)
        self.assertFalse(validation.object_download_performed)
        self.assertTrue(validation.execution_blocked)

    def test_validation_rejects_unsafe_validation_flags(self) -> None:
        module = self.module()
        safe = module.object_storage_configuration_validation_to_dict(
            module.evaluate_object_storage_configuration(self.complete_config())
        )
        unsafe_values = {
            "credential_validation_performed": True,
            "object_storage_call_performed": True,
            "bucket_list_performed": True,
            "object_download_performed": True,
            "execution_blocked": False,
        }
        for field_name, value in unsafe_values.items():
            with self.subTest(field_name=field_name):
                data = dict(safe)
                data[field_name] = value
                with self.assertRaises(module.ObjectStorageConfigValidationError):
                    module.object_storage_configuration_validation_from_dict(data)

    def test_summary_counts_and_safety_flags(self) -> None:
        module = self.module()
        validations = [
            module.evaluate_object_storage_configuration(self.complete_config()),
            module.evaluate_object_storage_configuration(self.complete_config(namespace=None)),
            module.evaluate_object_storage_configuration(
                self.complete_config(credential_mode="unsupported")
            ),
        ]
        summary = module.build_object_storage_configuration_summary(validations)
        self.assertIs(module.validate_object_storage_configuration_summary(summary), summary)
        self.assertEqual(summary.configured_count, 3)
        self.assertEqual(summary.valid_metadata_count, 1)
        self.assertEqual(summary.incomplete_count, 1)
        self.assertEqual(summary.unsupported_credential_count, 1)
        self.assertFalse(summary.execution_supported)
        self.assertFalse(summary.handoff_supported)
        self.assertFalse(summary.object_storage_call_performed)

        unsafe = module.object_storage_configuration_summary_to_dict(summary)
        for field_name in (
            "execution_supported",
            "handoff_supported",
            "object_storage_call_performed",
        ):
            with self.subTest(field_name=field_name):
                data = dict(unsafe)
                data[field_name] = True
                with self.assertRaises(module.ObjectStorageConfigValidationError):
                    module.object_storage_configuration_summary_from_dict(data)

    def test_serialization_round_trip(self) -> None:
        module = self.module()
        config = self.complete_config()
        config_round_trip = module.object_storage_configuration_from_dict(
            module.object_storage_configuration_to_dict(config)
        )
        self.assertEqual(config_round_trip, config)

        validation = module.evaluate_object_storage_configuration(config)
        validation_round_trip = module.object_storage_configuration_validation_from_dict(
            module.object_storage_configuration_validation_to_dict(validation)
        )
        self.assertEqual(validation_round_trip, validation)

        summary = module.build_object_storage_configuration_summary([validation])
        summary_round_trip = module.object_storage_configuration_summary_from_dict(
            module.object_storage_configuration_summary_to_dict(summary)
        )
        self.assertEqual(summary_round_trip, summary)

    def test_deterministic_ids(self) -> None:
        module = self.module()
        config_id = module.create_object_storage_config_id(
            namespace="namespace",
            bucket="bucket",
            object_name="awr/report.html",
            region="us-ashburn-1",
        )
        self.assertEqual(
            config_id,
            "OBJECT-STORAGE-CONFIG-NAMESPACE-BUCKET-AWR-REPORT-HTML-US-ASHBURN-1",
        )
        self.assertEqual(
            module.create_object_storage_config_validation_id(config_id),
            "OBJECT-STORAGE-CONFIG-VALIDATION-OBJECT-STORAGE-CONFIG-NAMESPACE-BUCKET-AWR-REPORT-HTML-US-ASHBURN-1",
        )
        self.assertEqual(
            module.create_object_storage_config_summary_id(2),
            "OBJECT-STORAGE-CONFIG-SUMMARY-COUNT-2",
        )

    def test_no_execution_or_access_functions_are_defined(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)

    def test_related_source_status_tests_pass(self) -> None:
        completed = subprocess.run(
            ("python3", "-m", "unittest", "tests/test_phase7br_source_status_panel.py"),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )


if __name__ == "__main__":
    unittest.main()
