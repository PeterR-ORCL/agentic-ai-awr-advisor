from __future__ import annotations

import ast
import importlib
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
BOUNDARY_DOC = DOCS / "phase7_learning_materialization_boundary.md"
LIFECYCLE_DOC = DOCS / "phase7_materialization_lifecycle.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "materialization_boundary.py"

CANDIDATE_TYPES = (
    "parser_mapping_candidate",
    "recommendation_rule_candidate",
    "scoring_weight_review_candidate",
    "dashboard_wording_candidate",
    "dashboard_interaction_candidate",
    "governance_workflow_candidate",
    "semantic_summary_candidate",
    "documentation_candidate",
    "validation_candidate",
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


class Phase7LearningMaterializationBoundaryTests(unittest.TestCase):
    def test_required_docs_exist(self) -> None:
        self.assertTrue(BOUNDARY_DOC.is_file(), BOUNDARY_DOC)
        self.assertTrue(LIFECYCLE_DOC.is_file(), LIFECYCLE_DOC)

    def test_boundary_doc_contains_required_phrases(self) -> None:
        text = lower_text(BOUNDARY_DOC)
        for phrase in (
            "candidate approval does not equal runtime activation",
            "materialization is separate from approval",
            "materialization is not activation",
            "runtime_influence remains false",
            "parser evolution is first-class",
            "no automatic parser mutation",
            "no automatic scoring mutation",
            "no automatic recommendation mutation",
            "semantic context is not implementation truth",
            "dashboard and cli are not runtime mutation paths",
            "phase 4i contract must be preserved",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_lifecycle_doc_contains_required_phrases(self) -> None:
        text = lower_text(LIFECYCLE_DOC)
        for phrase in (
            "approved_for_implementation is not runtime active",
            "approved_for_materialization is not runtime active",
            "materialized is not runtime active",
            "runtime_influence_granted=false by default",
            "rollback plan is required",
            "no automatic activation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_candidate_types_covered(self) -> None:
        combined = f"{lower_text(BOUNDARY_DOC)}\n{lower_text(LIFECYCLE_DOC)}"
        for candidate_type in CANDIDATE_TYPES:
            with self.subTest(candidate_type=candidate_type):
                self.assertIn(candidate_type, combined)

    def test_parser_boundary_is_explicit(self) -> None:
        text = lower_text(BOUNDARY_DOC)
        for phrase in (
            "unknown signal",
            "parser_mapping_candidate",
            "parser materialization artifact",
            "controlled parser code/config change",
            "parser tests",
            "awr regression validation",
            "phase 4i contract validation",
            "no automatic parser mutation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_scoring_boundary_is_explicit(self) -> None:
        text = lower_text(BOUNDARY_DOC)
        for phrase in (
            "scoring_weight_review_candidate",
            "versioned scoring config",
            "before/after comparison",
            "regression tests",
            "no automatic scoring mutation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_recommendation_boundary_is_explicit(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for phrase in (
            "recommendation_rule_candidate",
            "versioned recommendation rules",
            "output contract preservation",
            "no automatic recommendation mutation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_optional_module_safety_if_present(self) -> None:
        if not MODULE_PATH.is_file():
            self.skipTest("optional materialization boundary module not present")

        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.materialization_boundary")
        self.assertEqual(before_environment, dict(os.environ))

        imports = imported_modules(MODULE_PATH)
        for forbidden in (
            "oracledb",
            "requests",
            "socket",
            "urllib",
            "http.client",
            "httpx",
            "oci",
            "src.parser",
            "src.parsing",
            "src.scoring",
            "src.decision",
            "src.recommendation",
            "src.recommendations",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

        summary = module.materialization_boundary_summary()
        self.assertFalse(summary["runtime_influence_granted"])
        self.assertFalse(summary["materialization_active"])
        self.assertFalse(summary["runtime_activation_active"])
        self.assertTrue(summary["candidate_approval_is_not_runtime_activation"])
        self.assertTrue(summary["materialization_is_separate_from_approval"])
        self.assertTrue(summary["materialization_is_not_activation"])
        self.assertEqual(set(summary["candidate_types"]), set(CANDIDATE_TYPES))

        for candidate_type in CANDIDATE_TYPES:
            with self.subTest(candidate_type=candidate_type):
                boundary = module.validate_materialization_boundary(candidate_type)
                data = boundary.to_dict()
                self.assertEqual(data["candidate_type"], candidate_type)
                self.assertTrue(data["materializable"])
                self.assertFalse(data["runtime_influence_requested"])
                self.assertFalse(data["runtime_influence_granted"])
                self.assertFalse(data["candidate_approval_is_runtime_activation"])
                self.assertFalse(data["materialization_is_activation"])

    def test_runtime_import_isolation(self) -> None:
        for path in python_files(RUNTIME_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.materialization_boundary", imports)
                self.assertNotIn("learning.materialization_boundary", imports)
                self.assertNotIn("materialization_boundary", imports)

                for imported in imports:
                    if imported == "src.learning" or imported.startswith("src.learning."):
                        self.fail(
                            f"{path.relative_to(ROOT)} imports {imported}; "
                            "runtime paths must not import materialization learning modules"
                        )

    def test_no_runtime_activation_markers(self) -> None:
        paths = [BOUNDARY_DOC, LIFECYCLE_DOC]
        if MODULE_PATH.is_file():
            paths.append(MODULE_PATH)

        for path in paths:
            text = lower_text(path)
            with self.subTest(path=path.name):
                self.assertNotIn("runtime_influence=true", text)
                self.assertNotIn("runtime_influence_granted=true", text)

        if MODULE_PATH.is_file():
            tree = ast.parse(read_text(MODULE_PATH), filename=str(MODULE_PATH))
            function_names = {
                node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
            }
            for forbidden_name in (
                "activate_runtime",
                "apply_materialization",
                "create_materialization_artifact",
                "persist_materialization",
                "transition_candidate_status",
                "write_materialization",
            ):
                with self.subTest(function_name=forbidden_name):
                    self.assertNotIn(forbidden_name, function_names)

    def test_readme_links_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7 Learning Materialization Boundary",
                "phase7_learning_materialization_boundary.md",
            ),
            ("Phase 7 Materialization Lifecycle", "phase7_materialization_lifecycle.md"),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
