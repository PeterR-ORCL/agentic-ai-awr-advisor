from __future__ import annotations

import ast
import importlib
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
BRIDGE_DOC = DOCS / "phase7bi_feedback_learning_bridge.md"
MODEL_DOC = DOCS / "phase7bi_feedback_learning_intent_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen5_feedback_learning_bridge.py"

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
    "persist_feedback",
    "create_feedback_record",
    "create_dataset_label",
    "create_learning_candidate",
    "persist_candidate",
    "update_recommendation",
    "update_scoring",
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


class Phase7BIFeedbackLearningBridgeTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen5_feedback_learning_bridge")

    @staticmethod
    def decision_module():
        return importlib.import_module("src.learning.screen5_recommendation_decision")

    @staticmethod
    def action_module():
        return importlib.import_module("src.learning.screen5_action_tracking")

    @staticmethod
    def outcome_module():
        return importlib.import_module("src.learning.screen5_outcome_capture")

    def make_decision(self, decision_type: str = "accept_recommendation", **overrides):
        decision_module = self.decision_module()
        recommendation_id = overrides.get("recommendation_id", "RECO-CPU-001")
        values = {
            "decision_id": decision_module.create_recommendation_decision_id(
                recommendation_id,
                decision_type,
                run_id="RUN-1",
            ),
            "recommendation_id": recommendation_id,
            "run_id": "RUN-1",
            "awr_id": "AWR-1",
            "domain": "CPU",
            "recommendation_title": "Tune SQL action",
            "decision_type": decision_type,
            "decision_status": decision_module.decision_status_for_type(decision_type),
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "requires_followup": True,
            "followup_type": decision_module.followup_type_for_decision(decision_type),
        }
        values.update(overrides)
        return decision_module.RecommendationDecisionRecord(**values)

    def make_action(self, **overrides):
        action_module = self.action_module()
        values = {
            "action_preview_id": action_module.build_action_assignment_preview_id(
                "RECO-CPU-001",
                "Tune SQL action",
            ),
            "recommendation_id": "RECO-CPU-001",
            "action_title": "Tune SQL action",
            "action_status": "proposed",
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
        }
        values.update(overrides)
        return action_module.ActionAssignmentPreview(**values)

    def make_outcome(self, **overrides):
        outcome_module = self.outcome_module()
        values = {
            "outcome_preview_id": outcome_module.build_outcome_preview_id(
                "RECO-CPU-001",
                "ACTION-CPU-001",
            ),
            "recommendation_id": "RECO-CPU-001",
            "linked_action_id": "ACTION-CPU-001",
            "outcome_status": "pending",
            "outcome_effectiveness": "unknown",
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
        }
        values.update(overrides)
        return outcome_module.OutcomeCapturePreview(**values)

    def make_feedback(self, **overrides):
        module = self.module()
        feedback_type = overrides.get("feedback_type", "accepted")
        recommendation_id = overrides.get("recommendation_id", "RECO-CPU-001")
        values = {
            "feedback_intent_id": module.create_feedback_intent_id(
                recommendation_id,
                feedback_type,
            ),
            "recommendation_id": recommendation_id,
            "feedback_type": feedback_type,
            "feedback_status": "ready_for_review",
            "feedback_summary": "intent only",
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "source_payload": {"source": "unit-test"},
        }
        values.update(overrides)
        return module.RecommendationFeedbackIntent(**values)

    def make_signal(self, **overrides):
        module = self.module()
        feedback = overrides.pop("feedback", self.make_feedback())
        values = {
            "signal_intent_id": module.create_learning_signal_intent_id(
                feedback.recommendation_id,
                "recommendation_outcome",
                "recommendation_accepted",
            ),
            "recommendation_id": feedback.recommendation_id,
            "outcome_status": "unknown",
            "outcome_effectiveness": "unknown",
            "signal_type": "recommendation_outcome",
            "label_name": "recommendation_accepted",
            "label_value": "true",
            "supervised_label_eligible": True,
            "source_feedback_intent_id": feedback.feedback_intent_id,
            "source_evidence": ["feedback_intent"],
            "confidence": 0.80,
        }
        values.update(overrides)
        return module.LearningSignalIntent(**values)

    def make_candidate(self, **overrides):
        module = self.module()
        feedback = overrides.pop("feedback", self.make_feedback(feedback_type="rejected"))
        values = {
            "candidate_intent_id": module.create_recommendation_candidate_intent_id(
                feedback.recommendation_id,
                "recommendation_rule_candidate",
            ),
            "source_feedback_intent_id": feedback.feedback_intent_id,
            "candidate_type": "recommendation_rule_candidate",
            "affected_domain": "CPU",
            "affected_component": "recommendation",
            "rationale": "intent only",
            "source_evidence": ["feedback_intent"],
        }
        values.update(overrides)
        return module.RecommendationCandidateIntent(**values)

    def make_bridge_result(self, **overrides):
        module = self.module()
        feedback = self.make_feedback()
        signal = self.make_signal(feedback=feedback)
        candidate = self.make_candidate(feedback=feedback, candidate_type="documentation_candidate")
        values = {
            "bridge_result_id": module.create_feedback_bridge_result_id("RECO-CPU-001"),
            "recommendation_id": "RECO-CPU-001",
            "feedback_intents": [feedback],
            "learning_signal_intents": [signal],
            "candidate_intents": [candidate],
            "bridge_status": "ready_for_review",
            "warnings": ["intent only"],
            "required_next_steps": ["future review"],
        }
        values.update(overrides)
        return module.RecommendationFeedbackBridgeResult(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "RecommendationFeedbackIntent"))
        self.assertTrue(hasattr(module, "LearningSignalIntent"))
        self.assertTrue(hasattr(module, "RecommendationCandidateIntent"))
        self.assertTrue(hasattr(module, "RecommendationFeedbackBridgeResult"))

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
        self.assertTrue(BRIDGE_DOC.is_file(), BRIDGE_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        text = lower_text(BRIDGE_DOC) + "\n" + lower_text(MODEL_DOC)
        for phrase in (
            "feedback intents are not feedback records",
            "learning signal intents are not dataset labels",
            "candidate intents are not candidates",
            "no feedback is persisted",
            "no label is created",
            "no candidate is created automatically",
            "no recommendation truth is changed",
            "no scoring is changed",
            "no phase 4i mutation occurs",
            "phase 8 sizing/tco is not implemented",
            "feedback_created=false",
            "dataset_label_created=false",
            "candidate_created=false",
            "write_performed=false",
            "runtime_influence=false",
            "phase4i_mutation_requested=false",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_feedback_intent_validation(self) -> None:
        module = self.module()
        intent = self.make_feedback()
        self.assertIs(module.validate_recommendation_feedback_intent(intent), intent)
        for overrides in (
            {"feedback_created": True},
            {"write_performed": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
            {"feedback_type": "persisted_feedback"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen5FeedbackLearningBridgeError):
                    self.make_feedback(**overrides)

    def test_learning_signal_validation(self) -> None:
        module = self.module()
        signal = self.make_signal()
        self.assertIs(module.validate_learning_signal_intent(signal), signal)
        for overrides in (
            {"dataset_label_created": True},
            {"requires_human_review": False},
            {"confidence": 0.96},
            {"signal_type": "runtime_signal"},
            {"label_name": "runtime_label"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen5FeedbackLearningBridgeError):
                    self.make_signal(**overrides)

    def test_candidate_intent_validation(self) -> None:
        module = self.module()
        candidate = self.make_candidate()
        self.assertIs(module.validate_recommendation_candidate_intent(candidate), candidate)
        for overrides in (
            {"candidate_created": True},
            {"requires_human_review": False},
            {"runtime_influence": True},
            {"candidate_type": "runtime_candidate"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen5FeedbackLearningBridgeError):
                    self.make_candidate(**overrides)

    def test_bridge_result_validation(self) -> None:
        module = self.module()
        result = self.make_bridge_result()
        self.assertIs(module.validate_feedback_bridge_result(result), result)
        for overrides in (
            {"feedback_created": True},
            {"dataset_labels_created": True},
            {"candidates_created": True},
            {"write_performed": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen5FeedbackLearningBridgeError):
                    self.make_bridge_result(**overrides)

    def test_decision_and_outcome_mapping(self) -> None:
        module = self.module()
        accepted = module.build_feedback_intent_from_decision(self.make_decision())
        accepted_signal = module.build_learning_signal_intent(accepted)
        self.assertEqual(accepted.feedback_type, "accepted")
        self.assertEqual(accepted_signal.label_name, "recommendation_accepted")

        rejected = module.build_feedback_intent_from_decision(
            self.make_decision("reject_recommendation")
        )
        rejected_signal = module.build_learning_signal_intent(rejected)
        self.assertEqual(rejected.feedback_type, "rejected")
        self.assertEqual(rejected_signal.label_name, "recommendation_rejected")

        for outcome_status, expected_label in (
            ("improved", "performance_improved"),
            ("worsened", "performance_worsened"),
            ("issue_recurred", "issue_recurred"),
        ):
            with self.subTest(outcome_status=outcome_status):
                signal = module.build_learning_signal_intent(
                    accepted,
                    outcome_preview=self.make_outcome(outcome_status=outcome_status),
                )
                self.assertEqual(signal.label_name, expected_label)

        ineffective_signal = module.build_learning_signal_intent(
            accepted,
            outcome_preview=self.make_outcome(outcome_effectiveness="ineffective"),
        )
        self.assertEqual(ineffective_signal.label_name, "action_ineffective")

    def test_candidate_mapping(self) -> None:
        module = self.module()
        for feedback_type in ("rejected", "not_applicable", "ineffective"):
            with self.subTest(feedback_type=feedback_type):
                feedback = self.make_feedback(feedback_type=feedback_type)
                signal = module.build_learning_signal_intent(feedback)
                candidate = module.build_candidate_intent(feedback, signal)
                self.assertEqual(
                    candidate.candidate_type,
                    "recommendation_rule_candidate",
                )
                self.assertFalse(candidate.candidate_created)

        for feedback_type in ("false_positive", "false_negative"):
            with self.subTest(feedback_type=feedback_type):
                feedback = self.make_feedback(feedback_type=feedback_type)
                signal = module.build_learning_signal_intent(feedback)
                candidate = module.build_candidate_intent(feedback, signal)
                self.assertEqual(candidate.candidate_type, "validation_candidate")
                self.assertFalse(candidate.candidate_created)

        feedback = self.make_feedback(feedback_type="issue_recurred")
        signal = module.build_learning_signal_intent(feedback)
        scoring_candidate = module.build_candidate_intent(
            feedback,
            signal,
            affected_component="scoring weights",
        )
        recommendation_candidate = module.build_candidate_intent(
            feedback,
            signal,
            affected_component="recommendation action",
        )
        self.assertEqual(
            scoring_candidate.candidate_type,
            "scoring_weight_review_candidate",
        )
        self.assertEqual(
            recommendation_candidate.candidate_type,
            "recommendation_rule_candidate",
        )

    def test_bridge_builds_intents_only(self) -> None:
        module = self.module()
        result = module.bridge_recommendation_feedback(
            decision=self.make_decision(),
            action_preview=self.make_action(),
            outcome_preview=self.make_outcome(outcome_status="improved"),
            actor_id="ACTOR-LOCAL-JANE-REVIEWER",
        )
        self.assertEqual(result.bridge_status, "ready_for_review")
        self.assertEqual(len(result.feedback_intents), 1)
        self.assertEqual(len(result.learning_signal_intents), 1)
        self.assertEqual(len(result.candidate_intents), 1)
        self.assertFalse(result.feedback_created)
        self.assertFalse(result.dataset_labels_created)
        self.assertFalse(result.candidates_created)
        self.assertFalse(result.write_performed)
        self.assertFalse(result.runtime_influence)
        self.assertFalse(result.phase4i_mutation_requested)

        insufficient = module.bridge_recommendation_feedback()
        self.assertEqual(insufficient.bridge_status, "insufficient_context")
        self.assertFalse(insufficient.feedback_intents)

    def test_serialization_round_trips(self) -> None:
        module = self.module()
        feedback = self.make_feedback()
        signal = self.make_signal(feedback=feedback)
        candidate = self.make_candidate(feedback=feedback, candidate_type="documentation_candidate")
        result = self.make_bridge_result(
            feedback_intents=[feedback],
            learning_signal_intents=[signal],
            candidate_intents=[candidate],
        )

        self.assertEqual(
            module.recommendation_feedback_intent_to_dict(feedback),
            module.recommendation_feedback_intent_to_dict(
                module.recommendation_feedback_intent_from_dict(
                    module.recommendation_feedback_intent_to_dict(feedback)
                )
            ),
        )
        self.assertEqual(
            module.learning_signal_intent_to_dict(signal),
            module.learning_signal_intent_to_dict(
                module.learning_signal_intent_from_dict(
                    module.learning_signal_intent_to_dict(signal)
                )
            ),
        )
        self.assertEqual(
            module.recommendation_candidate_intent_to_dict(candidate),
            module.recommendation_candidate_intent_to_dict(
                module.recommendation_candidate_intent_from_dict(
                    module.recommendation_candidate_intent_to_dict(candidate)
                )
            ),
        )
        self.assertEqual(
            module.recommendation_feedback_bridge_result_to_dict(result),
            module.recommendation_feedback_bridge_result_to_dict(
                module.recommendation_feedback_bridge_result_from_dict(
                    module.recommendation_feedback_bridge_result_to_dict(result)
                )
            ),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        first = module.create_feedback_intent_id("RECO-CPU-001", "accepted")
        second = module.create_feedback_intent_id("RECO-CPU-001", "accepted")
        self.assertEqual(first, second)
        self.assertEqual(
            module.create_learning_signal_intent_id(
                "RECO-CPU-001",
                "recommendation_outcome",
                "recommendation_accepted",
            ),
            module.create_learning_signal_intent_id(
                "RECO-CPU-001",
                "recommendation_outcome",
                "recommendation_accepted",
            ),
        )
        self.assertEqual(
            module.create_recommendation_candidate_intent_id(
                "RECO-CPU-001",
                "recommendation_rule_candidate",
            ),
            module.create_recommendation_candidate_intent_id(
                "RECO-CPU-001",
                "recommendation_rule_candidate",
            ),
        )
        self.assertEqual(
            module.create_feedback_bridge_result_id("RECO-CPU-001"),
            module.create_feedback_bridge_result_id("RECO-CPU-001"),
        )
        self.assertFalse(
            re.search(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                first.lower(),
            )
        )

    def test_no_persistence_or_mutation_functions(self) -> None:
        names = function_names(MODULE_PATH)
        source = lower_text(MODULE_PATH)
        for forbidden in FORBIDDEN_SOURCE_TERMS:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)
                self.assertNotIn(forbidden, source)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen5_feedback_learning_bridge",
            "learning.screen5_feedback_learning_bridge",
            "screen5_feedback_learning_bridge",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen5_feedback_learning_bridge", imports)
                self.assertNotIn("learning.screen5_feedback_learning_bridge", imports)
                self.assertNotIn("screen5_feedback_learning_bridge", imports)
                self.assertNotIn("screen5_feedback_learning_bridge", source)


if __name__ == "__main__":
    unittest.main()
