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
SCRIPT_PATH = ROOT / "scripts" / "run_phase7_materialization_validation.py"
MATRIX_DOC = ROOT / "docs" / "architecture" / "phase7_materialization_validation_matrix.md"

REQUIRED_GROUPS = (
    "materialization_boundary",
    "approved_candidate_materialization",
    "adaptive_scoring_review",
    "recommendation_rule_evolution",
    "parser_mapping_evolution",
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
    "runtime_influence_granted",
    "runtime_active",
    "candidate_approval_is_not_activation",
    "materialization_is_not_activation",
    "parser_evolution_proposal_only",
    "scoring_review_proposal_only",
    "recommendation_evolution_proposal_only",
    "deterministic_runtime_remains_authoritative",
    "network_dependency",
    "database_dependency",
    "oracle_agent_memory_dependency",
)

REQUIRED_MATRIX_PHRASES = (
    "candidate approval does not equal runtime activation",
    "candidate approval is not activation",
    "materialization is separate from approval",
    "materialization is not activation",
    "parser/scoring/recommendation changes are proposal-only",
    "parser evolution is first-class and protected",
    "no automatic parser mutation",
    "no automatic scoring mutation",
    "no automatic recommendation mutation",
    "runtime_influence_granted=false",
    "runtime_active=false",
    "semantic context is not implementation truth",
    "dashboard and cli are not mutation paths",
    "phase 4i contract remains protected",
    "deterministic runtime remains authoritative",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def validation_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


class Phase7MaterializationValidationTests(unittest.TestCase):
    _json_completed: subprocess.CompletedProcess[str] | None = None
    _json_data: dict[str, object] | None = None

    def test_validation_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT_PATH.is_file(), SCRIPT_PATH)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT_PATH),
                cfile=str(Path(tempdir) / "run_phase7_materialization_validation.pyc"),
                doraise=True,
            )

    def test_validation_script_normal_output_returns_success(self) -> None:
        completed = subprocess.run(
            (sys.executable, str(SCRIPT_PATH)),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=validation_env(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("Phase 7 materialization validation passed.", completed.stdout)

    def test_validation_script_json_returns_valid_json(self) -> None:
        completed, payload = self.run_json_validation()

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIs(payload["success"], True)
        self.assertEqual(payload["phase"], "Phase 7M-7R")
        self.assertEqual(payload["command"], "run_phase7_materialization_validation")

    def test_json_contains_required_fields(self) -> None:
        _, payload = self.run_json_validation()
        for field in REQUIRED_JSON_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, payload)

    def test_required_validation_groups_are_present(self) -> None:
        _, payload = self.run_json_validation()
        groups = payload["validation_groups"]
        self.assertIsInstance(groups, list)
        names = {group["name"] for group in groups}  # type: ignore[index]
        for group_name in REQUIRED_GROUPS:
            with self.subTest(group_name=group_name):
                self.assertIn(group_name, names)

    def test_runtime_influence_granted_is_false(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["runtime_influence_granted"], False)

    def test_runtime_active_is_false(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["runtime_active"], False)

    def test_candidate_approval_is_not_activation(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["candidate_approval_is_not_activation"], True)

    def test_materialization_is_not_activation(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["materialization_is_not_activation"], True)

    def test_proposal_only_fields_are_true(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["parser_evolution_proposal_only"], True)
        self.assertIs(payload["scoring_review_proposal_only"], True)
        self.assertIs(payload["recommendation_evolution_proposal_only"], True)

    def test_no_unsafe_imports_in_validation_script(self) -> None:
        source = read_text(SCRIPT_PATH)
        tree = ast.parse(source, filename=str(SCRIPT_PATH))
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

        source_lower = source.lower()
        for forbidden_text in (
            "shell=True",
            "requests.",
            "urlopen",
            "create_connection",
            "oracledb.",
            "oci.config",
            "load_config_from_env",
            "semantic_recall_service",
        ):
            with self.subTest(forbidden_text=forbidden_text):
                self.assertNotIn(forbidden_text.lower(), source_lower)

    def test_documentation_validation_matrix_contains_required_phrases(self) -> None:
        self.assertTrue(MATRIX_DOC.is_file(), MATRIX_DOC)
        text = read_text(MATRIX_DOC).lower()
        for phrase in REQUIRED_MATRIX_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    @classmethod
    def run_json_validation(
        cls,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        if cls._json_completed is None:
            cls._json_completed = subprocess.run(
                (sys.executable, str(SCRIPT_PATH), "--json"),
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=validation_env(),
            )
            cls._json_data = json.loads(cls._json_completed.stdout)
        assert cls._json_data is not None
        return cls._json_completed, cls._json_data


if __name__ == "__main__":
    unittest.main()
