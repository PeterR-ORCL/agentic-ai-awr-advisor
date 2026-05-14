from __future__ import annotations

import ast
import importlib
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
ADAPTER_DOC = DOCS / "phase7aa_recommendation_integration_adapter.md"
MODEL_DOC = DOCS / "phase7aa_recommendation_integration_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "adaptive_recommendation_adapter.py"

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
    "apply_recommendation_result",
    "activate_recommendation",
    "update_runtime_recommendation",
    "replace_recommendation_engine",
    "mutate_recommendation",
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


class Phase7AARecommendationIntegrationAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module(
            "src.learning.adaptive_recommendation_adapter"
        )
        cls.gate_module = importlib.import_module("src.learning.adaptive_runtime_gate")
        cls.context_module = importlib.import_module("src.learning.adaptive_runtime_context")

    def recommendation_config(self):
        gate = self.gate_module
        return gate.AdaptiveRuntimeConfig(
            config_id=gate.create_adaptive_runtime_config_id(
                "controlled_runtime_candidate",
                "unit-test",
            ),
            mode="controlled_runtime_candidate",
            adaptive_runtime_enabled=True,
            recommendation_integration_enabled=True,
            fallback_to_deterministic=True,
            runtime_influence_allowed=True,
            deterministic_runtime_authoritative=True,
            created_by="unit-test",
        )

    def recommendation_eligibility(self):
        gate = self.gate_module
        return gate.AdaptiveComponentEligibility(
            component_id=gate.create_component_eligibility_id(
                "recommendation",
                artifact_id="artifact://recommendation/unit",
            ),
            component_type="recommendation",
            artifact_id="artifact://recommendation/unit",
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
            self.recommendation_config(),
            self.recommendation_eligibility(),
        )

    def denied_gate_result(self):
        return self.gate_module.evaluate_adaptive_runtime_gate(
            self.gate_module.default_deterministic_runtime_config(),
            self.recommendation_eligibility(),
        )

    def runtime_context(self, gate_result=None):
        gate = gate_result or self.allowed_gate_result()
        return self.context_module.build_adaptive_runtime_context(
            phase4i_output_summary={"phase4i_reference": "PHASE4I-RECO-UNIT"},
            adaptive_runtime_config=self.recommendation_config(),
            component_eligibilities=[self.recommendation_eligibility()],
            gate_results=[gate],
            recommendation_rule_evolutions=[
                {"evolution_id": "RECO-EVO-UNIT", "runtime_active": False}
            ],
            validation_references=[{"reference": "validation://unit"}],
            readiness_references=[{"reference": "readiness://unit"}],
            created_by="unit-test",
        )

    def deterministic_recommendation(self):
        return {
            "action": "Review SQL plan stability",
            "priority": "medium",
            "evidence_mapping": {"awr_section": "SQL ordered by Elapsed Time"},
        }

    def proposed_rule(self):
        return {
            "rule_id": "PROPOSED-RECO-RULE-UNIT",
            "rule_payload": {
                "action": "Review SQL plan stability and bind sensitivity",
                "priority": "high",
            },
            "evidence_requirements": ["evidence mapping validation"],
        }

    def recommendation_evolution(self):
        return {
            "evolution_id": "RECO-EVO-UNIT",
            "proposed_rule": {
                "action": "Review SQL plan baselines",
                "priority": "medium",
            },
            "source_evidence": [{"section": "SQL ordered by CPU Time"}],
        }

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.adaptive_recommendation_adapter")
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
            "adapter does not replace runtime recommendations",
            "deterministic recommendations remain authoritative",
            "selected advisory recommendation is not runtime recommendation",
            "fallback to deterministic recommendation is required",
            "runtime_recommendation_applied=false",
            "runtime_mutation_performed=false",
            "runtime_active=false",
            "no run_analysis.py integration is added",
            "no recommendation module is modified",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_fallback_result_uses_deterministic_recommendation(self) -> None:
        module = self.module
        deterministic = self.deterministic_recommendation()
        result = module.fallback_recommendation_result(
            "SQL",
            "RECO-001",
            deterministic,
            denied_reasons=["gate_denied_consideration"],
            created_by="unit-test",
        )
        self.assertEqual(result.selected_recommendation_source, "deterministic")
        self.assertEqual(result.selected_advisory_recommendation, deterministic)
        self.assertTrue(result.fallback_to_deterministic)
        self.assertTrue(result.deterministic_recommendation_authoritative)
        self.assertFalse(result.runtime_recommendation_applied)
        self.assertFalse(result.runtime_mutation_performed)
        self.assertFalse(result.runtime_active)
        self.assertFalse(result.runtime_influence_granted)

    def test_gate_denied_falls_back_to_deterministic(self) -> None:
        result = self.module.evaluate_recommendation_integration(
            deterministic_recommendation=self.deterministic_recommendation(),
            recommendation_id="RECO-001",
            domain="SQL",
            adaptive_runtime_context=self.runtime_context(self.denied_gate_result()),
            gate_result=self.denied_gate_result(),
            proposed_recommendation_rule=self.proposed_rule(),
            evidence_reference="evidence://unit",
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            created_by="unit-test",
        )
        self.assertEqual(result.selected_recommendation_source, "deterministic")
        self.assertEqual(
            result.selected_advisory_recommendation,
            self.deterministic_recommendation(),
        )
        self.assertTrue(result.fallback_to_deterministic)
        self.assertIn("gate_denied_consideration", result.denied_reasons)
        self.assertFalse(result.runtime_recommendation_applied)
        self.assertFalse(result.runtime_active)

    def test_gate_allowed_selects_advisory_without_runtime_application(self) -> None:
        result = self.module.evaluate_recommendation_integration(
            deterministic_recommendation=self.deterministic_recommendation(),
            recommendation_id="RECO-001",
            domain="SQL",
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            recommendation_rule_evolution=self.recommendation_evolution(),
            proposed_recommendation_rule=self.proposed_rule(),
            evidence_reference="evidence://unit",
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            created_by="unit-test",
        )
        self.assertEqual(result.selected_recommendation_source, "proposed_rule")
        self.assertEqual(
            result.selected_advisory_recommendation["action"],
            "Review SQL plan stability and bind sensitivity",
        )
        self.assertFalse(result.fallback_to_deterministic)
        self.assertTrue(result.deterministic_recommendation_authoritative)
        self.assertFalse(result.runtime_recommendation_applied)
        self.assertFalse(result.runtime_mutation_performed)
        self.assertFalse(result.runtime_active)
        self.assertFalse(result.runtime_influence_granted)

    def test_recommendation_source_selection_order(self) -> None:
        module = self.module
        deterministic = self.deterministic_recommendation()
        selected, source, warnings = module.choose_advisory_recommendation(
            deterministic,
            proposed_rule={"action": "Proposed rule action"},
            recommendation_evolution={"action": "Evolution action"},
            gate_allowed=True,
        )
        self.assertEqual(source, "proposed_rule")
        self.assertEqual(selected["action"], "Proposed rule action")
        self.assertEqual(warnings, [])

        selected, source, _ = module.choose_advisory_recommendation(
            deterministic,
            recommendation_evolution={"action": "Evolution action"},
            gate_allowed=True,
        )
        self.assertEqual(source, "recommendation_evolution")
        self.assertEqual(selected["action"], "Evolution action")

        selected, source, warnings = module.choose_advisory_recommendation(
            deterministic,
            proposed_rule={},
            recommendation_evolution={"action": "Evolution action"},
            gate_allowed=True,
        )
        self.assertEqual(source, "deterministic")
        self.assertEqual(selected, deterministic)
        self.assertTrue(warnings)

    def test_evidence_mapping_warnings_remain_advisory(self) -> None:
        result = self.module.evaluate_recommendation_integration(
            deterministic_recommendation=self.deterministic_recommendation(),
            recommendation_id="RECO-002",
            domain="SQL",
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            proposed_recommendation_rule={
                "rule_id": "PROPOSED-NO-EVIDENCE",
                "rule_payload": {"action": "Tune SQL profile review"},
            },
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
        )
        self.assertEqual(result.selected_recommendation_source, "proposed_rule")
        self.assertIn("proposed recommendation lacks evidence mapping", result.warnings)
        self.assertIn(
            "evidence reference missing for adaptive recommendation consideration",
            result.warnings,
        )
        self.assertTrue(result.evidence_mapping_summary)
        self.assertFalse(result.runtime_recommendation_applied)
        self.assertFalse(result.runtime_influence_granted)

    def test_validation_rejects_unsafe_result(self) -> None:
        module = self.module
        result_dict = module.recommendation_integration_result_to_dict(
            module.fallback_recommendation_result(
                "SQL",
                "RECO-001",
                self.deterministic_recommendation(),
            )
        )
        unsafe_fields = (
            ("runtime_recommendation_applied", True),
            ("runtime_mutation_performed", True),
            ("runtime_active", True),
            ("runtime_influence_granted", True),
            ("deterministic_recommendation_authoritative", False),
            ("phase4i_contract_preserved", False),
        )
        for field_name, value in unsafe_fields:
            with self.subTest(field_name=field_name):
                invalid = dict(result_dict)
                invalid[field_name] = value
                with self.assertRaises(module.AdaptiveRecommendationAdapterError):
                    module.recommendation_integration_result_from_dict(invalid)

        invalid = dict(result_dict)
        invalid["deterministic_recommendation"] = {}
        with self.assertRaises(module.AdaptiveRecommendationAdapterError):
            module.recommendation_integration_result_from_dict(invalid)

        invalid = dict(result_dict)
        invalid["selected_advisory_recommendation"] = {}
        with self.assertRaises(module.AdaptiveRecommendationAdapterError):
            module.recommendation_integration_result_from_dict(invalid)

    def test_serialization_round_trip_is_deterministic(self) -> None:
        module = self.module
        result = module.evaluate_recommendation_integration(
            deterministic_recommendation=self.deterministic_recommendation(),
            recommendation_id="RECO-003",
            domain="WAIT",
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            recommendation_rule_evolution=self.recommendation_evolution(),
            evidence_reference="evidence://unit",
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            created_by="unit-test",
        )
        data = module.recommendation_integration_result_to_dict(result)
        self.assertEqual(
            data,
            module.recommendation_integration_result_to_dict(
                module.recommendation_integration_result_from_dict(data)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module
        result_id_a = module.create_recommendation_integration_result_id(
            "sql",
            "reco-001",
            "proposed_rule",
        )
        result_id_b = module.create_recommendation_integration_result_id(
            "SQL",
            "RECO-001",
            "proposed_rule",
        )
        self.assertEqual(result_id_a, result_id_b)
        self.assertEqual(
            result_id_a,
            "ADAPTIVE-RECOMMENDATION-RESULT-SQL-RECO-001-PROPOSED-RULE",
        )
        self.assertNotRegex(result_id_a, re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-"))
        self.assertNotRegex(result_id_a, re.compile(r"\d{4}-\d{2}-\d{2}"))
        self.assertNotIn("T00", result_id_a)

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
                self.assertNotIn("src.learning.adaptive_recommendation_adapter", imports)
                self.assertNotIn("learning.adaptive_recommendation_adapter", imports)
                self.assertNotIn("adaptive_recommendation_adapter", imports)

    def test_existing_validation_entrypoints_still_exist(self) -> None:
        for relative_path in (
            "tests/test_phase7aa_runtime_integration_gate.py",
            "tests/test_phase7aa_adaptive_runtime_context.py",
            "tests/test_phase7aa_scoring_integration_adapter.py",
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
