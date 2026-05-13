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
APPROVED_MATERIALIZATION_DOC = DOCS / "phase7_approved_candidate_materialization.md"
ARTIFACT_MODEL_DOC = DOCS / "phase7_materialization_artifact_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "materialization_artifact.py"

EXPECTED_MAPPING = {
    "parser_mapping_candidate": "parser_mapping_artifact",
    "scoring_weight_review_candidate": "scoring_review_artifact",
    "recommendation_rule_candidate": "recommendation_rule_artifact",
    "dashboard_wording_candidate": "dashboard_wording_artifact",
    "dashboard_interaction_candidate": "dashboard_interaction_artifact",
    "governance_workflow_candidate": "governance_workflow_artifact",
    "semantic_summary_candidate": "semantic_summary_artifact",
    "documentation_candidate": "documentation_artifact",
    "validation_candidate": "validation_artifact",
}

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
    "activate_runtime",
    "apply_to_parser",
    "apply_to_scoring",
    "apply_to_recommendations",
    "mutate_runtime",
    "auto_apply",
    "autonomous_apply",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


def artifact_module():
    return importlib.import_module("src.learning.materialization_artifact")


def candidate_model_module():
    return importlib.import_module("src.learning.learning_candidate_model")


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


class Phase7ApprovedCandidateMaterializationTests(unittest.TestCase):
    def test_01_module_import_safety(self) -> None:
        before_environment = dict(os.environ)

        module = artifact_module()

        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "MaterializationArtifact"))
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
        self.assertTrue(APPROVED_MATERIALIZATION_DOC.is_file(), APPROVED_MATERIALIZATION_DOC)
        self.assertTrue(ARTIFACT_MODEL_DOC.is_file(), ARTIFACT_MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{lower_text(APPROVED_MATERIALIZATION_DOC)}\n{lower_text(ARTIFACT_MODEL_DOC)}"
        for phrase in (
            "materialization does not equal runtime activation",
            "runtime_influence_granted=false",
            "materialized is not runtime active",
            "validated is not runtime active by itself",
            "no automatic parser mutation",
            "no automatic scoring mutation",
            "no automatic recommendation mutation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_candidate_type_mapping(self) -> None:
        module = artifact_module()
        self.assertEqual(module.CANDIDATE_TYPE_TO_ARTIFACT_TYPE, EXPECTED_MAPPING)
        for candidate_type, artifact_type in EXPECTED_MAPPING.items():
            with self.subTest(candidate_type=candidate_type):
                self.assertEqual(module.infer_artifact_type(candidate_type), artifact_type)

    def test_approved_candidate_can_create_artifact(self) -> None:
        module = artifact_module()
        model = candidate_model_module()
        candidate = model.LearningCandidate(
            candidate_id="CANDIDATE-DOCUMENTATION-CANDIDATE-APPROVED",
            candidate_type="documentation_candidate",
            title="Review boundary wording",
            description="Review documentation boundary wording.",
            rationale="Human review approved this documentation proposal.",
            source_evidence=[{"source_type": "doc_review", "source_id": "DOC-1"}],
            status="APPROVED_FOR_IMPLEMENTATION",
            affected_component="documentation",
        )

        artifact = module.create_materialization_artifact(
            candidate,
            actor="reviewer@example.com",
            proposed_change_summary="Prepare a documentation change work item.",
        )

        self.assertEqual(artifact.source_candidate_id, candidate.candidate_id)
        self.assertEqual(artifact.proposed_artifact_type, "documentation_artifact")
        self.assertEqual(artifact.status, "APPROVED_FOR_MATERIALIZATION")
        self.assertFalse(artifact.runtime_influence_granted)

    def test_non_approved_candidates_fail_materialization(self) -> None:
        module = artifact_module()
        for status in ("PROPOSED", "REJECTED", "CLOSED"):
            with self.subTest(status=status):
                with self.assertRaises(module.MaterializationArtifactError):
                    module.create_materialization_artifact(
                        self.make_candidate_data(status=status),
                        actor="reviewer@example.com",
                        proposed_change_summary="Should not materialize.",
                    )

    def test_runtime_influence_safety(self) -> None:
        module = artifact_module()
        artifact = module.create_materialization_artifact(
            self.make_candidate_data(candidate_type="documentation_candidate"),
            actor="reviewer@example.com",
            proposed_change_summary="Prepare documentation artifact.",
            runtime_influence_requested=True,
        )

        self.assertTrue(artifact.runtime_influence_requested)
        self.assertFalse(artifact.runtime_influence_granted)

        data = module.materialization_artifact_to_dict(artifact)
        data["runtime_influence_granted"] = True
        with self.assertRaises(module.MaterializationArtifactError):
            module.materialization_artifact_from_dict(data)
        with self.assertRaises(module.MaterializationArtifactError):
            module.MaterializationArtifact(**data)

    def test_parser_artifact_requirements(self) -> None:
        module = artifact_module()
        artifact = module.create_materialization_artifact(
            self.make_candidate_data(candidate_type="parser_mapping_candidate"),
            actor="parser-owner@example.com",
            proposed_change_summary="Prepare parser mapping review artifact.",
            rollback_plan="Restore the previous parser mapping and rerun regression validation.",
        )

        self.assertEqual(artifact.proposed_artifact_type, "parser_mapping_artifact")
        requirements = "\n".join(artifact.validation_requirements).lower()
        for phrase in (
            "parser tests",
            "awr regression validation",
            "phase 4i contract validation",
            "unknown signal safety",
            "scoring regression check",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, requirements)

    def test_scoring_artifact_requirements(self) -> None:
        module = artifact_module()
        artifact = module.create_materialization_artifact(
            self.make_candidate_data(candidate_type="scoring_weight_review_candidate"),
            actor="scoring-owner@example.com",
            proposed_change_summary="Prepare scoring review artifact.",
            rollback_plan="Restore the previous versioned scoring config.",
        )

        self.assertEqual(artifact.proposed_artifact_type, "scoring_review_artifact")
        requirements = "\n".join(artifact.validation_requirements).lower()
        for phrase in (
            "versioned scoring config",
            "before/after comparison",
            "scoring regression tests",
            "phase 4i scores contract validation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, requirements)

    def test_recommendation_artifact_requirements(self) -> None:
        module = artifact_module()
        artifact = module.create_materialization_artifact(
            self.make_candidate_data(candidate_type="recommendation_rule_candidate"),
            actor="recommendation-owner@example.com",
            proposed_change_summary="Prepare recommendation rule artifact.",
            rollback_plan="Restore the previous recommendation rule config.",
        )

        self.assertEqual(artifact.proposed_artifact_type, "recommendation_rule_artifact")
        requirements = "\n".join(artifact.validation_requirements).lower()
        for phrase in (
            "versioned recommendation rule/config",
            "recommendation regression tests",
            "evidence mapping validation",
            "phase 4i recommendations contract validation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, requirements)

    def test_deterministic_id(self) -> None:
        module = artifact_module()
        candidate = self.make_candidate_data(candidate_type="parser_mapping_candidate")

        first = module.create_materialization_artifact(
            candidate,
            actor="parser-owner@example.com",
            proposed_change_summary="Prepare parser mapping review artifact.",
            rollback_plan="Restore the previous parser mapping.",
        )
        second = module.create_materialization_artifact(
            deepcopy(candidate),
            actor="parser-owner@example.com",
            proposed_change_summary="Prepare parser mapping review artifact.",
            rollback_plan="Restore the previous parser mapping.",
        )

        self.assertEqual(first.materialization_id, second.materialization_id)
        self.assertTrue(first.materialization_id.startswith("MAT-PARSER-MAPPING-ARTIFACT-"))
        self.assertNotRegex(
            first.materialization_id,
            re.compile(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                re.IGNORECASE,
            ),
        )
        self.assertNotIn("2026", first.materialization_id)
        self.assertNotRegex(first.materialization_id, r"\d{4}-\d{2}-\d{2}")

    def test_serialization_round_trip(self) -> None:
        module = artifact_module()
        artifact = module.create_materialization_artifact(
            self.make_candidate_data(candidate_type="governance_workflow_candidate"),
            actor="governance-owner@example.com",
            proposed_change_summary="Prepare governance workflow artifact.",
            rollback_plan="Reverse the proposed workflow documentation update.",
        )

        data = module.materialization_artifact_to_dict(artifact)
        self.assertEqual(tuple(data.keys()), module.MATERIALIZATION_ARTIFACT_FIELDS)
        self.assertEqual(module.materialization_artifact_from_dict(data), artifact)
        self.assertEqual(module.materialization_artifacts_to_dicts([artifact, artifact]), [data, data])

        data["source_evidence"][0]["source_id"] = "mutated"
        self.assertEqual(artifact.source_evidence[0]["source_id"], "SRC-1")

    def test_actor_requirement(self) -> None:
        module = artifact_module()
        with self.assertRaises(module.MaterializationArtifactError):
            module.create_materialization_artifact(
                self.make_candidate_data(candidate_type="documentation_candidate"),
                actor="",
                proposed_change_summary="Prepare documentation artifact.",
            )

        artifact = module.create_materialization_artifact(
            self.make_candidate_data(candidate_type="documentation_candidate"),
            actor="doc-owner@example.com",
            proposed_change_summary="Prepare documentation artifact.",
        )
        self.assertEqual(artifact.actor, "doc-owner@example.com")

    def test_rollback_requirement(self) -> None:
        module = artifact_module()
        with self.assertRaises(module.MaterializationArtifactError):
            module.create_materialization_artifact(
                self.make_candidate_data(candidate_type="parser_mapping_candidate"),
                actor="parser-owner@example.com",
                proposed_change_summary="Prepare parser mapping review artifact.",
            )

        artifact = module.create_materialization_artifact(
            self.make_candidate_data(candidate_type="documentation_candidate"),
            actor="doc-owner@example.com",
            proposed_change_summary="Prepare documentation artifact.",
        )
        self.assertEqual(artifact.rollback_plan, "")

    def test_creating_artifact_does_not_mutate_candidate_input(self) -> None:
        module = artifact_module()
        candidate = self.make_candidate_data(candidate_type="documentation_candidate")
        original = deepcopy(candidate)

        module.create_materialization_artifact(
            candidate,
            actor="doc-owner@example.com",
            proposed_change_summary="Prepare documentation artifact.",
        )

        self.assertEqual(candidate, original)

    def test_runtime_import_isolation(self) -> None:
        for path in python_files(RUNTIME_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.materialization_artifact", imports)
                self.assertNotIn("learning.materialization_artifact", imports)
                self.assertNotIn("materialization_artifact", imports)

                for imported in imports:
                    if imported == "src.learning" or imported.startswith("src.learning."):
                        self.fail(
                            f"{path.relative_to(ROOT)} imports {imported}; "
                            "runtime paths must not import materialization learning modules"
                        )

    def test_no_active_mutation_functions(self) -> None:
        tree = ast.parse(read_text(MODULE_PATH), filename=str(MODULE_PATH))
        function_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        for forbidden_name in FORBIDDEN_ACTIVE_FUNCTIONS:
            with self.subTest(function_name=forbidden_name):
                self.assertNotIn(forbidden_name, function_names)

    def make_candidate_data(
        self,
        candidate_type: str = "parser_mapping_candidate",
        status: str = "APPROVED_FOR_IMPLEMENTATION",
    ) -> dict[str, object]:
        component_by_type = {
            "parser_mapping_candidate": "parser",
            "scoring_weight_review_candidate": "scoring",
            "recommendation_rule_candidate": "recommendation",
            "dashboard_wording_candidate": "dashboard",
            "dashboard_interaction_candidate": "dashboard",
            "governance_workflow_candidate": "governance",
            "semantic_summary_candidate": "semantic_reviewer_assist",
            "documentation_candidate": "documentation",
            "validation_candidate": "validation",
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
