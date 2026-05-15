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
BOUNDARY_DOC = DOCS / "phase7aj_screen3_reanalysis_boundary.md"
LIFECYCLE_DOC = DOCS / "phase7aj_screen3_reanalysis_lifecycle.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen3_reanalysis_boundary.py"

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


class Phase7AJScreen3ReanalysisBoundaryTests(unittest.TestCase):
    def test_required_docs_exist(self) -> None:
        self.assertTrue(BOUNDARY_DOC.is_file(), BOUNDARY_DOC)
        self.assertTrue(LIFECYCLE_DOC.is_file(), LIFECYCLE_DOC)

    def test_boundary_doc_contains_required_sections(self) -> None:
        text = read_text(BOUNDARY_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Why Screen 3 Needs Backend Re-Analysis",
            "## 5. Existing Screen 3 Read-Only Boundary",
            "## 6. Selection Is Not Execution",
            "## 7. Future Selected State",
            "## 8. Future Actions",
            "## 9. Actor Requirement",
            "## 10. Backend Execution Mode Requirement",
            "## 11. Governed Write-Path Requirement",
            "## 12. Output Lifecycle Requirement",
            "## 13. Source Mode Boundary",
            "## 14. Local Source Boundary",
            "## 15. Object Storage Boundary",
            "## 16. Deterministic Execution Boundary",
            "## 17. Controlled Adaptive Execution Boundary",
            "## 18. Phase 4I Contract Boundary",
            "## 19. AWR / Report Comparison Future Requirement",
            "## 20. Missing Metric / Evidence Availability Future Requirement",
            "## 21. Runtime Truth Boundary",
            "## 22. Relationship to 7AD-7AI",
            "## 23. Relationship to Future 7AK",
            "## 24. Relationship to Future 7AL",
            "## 25. Relationship to Future 7AM",
            "## 26. Relationship to Future 7AM.1",
            "## 27. Relationship to Future 7AN",
            "## 28. Relationship to Future 7AO",
            "## 29. Relationship to Future 7AO.1 / 7AQ.1",
            "## 30. Relationship to Phase 8",
            "## 31. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_lifecycle_doc_contains_required_sections(self) -> None:
        text = read_text(LIFECYCLE_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Lifecycle Overview",
            "## 3. Read-Only Selection Stage",
            "## 4. User Action Stage",
            "## 5. Actor Identification Stage",
            "## 6. Backend Execution Mode Stage",
            "## 7. Governed Write-Path Stage",
            "## 8. Request Validation Stage",
            "## 9. Source Validation Stage",
            "## 10. Deterministic Execution Stage",
            "## 11. Controlled Adaptive Execution Stage",
            "## 12. Output Artifact Stage",
            "## 13. Dashboard Refresh Stage",
            "## 14. Error / Failure Stage",
            "## 15. Audit Trail Stage",
            "## 16. Forbidden Shortcuts",
            "## 17. Required Validation Evidence",
            "## 18. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_boundary_doc_contains_required_phrases(self) -> None:
        text = lower_text(BOUNDARY_DOC)
        for phrase in (
            "boundary-only",
            "no screen 3 buttons are added",
            "no backend execution is added",
            "no source selection implementation is added",
            "no object storage calls are added",
            "no run_analysis.py wiring is added",
            "no phase 4i mutation is added",
            "no dashboard behavior is changed",
            "selection is not execution",
            "deterministic execution is default",
            "controlled adaptive execution requires gate",
            "awr/report comparison is future 7am.1",
            "missing metric handling is future 7ao.1 / 7aq.1",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_lifecycle_doc_contains_required_phrases(self) -> None:
        text = lower_text(LIFECYCLE_DOC)
        for phrase in (
            "no lifecycle stage is implemented in 7aj",
            "future execution cannot skip actor",
            "future execution cannot skip validation",
            "future execution cannot skip output artifact tracking",
            "future adaptive execution cannot bypass 7aa gate",
            "object storage cannot be loaded without explicit validation",
            "comparison cannot be built without validated sources",
            "missing metrics must affect validation/confidence later",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_future_selected_state_fields_are_documented(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for field_name in (
            "selected_awr",
            "selected_run",
            "selected_database",
            "selected_system",
            "selected_snapshot",
            "selected_comparison_baseline",
            "selected_issue_domain",
            "selected_severity_status",
            "selected_source_mode",
            "selected_execution_mode",
        ):
            with self.subTest(field_name=field_name):
                self.assertIn(field_name, text)

    def test_future_actions_are_documented(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for action_name in (
            "analyze_selection",
            "rerun_analysis",
            "build_comparison",
            "load_from_object_storage",
        ):
            with self.subTest(action_name=action_name):
                self.assertIn(action_name, text)

    def test_optional_module_safety_if_present(self) -> None:
        if not MODULE_PATH.is_file():
            self.skipTest("optional Screen 3 re-analysis boundary module not present")

        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.screen3_reanalysis_boundary")
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

        summary = module.screen3_reanalysis_boundary_summary()
        self.assertTrue(summary["boundary_only"])
        self.assertFalse(summary["selection_is_execution"])
        self.assertFalse(summary["screen3_buttons_added"])
        self.assertFalse(summary["backend_execution_implemented"])
        self.assertFalse(summary["source_selection_implemented"])
        self.assertFalse(summary["object_storage_calls_added"])
        self.assertFalse(summary["run_analysis_wiring_added"])
        self.assertFalse(summary["phase4i_mutation_added"])
        self.assertFalse(summary["dashboard_behavior_changed"])
        self.assertFalse(summary["cli_behavior_changed"])
        self.assertTrue(summary["deterministic_execution_default"])
        self.assertTrue(summary["controlled_adaptive_execution_requires_gate"])
        self.assertFalse(summary["phase8_sizing_tco_implemented"])
        self.assertIn("no backend execution is implemented", summary["summary"])

        boundary = module.validate_screen3_reanalysis_boundary()
        self.assertIn("selected_awr", boundary["selected_state_fields"])
        self.assertIn("analyze_selection", boundary["future_actions"])
        self.assertIn("actor identity", boundary["required_gates"])

        with self.assertRaises(module.Screen3ReanalysisBoundaryError):
            module.validate_screen3_reanalysis_boundary(mode="execution")

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen3_reanalysis_boundary",
            "learning.screen3_reanalysis_boundary",
            "screen3_reanalysis_boundary",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen3_reanalysis_boundary", imports)
                self.assertNotIn("learning.screen3_reanalysis_boundary", imports)
                self.assertNotIn("screen3_reanalysis_boundary", imports)
                self.assertNotIn("screen3_reanalysis_boundary", source)

    def test_behavior_files_are_not_modified_by_phase7aj(self) -> None:
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
                "Phase 7AJ Screen 3 Backend Re-Analysis Boundary",
                "phase7aj_screen3_reanalysis_boundary.md",
            ),
            (
                "Phase 7AJ Screen 3 Backend Re-Analysis Lifecycle",
                "phase7aj_screen3_reanalysis_lifecycle.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
