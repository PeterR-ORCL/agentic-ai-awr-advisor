"""Phase 7BY tests for ML runtime eligibility metadata."""

from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "learning" / "ml_runtime_eligibility.py"
DOCS = ROOT / "docs" / "architecture"
ELIGIBILITY_DOC = DOCS / "phase7by_ml_runtime_eligibility.md"
MODEL_DOC = DOCS / "phase7by_ml_runtime_manifest_model.md"

FORBIDDEN_IMPORT_PREFIXES = (
    "sklearn",
    "tensorflow",
    "torch",
    "xgboost",
    "lightgbm",
    "catboost",
    "numpy",
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
    "src.scoring",
    "src.parser",
    "src.parsing",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.reporting",
    "scripts.run_analysis",
    "scripts.awr_memory_cli",
)

FORBIDDEN_FUNCTION_NAMES = (
    "deploy_model",
    "activate_model",
    "load_model",
    "save_model",
    "run_ml_inference",
    "replace_runtime_scoring",
    "replace_scoring_engine",
    "grant_runtime_eligibility",
    "grant_runtime_influence",
    "update_runtime_scoring",
    "apply_model",
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


class Phase7BYMLRuntimeEligibilityTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.ml_runtime_eligibility")

    def make_package(self, **overrides):
        module = self.module()
        model_id = overrides.get("model_id", "ML-MODEL-001")
        model_version = overrides.get("model_version", "v1")
        values = {
            "package_id": module.create_ml_runtime_package_id(
                model_id,
                model_version,
            ),
            "model_id": model_id,
            "model_family": "tree",
            "model_version": model_version,
            "registry_entry_id": "REGISTRY-ML-001",
            "training_reference": "training://phase7by",
            "backtest_reference": "backtest://phase7by",
            "explainability_reference": "explainability://phase7by",
            "validation_reference": "validation://phase7by",
            "dataset_reference": "dataset://phase7by",
            "feature_schema_version": "features-v1",
            "label_schema_version": "labels-v1",
            "deterministic_comparison_reference": "deterministic://phase7by",
            "drift_review_reference": "drift://phase7by",
            "rollback_reference": "rollback://phase7by",
            "monitoring_reference": "monitoring://phase7by",
            "eligibility_status": "eligible_metadata_only",
            "runtime_eligible": False,
            "runtime_active": False,
            "runtime_influence_granted": False,
            "runtime_eligibility_granted": False,
            "model_deployed": False,
            "model_loaded": False,
            "model_saved": False,
            "runtime_scoring_replaced": False,
            "phase4i_mutation_performed": False,
            "created_by": "unit-test",
            "created_at": "2026-05-16T00:00:00Z",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.MLRuntimeEligibilityPackage(**values)

    def make_manifest(self, package_id=None, **overrides):
        module = self.module()
        package_id = package_id or self.make_package().package_id
        manifest_version = overrides.get("manifest_version", "v1")
        values = {
            "manifest_id": module.create_ml_runtime_manifest_id(
                package_id,
                manifest_version,
            ),
            "package_id": package_id,
            "manifest_version": manifest_version,
            "activation_mode": "manual_review_required",
            "explicit_activation_required": True,
            "validation_reference": "manifest-validation://phase7by",
            "rollback_reference": "rollback://phase7by",
            "runtime_gate_reference": "runtime-gate://phase7by",
            "monitoring_reference": "monitoring://phase7by",
            "deterministic_fallback_available": True,
            "phase4i_contract_preserved": True,
            "runtime_activation_requested": False,
            "runtime_activation_approved": False,
            "runtime_active": False,
            "model_deployed": False,
            "runtime_scoring_replaced": False,
            "created_by": "unit-test",
            "created_at": "2026-05-16T00:00:00Z",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.MLRuntimeActivationManifest(**values)

    def make_fallback(self, package_id=None, **overrides):
        module = self.module()
        package_id = package_id or self.make_package().package_id
        strategy = overrides.get("fallback_strategy", "deterministic_scoring_only")
        values = {
            "fallback_id": module.create_ml_runtime_fallback_id(
                package_id,
                strategy,
            ),
            "package_id": package_id,
            "fallback_strategy": strategy,
            "deterministic_scoring_fallback": True,
            "disable_model_fallback": True,
            "rollback_reference": "rollback://phase7by",
            "fallback_validated": True,
            "fallback_executed": False,
            "model_disabled": False,
            "runtime_scoring_reverted": False,
            "notes": "fallback metadata only",
        }
        values.update(overrides)
        return module.MLRuntimeFallbackPlan(**values)

    def make_monitoring(self, package_id=None, **overrides):
        module = self.module()
        package_id = package_id or self.make_package().package_id
        strategy = overrides.get("monitoring_strategy", "shadow_drift_review")
        values = {
            "monitoring_id": module.create_ml_runtime_monitoring_id(
                package_id,
                strategy,
            ),
            "package_id": package_id,
            "monitoring_strategy": strategy,
            "drift_monitoring_required": True,
            "performance_monitoring_required": True,
            "confidence_monitoring_required": True,
            "fallback_trigger_defined": True,
            "monitoring_active": False,
            "runtime_active": False,
            "notes": "monitoring metadata only",
        }
        values.update(overrides)
        return module.MLRuntimeMonitoringPlan(**values)

    def make_regression(self, package_id=None, **overrides):
        module = self.module()
        package_id = package_id or self.make_package().package_id
        reference = overrides.get("backtest_reference", "backtest://phase7by")
        values = {
            "regression_id": module.create_ml_runtime_regression_id(
                package_id,
                reference,
            ),
            "package_id": package_id,
            "backtest_reference": reference,
            "explainability_reference": "explainability://phase7by",
            "deterministic_comparison_reference": "deterministic://phase7by",
            "validation_reference": "validation://phase7by",
            "regression_passed": True,
            "backtesting_passed": True,
            "explainability_present": True,
            "deterministic_comparison_acceptable": True,
            "phase4i_contract_preserved": True,
            "notes": "regression metadata only",
        }
        values.update(overrides)
        return module.MLRuntimeRegressionEvidence(**values)

    def test_import_safety_no_ml_or_runtime_imports(self) -> None:
        module = self.module()
        self.assertTrue(hasattr(module, "MLRuntimeEligibilityPackage"))
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
        self.assertTrue(ELIGIBILITY_DOC.is_file(), ELIGIBILITY_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        combined = f"{read_text(ELIGIBILITY_DOC)}\n{read_text(MODEL_DOC)}".lower()
        for phrase in (
            "no model is deployed",
            "no model is loaded/saved",
            "no runtime scoring is replaced",
            "eligible means metadata eligible, not active",
            "runtime_active=false",
            "runtime_eligibility_granted=false",
            "runtime_influence_granted=false",
            "deterministic fallback required",
            "phase 4i preserved",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_supported_statuses_activation_modes_and_model_families(self) -> None:
        module = self.module()
        self.assertIn("eligible_metadata_only", module.ML_RUNTIME_ELIGIBILITY_STATUSES)
        self.assertIn("needs_runtime_gate", module.ML_RUNTIME_ELIGIBILITY_STATUSES)
        self.assertEqual(
            set(module.ML_RUNTIME_ACTIVATION_MODES),
            {
                "disabled",
                "shadow_only",
                "manual_review_required",
                "future_runtime_manifest",
                "emergency_disabled",
            },
        )
        self.assertEqual(
            set(module.ML_RUNTIME_MODEL_FAMILIES),
            {
                "tree",
                "neural_net",
                "hybrid_rule_ml",
                "linear",
                "baseline_mock",
                "baseline_majority",
                "baseline_numeric_mean",
                "shadow_placeholder",
                "external_placeholder",
                "unknown",
            },
        )

    def test_package_validation(self) -> None:
        module = self.module()
        package = self.make_package()
        self.assertIs(module.validate_ml_runtime_eligibility_package(package), package)
        self.assertFalse(package.runtime_eligible)
        self.assertFalse(package.runtime_active)
        self.assertFalse(package.runtime_influence_granted)
        self.assertFalse(package.runtime_eligibility_granted)

        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(model_family="unsupported")
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(runtime_eligible=True, backtest_reference=None)

    def test_manifest_validation(self) -> None:
        module = self.module()
        manifest = self.make_manifest()
        self.assertIs(module.validate_ml_runtime_activation_manifest(manifest), manifest)
        self.assertTrue(manifest.explicit_activation_required)
        self.assertTrue(manifest.deterministic_fallback_available)
        self.assertTrue(manifest.phase4i_contract_preserved)
        self.assertFalse(manifest.runtime_active)

    def test_eligibility_validation(self) -> None:
        module = self.module()
        package = self.make_package()
        manifest = self.make_manifest(package.package_id)
        record = module.evaluate_ml_runtime_eligibility(package, manifest)
        self.assertIs(module.validate_ml_runtime_eligibility_record(record), record)
        self.assertTrue(record.eligible)
        self.assertEqual("eligible_metadata_only", record.eligibility_status)
        self.assertFalse(record.runtime_active)
        self.assertFalse(record.runtime_eligibility_granted)
        self.assertFalse(record.runtime_influence_granted)

        with self.assertRaises(module.MLRuntimeEligibilityError):
            module.MLRuntimeEligibilityRecord(
                eligibility_id=record.eligibility_id,
                package_id=record.package_id,
                manifest_id=record.manifest_id,
                eligible=True,
                eligibility_status="eligible_metadata_only",
                registry_reference_present=True,
                training_reference_present=True,
                backtest_reference_present=False,
                explainability_reference_present=True,
                validation_reference_present=True,
                deterministic_comparison_reference_present=True,
                drift_review_reference_present=True,
                rollback_reference_present=True,
                monitoring_reference_present=True,
                runtime_gate_reference_present=True,
                deterministic_fallback_available=True,
                phase4i_contract_preserved=True,
            )

    def test_fallback_plan_validation(self) -> None:
        module = self.module()
        fallback = self.make_fallback()
        self.assertIs(module.validate_ml_runtime_fallback_plan(fallback), fallback)
        self.assertTrue(fallback.deterministic_scoring_fallback)
        self.assertTrue(fallback.disable_model_fallback)
        self.assertFalse(fallback.fallback_executed)

    def test_monitoring_plan_validation(self) -> None:
        module = self.module()
        monitoring = self.make_monitoring()
        self.assertIs(module.validate_ml_runtime_monitoring_plan(monitoring), monitoring)
        self.assertTrue(monitoring.drift_monitoring_required)
        self.assertFalse(monitoring.monitoring_active)
        self.assertFalse(monitoring.runtime_active)

    def test_regression_evidence_validation(self) -> None:
        module = self.module()
        evidence = self.make_regression()
        self.assertIs(module.validate_ml_runtime_regression_evidence(evidence), evidence)
        self.assertTrue(evidence.regression_passed)
        self.assertTrue(evidence.phase4i_contract_preserved)

        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_regression(regression_passed=True, explainability_present=False)

    def test_eligibility_evaluation(self) -> None:
        module = self.module()
        package = self.make_package()
        manifest = self.make_manifest(package.package_id)
        record = module.evaluate_ml_runtime_eligibility(package, manifest)
        self.assertTrue(record.eligible)
        self.assertEqual("eligible_metadata_only", record.eligibility_status)
        self.assertTrue(record.registry_reference_present)
        self.assertTrue(record.runtime_gate_reference_present)

        record = module.evaluate_ml_runtime_eligibility(
            self.make_package(backtest_reference=None),
            manifest,
        )
        self.assertFalse(record.eligible)
        self.assertEqual("needs_backtest_reference", record.eligibility_status)

    def test_eligible_metadata_requires_all_validation_refs(self) -> None:
        module = self.module()
        package = self.make_package()
        manifest = self.make_manifest(package.package_id, runtime_gate_reference=None)
        record = module.evaluate_ml_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_runtime_gate", record.eligibility_status)

    def test_runtime_active_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(runtime_active=True)
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_manifest(runtime_active=True)

    def test_runtime_eligibility_granted_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(runtime_eligibility_granted=True)

    def test_runtime_influence_granted_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(runtime_influence_granted=True)

    def test_model_deployed_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(model_deployed=True)
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_manifest(model_deployed=True)

    def test_model_loaded_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(model_loaded=True)

    def test_model_saved_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(model_saved=True)

    def test_runtime_scoring_replaced_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(runtime_scoring_replaced=True)
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_manifest(runtime_scoring_replaced=True)

    def test_phase4i_mutation_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_package(phase4i_mutation_performed=True)

    def test_fallback_executed_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_fallback(fallback_executed=True)
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_fallback(model_disabled=True)
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_fallback(runtime_scoring_reverted=True)

    def test_monitoring_active_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_monitoring(monitoring_active=True)

    def test_deterministic_fallback_false_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_manifest(deterministic_fallback_available=False)
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_fallback(deterministic_scoring_fallback=False)

    def test_phase4i_contract_false_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_manifest(phase4i_contract_preserved=False)
        with self.assertRaises(module.MLRuntimeEligibilityError):
            self.make_regression(phase4i_contract_preserved=False)

    def test_serialization(self) -> None:
        module = self.module()
        package = self.make_package()
        manifest = self.make_manifest(package.package_id)
        record = module.evaluate_ml_runtime_eligibility(package, manifest)
        fallback = self.make_fallback(package.package_id)
        monitoring = self.make_monitoring(package.package_id)
        evidence = self.make_regression(package.package_id)

        self.assertEqual(
            module.ml_runtime_eligibility_package_from_dict(
                module.ml_runtime_eligibility_package_to_dict(package)
            ),
            package,
        )
        self.assertEqual(
            module.ml_runtime_activation_manifest_from_dict(
                module.ml_runtime_activation_manifest_to_dict(manifest)
            ),
            manifest,
        )
        self.assertEqual(
            module.ml_runtime_eligibility_record_from_dict(
                module.ml_runtime_eligibility_record_to_dict(record)
            ),
            record,
        )
        self.assertEqual(
            module.ml_runtime_fallback_plan_from_dict(
                module.ml_runtime_fallback_plan_to_dict(fallback)
            ),
            fallback,
        )
        self.assertEqual(
            module.ml_runtime_monitoring_plan_from_dict(
                module.ml_runtime_monitoring_plan_to_dict(monitoring)
            ),
            monitoring,
        )
        self.assertEqual(
            module.ml_runtime_regression_evidence_from_dict(
                module.ml_runtime_regression_evidence_to_dict(evidence)
            ),
            evidence,
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        package_id = module.create_ml_runtime_package_id("model 1", "v1")
        self.assertEqual(package_id, module.create_ml_runtime_package_id("model 1", "v1"))
        self.assertEqual("ML-RUNTIME-PACKAGE-MODEL-1-V1", package_id)
        manifest_id = module.create_ml_runtime_manifest_id(package_id, "v1")
        self.assertEqual(
            manifest_id,
            module.create_ml_runtime_manifest_id(package_id, "v1"),
        )
        self.assertEqual(
            module.create_ml_runtime_eligibility_id(package_id, manifest_id),
            module.create_ml_runtime_eligibility_id(package_id, manifest_id),
        )
        self.assertEqual(
            module.create_ml_runtime_fallback_id(package_id, "deterministic fallback"),
            "ML-RUNTIME-FALLBACK-ML-RUNTIME-PACKAGE-MODEL-1-V1-DETERMINISTIC-FALLBACK",
        )
        self.assertEqual(
            module.create_ml_runtime_monitoring_id(package_id, "drift monitoring"),
            "ML-RUNTIME-MONITORING-ML-RUNTIME-PACKAGE-MODEL-1-V1-DRIFT-MONITORING",
        )
        self.assertEqual(
            module.create_ml_runtime_regression_id(package_id, "backtest ref"),
            "ML-RUNTIME-REGRESSION-ML-RUNTIME-PACKAGE-MODEL-1-V1-BACKTEST-REF",
        )

    def test_no_mutation_deploy_or_load_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
