from __future__ import annotations

import ast
import importlib
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
EXPLAINABILITY_DOC = DOCS / "phase7_ml_explainability.md"
MODEL_DOC = DOCS / "phase7_ml_explainability_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "ml_explainability.py"

RUNTIME_PATHS = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "oracledb",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "sklearn",
    "tensorflow",
    "torch",
    "xgboost",
    "lightgbm",
    "catboost",
    "numpy",
    "sqlite3",
    "src.parser",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.reporting",
    "src.memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "apply_explanation",
    "activate_explanation",
    "update_runtime_scoring",
    "replace_scoring_engine",
    "update_decision",
    "update_recommendation",
    "auto_apply",
    "autonomous_apply",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


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


class Phase7MLExplainabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.ml_explainability")

    def contribution(self):
        module = self.module
        return module.FeatureContribution(
            feature_name="cpu_risk",
            feature_domain="CPU",
            contribution_direction="increases_risk",
            contribution_strength=0.82,
            contribution_weight=0.82,
            evidence_reference="feature://RUN-001/cpu_risk",
            explanation_text="CPU risk contribution is explanatory only.",
        )

    def comparison(self):
        return self.module.build_score_comparison_explanation(
            deterministic_score=60.0,
            trend_aware_score=66.0,
            shadow_ml_score=80.0,
        )

    def confidence(self):
        return self.module.build_confidence_explanation(
            confidence=0.74,
            factors=["shadow_ml_output", "trend_aware_score_available"],
        )

    def record(self, **overrides):
        module = self.module
        values = {
            "explanation_id": module.create_explanation_id(
                "SHADOW-OUTPUT-RUN-001",
                "SHADOW-MODEL-BASELINE",
                "CPU",
            ),
            "source_output_id": "SHADOW-OUTPUT-RUN-001",
            "model_id": "SHADOW-MODEL-BASELINE",
            "domain": "CPU",
            "feature_contributions": [self.contribution()],
            "score_comparison": self.comparison(),
            "confidence_explanation": self.confidence(),
            "top_positive_features": ["cpu_risk"],
            "top_negative_features": [],
            "boundary_summary": module.BOUNDARY_SUMMARY,
            "evidence_references": ["feature://RUN-001/cpu_risk"],
            "advisory_status": "SHADOW_EXPLANATION",
            "runtime_influence": False,
            "runtime_active": False,
            "runtime_influence_granted": False,
            "deterministic_runtime_remains_authoritative": True,
        }
        values.update(overrides)
        return module.MLExplanationRecord(**values)

    def shadow_output(self):
        shadow = importlib.import_module("src.learning.shadow_ml_model_interface")
        model_id = shadow.create_shadow_model_id(
            model_family="baseline_mock",
            model_version="7V.1",
            feature_schema_version="7T.1",
            label_schema_version="7T.1",
        )
        metadata = shadow.ShadowModelMetadata(
            model_id=model_id,
            model_family="baseline_mock",
            model_version="7V.1",
            feature_schema_version="7T.1",
            label_schema_version="7T.1",
            training_reference="training://phase7w/mock",
            validation_reference="validation://phase7w/backtest",
            runtime_active=False,
            runtime_influence_granted=False,
            notes="unit test metadata",
        )
        input_record = shadow.ShadowMLInput(
            input_id=shadow.create_shadow_ml_input_id(
                run_id="RUN-001",
                awr_id=None,
                model_id=model_id,
                score_version="7V.1",
            ),
            run_id="RUN-001",
            awr_id=None,
            feature_reference="feature://RUN-001/shadow",
            dataset_reference="dataset://phase7t/sample",
            deterministic_score=62.0,
            trend_aware_score=68.0,
            feature_values={
                "cpu_risk": 0.82,
                "io_wait_pressure": 71.0,
                "instance_name": "db01",
            },
            model_id=model_id,
            score_version="7V.1",
            runtime_influence=False,
            runtime_active=False,
        )
        return shadow.compute_placeholder_shadow_score(input_record, metadata)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.ml_explainability")
        self.assertEqual(before_environment, dict(os.environ))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )
        self.assertNotIn("uuid", imports)
        self.assertNotIn("datetime", imports)
        self.assertNotIn("time", imports)
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertFalse(hasattr(module, forbidden_name))

    def test_docs_exist(self) -> None:
        self.assertTrue(EXPLAINABILITY_DOC.is_file(), EXPLAINABILITY_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{read_text(EXPLAINABILITY_DOC)}\n{read_text(MODEL_DOC)}"
        lower = combined.lower()
        for phrase in (
            "explainability is not runtime truth",
            "explanations do not change runtime scoring",
            "deterministic scoring remains authoritative",
            "feature contributions are explanatory only",
            "confidence is not score",
            "semantic context is not ml explanation",
            "no model registry is implemented",
            "no runtime activation is implemented",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

    def test_feature_contribution_validation(self) -> None:
        module = self.module
        valid = module.validate_feature_contribution(self.contribution())
        self.assertEqual(valid.contribution_direction, "increases_risk")

        with self.assertRaises(module.MLExplainabilityError):
            module.FeatureContribution(
                feature_name="cpu_risk",
                feature_domain="CPU",
                contribution_direction="unsupported",
                contribution_strength=0.8,
                contribution_weight=0.8,
                evidence_reference=None,
                explanation_text="Invalid direction.",
            )
        with self.assertRaises(module.MLExplainabilityError):
            module.FeatureContribution(
                feature_name="cpu_risk",
                feature_domain="CPU",
                contribution_direction="increases_risk",
                contribution_strength=1.01,
                contribution_weight=0.8,
                evidence_reference=None,
                explanation_text="Invalid strength.",
            )
        with self.assertRaises(module.MLExplainabilityError):
            module.FeatureContribution(
                feature_name="cpu_risk",
                feature_domain="CPU",
                contribution_direction="increases_risk",
                contribution_strength=0.8,
                contribution_weight=1.01,
                evidence_reference=None,
                explanation_text="Invalid weight.",
            )

    def test_score_comparison(self) -> None:
        module = self.module
        comparison = module.build_score_comparison_explanation(
            deterministic_score=60.0,
            trend_aware_score=66.0,
            shadow_ml_score=80.0,
        )
        self.assertEqual(comparison.trend_delta, 6.0)
        self.assertEqual(comparison.shadow_delta, 20.0)
        self.assertEqual(comparison.disagreement_level, "high")
        self.assertIn("Deterministic score", comparison.disagreement_summary)

        no_context = module.build_score_comparison_explanation(
            deterministic_score=60.0
        )
        self.assertIsNone(no_context.trend_delta)
        self.assertIsNone(no_context.shadow_delta)
        self.assertEqual(no_context.disagreement_level, "insufficient_context")

        with self.assertRaises(module.MLExplainabilityError):
            module.build_score_comparison_explanation(
                deterministic_score=101.0,
                trend_aware_score=66.0,
                shadow_ml_score=80.0,
            )

    def test_confidence_explanation(self) -> None:
        module = self.module
        explanation = module.build_confidence_explanation(
            0.7,
            factors=["shadow_ml_output"],
            insufficient_context_flags=[],
        )
        self.assertEqual(explanation.confidence, 0.7)
        self.assertIn("confidence is not score", explanation.uncertainty_reason)

        with self.assertRaises(module.MLExplainabilityError):
            module.build_confidence_explanation(0.96)
        with self.assertRaises(module.MLExplainabilityError):
            module.ConfidenceExplanation(
                confidence=0.5,
                uncertainty_reason="",
                confidence_factors=[],
                insufficient_context_flags=[],
            )

    def test_ml_explanation_record_validation(self) -> None:
        module = self.module
        valid = module.validate_ml_explanation_record(self.record())
        self.assertFalse(valid.runtime_influence)
        self.assertFalse(valid.runtime_active)
        self.assertFalse(valid.runtime_influence_granted)
        self.assertTrue(valid.deterministic_runtime_remains_authoritative)

        with self.assertRaises(module.MLExplainabilityError):
            self.record(runtime_influence=True)
        with self.assertRaises(module.MLExplainabilityError):
            self.record(runtime_active=True)
        with self.assertRaises(module.MLExplainabilityError):
            self.record(runtime_influence_granted=True)
        with self.assertRaises(module.MLExplainabilityError):
            self.record(deterministic_runtime_remains_authoritative=False)

    def test_build_feature_contributions(self) -> None:
        module = self.module
        feature_values = {
            "io_wait_pressure": 70.0,
            "cpu_risk": 0.82,
            "instance_name": "db01",
            "active_sessions": 0,
        }
        first = module.build_feature_contributions(
            feature_values,
            evidence_reference="feature://RUN-001",
        )
        second = module.build_feature_contributions(
            feature_values,
            evidence_reference="feature://RUN-001",
        )
        self.assertEqual(
            [module.feature_contribution_to_dict(item) for item in first],
            [module.feature_contribution_to_dict(item) for item in second],
        )
        self.assertEqual(first[0].feature_name, "cpu_risk")
        self.assertEqual(first[0].contribution_direction, "increases_risk")
        directions = {item.feature_name: item.contribution_direction for item in first}
        self.assertEqual(directions["io_wait_pressure"], "increases_risk")
        self.assertEqual(directions["instance_name"], "neutral")
        self.assertEqual(directions["active_sessions"], "neutral")

    def test_build_explanation_from_shadow_output(self) -> None:
        module = self.module
        output = self.shadow_output()
        feature_values = {
            "cpu_risk": 0.82,
            "io_wait_pressure": 71.0,
            "instance_name": "db01",
        }
        record = module.build_ml_explanation_record(
            shadow_output=output,
            feature_values=feature_values,
            evidence_references=["validation://phase7w/backtest"],
        )
        expected_id = module.create_explanation_id(output.output_id, output.model_id)
        self.assertEqual(record.explanation_id, expected_id)
        self.assertEqual(record.source_output_id, output.output_id)
        self.assertEqual(record.score_comparison.shadow_ml_score, output.shadow_ml_score)
        self.assertEqual(record.confidence_explanation.confidence, output.confidence)
        self.assertIn("advisory/shadow only", record.boundary_summary)
        self.assertFalse(record.runtime_influence)
        self.assertFalse(record.runtime_active)
        self.assertFalse(record.runtime_influence_granted)
        self.assertTrue(record.deterministic_runtime_remains_authoritative)

    def test_serialization_round_trips(self) -> None:
        module = self.module
        contribution = self.contribution()
        contribution_dict = module.feature_contribution_to_dict(contribution)
        self.assertEqual(
            module.feature_contribution_to_dict(
                module.feature_contribution_from_dict(contribution_dict)
            ),
            contribution_dict,
        )

        comparison = self.comparison()
        comparison_dict = module.score_comparison_to_dict(comparison)
        self.assertEqual(
            module.score_comparison_to_dict(
                module.score_comparison_from_dict(comparison_dict)
            ),
            comparison_dict,
        )

        confidence = self.confidence()
        confidence_dict = module.confidence_explanation_to_dict(confidence)
        self.assertEqual(
            module.confidence_explanation_to_dict(
                module.confidence_explanation_from_dict(confidence_dict)
            ),
            confidence_dict,
        )

        record = self.record()
        record_dict = module.ml_explanation_record_to_dict(record)
        self.assertEqual(
            module.ml_explanation_record_to_dict(
                module.ml_explanation_record_from_dict(record_dict)
            ),
            record_dict,
        )

    def test_deterministic_ids(self) -> None:
        module = self.module
        first = module.create_explanation_id("source-1", "model-1", "CPU")
        second = module.create_explanation_id("source-1", "model-1", "CPU")
        self.assertEqual(first, second)
        self.assertEqual(first, "ML-EXPLAIN-SOURCE-1-MODEL-1-CPU")
        self.assertNotIn("UUID", first)
        self.assertNotIn("2026", first)

    def test_no_runtime_mutation_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertNotIn(forbidden_name, names)

    def test_runtime_import_isolation(self) -> None:
        files = python_files(RUNTIME_PATHS)
        self.assertTrue(files)
        for path in files:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("ml_explainability", read_text(path))


if __name__ == "__main__":
    unittest.main()
