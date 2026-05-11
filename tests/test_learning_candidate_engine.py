from __future__ import annotations

from copy import deepcopy
import ast
import importlib
import os
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
ENGINE_PATH = ROOT / "src" / "learning" / "learning_candidate_engine.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def engine_module():
    return importlib.import_module("src.learning.learning_candidate_engine")


def make_pattern(
    pattern_type: str,
    pattern_id: str | None = None,
    suggested_candidate_type: str | None = None,
    affected_component: str | None = None,
    affected_domain: str | None = None,
    confidence: float = 0.65,
    recurrence_count: int = 2,
    source_records: list[dict[str, object]] | None = None,
    title: str | None = None,
    description: str | None = None,
    observed_effect: str | None = None,
    rationale: str | None = None,
) -> dict[str, object]:
    pattern_id = pattern_id or f"PATTERN-{pattern_type.upper()}"
    source_records = source_records or [
        {"source_type": "unit", "source_id": f"{pattern_id}-1"},
        {"source_type": "unit", "source_id": f"{pattern_id}-2"},
    ]
    return {
        "pattern_id": pattern_id,
        "pattern_type": pattern_type,
        "title": title or f"Example {pattern_type}",
        "description": description or f"Observed repeated {pattern_type}.",
        "source_records": source_records,
        "affected_domain": affected_domain,
        "affected_component": affected_component,
        "recurrence_count": recurrence_count,
        "observed_effect": observed_effect or pattern_type,
        "confidence": confidence,
        "rationale": rationale or f"{recurrence_count} records support {pattern_type}.",
        "requires_human_review": True,
        "runtime_influence": False,
        "suggested_candidate_type": suggested_candidate_type,
    }


