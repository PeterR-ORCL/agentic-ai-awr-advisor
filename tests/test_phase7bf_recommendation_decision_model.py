from __future__ import annotations

import ast
import importlib
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
MODEL_DOC = DOCS / "phase7bf_recommendation_decision_model.md"
LIFECYCLE_DOC = DOCS / "phase7bf_recommendation_decision_lifecycle.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen5_recommendation_decision.py"

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

FORBIDDEN_SOURCE_TERMS = (
    "persist_recommendation_decision",
    "create_action_record",
    "create_outcome_record",
    "create_feedback_record",
    "update_recommendation",
    "mutate_recommendation",
    "write_database",
    "run_analysis",
    "auto_apply",
    "autonomous_apply",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


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


def python_files(paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
    return files


class Phase7BFRecommendationDecisionModelTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen5_recommendation_decision")

    def make_record(self, **overrides):
        module = self.module()
        decision_type = overrides.get("decision_type", "accept_recommendation")
        recommendation_id = overrides.get("recommendation_id", "RECO-CPU-001")
        values = {
            "decision_id": module.create_recommendation_decision_id(
                recommendation_id,
                decision_type,
                run_id="RUN-1",
            ),
            "recommendation_id": recommendation_id,
            "run_id": "RUN-1",
            "awr_id": "AWR-1",
            "domain": "CPU",
            "recommendation_title": "Tune CPU workload",
            "decision_type": decision_type,
            "decision_status": module.decision_status_for_type(decision_type),
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "decision_rationale": "Accepted during unit test",
            "decision_notes": "metadata only",
            "requires_followup": True,
            "followup_type": module.followup_type_for_decision(decision_type),
        }
        values.update(overrides)
        return module.RecommendationDecisionRecord(**values)

    def make_request(self, **overrides):
        module = self.module()
        requested_decision = overrides.get(
            "requested_decision",
            "accept_recommendation",
        )
        recommendation_id = overrides.get("recommendation_id", "RECO-CPU-001")
        if recommendation_id:
            request_id = module.create_recommendation_decision_request_id(
                recommendation_id,
                requested_decision,
            )
        else:
            request_id = "SCREEN5-RECO-REQUEST-MISSING-RECOMMENDATION"
        values = {
            "request_id": request_id,
            "recommendation_id": recommendation_id,
            "requested_decision": requested_decision,
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "payload": {"rationale": "unit test"},
            "validation_status": "valid",
            "can_route_to_write_path": True,
            "write_performed": False,
        }
        values.update(overrides)
        return module.RecommendationDecisionRequest(**values)

    def make_validation(self, **overrides):
        module = self.module()
        request = overrides.pop("request", self.make_request())
        values = {
            "validation_id": module.create_recommendation_decision_validation_id(
                request.request_id,
            ),
            "request_id": request.request_id,
            "valid": True,
            "validation_status": "valid",
            "requested_decision": request.requested_decision,
            "actor_present": True,
            "recommendation_present": True,
            "can_route_to_write_path": True,
            "write_performed": False,
            "denied_reasons": [],
            "warnings": ["metadata only"],
            "required_next_steps": ["future governed write path"],
        }
        values.update(overrides)
        return module.RecommendationDecisionValidation(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "RecommendationDecisionRecord"))
        self.assertTrue(hasattr(module, "RecommendationDecisionRequest"))
        self.assertTrue(hasattr(module, "RecommendationDecisionValidation"))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_docs_exist_and_contain_required_boundary_phrases(self) -> None:
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        self.assertTrue(LIFECYCLE_DOC.is_file(), LIFECYCLE_DOC)
        text = lower_text(MODEL_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for phrase in (
            "recommendation decisions do not change recommendation truth",
            "recommendation decisions do not change recommendation ranking",
            "recommendation decisions do not change recommendation text/evidence/action sequencing",
            "write_performed=false in 7bf",
            "runtime_influence=false",
            "phase 4i mutation is forbidden",
            "action/outcome/feedback records are future phases",
            "deterministic runtime remains authoritative",
            "no lifecycle stage writes records in 7bf",
            "decision validation is not persistence",
            "follow-up classification is metadata only",
            "future workflows cannot skip actor",
            "future workflows cannot skip governed write path",
            "decisions cannot mutate recommendation truth",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_decision_types_statuses_followups(self) -> None:
        module = self.module()
        self.assertEqual(
            module.RECOMMENDATION_DECISION_TYPES,
            (
                "accept_recommendation",
                "reject_recommendation",
                "defer_recommendation",
                "mark_not_applicable",
                "request_recommendation_review",
                "request_learning_candidate",
            ),
        )
        self.assertEqual(
            module.RECOMMENDATION_DECISION_STATUSES,
            (
                "proposed",
                "accepted",
                "rejected",
                "deferred",
                "not_applicable",
                "under_review",
                "routed_to_governance",
                "closed",
            ),
        )
        self.assertEqual(
            module.RECOMMENDATION_FOLLOWUP_TYPES,
            (
                "none",
                "action_required",
                "outcome_required",
                "feedback_required",
                "recommendation_review_required",
                "learning_candidate_review_required",
                "human_review_required",
            ),
        )
        with self.assertRaises(module.Screen5RecommendationDecisionError):
            module.decision_status_for_type("approve_runtime")
        with self.assertRaises(module.Screen5RecommendationDecisionError):
            self.make_record(decision_status="runtime_applied")
        with self.assertRaises(module.Screen5RecommendationDecisionError):
            self.make_record(followup_type="runtime_change")

    def test_decision_type_mapping(self) -> None:
        module = self.module()
        expected = {
            "accept_recommendation": ("accepted", "action_required"),
            "reject_recommendation": ("rejected", "feedback_required"),
            "defer_recommendation": ("deferred", "human_review_required"),
            "mark_not_applicable": ("not_applicable", "feedback_required"),
            "request_recommendation_review": (
                "under_review",
                "recommendation_review_required",
            ),
            "request_learning_candidate": (
                "routed_to_governance",
                "learning_candidate_review_required",
            ),
        }
        for decision_type, (status, followup) in expected.items():
            with self.subTest(decision_type=decision_type):
                self.assertEqual(status, module.decision_status_for_type(decision_type))
                self.assertEqual(
                    followup,
                    module.followup_type_for_decision(decision_type),
                )
                if decision_type == "request_recommendation_review":
                    self.assertIn(
                        module.decision_status_for_type(decision_type),
                        ("under_review", "routed_to_governance"),
                    )

    def test_recommendation_decision_record_validation(self) -> None:
        module = self.module()
        record = self.make_record()
        self.assertIs(module.validate_recommendation_decision_record(record), record)
        self.assertFalse(record.write_performed)
        self.assertFalse(record.runtime_influence)
        self.assertFalse(record.phase4i_mutation_requested)

        for overrides in (
            {"recommendation_id": ""},
            {"actor_id": ""},
            {"write_performed": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
            {"decision_status": "unsupported"},
            {"followup_type": "unsupported"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen5RecommendationDecisionError):
                    self.make_record(**overrides)

    def test_recommendation_decision_request_validation(self) -> None:
        module = self.module()
        request = self.make_request()
        self.assertIs(module.validate_recommendation_decision_request(request), request)
        self.assertTrue(request.can_route_to_write_path)
        self.assertFalse(request.write_performed)

        with self.assertRaises(module.Screen5RecommendationDecisionError):
            module.validate_recommendation_decision_request(
                self.make_request(actor_id="")
            )
        with self.assertRaises(module.Screen5RecommendationDecisionError):
            self.make_request(requested_decision="unsupported_decision")
        with self.assertRaises(module.Screen5RecommendationDecisionError):
            self.make_request(write_performed=True)
        with self.assertRaises(module.Screen5RecommendationDecisionError):
            self.make_request(runtime_influence=True)
        with self.assertRaises(module.Screen5RecommendationDecisionError):
            self.make_request(phase4i_mutation_requested=True)

    def test_recommendation_decision_validation_validation(self) -> None:
        module = self.module()
        validation = self.make_validation()
        self.assertIs(
            module.validate_recommendation_decision_validation(validation),
            validation,
        )

        for overrides in (
            {"write_performed": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
            {"validation_status": "runtime_applied"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen5RecommendationDecisionError):
                    self.make_validation(**overrides)

    def test_evaluation_metadata_only(self) -> None:
        module = self.module()
        missing_actor = module.evaluate_recommendation_decision_request(
            self.make_request(actor_id="")
        )
        self.assertFalse(missing_actor.valid)
        self.assertEqual("needs_actor", missing_actor.validation_status)
        self.assertFalse(missing_actor.write_performed)

        missing_recommendation = module.evaluate_recommendation_decision_request(
            self.make_request(recommendation_id=None)
        )
        self.assertFalse(missing_recommendation.valid)
        self.assertEqual(
            "needs_recommendation",
            missing_recommendation.validation_status,
        )

        valid = module.evaluate_recommendation_decision_request(self.make_request())
        self.assertTrue(valid.valid)
        self.assertEqual("valid", valid.validation_status)
        self.assertFalse(valid.write_performed)
        self.assertFalse(valid.runtime_influence)
        self.assertFalse(valid.phase4i_mutation_requested)

    def test_serialization_round_trips_are_deterministic(self) -> None:
        module = self.module()
        objects = (
            (
                module.recommendation_decision_record_to_dict,
                module.recommendation_decision_record_from_dict,
                self.make_record(),
            ),
            (
                module.recommendation_decision_request_to_dict,
                module.recommendation_decision_request_from_dict,
                self.make_request(),
            ),
            (
                module.recommendation_decision_validation_to_dict,
                module.recommendation_decision_validation_from_dict,
                self.make_validation(),
            ),
        )
        for to_dict, from_dict, value in objects:
            with self.subTest(value=type(value).__name__):
                serialized = to_dict(value)
                self.assertEqual(to_dict(from_dict(serialized)), serialized)
                self.assertEqual(
                    to_dict(from_dict(serialized)),
                    to_dict(from_dict(serialized)),
                )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        ids = (
            module.create_recommendation_decision_id(
                "RECO-CPU-001",
                "accept_recommendation",
                run_id="RUN-1",
            ),
            module.create_recommendation_decision_request_id(
                "RECO-CPU-001",
                "accept_recommendation",
            ),
            module.create_recommendation_decision_validation_id(
                "SCREEN5-RECO-REQUEST-RECO-CPU-001-ACCEPT-RECOMMENDATION"
            ),
        )
        self.assertEqual(
            ids[0],
            module.create_recommendation_decision_id(
                "RECO-CPU-001",
                "accept_recommendation",
                run_id="RUN-1",
            ),
        )
        self.assertEqual(
            ids[1],
            module.create_recommendation_decision_request_id(
                "RECO-CPU-001",
                "accept_recommendation",
            ),
        )
        self.assertEqual(
            ids[2],
            module.create_recommendation_decision_validation_id(
                "SCREEN5-RECO-REQUEST-RECO-CPU-001-ACCEPT-RECOMMENDATION"
            ),
        )
        for value in ids:
            with self.subTest(value=value):
                self.assertFalse(
                    re.search(
                        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                        value.lower(),
                    )
                )

    def test_no_mutation_or_persistence_functions(self) -> None:
        names = function_names(MODULE_PATH)
        source = read_text(MODULE_PATH)
        for forbidden in FORBIDDEN_SOURCE_TERMS:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)
                self.assertNotIn(forbidden, source)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen5_recommendation_decision",
            "learning.screen5_recommendation_decision",
            "screen5_recommendation_decision",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen5_recommendation_decision", imports)
                self.assertNotIn("learning.screen5_recommendation_decision", imports)
                self.assertNotIn("screen5_recommendation_decision", imports)
                self.assertNotIn("screen5_recommendation_decision", source)


if __name__ == "__main__":
    unittest.main()
