"""Phase 7BX tests for recommendation runtime activation metadata."""

from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "learning" / "recommendation_runtime_activation.py"
DOCS = ROOT / "docs" / "architecture"
ACTIVATION_DOC = DOCS / "phase7bx_recommendation_runtime_rule_activation.md"
MODEL_DOC = DOCS / "phase7bx_recommendation_runtime_rule_model.md"

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
    "src.recommendation",
    "src.recommendations",
    "src.scoring",
    "src.parser",
    "src.parsing",
    "src.decision",
    "src.reporting",
    "scripts.run_analysis",
    "scripts.awr_memory_cli",
)

FORBIDDEN_FUNCTION_NAMES = (
    "apply_recommendation_rule",
    "activate_recommendation_rule",
    "update_runtime_recommendation",
    "modify_recommendation_catalog",
    "modify_recommendation_ranking",
    "mutate_recommendation_output",
    "invoke_recommendation_runtime",
    "run_recommendation_engine",
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


class Phase7BXRecommendationRuntimeActivationTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.recommendation_runtime_activation")

    def make_package(self, **overrides):
        module = self.module()
        evolution_id = overrides.get(
            "source_recommendation_evolution_id",
            "RECO-EVO-001",
        )
        version = overrides.get("recommendation_rule_version", "v1")
        values = {
            "package_id": module.create_recommendation_runtime_package_id(
                evolution_id,
                version,
            ),
            "source_recommendation_evolution_id": evolution_id,
            "source_materialization_id": "MAT-RECO-001",
            "recommendation_rule_version": version,
            "affected_domains": ["SQL", "Storage"],
            "affected_components": ["priority", "evidence_mapping"],
            "rule_type": "priority",
            "proposed_rule_summary": "Review recommendation priority metadata",
            "wording_changes": {"summary": "metadata-only wording review"},
            "priority_changes": {"from": "medium", "to": "high"},
            "evidence_mapping_changes": {"section": "SQL ordered by Elapsed Time"},
            "action_sequence_changes": {"step": "review_plan_stability"},
            "risk_label_changes": {"risk": "moderate"},
            "suppression_rule_changes": {"suppress_duplicate": True},
            "escalation_rule_changes": {"escalate_if_repeated": True},
            "before_after_reference": "before-after://phase7bx",
            "regression_reference": "regression://phase7bx",
            "evidence_mapping_validation_reference": "evidence-map://phase7bx",
            "action_sequence_validation_reference": "action-sequence://phase7bx",
            "risk_label_validation_reference": "risk-label://phase7bx",
            "phase4i_recommendation_contract_reference": "phase4i-reco://phase7bx",
            "rollback_reference": "rollback://phase7bx",
            "package_status": "eligible_for_runtime_review",
            "runtime_eligible": False,
            "runtime_active": False,
            "recommendation_rule_applied": False,
            "recommendation_output_mutation_performed": False,
            "phase4i_mutation_performed": False,
            "created_by": "unit-test",
            "created_at": "2026-05-16T00:00:00Z",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.RecommendationRuntimeRulePackage(**values)

    def make_manifest(self, package_id=None, **overrides):
        module = self.module()
        package_id = package_id or self.make_package().package_id
        manifest_version = overrides.get("manifest_version", "v1")
        values = {
            "manifest_id": module.create_recommendation_activation_manifest_id(
                package_id,
                manifest_version,
            ),
            "package_id": package_id,
            "manifest_version": manifest_version,
            "activation_mode": "manual_review_required",
            "explicit_activation_required": True,
            "validation_reference": "manifest-validation://phase7bx",
            "rollback_reference": "rollback://phase7bx",
            "runtime_gate_reference": "runtime-gate://phase7bx",
            "deterministic_fallback_available": True,
            "phase4i_recommendation_contract_preserved": True,
            "runtime_activation_requested": False,
            "runtime_activation_approved": False,
            "runtime_active": False,
            "recommendation_rule_applied": False,
            "created_by": "unit-test",
            "created_at": "2026-05-16T00:00:00Z",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.RecommendationActivationManifest(**values)

    def make_rollback(self, package_id=None, **overrides):
        module = self.module()
        package_id = package_id or self.make_package().package_id
        strategy = overrides.get("rollback_strategy", "restore_current_recommendation_rule")
        values = {
            "rollback_id": module.create_recommendation_rollback_id(
                package_id,
                strategy,
            ),
            "package_id": package_id,
            "rollback_strategy": strategy,
            "rollback_reference": "rollback://phase7bx",
            "rollback_validated": True,
            "rollback_executed": False,
            "recommendation_rule_reverted": False,
            "notes": "rollback metadata only",
        }
        values.update(overrides)
        return module.RecommendationRollbackReference(**values)

    def make_regression(self, package_id=None, **overrides):
        module = self.module()
        package_id = package_id or self.make_package().package_id
        reference = overrides.get(
            "test_suite_reference",
            "recommendation-suite://phase7bx",
        )
        values = {
            "regression_id": module.create_recommendation_regression_id(
                package_id,
                reference,
            ),
            "package_id": package_id,
            "test_suite_reference": reference,
            "before_after_reference": "before-after://phase7bx",
            "evidence_mapping_validation_reference": "evidence-map://phase7bx",
            "action_sequence_validation_reference": "action-sequence://phase7bx",
            "risk_label_validation_reference": "risk-label://phase7bx",
            "recommendation_contract_reference": "phase4i-reco://phase7bx",
            "regression_passed": True,
            "evidence_mapping_valid": True,
            "action_sequence_valid": True,
            "risk_label_valid": True,
            "phase4i_contract_preserved": True,
            "notes": "regression metadata only",
        }
        values.update(overrides)
        return module.RecommendationRegressionEvidence(**values)

    def test_import_safety_no_runtime_imports(self) -> None:
        module = self.module()
        self.assertTrue(hasattr(module, "RecommendationRuntimeRulePackage"))
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
        self.assertTrue(ACTIVATION_DOC.is_file(), ACTIVATION_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        combined = f"{read_text(ACTIVATION_DOC)}\n{read_text(MODEL_DOC)}".lower()
        for phrase in (
            "no recommendation modules are modified",
            "no recommendation rule is applied",
            "no recommendation output is changed",
            "eligible means metadata eligible, not active",
            "runtime_active=false",
            "recommendation_rule_applied=false",
            "deterministic fallback required",
            "phase 4i recommendation contract preserved",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_supported_statuses_activation_modes_and_rule_types(self) -> None:
        module = self.module()
        self.assertIn(
            "eligible_for_runtime_review",
            module.RECOMMENDATION_RUNTIME_PACKAGE_STATUSES,
        )
        self.assertIn(
            "eligible_metadata_only",
            module.RECOMMENDATION_RUNTIME_ELIGIBILITY_STATUSES,
        )
        self.assertEqual(
            set(module.RECOMMENDATION_RUNTIME_ACTIVATION_MODES),
            {
                "disabled",
                "manual_review_required",
                "future_runtime_manifest",
                "emergency_disabled",
            },
        )
        self.assertEqual(
            set(module.RECOMMENDATION_RULE_TYPES),
            {
                "wording",
                "priority",
                "domain_mapping",
                "suppression",
                "action_sequence",
                "risk_label",
                "evidence_mapping",
                "category",
                "confidence_wording",
                "escalation",
                "unknown",
            },
        )

    def test_package_validation(self) -> None:
        module = self.module()
        package = self.make_package()
        self.assertIs(
            module.validate_recommendation_runtime_rule_package(package),
            package,
        )
        self.assertFalse(package.runtime_eligible)
        self.assertFalse(package.runtime_active)
        self.assertFalse(package.recommendation_rule_applied)

        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_package(package_status="regression_ready", rollback_reference=None)
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_package(rule_type="runtime_patch")

    def test_manifest_validation(self) -> None:
        module = self.module()
        manifest = self.make_manifest()
        self.assertIs(module.validate_recommendation_activation_manifest(manifest), manifest)
        self.assertTrue(manifest.explicit_activation_required)
        self.assertTrue(manifest.deterministic_fallback_available)
        self.assertTrue(manifest.phase4i_recommendation_contract_preserved)
        self.assertFalse(manifest.runtime_active)

    def test_eligibility_validation(self) -> None:
        module = self.module()
        package = self.make_package()
        manifest = self.make_manifest(package.package_id)
        record = module.evaluate_recommendation_runtime_eligibility(package, manifest)
        self.assertIs(
            module.validate_recommendation_runtime_eligibility_record(record),
            record,
        )
        self.assertTrue(record.eligible)
        self.assertEqual("eligible_metadata_only", record.eligibility_status)
        self.assertFalse(record.runtime_active)
        self.assertFalse(record.recommendation_rule_applied)

        with self.assertRaises(module.RecommendationRuntimeActivationError):
            module.RecommendationRuntimeEligibilityRecord(
                eligibility_id=record.eligibility_id,
                package_id=record.package_id,
                manifest_id=record.manifest_id,
                eligible=True,
                eligibility_status="eligible_metadata_only",
                required_validation_present=True,
                regression_reference_present=False,
                before_after_reference_present=True,
                evidence_mapping_validation_present=True,
                action_sequence_validation_present=True,
                risk_label_validation_present=True,
                phase4i_recommendation_contract_reference_present=True,
                rollback_reference_present=True,
                runtime_gate_reference_present=True,
                deterministic_fallback_available=True,
            )

    def test_rollback_validation(self) -> None:
        module = self.module()
        rollback = self.make_rollback()
        self.assertIs(
            module.validate_recommendation_rollback_reference(rollback),
            rollback,
        )
        self.assertFalse(rollback.rollback_executed)
        self.assertFalse(rollback.recommendation_rule_reverted)

    def test_regression_evidence_validation(self) -> None:
        module = self.module()
        evidence = self.make_regression()
        self.assertIs(
            module.validate_recommendation_regression_evidence(evidence),
            evidence,
        )
        self.assertTrue(evidence.regression_passed)
        self.assertTrue(evidence.evidence_mapping_valid)
        self.assertTrue(evidence.action_sequence_valid)
        self.assertTrue(evidence.risk_label_valid)
        self.assertTrue(evidence.phase4i_contract_preserved)

    def test_eligibility_evaluation_missing_references(self) -> None:
        module = self.module()
        manifest = self.make_manifest()

        package = self.make_package(regression_reference=None)
        record = module.evaluate_recommendation_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_regression_reference", record.eligibility_status)

        package = self.make_package(before_after_reference=None)
        record = module.evaluate_recommendation_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_before_after_reference", record.eligibility_status)

        package = self.make_package(evidence_mapping_validation_reference=None)
        record = module.evaluate_recommendation_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual(
            "needs_evidence_mapping_validation",
            record.eligibility_status,
        )

    def test_eligible_metadata_requires_all_validation_refs(self) -> None:
        module = self.module()
        manifest = self.make_manifest()

        package = self.make_package(action_sequence_validation_reference=None)
        record = module.evaluate_recommendation_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_action_sequence_validation", record.eligibility_status)

        package = self.make_package(risk_label_validation_reference=None)
        record = module.evaluate_recommendation_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual("needs_risk_label_validation", record.eligibility_status)

        package = self.make_package(phase4i_recommendation_contract_reference=None)
        record = module.evaluate_recommendation_runtime_eligibility(package, manifest)
        self.assertFalse(record.eligible)
        self.assertEqual(
            "needs_phase4i_recommendation_contract",
            record.eligibility_status,
        )

    def test_evidence_mapping_valid_false_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_regression(evidence_mapping_valid=False)

    def test_action_sequence_valid_false_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_regression(action_sequence_valid=False)

    def test_risk_label_valid_false_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_regression(risk_label_valid=False)

    def test_runtime_active_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_package(runtime_active=True)
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_manifest(runtime_active=True)
        record = module.evaluate_recommendation_runtime_eligibility(
            self.make_package(),
            self.make_manifest(),
        )
        values = module.recommendation_runtime_eligibility_record_to_dict(record)
        values["runtime_active"] = True
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            module.recommendation_runtime_eligibility_record_from_dict(values)

    def test_recommendation_rule_applied_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_package(recommendation_rule_applied=True)
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_manifest(recommendation_rule_applied=True)

    def test_recommendation_output_mutation_performed_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_package(recommendation_output_mutation_performed=True)

    def test_phase4i_mutation_performed_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_package(phase4i_mutation_performed=True)

    def test_runtime_activation_requested_or_approved_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_manifest(runtime_activation_requested=True)
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_manifest(runtime_activation_approved=True)

    def test_rollback_executed_true_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_rollback(rollback_executed=True)
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_rollback(recommendation_rule_reverted=True)

    def test_deterministic_fallback_false_fails(self) -> None:
        module = self.module()
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_manifest(deterministic_fallback_available=False)
        record = module.evaluate_recommendation_runtime_eligibility(
            self.make_package(),
            self.make_manifest(),
        )
        values = module.recommendation_runtime_eligibility_record_to_dict(record)
        values["deterministic_fallback_available"] = False
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            module.recommendation_runtime_eligibility_record_from_dict(values)
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_manifest(phase4i_recommendation_contract_preserved=False)
        with self.assertRaises(module.RecommendationRuntimeActivationError):
            self.make_regression(phase4i_contract_preserved=False)

    def test_serialization_round_trip(self) -> None:
        module = self.module()
        package = self.make_package()
        manifest = self.make_manifest(package.package_id)
        record = module.evaluate_recommendation_runtime_eligibility(package, manifest)
        rollback = self.make_rollback(package.package_id)
        evidence = self.make_regression(package.package_id)

        self.assertEqual(
            package,
            module.recommendation_runtime_rule_package_from_dict(
                module.recommendation_runtime_rule_package_to_dict(package)
            ),
        )
        self.assertEqual(
            manifest,
            module.recommendation_activation_manifest_from_dict(
                module.recommendation_activation_manifest_to_dict(manifest)
            ),
        )
        self.assertEqual(
            record,
            module.recommendation_runtime_eligibility_record_from_dict(
                module.recommendation_runtime_eligibility_record_to_dict(record)
            ),
        )
        self.assertEqual(
            rollback,
            module.recommendation_rollback_reference_from_dict(
                module.recommendation_rollback_reference_to_dict(rollback)
            ),
        )
        self.assertEqual(
            evidence,
            module.recommendation_regression_evidence_from_dict(
                module.recommendation_regression_evidence_to_dict(evidence)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        package_id = module.create_recommendation_runtime_package_id(
            "RECO-EVO-1",
            "v1",
        )
        self.assertEqual(
            "RECOMMENDATION-RUNTIME-PACKAGE-RECO-EVO-1-V1",
            package_id,
        )
        self.assertEqual(
            module.create_recommendation_activation_manifest_id(package_id, "v1"),
            module.create_recommendation_activation_manifest_id(package_id, "v1"),
        )
        manifest_id = module.create_recommendation_activation_manifest_id(
            package_id,
            "v1",
        )
        self.assertEqual(
            module.create_recommendation_runtime_eligibility_id(
                package_id,
                manifest_id,
            ),
            module.create_recommendation_runtime_eligibility_id(
                package_id,
                manifest_id,
            ),
        )
        self.assertEqual(
            module.create_recommendation_rollback_id(package_id, "restore_current"),
            module.create_recommendation_rollback_id(package_id, "restore_current"),
        )
        self.assertEqual(
            module.create_recommendation_regression_id(package_id, "suite-1"),
            module.create_recommendation_regression_id(package_id, "suite-1"),
        )

    def test_no_mutation_or_apply_functions(self) -> None:
        functions = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, functions)


if __name__ == "__main__":
    unittest.main()
