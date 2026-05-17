"""Tests for the Phase 7CI operational readiness checker."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from importlib import util
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_operational_readiness_check.py"

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


def git_phase7_complete_tags() -> list[str]:
    completed = subprocess.run(
        ["git", "tag", "--list", "PHASE7_COMPLETE"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return [line for line in completed.stdout.splitlines() if line]


def readiness_module():
    spec = util.spec_from_file_location(
        "phase7_operational_readiness_check_test_module",
        SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {SCRIPT}")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Phase7OperationalReadinessCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tags_before = git_phase7_complete_tags()
        cls.default_result = cls.run_checker("--json", timeout=180)
        cls.final_result = cls.run_checker("--final-certification", "--json", timeout=360)
        cls.list_result = cls.run_checker("--list-requirements", timeout=60)
        cls.tags_after = git_phase7_complete_tags()

        cls.default_payload = json.loads(cls.default_result.stdout)
        cls.final_payload = json.loads(cls.final_result.stdout)

    @classmethod
    def run_checker(
        cls,
        *args: str,
        timeout: int = 240,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=clean_env(),
            timeout=timeout,
            shell=False,
        )

    def test_json_output_contract(self) -> None:
        self.assertEqual(0, self.default_result.returncode, self.default_result.stderr)
        payload = self.default_payload
        self.assertEqual("Phase 7", payload["phase"])
        self.assertEqual("7CI", payload["subphase"])
        self.assertEqual("Phase 7 Operational Readiness Check", payload["readiness_name"])
        self.assertIs(payload["phase7_complete"], False)
        self.assertIs(payload["phase8_started"], False)
        self.assertIs(payload["phase7_operational_ready"], False)
        self.assertIsInstance(payload["required_final_certification_checks"], list)
        self.assertIsInstance(payload["satisfied_checks"], list)
        self.assertIsInstance(payload["blocked_checks"], list)
        self.assertIsInstance(payload["skipped_checks"], list)
        self.assertIsInstance(payload["known_blockers"], list)

    def test_default_mode_is_safe_local_and_not_ready(self) -> None:
        payload = self.default_payload
        self.assertIs(payload["final_certification_mode"], False)
        self.assertIs(payload["safe_local_mode"], True)
        self.assertIs(payload["phase7_operational_ready"], False)

        skipped = {check["id"]: check for check in payload["skipped_checks"]}
        self.assertIn("db_persistence_validation", skipped)
        self.assertIn("object_storage_live_validation", skipped)
        self.assertIn("screen1_operational_wiring", skipped)

    def test_final_certification_blocks_on_live_requirements(self) -> None:
        self.assertEqual(0, self.final_result.returncode, self.final_result.stderr)
        payload = self.final_payload
        self.assertIs(payload["final_certification_mode"], True)
        self.assertIs(payload["safe_local_mode"], False)
        self.assertIs(payload["phase7_operational_ready"], False)

        blocked = {check["id"]: check for check in payload["blocked_checks"]}
        self.assertIn("db_persistence_validation", blocked)
        self.assertIn("object_storage_live_validation", blocked)
        self.assertNotIn("screen2_operational_wiring", blocked)
        self.assertIn("required for final certification", blocked["db_persistence_validation"]["reason"])
        self.assertIn("required for final certification", blocked["object_storage_live_validation"]["reason"])

    def test_known_screen2_blocker_is_resolved_when_broad_validator_passes(self) -> None:
        payload = self.default_payload
        blockers = {blocker["id"]: blocker for blocker in payload["known_blockers"]}
        self.assertNotIn("SCREEN2_BROAD_VALIDATOR_FAILURE", blockers)

        requirements = {req["id"]: req for req in payload["requirements"]}
        self.assertEqual("satisfied", requirements["screen2_operational_wiring"]["status"])
        self.assertIs(payload["phase7_operational_ready"], False)

    def test_screen2_blocker_is_active_when_broad_validator_fails(self) -> None:
        module = readiness_module()

        def fake_run_command(spec, *, env_update=None):
            del env_update
            if spec.id == "screen2_operational_wiring":
                return {
                    "status": "failed",
                    "reason": "command failed",
                    "returncode": 1,
                    "command": "python scripts/run_phase7_screen2_review_validation.py --json",
                    "stdout_tail": "",
                    "stderr_tail": "",
                }
            raise AssertionError(f"unexpected command for {spec.id}")

        with mock.patch.object(module, "run_command", side_effect=fake_run_command):
            requirements = module.evaluate_screen_and_operational_wiring(
                SimpleNamespace(final_certification=False)
            )

        blockers = {blocker["id"]: blocker for blocker in module.build_known_blockers(requirements)}
        requirements_by_id = {req["id"]: req for req in requirements}
        self.assertIn("SCREEN2_BROAD_VALIDATOR_FAILURE", blockers)
        self.assertEqual("blocked", requirements_by_id["screen2_operational_wiring"]["status"])

    def test_list_requirements_does_not_execute_live_checks(self) -> None:
        self.assertEqual(0, self.list_result.returncode, self.list_result.stderr)
        stdout = self.list_result.stdout
        self.assertIn("db_persistence_validation", stdout)
        self.assertIn("object_storage_live_validation", stdout)
        self.assertIn("screen2_operational_wiring", stdout)
        self.assertIn("required_for_final_certification=true", stdout)
        self.assertIn("List mode does not execute checks", stdout)
        self.assertNotIn("phase7_operational_ready", stdout)

    def test_required_invariants_are_reported(self) -> None:
        invariants = self.default_payload["invariants"]
        self.assertIs(invariants["deterministic_runtime_authoritative"], True)
        self.assertIs(invariants["phase4i_contract_protected"], True)
        self.assertIs(invariants["runtime_influence_denied_by_default"], True)
        self.assertIs(invariants["phase8_behavior_implemented"], False)
        self.assertIs(invariants["screen_wiring_required_for_final_certification"], True)
        self.assertIs(invariants["db_validation_required_for_final_certification"], True)
        self.assertIs(invariants["object_storage_validation_required_for_final_certification"], True)

    def test_checker_does_not_create_phase7_complete_tag(self) -> None:
        self.assertEqual(self.tags_before, self.tags_after)
        self.assertIs(self.default_payload["phase7_complete"], False)
        self.assertIs(self.final_payload["phase7_complete"], False)
        self.assertIs(self.default_payload["invariants"]["phase7_complete"], False)


if __name__ == "__main__":
    unittest.main()
