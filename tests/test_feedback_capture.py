from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from scripts import record_feedback as record_feedback_cli
from src.memory import memory_orchestrator


class FeedbackCaptureTests(unittest.TestCase):
    def test_memory_disabled_does_not_call_insert(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "false"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_feedback_history",
            ) as insert_feedback:
                result = memory_orchestrator.record_feedback(
                    run_history_id=1,
                    feedback_type="DIAGNOSIS_CORRECTNESS",
                    feedback_rating="POSITIVE",
                    feedback_summary="Advisor diagnosis matched DBA review.",
                )

        insert_feedback.assert_not_called()
        self.assertFalse(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["skipped"], ["memory_disabled"])

    def test_missing_run_history_id_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.record_feedback(
                run_history_id=0,
                feedback_type="DIAGNOSIS_CORRECTNESS",
                feedback_rating="POSITIVE",
                feedback_summary="Advisor diagnosis matched DBA review.",
            )

        self.assertFalse(result["success"])
        self.assertIn("run_history_id is required", result["errors"][0])

    def test_invalid_feedback_rating_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.record_feedback(
                run_history_id=1,
                feedback_type="DIAGNOSIS_CORRECTNESS",
                feedback_rating="GOOD",
                feedback_summary="Advisor diagnosis matched DBA review.",
            )

        self.assertFalse(result["success"])
        self.assertIn("feedback_rating must be one of", result["errors"][0])

    def test_missing_feedback_summary_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.record_feedback(
                run_history_id=1,
                feedback_type="DIAGNOSIS_CORRECTNESS",
                feedback_rating="POSITIVE",
                feedback_summary="",
            )

        self.assertFalse(result["success"])
        self.assertIn("feedback_summary is required", result["errors"])

    def test_successful_record_feedback_returns_feedback_id(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_feedback_history",
                return_value=88,
            ) as insert_feedback:
                result = memory_orchestrator.record_feedback(
                    run_history_id=1,
                    recommendation_history_id=2,
                    action_history_id=3,
                    action_outcome_id=4,
                    feedback_type="diagnosis correctness",
                    feedback_rating="positive",
                    feedback_summary="Advisor diagnosis matched DBA review.",
                    feedback_detail="CPU and User I/O were highlighted.",
                    feedback_source="dba",
                    recorded_by="tester",
                    metadata={"ticket": "INC123"},
                )

        self.assertTrue(result["success"])
        self.assertEqual(result["feedback_id"], 88)
        self.assertEqual(result["feedback_type"], "DIAGNOSIS_CORRECTNESS")
        self.assertEqual(result["feedback_rating"], "POSITIVE")
        insert_feedback.assert_called_once()
        call_kwargs = insert_feedback.call_args.kwargs
        self.assertEqual(call_kwargs["run_history_id"], 1)
        self.assertEqual(call_kwargs["recommendation_history_id"], 2)
        self.assertEqual(call_kwargs["action_history_id"], 3)
        self.assertEqual(call_kwargs["action_outcome_id"], 4)

    def test_insert_exception_returns_failure_without_raising(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_feedback_history",
                side_effect=RuntimeError("insert failed"),
            ):
                result = memory_orchestrator.record_feedback(
                    run_history_id=1,
                    feedback_type="DIAGNOSIS_CORRECTNESS",
                    feedback_rating="POSITIVE",
                    feedback_summary="Advisor diagnosis matched DBA review.",
                )

        self.assertFalse(result["success"])
        self.assertIn("RuntimeError: insert failed", result["errors"])

    def test_cli_argument_parsing_handles_required_fields(self) -> None:
        parser = record_feedback_cli.build_parser()
        args = parser.parse_args(
            [
                "--run-history-id",
                "1",
                "--feedback-type",
                "GENERAL",
                "--feedback-rating",
                "NEUTRAL",
                "--feedback-summary",
                "Manual review completed.",
            ]
        )

        self.assertEqual(args.run_history_id, 1)
        self.assertEqual(args.feedback_type, "GENERAL")
        self.assertEqual(args.feedback_rating, "NEUTRAL")

    def test_optional_linkage_ids_must_be_positive(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.record_feedback(
                run_history_id=1,
                recommendation_history_id=0,
                action_history_id=-1,
                action_outcome_id="bad",
                feedback_type="GENERAL",
                feedback_rating="NEUTRAL",
                feedback_summary="Manual review completed.",
            )

        self.assertFalse(result["success"])
        self.assertIn("recommendation_history_id must be an integer greater than 0", result["errors"])
        self.assertIn("action_history_id must be an integer greater than 0", result["errors"])
        self.assertIn("action_outcome_id must be an integer greater than 0", result["errors"])


if __name__ == "__main__":
    unittest.main()
