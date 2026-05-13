from __future__ import annotations

import ast
import importlib
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
REGISTRY_DOC = DOCS / "phase7_ml_model_registry.md"
MODEL_DOC = DOCS / "phase7_ml_governance_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "ml_model_registry.py"

RUNTIME_PATHS = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "oracledb",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "sklearn",
    "tensorflow",
    "torch",
    "xgboost",
    "lightgbm",
    "catboost",
    "numpy",
    "sqlite3",
    "src.parser",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.reporting",
    "src.memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "deploy_model",
    "activate_model",
    "load_model",
    "save_model",
    "update_runtime_scoring",
    "replace_scoring_engine",
    "grant_runtime_eligibility",
    "auto_apply",
    "autonomous_apply",
)

REQUIRED_MODEL_FAMILIES = (
    "tree",
    "neural_net",
    "hybrid_rule_ml",
    "linear",
    "baseline_mock",
    "baseline_majority",
    "baseline_numeric_mean",
    "shadow_placeholder",
    "external_placeholder",
)

EXPECTED_DECISION_TRANSITIONS = {
    "register": "REGISTERED",
    "mark-trained": "TRAINED",
    "mark-backtested": "BACKTESTED",
    "attach-explainability": "EXPLAINED",
    "approve-for-shadow": "APPROVED_FOR_SHADOW",
    "request-runtime-review": "APPROVED_FOR_RUNTIME_REVIEW",
    "reject": "REJECTED",
    "retire": "RETIRED",
    "close": "CLOSED",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def python_files(paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
    return files


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
            imports.update(f"{node.module}.{alias.name}" for alias in node.names)
    return imports


def function_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


class Phase7MLModelRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.ml_model_registry")

    def entry(self, **overrides):
        module = self.module
        values = {
            "model_family": "baseline_mock",
            "model_version": "7Y.1",
            "model_name": "phase7y_baseline",
            "feature_schema_version": "7T.1",
            "label_schema_version": "7T.1",
            "training_dataset_id": "DATASET-7T-SAMPLE",
            "training_reference": "training://phase7w/baseline",
            "backtest_reference": "backtest://phase7w/baseline",
            "explainability_reference": "explainability://phase7x/baseline",
            "validation_metrics": {"accuracy": 0.75, "disagreement_rate": 0.12},
            "created_by": "unit-test",
            "notes": "governance metadata only",
        }
        values.update(overrides)
        return module.create_model_registry_entry(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.ml_model_registry")
        self.assertEqual(before_environment, dict(os.environ))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )
        self.assertNotIn("uuid", imports)
        self.assertNotIn("datetime", imports)
        self.assertNotIn("time", imports)
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertFalse(hasattr(module, forbidden_name))

    def test_docs_exist(self) -> None:
        self.assertTrue(REGISTRY_DOC.is_file(), REGISTRY_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{read_text(REGISTRY_DOC)}\n{read_text(MODEL_DOC)}"
        lower = combined.lower()
        for phrase in (
            "registry is governance metadata only",
            "model registry does not deploy models",
            "model approval does not activate runtime scoring",
            "approved_for_runtime_review is not runtime active",
            "runtime_eligibility_granted=false",
            "runtime_active=false",
            "runtime_influence_granted=false",
            "deterministic scoring remains authoritative",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

    def test_supported_model_families(self) -> None:
        module = self.module
        self.assertEqual(set(REQUIRED_MODEL_FAMILIES), set(module.MODEL_REGISTRY_FAMILIES))
        for family in REQUIRED_MODEL_FAMILIES:
            with self.subTest(family=family):
                entry = self.entry(model_family=family)
                self.assertEqual(entry.model_family, family)
        with self.assertRaises(module.MLModelRegistryError):
            self.entry(model_family="unsupported_family")

    def test_registry_entry_validation(self) -> None:
        module = self.module
        entry = module.validate_model_registry_entry(self.entry())
        self.assertEqual(entry.governance_status, "PROPOSED")
        self.assertFalse(entry.runtime_active)
        self.assertFalse(entry.runtime_influence_granted)
        self.assertFalse(entry.runtime_eligibility_granted)

        entry_dict = module.model_registry_entry_to_dict(entry)
        for field_name in (
            "runtime_active",
            "runtime_influence_granted",
            "runtime_eligibility_granted",
        ):
            with self.subTest(field_name=field_name):
                invalid = dict(entry_dict)
                invalid[field_name] = True
                with self.assertRaises(module.MLModelRegistryError):
                    module.model_registry_entry_from_dict(invalid)

        invalid = dict(entry_dict)
        invalid["model_family"] = "deep_magic"
        with self.assertRaises(module.MLModelRegistryError):
            module.model_registry_entry_from_dict(invalid)

        invalid = dict(entry_dict)
        invalid["governance_status"] = "DEPLOYED"
        with self.assertRaises(module.MLModelRegistryError):
            module.model_registry_entry_from_dict(invalid)

        invalid = dict(entry_dict)
        invalid["shadow_eligible"] = True
        invalid["governance_status"] = "TRAINED"
        with self.assertRaises(module.MLModelRegistryError):
            module.model_registry_entry_from_dict(invalid)

        invalid = dict(entry_dict)
        invalid["retired"] = True
        invalid["governance_status"] = "APPROVED_FOR_SHADOW"
        with self.assertRaises(module.MLModelRegistryError):
            module.model_registry_entry_from_dict(invalid)

        invalid = dict(entry_dict)
        invalid["validation_metrics"] = {"accuracy": "high"}
        with self.assertRaises(module.MLModelRegistryError):
            module.model_registry_entry_from_dict(invalid)

    def test_governance_decision_transitions(self) -> None:
        module = self.module
        base_entry = self.entry()
        for decision_type, expected_status in EXPECTED_DECISION_TRANSITIONS.items():
            with self.subTest(decision_type=decision_type):
                updated, decision = module.create_governance_decision(
                    base_entry,
                    decision_type,
                    actor="reviewer@example.com",
                    review_notes="reviewed locally",
                    validation_reference="validation://unit-test",
                )
                self.assertEqual(updated.governance_status, expected_status)
                self.assertEqual(decision.to_status, expected_status)
                self.assertEqual(decision.from_status, "PROPOSED")
                self.assertEqual(decision.decision_type, decision_type)
                self.assertFalse(decision.runtime_active)
                self.assertFalse(decision.runtime_eligibility_granted)
                self.assertFalse(updated.runtime_active)
                self.assertFalse(updated.runtime_eligibility_granted)
                self.assertFalse(updated.runtime_influence_granted)
                expected_id = module.create_governance_decision_id(
                    base_entry.model_id,
                    decision_type,
                    "PROPOSED",
                    expected_status,
                )
                self.assertEqual(decision.decision_id, expected_id)

        with self.assertRaises(module.MLModelRegistryError):
            module.create_governance_decision(base_entry, "register", actor=" ")

        invalid_id = module.create_governance_decision_id(
            base_entry.model_id,
            "register",
            "PROPOSED",
            "TRAINED",
        )
        with self.assertRaises(module.MLModelRegistryError):
            module.MLModelGovernanceDecision(
                decision_id=invalid_id,
                model_id=base_entry.model_id,
                from_status="PROPOSED",
                to_status="TRAINED",
                decision_type="register",
                actor="reviewer@example.com",
                review_notes=None,
                validation_reference=None,
                runtime_eligibility_requested=False,
                runtime_eligibility_granted=False,
                runtime_active=False,
                created_at=None,
            )

    def test_request_runtime_review_does_not_grant_runtime_eligibility(self) -> None:
        module = self.module
        updated, decision = module.create_governance_decision(
            self.entry(),
            "request-runtime-review",
            actor="reviewer@example.com",
        )
        self.assertEqual(updated.governance_status, "APPROVED_FOR_RUNTIME_REVIEW")
        self.assertTrue(updated.runtime_eligibility_requested)
        self.assertTrue(decision.runtime_eligibility_requested)
        self.assertTrue(updated.shadow_eligible)
        self.assertFalse(updated.runtime_eligibility_granted)
        self.assertFalse(decision.runtime_eligibility_granted)
        self.assertFalse(updated.runtime_active)
        self.assertFalse(decision.runtime_active)

    def test_approve_for_shadow_sets_shadow_only_eligibility(self) -> None:
        module = self.module
        updated, decision = module.create_governance_decision(
            self.entry(),
            "approve-for-shadow",
            actor="reviewer@example.com",
        )
        self.assertEqual(updated.governance_status, "APPROVED_FOR_SHADOW")
        self.assertTrue(updated.shadow_eligible)
        self.assertFalse(updated.runtime_active)
        self.assertFalse(updated.runtime_eligibility_granted)
        self.assertFalse(updated.runtime_influence_granted)
        self.assertFalse(decision.runtime_active)
        self.assertFalse(decision.runtime_eligibility_granted)

    def test_eligibility_records(self) -> None:
        module = self.module
        shadow_entry, _ = module.create_governance_decision(
            self.entry(),
            "approve-for-shadow",
            actor="reviewer@example.com",
        )
        shadow_record = module.create_model_eligibility_record(
            shadow_entry,
            "shadow",
            validation_reference="validation://shadow",
            rollback_reference="rollback://previous",
        )
        self.assertEqual(shadow_record.eligibility_type, "shadow")
        self.assertTrue(shadow_record.shadow_eligible)
        self.assertFalse(shadow_record.runtime_eligible)
        self.assertFalse(shadow_record.runtime_active)
        self.assertFalse(shadow_record.runtime_influence_granted)

        runtime_review_entry, _ = module.create_governance_decision(
            self.entry(),
            "request-runtime-review",
            actor="reviewer@example.com",
        )
        runtime_review_record = module.create_model_eligibility_record(
            runtime_review_entry,
            "runtime_review",
            validation_reference="validation://runtime-review",
        )
        self.assertEqual(runtime_review_record.eligibility_type, "runtime_review")
        self.assertFalse(runtime_review_record.runtime_eligible)
        self.assertFalse(runtime_review_record.runtime_active)
        self.assertFalse(runtime_review_record.runtime_influence_granted)

        with self.assertRaises(module.MLModelRegistryError):
            module.create_model_eligibility_record(shadow_entry, "runtime-active")

        invalid = module.model_eligibility_record_to_dict(shadow_record)
        invalid["runtime_eligible"] = True
        with self.assertRaises(module.MLModelRegistryError):
            module.model_eligibility_record_from_dict(invalid)

    def test_serialization_round_trips_are_deterministic(self) -> None:
        module = self.module
        entry, decision = module.create_governance_decision(
            self.entry(),
            "approve-for-shadow",
            actor="reviewer@example.com",
        )
        eligibility = module.create_model_eligibility_record(entry, "shadow")

        entry_dict = module.model_registry_entry_to_dict(entry)
        decision_dict = module.model_governance_decision_to_dict(decision)
        eligibility_dict = module.model_eligibility_record_to_dict(eligibility)

        self.assertEqual(
            entry_dict,
            module.model_registry_entry_to_dict(
                module.model_registry_entry_from_dict(entry_dict)
            ),
        )
        self.assertEqual(
            decision_dict,
            module.model_governance_decision_to_dict(
                module.model_governance_decision_from_dict(decision_dict)
            ),
        )
        self.assertEqual(
            eligibility_dict,
            module.model_eligibility_record_to_dict(
                module.model_eligibility_record_from_dict(eligibility_dict)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module
        model_id_a = module.create_model_id("tree", "7Y.1", "risk model")
        model_id_b = module.create_model_id("tree", "7Y.1", "risk model")
        self.assertEqual(model_id_a, model_id_b)
        self.assertEqual(model_id_a, "ML-MODEL-TREE-7Y-1-RISK-MODEL")

        decision_id_a = module.create_governance_decision_id(
            model_id_a,
            "register",
            "PROPOSED",
            "REGISTERED",
        )
        decision_id_b = module.create_governance_decision_id(
            model_id_a,
            "register",
            "PROPOSED",
            "REGISTERED",
        )
        self.assertEqual(decision_id_a, decision_id_b)

        eligibility_id_a = module.create_eligibility_id(model_id_a, "shadow")
        eligibility_id_b = module.create_eligibility_id(model_id_a, "shadow")
        self.assertEqual(eligibility_id_a, eligibility_id_b)
        self.assertNotRegex(model_id_a, re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-"))
        self.assertNotIn("T00", model_id_a)

    def test_no_runtime_or_model_deployment_functions(self) -> None:
        module = self.module
        names = function_names(MODULE_PATH)
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertNotIn(forbidden_name, names)
                self.assertFalse(hasattr(module, forbidden_name))

    def test_runtime_import_isolation(self) -> None:
        for path in python_files(RUNTIME_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.ml_model_registry", imports)
                self.assertNotIn("ml_model_registry", imports)

    def test_existing_phase7_validation_targets_exist(self) -> None:
        for relative_path in (
            "tests/test_phase7_ml_explainability.py",
            "tests/test_phase7_ml_training_backtesting.py",
            "tests/test_phase7_shadow_ml_model_interface.py",
            "tests/test_phase7_trend_aware_scoring.py",
            "tests/test_phase7_feature_label_dataset.py",
            "tests/test_phase7_ml_adaptive_scoring_boundary.py",
            "scripts/run_phase7_materialization_validation.py",
            "scripts/run_phase7_materialization_readiness_check.py",
        ):
            with self.subTest(relative_path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file(), relative_path)


if __name__ == "__main__":
    unittest.main()
