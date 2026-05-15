"""Tests for Phase 7AU-7AY Screen 1 workflow validation."""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_screen1_workflow_validation.py"
DOCS = ROOT / "docs" / "architecture"

REQUIRED_GROUPS = (
    "workflow_boundary",
    "source_intake",
    "parser_unknown_review",
    "parser_unknown_review_panel",
    "knowledge_artifact_review",
    "knowledge_artifact_review_panel",
    "screen1_governance_exploration_regression",
    "import_isolation",
    "runtime_safety",
    "documentation",
)

REQUIRED_DOCS = (
    "phase7_screen1_workflow_validation_matrix.md",
    "phase7_screen1_workflow_readiness.md",
    "phase7_screen1_workflow_release_certification.md",
    "phase7_screen1_workflow_operational_checklist.md",
)


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (sys.executable, str(SCRIPT), *args),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


class Phase7Screen1WorkflowValidationTests(unittest.TestCase):
    def test_validation_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT),
                cfile=str(Path(tempdir) / "run_phase7_screen1_workflow_validation.pyc"),
                doraise=True,
            )

    def test_text_output_passes(self) -> None:
        completed = run_script()
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("Phase 7 Screen 1 workflow validation passed.", completed.stdout)

    def test_json_output_valid(self) -> None:
        completed = run_script("--json")
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["phase"], "Phase 7AU-7AY")
        self.assertEqual(payload["command"], "run_phase7_screen1_workflow_validation")
        self.assertIs(payload["success"], True)
        self.assertIs(payload["screen1_workflow_ready"], True)

    def test_required_validation_groups_present(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        groups = {group["name"] for group in payload["validation_groups"]}
        for group in REQUIRED_GROUPS:
            with self.subTest(group=group):
                self.assertIn(group, groups)

    def test_required_json_safety_flags(self) -> None:
        payload = json.loads(run_script("--json").stdout)
        self.assertIs(payload["screen1_workflow_ready"], True)
        self.assertIs(payload["source_intake_performed"], False)
        self.assertIs(payload["local_file_read_performed"], False)
        self.assertIs(payload["object_storage_called"], False)
        self.assertIs(payload["db_lookup_performed"], False)
        self.assertIs(payload["parser_invoked"], False)
        self.assertIs(payload["run_analysis_called"], False)
        self.assertIs(payload["parser_unknown_classification_persisted"], False)
        self.assertIs(payload["parser_mapping_created"], False)
        self.assertIs(payload["parser_candidate_created"], False)
        self.assertIs(payload["parser_backlog_item_created"], False)
        self.assertIs(payload["artifact_approval_executed"], False)
        self.assertIs(payload["artifact_rejection_executed"], False)
        self.assertIs(payload["materialization_created"], False)
        self.assertIs(payload["parser_output_changed"], False)
        self.assertIs(payload["phase4i_mutated"], False)
        self.assertIs(payload["deterministic_runtime_remains_authoritative"], True)
        self.assertIs(payload["phase8_em_extract_implemented"], False)
        self.assertIs(payload["phase8_sizing_tco_implemented"], False)

    def test_docs_exist(self) -> None:
        for doc_name in REQUIRED_DOCS:
            with self.subTest(doc_name=doc_name):
                self.assertTrue((DOCS / doc_name).is_file())


if __name__ == "__main__":
    unittest.main()
