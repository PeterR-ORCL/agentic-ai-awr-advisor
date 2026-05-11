from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
LEARNING_DIR = ROOT / "src" / "learning"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class Phase7LearningBoundaryTests(unittest.TestCase):
    def test_phase7_docs_exist(self) -> None:
        for relative_path in (
            "docs/architecture/phase7_learning_boundary.md",
            "docs/architecture/phase7_candidate_lifecycle.md",
            "docs/architecture/phase7_roadmap.md",
        ):
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

    def test_boundary_document_contains_required_phrases(self) -> None:
        text = read_text(DOCS / "phase7_learning_boundary.md").lower()
        for phrase in (
            "candidate-based",
            "human-reviewed",
            "non-authoritative until approved",
            "no runtime self-modification",
            "no autonomous parser changes",
            "no autonomous scoring changes",
            "no autonomous recommendation changes",
            "semantic recall is reviewer-assist only",
            "deterministic runtime remains authoritative",
            "runtime_influence=false",
            "dashboard selections must not mutate backend truth",
            "dashboard interactivity is exploratory and read-only",
        ):
            self.assertIn(phrase, text)

    def test_candidate_lifecycle_document_contains_required_terms(self) -> None:
        text = read_text(DOCS / "phase7_candidate_lifecycle.md")
        for term in (
            "PROPOSED",
            "UNDER_REVIEW",
            "APPROVED_FOR_IMPLEMENTATION",
            "REJECTED",
            "NEEDS_REVISION",
            "IMPLEMENTED",
            "VALIDATED",
            "CLOSED",
            "runtime_influence",
            "requires_human_review",
            "semantic_context",
            "source_evidence",
            "dashboard_interaction_candidate",
        ):
            self.assertIn(term, text)

    def test_roadmap_document_contains_phase7_plan_and_dashboard_goal(self) -> None:
        text = read_text(DOCS / "phase7_roadmap.md")
        for term in (
            "Phase 7A",
            "Phase 7B",
            "Phase 7C",
            "Phase 7D",
            "Phase 7E",
            "Phase 7F",
            "Phase 7G",
            "Phase 7H",
            "Phase 7I",
            "Phase 7J",
            "Phase 7K",
            "Phase 7L",
            "Full Dashboard Interactive Selection Upgrade",
            "all current static selection areas",
            "fully interactive",
            "selectable",
            "exploratory and read-only",
        ):
            self.assertIn(term, text)

    def test_run_analysis_does_not_import_learning_modules(self) -> None:
        path = ROOT / "scripts" / "run_analysis.py"
        self.assertTrue(path.is_file())
        self.assertNoLearningImports(path)

    def test_runtime_paths_do_not_import_learning_modules(self) -> None:
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

        self.assertTrue(checked_files, "expected at least one runtime file to inspect")
        for path in checked_files:
            self.assertNoLearningImports(path)

    def test_no_autonomous_learning_function_names_exist(self) -> None:
        if not LEARNING_DIR.exists():
            return

        forbidden_names = (
            "auto_apply",
            "autonomous_apply",
            "self_modify",
            "mutate_runtime",
            "update_parser_automatically",
            "update_scoring_automatically",
            "update_recommendations_automatically",
        )
        for path in sorted(LEARNING_DIR.rglob("*.py")):
            text = read_text(path).lower()
            for name in forbidden_names:
                self.assertNotIn(name, text, f"{name} found in {path}")

    def test_semantic_recall_remains_non_authoritative(self) -> None:
        semantic_paths = [
            ROOT / "src" / "memory" / "semantic_recall_service.py",
            ROOT / "src" / "memory" / "governance_semantic_assist.py",
            ROOT / "src" / "memory" / "oracle_agent_memory_adapter.py",
        ]
        existing_paths = [path for path in semantic_paths if path.is_file()]
        self.assertTrue(existing_paths, "expected semantic memory files to inspect")

        for path in existing_paths:
            text = read_text(path).lower()
            self.assertTrue(
                any(
                    phrase in text
                    for phrase in (
                        "non_authoritative",
                        "non-authoritative",
                        "runtime_influence",
                        "reviewer",
                    )
                ),
                f"semantic boundary wording missing from {path}",
            )

    def test_dashboard_interactivity_is_documented_as_future_phase7h_only(self) -> None:
        boundary = read_text(DOCS / "phase7_learning_boundary.md").lower()
        roadmap = read_text(DOCS / "phase7_roadmap.md").lower()

        self.assertIn("future phase 7h", boundary)
        self.assertIn("phase 7a does not implement dashboard interactivity", boundary)
        self.assertIn("future/deferred", roadmap)
        self.assertIn("do not implement dashboard interactivity in phase 7a", roadmap)
        self.assertIn("selections are exploratory and read-only", roadmap)

    def assertNoLearningImports(self, path: Path) -> None:
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
