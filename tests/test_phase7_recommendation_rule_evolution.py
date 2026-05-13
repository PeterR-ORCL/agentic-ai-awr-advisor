from __future__ import annotations

import ast
from copy import deepcopy
import importlib
import os
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
RECOMMENDATION_RULE_EVOLUTION_DOC = DOCS / "phase7_recommendation_rule_evolution.md"
RECOMMENDATION_RULE_MODEL_DOC = DOCS / "phase7_recommendation_rule_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "recommendation_rule_evolution.py"

REQUIRED_EVOLUTION_TYPES = (
    "recommendation_wording_review",
    "recommendation_priority_review",
    "recommendation_domain_mapping_review",
    "recommendation_suppression_review",
    "action_sequencing_review",
    "risk_label_review",
    "evidence_mapping_review",
    "recommendation_category_review",
    "recommendation_confidence_wording_review",
    "recommendation_escalation_review",
)

RUNTIME_PATHS = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/parsing",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
    "src/analysis",
)

FORBIDDEN_ACTIVE_FUNCTIONS = (
    "apply_recommendation_rule",
    "activate_recommendation_rule",
    "mutate_recommendations",
    "update_runtime_recommendations",
    "update_recommendation_rules",
    "auto_apply",
    "autonomous_apply",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


def evolution_module():
    return importlib.import_module("src.learning.recommendation_rule_evolution")


def artifact_module():
    return importlib.import_module("src.learning.materialization_artifact")


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
    return imports


class Phase7RecommendationRuleEvolutionTests(unittest.TestCase):
    def test_01_module_import_safety(self) -> None:
        before_environment = dict(os.environ)

        module = evolution_module()

        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "RecommendationRuleEvolution"))
        imports = imported_modules(MODULE_PATH)
        for forbidden in (
            "oracledb",
            "requests",
            "socket",
            "urllib",
            "http.client",
            "httpx",
            "oci",
            "oracle_agent_memory",
            "src.parser",
            "src.parsing",
            "src.scoring",
            "src.decision",
            "src.recommendation",
            "src.recommendations",
            "src.reporting",
            "scripts.run_analysis",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_docs_exist(self) -> None:
        self.assertTrue(
            RECOMMENDATION_RULE_EVOLUTION_DOC.is_file(),
            RECOMMENDATION_RULE_EVOLUTION_DOC,
        )
        self.assertTrue(RECOMMENDATION_RULE_MODEL_DOC.is_file(), RECOMMENDATION_RULE_MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = (
            f"{lower_text(RECOMMENDATION_RULE_EVOLUTION_DOC)}\n"
            f"{lower_text(RECOMMENDATION_RULE_MODEL_DOC)}"
        )
        for phrase in (
            "proposal-only",
            "no runtime recommendation changes are applied",
            "runtime_influence_granted=false",
            "proposed recommendation rules are inactive",
            "validated does not mean runtime active",
            "existing recommendation engine remains authoritative",
            "semantic context is not recommendation truth",
            "this is not ml",
            "does not implement learned_model(x)",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_supported_evolution_types(self) -> None:
        module = evolution_module()
        self.assertEqual(set(module.RECOMMENDATION_EVOLUTION_TYPES), set(REQUIRED_EVOLUTION_TYPES))
        for evolution_type in REQUIRED_EVOLUTION_TYPES:
            with self.subTest(evolution_type=evolution_type):
                self.assertTrue(module.is_supported_recommendation_evolution_type(evolution_type))
                self.assertIn(
                    "versioned recommendation rule/config",
                    module.required_recommendation_validation_requirements(evolution_type),
                )
        self.assertFalse(
            module.is_supported_recommendation_evolution_type("parser_mapping_review")
        )
        with self.assertRaises(module.RecommendationRuleEvolutionError):
            module.required_recommendation_validation_requirements("parser_mapping_review")

    def test_source_artifact_requirement(self) -> None:
        module = evolution_module()

        evolution = self.create_evolution()
        self.assertEqual(
            evolution.source_materialization_id,
            self.make_source_artifact().materialization_id,
        )

        for candidate_type in ("parser_mapping_candidate", "scoring_weight_review_candidate"):
            with self.subTest(candidate_type=candidate_type):
                with self.assertRaises(module.RecommendationRuleEvolutionError):
                    self.create_evolution(
                        source=self.make_source_artifact(candidate_type=candidate_type)
                    )

        for status in ("REJECTED", "ROLLED_BACK", "CLOSED"):
            with self.subTest(status=status):
                with self.assertRaises(module.RecommendationRuleEvolutionError):
                    self.create_evolution(source=self.make_source_artifact(status=status))

        source_data = self.make_source_artifact_data()
        source_data["runtime_influence_granted"] = True
        with self.assertRaises(module.RecommendationRuleEvolutionError):
            self.create_evolution(source=source_data)

    def test_evolution_creation(self) -> None:
        module = evolution_module()
        source = self.make_source_artifact()
        evolution = self.create_evolution(source=source)

        expected_id = module.create_recommendation_evolution_id(
            source.materialization_id,
            "recommendation_wording_review",
            "v1.0",
        )
        self.assertEqual(evolution.evolution_id, expected_id)
        self.assertTrue(
            evolution.evolution_id.startswith("RECO-EVO-RECOMMENDATION-WORDING-REVIEW-")
        )
        self.assertNotRegex(
            evolution.evolution_id,
            re.compile(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                re.IGNORECASE,
            ),
        )
        self.assertFalse(evolution.runtime_influence_granted)
        self.assertFalse(evolution.status == "VALIDATED" and evolution.runtime_influence_granted)
        self.assertEqual(evolution.semantic_context, {"summary": "Reviewer-assist context only."})

        for kwargs in (
            {"actor": ""},
            {"proposed_rule_version": ""},
            {"proposed_rule": {}},
            {"before_after_summary": ""},
            {"rollback_plan": ""},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(module.RecommendationRuleEvolutionError):
                    self.create_evolution(**kwargs)

    def test_validation_requirements(self) -> None:
        module = evolution_module()
        with self.assertRaises(module.RecommendationRuleEvolutionError):
            self.create_evolution(validation_requirements=["versioned recommendation rule/config"])

        evolution = self.create_evolution()
        requirements = "\n".join(evolution.validation_requirements).lower()
        for phrase in (
            "versioned recommendation rule/config",
            "recommendation regression tests",
            "evidence mapping validation",
            "phase 4i recommendations contract validation",
            "rollback plan",
            "deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, requirements)

        data = module.recommendation_rule_evolution_to_dict(evolution)
        data["runtime_influence_granted"] = True
        with self.assertRaises(module.RecommendationRuleEvolutionError):
            module.recommendation_rule_evolution_from_dict(data)

    def test_evolution_type_specific_validation(self) -> None:
        module = evolution_module()
        cases = {
            "recommendation_wording_review": "wording regression validation",
            "recommendation_priority_review": "priority/order regression validation",
            "recommendation_domain_mapping_review": "domain mapping validation",
            "recommendation_suppression_review": (
                "suppression false positive/false negative review"
            ),
            "action_sequencing_review": "action sequencing validation",
            "risk_label_review": "risk label consistency validation",
            "evidence_mapping_review": "evidence linkage validation",
            "recommendation_category_review": "category consistency validation",
            "recommendation_confidence_wording_review": (
                "confidence wording calibration validation"
            ),
            "recommendation_escalation_review": "escalation/de-escalation validation",
        }
        for evolution_type, required_phrase in cases.items():
            with self.subTest(evolution_type=evolution_type):
                evolution = self.create_evolution(evolution_type=evolution_type)
                self.assertIn(required_phrase, "\n".join(evolution.validation_requirements))

                requirements = module.required_recommendation_validation_requirements(
                    evolution_type
                )
                requirements.remove(required_phrase)
                with self.assertRaises(module.RecommendationRuleEvolutionError):
                    self.create_evolution(
                        evolution_type=evolution_type,
                        validation_requirements=requirements,
                    )

    def test_proposed_recommendation_rule(self) -> None:
        module = evolution_module()
        evolution = self.create_evolution()
        rule = module.create_proposed_recommendation_rule(evolution)

        self.assertEqual(rule.version, evolution.proposed_rule_version)
        self.assertFalse(rule.runtime_active)
        self.assertFalse(rule.runtime_influence_granted)
        self.assertTrue(rule.rule_id.startswith("RECO-RULE-RECOMMENDATION-RULE-REVIEW-V1-0-"))
        self.assertEqual(rule.source_evolution_id, evolution.evolution_id)
        self.assertEqual(rule.rule_payload["recommendation_key"], "sql_high_db_time")

        data = module.proposed_recommendation_rule_to_dict(rule)
        data["runtime_active"] = True
        with self.assertRaises(module.RecommendationRuleEvolutionError):
            module.proposed_recommendation_rule_from_dict(data)

        data = module.proposed_recommendation_rule_to_dict(rule)
        data["runtime_influence_granted"] = True
        with self.assertRaises(module.RecommendationRuleEvolutionError):
            module.proposed_recommendation_rule_from_dict(data)

    def test_serialization(self) -> None:
        module = evolution_module()
        evolution = self.create_evolution()
        evolution_data = module.recommendation_rule_evolution_to_dict(evolution)
        self.assertEqual(tuple(evolution_data.keys()), module.RECOMMENDATION_RULE_EVOLUTION_FIELDS)
        self.assertEqual(module.recommendation_rule_evolution_from_dict(evolution_data), evolution)
        self.assertEqual(
            module.recommendation_rule_evolutions_to_dicts([evolution, evolution]),
            [evolution_data, evolution_data],
        )

        rule = module.create_proposed_recommendation_rule(evolution)
        rule_data = module.proposed_recommendation_rule_to_dict(rule)
        self.assertEqual(tuple(rule_data.keys()), module.PROPOSED_RECOMMENDATION_RULE_FIELDS)
        self.assertEqual(module.proposed_recommendation_rule_from_dict(rule_data), rule)

        evolution_data["source_evidence"][0]["source_id"] = "mutated"
        self.assertEqual(evolution.source_evidence[0]["source_id"], "SRC-1")

    def test_no_source_mutation(self) -> None:
        source_data = self.make_source_artifact_data()
        original = deepcopy(source_data)

        self.create_evolution(source=source_data)

        self.assertEqual(source_data, original)

    def test_runtime_import_isolation(self) -> None:
        for path in python_files(RUNTIME_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.recommendation_rule_evolution", imports)
                self.assertNotIn("learning.recommendation_rule_evolution", imports)
                self.assertNotIn("recommendation_rule_evolution", imports)

    def test_no_active_mutation_functions(self) -> None:
        tree = ast.parse(read_text(MODULE_PATH), filename=str(MODULE_PATH))
        function_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        for forbidden_name in FORBIDDEN_ACTIVE_FUNCTIONS:
            with self.subTest(function_name=forbidden_name):
                self.assertNotIn(forbidden_name, function_names)

    def create_evolution(self, source=None, **overrides):
        module = evolution_module()
        kwargs = {
            "materialization_artifact": self.make_source_artifact() if source is None else source,
            "actor": "recommendation-owner@example.com",
            "evolution_type": "recommendation_wording_review",
            "proposed_rule": self.proposed_rule(),
            "proposed_rule_version": "v1.0",
            "proposed_change_summary": "Review proposed recommendation wording adjustment.",
            "before_after_summary": (
                "Before: current deterministic recommendations remain authoritative. "
                "After: proposed recommendation rule is available for review only."
            ),
            "validation_requirements": None,
            "rollback_plan": (
                "Keep the current runtime recommendation rule and discard the proposed version."
            ),
            "runtime_influence_requested": True,
            "baseline_reference": "phase4i-current-recommendation-baseline",
        }
        kwargs.update(overrides)
        return module.create_recommendation_rule_evolution(**kwargs)

    def make_source_artifact(
        self,
        candidate_type: str = "recommendation_rule_candidate",
        status: str = "MATERIALIZED",
    ):
        artifact = artifact_module().create_materialization_artifact(
            self.make_candidate_data(candidate_type=candidate_type),
            actor="materialization-owner@example.com",
            proposed_change_summary="Prepare a controlled materialization artifact.",
            rollback_plan="Restore the previous governed runtime-sensitive configuration.",
        )
        data = artifact_module().materialization_artifact_to_dict(artifact)
        data["status"] = status
        return artifact_module().materialization_artifact_from_dict(data)

    def make_source_artifact_data(
        self,
        candidate_type: str = "recommendation_rule_candidate",
        status: str = "MATERIALIZED",
    ) -> dict[str, object]:
        return artifact_module().materialization_artifact_to_dict(
            self.make_source_artifact(candidate_type=candidate_type, status=status)
        )

    def proposed_rule(self) -> dict[str, object]:
        return {
            "recommendation_key": "sql_high_db_time",
            "proposed_wording": "Review SQL with high DB time and validate execution plan drift.",
            "proposed_priority": "P2",
            "evidence_mapping": ["top_sql", "db_time"],
            "action_sequence": ["review_sql", "compare_plan", "validate_index_options"],
            "risk_label": "medium",
            "category": "sql",
            "confidence_wording": "confidence depends on deterministic evidence coverage",
        }

    def make_candidate_data(
        self,
        candidate_type: str = "recommendation_rule_candidate",
        status: str = "APPROVED_FOR_IMPLEMENTATION",
    ) -> dict[str, object]:
        component_by_type = {
            "parser_mapping_candidate": "parser",
            "scoring_weight_review_candidate": "scoring",
            "recommendation_rule_candidate": "recommendation",
        }
        return {
            "candidate_id": f"CANDIDATE-{candidate_type.upper().replace('_', '-')}-1",
            "candidate_type": candidate_type,
            "title": f"Candidate for {candidate_type}",
            "description": "Approved governed learning candidate.",
            "source_evidence": [{"source_type": "unit_test", "source_id": "SRC-1"}],
            "structured_sources": [{"source_type": "outcome_pattern", "pattern_id": "P-1"}],
            "semantic_context": {"summary": "Reviewer-assist context only."},
            "affected_component": component_by_type[candidate_type],
            "affected_domain": "sql",
            "confidence": 0.5,
            "rationale": "Human-reviewed candidate for controlled materialization.",
            "requires_human_review": True,
            "runtime_influence": False,
            "status": status,
            "created_at": None,
            "created_by": "candidate-engine",
            "reviewed_by": "reviewer@example.com",
            "review_notes": "Approved for implementation consideration only.",
            "materialization_reference": None,
        }


if __name__ == "__main__":
    unittest.main()
