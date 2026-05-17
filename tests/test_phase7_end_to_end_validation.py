"""Tests for the Phase 7CH end-to-end validation harness."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from importlib import util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_end_to_end_validation.py"

LIVE_ENV_KEYS = (
    "AWR_PHASE7CA_DB_TEST",
    "AWR_PHASE7CB_DB_TEST",
    "AWR_PHASE7CC_DB_TEST",
    "AWR_PHASE7CD_DB_TEST",
    "AWR_PHASE7CE_DB_TEST",
    "AWR_PHASE7CD_OBJECT_STORAGE_TEST",
    "OCI_NAMESPACE",
    "OCI_OBJECT_STORAGE_NAMESPACE",
    "OCI_BUCKET_NAME",
    "OCI_OBJECT_STORAGE_BUCKET",
    "OCI_OBJECT_NAME",
    "OCI_OBJECT_STORAGE_OBJECT_NAME",
    "OCI_REGION",
)


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in LIVE_ENV_KEYS:
        env.pop(key, None)
    return env


def harness_module():
    spec = util.spec_from_file_location(
        "phase7_end_to_end_validation_test_module",
        SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {SCRIPT}")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Phase7EndToEndValidationHarnessTests(unittest.TestCase):
    def run_harness(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        timeout: int = 240,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=env or clean_env(),
            timeout=timeout,
            shell=False,
        )

    def test_json_output_contract(self) -> None:
        completed = self.run_harness("--fast", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)

        payload = json.loads(completed.stdout)
        self.assertEqual("Phase 7", payload["phase"])
        self.assertEqual("7CH", payload["subphase"])
        self.assertIs(payload["phase7_complete"], False)
        self.assertIs(payload["phase8_started"], False)
        self.assertIsInstance(payload["checks"], list)

        invariants = payload["invariants"]
        self.assertIs(invariants["phase7_complete"], False)
        self.assertIs(invariants["phase8_started"], False)
        self.assertIs(invariants["deterministic_runtime_authoritative"], True)
        self.assertIs(invariants["phase4i_contract_protected"], True)
        self.assertIs(invariants["uncontrolled_runtime_mutation_allowed"], False)
        self.assertIs(invariants["adaptive_runtime_default_active"], False)
        self.assertIs(invariants["phase8_behavior_implemented"], False)

        boundary_checks = [
            check
            for check in payload["checks"]
            if check["name"] == "phase7cg_boundary_document"
        ]
        self.assertEqual(1, len(boundary_checks))
        self.assertEqual("passed", boundary_checks[0]["status"])

    def test_list_checks_does_not_execute_checks(self) -> None:
        completed = self.run_harness("--list-checks")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Phase 7CH known checks:", completed.stdout)
        self.assertIn("phase7cg_boundary_document", completed.stdout)
        self.assertIn("phase7_db_backed_validation", completed.stdout)
        self.assertNotIn("overall_status", completed.stdout)
        self.assertNotIn("command completed successfully", completed.stdout)

    def test_default_mode_does_not_require_live_env(self) -> None:
        completed = self.run_harness("--json", timeout=360)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("passed", payload["overall_status"])
        self.assertIs(payload["phase7_complete"], False)
        self.assertIs(payload["phase8_started"], False)

        skipped = {check["name"]: check for check in payload["skipped_checks"]}
        self.assertIn("phase7_db_backed_validation", skipped)
        self.assertIn("phase7_object_storage_live_validation", skipped)

    def test_strict_live_missing_db_env_fails(self) -> None:
        completed = self.run_harness(
            "--fast",
            "--include-db",
            "--strict-live",
            "--json",
        )
        self.assertNotEqual(0, completed.returncode)
        payload = json.loads(completed.stdout)
        self.assertEqual("failed", payload["overall_status"])
        failures = {failure["name"]: failure for failure in payload["failures"]}
        self.assertIn("phase7_db_backed_validation", failures)
        self.assertIn("AWR_PHASE7CA_DB_TEST", failures["phase7_db_backed_validation"]["reason"])

    def test_strict_live_missing_object_storage_env_fails(self) -> None:
        completed = self.run_harness(
            "--fast",
            "--include-object-storage",
            "--strict-live",
            "--json",
        )
        self.assertNotEqual(0, completed.returncode)
        payload = json.loads(completed.stdout)
        self.assertEqual("failed", payload["overall_status"])
        failures = {failure["name"]: failure for failure in payload["failures"]}
        self.assertIn("phase7_object_storage_live_validation", failures)
        self.assertIn("OCI_NAMESPACE", failures["phase7_object_storage_live_validation"]["reason"])

    def test_live_unittest_skip_output_is_not_successful_evidence(self) -> None:
        module = harness_module()
        self.assertFalse(module.command_output_reports_skips("", "Ran 1 test\n\nOK"))
        self.assertTrue(
            module.command_output_reports_skips(
                "",
                "Ran 1 test in 0.1s\n\nOK (skipped=1)",
            )
        )

    def test_harness_never_marks_phase7_complete(self) -> None:
        completed = self.run_harness("--fast", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIs(payload["phase7_complete"], False)
        self.assertIs(payload["invariants"]["phase7_complete"], False)


if __name__ == "__main__":
    unittest.main()
