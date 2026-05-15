"""Tests for Phase 7 dashboard workflow infrastructure readiness."""

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
SCRIPT = ROOT / "scripts" / "run_phase7_dashboard_workflow_readiness_check.py"
DOCS = ROOT / "docs" / "architecture"
README = DOCS / "README.md"
SELFTEST = os.environ.get("PHASE7_DASHBOARD_WORKFLOW_READINESS_SELFTEST") == "1"

READINESS_DOC = DOCS / "phase7_dashboard_workflow_readiness.md"
RELEASE_DOC = DOCS / "phase7_dashboard_workflow_release_certification.md"
CHECKLIST_DOC = DOCS / "phase7_dashboard_workflow_operational_checklist.md"
VALIDATION_MATRIX = DOCS / "phase7_dashboard_workflow_validation_matrix.md"

REQUIRED_CATEGORIES = (
    "workflow_boundary",
    "actor_identity",
    "backend_execution_mode",
    "governed_write_path",
    "output_lifecycle",
    "runtime_isolation",
    "documentation_complete",
    "phase7_regression",
    "phase6_regression",
)

FORBIDDEN_IMPORTS = (
    "oracledb",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
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


class Phase7DashboardWorkflowReadinessTests(unittest.TestCase):
    def test_readiness_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT),
                cfile=str(Path(tempdir) / "run_phase7_dashboard_workflow_readiness_check.pyc"),
                doraise=True,
            )

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_readiness_script_normal_output_returns_success(self) -> None:
        completed = run_script()
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn(
            "Phase 7 dashboard workflow infrastructure readiness passed.",
            completed.stdout,
        )
        self.assertIn("dashboard_workflow_ready=true", completed.stdout)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_readiness_script_json_returns_required_payload(self) -> None:
        completed = run_script("--json")
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["phase"], "Phase 7AD-7AI")
        self.assertEqual(
            payload["command"],
            "run_phase7_dashboard_workflow_readiness_check",
        )
        self.assertIs(payload["success"], True)
        self.assertIs(payload["dashboard_workflow_ready"], True)
        for category in REQUIRED_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(category, payload["readiness_categories"])
        self.assertIs(payload["backend_execution_performed"], False)
        self.assertIs(payload["write_performed"], False)
        self.assertIs(payload["output_written"], False)
        self.assertIs(payload["dashboard_regenerated"], False)
        self.assertIs(payload["phase4i_mutated"], False)
        self.assertIs(payload["deterministic_runtime_remains_authoritative"], True)

    def test_readiness_docs_exist(self) -> None:
        self.assertTrue(READINESS_DOC.is_file(), READINESS_DOC)

    def test_release_certification_docs_exist(self) -> None:
        self.assertTrue(RELEASE_DOC.is_file(), RELEASE_DOC)

    def test_operational_checklist_docs_exist(self) -> None:
        self.assertTrue(CHECKLIST_DOC.is_file(), CHECKLIST_DOC)

    def test_validation_matrix_exists(self) -> None:
        self.assertTrue(VALIDATION_MATRIX.is_file(), VALIDATION_MATRIX)

    def test_readiness_docs_contain_required_language(self) -> None:
        combined = "\n".join(
            read_text(path).lower()
            for path in (READINESS_DOC, RELEASE_DOC, CHECKLIST_DOC)
        )
        for phrase in (
            "dashboard_workflow_ready=true only when all checks pass",
            "infrastructure is ready for future screen workflows",
            "no dashboard workflow is activated yet",
            "no backend execution occurs yet",
            "7ad-7ai is certified as workflow infrastructure only",
            "no screen 2/3/5/6 workflows are certified here",
            "no backend execution is certified here",
            "no runtime mutation is certified here",
            "do not certify if validation fails",
            "do not treat infrastructure readiness as workflow activation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_readme_links_new_dashboard_workflow_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7 Dashboard Workflow Validation Matrix",
                "phase7_dashboard_workflow_validation_matrix.md",
            ),
            (
                "Phase 7 Dashboard Workflow Readiness",
                "phase7_dashboard_workflow_readiness.md",
            ),
            (
                "Phase 7 Dashboard Workflow Release Certification",
                "phase7_dashboard_workflow_release_certification.md",
            ),
            (
                "Phase 7 Dashboard Workflow Operational Checklist",
                "phase7_dashboard_workflow_operational_checklist.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)

    def test_readiness_script_has_no_unsafe_imports(self) -> None:
        tree = ast.parse(read_text(SCRIPT), filename=str(SCRIPT))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        for forbidden in FORBIDDEN_IMPORTS:
            self.assertFalse(
                any(
                    imported == forbidden or imported.startswith(f"{forbidden}.")
                    for imported in imports
                ),
                f"unsafe import found: {forbidden}",
            )


if __name__ == "__main__":
    unittest.main()
