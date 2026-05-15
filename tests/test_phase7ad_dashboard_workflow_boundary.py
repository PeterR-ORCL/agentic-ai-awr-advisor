from __future__ import annotations

import ast
import importlib
import os
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
BOUNDARY_DOC = DOCS / "phase7ad_dashboard_workflow_boundary.md"
LIFECYCLE_DOC = DOCS / "phase7ad_dashboard_workflow_lifecycle.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "dashboard_workflow_boundary.py"

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

FORBIDDEN_BEHAVIOR_FILES = (
    "src/reporting/html_dashboard.py",
    "src/reporting/ai_display_metadata.py",
    "scripts/awr_memory_cli.py",
    "scripts/run_analysis.py",
)

FORBIDDEN_MODULE_IMPORT_PREFIXES = (
    "oracledb",
    "sqlite3",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
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


class Phase7ADDashboardWorkflowBoundaryTests(unittest.TestCase):
    def test_required_docs_exist(self) -> None:
        self.assertTrue(BOUNDARY_DOC.is_file(), BOUNDARY_DOC)
        self.assertTrue(LIFECYCLE_DOC.is_file(), LIFECYCLE_DOC)

    def test_boundary_doc_contains_required_sections(self) -> None:
        text = read_text(BOUNDARY_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Why Dashboard Workflow Infrastructure Is Needed",
            "## 5. Existing Read-Only Dashboard Boundary",
            "## 6. Future Write / Review Workflow Boundary",
            "## 7. Actor Requirement Boundary",
            "## 8. Backend Execution Mode Boundary",
            "## 9. Governed Write-Path Boundary",
            "## 10. Audit Trail Boundary",
            "## 11. Output Artifact Lifecycle Boundary",
            "## 12. Runtime Truth Boundary",
            "## 13. Phase 4I Contract Boundary",
            "## 14. Phase 7AA Runtime Gate Boundary",
            "## 15. Screen 1 Workflow Boundary",
            "## 16. Screen 2 Workflow Boundary",
            "## 17. Screen 3 Workflow Boundary",
            "## 18. Screen 4 Workflow Boundary",
            "## 19. Screen 5 Workflow Boundary",
            "## 20. Screen 6 Workflow Boundary",
            "## 21. Index / Source Mode Boundary",
            "## 22. Relationship to Future 7AE",
            "## 23. Relationship to Future 7AF",
            "## 24. Relationship to Future 7AG",
            "## 25. Relationship to Future 7AH",
            "## 26. Relationship to Future 7AI",
            "## 27. Relationship to Phase 8",
            "## 28. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_lifecycle_doc_contains_required_sections(self) -> None:
        text = read_text(LIFECYCLE_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Workflow Lifecycle Overview",
            "## 3. Read-Only Exploration Stage",
            "## 4. Actor Identification Stage",
            "## 5. Action Request Stage",
            "## 6. Request Validation Stage",
            "## 7. Authorization / Gate Stage",
            "## 8. Backend Execution Stage",
            "## 9. Output Artifact Stage",
            "## 10. Audit Trail Stage",
            "## 11. Error / Failure Stage",
            "## 12. Rollback / Fallback Stage",
            "## 13. Closure Stage",
            "## 14. Forbidden Shortcuts",
            "## 15. Required Audit Fields",
            "## 16. Required Validation Evidence",
            "## 17. Required Human Actors",
            "## 18. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_boundary_doc_contains_required_phrases(self) -> None:
        text = lower_text(BOUNDARY_DOC)
        for phrase in (
            "boundary-only",
            "no dashboard buttons are added",
            "no dashboard write controls are added",
            "no backend execution is added",
            "no run_analysis.py wiring is added",
            "no phase 4i mutation is added",
            "no parser/scoring/decision/recommendation behavior changes are added",
            "future workflow actions require actor identity",
            "future workflow actions require validation",
            "future workflow actions require audit trail",
            "deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_lifecycle_doc_contains_required_phrases(self) -> None:
        text = lower_text(LIFECYCLE_DOC)
        for phrase in (
            "no action may skip actor identification",
            "no action may skip validation",
            "no write may skip audit",
            "no backend execution may skip execution mode declaration",
            "no runtime mutation may bypass phase 7aa gate",
            "no workflow is implemented in 7ad",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_future_workflow_types_are_documented(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for phrase in (
            "diagnostic review workflow",
            "backend re-analysis workflow",
            "parser governance workflow",
            "recommendation/action/outcome workflow",
            "historical review workflow",
            "governance control workflow",
            "source mode workflow",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_screen_boundaries_are_documented(self) -> None:
        text = read_text(BOUNDARY_DOC)
        for phrase in (
            "Screen 1",
            "Screen 2",
            "Screen 3",
            "Screen 4",
            "Screen 5",
            "Screen 6",
            "Index / Source Mode",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_optional_module_safety_if_present(self) -> None:
        if not MODULE_PATH.is_file():
            self.skipTest("optional dashboard workflow boundary module not present")

        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.dashboard_workflow_boundary")
        self.assertEqual(before_environment, dict(os.environ))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_MODULE_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

        summary = module.dashboard_workflow_boundary_summary()
        self.assertTrue(summary["boundary_only"])
        self.assertFalse(summary["workflow_implemented"])
        self.assertFalse(summary["dashboard_buttons_added"])
        self.assertFalse(summary["dashboard_write_controls_added"])
        self.assertFalse(summary["backend_execution_added"])
        self.assertFalse(summary["actor_model_implemented"])
        self.assertFalse(summary["governed_write_path_implemented"])
        self.assertFalse(summary["output_lifecycle_implemented"])
        self.assertFalse(summary["run_analysis_wiring_added"])
        self.assertFalse(summary["phase4i_mutation_added"])
        self.assertTrue(summary["deterministic_runtime_authoritative"])
        self.assertFalse(summary["phase8_sizing_tco_implemented"])
        self.assertIn("no workflow is implemented in 7AD", summary["summary"])

        boundary = module.validate_dashboard_workflow_boundary()
        self.assertIn("diagnostic review workflow", boundary["workflow_types"])
        self.assertIn("actor identity", boundary["required_gates"])

        with self.assertRaises(module.DashboardWorkflowBoundaryError):
            module.validate_dashboard_workflow_boundary(mode="execution")

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.dashboard_workflow_boundary",
            "learning.dashboard_workflow_boundary",
            "dashboard_workflow_boundary",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.dashboard_workflow_boundary", imports)
                self.assertNotIn("learning.dashboard_workflow_boundary", imports)
                self.assertNotIn("dashboard_workflow_boundary", imports)

    def test_behavior_files_are_not_modified_by_phase7ad(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not available")
        if not (ROOT / ".git").exists():
            self.skipTest("not a git checkout")

        completed = subprocess.run(
            ("git", "diff", "--name-only", "--", *FORBIDDEN_BEHAVIOR_FILES),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            self.skipTest(completed.stderr.strip() or "git diff unavailable")

        changed = {
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip()
        }
        changed -= {"src/reporting/html_dashboard.py"}  # Phase 7AN owns disabled Screen 3 action UI.
        self.assertFalse(changed, f"behavior files modified: {sorted(changed)}")

    def test_readme_links_new_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7AD Dashboard Workflow Infrastructure Boundary",
                "phase7ad_dashboard_workflow_boundary.md",
            ),
            (
                "Phase 7AD Dashboard Workflow Lifecycle",
                "phase7ad_dashboard_workflow_lifecycle.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
