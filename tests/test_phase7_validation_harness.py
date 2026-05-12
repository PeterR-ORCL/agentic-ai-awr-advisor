from __future__ import annotations

import ast
import json
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import scripts.run_phase7_validation as harness


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_phase7_validation.py"
MATRIX_DOC = ROOT / "docs" / "architecture" / "phase7_validation_matrix.md"
HARNESS_DOC = ROOT / "docs" / "architecture" / "phase7_validation_harness.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class Phase7ValidationHarnessTests(unittest.TestCase):
    _json_completed: subprocess.CompletedProcess[str] | None = None
    _json_data: dict[str, object] | None = None

    def test_validation_script_exists(self) -> None:
        self.assertTrue(SCRIPT_PATH.is_file())

    def test_validation_script_compiles(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT_PATH),
                cfile=str(Path(tempdir) / "run_phase7_validation.pyc"),
                doraise=True,
            )

    def test_validation_docs_exist(self) -> None:
        self.assertTrue(MATRIX_DOC.is_file())
        self.assertTrue(HARNESS_DOC.is_file())

    def test_validation_script_supports_json(self) -> None:
        completed, data = self.run_json_validation()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(data["success"])
        self.assertEqual(data["command"], "run_phase7_validation")
        self.assertEqual(data["phase"], "Phase 7")
        self.assertFalse(data["runtime_influence"])
        self.assertFalse(data["network_dependency"])
        self.assertFalse(data["database_dependency"])
        self.assertFalse(data["oracle_agent_memory_dependency"])

    def test_validation_script_normal_output(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Phase 7 validation passed.", completed.stdout)
        self.assertIn("deterministic runtime remains authoritative", completed.stdout)

    def test_required_validation_groups_present(self) -> None:
        _, data = self.run_json_validation()
        groups = data["validation_groups"]
        self.assertIsInstance(groups, list)
        names = {group["name"] for group in groups}  # type: ignore[index]

        for name in (
            "phase7_boundary",
            "outcome_pattern_mining",
            "candidate_model",
            "candidate_generation",
            "semantic_candidate_context",
            "learning_governance_bridge",
            "dashboard_learning_visibility",
            "dashboard_interactivity",
            "learning_cli",
            "import_isolation",
            "runtime_safety",
            "documentation",
        ):
            self.assertIn(name, names)

    def test_import_isolation(self) -> None:
        result = harness.run_import_isolation_group()

        self.assertTrue(result["success"], result["details"])
        self.assertGreater(result["checks_run"], 0)

    def test_runtime_safety_markers(self) -> None:
        _, data = self.run_json_validation()

        self.assertTrue(data["deterministic_runtime_remains_authoritative"])
        self.assertTrue(data["semantic_context_non_authoritative"])
        self.assertTrue(data["learning_candidates_proposal_only"])
        self.assertTrue(data["dashboard_interactivity_read_only"])
        self.assertTrue(data["cli_learning_local_only"])

    def test_documentation_boundary_phrases(self) -> None:
        text = read_text(MATRIX_DOC).lower()
        for phrase in (
            "local and deterministic",
            "no runtime activation",
            "deterministic runtime remains authoritative",
            "semantic context remains reviewer-assist only",
            "dashboard interactivity remains read-only",
            "cli learning commands are local and actor-gated",
            "no parser/scoring/decision/recommendation behavior change",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_no_unsafe_dependencies(self) -> None:
        source = read_text(SCRIPT_PATH)
        source_lower = source.lower()
        tree = ast.parse(source, filename=str(SCRIPT_PATH))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        for module_name in imported_modules:
            self.assertFalse(module_name == "oracledb" or module_name.startswith("oracledb."))
            self.assertFalse(module_name == "requests" or module_name.startswith("requests."))
            self.assertFalse(module_name == "socket" or module_name.startswith("socket."))
            self.assertFalse(module_name == "oci" or module_name.startswith("oci."))

        for forbidden in (
            "socket.",
            "create_connection",
            "urlopen",
            "requests.",
            "oracledb.",
            "load_config_from_env",
            "oracle_agent_memory_adapter",
            "semantic_recall_service",
        ):
            self.assertNotIn(forbidden, source_lower)

    def test_existing_validation_scripts_are_referenced_safely(self) -> None:
        _, data = self.run_json_validation()
        groups = data["validation_groups"]
        dashboard_group = next(
            group for group in groups if group["name"] == "dashboard_interactivity"  # type: ignore[index]
        )

        if (ROOT / "scripts" / "run_phase7h_dashboard_validation.py").is_file():
            self.assertTrue(dashboard_group["invoked"])  # type: ignore[index]
            self.assertEqual(
                dashboard_group["runner"],  # type: ignore[index]
                "scripts/run_phase7h_dashboard_validation.py",
            )

        self.assertFalse(data["phase6_validation_included"])

    @classmethod
    def run_json_validation(
        cls,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        if cls._json_completed is None:
            cls._json_completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--json"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            cls._json_data = json.loads(cls._json_completed.stdout)
        assert cls._json_data is not None
        return cls._json_completed, cls._json_data


if __name__ == "__main__":
    unittest.main()
