from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from scripts import materialize_knowledge as materialize_cli
from src.memory import memory_orchestrator


class KnowledgeMaterializationTests(unittest.TestCase):
    def test_success_path_with_approved_request(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_knowledge_artifact",
                return_value=55,
            ) as insert_artifact:
                result = memory_orchestrator.materialize_knowledge_artifact(
                    request_id=1,
                    artifact_type="signal classification",
                    artifact_classification="io",
                    artifact_summary="Approved IO classification for unknown signal.",
                    artifact_details="Derived from repeated unknown signal pattern.",
                    created_by="tester",
                    metadata={"ticket": "INC123"},
                )

        self.assertTrue(result["success"])
        self.assertEqual(result["artifact_id"], 55)
        self.assertEqual(result["artifact_type"], "SIGNAL_CLASSIFICATION")
        self.assertEqual(result["activation_status"], "INACTIVE")
        insert_artifact.assert_called_once()
        self.assertEqual(insert_artifact.call_args.kwargs["artifact_classification"], "IO")

    def test_reject_if_not_approved(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_knowledge_artifact",
                side_effect=ValueError("request_id must be APPROVED before materialization"),
            ):
                result = memory_orchestrator.materialize_knowledge_artifact(
                    request_id=1,
                    artifact_type="SIGNAL_CLASSIFICATION",
                )

        self.assertFalse(result["success"])
        self.assertIn("ValueError: request_id must be APPROVED", result["errors"][0])

    def test_invalid_request_id_fails_validation(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            result = memory_orchestrator.materialize_knowledge_artifact(
                request_id=0,
                artifact_type="SIGNAL_CLASSIFICATION",
            )

        self.assertFalse(result["success"])
        self.assertIn("request_id is required", result["errors"][0])

    def test_metadata_serialization_passes_dict_to_memory_agent(self) -> None:
        metadata = {"review": "manual"}
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_knowledge_artifact",
                return_value=55,
            ) as insert_artifact:
                result = memory_orchestrator.materialize_knowledge_artifact(
                    request_id=1,
                    artifact_type="RULE_HINT",
                    metadata=metadata,
                )

        self.assertTrue(result["success"])
        self.assertEqual(insert_artifact.call_args.kwargs["metadata"], metadata)

    def test_memory_disabled_does_not_call_insert(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "false"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_knowledge_artifact",
            ) as insert_artifact:
                result = memory_orchestrator.materialize_knowledge_artifact(
                    request_id=1,
                    artifact_type="SIGNAL_CLASSIFICATION",
                )

        insert_artifact.assert_not_called()
        self.assertFalse(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["skipped"], ["memory_disabled"])

    def test_db_failure_handling(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False):
            with patch.object(
                memory_orchestrator.memory_agent,
                "insert_knowledge_artifact",
                side_effect=RuntimeError("insert failed"),
            ):
                result = memory_orchestrator.materialize_knowledge_artifact(
                    request_id=1,
                    artifact_type="PATTERN",
                )

        self.assertFalse(result["success"])
        self.assertIn("RuntimeError: insert failed", result["errors"])

    def test_cli_argument_parsing_handles_required_fields(self) -> None:
        parser = materialize_cli.build_parser()
        args = parser.parse_args(
            [
                "--request-id",
                "1",
                "--artifact-type",
                "SIGNAL_CLASSIFICATION",
            ]
        )

        self.assertEqual(args.request_id, 1)
        self.assertEqual(args.artifact_type, "SIGNAL_CLASSIFICATION")


if __name__ == "__main__":
    unittest.main()
