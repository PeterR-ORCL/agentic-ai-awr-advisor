from __future__ import annotations

import ast
import importlib
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
BOUNDARY_DOC = DOCS / "phase7_ml_adaptive_scoring_boundary.md"
LIFECYCLE_DOC = DOCS / "phase7_ml_lifecycle.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "ml_boundary.py"

RUNTIME_PATHS = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "sklearn",
    "tensorflow",
    "torch",
    "oracledb",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "src.parser",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "train_model",
    "learned_model",
    "score_ml",
    "apply_ml_score",
    "activate_model",
    "update_runtime_scoring",
    "replace_scoring_engine",
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


class Phase7MLAdaptiveScoringBoundaryTests(unittest.TestCase):
    def test_required_docs_exist(self) -> None:
        self.assertTrue(BOUNDARY_DOC.is_file(), BOUNDARY_DOC)
        self.assertTrue(LIFECYCLE_DOC.is_file(), LIFECYCLE_DOC)

    def test_boundary_doc_contains_required_sections(self) -> None:
        text = read_text(BOUNDARY_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Deterministic Scoring Boundary",
            "## 5. ML Shadow Mode Boundary",
            "## 6. Observation Boundary",
            "## 7. Scoring Boundary",
            "## 8. Proposal Boundary",
            "## 9. Runtime Influence Boundary",
            "## 10. Governance Boundary",
            "## 11. Materialization Boundary",
            "## 12. Validation Boundary",
            "## 13. Explainability Boundary",
            "## 14. Rollback Boundary",
            "## 15. Semantic Context Boundary",
            "## 16. Parser Boundary",
            "## 17. Recommendation Boundary",
            "## 18. Phase 4I Contract Boundary",
            "## 19. Phase 8 Boundary",
            "## 20. Future Phase 7T Dataset Model",
            "## 21. Future Phase 7U Trend-Aware Scoring",
            "## 22. Future Phase 7V Shadow ML Model Interface",
            "## 23. Future Phase 7W Training / Backtesting",
            "## 24. Future Phase 7X Explainability",
            "## 25. Future Phase 7Y Model Registry",
            "## 26. Future Phase 7Z ML Certification",
            "## 27. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_lifecycle_doc_contains_required_sections(self) -> None:
        text = read_text(LIFECYCLE_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Lifecycle Overview",
            "## 3. Observation Stage",
            "## 4. Dataset Stage",
            "## 5. Training Stage",
            "## 6. Shadow Scoring Stage",
            "## 7. Backtesting Stage",
            "## 8. Explainability Stage",
            "## 9. Candidate Proposal Stage",
            "## 10. Materialization Stage",
            "## 11. Model Registry Stage",
            "## 12. Runtime Eligibility Stage",
            "## 13. Rollback Stage",
            "## 14. Retirement Stage",
            "## 15. Forbidden Shortcuts",
            "## 16. Required Audit Fields",
            "## 17. Required Validation Evidence",
            "## 18. Required Human Actors",
            "## 19. Relationship to Phase 7M–7R",
            "## 20. Relationship to Phase 8",
            "## 21. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_boundary_doc_contains_required_phrases(self) -> None:
        text = lower_text(BOUNDARY_DOC)
        for phrase in (
            "ml starts in shadow mode",
            "deterministic scoring remains authoritative",
            "ml is non-authoritative by default",
            "learned_model(x) is not implemented",
            "score_ml(x) is not implemented",
            "score(x, t) is not implemented",
            "ml may compare, explain, and propose",
            "ml may not replace scoring",
            "ml may not change parser output",
            "ml may not change recommendation truth",
            "ml may not change phase 4i output",
            "ml may not bypass phase 7m–7r materialization",
            "phase 8 sizing/tco is not implemented here",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_lifecycle_doc_contains_required_phrases(self) -> None:
        text = lower_text(LIFECYCLE_DOC)
        for phrase in (
            "shadow scoring is not runtime scoring",
            "model validation is not runtime activation",
            "model approval is not runtime activation",
            "runtime eligibility requires explicit certification",
            "no automatic parser/scoring/recommendation mutation",
            "no learned model is active in phase 7s",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_ml_concepts_are_documented(self) -> None:
        combined = f"{read_text(BOUNDARY_DOC)}\n{read_text(LIFECYCLE_DOC)}"
        for phrase in (
            "Score(x)",
            "Score(x, t)",
            "Score_ml(x)",
            "learned_model(x)",
            "(X, y)",
            "feature vectors",
            "observed outcomes",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_future_phases_are_referenced(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for phrase in (
            "7t dataset model",
            "7u trend-aware scoring",
            "7v shadow ml model interface",
            "7w training/backtesting",
            "7x explainability",
            "7y model registry",
            "7z certification",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_materialization_relationship_is_explicit(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for phrase in (
            "phase 7m–7r",
            "materialization",
            "runtime eligibility",
            "rollback",
            "certification",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_optional_module_safety_if_present(self) -> None:
        if not MODULE_PATH.is_file():
            self.skipTest("optional ML boundary module not present")

        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.ml_boundary")
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

        summary = module.ml_boundary_summary()
        self.assertEqual(summary["mode"], "shadow")
        self.assertTrue(summary["shadow_mode"])
        self.assertTrue(summary["non_authoritative"])
        self.assertTrue(summary["deterministic_runtime_authoritative"])
        self.assertFalse(summary["runtime_active"])
        self.assertFalse(summary["runtime_influence_granted"])
        self.assertTrue(summary["learned_model_x_not_implemented"])
        self.assertTrue(summary["score_ml_x_not_implemented"])
        self.assertTrue(summary["score_x_t_not_implemented"])
        self.assertIn("shadow mode", summary["summary"])
        self.assertIn("non-authoritative", summary["summary"])
        self.assertIn(
            "deterministic runtime remains authoritative", summary["summary"]
        )
        self.assertIn("runtime_influence_granted=false", summary["summary"])
        self.assertIn("runtime_active=false", summary["summary"])
        self.assertIn("learned_model(x) not implemented", summary["summary"])

        boundary = module.validate_ml_runtime_boundary()
        self.assertFalse(boundary["runtime_active"])
        self.assertFalse(boundary["runtime_influence_granted"])
        self.assertTrue(boundary["ml_may_compare_explain_and_propose_only"])

        with self.assertRaises(module.MLBoundaryError):
            module.validate_ml_runtime_boundary(mode="runtime")

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        self.assertNotIn("src.learning.ml_boundary", run_analysis_imports)
        self.assertNotIn("learning.ml_boundary", run_analysis_imports)
        self.assertNotIn("ml_boundary", run_analysis_imports)

        for path in python_files(RUNTIME_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.ml_boundary", imports)
                self.assertNotIn("learning.ml_boundary", imports)
                self.assertNotIn("ml_boundary", imports)

                for imported in imports:
                    if imported == "src.learning" or imported.startswith("src.learning."):
                        self.fail(
                            f"{path.relative_to(ROOT)} imports {imported}; "
                            "runtime paths must not import ML boundary learning modules"
                        )

    def test_no_ml_implementation_functions(self) -> None:
        paths = [path for path in (MODULE_PATH,) if path.is_file()]
        for path in paths:
            names = function_names(path)
            for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
                with self.subTest(path=path.name, function_name=forbidden_name):
                    self.assertNotIn(forbidden_name, names)

    def test_no_runtime_activation_markers(self) -> None:
        paths = [BOUNDARY_DOC, LIFECYCLE_DOC]
        if MODULE_PATH.is_file():
            paths.append(MODULE_PATH)

        for path in paths:
            text = lower_text(path)
            with self.subTest(path=path.name):
                self.assertNotIn("runtime_influence" + "=true", text)
                self.assertNotIn("runtime_influence_granted" + "=true", text)
                self.assertNotIn("runtime_active" + "=true", text)

    def test_materialization_validation_entrypoints_still_exist(self) -> None:
        for relative_path in (
            "scripts/run_phase7_materialization_validation.py",
            "scripts/run_phase7_materialization_readiness_check.py",
            "tests/test_phase7_parser_mapping_evolution.py",
            "tests/test_phase7_recommendation_rule_evolution.py",
            "tests/test_phase7_adaptive_scoring_review.py",
            "tests/test_phase7_approved_candidate_materialization.py",
            "tests/test_phase7_learning_materialization_boundary.py",
        ):
            with self.subTest(relative_path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file(), relative_path)

    def test_readme_links_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7S ML / Adaptive Scoring Boundary",
                "phase7_ml_adaptive_scoring_boundary.md",
            ),
            ("Phase 7S ML Lifecycle", "phase7_ml_lifecycle.md"),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
