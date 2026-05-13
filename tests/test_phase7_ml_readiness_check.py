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
READINESS_SCRIPT = ROOT / "scripts" / "run_phase7_ml_readiness_check.py"
SELFTEST = os.environ.get("PHASE7_ML_READINESS_SELFTEST") == "1"

READINESS_DOC = DOCS / "phase7_ml_readiness.md"
RELEASE_CERTIFICATION_DOC = DOCS / "phase7_ml_release_certification.md"
OPERATIONAL_CHECKLIST_DOC = DOCS / "phase7_ml_operational_checklist.md"

REQUIRED_CATEGORIES = (
    "ml_boundary",
    "feature_label_dataset",
    "trend_aware_scoring",
    "shadow_ml_model_interface",
    "ml_training_backtesting",
    "ml_explainability",
    "ml_model_registry",
    "runtime_isolation",
    "documentation_complete",
    "materialization_regression",
    "phase7_regression",
    "phase6_regression",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def validation_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def load_readiness_module():
    spec = importlib.util.spec_from_file_location(
        "phase7_ml_readiness_check",
        READINESS_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise AssertionError("could not load ML readiness script module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Phase7MLReadinessCheckTests(unittest.TestCase):
    _json_completed: subprocess.CompletedProcess[str] | None = None
    _json_data: dict[str, object] | None = None

    def test_ml_readiness_script_exists_and_compiles(self) -> None:
        self.assertTrue(READINESS_SCRIPT.is_file(), READINESS_SCRIPT)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(READINESS_SCRIPT),
                cfile=str(Path(tempdir) / "run_phase7_ml_readiness_check.pyc"),
                doraise=True,
            )

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_ml_readiness_script_normal_output_returns_success(self) -> None:
        completed = subprocess.run(
            (sys.executable, str(READINESS_SCRIPT)),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=validation_env(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("Phase 7 ML readiness passed.", completed.stdout)
        self.assertIn("ml_ready=true", completed.stdout)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_ml_readiness_script_json_returns_valid_json(self) -> None:
        completed, payload = self.run_json_readiness()

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertEqual(payload["phase"], "Phase 7S-7Z")
        self.assertEqual(payload["command"], "run_phase7_ml_readiness_check")
        self.assertIs(payload["success"], True)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_json_contains_ml_ready_true(self) -> None:
        _, payload = self.run_json_readiness()
        self.assertIs(payload["ml_ready"], True)

    def test_required_readiness_categories_are_present(self) -> None:
        module = load_readiness_module()
        categories = set(module.READINESS_CATEGORY_KEYS)
        for category in REQUIRED_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(category, categories)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_json_readiness_categories_are_present(self) -> None:
        _, payload = self.run_json_readiness()
        categories = payload["readiness_categories"]
        self.assertIsInstance(categories, dict)
        for category in REQUIRED_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(category, categories)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_runtime_active_false(self) -> None:
        _, payload = self.run_json_readiness()
        self.assertIs(payload["runtime_active"], False)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_runtime_influence_false(self) -> None:
        _, payload = self.run_json_readiness()
        self.assertIs(payload["runtime_influence"], False)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_runtime_influence_granted_false(self) -> None:
        _, payload = self.run_json_readiness()
        self.assertIs(payload["runtime_influence_granted"], False)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_runtime_eligibility_granted_false(self) -> None:
        _, payload = self.run_json_readiness()
        self.assertIs(payload["runtime_eligibility_granted"], False)

    @unittest.skipIf(SELFTEST, "avoid recursive readiness checker subprocess calls")
    def test_deterministic_runtime_remains_authoritative_true(self) -> None:
        _, payload = self.run_json_readiness()
        self.assertIs(payload["deterministic_runtime_remains_authoritative"], True)

    def test_readiness_docs_exist(self) -> None:
        self.assertTrue(READINESS_DOC.is_file(), READINESS_DOC)

    def test_release_certification_docs_exist(self) -> None:
        self.assertTrue(RELEASE_CERTIFICATION_DOC.is_file(), RELEASE_CERTIFICATION_DOC)

    def test_operational_checklist_docs_exist(self) -> None:
        self.assertTrue(OPERATIONAL_CHECKLIST_DOC.is_file(), OPERATIONAL_CHECKLIST_DOC)

    def test_readme_links_new_ml_readiness_certification_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            ("Phase 7 ML Validation Matrix", "phase7_ml_validation_matrix.md"),
            ("Phase 7 ML Readiness", "phase7_ml_readiness.md"),
            ("Phase 7 ML Release Certification", "phase7_ml_release_certification.md"),
            ("Phase 7 ML Operational Checklist", "phase7_ml_operational_checklist.md"),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)

    def test_no_unsafe_imports_in_readiness_script(self) -> None:
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
        self.assertNotIn("requests.", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("create_connection", source)

    @classmethod
    def run_json_readiness(
        cls,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        if cls._json_completed is None:
            cls._json_completed = subprocess.run(
                (sys.executable, str(READINESS_SCRIPT), "--json"),
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
