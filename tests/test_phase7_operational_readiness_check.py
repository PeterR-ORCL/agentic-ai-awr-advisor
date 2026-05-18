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

    def test_db_live_evidence_satisfies_requirement_when_not_skipped(self) -> None:
        module = readiness_module()
        flags = {flag: "1" for flag in module.DB_FLAGS}

        def fake_run_command(spec, *, env_update=None):
            del env_update
            self.assertEqual("db_persistence_validation", spec.id)
            return {
                "status": "passed",
                "reason": "command completed successfully",
                "returncode": 0,
                "command": "python -m unittest db",
                "stdout_tail": "",
                "stderr_tail": "Ran 8 tests in 1.0s\n\nOK",
            }

        with mock.patch.dict(os.environ, flags, clear=True):
            with mock.patch.object(module, "run_command", side_effect=fake_run_command):
                result = module.evaluate_db_requirement(
                    SimpleNamespace(include_db=True, final_certification=True)
                )

        self.assertEqual("satisfied", result["status"])

    def test_db_live_evidence_blocks_when_unittest_skipped(self) -> None:
        module = readiness_module()
        flags = {flag: "1" for flag in module.DB_FLAGS}

        def fake_run_command(spec, *, env_update=None):
            del env_update
            self.assertEqual("db_persistence_validation", spec.id)
            return {
                "status": "passed",
                "reason": "command completed successfully",
                "returncode": 0,
                "command": "python -m unittest db",
                "stdout_tail": "",
                "stderr_tail": "Ran 8 tests in 1.0s\n\nOK (skipped=1)",
            }

        with mock.patch.dict(os.environ, flags, clear=True):
            with mock.patch.object(module, "run_command", side_effect=fake_run_command):
                result = module.evaluate_db_requirement(
                    SimpleNamespace(include_db=True, final_certification=True)
                )

        self.assertEqual("blocked", result["status"])
        self.assertIn("skipped", result["reason"])

    def test_object_storage_live_evidence_satisfies_requirement_when_not_skipped(self) -> None:
        module = readiness_module()
        env = {
            "OCI_NAMESPACE": "configured",
            "OCI_BUCKET_NAME": "configured",
            "OCI_OBJECT_NAME": "configured",
            "OCI_REGION": "configured",
        }

        def fake_run_command(spec, *, env_update=None):
            self.assertEqual("object_storage_live_validation", spec.id)
            self.assertEqual({"AWR_PHASE7CD_OBJECT_STORAGE_TEST": "1"}, env_update)
            return {
                "status": "passed",
                "reason": "command completed successfully",
                "returncode": 0,
                "command": "python -m unittest object-storage",
                "stdout_tail": "",
                "stderr_tail": "Ran 1 test in 1.0s\n\nOK",
            }

        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(module, "run_command", side_effect=fake_run_command):
                result = module.evaluate_object_storage_requirement(
                    SimpleNamespace(include_object_storage=True, final_certification=True)
                )

        self.assertEqual("satisfied", result["status"])

    def test_object_storage_live_evidence_blocks_when_unittest_skipped(self) -> None:
        module = readiness_module()
        env = {
            "OCI_NAMESPACE": "configured",
            "OCI_BUCKET_NAME": "configured",
            "OCI_OBJECT_NAME": "configured",
            "OCI_REGION": "configured",
        }

        def fake_run_command(spec, *, env_update=None):
            self.assertEqual("object_storage_live_validation", spec.id)
            self.assertEqual({"AWR_PHASE7CD_OBJECT_STORAGE_TEST": "1"}, env_update)
            return {
                "status": "passed",
                "reason": "command completed successfully",
                "returncode": 0,
                "command": "python -m unittest object-storage",
                "stdout_tail": "",
                "stderr_tail": "Ran 1 test in 1.0s\n\nOK (skipped=1)",
            }

        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(module, "run_command", side_effect=fake_run_command):
                result = module.evaluate_object_storage_requirement(
                    SimpleNamespace(include_object_storage=True, final_certification=True)
                )

        self.assertEqual("blocked", result["status"])
        self.assertIn("skipped", result["reason"])

    def test_7cj_release_documentation_is_recognized(self) -> None:
        payload = self.default_payload
        requirements = {req["id"]: req for req in payload["requirements"]}
        pending = {req["id"]: req for req in payload["pending_checks"]}

        self.assertEqual(
            "satisfied",
            requirements["final_release_documentation_pending"]["status"],
        )
        self.assertNotIn("final_release_documentation_pending", pending)
        self.assertIn("final_certification_tag_pending", pending)
        self.assertIs(payload["phase7_operational_ready"], False)

    def test_known_screen2_blocker_is_not_reopened_by_narrowed_7cm_scope(self) -> None:
        payload = self.default_payload
        blockers = {blocker["id"]: blocker for blocker in payload["known_blockers"]}
        self.assertNotIn("SCREEN2_BROAD_VALIDATOR_FAILURE", blockers)

        requirements = {req["id"]: req for req in payload["requirements"]}
        self.assertIn(
            requirements["screen2_operational_wiring"]["status"],
            {"skipped", "pending"},
        )
        self.assertEqual(
            "pending",
            requirements["screen2_diagnostic_review_runtime_workflow"]["status"],
        )
        self.assertIs(payload["phase7_operational_ready"], False)

    def test_index_source_selection_can_pass_while_broader_dashboard_runtime_remains_blocked(self) -> None:
        module = readiness_module()

        def fake_run_command(spec, *, env_update=None):
            del env_update
            self.assertEqual("index_source_selection_runtime_workflow", spec.id)
            return {
                "status": "passed",
                "reason": "command completed successfully",
                "returncode": 0,
                "command": "python scripts/run_phase7_dashboard_runtime_interaction_validation.py --json",
                "stdout_tail": json.dumps(
                    {
                        "index_source_selection_ready": True,
                        "dashboard_runtime_interaction_ready": True,
                        "blocker_active": False,
                    }
                ),
                "stderr_tail": "",
            }

        with mock.patch.object(module, "run_command", side_effect=fake_run_command):
            index_requirement = module.evaluate_index_source_selection_runtime_requirement()

        requirements = {
            req["id"]: req
            for req in [
                index_requirement,
                module.evaluate_dashboard_runtime_interaction_requirement(),
                *module.evaluate_deferred_dashboard_runtime_workflow_requirements(),
            ]
        }
        blockers = {
            blocker["id"]: blocker
            for blocker in module.build_known_blockers(list(requirements.values()))
        }
        self.assertIn("DASHBOARD_RUNTIME_INTERACTION_NOT_WIRED", blockers)
        self.assertIn("DASHBOARD_SELECTION_WORKFLOW_UNCLEAR", blockers)
        self.assertEqual(
            "satisfied",
            requirements["index_source_selection_runtime_workflow"]["status"],
        )
        self.assertEqual(
            "pending",
            requirements["dashboard_runtime_interaction_wiring"]["status"],
        )
        self.assertEqual(
            "pending",
            requirements["screen1_parser_governance_runtime_workflow"]["status"],
        )

    def test_index_source_selection_blocker_is_active_when_validator_fails(self) -> None:
        module = readiness_module()

        def fake_run_command(spec, *, env_update=None):
            del env_update
            self.assertEqual("index_source_selection_runtime_workflow", spec.id)
            return {
                "status": "failed",
                "reason": "command failed",
                "returncode": 1,
                "command": "python scripts/run_phase7_dashboard_runtime_interaction_validation.py --json",
                "stdout_tail": json.dumps(
                    {
                        "index_source_selection_ready": False,
                        "blocker_active": True,
                    }
                ),
                "stderr_tail": "",
            }

        with mock.patch.object(module, "run_command", side_effect=fake_run_command):
            requirement = module.evaluate_index_source_selection_runtime_requirement()

        blockers = {
            blocker["id"]: blocker
            for blocker in module.build_known_blockers([requirement])
        }
        self.assertIn("DASHBOARD_RUNTIME_INTERACTION_NOT_WIRED", blockers)
        self.assertEqual("blocked", requirement["status"])

    def test_screen_operational_validators_are_deferred_after_narrowed_7cm(self) -> None:
        module = readiness_module()

        with mock.patch.object(module, "run_command") as run_command:
            requirements = module.evaluate_screen_and_operational_wiring(
                SimpleNamespace(final_certification=True)
            )
            executed_ids = {call.args[0].id for call in run_command.call_args_list}
            self.assertNotIn("screen1_operational_wiring", executed_ids)
            self.assertNotIn("screen2_operational_wiring", executed_ids)
            self.assertNotIn("screen3_active_backend_execution", executed_ids)
            self.assertNotIn("screen4_operational_wiring", executed_ids)
            self.assertNotIn("screen5_operational_wiring", executed_ids)
            self.assertNotIn("screen6_operational_wiring", executed_ids)

        blockers = {blocker["id"]: blocker for blocker in module.build_known_blockers(requirements)}
        requirements_by_id = {req["id"]: req for req in requirements}
        self.assertNotIn("SCREEN2_BROAD_VALIDATOR_FAILURE", blockers)
        self.assertEqual("pending", requirements_by_id["screen2_operational_wiring"]["status"])
        self.assertEqual("pending", requirements_by_id["screen1_operational_wiring"]["status"])

    def test_list_requirements_does_not_execute_live_checks(self) -> None:
        self.assertEqual(0, self.list_result.returncode, self.list_result.stderr)
        stdout = self.list_result.stdout
        self.assertIn("db_persistence_validation", stdout)
        self.assertIn("object_storage_live_validation", stdout)
        self.assertIn("index_source_selection_runtime_workflow", stdout)
        self.assertIn("dashboard_runtime_interaction_wiring", stdout)
        self.assertIn("screen1_parser_governance_runtime_workflow", stdout)
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
