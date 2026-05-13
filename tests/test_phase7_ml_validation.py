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
SCRIPT_PATH = ROOT / "scripts" / "run_phase7_ml_validation.py"
MATRIX_DOC = ROOT / "docs" / "architecture" / "phase7_ml_validation_matrix.md"

REQUIRED_GROUPS = (
    "ml_boundary",
    "feature_label_dataset",
    "trend_aware_scoring",
    "shadow_ml_model_interface",
    "ml_training_backtesting",
    "ml_explainability",
    "ml_model_registry",
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
    "ml_shadow_only",
    "dataset_is_not_model",
    "trend_aware_scoring_advisory_only",
    "shadow_ml_non_authoritative",
    "training_backtesting_evaluation_only",
    "explainability_not_runtime_truth",
    "model_registry_governance_only",
    "runtime_active",
    "runtime_influence",
    "runtime_influence_granted",
    "runtime_eligibility_granted",
    "deterministic_runtime_remains_authoritative",
    "network_dependency",
    "database_dependency",
    "oracle_agent_memory_dependency",
)

REQUIRED_MATRIX_PHRASES = (
    "ml remains shadow/advisory",
    "dataset is not a model",
    "training/backtesting is evaluation only",
    "explainability is not runtime truth",
    "model registry is governance metadata only",
    "no model is runtime active",
    "no runtime scoring changes are applied",
    "deterministic runtime remains authoritative",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def validation_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


class Phase7MLValidationTests(unittest.TestCase):
    _json_completed: subprocess.CompletedProcess[str] | None = None
    _json_data: dict[str, object] | None = None

    def test_ml_validation_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT_PATH.is_file(), SCRIPT_PATH)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT_PATH),
                cfile=str(Path(tempdir) / "run_phase7_ml_validation.pyc"),
                doraise=True,
            )

    def test_ml_validation_script_normal_output_returns_success(self) -> None:
        completed = subprocess.run(
            (sys.executable, str(SCRIPT_PATH)),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=validation_env(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("Phase 7 ML validation passed.", completed.stdout)

    def test_ml_validation_script_json_returns_valid_json(self) -> None:
        completed, payload = self.run_json_validation()

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIs(payload["success"], True)
        self.assertEqual(payload["phase"], "Phase 7S-7Z")
        self.assertEqual(payload["command"], "run_phase7_ml_validation")

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

    def test_runtime_active_is_false(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["runtime_active"], False)

    def test_runtime_influence_is_false(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["runtime_influence"], False)

    def test_runtime_influence_granted_is_false(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["runtime_influence_granted"], False)

    def test_runtime_eligibility_granted_is_false(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["runtime_eligibility_granted"], False)

    def test_ml_shadow_only_is_true(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["ml_shadow_only"], True)

    def test_dataset_is_not_model_is_true(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["dataset_is_not_model"], True)

    def test_model_registry_governance_only_is_true(self) -> None:
        _, payload = self.run_json_validation()
        self.assertIs(payload["model_registry_governance_only"], True)

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

        self.assertNotIn("shell=True", source)
        self.assertNotIn("requests.", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("create_connection", source)

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