class LearningCandidateEngineTests(unittest.TestCase):
    def test_01_import_safety(self) -> None:
        before_environment = dict(os.environ)

        module = engine_module()

        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "LearningCandidateEngine"))
        self.assertTrue(hasattr(module, "generate_learning_candidates"))

    def test_empty_input_returns_no_candidates(self) -> None:
        module = engine_module()

        self.assertEqual(module.LearningCandidateEngine().generate_candidates([]), [])
        self.assertEqual(module.generate_learning_candidates([]), [])

    def test_pattern_mappings(self) -> None:
        module = engine_module()
        cases = (
            ("repeated_rejected_recommendation", "recommendation_rule_candidate"),
            ("poor_outcome_after_action", "recommendation_rule_candidate"),
            ("recurring_issue_after_action", "recommendation_rule_candidate"),
            ("repeated_unknown_signal", "parser_mapping_candidate"),
            ("repeated_feedback_theme", "dashboard_wording_candidate"),
            ("recurring_domain_issue", "scoring_weight_review_candidate"),
        )

        for pattern_type, expected_candidate_type in cases:
            with self.subTest(pattern_type=pattern_type):
                candidates = module.LearningCandidateEngine().generate_candidates(
                    [make_pattern(pattern_type)]
                )
                self.assertEqual(len(candidates), 1)
                self.assertEqual(candidates[0].candidate_type, expected_candidate_type)

    def test_feedback_and_domain_recommendation_overrides(self) -> None:
        module = engine_module()
        feedback = make_pattern(
            "repeated_feedback_theme",
            observed_effect="recommendation not useful",
            rationale="Repeated feedback says the recommendation is not useful.",
        )
        default_domain = make_pattern(
            "recurring_domain_issue",
            pattern_id="PATTERN-DOMAIN-DEFAULT",
            description=(
                "The same domain appears across governed run, recommendation, "
                "or outcome records."
            ),
            rationale="2 source records mention canonical domain 'CPU'.",
        )
        domain = make_pattern(
            "recurring_domain_issue",
            pattern_id="PATTERN-DOMAIN-RECOMMENDATION",
            rationale="The same action/domain recurrence appears after action records.",
        )

        candidates = module.LearningCandidateEngine().generate_candidates(
            [feedback, default_domain, domain]
        )
        candidate_types = {
            candidate.structured_sources[0]["pattern_id"]: candidate.candidate_type
            for candidate in candidates
        }

        self.assertEqual(
            candidate_types["PATTERN-DOMAIN-DEFAULT"],
            "scoring_weight_review_candidate",
        )
        self.assertEqual(
            candidate_types["PATTERN-DOMAIN-RECOMMENDATION"],
            "recommendation_rule_candidate",
        )
        self.assertIn("recommendation_rule_candidate", candidate_types.values())

    def test_suggested_candidate_type_is_honored_when_supported(self) -> None:
        module = engine_module()
        pattern = make_pattern(
            "repeated_unknown_signal",
            suggested_candidate_type="documentation_candidate",
        )

        candidate = module.LearningCandidateEngine().generate_candidates([pattern])[0]

        self.assertEqual(candidate.candidate_type, "documentation_candidate")

    def test_unsupported_suggested_candidate_type_falls_back_to_mapping(self) -> None:
        module = engine_module()
        pattern = make_pattern(
            "repeated_unknown_signal",
            suggested_candidate_type="not_a_supported_type",
        )

        candidate = module.LearningCandidateEngine().generate_candidates([pattern])[0]

        self.assertEqual(candidate.candidate_type, "parser_mapping_candidate")

    def test_candidate_safety_defaults(self) -> None:
        module = engine_module()
        patterns = [
            make_pattern("repeated_unknown_signal"),
            make_pattern("repeated_feedback_theme"),
            make_pattern("recurring_domain_issue"),
        ]

        candidates = module.LearningCandidateEngine().generate_candidates(patterns)

        for candidate in candidates:
            self.assertEqual(candidate.status, "PROPOSED")
            self.assertTrue(candidate.requires_human_review)
            self.assertFalse(candidate.runtime_influence)
            self.assertIsNone(candidate.semantic_context)
            self.assertIsNone(candidate.reviewed_by)
            self.assertIsNone(candidate.materialization_reference)

    def test_candidate_validation(self) -> None:
        engine = engine_module()
        model = importlib.import_module("src.learning.learning_candidate_model")
        patterns = [
            make_pattern("repeated_rejected_recommendation"),
            make_pattern("poor_outcome_after_action"),
            make_pattern("recurring_issue_after_action"),
            make_pattern("repeated_unknown_signal"),
            make_pattern("repeated_feedback_theme"),
            make_pattern("recurring_domain_issue"),
        ]

        candidates = engine.LearningCandidateEngine().generate_candidates(patterns)

        for candidate in candidates:
            self.assertIs(model.validate_candidate(candidate), candidate)

    def test_deterministic_output_and_stable_order(self) -> None:
        module = engine_module()
        patterns = [
            make_pattern("recurring_domain_issue", pattern_id="PATTERN-Z"),
            make_pattern("repeated_unknown_signal", pattern_id="PATTERN-A"),
            make_pattern("repeated_rejected_recommendation", pattern_id="PATTERN-B"),
        ]

        first = module.generate_learning_candidates(patterns)
        second = module.generate_learning_candidates(deepcopy(patterns))

        self.assertEqual(first, second)
        self.assertEqual(
            [candidate["candidate_type"] for candidate in first],
            [
                "recommendation_rule_candidate",
                "parser_mapping_candidate",
                "scoring_weight_review_candidate",
            ],
        )

    def test_deduplication_removes_duplicate_candidate_ids(self) -> None:
        module = engine_module()
        patterns = [
            make_pattern(
                "repeated_unknown_signal",
                pattern_id="PATTERN-DUPLICATE",
                confidence=0.50,
                source_records=[{"source_type": "unknown_signal", "source_id": "u1"}],
            ),
            make_pattern(
                "repeated_unknown_signal",
                pattern_id="PATTERN-DUPLICATE",
                confidence=0.85,
                source_records=[{"source_type": "unknown_signal", "source_id": "u2"}],
            ),
        ]

        candidates = module.LearningCandidateEngine().generate_candidates(patterns)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(len({candidate.candidate_id for candidate in candidates}), 1)
        self.assertEqual(candidates[0].confidence, 0.85)
        self.assertEqual(len(candidates[0].source_evidence), 2)
        self.assertEqual(candidates[0].status, "PROPOSED")
        self.assertTrue(candidates[0].requires_human_review)
        self.assertFalse(candidates[0].runtime_influence)

    def test_memory_helper_mines_patterns_and_does_not_mutate_input(self) -> None:
        module = engine_module()
        memory_records = {
            "unknown_signals": [
                {"unknown_signal_id": "u1", "section": "SQL", "signature": "PX wait"},
                {"unknown_signal_id": "u2", "section": "SQL", "signature": "PX wait"},
            ]
        }
        original = deepcopy(memory_records)

        candidates = module.LearningCandidateEngine().generate_candidates_from_memory(
            memory_records
        )

        self.assertEqual(memory_records, original)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].candidate_type, "parser_mapping_candidate")
        self.assertEqual(
            module.generate_learning_candidates_from_memory(memory_records),
            [candidates[0].to_dict()],
        )

    def test_no_input_mutation(self) -> None:
        module = engine_module()
        patterns = [
            make_pattern("repeated_unknown_signal"),
            make_pattern("repeated_feedback_theme"),
        ]
        original_patterns = deepcopy(patterns)
        memory_records = {
            "feedback": [
                {"feedback_id": "f1", "feedback_text": "The wording is confusing."},
                {"feedback_id": "f2", "comment": "Confusing wording in the finding."},
            ]
        }
        original_memory = deepcopy(memory_records)

        module.LearningCandidateEngine().generate_candidates(patterns)
        module.LearningCandidateEngine().generate_candidates_from_memory(memory_records)

        self.assertEqual(patterns, original_patterns)
        self.assertEqual(memory_records, original_memory)

    def test_source_evidence_and_structured_sources(self) -> None:
        module = engine_module()
        source_records = [
            {"source_type": "feedback", "source_id": "f1"},
            {"source_type": "feedback", "source_id": "f2"},
        ]
        pattern = make_pattern(
            "repeated_feedback_theme",
            pattern_id="PATTERN-FEEDBACK",
            source_records=source_records,
            recurrence_count=4,
        )

        candidate = module.LearningCandidateEngine().generate_candidates([pattern])[0]

        self.assertEqual(candidate.source_evidence, source_records)
        self.assertEqual(candidate.structured_sources[0]["pattern_id"], "PATTERN-FEEDBACK")
        self.assertEqual(
            candidate.structured_sources[0]["pattern_type"],
            "repeated_feedback_theme",
        )
        self.assertEqual(candidate.structured_sources[0]["recurrence_count"], 4)

    def test_created_fields(self) -> None:
        module = engine_module()
        candidate = module.LearningCandidateEngine().generate_candidates(
            [make_pattern("repeated_unknown_signal")]
        )[0]

        self.assertEqual(candidate.created_by, "phase7_candidate_generation_engine")
        self.assertIsNone(candidate.created_at)

    def test_no_forbidden_autonomous_function_names(self) -> None:
        text = read_text(ENGINE_PATH).lower()
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
        doc_path = DOCS / "phase7_candidate_generation_engine.md"
        self.assertTrue(doc_path.is_file())
        text = read_text(doc_path)
        lower_text = text.lower()

        for phrase in (
            "proposal-only",
            "generated candidates are not approved",
            "generated candidates are not implemented",
            "generated candidates are not activated",
            "runtime_influence=false",
            "requires_human_review=true",
            "semantic_context remains None in Phase 7D",
            "governance bridge remains future Phase 7F",
            "dashboard learning visibility remains future Phase 7G",
            "dashboard interactivity remains future Phase 7H",
        ):
            self.assertIn(phrase.lower(), lower_text)

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
