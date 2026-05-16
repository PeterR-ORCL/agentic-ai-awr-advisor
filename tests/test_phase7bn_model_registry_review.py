from __future__ import annotations

import ast
import importlib
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
MODULE_PATH = ROOT / "src" / "learning" / "screen6_model_registry_review.py"
UI_DOC = DOCS / "phase7bn_model_registry_review_ui.md"
MODEL_DOC = DOCS / "phase7bn_model_registry_review_model.md"
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
    "persist_model_registry_review",
    "persist_review_record",
    "update_model_registry_status",
    "approve_model_for_shadow",
    "request_runtime_review_for_model",
    "grant_runtime_eligibility",
    "set_runtime_eligibility_granted",
    "set_runtime_active",
    "deploy_model",
    "load_model",
    "save_model",
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


class Phase7BNModelRegistryReviewTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen6_model_registry_review")

    def make_request(self, **overrides):
        module = self.module()
        model_id = overrides.get("model_id", "MODEL-CPU-001")
        requested_action = overrides.get("requested_action", "mark_under_review")
        if model_id and requested_action in module.MODEL_REGISTRY_REVIEW_ACTIONS:
            request_id = module.create_model_registry_review_request_id(
                model_id,
                requested_action,
            )
        else:
            request_id = "SCREEN6-MODEL-REGISTRY-REVIEW-REQUEST-LOCAL-TEST"
        values = {
            "review_request_id": request_id,
            "model_id": model_id,
            "model_family": "tree",
            "model_version": "v1",
            "requested_action": requested_action,
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "governance_note": "preview model note",
            "validation_reference": "VAL-PREVIEW-001",
            "rollback_reference": "RB-PREVIEW-001",
            "payload": {"reason": "unit test"},
            "validation_status": "preview_only",
            "can_route_to_write_path": False,
            "write_performed": False,
            "model_status_changed": False,
            "shadow_eligibility_changed": False,
            "runtime_review_requested": False,
            "runtime_eligibility_granted": False,
            "runtime_active": False,
            "validation_reference_attached": False,
            "rollback_reference_attached": False,
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "created_at": "2026-05-16T00:00:00Z",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.ModelRegistryReviewRequest(**values)

    def make_result(self, **overrides):
        module = self.module()
        request = overrides.pop("request", self.make_request())
        values = {
            "review_result_id": module.create_model_registry_review_result_id(
                request.review_request_id,
            ),
            "review_request_id": request.review_request_id,
            "model_id": request.model_id or "MODEL-CPU-001",
            "requested_action": request.requested_action,
            "result_status": "valid_for_future_review",
            "proposed_next_status": module.proposed_next_status_for_action(
                request.requested_action
            )
            if request.requested_action in module.MODEL_REGISTRY_REVIEW_ACTIONS
            else None,
            "model_status_changed": False,
            "shadow_eligibility_changed": False,
            "runtime_review_requested": False,
            "runtime_eligibility_granted": False,
            "runtime_active": False,
            "governance_action_performed": False,
            "validation_reference_attached": False,
            "rollback_reference_attached": False,
            "write_performed": False,
            "denied_reasons": [],
            "warnings": ["preview only"],
            "required_next_steps": ["future governed write path"],
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.ModelRegistryReviewResult(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "ModelRegistryReviewRequest"))
        self.assertTrue(hasattr(module, "ModelRegistryReviewResult"))

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
            "no model status is changed",
            "no shadow eligibility is changed",
            "no runtime review is requested",
            "no runtime eligibility is granted",
            "no model is deployed",
            "no runtime activation occurs",
            "controls are disabled/preview-only",
            "deterministic runtime remains authoritative",
            "write_performed=false",
            "model_status_changed=false",
            "shadow_eligibility_changed=false",
            "runtime_review_requested=false",
            "runtime_eligibility_granted=false",
            "runtime_active=false",
            "validation_reference_attached=false",
            "rollback_reference_attached=false",
            "runtime_influence=false",
            "phase4i_mutation_requested=false",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_actions_model_families_and_statuses(self) -> None:
        module = self.module()
        self.assertEqual(
            module.MODEL_REGISTRY_REVIEW_ACTIONS,
            (
                "mark_under_review",
                "approve_for_shadow",
                "request_runtime_review",
                "reject_model",
                "retire_model",
                "attach_validation_reference",
                "attach_rollback_reference",
                "add_model_governance_note",
                "close_model_review",
            ),
        )
        self.assertEqual(
            module.MODEL_REGISTRY_REVIEW_MODEL_FAMILIES,
            (
                "tree",
                "neural_net",
                "hybrid_rule_ml",
                "linear",
                "baseline_mock",
                "baseline_majority",
                "baseline_numeric_mean",
                "shadow_placeholder",
                "external_placeholder",
                "unknown",
            ),
        )
        self.assertEqual(
            module.MODEL_REGISTRY_REVIEW_RESULT_STATUSES,
            (
                "preview_only",
                "valid_for_future_review",
                "needs_actor",
                "needs_model",
                "needs_validation_reference",
                "needs_rollback_reference",
                "unsupported_action",
                "write_not_allowed_in_this_phase",
                "blocked_by_runtime_safety",
            ),
        )
        self.assertEqual(
            module.proposed_next_status_for_action("approve_for_shadow"),
            "approved_for_shadow_review",
        )

    def test_request_validation(self) -> None:
        module = self.module()
        request = self.make_request(requested_action="approve_for_shadow")
        self.assertIs(module.validate_model_registry_review_request(request), request)

        invalid_cases = (
            {"model_id": None},
            {"model_family": "unsupported_family"},
            {"requested_action": "deploy_model"},
            {"actor_id": None},
            {"payload": "not-a-dict"},
            {"write_performed": True},
            {"model_status_changed": True},
            {"shadow_eligibility_changed": True},
            {"runtime_review_requested": True},
            {"runtime_eligibility_granted": True},
            {"runtime_active": True},
            {"validation_reference_attached": True},
            {"rollback_reference_attached": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
        )
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen6ModelRegistryReviewError):
                    module.validate_model_registry_review_request(
                        self.make_request(**overrides)
                    )

    def test_result_validation(self) -> None:
        module = self.module()
        result = self.make_result()
        self.assertIs(module.validate_model_registry_review_result(result), result)

        invalid_cases = (
            {"requested_action": "deploy_model"},
            {"result_status": "runtime_active"},
            {"model_status_changed": True},
            {"shadow_eligibility_changed": True},
            {"runtime_review_requested": True},
            {"runtime_eligibility_granted": True},
            {"runtime_active": True},
            {"governance_action_performed": True},
            {"validation_reference_attached": True},
            {"rollback_reference_attached": True},
            {"write_performed": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
        )
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen6ModelRegistryReviewError):
                    module.validate_model_registry_review_result(
                        self.make_result(**overrides)
                    )

    def test_evaluation_behavior_is_preview_only(self) -> None:
        module = self.module()
        valid = module.evaluate_model_registry_review_request(
            self.make_request(requested_action="approve_for_shadow")
        )
        self.assertEqual(valid.result_status, "valid_for_future_review")
        self.assertEqual(valid.proposed_next_status, "approved_for_shadow_review")
        self.assertFalse(valid.model_status_changed)
        self.assertFalse(valid.shadow_eligibility_changed)
        self.assertFalse(valid.runtime_review_requested)
        self.assertFalse(valid.runtime_eligibility_granted)
        self.assertFalse(valid.runtime_active)
        self.assertFalse(valid.governance_action_performed)
        self.assertFalse(valid.validation_reference_attached)
        self.assertFalse(valid.rollback_reference_attached)
        self.assertFalse(valid.write_performed)
        self.assertFalse(valid.runtime_influence)
        self.assertFalse(valid.phase4i_mutation_requested)

        runtime_review = module.evaluate_model_registry_review_request(
            self.make_request(requested_action="request_runtime_review")
        )
        self.assertEqual(runtime_review.result_status, "valid_for_future_review")
        self.assertFalse(runtime_review.runtime_review_requested)
        self.assertFalse(runtime_review.runtime_eligibility_granted)
        self.assertFalse(runtime_review.runtime_active)

        cases = (
            ({"actor_id": None}, "needs_actor"),
            ({"model_id": None}, "needs_model"),
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
            ({"requested_action": "deploy_model"}, "unsupported_action"),
        )
        for overrides, expected_status in cases:
            with self.subTest(overrides=overrides):
                result = module.evaluate_model_registry_review_request(
                    self.make_request(**overrides)
                )
                self.assertEqual(result.result_status, expected_status)
                self.assertFalse(result.write_performed)
                self.assertFalse(result.model_status_changed)
                self.assertFalse(result.shadow_eligibility_changed)
                self.assertFalse(result.runtime_review_requested)
                self.assertFalse(result.runtime_eligibility_granted)
                self.assertFalse(result.runtime_active)

    def test_serialization_round_trip(self) -> None:
        module = self.module()
        request = self.make_request(requested_action="attach_validation_reference")
        request_dict = module.model_registry_review_request_to_dict(request)
        self.assertEqual(
            module.model_registry_review_request_from_dict(request_dict),
            request,
        )

        result = module.evaluate_model_registry_review_request(request)
        result_dict = module.model_registry_review_result_to_dict(result)
        self.assertEqual(
            module.model_registry_review_result_from_dict(result_dict),
            result,
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        request_id = module.create_model_registry_review_request_id(
            "model cpu 001",
            "approve_for_shadow",
        )
        self.assertEqual(
            request_id,
            "SCREEN6-MODEL-REGISTRY-REVIEW-REQUEST-MODEL-CPU-001-APPROVE-FOR-SHADOW",
        )
        self.assertEqual(
            module.create_model_registry_review_result_id(request_id),
            (
                "SCREEN6-MODEL-REGISTRY-REVIEW-RESULT-"
                "SCREEN6-MODEL-REGISTRY-REVIEW-REQUEST-MODEL-CPU-001-APPROVE-FOR-SHADOW"
            ),
        )
        self.assertEqual(
            module.create_model_registry_review_request_id(
                "model cpu 001",
                "approve_for_shadow",
            ),
            request_id,
        )

    def test_no_mutation_or_deployment_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen6_model_registry_review",
            "learning.screen6_model_registry_review",
            "screen6_model_registry_review",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen6_model_registry_review", imports)
                self.assertNotIn("learning.screen6_model_registry_review", imports)
                self.assertNotIn("screen6_model_registry_review", imports)
                self.assertNotIn("screen6_model_registry_review", source)

    def test_existing_7bk_7bl_and_7bm_tests_pass(self) -> None:
        for test_path in (
            "tests/test_phase7bk_screen6_governance_control_boundary.py",
            "tests/test_phase7bl_learning_candidate_review.py",
            "tests/test_phase7bm_materialization_review.py",
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
                "Phase 7BN ML Model Registry Review UI",
                "phase7bn_model_registry_review_ui.md",
            ),
            (
                "Phase 7BN ML Model Registry Review Model",
                "phase7bn_model_registry_review_model.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
