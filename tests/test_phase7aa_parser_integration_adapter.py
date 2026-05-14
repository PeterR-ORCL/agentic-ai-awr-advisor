from __future__ import annotations

import ast
import importlib
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
ADAPTER_DOC = DOCS / "phase7aa_parser_integration_adapter.md"
MODEL_DOC = DOCS / "phase7aa_parser_integration_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "adaptive_parser_adapter.py"

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
    "apply_parser_result",
    "activate_parser",
    "update_runtime_parser",
    "replace_parser_engine",
    "mutate_parser",
    "classify_unknown_signal",
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


class Phase7AAParserIntegrationAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.adaptive_parser_adapter")
        cls.gate_module = importlib.import_module("src.learning.adaptive_runtime_gate")
        cls.context_module = importlib.import_module("src.learning.adaptive_runtime_context")

    def parser_config(self):
        gate = self.gate_module
        return gate.AdaptiveRuntimeConfig(
            config_id=gate.create_adaptive_runtime_config_id(
                "controlled_runtime_candidate",
                "unit-test",
            ),
            mode="controlled_runtime_candidate",
            adaptive_runtime_enabled=True,
            parser_integration_enabled=True,
            fallback_to_deterministic=True,
            runtime_influence_allowed=True,
            deterministic_runtime_authoritative=True,
            created_by="unit-test",
        )

    def parser_eligibility(self):
        gate = self.gate_module
        return gate.AdaptiveComponentEligibility(
            component_id=gate.create_component_eligibility_id(
                "parser",
                artifact_id="artifact://parser/unit",
            ),
            component_type="parser",
            artifact_id="artifact://parser/unit",
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
            self.parser_config(),
            self.parser_eligibility(),
        )

    def denied_gate_result(self):
        return self.gate_module.evaluate_adaptive_runtime_gate(
            self.gate_module.default_deterministic_runtime_config(),
            self.parser_eligibility(),
        )

    def runtime_context(self, gate_result=None):
        gate = gate_result or self.allowed_gate_result()
        return self.context_module.build_adaptive_runtime_context(
            phase4i_output_summary={"phase4i_reference": "PHASE4I-PARSER-UNIT"},
            adaptive_runtime_config=self.parser_config(),
            component_eligibilities=[self.parser_eligibility()],
            gate_results=[gate],
            parser_mapping_evolutions=[
                {"evolution_id": "PARSER-EVO-UNIT", "runtime_active": False}
            ],
            validation_references=[{"reference": "validation://unit"}],
            readiness_references=[{"reference": "readiness://unit"}],
            created_by="unit-test",
        )

    def parser_evolution(self):
        return {
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
        }

    def parser_backlog_item(self):
        return {
            "backlog_id": "PARSER-BACKLOG-UNIT",
            "source_evolution_id": "PARSER-EVO-UNIT",
            "parser_section": "SQL Statistics",
            "signal_name": "elapsed_time",
            "proposed_parser_change_type": "field_extraction_change",
            "title": "Review elapsed time mapping",
            "runtime_active": False,
            "runtime_influence_granted": False,
        }

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.adaptive_parser_adapter")
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
            "adapter does not modify runtime parser",
            "current parser remains authoritative",
            "selected parser action is consideration only",
            "fallback to current parser is required",
            "runtime_parser_applied=false",
            "runtime_mutation_performed=false",
            "runtime_active=false",
            "no run_analysis.py integration is added",
            "no parser module is modified",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_fallback_result_uses_current_parser(self) -> None:
        module = self.module
        result = module.fallback_parser_result(
            "SQL Statistics",
            "elapsed_time",
            denied_reasons=["gate_denied_consideration"],
            created_by="unit-test",
        )
        self.assertEqual(result.selected_parser_source, "current_parser")
        self.assertEqual(result.selected_parser_action, "keep_current_parser")
        self.assertTrue(result.fallback_to_current_parser)
        self.assertTrue(result.parser_runtime_authoritative)
        self.assertFalse(result.runtime_parser_applied)
        self.assertFalse(result.runtime_mutation_performed)
        self.assertFalse(result.runtime_active)
        self.assertFalse(result.runtime_influence_granted)

    def test_gate_denied_falls_back_to_current_parser(self) -> None:
        result = self.module.evaluate_parser_integration(
            parser_mapping_evolution=self.parser_evolution(),
            parser_backlog_item=self.parser_backlog_item(),
            adaptive_runtime_context=self.runtime_context(self.denied_gate_result()),
            gate_result=self.denied_gate_result(),
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            awr_regression_reference="awr://unit",
            scoring_regression_reference="scoring://unit",
            phase4i_reference="phase4i://unit",
            created_by="unit-test",
        )
        self.assertEqual(result.selected_parser_source, "current_parser")
        self.assertEqual(result.selected_parser_action, "keep_current_parser")
        self.assertTrue(result.fallback_to_current_parser)
        self.assertIn("gate_denied_consideration", result.denied_reasons)
        self.assertFalse(result.runtime_parser_applied)
        self.assertFalse(result.runtime_active)

    def test_gate_allowed_selects_backlog_without_runtime_application(self) -> None:
        result = self.module.evaluate_parser_integration(
            parser_mapping_evolution=self.parser_evolution(),
            parser_backlog_item=self.parser_backlog_item(),
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            awr_regression_reference="awr://unit",
            scoring_regression_reference="scoring://unit",
            phase4i_reference="phase4i://unit",
            created_by="unit-test",
        )
        self.assertEqual(result.selected_parser_source, "parser_backlog")
        self.assertEqual(result.selected_parser_action, "consider_parser_backlog")
        self.assertEqual(result.parser_backlog_id, "PARSER-BACKLOG-UNIT")
        self.assertFalse(result.fallback_to_current_parser)
        self.assertTrue(result.parser_runtime_authoritative)
        self.assertFalse(result.runtime_parser_applied)
        self.assertFalse(result.runtime_mutation_performed)
        self.assertFalse(result.runtime_active)
        self.assertFalse(result.runtime_influence_granted)

    def test_parser_source_selection_order(self) -> None:
        module = self.module
        action, source, warnings = module.choose_parser_consideration(
            parser_mapping_evolution=self.parser_evolution(),
            parser_backlog_item=self.parser_backlog_item(),
            gate_allowed=True,
        )
        self.assertEqual((action, source, warnings), (
            "consider_parser_backlog",
            "parser_backlog",
            [],
        ))

        action, source, _ = module.choose_parser_consideration(
            parser_mapping_evolution=self.parser_evolution(),
            gate_allowed=True,
        )
        self.assertEqual((action, source), (
            "consider_parser_evolution",
            "parser_evolution",
        ))

        action, source, warnings = module.choose_parser_consideration(
            parser_mapping_evolution=self.parser_evolution(),
            parser_backlog_item={},
            gate_allowed=True,
        )
        self.assertEqual((action, source), ("keep_current_parser", "current_parser"))
        self.assertTrue(warnings)

    def test_regression_references_are_required_for_consideration(self) -> None:
        base = {
            "parser_mapping_evolution": self.parser_evolution(),
            "parser_backlog_item": self.parser_backlog_item(),
            "adaptive_runtime_context": self.runtime_context(),
            "gate_result": self.allowed_gate_result(),
            "validation_reference": "validation://unit",
            "rollback_reference": "rollback://unit",
            "awr_regression_reference": "awr://unit",
            "scoring_regression_reference": "scoring://unit",
            "phase4i_reference": "phase4i://unit",
        }
        missing_fields = (
            ("validation_reference", "validation_reference_required"),
            ("rollback_reference", "rollback_reference_required"),
            ("awr_regression_reference", "awr_regression_reference_required"),
            ("scoring_regression_reference", "scoring_regression_reference_required"),
            ("phase4i_reference", "phase4i_reference_required"),
        )
        for field_name, denied_reason in missing_fields:
            with self.subTest(field_name=field_name):
                args = dict(base)
                args[field_name] = None
                result = self.module.evaluate_parser_integration(**args)
                self.assertEqual(result.selected_parser_source, "current_parser")
                self.assertTrue(result.fallback_to_current_parser)
                self.assertIn(denied_reason, result.denied_reasons)

    def test_invalid_parser_input_falls_back_safely(self) -> None:
        result = self.module.evaluate_parser_integration(
            parser_backlog_item={
                "backlog_id": "PARSER-BACKLOG-UNSAFE",
                "runtime_active": True,
            },
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            awr_regression_reference="awr://unit",
            scoring_regression_reference="scoring://unit",
            phase4i_reference="phase4i://unit",
        )
        self.assertEqual(result.selected_parser_source, "current_parser")
        self.assertTrue(result.fallback_to_current_parser)
        self.assertIn("parser_input_invalid", result.denied_reasons)
        self.assertTrue(result.warnings)

    def test_validation_rejects_unsafe_result(self) -> None:
        module = self.module
        result_dict = module.parser_integration_result_to_dict(
            module.fallback_parser_result("SQL Statistics", "elapsed_time")
        )
        unsafe_fields = (
            ("runtime_parser_applied", True),
            ("runtime_mutation_performed", True),
            ("runtime_active", True),
            ("runtime_influence_granted", True),
            ("parser_runtime_authoritative", False),
            ("phase4i_contract_preserved", False),
            ("awr_regression_required", False),
            ("scoring_regression_required", False),
            ("unknown_signal_safety_required", False),
        )
        for field_name, value in unsafe_fields:
            with self.subTest(field_name=field_name):
                invalid = dict(result_dict)
                invalid[field_name] = value
                with self.assertRaises(module.AdaptiveParserAdapterError):
                    module.parser_integration_result_from_dict(invalid)

    def test_serialization_round_trip_is_deterministic(self) -> None:
        module = self.module
        result = module.evaluate_parser_integration(
            parser_mapping_evolution=self.parser_evolution(),
            adaptive_runtime_context=self.runtime_context(),
            gate_result=self.allowed_gate_result(),
            validation_reference="validation://unit",
            rollback_reference="rollback://unit",
            awr_regression_reference="awr://unit",
            scoring_regression_reference="scoring://unit",
            phase4i_reference="phase4i://unit",
            created_by="unit-test",
        )
        data = module.parser_integration_result_to_dict(result)
        self.assertEqual(
            data,
            module.parser_integration_result_to_dict(
                module.parser_integration_result_from_dict(data)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module
        result_id_a = module.create_parser_integration_result_id(
            "sql statistics",
            "elapsed_time",
            "parser_backlog",
        )
        result_id_b = module.create_parser_integration_result_id(
            "SQL Statistics",
            "elapsed_time",
            "parser_backlog",
        )
        self.assertEqual(result_id_a, result_id_b)
        self.assertEqual(
            result_id_a,
            "ADAPTIVE-PARSER-RESULT-SQL-STATISTICS-ELAPSED-TIME-PARSER-BACKLOG",
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
                self.assertNotIn("src.learning.adaptive_parser_adapter", imports)
                self.assertNotIn("learning.adaptive_parser_adapter", imports)
                self.assertNotIn("adaptive_parser_adapter", imports)

    def test_existing_validation_entrypoints_still_exist(self) -> None:
        for relative_path in (
            "tests/test_phase7aa_runtime_integration_gate.py",
            "tests/test_phase7aa_adaptive_runtime_context.py",
            "tests/test_phase7aa_scoring_integration_adapter.py",
            "tests/test_phase7aa_recommendation_integration_adapter.py",
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
