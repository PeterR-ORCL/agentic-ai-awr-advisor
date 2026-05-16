from __future__ import annotations

import ast
import importlib
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
MODULE_PATH = ROOT / "src" / "learning" / "screen6_candidate_review.py"
UI_DOC = DOCS / "phase7bl_learning_candidate_review_ui.md"
MODEL_DOC = DOCS / "phase7bl_learning_candidate_review_model.md"

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
    "persist_candidate_review",
    "persist_review_record",
    "update_candidate_status",
    "approve_candidate",
    "reject_candidate",
    "request_candidate_revision",
    "close_candidate_record",
    "attach_materialization_reference",
    "create_materialization_artifact",
    "invoke_governed_write_path",
    "call_backend",
    "run_analysis",
    "activate_runtime",
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


class Phase7BLLearningCandidateReviewTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen6_candidate_review")

    def make_request(self, **overrides):
        module = self.module()
        candidate_id = overrides.get("candidate_id", "CAND-CPU-001")
        requested_action = overrides.get("requested_action", "mark_under_review")
        if candidate_id and requested_action in module.LEARNING_CANDIDATE_REVIEW_ACTIONS:
            request_id = module.create_learning_candidate_review_request_id(
                candidate_id,
                requested_action,
            )
        else:
            request_id = "SCREEN6-CANDIDATE-REVIEW-REQUEST-LOCAL-TEST"
        values = {
            "review_request_id": request_id,
            "candidate_id": candidate_id,
            "candidate_type": "parser_mapping_candidate",
            "requested_action": requested_action,
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "governance_note": "preview note",
            "materialization_reference": "MAT-PREVIEW-001",
            "payload": {"reason": "unit test"},
            "validation_status": "preview_only",
            "can_route_to_write_path": False,
            "write_performed": False,
            "candidate_status_changed": False,
            "materialization_reference_attached": False,
            "runtime_influence": False,
            "runtime_activation_requested": False,
            "phase4i_mutation_requested": False,
            "created_at": "2026-05-16T00:00:00Z",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.LearningCandidateReviewRequest(**values)

    def make_result(self, **overrides):
        module = self.module()
        request = overrides.pop("request", self.make_request())
        values = {
            "review_result_id": module.create_learning_candidate_review_result_id(
                request.review_request_id,
            ),
            "review_request_id": request.review_request_id,
            "candidate_id": request.candidate_id or "CAND-CPU-001",
            "requested_action": request.requested_action,
            "result_status": "valid_for_future_review",
            "candidate_status_changed": False,
            "proposed_next_status": module.proposed_next_status_for_action(
                request.requested_action
            )
            if request.requested_action in module.LEARNING_CANDIDATE_REVIEW_ACTIONS
            else None,
            "governance_action_performed": False,
            "materialization_reference_attached": False,
            "write_performed": False,
            "denied_reasons": [],
            "warnings": ["preview only"],
            "required_next_steps": ["future governed write path"],
            "runtime_influence": False,
            "runtime_activation_requested": False,
            "phase4i_mutation_requested": False,
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.LearningCandidateReviewResult(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "LearningCandidateReviewRequest"))
        self.assertTrue(hasattr(module, "LearningCandidateReviewResult"))

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
        self.assertTrue(UI_DOC.is_file(), UI_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        text = lower_text(UI_DOC) + "\n" + lower_text(MODEL_DOC)
        for phrase in (
            "no candidate status is changed",
            "no governance action is performed",
            "no materialization reference is attached",
            "no runtime activation occurs",
            "controls are disabled/preview-only",
            "deterministic runtime remains authoritative",
            "write_performed=false",
            "candidate_status_changed=false",
            "materialization_reference_attached=false",
            "runtime_influence=false",
            "runtime_activation_requested=false",
            "phase4i_mutation_requested=false",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_actions_candidate_types_and_statuses(self) -> None:
        module = self.module()
        self.assertEqual(
            module.LEARNING_CANDIDATE_REVIEW_ACTIONS,
            (
                "mark_under_review",
                "approve_for_implementation",
                "reject",
                "request_revision",
                "close_candidate",
                "add_governance_note",
                "attach_materialization_reference",
            ),
        )
        self.assertEqual(
            module.LEARNING_CANDIDATE_REVIEW_CANDIDATE_TYPES,
            (
                "parser_mapping_candidate",
                "recommendation_rule_candidate",
                "scoring_weight_review_candidate",
                "dashboard_wording_candidate",
                "dashboard_interaction_candidate",
                "governance_workflow_candidate",
                "semantic_summary_candidate",
                "documentation_candidate",
                "validation_candidate",
            ),
        )
        self.assertEqual(
            module.LEARNING_CANDIDATE_REVIEW_RESULT_STATUSES,
            (
                "preview_only",
                "valid_for_future_review",
                "needs_actor",
                "needs_candidate",
                "unsupported_action",
                "write_not_allowed_in_this_phase",
                "blocked_by_runtime_safety",
            ),
        )
        self.assertEqual(
            module.proposed_next_status_for_action("approve_for_implementation"),
            "approved_for_implementation",
        )
        with self.assertRaises(module.Screen6CandidateReviewError):
            module.proposed_next_status_for_action("activate_runtime")

    def test_request_validation(self) -> None:
        module = self.module()
        request = self.make_request()
        self.assertIs(module.validate_learning_candidate_review_request(request), request)

        for overrides in (
            {"candidate_id": ""},
            {"candidate_type": "unsupported_candidate"},
            {"requested_action": "activate_runtime"},
            {"actor_id": ""},
            {"payload": []},
            {"write_performed": True},
            {"candidate_status_changed": True},
            {"materialization_reference_attached": True},
            {"runtime_influence": True},
            {"runtime_activation_requested": True},
            {"phase4i_mutation_requested": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen6CandidateReviewError):
                    module.validate_learning_candidate_review_request(
                        self.make_request(**overrides)
                    )

    def test_result_validation(self) -> None:
        module = self.module()
        result = self.make_result()
        self.assertIs(module.validate_learning_candidate_review_result(result), result)
        self.assertFalse(result.candidate_status_changed)
        self.assertFalse(result.governance_action_performed)
        self.assertFalse(result.materialization_reference_attached)
        self.assertFalse(result.write_performed)

        for overrides in (
            {"review_result_id": ""},
            {"review_request_id": ""},
            {"candidate_id": ""},
            {"requested_action": "activate_runtime"},
            {"result_status": "runtime_applied"},
            {"candidate_status_changed": True},
            {"governance_action_performed": True},
            {"materialization_reference_attached": True},
            {"write_performed": True},
            {"runtime_influence": True},
            {"runtime_activation_requested": True},
            {"phase4i_mutation_requested": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen6CandidateReviewError):
                    module.validate_learning_candidate_review_result(
                        self.make_result(**overrides)
                    )

    def test_evaluation_behavior(self) -> None:
        module = self.module()

        valid_result = module.evaluate_learning_candidate_review_request(
            self.make_request(requested_action="approve_for_implementation")
        )
        self.assertEqual(valid_result.result_status, "valid_for_future_review")
        self.assertEqual(valid_result.proposed_next_status, "approved_for_implementation")
        self.assertFalse(valid_result.write_performed)
        self.assertFalse(valid_result.candidate_status_changed)
        self.assertFalse(valid_result.governance_action_performed)
        self.assertFalse(valid_result.materialization_reference_attached)
        self.assertFalse(valid_result.runtime_influence)
        self.assertFalse(valid_result.runtime_activation_requested)
        self.assertFalse(valid_result.phase4i_mutation_requested)

        needs_actor = module.evaluate_learning_candidate_review_request(
            self.make_request(actor_id=None)
        )
        self.assertEqual(needs_actor.result_status, "needs_actor")

        needs_candidate = module.evaluate_learning_candidate_review_request(
            self.make_request(candidate_id=None)
        )
        self.assertEqual(needs_candidate.result_status, "needs_candidate")

        unsupported_action = module.evaluate_learning_candidate_review_request(
            self.make_request(requested_action="activate_runtime")
        )
        self.assertEqual(unsupported_action.result_status, "unsupported_action")
        self.assertFalse(unsupported_action.write_performed)

    def test_serialization_round_trips(self) -> None:
        module = self.module()
        request = self.make_request()
        result = module.evaluate_learning_candidate_review_request(request)

        request_data = module.learning_candidate_review_request_to_dict(request)
        result_data = module.learning_candidate_review_result_to_dict(result)

        self.assertEqual(
            request_data,
            module.learning_candidate_review_request_to_dict(
                module.learning_candidate_review_request_from_dict(request_data)
            ),
        )
        self.assertEqual(
            result_data,
            module.learning_candidate_review_result_to_dict(
                module.learning_candidate_review_result_from_dict(result_data)
            ),
        )
        self.assertFalse(request_data["write_performed"])
        self.assertFalse(result_data["candidate_status_changed"])
        self.assertFalse(result_data["materialization_reference_attached"])

    def test_deterministic_ids(self) -> None:
        module = self.module()
        first = module.create_learning_candidate_review_request_id(
            "CAND-CPU-001",
            "mark_under_review",
        )
        second = module.create_learning_candidate_review_request_id(
            "CAND-CPU-001",
            "mark_under_review",
        )
        different = module.create_learning_candidate_review_request_id(
            "CAND-CPU-001",
            "reject",
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertTrue(
            first.startswith("SCREEN6-CANDIDATE-REVIEW-REQUEST-CAND-CPU-001")
        )
        result_id = module.create_learning_candidate_review_result_id(first)
        self.assertEqual(
            result_id,
            module.create_learning_candidate_review_result_id(first),
        )
        self.assertTrue(result_id.startswith("SCREEN6-CANDIDATE-REVIEW-RESULT-"))

    def test_no_mutation_or_persistence_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)

    def test_runtime_import_isolation(self) -> None:
        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen6_candidate_review", imports)
                self.assertNotIn("learning.screen6_candidate_review", imports)
                self.assertNotIn("screen6_candidate_review", imports)
                self.assertNotIn("screen6_candidate_review", source)

    def test_existing_7bk_boundary_remains_inert(self) -> None:
        boundary = importlib.import_module("src.learning.screen6_governance_control_boundary")
        summary = boundary.screen6_governance_control_boundary_summary()
        self.assertTrue(summary["boundary_only"])
        self.assertFalse(summary["workflow_implemented"])
        self.assertFalse(summary["governance_records_persisted"])
        self.assertFalse(summary["candidate_status_changed"])
        self.assertFalse(summary["runtime_activation_occurred"])

        completed = subprocess.run(
            (
                "python3",
                "-m",
                "unittest",
                "tests/test_phase7bk_screen6_governance_control_boundary.py",
            ),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )


if __name__ == "__main__":
    unittest.main()
