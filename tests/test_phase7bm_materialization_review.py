from __future__ import annotations

import ast
import importlib
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
MODULE_PATH = ROOT / "src" / "learning" / "screen6_materialization_review.py"
UI_DOC = DOCS / "phase7bm_materialization_review_ui.md"
MODEL_DOC = DOCS / "phase7bm_materialization_review_model.md"
README = DOCS / "README.md"

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
    "persist_materialization_review",
    "persist_review_record",
    "update_materialization_status",
    "approve_materialization",
    "reject_materialization",
    "create_materialization_artifact",
    "mutate_materialization_artifact",
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


class Phase7BMMaterializationReviewTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen6_materialization_review")

    def make_request(self, **overrides):
        module = self.module()
        materialization_id = overrides.get("materialization_id", "MAT-CPU-001")
        requested_action = overrides.get("requested_action", "mark_under_review")
        if materialization_id and requested_action in module.MATERIALIZATION_REVIEW_ACTIONS:
            request_id = module.create_materialization_review_request_id(
                materialization_id,
                requested_action,
            )
        else:
            request_id = "SCREEN6-MATERIALIZATION-REVIEW-REQUEST-LOCAL-TEST"
        values = {
            "review_request_id": request_id,
            "materialization_id": materialization_id,
            "materialization_type": "parser_mapping_artifact",
            "requested_action": requested_action,
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "governance_note": "preview materialization note",
            "validation_reference": "VAL-PREVIEW-001",
            "rollback_reference": "RB-PREVIEW-001",
            "payload": {"reason": "unit test"},
            "validation_status": "preview_only",
            "can_route_to_write_path": False,
            "write_performed": False,
            "materialization_status_changed": False,
            "validation_reference_attached": False,
            "rollback_reference_attached": False,
            "runtime_activation_requested": False,
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "created_at": "2026-05-16T00:00:00Z",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.MaterializationReviewRequest(**values)

    def make_result(self, **overrides):
        module = self.module()
        request = overrides.pop("request", self.make_request())
        values = {
            "review_result_id": module.create_materialization_review_result_id(
                request.review_request_id,
            ),
            "review_request_id": request.review_request_id,
            "materialization_id": request.materialization_id or "MAT-CPU-001",
            "materialization_type": request.materialization_type,
            "requested_action": request.requested_action,
            "result_status": "valid_for_future_review",
            "materialization_status_changed": False,
            "proposed_next_status": module.proposed_next_status_for_action(
                request.requested_action
            )
            if request.requested_action in module.MATERIALIZATION_REVIEW_ACTIONS
            else None,
            "governance_action_performed": False,
            "validation_reference_attached": False,
            "rollback_reference_attached": False,
            "write_performed": False,
            "denied_reasons": [],
            "warnings": ["preview only"],
            "required_next_steps": ["future governed write path"],
            "runtime_activation_requested": False,
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.MaterializationReviewResult(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "MaterializationReviewRequest"))
        self.assertTrue(hasattr(module, "MaterializationReviewResult"))

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
            "no materialization status is changed",
            "no governance action is performed",
            "no validation reference is attached",
            "no rollback reference is attached",
            "no runtime activation is requested",
            "no governed write path is invoked",
            "controls are disabled/preview-only",
            "deterministic runtime remains authoritative",
            "write_performed=false",
            "materialization_status_changed=false",
            "validation_reference_attached=false",
            "rollback_reference_attached=false",
            "runtime_activation_requested=false",
            "runtime_influence=false",
            "phase4i_mutation_requested=false",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_actions_materialization_types_and_statuses(self) -> None:
        module = self.module()
        self.assertEqual(
            module.MATERIALIZATION_REVIEW_ACTIONS,
            (
                "mark_under_review",
                "approve_for_validation",
                "reject",
                "request_revision",
                "attach_validation_reference",
                "attach_rollback_reference",
                "mark_validated",
                "mark_implemented",
                "close_materialization",
                "add_materialization_note",
            ),
        )
        self.assertEqual(
            module.MATERIALIZATION_REVIEW_TYPES,
            (
                "parser_mapping_artifact",
                "scoring_review_artifact",
                "recommendation_rule_artifact",
                "dashboard_wording_artifact",
                "dashboard_interaction_artifact",
                "governance_workflow_artifact",
                "semantic_summary_artifact",
                "documentation_artifact",
                "validation_artifact",
                "unknown",
            ),
        )
        self.assertEqual(
            module.MATERIALIZATION_REVIEW_RESULT_STATUSES,
            (
                "preview_only",
                "valid_for_future_review",
                "needs_actor",
                "needs_materialization",
                "needs_validation_reference",
                "needs_rollback_reference",
                "unsupported_action",
                "write_not_allowed_in_this_phase",
                "blocked_by_runtime_safety",
            ),
        )
        self.assertEqual(
            module.proposed_next_status_for_action("approve_for_validation"),
            "approved_for_validation",
        )

    def test_request_validation(self) -> None:
        module = self.module()
        request = self.make_request(requested_action="approve_for_validation")
        self.assertIs(module.validate_materialization_review_request(request), request)

        invalid_cases = (
            {"materialization_id": None},
            {"materialization_type": "unsupported_artifact"},
            {"requested_action": "deploy_artifact"},
            {"actor_id": None},
            {"payload": "not-a-dict"},
            {"write_performed": True},
            {"materialization_status_changed": True},
            {"validation_reference_attached": True},
            {"rollback_reference_attached": True},
            {"runtime_activation_requested": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
        )
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen6MaterializationReviewError):
                    module.validate_materialization_review_request(
                        self.make_request(**overrides)
                    )

    def test_result_validation(self) -> None:
        module = self.module()
        result = self.make_result()
        self.assertIs(module.validate_materialization_review_result(result), result)

        invalid_cases = (
            {"requested_action": "deploy_artifact"},
            {"result_status": "runtime_active"},
            {"materialization_status_changed": True},
            {"governance_action_performed": True},
            {"validation_reference_attached": True},
            {"rollback_reference_attached": True},
            {"write_performed": True},
            {"runtime_activation_requested": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
        )
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen6MaterializationReviewError):
                    module.validate_materialization_review_result(
                        self.make_result(**overrides)
                    )

    def test_evaluation_behavior_is_preview_only(self) -> None:
        module = self.module()
        valid = module.evaluate_materialization_review_request(
            self.make_request(requested_action="approve_for_validation")
        )
        self.assertEqual(valid.result_status, "valid_for_future_review")
        self.assertEqual(valid.proposed_next_status, "approved_for_validation")
        self.assertFalse(valid.materialization_status_changed)
        self.assertFalse(valid.governance_action_performed)
        self.assertFalse(valid.validation_reference_attached)
        self.assertFalse(valid.rollback_reference_attached)
        self.assertFalse(valid.write_performed)
        self.assertFalse(valid.runtime_activation_requested)
        self.assertFalse(valid.runtime_influence)
        self.assertFalse(valid.phase4i_mutation_requested)

        cases = (
            ({"actor_id": None}, "needs_actor"),
            ({"materialization_id": None}, "needs_materialization"),
            (
                {
                    "requested_action": "attach_validation_reference",
                    "validation_reference": None,
                },
                "needs_validation_reference",
            ),
            (
                {
                    "requested_action": "attach_rollback_reference",
                    "rollback_reference": None,
                },
                "needs_rollback_reference",
            ),
            ({"requested_action": "deploy_artifact"}, "unsupported_action"),
        )
        for overrides, expected_status in cases:
            with self.subTest(overrides=overrides):
                result = module.evaluate_materialization_review_request(
                    self.make_request(**overrides)
                )
                self.assertEqual(result.result_status, expected_status)
                self.assertFalse(result.write_performed)
                self.assertFalse(result.materialization_status_changed)
                self.assertFalse(result.validation_reference_attached)
                self.assertFalse(result.rollback_reference_attached)
                self.assertFalse(result.runtime_activation_requested)

    def test_serialization_round_trip(self) -> None:
        module = self.module()
        request = self.make_request(requested_action="attach_validation_reference")
        request_dict = module.materialization_review_request_to_dict(request)
        self.assertEqual(
            module.materialization_review_request_from_dict(request_dict),
            request,
        )

        result = module.evaluate_materialization_review_request(request)
        result_dict = module.materialization_review_result_to_dict(result)
        self.assertEqual(
            module.materialization_review_result_from_dict(result_dict),
            result,
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        request_id = module.create_materialization_review_request_id(
            "MAT cpu 001",
            "approve_for_validation",
        )
        self.assertEqual(
            request_id,
            "SCREEN6-MATERIALIZATION-REVIEW-REQUEST-MAT-CPU-001-APPROVE-FOR-VALIDATION",
        )
        self.assertEqual(
            module.create_materialization_review_result_id(request_id),
            (
                "SCREEN6-MATERIALIZATION-REVIEW-RESULT-"
                "SCREEN6-MATERIALIZATION-REVIEW-REQUEST-MAT-CPU-001-APPROVE-FOR-VALIDATION"
            ),
        )
        self.assertEqual(
            module.create_materialization_review_request_id(
                "MAT cpu 001",
                "approve_for_validation",
            ),
            request_id,
        )

    def test_no_mutation_or_persistence_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen6_materialization_review",
            "learning.screen6_materialization_review",
            "screen6_materialization_review",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen6_materialization_review", imports)
                self.assertNotIn("learning.screen6_materialization_review", imports)
                self.assertNotIn("screen6_materialization_review", imports)
                self.assertNotIn("screen6_materialization_review", source)

    def test_existing_7bk_and_7bl_tests_pass(self) -> None:
        for test_path in (
            "tests/test_phase7bk_screen6_governance_control_boundary.py",
            "tests/test_phase7bl_learning_candidate_review.py",
        ):
            with self.subTest(test_path=test_path):
                completed = subprocess.run(
                    ("python3", "-m", "unittest", test_path),
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

    def test_readme_links_new_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7BM Materialization Review UI",
                "phase7bm_materialization_review_ui.md",
            ),
            (
                "Phase 7BM Materialization Review Model",
                "phase7bm_materialization_review_model.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
