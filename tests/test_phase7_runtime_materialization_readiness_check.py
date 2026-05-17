"""Phase 7BZ tests for runtime materialization readiness."""

from __future__ import annotations

import ast
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_runtime_materialization_readiness_check.py"
README = ROOT / "docs" / "architecture" / "README.md"

REQUIRED_CATEGORIES = (
    "governed_workflow_persistence",
    "status_transition_execution",
    "parser_runtime_update",
    "scoring_runtime_activation",
    "recommendation_runtime_activation",
    "ml_runtime_eligibility",
    "runtime_isolation",
    "documentation_complete",
    "phase7_regression",
    "phase6_regression",
)

README_LINKS = (
    "phase7_runtime_materialization_validation_matrix.md",
    "phase7_runtime_materialization_readiness.md",
    "phase7_runtime_materialization_release_certification.md",
    "phase7_runtime_materialization_operational_checklist.md",
)

FORBIDDEN_IMPORTS = (
    "oracledb",
    "cx_Oracle",
    "sqlite3",
    "requests",
    "httpx",
    "urllib",
    "socket",
    "http.client",
    "oci",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (sys.executable, str(SCRIPT), *args),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


class Phase7RuntimeMaterializationReadinessTests(unittest.TestCase):
    def test_readiness_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT),
                cfile=str(Path(tempdir) / "readiness.pyc"),
                doraise=True,
            )

    def test_text_output_passes(self) -> None:
        completed = run_script()
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn(
            "Phase 7 runtime materialization readiness passed.",
            completed.stdout,
        )
        self.assertIn("runtime_materialization_ready=true", completed.stdout)

    def test_json_output_valid(self) -> None:
        completed = run_script("--json")
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["phase"], "Phase 7BU-7BZ")
        self.assertEqual(
            payload["command"],
            "run_phase7_runtime_materialization_readiness_check",
        )
        self.assertIs(payload["success"], True)

    def test_runtime_materialization_ready_true(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["runtime_materialization_ready"], True)

    def test_readiness_categories_present(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        categories = payload["readiness_categories"]
        for category in REQUIRED_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(category, categories)
        self.assertIs(categories["governed_workflow_persistence"], True)
        self.assertIs(categories["status_transition_execution"], True)
        self.assertIs(categories["parser_runtime_update"], True)
        self.assertIs(categories["scoring_runtime_activation"], True)
        self.assertIs(categories["recommendation_runtime_activation"], True)
        self.assertIs(categories["ml_runtime_eligibility"], True)
        self.assertIs(categories["runtime_isolation"], True)
        self.assertIs(categories["documentation_complete"], True)
        self.assertIsNone(categories["phase7_regression"])
        self.assertIsNone(categories["phase6_regression"])

    def test_db_persistence_performed_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["db_persistence_performed"], False)

    def test_status_transition_performed_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["status_transition_performed"], False)

    def test_runtime_active_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["runtime_active"], False)

    def test_phase4i_mutated_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["phase4i_mutated"], False)

    def test_readme_links_docs(self) -> None:
        text = read_text(README)
        for link in README_LINKS:
            with self.subTest(link=link):
                self.assertIn(link, text)

    def test_no_unsafe_imports(self) -> None:
        tree = ast.parse(read_text(SCRIPT), filename=str(SCRIPT))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        for forbidden in FORBIDDEN_IMPORTS:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )
        self.assertNotIn("shell=True", read_text(SCRIPT))


if __name__ == "__main__":
    unittest.main()
