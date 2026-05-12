from __future__ import annotations

import ast
import importlib.util
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
README = DOCS / "README.md"
READINESS_SCRIPT = ROOT / "scripts" / "run_phase7_readiness_check.py"
SELFTEST = os.environ.get("PHASE7_READINESS_SELFTEST") == "1"

READINESS_DOCS = (
    DOCS / "phase7_production_readiness.md",
    DOCS / "phase7_release_certification.md",
    DOCS / "phase7_operational_checklist.md",
)

SAFETY_LANGUAGE = (
    "deterministic runtime remains authoritative",
    "no runtime activation",
    "candidate-based",
    "human-governed",
    "semantic context remains reviewer-assist only",
    "dashboard interactivity remains read-only",
    "cli learning commands are local and actor-gated",
    "no parser/scoring/decision/recommendation behavior change",
)

REQUIRED_CATEGORIES = (
    "validation_harness",
    "dashboard_interactivity_validation",
    "learning_cli_validation",
    "documentation_complete",
    "runtime_isolation",
    "semantic_boundary",
    "learning_candidate_safety",
    "governance_safety",
    "readiness_docs",
)

OPERATIONAL_COMMANDS = (
    "python3 scripts/run_phase7_readiness_check.py",
    "python3 scripts/run_phase7_readiness_check.py --json",
    "python3 scripts/run_phase7_validation.py",
    "python3 scripts/run_phase7h_dashboard_validation.py",
    "python3 scripts/awr_memory_cli.py learning validate --json",
    "PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_readiness_module():
    spec = importlib.util.spec_from_file_location("phase7_readiness_check", READINESS_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load readiness script module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Phase7ReadinessCheckTests(unittest.TestCase):
    def test_readiness_script_exists(self) -> None:
        self.assertTrue(READINESS_SCRIPT.is_file(), READINESS_SCRIPT)

    def test_readiness_script_compiles(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(READINESS_SCRIPT),
                cfile=str(Path(tempdir) / "run_phase7_readiness_check.pyc"),
                doraise=True,
            )

    def test_readiness_docs_exist(self) -> None:
        for path in READINESS_DOCS:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), path)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_readiness_script_supports_json(self) -> None:
        completed = subprocess.run(
            (sys.executable, str(READINESS_SCRIPT), "--json"),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertIs(payload["success"], True)
        self.assertIs(payload["production_ready"], True)
        self.assertEqual(payload["phase"], "Phase 7")
        self.assertEqual(payload["command"], "run_phase7_readiness_check")
        self.assertIs(payload["runtime_influence"], False)
        self.assertIs(payload["network_dependency"], False)
        self.assertIs(payload["database_dependency"], False)
        self.assertIs(payload["oracle_agent_memory_dependency"], False)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_readiness_script_normal_output(self) -> None:
        completed = subprocess.run(
            (sys.executable, str(READINESS_SCRIPT)),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("Phase 7 readiness check passed", completed.stdout)
        self.assertIn("production_ready=true", completed.stdout)

    def test_required_readiness_categories_present(self) -> None:
        module = load_readiness_module()
        categories = set(module.READINESS_CATEGORY_KEYS)
        for category in REQUIRED_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(category, categories)

    def test_required_docs_contain_safety_language(self) -> None:
        combined = "\n".join(read_text(path).lower() for path in READINESS_DOCS)
        for phrase in SAFETY_LANGUAGE:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_release_certification_contains_non_goals(self) -> None:
        text = read_text(DOCS / "phase7_release_certification.md").lower()
        for phrase in (
            "not autonomous self-learning",
            "does not activate candidates",
            "does not automatically modify parser/scoring/recommendation logic",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_operational_checklist_contains_required_commands(self) -> None:
        text = read_text(DOCS / "phase7_operational_checklist.md")
        for command in OPERATIONAL_COMMANDS:
            with self.subTest(command=command):
                self.assertIn(command, text)

    def test_readme_links_readiness_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            ("Phase 7 Production Readiness", "phase7_production_readiness.md"),
            ("Phase 7 Release Certification", "phase7_release_certification.md"),
            ("Phase 7 Operational Checklist", "phase7_operational_checklist.md"),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)

    def test_no_unsafe_dependencies(self) -> None:
        source = read_text(READINESS_SCRIPT)
        tree = ast.parse(source, filename=str(READINESS_SCRIPT))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

        for forbidden in ("oracledb", "requests", "socket", "urllib", "http.client", "httpx", "oci"):
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        module == forbidden or module.startswith(f"{forbidden}.")
                        for module in imports
                    )
                )

        self.assertNotIn("shell=True", source)
        self.assertNotIn("OCI_", source)
        self.assertNotIn("ORACLE_", source)
        self.assertNotIn("AgentMemory", source)

    def test_phase7_validation_script_remains_available_and_referenced(self) -> None:
        self.assertTrue((ROOT / "scripts" / "run_phase7_validation.py").is_file())
        combined_docs = "\n".join(read_text(path) for path in READINESS_DOCS)
        self.assertIn("scripts/run_phase7_validation.py", combined_docs)


if __name__ == "__main__":
    unittest.main()
