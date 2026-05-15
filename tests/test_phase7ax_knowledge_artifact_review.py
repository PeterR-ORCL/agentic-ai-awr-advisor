from __future__ import annotations

import ast
import importlib
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
WORKFLOW_DOC = DOCS / "phase7ax_knowledge_artifact_review_workflow.md"
MODEL_DOC = DOCS / "phase7ax_knowledge_artifact_review_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen1_knowledge_artifact_review.py"

RUNTIME_IMPORT_PATHS = (
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
    "subprocess",
    "oracledb",
    "cx_Oracle",
    "sqlite3",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "boto3",
    "botocore",
    "src.reporting",
    "src.parser",
    "src.parsing",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.analysis",
    "src.memory",
    "scripts.awr_memory_cli",
    "scripts.run_analysis",
    "oracle_agent_memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "persist_artifact_review",
    "approve_artifact",
    "reject_artifact",
    "request_artifact_revision",
    "create_learning_candidate",
    "create_materialization_artifact",
    "update_parser",
    "update_scoring",
    "update_recommendation",
    "mutate_phase4i",
    "write_database",
    "run_analysis",
    "auto_apply",
    "autonomous_apply",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


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


def function_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


class Phase7AXKnowledgeArtifactReviewTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen1_knowledge_artifact_review")

    def make_request(self, decision: str = "link_to_candidate", artifact_type: str = "parser_mapping_guidance", **overrides):
        module = self.module()
        values = {
            "artifact_review_request_id": module.make_artifact_review_request_id(
                "ARTIFACT-1",
                decision,
            ),
            "artifact_id": "ARTIFACT-1",
            "requested_decision": decision,
            "actor_id": "ACTOR-LOCAL-REVIEWER",
            "payload": {
                "artifact_type": artifact_type,
                "artifact_title": "Parser mapping guidance",
                "affected_component": "parser",
                "affected_domain": "load_profile",
                "rationale": "metadata only",
                "source_evidence": ["UNKNOWN-1"],
                "review_notes": ["preview only"],
            },
            "can_route_to_write_path": True,
            "notes": "unit test",
        }
        values.update(overrides)
        return module.KnowledgeArtifactReviewRequest(**values)

    def make_review(self, **overrides):
        module = self.module()
        values = {
            "artifact_review_id": module.make_artifact_review_id(
                "ARTIFACT-1",
                "link_to_candidate",
            ),
            "artifact_id": "ARTIFACT-1",
            "artifact_type": "parser_mapping_guidance",
            "artifact_title": "Parser mapping guidance",
            "review_decision": "link_to_candidate",
            "review_status": "linked_to_candidate",
            "reviewer_actor_id": "ACTOR-LOCAL-REVIEWER",
            "review_notes": ["metadata only"],
        }
        values.update(overrides)
        return module.KnowledgeArtifactReviewRecord(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "KnowledgeArtifactReviewRecord"))
        self.assertTrue(hasattr(module, "KnowledgeArtifactReviewRequest"))
        self.assertTrue(hasattr(module, "KnowledgeArtifactDecision"))
        self.assertTrue(hasattr(module, "ArtifactCandidateLinkIntent"))
        self.assertTrue(hasattr(module, "ArtifactMaterializationLinkIntent"))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_docs_exist(self) -> None:
        self.assertTrue(WORKFLOW_DOC.is_file(), WORKFLOW_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        text = lower_text(WORKFLOW_DOC) + "\n" + lower_text(MODEL_DOC)
        for phrase in (
            "no artifact review is persisted",
            "no artifact approval/rejection is executed",
            "no artifact revision request is persisted",
            "no candidate is created automatically",
            "no materialization artifact is created",
            "no parser/scoring/recommendation behavior changes occur",
            "no phase 4i mutation occurs",
            "deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_values_and_unsupported_values_fail(self) -> None:
        module = self.module()
        self.assertIn("parser_mapping_guidance", module.KNOWLEDGE_ARTIFACT_TYPES)
        self.assertIn("link_to_materialization", module.KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS)
        self.assertIn("linked_to_candidate", module.KNOWLEDGE_ARTIFACT_REVIEW_STATUSES)
        self.assertIn("materialization_review_required", module.KNOWLEDGE_ARTIFACT_FOLLOWUP_TYPES)

        with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
            self.make_request(decision="unsupported")
        with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
            self.make_review(artifact_type="unsupported")
        with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
            self.make_review(review_status="unsupported")

    def test_review_record_validation_rejects_unsafe_flags(self) -> None:
        module = self.module()
        review = self.make_review()
        self.assertIs(module.validate_artifact_review_record(review), review)

        for field_name in (
            "write_performed",
            "artifact_approved",
            "artifact_rejected",
            "artifact_revision_requested",
            "materialization_created",
            "candidate_created",
            "runtime_influence",
            "phase4i_mutation_requested",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
                    self.make_review(**{field_name: True})

    def test_review_request_validation(self) -> None:
        module = self.module()
        request = self.make_request()
        self.assertIs(module.validate_artifact_review_request(request), request)

        with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
            module.validate_artifact_review_request(
                self.make_request(actor_id=None, actor_audit_context=None)
            )
        with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
            self.make_request(decision="unsupported")

        for field_name in (
            "write_performed",
            "artifact_approved",
            "artifact_rejected",
            "artifact_revision_requested",
            "materialization_created",
            "candidate_created",
            "runtime_influence",
            "phase4i_mutation_requested",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
                    self.make_request(**{field_name: True})

    def test_decision_validation(self) -> None:
        module = self.module()
        request = self.make_request("request_revision")
        decision = module.build_artifact_decision_for_request(request)
        self.assertIs(module.validate_artifact_decision(decision), decision)
        self.assertEqual(decision.followup_type, "artifact_revision_required")

        with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
            module.validate_artifact_decision(
                module.KnowledgeArtifactDecision(
                    artifact_decision_id="DECISION-1",
                    artifact_review_id="REVIEW-1",
                    decision_type="add_review_note",
                    decision_status="under_review",
                )
            )
        with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
            module.KnowledgeArtifactDecision(
                artifact_decision_id="DECISION-2",
                artifact_review_id="REVIEW-1",
                decision_type="add_review_note",
                decision_status="under_review",
                actor_id="ACTOR-LOCAL-REVIEWER",
                runtime_influence=True,
            )

    def test_candidate_link_intent_mapping(self) -> None:
        module = self.module()
        expected = {
            "parser_mapping_guidance": "parser_mapping_candidate",
            "scoring_review_guidance": "scoring_weight_review_candidate",
            "recommendation_rule_guidance": "recommendation_rule_candidate",
        }
        for artifact_type, candidate_type in expected.items():
            with self.subTest(artifact_type=artifact_type):
                intent = module.build_candidate_link_intent_for_request(
                    self.make_request("link_to_candidate", artifact_type)
                )
                self.assertIsNotNone(intent)
                self.assertEqual(intent.candidate_type, candidate_type)
                self.assertFalse(intent.candidate_created)
                self.assertTrue(intent.requires_human_review)
                self.assertFalse(intent.runtime_influence)

    def test_materialization_link_intent_mapping(self) -> None:
        module = self.module()
        expected = {
            "parser_mapping_guidance": "parser_mapping_artifact",
            "scoring_review_guidance": "scoring_review_artifact",
            "recommendation_rule_guidance": "recommendation_rule_artifact",
        }
        for artifact_type, materialization_type in expected.items():
            with self.subTest(artifact_type=artifact_type):
                intent = module.build_materialization_link_intent_for_request(
                    self.make_request("link_to_materialization", artifact_type)
                )
                self.assertIsNotNone(intent)
                self.assertEqual(intent.materialization_type, materialization_type)
                self.assertFalse(intent.materialization_created)
                self.assertFalse(intent.runtime_influence)
                self.assertFalse(intent.phase4i_mutation_requested)

    def test_review_validation_and_routing(self) -> None:
        module = self.module()
        request = self.make_request(can_route_to_write_path=True)
        validation = module.evaluate_artifact_review_request(request)
        self.assertTrue(validation.valid)
        self.assertTrue(validation.can_route_to_write_path)
        self.assertFalse(validation.write_performed)
        self.assertFalse(validation.artifact_approved)
        self.assertFalse(validation.materialization_created)
        self.assertFalse(validation.candidate_created)

        routed = module.route_artifact_review_request(request)
        self.assertIsNotNone(routed["candidate_link_intent"])
        self.assertIsNone(routed["materialization_link_intent"])
        self.assertEqual(
            routed["review_record"]["review_status"],
            "linked_to_candidate",
        )

        with self.assertRaises(module.Screen1KnowledgeArtifactReviewError):
            module.KnowledgeArtifactReviewValidation(
                validation_id="VALIDATION-1",
                artifact_review_request_id="REQUEST-1",
                valid=True,
                validation_status="VALID_METADATA_ONLY",
                requested_decision="add_review_note",
                actor_present=True,
                artifact_present=True,
                can_route_to_write_path=True,
                candidate_created=True,
            )

    def test_serialization_round_trip(self) -> None:
        module = self.module()
        request = self.make_request()
        validation = module.evaluate_artifact_review_request(request)
        review = self.make_review()
        decision = module.build_artifact_decision_for_request(request)
        candidate_intent = module.build_candidate_link_intent_for_request(request)
        materialization_intent = module.build_materialization_link_intent_for_request(
            self.make_request("link_to_materialization")
        )
        self.assertIsNotNone(candidate_intent)
        self.assertIsNotNone(materialization_intent)

        review_dict = module.artifact_review_record_to_dict(review)
        request_dict = module.artifact_review_request_to_dict(request)
        validation_dict = module.artifact_review_validation_to_dict(validation)
        decision_dict = module.artifact_decision_to_dict(decision)
        candidate_dict = module.candidate_link_intent_to_dict(candidate_intent)
        materialization_dict = module.materialization_link_intent_to_dict(
            materialization_intent
        )

        self.assertEqual(
            review_dict,
            module.artifact_review_record_to_dict(
                module.artifact_review_record_from_dict(review_dict)
            ),
        )
        self.assertEqual(
            request_dict,
            module.artifact_review_request_to_dict(
                module.artifact_review_request_from_dict(request_dict)
            ),
        )
        self.assertEqual(
            validation_dict,
            module.artifact_review_validation_to_dict(
                module.artifact_review_validation_from_dict(validation_dict)
            ),
        )
        self.assertEqual(
            decision_dict,
            module.artifact_decision_to_dict(
                module.artifact_decision_from_dict(decision_dict)
            ),
        )
        self.assertEqual(
            candidate_dict,
            module.candidate_link_intent_to_dict(
                module.candidate_link_intent_from_dict(candidate_dict)
            ),
        )
        self.assertEqual(
            materialization_dict,
            module.materialization_link_intent_to_dict(
                module.materialization_link_intent_from_dict(materialization_dict)
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        first = module.make_artifact_review_id("ARTIFACT-1", "link_to_candidate")
        second = module.make_artifact_review_id("ARTIFACT-1", "link_to_candidate")
        self.assertEqual(first, second)
        self.assertEqual(
            module.make_artifact_review_request_id("ARTIFACT-1", "link_to_candidate"),
            module.make_artifact_review_request_id("ARTIFACT-1", "link_to_candidate"),
        )
        self.assertEqual(
            module.make_artifact_candidate_link_intent_id(
                "ARTIFACT-1",
                "parser_mapping_candidate",
            ),
            module.make_artifact_candidate_link_intent_id(
                "ARTIFACT-1",
                "parser_mapping_candidate",
            ),
        )
        self.assertNotIn("UUID", first.upper())

    def test_no_mutation_or_persistence_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen1_knowledge_artifact_review",
            "learning.screen1_knowledge_artifact_review",
            "screen1_knowledge_artifact_review",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen1_knowledge_artifact_review", imports)
                self.assertNotIn("learning.screen1_knowledge_artifact_review", imports)
                self.assertNotIn("screen1_knowledge_artifact_review", imports)
                self.assertNotIn("screen1_knowledge_artifact_review", source)


if __name__ == "__main__":
    unittest.main()
