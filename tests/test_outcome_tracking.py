from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from scripts import record_outcome as record_outcome_cli
from src.memory import memory_orchestrator


class OutcomeTrackingTests(unittest.TestCase):
    def test_memory_disabled_does_not_call_insert(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "false"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_action_outcome_history",
            ) as insert_outcome:
                result = memory_orchestrator.record_outcome(
                    run_history_id=1,
                    action_history_id=1,
                    outcome_status="SUCCESS",
                    outcome_summary="Reduced commit latency after tuning.",
                )

        insert_outcome.assert_not_called()
        self.assertFalse(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["skipped"], ["memory_disabled"])

    def test_missing_run_history_id_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.record_outcome(
                run_history_id=0,
                action_history_id=1,
                outcome_status="SUCCESS",
                outcome_summary="Reduced commit latency after tuning.",
            )

        self.assertFalse(result["success"])
        self.assertIn("run_history_id is required", result["errors"][0])

    def test_missing_action_history_id_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.record_outcome(
                run_history_id=1,
                action_history_id=0,
                outcome_status="SUCCESS",
                outcome_summary="Reduced commit latency after tuning.",
            )

        self.assertFalse(result["success"])
        self.assertIn("action_history_id is required", result["errors"][0])

    def test_invalid_outcome_status_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.record_outcome(
                run_history_id=1,
                action_history_id=1,
                outcome_status="IMPROVED",
                outcome_summary="Reduced commit latency after tuning.",
            )

        self.assertFalse(result["success"])
        self.assertIn("outcome_status must be one of", result["errors"][0])

    def test_successful_record_outcome_returns_outcome_id(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_action_outcome_history",
                return_value=77,
            ) as insert_outcome:
                result = memory_orchestrator.record_outcome(
                    run_history_id=1,
                    action_history_id=2,
                    outcome_status="partial",
                    outcome_summary="Some waits improved, but commit latency remains.",
                    before_metrics={"log_file_sync_ms": 18},
                    after_metrics={"log_file_sync_ms": 12},
                    impact_score=0.35,
                    recorded_by="tester",
                    notes={"ticket": "INC123"},
                )

        self.assertTrue(result["success"])
        self.assertEqual(result["outcome_id"], 77)
        self.assertEqual(result["outcome_status"], "PARTIAL")
        insert_outcome.assert_called_once()
        call_kwargs = insert_outcome.call_args.kwargs
        self.assertEqual(call_kwargs["run_history_id"], 1)
        self.assertEqual(call_kwargs["action_history_id"], 2)
        self.assertEqual(call_kwargs["before_metrics"], {"log_file_sync_ms": 18})

    def test_insert_exception_returns_failure_without_raising(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_action_outcome_history",
                side_effect=RuntimeError("insert failed"),
            ):
                result = memory_orchestrator.record_outcome(
                    run_history_id=1,
                    action_history_id=1,
                    outcome_status="SUCCESS",
                    outcome_summary="Reduced commit latency after tuning.",
                )

        self.assertFalse(result["success"])
        self.assertIn("RuntimeError: insert failed", result["errors"])

    def test_cli_argument_parsing_handles_required_fields(self) -> None:
        parser = record_outcome_cli.build_parser()
        args = parser.parse_args(
            [
                "--run-history-id",
                "1",
                "--action-history-id",
                "2",
                "--outcome-status",
                "SUCCESS",
                "--outcome-summary",
                "Reduced commit latency after tuning.",
            ]
        )

        self.assertEqual(args.run_history_id, 1)
        self.assertEqual(args.action_history_id, 2)
        self.assertEqual(args.outcome_status, "SUCCESS")


if __name__ == "__main__":
    unittest.main()
