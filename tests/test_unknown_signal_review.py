from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from scripts import review_unknown_signal as review_unknown_signal_cli
from src.memory import memory_orchestrator


class UnknownSignalReviewTests(unittest.TestCase):
    def test_valid_update(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "update_unknown_signal_review",
                return_value={
                    "unknown_signal_id": 10,
                    "previous_review_status": "NEW",
                    "previous_review_classification": None,
                },
            ) as update_review:
                result = memory_orchestrator.review_unknown_signal(
                    unknown_signal_id=10,
                    review_status="classified",
                    review_classification="io",
                    review_notes="Likely IO wait with missing STAT_NAME.",
                    reviewed_by="tester",
                    metadata={"source": "unit"},
                )

        self.assertTrue(result["success"])
        self.assertEqual(result["unknown_signal_id"], 10)
        self.assertEqual(result["review_status"], "CLASSIFIED")
        self.assertEqual(result["review_classification"], "IO")
        update_review.assert_called_once()
        self.assertEqual(update_review.call_args.kwargs["review_classification"], "IO")

    def test_invalid_unknown_signal_id_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.review_unknown_signal(
                unknown_signal_id=0,
                review_status="REVIEWED",
            )

        self.assertFalse(result["success"])
        self.assertIn("unknown_signal_id is required", result["errors"][0])

    def test_invalid_review_status_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.review_unknown_signal(
                unknown_signal_id=10,
                review_status="DONE",
            )

        self.assertFalse(result["success"])
        self.assertIn("review_status must be one of", result["errors"][0])

    def test_classification_normalization(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "update_unknown_signal_review",
                return_value={"previous_review_status": "NEW"},
            ):
                result = memory_orchestrator.review_unknown_signal(
                    unknown_signal_id=10,
                    review_status="classified",
                    review_classification="adg",
                )

        self.assertTrue(result["success"])
        self.assertEqual(result["review_classification"], "ADG")

    def test_metadata_serialization_passes_dict_to_memory_agent(self) -> None:
        metadata = {"ticket": "INC123"}
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "update_unknown_signal_review",
                return_value={"previous_review_status": "NEW"},
            ) as update_review:
                result = memory_orchestrator.review_unknown_signal(
                    unknown_signal_id=10,
                    review_status="REVIEWED",
                    metadata=metadata,
                )

        self.assertTrue(result["success"])
        self.assertEqual(update_review.call_args.kwargs["metadata"], metadata)

    def test_overwrite_warning(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "update_unknown_signal_review",
                return_value={"previous_review_status": "CLASSIFIED"},
            ):
                result = memory_orchestrator.review_unknown_signal(
                    unknown_signal_id=10,
                    review_status="IGNORED",
                )

        self.assertTrue(result["success"])
        self.assertIn("overwriting existing review classification", result["warnings"])

    def test_memory_disabled_does_not_call_update(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "false"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "update_unknown_signal_review",
            ) as update_review:
                result = memory_orchestrator.review_unknown_signal(
                    unknown_signal_id=10,
                    review_status="REVIEWED",
                )

        update_review.assert_not_called()
        self.assertFalse(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["skipped"], ["memory_disabled"])

    def test_db_failure_handling(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "update_unknown_signal_review",
                side_effect=RuntimeError("update failed"),
            ):
                result = memory_orchestrator.review_unknown_signal(
                    unknown_signal_id=10,
                    review_status="REVIEWED",
                )

        self.assertFalse(result["success"])
        self.assertIn("RuntimeError: update failed", result["errors"])

    def test_cli_argument_parsing_handles_required_fields(self) -> None:
        parser = review_unknown_signal_cli.build_parser()
        args = parser.parse_args(
            [
                "--unknown-signal-id",
                "10",
                "--review-status",
                "CLASSIFIED",
                "--review-classification",
                "IO",
            ]
        )

        self.assertEqual(args.unknown_signal_id, 10)
        self.assertEqual(args.review_status, "CLASSIFIED")
        self.assertEqual(args.review_classification, "IO")


if __name__ == "__main__":
    unittest.main()
