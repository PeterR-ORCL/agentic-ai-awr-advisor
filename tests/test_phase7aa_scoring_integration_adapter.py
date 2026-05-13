from __future__ import annotations

import ast
import importlib
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
ADAPTER_DOC = DOCS / "phase7aa_scoring_integration_adapter.md"
MODEL_DOC = DOCS / "phase7aa_scoring_integration_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "adaptive_scoring_adapter.py"

RUNTIME_PATHS = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/parsing",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
    "src/analysis/decision_engine.py",
    "src/analysis/recommendation_engine.py",
    "src/analysis/scoring_adapter.py",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "oracledb",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "sqlite3",
    "src.parser",
    "src.parsing",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.analysis",
    "src.reporting",
    "src.memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "apply_scoring_result",
    "activate_scoring",
    "update_runtime_scoring",
    "replace_scoring_engine",
    "mutate_scoring",
    "auto_apply",
    "autonomous_apply",
)


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


class Phase7AAScoringIntegrationAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.adaptive_scoring_adapter")
        cls.gate_module = importlib.import_module("src.learning.adaptive_runtime_gate")
        cls.context_module = importlib.import_module("src.learning.adaptive_runtime_context")

    def scoring_config(self):
        gate = self.gate_module
        return gate.AdaptiveRuntimeConfig(
            config_id=gate.create_adaptive_runtime_config_id(
                "controlled_runtime_candidate",
                "unit-test",
            ),
            mode="controlled_runtime_candidate",
            adaptive_runtime_enabled=True,
            scoring_integration_enabled=True,
            fallback_to_deterministic=True,
            runtime_influence_allowed=True,
            deterministic_runtime_authoritative=True,
            created_by="unit-test",
        )

    def scoring_eligibility(self):
        gate = self.gate_module
        return gate.AdaptiveComponentEligibility(
            component_id=gate.create_component_eligibility_id(
                "scoring",
                artifact_id="artifact://scoring/unit",
            ),
            component_type="scoring",
            artifact_id="artifact://scoring/unit",
            certified=True,
            runtime_eligible=True,
            runtime_influence_granted=True,
            runtime_active=False,
            rollback_reference="rollback://unit",
            validation_reference="validation://unit",
            phase4i_contract_preserved=True,
        )

    def allowed_gate_result(self):
        return self.gate_module.evaluate_adaptive_runtime_gate(
            self.scoring_config(),
            self.scoring_eligibility(),
        )

    def denied_gate_result(self):
        return self.gate_module.evaluate_adaptive_runtime_gate(
            self.gate_module.default_deterministic_runtime_config(),
            self.scoring_eligibility(),
        )

    def runtime_context(self, gate_result=None):
        gate = gate_result or self.allowed_gate_result()
        return self.context_module.build_adaptive_runtime_context(
            phase4i_output_summary={"phase4i_reference": "PHASE4I-SCORING-UNIT"},
            adaptive_runtime_config=self.scoring_config(),
            component_eligibilities=[self.scoring_eligibility()],
            gate_results=[gate],
            adaptive_scoring_reviews=[
                {"review_id": "SCORING-REVIEW-UNIT", "runtime_active": False}
            ],
            validation_references=[{"reference": "validation://unit"}],
            readiness_references=[{"reference": "readiness://unit"}],
            created_by="unit-test",
        )

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.adaptive_scoring_adapter")
        self.assertEqual(before_environment, dict(os.environ))

        imports = imported_modules(MODULE_PATH)
        self.assertIn("src.learning.adaptive_runtime_context", imports)
        self.assertIn("src.learning.adaptive_runtime_gate", imports)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )
        for forbidden in ("uuid", "datetime", "time"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, imports)
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertFalse(hasattr(module, forbidden_name))

    def test_docs_exist(self) -> None:
        self.assertTrue(ADAPTER_DOC.is_file(), ADAPTER_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{read_text(ADAPTER_DOC)}\n{read_text(MODEL_DOC)}".lower()
        for phrase in (
            "adapter does not replace runtime scoring",
            "deterministic scoring remains authoritative",
            "selected advisory score is not runtime score",
            "fallback to deterministic is required",
            "runtime_score_applied=false",
            "runtime_mutation_performed=false",
            "runtime_active=false",
            "no run_analysis.py integration is added",
            "no scoring module is modified",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_fallback_result_uses_deterministic_score(self) -> None:
        module = self.module
        result = module.fallback_scoring_result(
            "CPU",
            72.5,
            denied_reasons=["gate_denied_consideration"],
            created_by="unit-test",
        )
        self.assertEqual(result.selected_score_source, "deterministic")
        self.assertEqual(result.selected_advisory_score, 72.5)
        self.assertEqual(result.score_delta_from_deterministic, 0.0)
        self.assertTrue(result.fallback_to_deterministic)
        self.assertTrue(result.deterministic_score_authoritative)
        self.assertFalse(result.runtime_score_applied)
        self.assertFalse(result.runtime_mutation_performed)
        self.assertFalse(result.runtime_active)
        self.assertFalse(result.runtime_influence_granted)

    def test_gate_denied_falls_back_to_deterministic(self) -> None:
        result = self.module.evaluate_scoring_integration(
            domain="CPU",
            deterministic_score=70.0,
            adaptive_runtime_context=self.runtime_context(self.denied_gate_result()),
            gate_result=self.denied_gate_result(),
            trend_aware_score_result={"trend_aware_score": 82.0},
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            created_by="unit-test",
        )
        self.assertEqual(result.selected_score_source, "deterministic")
        self.assertEqual(result.selected_advisory_score, 70.0)
        self.assertTrue(result.fallback_to_deterministic)
        self.assertIn("gate_denied_consideration", result.denied_reasons)
        self.assertFalse(result.runtime_score_applied)
        self.assertFalse(result.runtime_active)

    def test_gate_allowed_selects_advisory_score_without_runtime_application(self) -> None:
        result = self.module.evaluate_scoring_integration(
            domain="CPU",
            deterministic_score=70.0,
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            trend_aware_score_result={"trend_aware_score": 75.0},
            shadow_ml_output={"shadow_ml_score": 81.0},
            proposed_scoring_config={"proposed_score": 88.0},
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            created_by="unit-test",
        )
        self.assertEqual(result.selected_score_source, "proposed_scoring_config")
        self.assertEqual(result.selected_advisory_score, 88.0)
        self.assertEqual(result.score_delta_from_deterministic, 18.0)
        self.assertFalse(result.fallback_to_deterministic)
        self.assertTrue(result.deterministic_score_authoritative)
        self.assertFalse(result.runtime_score_applied)
        self.assertFalse(result.runtime_mutation_performed)
        self.assertFalse(result.runtime_active)
        self.assertFalse(result.runtime_influence_granted)

    def test_score_source_selection_order(self) -> None:
        module = self.module
        selected, source, warnings = module.choose_advisory_score(
            50.0,
            trend_aware_score=60.0,
            shadow_ml_score=70.0,
            proposed_score=80.0,
            gate_allowed=True,
        )
        self.assertEqual((selected, source, warnings), (80.0, "proposed_scoring_config", []))

        selected, source, _ = module.choose_advisory_score(
            50.0,
            trend_aware_score=60.0,
            shadow_ml_score=70.0,
            gate_allowed=True,
        )
        self.assertEqual((selected, source), (70.0, "shadow_ml"))

        selected, source, _ = module.choose_advisory_score(
            50.0,
            trend_aware_score=60.0,
            gate_allowed=True,
        )
        self.assertEqual((selected, source), (60.0, "trend_aware"))

        selected, source, warnings = module.choose_advisory_score(
            50.0,
            trend_aware_score=101.0,
            gate_allowed=True,
        )
        self.assertEqual((selected, source), (50.0, "deterministic"))
        self.assertTrue(warnings)

    def test_score_scale_and_delta(self) -> None:
        module = self.module
        self.assertEqual(module.normalize_score(0.0), 0.0)
        self.assertEqual(module.normalize_score(100.0), 100.0)
        with self.assertRaises(module.AdaptiveScoringAdapterError):
            module.normalize_score(-0.1)
        with self.assertRaises(module.AdaptiveScoringAdapterError):
            module.normalize_score(100.1)

        result = module.evaluate_scoring_integration(
            domain="IO",
            deterministic_score=62.5,
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            trend_aware_score_result={"trend_aware_score": 67.0},
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
        )
        self.assertEqual(result.selected_score_source, "trend_aware")
        self.assertEqual(result.score_delta_from_deterministic, 4.5)

    def test_validation_rejects_unsafe_result(self) -> None:
        module = self.module
        result_dict = module.scoring_integration_result_to_dict(
            module.fallback_scoring_result("CPU", 70.0)
        )
        unsafe_fields = (
            ("runtime_score_applied", True),
            ("runtime_mutation_performed", True),
            ("runtime_active", True),
            ("runtime_influence_granted", True),
            ("deterministic_score_authoritative", False),
            ("phase4i_contract_preserved", False),
        )
        for field_name, value in unsafe_fields:
            with self.subTest(field_name=field_name):
                invalid = dict(result_dict)
                invalid[field_name] = value
                with self.assertRaises(module.AdaptiveScoringAdapterError):
                    module.scoring_integration_result_from_dict(invalid)

    def test_serialization_round_trip_is_deterministic(self) -> None:
        module = self.module
        result = module.evaluate_scoring_integration(
            domain="MEMORY",
            deterministic_score=55.0,
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            shadow_ml_output={"shadow_ml_score": 64.0},
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            created_by="unit-test",
        )
        data = module.scoring_integration_result_to_dict(result)
        self.assertEqual(
            data,
            module.scoring_integration_result_to_dict(
                module.scoring_integration_result_from_dict(data)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module
        result_id_a = module.create_scoring_integration_result_id(
            "cpu",
            "shadow_ml",
            72.5,
        )
        result_id_b = module.create_scoring_integration_result_id(
            "CPU",
            "shadow_ml",
            72.5,
        )
        self.assertEqual(result_id_a, result_id_b)
        self.assertEqual(result_id_a, "ADAPTIVE-SCORING-RESULT-CPU-SHADOW-ML-72-50")
        self.assertNotRegex(result_id_a, re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-"))
        self.assertNotRegex(result_id_a, re.compile(r"\d{4}-\d{2}-\d{2}"))
        self.assertNotIn("T00", result_id_a)

    def test_invalid_adaptive_score_falls_back_safely(self) -> None:
        result = self.module.evaluate_scoring_integration(
            domain="RAC",
            deterministic_score=44.0,
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            trend_aware_score_result={"trend_aware_score": 140.0},
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
        )
        self.assertEqual(result.selected_score_source, "deterministic")
        self.assertEqual(result.selected_advisory_score, 44.0)
        self.assertTrue(result.fallback_to_deterministic)
        self.assertTrue(result.warnings)

    def test_no_mutation_functions(self) -> None:
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
                self.assertNotIn("src.learning.adaptive_scoring_adapter", imports)
                self.assertNotIn("learning.adaptive_scoring_adapter", imports)
                self.assertNotIn("adaptive_scoring_adapter", imports)

    def test_existing_validation_entrypoints_still_exist(self) -> None:
        for relative_path in (
            "tests/test_phase7aa_runtime_integration_gate.py",
            "tests/test_phase7aa_adaptive_runtime_context.py",
            "scripts/run_phase7_ml_validation.py",
            "scripts/run_phase7_ml_readiness_check.py",
            "scripts/run_phase7_materialization_validation.py",
            "scripts/run_phase7_materialization_readiness_check.py",
            "scripts/run_phase7_validation.py",
            "scripts/run_phase7_readiness_check.py",
        ):
            with self.subTest(relative_path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file(), relative_path)


if __name__ == "__main__":
    unittest.main()
