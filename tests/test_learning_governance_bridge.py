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
BRIDGE_PATH = ROOT / "src" / "learning" / "learning_governance_bridge.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def bridge_module():
    return importlib.import_module("src.learning.learning_governance_bridge")


def model_module():
    return importlib.import_module("src.learning.learning_candidate_model")


class LearningGovernanceBridgeTests(unittest.TestCase):
    def test_01_import_safety(self) -> None:
        before_environment = dict(os.environ)

        module = bridge_module()

        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "GovernanceDecision"))
        self.assertTrue(hasattr(module, "LearningGovernanceBridge"))
        self.assertTrue(hasattr(module, "apply_governance_action"))

    def test_governance_decision_serialization(self) -> None:
        module = bridge_module()
        candidate = self.make_candidate(status="UNDER_REVIEW")

        _, decision = module.LearningGovernanceBridge().approve_for_implementation(
            candidate,
            "reviewer@example.com",
            review_notes="Approved for implementation work only.",
        )
        data = module.governance_decision_to_dict(decision)

        self.assertEqual(tuple(data.keys()), module.DECISION_FIELDS)
        self.assertEqual(data["candidate_id"], candidate.candidate_id)
        self.assertEqual(data["from_status"], "UNDER_REVIEW")
        self.assertEqual(data["to_status"], "APPROVED_FOR_IMPLEMENTATION")
        self.assertFalse(data["runtime_influence"])
        self.assertTrue(data["approved_for_implementation_only"])
        self.assertEqual(module.governance_decision_from_dict(data), decision)

        data["audit_records"][0]["actor"] = "mutated@example.com"
        self.assertEqual(decision.audit_records[0]["actor"], "reviewer@example.com")

    def test_every_governance_action_requires_actor(self) -> None:
        module = bridge_module()
        bridge = module.LearningGovernanceBridge()
        cases = (
            (
                bridge.mark_under_review,
                (self.make_candidate(status="PROPOSED"), "", None),
            ),
            (
                bridge.reject_candidate,
                (self.make_candidate(status="PROPOSED"), "", "Rejected by review."),
            ),
            (
                bridge.request_revision,
                (self.make_candidate(status="PROPOSED"), "", "Needs clearer evidence."),
            ),
            (
                bridge.approve_for_implementation,
                (self.make_candidate(status="UNDER_REVIEW"), "", None),
            ),
            (
                bridge.attach_materialization,
                (
                    self.make_candidate(status="APPROVED_FOR_IMPLEMENTATION"),
                    "",
                    "commit:abc123",
                    None,
                ),
            ),
            (
                bridge.mark_implemented,
                (
                    self.make_candidate(status="APPROVED_FOR_IMPLEMENTATION"),
                    "",
                    "commit:abc123",
                    None,
                ),
            ),
            (
                bridge.mark_validated,
                (self.make_candidate(status="IMPLEMENTED", materialization_reference="commit:abc123"), "", None),
            ),
            (
                bridge.close_candidate,
                (self.make_candidate(status="VALIDATED", materialization_reference="commit:abc123"), "", None),
            ),
        )

        for action, args in cases:
            with self.subTest(action=action.__name__):
                with self.assertRaises(module.LearningGovernanceBridgeError):
                    action(*args)

    def test_allowed_status_transitions(self) -> None:
        bridge = bridge_module().LearningGovernanceBridge()
        actor = "reviewer@example.com"

        proposed = self.make_candidate(status="PROPOSED")
        under_review, _ = bridge.mark_under_review(proposed, actor)
        self.assertEqual(under_review.status, "UNDER_REVIEW")

        approved, approval = bridge.approve_for_implementation(under_review, actor)
        self.assertEqual(approved.status, "APPROVED_FOR_IMPLEMENTATION")
        self.assertTrue(approval.approved_for_implementation_only)

        implemented, _ = bridge.mark_implemented(
            approved,
            actor,
            materialization_reference="commit:abc123",
        )
        self.assertEqual(implemented.status, "IMPLEMENTED")

        validated, _ = bridge.mark_validated(implemented, actor)
        self.assertEqual(validated.status, "VALIDATED")

        closed, _ = bridge.close_candidate(validated, actor)
        self.assertEqual(closed.status, "CLOSED")

        rejected, _ = bridge.reject_candidate(
            self.make_candidate(status="PROPOSED"),
            actor,
            "Rejected with audit notes.",
        )
        self.assertEqual(rejected.status, "REJECTED")

        needs_revision, _ = bridge.request_revision(
            self.make_candidate(status="PROPOSED"),
            actor,
            "Needs revised scope.",
        )
        self.assertEqual(needs_revision.status, "NEEDS_REVISION")

        revised_review, _ = bridge.mark_under_review(needs_revision, actor)
        self.assertEqual(revised_review.status, "UNDER_REVIEW")

    def test_invalid_status_transitions_fail_clearly(self) -> None:
        module = bridge_module()
        bridge = module.LearningGovernanceBridge()
        actor = "reviewer@example.com"

        with self.assertRaisesRegex(
            module.LearningGovernanceBridgeError,
            "Invalid governance status transition",
        ):
            bridge.approve_for_implementation(self.make_candidate(status="PROPOSED"), actor)

        closed = self.make_candidate(status="CLOSED")
        for action in (
            bridge.mark_under_review,
            bridge.approve_for_implementation,
            bridge.mark_validated,
        ):
            with self.subTest(action=action.__name__):
                with self.assertRaisesRegex(
                    module.LearningGovernanceBridgeError,
                    "Invalid governance status transition",
                ):
                    action(closed, actor)

    def test_approval_boundary(self) -> None:
        bridge = bridge_module().LearningGovernanceBridge()
        candidate = self.make_candidate(status="UNDER_REVIEW")

        approved, decision = bridge.approve_for_implementation(
            candidate,
            "reviewer@example.com",
        )

        self.assertEqual(approved.status, "APPROVED_FOR_IMPLEMENTATION")
        self.assertFalse(approved.runtime_influence)
        self.assertTrue(approved.requires_human_review)
        self.assertTrue(decision.approved_for_implementation_only)
        self.assertFalse(decision.runtime_influence)
        self.assertIsNone(approved.materialization_reference)
        self.assertIsNone(decision.materialization_reference)

    def test_materialization_boundary(self) -> None:
        module = bridge_module()
        bridge = module.LearningGovernanceBridge()
        approved = self.make_candidate(status="APPROVED_FOR_IMPLEMENTATION")

        with self.assertRaises(module.LearningGovernanceBridgeError):
            bridge.attach_materialization(approved, "reviewer@example.com", "")

        attached, attach_decision = bridge.attach_materialization(
            approved,
            "reviewer@example.com",
            "commit:abc123",
            review_notes="Implementation reference recorded.",
        )

        self.assertEqual(attached.status, "APPROVED_FOR_IMPLEMENTATION")
        self.assertEqual(attached.materialization_reference, "commit:abc123")
        self.assertFalse(attached.runtime_influence)
        self.assertFalse(attach_decision.runtime_influence)
        self.assertEqual(attach_decision.from_status, attach_decision.to_status)

        implemented, implementation_decision = bridge.mark_implemented(
            attached,
            "reviewer@example.com",
        )
        self.assertEqual(implemented.status, "IMPLEMENTED")
        self.assertEqual(implemented.materialization_reference, "commit:abc123")
        self.assertFalse(implemented.runtime_influence)
        self.assertFalse(implementation_decision.runtime_influence)

    def test_candidate_immutability_and_safety_fields(self) -> None:
        bridge = bridge_module().LearningGovernanceBridge()
        candidate = self.make_candidate(status="UNDER_REVIEW")
        original = candidate.to_dict()

        updated, _ = bridge.approve_for_implementation(
            candidate,
            "reviewer@example.com",
            review_notes="Approved for implementation review.",
        )

        self.assertEqual(candidate.to_dict(), original)
        self.assertIsNot(updated, candidate)
        self.assertEqual(updated.source_evidence, original["source_evidence"])
        self.assertEqual(updated.structured_sources, original["structured_sources"])
        self.assertEqual(updated.semantic_context, original["semantic_context"])
        self.assertEqual(updated.confidence, original["confidence"])
        self.assertEqual(updated.candidate_type, original["candidate_type"])
        self.assertFalse(updated.runtime_influence)
        self.assertTrue(updated.requires_human_review)

    def test_decision_id_determinism(self) -> None:
        bridge = bridge_module().LearningGovernanceBridge()
        first_candidate = self.make_candidate(status="UNDER_REVIEW")
        second_candidate = self.make_candidate(status="UNDER_REVIEW")

        _, first = bridge.approve_for_implementation(
            first_candidate,
            "reviewer@example.com",
            review_notes="Stable note.",
        )
        _, second = bridge.approve_for_implementation(
            second_candidate,
            "reviewer@example.com",
            review_notes="Stable note.",
        )
        _, different_actor = bridge.approve_for_implementation(
            second_candidate,
            "other-reviewer@example.com",
            review_notes="Stable note.",
        )

        self.assertEqual(first.decision_id, second.decision_id)
        self.assertNotEqual(first.decision_id, different_actor.decision_id)
        self.assertTrue(first.decision_id.startswith("GOVDEC-APPROVE-FOR-IMPLEMENTATION-"))
        self.assertIsNone(re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-", first.decision_id))

    def test_audit_records_are_explicit_and_non_runtime(self) -> None:
        bridge = bridge_module().LearningGovernanceBridge()
        candidate = self.make_candidate(status="UNDER_REVIEW")

        _, decision = bridge.approve_for_implementation(
            candidate,
            "reviewer@example.com",
            review_notes="Reviewed and approved for implementation work only.",
        )

        self.assertEqual(len(decision.audit_records), 1)
        record = decision.audit_records[0]
        for key in ("candidate_id", "action", "from_status", "to_status", "actor"):
            self.assertIn(key, record)
        self.assertEqual(record["candidate_id"], candidate.candidate_id)
        self.assertEqual(record["from_status"], "UNDER_REVIEW")
        self.assertEqual(record["to_status"], "APPROVED_FOR_IMPLEMENTATION")
        self.assertEqual(record["actor"], "reviewer@example.com")
        self.assertFalse(record["runtime_influence"])
        self.assertTrue(record["requires_human_review"])
        self.assertTrue(record["approved_for_implementation_only"])
        self.assertNotIn("runtime_activation", record)
        self.assertNotIn("activated", record)

    def test_apply_governance_action_helper(self) -> None:
        module = bridge_module()
        actor = "reviewer@example.com"

        under_review, _ = module.apply_governance_action(
            self.make_candidate(status="PROPOSED"),
            "mark_under_review",
            actor,
        )
        self.assertEqual(under_review.status, "UNDER_REVIEW")

        approved, _ = module.apply_governance_action(
            under_review,
            "approve",
            actor,
        )
        self.assertEqual(approved.status, "APPROVED_FOR_IMPLEMENTATION")

        implemented, _ = module.apply_governance_action(
            approved,
            "mark_implemented",
            actor,
            materialization_reference="commit:abc123",
        )
        self.assertEqual(implemented.status, "IMPLEMENTED")
        self.assertFalse(implemented.runtime_influence)

        with self.assertRaises(module.LearningGovernanceBridgeError):
            module.apply_governance_action(implemented, "unknown_action", actor)
        with self.assertRaises(module.LearningGovernanceBridgeError):
            module.apply_governance_action(implemented, "mark_validated", "")

    def test_no_forbidden_autonomous_function_names(self) -> None:
        text = read_text(BRIDGE_PATH).lower()
        for name in (
            "auto_apply",
            "autonomous_apply",
            "self_modify",
            "mutate_runtime",
            "update_parser_automatically",
            "update_scoring_automatically",
            "update_recommendations_automatically",
        ):
            self.assertNotIn(name, text)

    def test_runtime_import_isolation(self) -> None:
        self.assert_no_learning_imports(ROOT / "scripts" / "run_analysis.py")
        runtime_paths = [
            ROOT / "src" / "parser",
            ROOT / "src" / "parsing",
            ROOT / "src" / "analysis",
            ROOT / "src" / "recommendation",
            ROOT / "src" / "recommendations",
            ROOT / "src" / "scoring",
            ROOT / "src" / "decision",
        ]

        checked_files: list[Path] = []
        for path in runtime_paths:
            if path.is_dir():
                checked_files.extend(sorted(path.rglob("*.py")))
            elif path.is_file():
                checked_files.append(path)

        self.assertTrue(checked_files, "expected runtime files to inspect")
        for path in checked_files:
            self.assert_no_learning_imports(path)

    def test_documentation_exists_and_contains_required_boundary_phrases(self) -> None:
        doc_path = DOCS / "phase7_learning_governance_bridge.md"
        self.assertTrue(doc_path.is_file())
        lower_text = read_text(doc_path).lower()

        for phrase in (
            "not runtime integration",
            "approved for implementation only",
            "approval does not activate runtime behavior",
            "materialization reference does not activate runtime behavior",
            "runtime_influence=false",
            "requires_human_review=true",
            "does not change confidence",
            "does not change source_evidence",
            "dashboard learning visibility remains future Phase 7G",
            "dashboard interactivity remains future Phase 7H",
            "CLI learning commands remain future Phase 7I",
        ):
            self.assertIn(phrase.lower(), lower_text)

    def make_candidate(self, status: str = "PROPOSED", **overrides: object):
        model = model_module()
        data = {
            "candidate_id": "CANDIDATE-PARSER-MAPPING-CANDIDATE-GOVERNANCE",
            "candidate_type": "parser_mapping_candidate",
            "title": "Review parser signal",
            "description": "Review repeated unknown parser signal.",
            "rationale": "Repeated governed records justify human review.",
            "source_evidence": [
                {"source_type": "unknown_signal", "source_id": "u1"},
            ],
            "structured_sources": [
                {"source_type": "outcome_pattern", "pattern_id": "PATTERN-1"},
            ],
            "semantic_context": {
                "summary": "Reviewer-assist context only.",
                "runtime_influence": False,
            },
            "affected_component": "parser",
            "affected_domain": "SQL",
            "confidence": 0.62,
            "requires_human_review": True,
            "runtime_influence": False,
            "status": status,
            "materialization_reference": None,
        }
        data.update(deepcopy(overrides))
        return model.LearningCandidate(**data)

    def assert_no_learning_imports(self, path: Path) -> None:
        text = read_text(path)
        tree = ast.parse(text, filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertFalse(
                        self._is_learning_module(alias.name),
                        f"{path} imports {alias.name}",
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                self.assertFalse(
                    self._is_learning_module(module),
                    f"{path} imports from {module}",
                )

    @staticmethod
    def _is_learning_module(module_name: str) -> bool:
        return (
            module_name == "learning"
            or module_name.startswith("learning.")
            or module_name == "src.learning"
            or module_name.startswith("src.learning.")
        )


if __name__ == "__main__":
    unittest.main()
