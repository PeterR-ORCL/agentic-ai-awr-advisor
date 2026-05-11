from __future__ import annotations

import contextlib
import io
import json
import unittest
from argparse import Namespace
from unittest.mock import patch

import scripts.awr_memory_cli as cli


def _ok_result(**extra):
    result = {
        "enabled": True,
        "success": True,
        "records": [],
        "count": 0,
        "authoritative": False,
        "runtime_influence": False,
    }
    result.update(extra)
    return result


def _run_main_silent(argv: list[str]) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return cli.main(argv)


class AwrMemoryCliTests(unittest.TestCase):
    def test_status_command_shape(self) -> None:
        with patch.object(
            cli.memory_orchestrator,
            "recall_memory_summary",
            return_value=_ok_result(summary={"runs": 1}),
        ):
            result = cli.dispatch(Namespace(command="status"))

        self.assertTrue(result["success"])
        self.assertTrue(result["memory_enabled"])
        self.assertTrue(result["structured_recall_available"])
        self.assertFalse(result["runtime_influence"])
        self.assertFalse(result["semantic_authoritative"])
        self.assertTrue(result["governance_apis_available"])
        self.assertTrue(result["artifact_apis_available"])

    def test_recall_summary_delegates_correctly(self) -> None:
        with patch.object(
            cli.memory_orchestrator,
            "recall_memory_summary",
            return_value=_ok_result(summary={"runs": 1}, order="oldest"),
        ) as recall_summary:
            result = _run_main_silent(["recall", "summary", "--order", "oldest"])

        self.assertEqual(result, 0)
        recall_summary.assert_called_once_with(order="oldest")

    def test_recall_unknown_signals_passes_status_order_limit(self) -> None:
        with patch.object(
            cli.memory_orchestrator,
            "recall_unknown_signals",
            return_value=_ok_result(records=[]),
        ) as recall_unknowns:
            exit_code = _run_main_silent(
                [
                    "recall",
                    "unknown-signals",
                    "--status",
                    "NEW",
                    "--limit",
                    "5",
                    "--order",
                    "newest",
                ]
            )

        self.assertEqual(exit_code, 0)
        recall_unknowns.assert_called_once_with(
            review_status="NEW",
            review_classification=None,
            db_name=None,
            section_name=None,
            limit=5,
            order="newest",
        )

    def test_semantic_recall_disabled_safe_behavior(self) -> None:
        disabled = {
            "enabled": False,
            "success": True,
            "skipped": ["oracle_agent_memory_disabled"],
            "records": [],
            "count": 0,
            "authoritative": False,
            "runtime_influence": False,
            "semantic_only": True,
        }
        with patch.object(
            cli.semantic_recall_service,
            "recall_related_context",
            return_value=disabled,
        ) as semantic_recall:
            exit_code = _run_main_silent(["semantic", "recall", "--query", "SPRTRN io pressure"])

        self.assertEqual(exit_code, 0)
        semantic_recall.assert_called_once_with("SPRTRN io pressure", limit=5)

    def test_semantic_assist_unknown_signal_shape(self) -> None:
        recall_result = _ok_result(
            records=[
                {
                    "UNKNOWN_SIGNAL_ID": 1,
                    "SECTION_NAME": "io",
                    "UNKNOWN_TYPE": "MISSING_EXPECTED_SECTION",
                    "DB_NAME": "SPRTRN",
                }
            ]
        )
        assist_result = _ok_result(
            review_type="unknown_signal",
            reviewer_assist_only=True,
            semantic_only=True,
        )
        with patch.object(
            cli.memory_orchestrator,
            "recall_unknown_signals",
            return_value=recall_result,
        ) as recall_unknowns, patch.object(
            cli.governance_semantic_assist,
            "assist_unknown_signal_review",
            return_value=assist_result,
        ) as assist_unknown:
            exit_code = _run_main_silent(["semantic", "assist-unknown-signal", "--unknown-signal-id", "1"])

        self.assertEqual(exit_code, 0)
        recall_unknowns.assert_called_once_with(limit=500, order="newest")
        assist_unknown.assert_called_once()
        self.assertEqual(assist_unknown.call_args.args[0]["UNKNOWN_SIGNAL_ID"], 1)

    def test_review_unknown_signal_requires_actor(self) -> None:
        with self.assertRaises(SystemExit):
            _run_main_silent(
                [
                    "review",
                    "unknown-signal",
                    "--unknown-signal-id",
                    "1",
                    "--review-status",
                    "CLASSIFIED",
                ]
            )

    def test_governance_approve_requires_actor(self) -> None:
        with self.assertRaises(SystemExit):
            _run_main_silent(
                [
                    "governance",
                    "approve-request",
                    "--request-id",
                    "1",
                    "--approval-status",
                    "APPROVED",
                ]
            )

    def test_artifact_materialize_requires_actor(self) -> None:
        with self.assertRaises(SystemExit):
            _run_main_silent(
                [
                    "artifact",
                    "materialize",
                    "--request-id",
                    "1",
                    "--artifact-type",
                    "SIGNAL_CLASSIFICATION",
                ]
            )

    def test_write_commands_do_not_call_semantic_recall_implicitly(self) -> None:
        with patch.object(
            cli.memory_orchestrator,
            "review_unknown_signal",
            return_value=_ok_result(unknown_signal_id=1),
        ), patch.object(
            cli.semantic_recall_service,
            "recall_related_context",
        ) as semantic_recall:
            exit_code = _run_main_silent(
                [
                    "review",
                    "unknown-signal",
                    "--unknown-signal-id",
                    "1",
                    "--review-status",
                    "CLASSIFIED",
                    "--review-classification",
                    "IO",
                    "--actor",
                    "probev",
                ]
            )

        self.assertEqual(exit_code, 0)
        semantic_recall.assert_not_called()

    def test_compact_json_output(self) -> None:
        buffer = io.StringIO()
        with patch.object(
            cli.memory_orchestrator,
            "recall_memory_summary",
            return_value=_ok_result(summary={"runs": 1}),
        ), contextlib.redirect_stdout(buffer):
            exit_code = cli.main(["--compact", "recall", "summary"])

        self.assertEqual(exit_code, 0)
        rendered = buffer.getvalue().strip()
        self.assertNotIn("\n", rendered)
        self.assertEqual(json.loads(rendered)["summary"], {"runs": 1})


if __name__ == "__main__":
    unittest.main()
