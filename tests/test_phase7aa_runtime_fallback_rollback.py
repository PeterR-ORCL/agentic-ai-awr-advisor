from __future__ import annotations

import ast
import importlib
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
FALLBACK_DOC = DOCS / "phase7aa_runtime_fallback_rollback.md"
MODEL_DOC = DOCS / "phase7aa_runtime_fallback_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "adaptive_runtime_fallback.py"

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
    "execute_rollback",
    "apply_rollback",
    "apply_adaptive_runtime",
    "activate_runtime",
    "update_runtime_scoring",
    "update_runtime_parser",
    "update_runtime_recommendation",
    "replace_scoring_engine",
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


class Phase7AARuntimeFallbackRollbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.adaptive_runtime_fallback")
        cls.gate_module = importlib.import_module("src.learning.adaptive_runtime_gate")
        cls.context_module = importlib.import_module("src.learning.adaptive_runtime_context")
        cls.scoring_module = importlib.import_module("src.learning.adaptive_scoring_adapter")
        cls.recommendation_module = importlib.import_module(
            "src.learning.adaptive_recommendation_adapter"
        )
        cls.parser_module = importlib.import_module("src.learning.adaptive_parser_adapter")

    def runtime_config(self):
        gate = self.gate_module
        return gate.AdaptiveRuntimeConfig(
            config_id=gate.create_adaptive_runtime_config_id(
                "controlled_runtime_candidate",
                "unit-test",
            ),
            mode="controlled_runtime_candidate",
            adaptive_runtime_enabled=True,
            scoring_integration_enabled=True,
            recommendation_integration_enabled=True,
            parser_integration_enabled=True,
            fallback_to_deterministic=True,
            runtime_influence_allowed=True,
            deterministic_runtime_authoritative=True,
            created_by="unit-test",
        )

    def eligibility(self, component_type: str):
        gate = self.gate_module
        return gate.AdaptiveComponentEligibility(
            component_id=gate.create_component_eligibility_id(
                component_type,
                artifact_id=f"artifact://{component_type}/unit",
            ),
            component_type=component_type,
            artifact_id=f"artifact://{component_type}/unit",
            certified=True,
            runtime_eligible=True,
            runtime_influence_granted=True,
            runtime_active=False,
            rollback_reference="rollback://unit",
            validation_reference="validation://unit",
            phase4i_contract_preserved=True,
        )

    def allowed_gate_result(self, component_type: str):
        return self.gate_module.evaluate_adaptive_runtime_gate(
            self.runtime_config(),
            self.eligibility(component_type),
        )

    def runtime_context(self):
        gates = [
            self.allowed_gate_result("scoring"),
            self.allowed_gate_result("recommendation"),
            self.allowed_gate_result("parser"),
        ]
        return self.context_module.build_adaptive_runtime_context(
            phase4i_output_summary={"phase4i_reference": "PHASE4I-FALLBACK-UNIT"},
            adaptive_runtime_config=self.runtime_config(),
            component_eligibilities=[
                self.eligibility("scoring"),
                self.eligibility("recommendation"),
                self.eligibility("parser"),
            ],
            gate_results=gates,
            adaptive_scoring_reviews=[
                {"review_id": "SCORING-REVIEW-UNIT", "runtime_active": False}
            ],
            recommendation_rule_evolutions=[
                {"evolution_id": "RECO-EVO-UNIT", "runtime_active": False}
            ],
            parser_mapping_evolutions=[
                {"evolution_id": "PARSER-EVO-UNIT", "runtime_active": False}
            ],
            validation_references=[{"reference": "validation://unit"}],
            readiness_references=[{"reference": "readiness://unit"}],
            created_by="unit-test",
        )

    def scoring_result(self):
        return self.scoring_module.evaluate_scoring_integration(
            domain="CPU",
            deterministic_score=70.0,
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result("scoring"),
            proposed_scoring_config={"proposed_score": 82.0},
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            created_by="unit-test",
        )

    def recommendation_result(self):
        return self.recommendation_module.evaluate_recommendation_integration(
            deterministic_recommendation={
                "action": "Review SQL plan stability",
                "evidence_mapping": {"awr_section": "SQL ordered by Elapsed Time"},
            },
            recommendation_id="RECO-001",
            domain="SQL",
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result("recommendation"),
            proposed_recommendation_rule={
                "rule_id": "RECO-RULE-UNIT",
                "rule_payload": {"action": "Review SQL plan stability and bind sensitivity"},
                "evidence_requirements": ["evidence mapping validation"],
            },
            evidence_reference="evidence://unit",
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            created_by="unit-test",
        )

    def parser_result(self):
        return self.parser_module.evaluate_parser_integration(
            parser_mapping_evolution={
                "evolution_id": "PARSER-EVO-UNIT",
                "parser_section": "SQL Statistics",
                "signal_name": "elapsed_time",
                "proposed_parser_change_type": "field_extraction_change",
                "proposed_mapping": {"column": "Elapsed Time"},
                "phase4i_contract_required": True,
                "awr_regression_required": True,
                "scoring_regression_required": True,
                "runtime_active": False,
                "runtime_influence_granted": False,
            },
            parser_backlog_item={
                "backlog_id": "PARSER-BACKLOG-UNIT",
                "source_evolution_id": "PARSER-EVO-UNIT",
                "parser_section": "SQL Statistics",
                "signal_name": "elapsed_time",
                "proposed_parser_change_type": "field_extraction_change",
                "runtime_active": False,
                "runtime_influence_granted": False,
            },
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result("parser"),
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            awr_regression_reference="awr://unit",
            scoring_regression_reference="scoring://unit",
            phase4i_reference="phase4i://unit",
            created_by="unit-test",
        )

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.adaptive_runtime_fallback")
        self.assertEqual(before_environment, dict(os.environ))

        imports = imported_modules(MODULE_PATH)
        for expected in (
            "src.learning.adaptive_scoring_adapter",
            "src.learning.adaptive_recommendation_adapter",
            "src.learning.adaptive_parser_adapter",
            "src.learning.adaptive_runtime_context",
            "src.learning.adaptive_runtime_gate",
        ):
            self.assertIn(expected, imports)
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
        self.assertTrue(FALLBACK_DOC.is_file(), FALLBACK_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{read_text(FALLBACK_DOC)}\n{read_text(MODEL_DOC)}".lower()
        for phrase in (
            "fallback layer does not execute rollback",
            "fallback layer does not apply adaptive behavior",
            "deterministic fallback is default",
            "adaptive_consideration_ready is not runtime active",
            "runtime mutation is not allowed",
            "run_analysis.py is not modified",
            "parser/scoring/recommendation modules are not modified",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_deterministic_fallback_decision(self) -> None:
        result = self.module.deterministic_fallback_decision(
            "no_adapter_results",
            created_by="unit-test",
        )
        self.assertEqual(result.final_runtime_posture, "deterministic_fallback")
        self.assertTrue(result.fallback_to_deterministic)
        self.assertTrue(result.fallback_required)
        self.assertTrue(result.deterministic_runtime_authoritative)
        self.assertFalse(result.runtime_mutation_detected)
        self.assertFalse(result.runtime_influence_detected)

    def test_safe_empty_inputs_return_deterministic_fallback(self) -> None:
        result = self.module.evaluate_runtime_fallback(created_by="unit-test")
        self.assertEqual(result.final_runtime_posture, "deterministic_fallback")
        self.assertTrue(result.fallback_to_deterministic)
        self.assertTrue(result.fallback_required)
        self.assertFalse(result.runtime_mutation_detected)
        self.assertFalse(result.runtime_influence_detected)

    def test_safe_adapter_results(self) -> None:
        scoring_safe, scoring_denied, _ = self.module.evaluate_scoring_result_safety(
            self.scoring_result()
        )
        recommendation_safe, recommendation_denied, _ = (
            self.module.evaluate_recommendation_result_safety(
                self.recommendation_result()
            )
        )
        parser_safe, parser_denied, _ = self.module.evaluate_parser_result_safety(
            self.parser_result()
        )
        self.assertTrue(scoring_safe, scoring_denied)
        self.assertTrue(recommendation_safe, recommendation_denied)
        self.assertTrue(parser_safe, parser_denied)

    def test_unsafe_scoring_result(self) -> None:
        data = self.scoring_module.scoring_integration_result_to_dict(
            self.scoring_result()
        )
        unsafe_cases = (
            ("runtime_score_applied", True, "scoring_runtime_score_applied_unsafe"),
            ("runtime_mutation_performed", True, "scoring_runtime_mutation_performed_unsafe"),
            (
                "deterministic_score_authoritative",
                False,
                "scoring_deterministic_score_authoritative_unsafe",
            ),
        )
        for field_name, value, denied_reason in unsafe_cases:
            with self.subTest(field_name=field_name):
                unsafe = dict(data)
                unsafe[field_name] = value
                safe, denied, _ = self.module.evaluate_scoring_result_safety(unsafe)
                self.assertFalse(safe)
                self.assertIn(denied_reason, denied)

    def test_unsafe_recommendation_result(self) -> None:
        data = self.recommendation_module.recommendation_integration_result_to_dict(
            self.recommendation_result()
        )
        unsafe_cases = (
            (
                "runtime_recommendation_applied",
                True,
                "recommendation_runtime_recommendation_applied_unsafe",
            ),
            (
                "runtime_mutation_performed",
                True,
                "recommendation_runtime_mutation_performed_unsafe",
            ),
            (
                "deterministic_recommendation_authoritative",
                False,
                "recommendation_deterministic_recommendation_authoritative_unsafe",
            ),
        )
        for field_name, value, denied_reason in unsafe_cases:
            with self.subTest(field_name=field_name):
                unsafe = dict(data)
                unsafe[field_name] = value
                safe, denied, _ = self.module.evaluate_recommendation_result_safety(unsafe)
                self.assertFalse(safe)
                self.assertIn(denied_reason, denied)

    def test_unsafe_parser_result(self) -> None:
        data = self.parser_module.parser_integration_result_to_dict(self.parser_result())
        unsafe_cases = (
            ("runtime_parser_applied", True, "parser_runtime_parser_applied_unsafe"),
            ("runtime_mutation_performed", True, "parser_runtime_mutation_performed_unsafe"),
            (
                "parser_runtime_authoritative",
                False,
                "parser_parser_runtime_authoritative_unsafe",
            ),
            (
                "phase4i_contract_preserved",
                False,
                "parser_phase4i_contract_preserved_unsafe",
            ),
            ("awr_regression_required", False, "parser_awr_regression_required_unsafe"),
            (
                "scoring_regression_required",
                False,
                "parser_scoring_regression_required_unsafe",
            ),
            (
                "unknown_signal_safety_required",
                False,
                "parser_unknown_signal_safety_required_unsafe",
            ),
        )
        for field_name, value, denied_reason in unsafe_cases:
            with self.subTest(field_name=field_name):
                unsafe = dict(data)
                unsafe[field_name] = value
                safe, denied, _ = self.module.evaluate_parser_result_safety(unsafe)
                self.assertFalse(safe)
                self.assertIn(denied_reason, denied)

    def test_rollback_required_without_reference(self) -> None:
        result = self.module.evaluate_runtime_fallback(
            scoring_integration_result=self.scoring_result(),
            recommendation_integration_result=self.recommendation_result(),
            parser_integration_result=self.parser_result(),
            validation_reference="validation://unit",
            readiness_reference="readiness://unit",
        )
        self.assertEqual(result.final_runtime_posture, "deterministic_fallback")
        self.assertTrue(result.rollback_required)
        self.assertFalse(result.rollback_available)
        self.assertTrue(result.fallback_required)
        self.assertIn("rollback_reference_required", result.denied_reasons)

    def test_adaptive_consideration_ready_with_references(self) -> None:
        result = self.module.evaluate_runtime_fallback(
            scoring_integration_result=self.scoring_result(),
            recommendation_integration_result=self.recommendation_result(),
            parser_integration_result=self.parser_result(),
            rollback_reference="rollback://unit",
            validation_reference="validation://unit",
            readiness_reference="readiness://unit",
            created_by="unit-test",
        )
        self.assertEqual(result.final_runtime_posture, "adaptive_consideration_ready")
        self.assertFalse(result.fallback_required)
        self.assertTrue(result.fallback_to_deterministic)
        self.assertTrue(result.rollback_available)
        self.assertFalse(result.rollback_required)
        self.assertFalse(result.runtime_mutation_detected)
        self.assertFalse(result.runtime_influence_detected)

    def test_validation_rejects_unsafe_fields(self) -> None:
        module = self.module
        result_dict = module.runtime_fallback_decision_to_dict(
            module.deterministic_fallback_decision("unit")
        )
        unsafe_cases = (
            ("deterministic_runtime_authoritative", False),
            ("phase4i_contract_preserved", False),
            ("final_runtime_posture", "unsupported"),
            ("runtime_mutation_detected", True),
            ("runtime_influence_detected", True),
        )
        for field_name, value in unsafe_cases:
            with self.subTest(field_name=field_name):
                invalid = dict(result_dict)
                invalid[field_name] = value
                with self.assertRaises(module.AdaptiveRuntimeFallbackError):
                    module.runtime_fallback_decision_from_dict(invalid)

    def test_serialization_round_trip_is_deterministic(self) -> None:
        module = self.module
        result = module.evaluate_runtime_fallback(
            scoring_integration_result=self.scoring_result(),
            recommendation_integration_result=self.recommendation_result(),
            parser_integration_result=self.parser_result(),
            rollback_reference="rollback://unit",
            validation_reference="validation://unit",
            readiness_reference="readiness://unit",
            created_by="unit-test",
        )
        data = module.runtime_fallback_decision_to_dict(result)
        self.assertEqual(
            data,
            module.runtime_fallback_decision_to_dict(
                module.runtime_fallback_decision_from_dict(data)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module
        result_id_a = module.create_runtime_fallback_decision_id(
            "validation://unit",
            "readiness://unit",
        )
        result_id_b = module.create_runtime_fallback_decision_id(
            "validation://unit",
            "readiness://unit",
        )
        self.assertEqual(result_id_a, result_id_b)
        self.assertEqual(
            result_id_a,
            "RUNTIME-FALLBACK-VALIDATION-UNIT-READINESS-UNIT",
        )
        self.assertNotRegex(result_id_a, re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-"))
        self.assertNotRegex(result_id_a, re.compile(r"\d{4}-\d{2}-\d{2}"))
        self.assertNotIn("T00", result_id_a)

    def test_no_execution_functions(self) -> None:
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
                self.assertNotIn("src.learning.adaptive_runtime_fallback", imports)
                self.assertNotIn("learning.adaptive_runtime_fallback", imports)
                self.assertNotIn("adaptive_runtime_fallback", imports)

    def test_existing_validation_entrypoints_still_exist(self) -> None:
        for relative_path in (
            "tests/test_phase7aa_runtime_integration_gate.py",
            "tests/test_phase7aa_adaptive_runtime_context.py",
            "tests/test_phase7aa_scoring_integration_adapter.py",
            "tests/test_phase7aa_recommendation_integration_adapter.py",
            "tests/test_phase7aa_parser_integration_adapter.py",
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
