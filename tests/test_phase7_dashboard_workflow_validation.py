"""Tests for Phase 7 dashboard workflow infrastructure validation."""

from __future__ import annotations

import ast
import json
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_dashboard_workflow_validation.py"
DOCS = ROOT / "docs" / "architecture"
VALIDATION_MATRIX = DOCS / "phase7_dashboard_workflow_validation_matrix.md"

REQUIRED_GROUPS = (
    "workflow_boundary",
    "actor_identity",
    "backend_execution_mode",
    "governed_write_path",
    "output_lifecycle",
    "import_isolation",
    "runtime_safety",
    "documentation",
)

REQUIRED_JSON_FIELDS = (
    "phase",
    "command",
    "success",
    "validation_groups",
    "tests_run",
    "checks_run",
    "failures",
    "errors",
    "skipped",
    "workflow_boundary_defined",
    "actor_identity_metadata_only",
    "backend_execution_metadata_only",
    "governed_write_path_dry_run_only",
    "output_lifecycle_metadata_only",
    "backend_execution_performed",
    "write_performed",
    "output_written",
    "dashboard_regenerated",
    "phase4i_mutated",
    "run_analysis_wired",
    "deterministic_runtime_remains_authoritative",
    "network_dependency",
    "database_dependency",
    "object_storage_dependency",
    "oracle_agent_memory_dependency",
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
    )


class Phase7DashboardWorkflowValidationTests(unittest.TestCase):
    def test_validation_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT),
                cfile=str(Path(tempdir) / "run_phase7_dashboard_workflow_validation.pyc"),
                doraise=True,
            )

    def test_validation_script_normal_output_returns_success(self) -> None:
        completed = run_script()
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn(
            "Phase 7 dashboard workflow infrastructure validation passed.",
            completed.stdout,
        )

    def test_validation_script_json_returns_required_payload(self) -> None:
        completed = run_script("--json")
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        for field in REQUIRED_JSON_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, payload)
        self.assertEqual(payload["phase"], "Phase 7AD-7AI")
        self.assertEqual(payload["command"], "run_phase7_dashboard_workflow_validation")
        self.assertIs(payload["success"], True)

    def test_required_validation_groups_are_present(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        groups = {group["name"] for group in payload["validation_groups"]}
        for group in REQUIRED_GROUPS:
            with self.subTest(group=group):
                self.assertIn(group, groups)

    def test_json_safety_flags_are_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["backend_execution_performed"], False)
        self.assertIs(payload["write_performed"], False)
        self.assertIs(payload["output_written"], False)
        self.assertIs(payload["dashboard_regenerated"], False)
        self.assertIs(payload["phase4i_mutated"], False)
        self.assertIs(payload["run_analysis_wired"], False)
        self.assertIs(payload["deterministic_runtime_remains_authoritative"], True)

    def test_validation_script_has_no_unsafe_imports(self) -> None:
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

    def test_documentation_validation_matrix_exists_and_has_required_language(self) -> None:
        self.assertTrue(VALIDATION_MATRIX.is_file(), VALIDATION_MATRIX)
        text = read_text(VALIDATION_MATRIX).lower()
        for phrase in (
            "workflow infrastructure is metadata/validation only",
            "no dashboard workflows are implemented here",
            "no backend execution occurs",
            "no write is performed",
            "no output artifact is written",
            "deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
