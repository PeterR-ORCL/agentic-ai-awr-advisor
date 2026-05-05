from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from scripts import approve_knowledge_request as approve_cli
from scripts import create_knowledge_request as create_cli
from src.memory import memory_orchestrator


class KnowledgeApprovalTests(unittest.TestCase):
    def test_create_request_success(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_knowledge_update_request",
                return_value=44,
            ) as insert_request:
                result = memory_orchestrator.create_knowledge_update_request(
                    source_type="unknown signal",
                    source_id=1,
                    run_history_id=1,
                    candidate_classification="io",
                    candidate_summary="Unknown IO section consistently detected.",
                    candidate_details="Appears with missing STAT_NAME.",
                    created_by="tester",
                    metadata={"ticket": "INC123"},
                )

        self.assertTrue(result["success"])
        self.assertEqual(result["request_id"], 44)
        self.assertEqual(result["source_type"], "UNKNOWN_SIGNAL")
        self.assertEqual(result["approval_status"], "PENDING")
        insert_request.assert_called_once()
        self.assertEqual(insert_request.call_args.kwargs["candidate_classification"], "IO")

    def test_invalid_source_type_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.create_knowledge_update_request(
                source_type="parser",
                source_id=1,
                candidate_classification=None,
                candidate_summary="Candidate summary.",
            )

        self.assertFalse(result["success"])
        self.assertIn("source_type must be one of", result["errors"][0])

    def test_approve_success(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "update_knowledge_update_request_status",
                return_value=44,
            ) as update_request:
                result = memory_orchestrator.approve_knowledge_update_request(
                    request_id=44,
                    approval_status="approved",
                    approved_by="senior_dba",
                    approval_notes="Confirmed valid mapping.",
                )

        self.assertTrue(result["success"])
        self.assertEqual(result["request_id"], 44)
        self.assertEqual(result["approval_status"], "APPROVED")
        update_request.assert_called_once()

    def test_invalid_approval_status_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.approve_knowledge_update_request(
                request_id=1,
                approval_status="DONE",
            )

        self.assertFalse(result["success"])
        self.assertIn("approval_status must be one of", result["errors"][0])

    def test_request_not_found_returns_failure_without_raising(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "update_knowledge_update_request_status",
                side_effect=ValueError("request_id must reference an existing knowledge update request"),
            ):
                result = memory_orchestrator.approve_knowledge_update_request(
                    request_id=999,
                    approval_status="REJECTED",
                )

        self.assertFalse(result["success"])
        self.assertIn("ValueError: request_id must reference", result["errors"][0])

    def test_memory_disabled_create_does_not_call_insert(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "false"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_knowledge_update_request",
            ) as insert_request:
                result = memory_orchestrator.create_knowledge_update_request(
                    source_type="UNKNOWN_SIGNAL",
                    source_id=1,
                    candidate_classification="IO",
                    candidate_summary="Candidate summary.",
                )

        insert_request.assert_not_called()
        self.assertFalse(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["skipped"], ["memory_disabled"])

    def test_update_failure_handling(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "update_knowledge_update_request_status",
                side_effect=RuntimeError("update failed"),
            ):
                result = memory_orchestrator.approve_knowledge_update_request(
                    request_id=1,
                    approval_status="NEEDS_REVIEW",
                )

        self.assertFalse(result["success"])
        self.assertIn("RuntimeError: update failed", result["errors"])

    def test_cli_argument_parsing_handles_create_fields(self) -> None:
        parser = create_cli.build_parser()
        args = parser.parse_args(
            [
                "--source-type",
                "UNKNOWN_SIGNAL",
                "--source-id",
                "1",
                "--summary",
                "Unknown IO section consistently detected.",
            ]
        )

        self.assertEqual(args.source_type, "UNKNOWN_SIGNAL")
        self.assertEqual(args.source_id, 1)
        self.assertEqual(args.summary, "Unknown IO section consistently detected.")

    def test_cli_argument_parsing_handles_approval_fields(self) -> None:
        parser = approve_cli.build_parser()
        args = parser.parse_args(
            [
                "--request-id",
                "1",
                "--approval-status",
                "APPROVED",
            ]
        )

        self.assertEqual(args.request_id, 1)
        self.assertEqual(args.approval_status, "APPROVED")


if __name__ == "__main__":
    unittest.main()
