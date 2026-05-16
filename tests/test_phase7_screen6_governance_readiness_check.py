"""Tests for Phase 7BK-7BP Screen 6 governance readiness checks."""

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
SCRIPT = ROOT / "scripts" / "run_phase7_screen6_governance_readiness_check.py"
VALIDATION_SCRIPT = ROOT / "scripts" / "run_phase7_screen6_governance_validation.py"
README = ROOT / "docs" / "architecture" / "README.md"

REQUIRED_CATEGORIES = (
    "governance_boundary",
    "candidate_review",
    "candidate_review_panel",
    "materialization_review",
    "materialization_review_panel",
    "model_registry_review",
    "model_registry_review_panel",
    "runtime_gate_review",
    "runtime_gate_review_panel",
    "screen6_visibility_regression",
    "runtime_isolation",
    "documentation_complete",
    "phase7_regression",
    "phase6_regression",
)

README_LINKS = (
    "phase7_screen6_governance_validation_matrix.md",
    "phase7_screen6_governance_readiness.md",
    "phase7_screen6_governance_release_certification.md",
    "phase7_screen6_governance_operational_checklist.md",
)

FORBIDDEN_IMPORTS = (
    "subprocess",
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
    "oracle_agent_memory",
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


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


class Phase7Screen6GovernanceReadinessCheckTests(unittest.TestCase):
    _json_payload: dict[str, object] | None = None
    _text_result: subprocess.CompletedProcess[str] | None = None

    def test_readiness_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT),
                cfile=str(Path(tempdir) / "run_phase7_screen6_governance_readiness_check.pyc"),
                doraise=True,
            )

    def test_text_output_passes(self) -> None:
        completed = self.text_result()
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("Phase 7 Screen 6 governance readiness passed.", completed.stdout)
        self.assertIn("screen6_governance_ready=true", completed.stdout)

    def test_json_output_valid(self) -> None:
        payload = self.json_payload()
        self.assertEqual(payload["phase"], "Phase 7BK-7BP")
        self.assertEqual(payload["command"], "run_phase7_screen6_governance_readiness_check")
        self.assertIs(payload["success"], True)
        self.assertIs(payload["screen6_governance_ready"], True)

    def test_readiness_categories_present(self) -> None:
        payload = self.json_payload()
        categories = payload["readiness_categories"]
        for category in REQUIRED_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(category, categories)
        self.assertIs(categories["phase7_regression"], None)
        self.assertIs(categories["phase6_regression"], None)

    def test_required_json_safety_flags(self) -> None:
        payload = self.json_payload()
        self.assertIs(payload["governance_action_performed"], False)
        self.assertIs(payload["candidate_status_changed"], False)
        self.assertIs(payload["materialization_status_changed"], False)
        self.assertIs(payload["model_registry_status_changed"], False)
        self.assertIs(payload["runtime_gate_state_changed"], False)
        self.assertIs(payload["runtime_eligibility_granted"], False)
        self.assertIs(payload["runtime_active"], False)
        self.assertIs(payload["phase4i_mutated"], False)
        self.assertIs(payload["deterministic_runtime_remains_authoritative"], True)

    def test_readme_links_docs(self) -> None:
        text = read_text(README)
        for link in README_LINKS:
            with self.subTest(link=link):
                self.assertIn(link, text)

    def test_no_unsafe_imports(self) -> None:
        for script in (SCRIPT, VALIDATION_SCRIPT):
            imports = imported_modules(script)
            for forbidden in FORBIDDEN_IMPORTS:
                with self.subTest(script=script.name, forbidden=forbidden):
                    self.assertFalse(
                        any(
                            imported == forbidden or imported.startswith(f"{forbidden}.")
                            for imported in imports
                        ),
                        f"unsafe import found in {script.name}: {forbidden}",
                    )

    @classmethod
    def json_payload(cls) -> dict[str, object]:
        if cls._json_payload is None:
            completed = run_script("--json")
            if completed.returncode != 0:
                raise AssertionError(completed.stderr or completed.stdout)
            cls._json_payload = json.loads(completed.stdout)
        return cls._json_payload

    @classmethod
    def text_result(cls) -> subprocess.CompletedProcess[str]:
        if cls._text_result is None:
            cls._text_result = run_script()
        return cls._text_result


if __name__ == "__main__":
    unittest.main()
