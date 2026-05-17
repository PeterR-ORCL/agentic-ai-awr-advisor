"""Phase 7BZ tests for runtime materialization validation."""

from __future__ import annotations

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
SCRIPT = ROOT / "scripts" / "run_phase7_runtime_materialization_validation.py"
DOCS = ROOT / "docs" / "architecture"

REQUIRED_GROUPS = (
    "governed_workflow_persistence",
    "status_transition_execution",
    "parser_runtime_update",
    "scoring_runtime_activation",
    "recommendation_runtime_activation",
    "ml_runtime_eligibility",
    "import_isolation",
    "runtime_safety",
    "documentation",
)

REQUIRED_DOCS = (
    "phase7_runtime_materialization_validation_matrix.md",
    "phase7_runtime_materialization_readiness.md",
    "phase7_runtime_materialization_release_certification.md",
    "phase7_runtime_materialization_operational_checklist.md",
)


def load_validation_module():
    spec = importlib.util.spec_from_file_location("phase7bz_validation", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load validation script module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (sys.executable, str(SCRIPT), *args),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


class Phase7RuntimeMaterializationValidationTests(unittest.TestCase):
    def test_validation_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT),
                cfile=str(Path(tempdir) / "validation.pyc"),
                doraise=True,
            )

    def test_text_output_passes(self) -> None:
        completed = run_script()
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn(
            "Phase 7 runtime materialization validation passed.",
            completed.stdout,
        )

    def test_json_output_valid(self) -> None:
        completed = run_script("--json")
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["phase"], "Phase 7BU-7BZ")
        self.assertEqual(
            payload["command"],
            "run_phase7_runtime_materialization_validation",
        )
        self.assertIs(payload["success"], True)

    def test_required_validation_groups_present(self) -> None:
        module = load_validation_module()
        group_names = {group.name for group in module.UNITTEST_GROUPS}
        group_names.update({"import_isolation", "runtime_safety", "documentation"})
        for group_name in REQUIRED_GROUPS:
            with self.subTest(group_name=group_name):
                self.assertIn(group_name, group_names)

    def test_runtime_materialization_ready_true(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["runtime_materialization_ready"], True)

    def test_db_persistence_performed_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["db_persistence_performed"], False)

    def test_status_transition_performed_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["status_transition_performed"], False)

    def test_parser_update_applied_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["parser_update_applied"], False)

    def test_scoring_config_applied_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["scoring_config_applied"], False)

    def test_recommendation_rule_applied_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["recommendation_rule_applied"], False)

    def test_model_deployed_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["model_deployed"], False)
        self.assertIs(payload["model_loaded"], False)
        self.assertIs(payload["model_saved"], False)

    def test_runtime_eligibility_granted_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["runtime_eligibility_granted"], False)

    def test_runtime_active_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["runtime_active"], False)

    def test_phase4i_mutated_false(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["phase4i_mutated"], False)

    def test_deterministic_fallback_required_true(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["deterministic_fallback_required"], True)

    def test_deterministic_runtime_remains_authoritative_true(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["deterministic_runtime_remains_authoritative"], True)

    def test_docs_exist(self) -> None:
        for doc in REQUIRED_DOCS:
            with self.subTest(doc=doc):
                self.assertTrue((DOCS / doc).is_file(), doc)


if __name__ == "__main__":
    unittest.main()
