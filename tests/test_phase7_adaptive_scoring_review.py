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
ADAPTIVE_SCORING_REVIEW_DOC = DOCS / "phase7_adaptive_scoring_review.md"
SCORING_REVIEW_MODEL_DOC = DOCS / "phase7_scoring_review_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "adaptive_scoring_review.py"

REQUIRED_REVIEW_TYPES = (
    "scoring_weight_review",
    "domain_weight_review",
    "threshold_review",
    "severity_cutoff_review",
    "confidence_logic_review",
    "trend_sensitivity_review",
    "anomaly_sensitivity_review",
    "recurring_issue_sensitivity_review",
    "score_normalization_review",
    "score_label_review",
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
    "apply_scoring_config",
    "activate_scoring",
    "mutate_scoring",
    "update_runtime_scoring",
    "update_scoring_weights",
    "auto_apply",
    "autonomous_apply",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


def review_module():
    return importlib.import_module("src.learning.adaptive_scoring_review")


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


class Phase7AdaptiveScoringReviewTests(unittest.TestCase):
    def test_01_module_import_safety(self) -> None:
        before_environment = dict(os.environ)

        module = review_module()

        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "AdaptiveScoringReview"))
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
        self.assertTrue(ADAPTIVE_SCORING_REVIEW_DOC.is_file(), ADAPTIVE_SCORING_REVIEW_DOC)
        self.assertTrue(SCORING_REVIEW_MODEL_DOC.is_file(), SCORING_REVIEW_MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{lower_text(ADAPTIVE_SCORING_REVIEW_DOC)}\n{lower_text(SCORING_REVIEW_MODEL_DOC)}"
        for phrase in (
            "proposal-only",
            "no runtime scoring changes are applied",
            "runtime_influence_granted=false",
            "proposed scoring configs are inactive",
            "validated does not mean runtime active",
            "existing scoring engine remains authoritative",
            "this is not ml",
            "does not implement learned_model(x)",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_supported_review_types(self) -> None:
        module = review_module()
        self.assertEqual(set(module.SCORING_REVIEW_TYPES), set(REQUIRED_REVIEW_TYPES))
        for review_type in REQUIRED_REVIEW_TYPES:
            with self.subTest(review_type=review_type):
                self.assertTrue(module.is_supported_scoring_review_type(review_type))
                self.assertIn(
                    "versioned scoring config",
                    module.required_scoring_validation_requirements(review_type),
                )
        self.assertFalse(module.is_supported_scoring_review_type("parser_mapping_review"))
        with self.assertRaises(module.AdaptiveScoringReviewError):
            module.required_scoring_validation_requirements("parser_mapping_review")

    def test_source_artifact_requirement(self) -> None:
        module = review_module()

        review = self.create_review()
        self.assertEqual(review.source_materialization_id, self.make_source_artifact().materialization_id)

        for candidate_type in ("parser_mapping_candidate", "recommendation_rule_candidate"):
            with self.subTest(candidate_type=candidate_type):
                with self.assertRaises(module.AdaptiveScoringReviewError):
                    self.create_review(source=self.make_source_artifact(candidate_type=candidate_type))

        for status in ("REJECTED", "ROLLED_BACK", "CLOSED"):
            with self.subTest(status=status):
                with self.assertRaises(module.AdaptiveScoringReviewError):
                    self.create_review(source=self.make_source_artifact(status=status))

        source_data = self.make_source_artifact_data()
        source_data["runtime_influence_granted"] = True
        with self.assertRaises(module.AdaptiveScoringReviewError):
            self.create_review(source=source_data)

    def test_review_creation(self) -> None:
        module = review_module()
        source = self.make_source_artifact()
        review = self.create_review(source=source)

        expected_id = module.create_scoring_review_id(
            source.materialization_id,
            "scoring_weight_review",
            "v1.0",
        )
        self.assertEqual(review.review_id, expected_id)
        self.assertTrue(review.review_id.startswith("SCORING-REVIEW-SCORING-WEIGHT-REVIEW-"))
        self.assertNotRegex(
            review.review_id,
            re.compile(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                re.IGNORECASE,
            ),
        )
        self.assertFalse(review.runtime_influence_granted)
        self.assertFalse(review.status == "VALIDATED" and review.runtime_influence_granted)

        for kwargs in (
            {"actor": ""},
            {"proposed_config_version": ""},
            {"proposed_config": {}},
            {"before_after_summary": ""},
            {"rollback_plan": ""},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(module.AdaptiveScoringReviewError):
                    self.create_review(**kwargs)

    def test_validation_requirements(self) -> None:
        module = review_module()
        with self.assertRaises(module.AdaptiveScoringReviewError):
            self.create_review(validation_requirements=["versioned scoring config"])

        review = self.create_review()
        requirements = "\n".join(review.validation_requirements).lower()
        for phrase in (
            "versioned scoring config",
            "before/after comparison",
            "scoring regression tests",
            "phase 4i scores contract validation",
            "rollback plan",
            "deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, requirements)

        data = module.adaptive_scoring_review_to_dict(review)
        data["runtime_influence_granted"] = True
        with self.assertRaises(module.AdaptiveScoringReviewError):
            module.adaptive_scoring_review_from_dict(data)

    def test_review_type_specific_validation(self) -> None:
        module = review_module()
        cases = {
            "threshold_review": "threshold regression tests",
            "severity_cutoff_review": "severity distribution comparison",
            "confidence_logic_review": "confidence calibration validation",
            "trend_sensitivity_review": "trend regression validation",
            "anomaly_sensitivity_review": "anomaly false positive/false negative review",
            "domain_weight_review": "domain score distribution comparison",
        }
        for review_type, required_phrase in cases.items():
            with self.subTest(review_type=review_type):
                review = self.create_review(review_type=review_type)
                self.assertIn(required_phrase, "\n".join(review.validation_requirements))

                requirements = module.required_scoring_validation_requirements(review_type)
                requirements.remove(required_phrase)
                with self.assertRaises(module.AdaptiveScoringReviewError):
                    self.create_review(
                        review_type=review_type,
                        validation_requirements=requirements,
                    )

    def test_proposed_scoring_config(self) -> None:
        module = review_module()
        review = self.create_review()
        config = module.create_proposed_scoring_config(review)

        self.assertEqual(config.version, review.proposed_config_version)
        self.assertFalse(config.runtime_active)
        self.assertFalse(config.runtime_influence_granted)
        self.assertTrue(config.config_id.startswith("SCORING-CONFIG-SCORING-REVIEW-V1-0-"))
        self.assertEqual(config.source_review_id, review.review_id)
        self.assertEqual(config.domain_weights["sql"], 1.25)

        data = module.proposed_scoring_config_to_dict(config)
        data["runtime_active"] = True
        with self.assertRaises(module.AdaptiveScoringReviewError):
            module.proposed_scoring_config_from_dict(data)

        data = module.proposed_scoring_config_to_dict(config)
        data["runtime_influence_granted"] = True
        with self.assertRaises(module.AdaptiveScoringReviewError):
            module.proposed_scoring_config_from_dict(data)

    def test_serialization(self) -> None:
        module = review_module()
        review = self.create_review()
        review_data = module.adaptive_scoring_review_to_dict(review)
        self.assertEqual(tuple(review_data.keys()), module.ADAPTIVE_SCORING_REVIEW_FIELDS)
        self.assertEqual(module.adaptive_scoring_review_from_dict(review_data), review)
        self.assertEqual(
            module.adaptive_scoring_reviews_to_dicts([review, review]),
            [review_data, review_data],
        )

        config = module.create_proposed_scoring_config(review)
        config_data = module.proposed_scoring_config_to_dict(config)
        self.assertEqual(tuple(config_data.keys()), module.PROPOSED_SCORING_CONFIG_FIELDS)
        self.assertEqual(module.proposed_scoring_config_from_dict(config_data), config)

        review_data["source_evidence"][0]["source_id"] = "mutated"
        self.assertEqual(review.source_evidence[0]["source_id"], "SRC-1")

    def test_no_source_mutation(self) -> None:
        source_data = self.make_source_artifact_data()
        original = deepcopy(source_data)

        self.create_review(source=source_data)

        self.assertEqual(source_data, original)

    def test_runtime_import_isolation(self) -> None:
        for path in python_files(RUNTIME_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.adaptive_scoring_review", imports)
                self.assertNotIn("learning.adaptive_scoring_review", imports)
                self.assertNotIn("adaptive_scoring_review", imports)

    def test_no_active_mutation_functions(self) -> None:
        tree = ast.parse(read_text(MODULE_PATH), filename=str(MODULE_PATH))
        function_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        for forbidden_name in FORBIDDEN_ACTIVE_FUNCTIONS:
            with self.subTest(function_name=forbidden_name):
                self.assertNotIn(forbidden_name, function_names)

    def create_review(self, source=None, **overrides):
        module = review_module()
        kwargs = {
            "materialization_artifact": self.make_source_artifact() if source is None else source,
            "actor": "scoring-owner@example.com",
            "review_type": "scoring_weight_review",
            "proposed_config": self.proposed_config(),
            "proposed_config_version": "v1.0",
            "proposed_change_summary": "Review proposed scoring weight adjustment.",
            "before_after_summary": (
                "Before: current deterministic scoring remains authoritative. "
                "After: proposed scoring config is available for review only."
            ),
            "validation_requirements": None,
            "rollback_plan": "Keep the current runtime scoring config and discard the proposed version.",
            "runtime_influence_requested": True,
            "baseline_reference": "phase4i-current-scoring-baseline",
        }
        kwargs.update(overrides)
        return module.create_adaptive_scoring_review(**kwargs)

    def make_source_artifact(
        self,
        candidate_type: str = "scoring_weight_review_candidate",
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
        candidate_type: str = "scoring_weight_review_candidate",
        status: str = "MATERIALIZED",
    ) -> dict[str, object]:
        return artifact_module().materialization_artifact_to_dict(
            self.make_source_artifact(candidate_type=candidate_type, status=status)
        )

    def proposed_config(self) -> dict[str, object]:
        return {
            "domain_weights": {"sql": 1.25, "io": 0.9},
            "thresholds": {"critical": 85.0, "warning": 65.0},
            "severity_cutoffs": {"high": 80.0, "medium": 50.0},
            "confidence_rules": {"minimum_evidence_count": 2},
            "trend_sensitivity": {"window": "baseline-relative"},
            "anomaly_sensitivity": {"z_score": 2.5},
            "score_labels": {"critical": "Critical"},
        }

    def make_candidate_data(
        self,
        candidate_type: str = "scoring_weight_review_candidate",
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
