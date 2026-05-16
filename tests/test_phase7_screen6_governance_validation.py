"""Tests for Phase 7BK-7BP Screen 6 governance validation."""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_screen6_governance_validation.py"
DOCS = ROOT / "docs" / "architecture"

REQUIRED_GROUPS = (
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
    "import_isolation",
    "runtime_safety",
    "documentation",
)

REQUIRED_DOCS = (
    "phase7_screen6_governance_validation_matrix.md",
    "phase7_screen6_governance_readiness.md",
    "phase7_screen6_governance_release_certification.md",
    "phase7_screen6_governance_operational_checklist.md",
)


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (sys.executable, str(SCRIPT), *args),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


class Phase7Screen6GovernanceValidationTests(unittest.TestCase):
    _json_payload: dict[str, object] | None = None
    _text_result: subprocess.CompletedProcess[str] | None = None

    def test_validation_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT),
                cfile=str(Path(tempdir) / "run_phase7_screen6_governance_validation.pyc"),
                doraise=True,
            )

    def test_text_output_passes(self) -> None:
        completed = self.text_result()
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("Phase 7 Screen 6 governance validation passed.", completed.stdout)

    def test_json_output_valid(self) -> None:
        payload = self.json_payload()
        self.assertEqual(payload["phase"], "Phase 7BK-7BP")
        self.assertEqual(payload["command"], "run_phase7_screen6_governance_validation")
        self.assertIs(payload["success"], True)
        self.assertIs(payload["screen6_governance_ready"], True)

    def test_required_validation_groups_present(self) -> None:
        payload = self.json_payload()
        groups = {group["name"] for group in payload["validation_groups"]}  # type: ignore[index]
        for group in REQUIRED_GROUPS:
            with self.subTest(group=group):
                self.assertIn(group, groups)

    def test_preview_only_flags(self) -> None:
        payload = self.json_payload()
        self.assertIs(payload["candidate_review_preview_only"], True)
        self.assertIs(payload["materialization_review_preview_only"], True)
        self.assertIs(payload["model_registry_review_preview_only"], True)
        self.assertIs(payload["runtime_gate_review_preview_only"], True)

    def test_runtime_safety_flags(self) -> None:
        payload = self.json_payload()
        self.assertIs(payload["governance_action_performed"], False)
        self.assertIs(payload["candidate_status_changed"], False)
        self.assertIs(payload["materialization_status_changed"], False)
        self.assertIs(payload["model_registry_status_changed"], False)
        self.assertIs(payload["runtime_gate_state_changed"], False)
        self.assertIs(payload["shadow_eligibility_changed"], False)
        self.assertIs(payload["runtime_review_requested"], False)
        self.assertIs(payload["runtime_eligibility_granted"], False)
        self.assertIs(payload["runtime_active"], False)
        self.assertIs(payload["rollback_execution"], False)
        self.assertIs(payload["phase4i_mutated"], False)
        self.assertIs(payload["deterministic_runtime_remains_authoritative"], True)
        self.assertIs(payload["phase8_implemented"], False)

    def test_docs_exist(self) -> None:
        for doc_name in REQUIRED_DOCS:
            with self.subTest(doc_name=doc_name):
                self.assertTrue((DOCS / doc_name).is_file())

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
