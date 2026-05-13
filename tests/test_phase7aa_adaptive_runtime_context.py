from __future__ import annotations

import ast
import importlib
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
CONTEXT_DOC = DOCS / "phase7aa_adaptive_runtime_context.md"
MODEL_DOC = DOCS / "phase7aa_runtime_context_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "adaptive_runtime_context.py"

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


class Phase7AAAdaptiveRuntimeContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.adaptive_runtime_context")
        cls.gate_module = importlib.import_module("src.learning.adaptive_runtime_gate")

    def config(self, component_type: str = "scoring"):
        gate = self.gate_module
        return gate.AdaptiveRuntimeConfig(
            config_id=gate.create_adaptive_runtime_config_id(
                "controlled_runtime_candidate",
                "unit-test",
            ),
            mode="controlled_runtime_candidate",
            adaptive_runtime_enabled=True,
            scoring_integration_enabled=component_type == "scoring",
            recommendation_integration_enabled=component_type == "recommendation",
            parser_integration_enabled=component_type == "parser",
            trend_aware_scoring_enabled=component_type == "trend_aware_scoring",
            shadow_ml_enabled=component_type == "shadow_ml",
            model_registry_enabled=component_type == "model_registry",
            materialization_artifact_enabled=component_type == "materialization_artifact",
            fallback_to_deterministic=True,
            runtime_influence_allowed=True,
            deterministic_runtime_authoritative=True,
            created_by="unit-test",
        )

    def eligibility(self, component_type: str = "scoring"):
        gate = self.gate_module
        artifact_id = f"artifact://{component_type}/unit"
        model_id = f"model://{component_type}/unit" if component_type in ("shadow_ml", "model_registry") else None
        return gate.AdaptiveComponentEligibility(
            component_id=gate.create_component_eligibility_id(
                component_type,
                artifact_id=artifact_id,
                model_id=model_id,
            ),
            component_type=component_type,
            artifact_id=artifact_id,
            model_id=model_id,
            certified=True,
            runtime_eligible=True,
            runtime_influence_granted=True,
            runtime_active=False,
            rollback_reference="rollback://unit",
            validation_reference="validation://unit",
            phase4i_contract_preserved=True,
        )

    def allowed_gate_result(self, component_type: str = "scoring"):
        gate = self.gate_module
        return gate.evaluate_adaptive_runtime_gate(
            self.config(component_type),
            self.eligibility(component_type),
        )

    def denied_gate_result(self, component_type: str = "scoring"):
        gate = self.gate_module
        return gate.evaluate_adaptive_runtime_gate(
            gate.default_deterministic_runtime_config(),
            self.eligibility(component_type),
        )

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.adaptive_runtime_context")
        self.assertEqual(before_environment, dict(os.environ))

        imports = imported_modules(MODULE_PATH)
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
        self.assertTrue(CONTEXT_DOC.is_file(), CONTEXT_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{read_text(CONTEXT_DOC)}\n{read_text(MODEL_DOC)}".lower()
        for phrase in (
            "context is read-only",
            "context is not runtime activation",
            "deterministic runtime remains authoritative",
            "fallback to deterministic runtime remains required",
            "runtime_influence_applied=false",
            "runtime_mutation_performed=false",
            "parser/scoring/recommendation adapters are future work",
            "no run_analysis.py integration is added",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_empty_context_is_safe_and_valid(self) -> None:
        module = self.module
        context = module.empty_adaptive_runtime_context(created_by="unit-test")
        self.assertEqual(context.runtime_mode, "deterministic_only")
        self.assertTrue(context.deterministic_runtime_authoritative)
        self.assertTrue(context.fallback_to_deterministic)
        self.assertTrue(context.phase4i_contract_preserved)
        self.assertFalse(context.runtime_influence_applied)
        self.assertFalse(context.runtime_mutation_performed)
        self.assertIn("7AA.1 runtime gate", " ".join(context.required_next_steps))

        sections = (
            context.scoring_context,
            context.recommendation_context,
            context.parser_context,
            context.trend_context,
            context.shadow_ml_context,
            context.model_registry_context,
            context.explainability_context,
            context.materialization_context,
        )
        for section in sections:
            with self.subTest(section=section.section_name):
                self.assertEqual(section.runtime_active_count, 0)
                self.assertFalse(section.available)
        self.assertEqual(module.validate_adaptive_runtime_context(context), context)

    def test_context_builder_summarizes_gate_results(self) -> None:
        module = self.module
        context = module.build_adaptive_runtime_context(
            phase4i_output_summary={"phase4i_reference": "PHASE4I-UNIT"},
            adaptive_runtime_config=self.config("scoring"),
            component_eligibilities=[self.eligibility("scoring")],
            gate_results=[
                self.allowed_gate_result("scoring"),
                self.denied_gate_result("recommendation"),
            ],
            adaptive_scoring_reviews=[
                {
                    "review_id": "SCORING-REVIEW-1",
                    "status": "VALIDATED",
                    "runtime_active": False,
                }
            ],
            created_by="unit-test",
        )
        self.assertEqual(context.runtime_mode, "controlled_runtime_candidate")
        self.assertEqual(context.scoring_context.item_count, 1)
        self.assertEqual(context.scoring_context.eligible_count, 1)
        self.assertEqual(context.scoring_context.allowed_for_consideration_count, 1)
        self.assertEqual(context.scoring_context.runtime_active_count, 0)
        self.assertFalse(context.runtime_influence_applied)
        self.assertFalse(context.runtime_mutation_performed)
        self.assertIn("adaptive_runtime_disabled", context.denied_reasons)

    def test_scoring_context_counts_reviews_without_applying_scoring(self) -> None:
        context = self.module.build_adaptive_runtime_context(
            adaptive_scoring_reviews=[
                {"review_id": "REVIEW-1", "runtime_active": False},
                {"review_id": "REVIEW-2", "runtime_active": False},
            ]
        )
        self.assertEqual(context.scoring_context.review_count, 2)
        self.assertEqual(context.scoring_context.runtime_active_count, 0)
        self.assertFalse(context.runtime_mutation_performed)

    def test_recommendation_context_counts_evolutions_without_applying_rules(self) -> None:
        context = self.module.build_adaptive_runtime_context(
            recommendation_rule_evolutions=[
                {"evolution_id": "REC-EVO-1", "status": "VALIDATED", "runtime_active": False},
                {"evolution_id": "REC-EVO-2", "status": "PROPOSED", "runtime_active": False},
            ]
        )
        self.assertEqual(context.recommendation_context.review_count, 2)
        self.assertEqual(context.recommendation_context.runtime_active_count, 0)
        self.assertFalse(context.runtime_influence_applied)

    def test_parser_context_counts_evolutions_and_backlog(self) -> None:
        context = self.module.build_adaptive_runtime_context(
            parser_mapping_evolutions=[
                {
                    "evolution_id": "PARSER-EVO-1",
                    "status": "PROPOSED",
                    "runtime_active": False,
                },
                {
                    "backlog_id": "PARSER-BACKLOG-1",
                    "source_evolution_id": "PARSER-EVO-2",
                    "runtime_active": False,
                },
            ]
        )
        self.assertEqual(context.parser_context.parser_evolution_count, 1)
        self.assertEqual(context.parser_context.parser_backlog_count, 1)
        self.assertTrue(context.parser_context.phase4i_contract_required)
        self.assertTrue(context.parser_context.awr_regression_required)
        self.assertTrue(context.parser_context.scoring_regression_required)
        self.assertEqual(context.parser_context.runtime_active_count, 0)
        self.assertFalse(context.runtime_mutation_performed)

    def test_trend_shadow_model_and_explainability_sections(self) -> None:
        context = self.module.build_adaptive_runtime_context(
            trend_aware_scores=[
                {"result_id": "TREND-1", "domain": "CPU", "runtime_active": False},
                {"result_id": "TREND-2", "domain": "IO", "runtime_active": False},
            ],
            shadow_ml_outputs=[
                {"output_id": "SHADOW-1", "model_id": "MODEL-A", "runtime_active": False},
                {"output_id": "SHADOW-2", "model_id": "MODEL-A", "runtime_active": False},
            ],
            model_registry_entries=[
                {
                    "model_id": "MODEL-A",
                    "shadow_eligible": True,
                    "runtime_eligible": False,
                    "runtime_active": False,
                }
            ],
            ml_explanations=[
                {"explanation_id": "EXPLAIN-1", "runtime_active": False}
            ],
        )
        self.assertEqual(context.trend_context.result_count, 2)
        self.assertEqual(context.trend_context.domains, ["CPU", "IO"])
        self.assertEqual(context.shadow_ml_context.output_count, 2)
        self.assertEqual(context.shadow_ml_context.model_count, 1)
        self.assertEqual(context.model_registry_context.registered_model_count, 1)
        self.assertEqual(context.model_registry_context.shadow_eligible_count, 1)
        self.assertEqual(context.model_registry_context.runtime_active_count, 0)
        self.assertEqual(context.explainability_context.item_count, 1)

    def test_materialization_context_counts_artifacts(self) -> None:
        context = self.module.build_adaptive_runtime_context(
            materialization_artifacts=[
                {
                    "materialization_id": "MAT-1",
                    "runtime_sensitive": True,
                    "runtime_active": False,
                },
                {
                    "materialization_id": "MAT-2",
                    "runtime_sensitive": False,
                    "runtime_active": False,
                },
            ]
        )
        self.assertEqual(context.materialization_context.artifact_count, 2)
        self.assertEqual(context.materialization_context.runtime_sensitive_count, 1)
        self.assertEqual(context.materialization_context.runtime_active_count, 0)

    def test_validation_rejects_unsafe_context(self) -> None:
        module = self.module
        context_dict = module.adaptive_runtime_context_to_dict(
            module.empty_adaptive_runtime_context()
        )
        unsafe_fields = (
            ("deterministic_runtime_authoritative", False),
            ("fallback_to_deterministic", False),
            ("phase4i_contract_preserved", False),
            ("runtime_influence_applied", True),
            ("runtime_mutation_performed", True),
        )
        for field_name, value in unsafe_fields:
            with self.subTest(field_name=field_name):
                invalid = dict(context_dict)
                invalid[field_name] = value
                with self.assertRaises(module.AdaptiveRuntimeContextError):
                    module.adaptive_runtime_context_from_dict(invalid)

        invalid_section = module.adaptive_runtime_section_to_dict(
            module.AdaptiveRuntimeSection(
                section_name="scoring",
                available=False,
                item_count=0,
                eligible_count=0,
                allowed_for_consideration_count=0,
                runtime_active_count=0,
            )
        )
        invalid_section["runtime_active_count"] = 1
        invalid_section["item_count"] = 1
        invalid_section["summaries"] = [{"review_id": "UNSAFE", "runtime_active": True}]
        with self.assertRaises(module.AdaptiveRuntimeContextError):
            module.adaptive_runtime_section_from_dict(invalid_section)

        with self.assertRaises(module.AdaptiveRuntimeContextError):
            module.build_adaptive_runtime_context(
                adaptive_scoring_reviews=[
                    {"review_id": "UNSAFE", "runtime_active": True}
                ]
            )

    def test_serialization_round_trips_are_deterministic(self) -> None:
        module = self.module
        section = module.AdaptiveRuntimeSection(
            section_name="scoring",
            available=True,
            item_count=1,
            eligible_count=0,
            allowed_for_consideration_count=0,
            runtime_active_count=0,
            summaries=[{"review_id": "REVIEW-1", "runtime_active": False}],
            warnings=[],
        )
        parser_section = module.AdaptiveParserRuntimeSection(
            section_name="parser",
            available=True,
            parser_evolution_count=1,
            parser_backlog_count=0,
            runtime_active_count=0,
            phase4i_contract_required=True,
            awr_regression_required=True,
            scoring_regression_required=True,
            summaries=[{"evolution_id": "PARSER-1", "runtime_active": False}],
            warnings=[],
        )
        context = module.build_adaptive_runtime_context(
            phase4i_output_summary={"phase4i_reference": "PHASE4I-ROUNDTRIP"},
            adaptive_scoring_reviews=[{"review_id": "REVIEW-1", "runtime_active": False}],
            validation_references=[{"reference": "validation://unit"}],
            readiness_references=[{"reference": "readiness://unit"}],
            created_by="unit-test",
        )

        section_dict = module.adaptive_runtime_section_to_dict(section)
        parser_section_dict = module.adaptive_parser_runtime_section_to_dict(
            parser_section
        )
        context_dict = module.adaptive_runtime_context_to_dict(context)

        self.assertEqual(
            section_dict,
            module.adaptive_runtime_section_to_dict(
                module.adaptive_runtime_section_from_dict(section_dict)
            ),
        )
        self.assertEqual(
            parser_section_dict,
            module.adaptive_parser_runtime_section_to_dict(
                module.adaptive_parser_runtime_section_from_dict(parser_section_dict)
            ),
        )
        self.assertEqual(
            context_dict,
            module.adaptive_runtime_context_to_dict(
                module.adaptive_runtime_context_from_dict(context_dict)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module
        context_id_a = module.create_adaptive_runtime_context_id(
            "controlled_runtime_candidate",
            "PHASE4I-UNIT",
        )
        context_id_b = module.create_adaptive_runtime_context_id(
            "controlled_runtime_candidate",
            "PHASE4I-UNIT",
        )
        self.assertEqual(context_id_a, context_id_b)
        self.assertEqual(
            context_id_a,
            "ADAPTIVE-RUNTIME-CONTEXT-CONTROLLED-RUNTIME-CANDIDATE-PHASE4I-UNIT",
        )
        self.assertNotRegex(context_id_a, re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-"))
        self.assertNotRegex(context_id_a, re.compile(r"\d{4}-\d{2}-\d{2}"))
        self.assertNotIn("T00", context_id_a)

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
                self.assertNotIn("src.learning.adaptive_runtime_context", imports)
                self.assertNotIn("learning.adaptive_runtime_context", imports)
                self.assertNotIn("adaptive_runtime_context", imports)

    def test_existing_validation_entrypoints_still_exist(self) -> None:
        for relative_path in (
            "tests/test_phase7aa_runtime_integration_gate.py",
            "scripts/run_phase7_ml_validation.py",
            "scripts/run_phase7_ml_readiness_check.py",
            "scripts/run_phase7_materialization_validation.py",
            "scripts/run_phase7_materialization_readiness_check.py",
            "scripts/run_phase7_validation.py",
            "scripts/run_phase7_readiness_check.py",
            "scripts/run_phase7h_dashboard_validation.py",
            "scripts/awr_memory_cli.py",
            "scripts/run_phase6_validation.py",
        ):
            with self.subTest(relative_path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file(), relative_path)


if __name__ == "__main__":
    unittest.main()
