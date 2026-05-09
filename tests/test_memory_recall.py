from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from scripts import recall_memory as recall_memory_cli
from src.memory import memory_orchestrator, memory_recall


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self.description = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # noqa: ANN001
        return None

    def execute(self, sql: str, params: dict | None = None) -> None:
        self.connection.executed.append((sql, params or {}))
        if "COUNT(*)" in sql.upper():
            self.description = [("COUNT",)]
            self.connection.current_rows = [(self.connection.count_value,)]
        else:
            self.description = self.connection.description
            self.connection.current_rows = self.connection.rows

    def fetchall(self) -> list[tuple]:
        return list(self.connection.current_rows)

    def fetchone(self) -> tuple | None:
        return self.connection.current_rows[0] if self.connection.current_rows else None


class FakeConnection:
    def __init__(
        self,
        rows: list[tuple] | None = None,
        description: list[tuple] | None = None,
        count_value: int = 3,
    ) -> None:
        self.rows = rows or []
        self.description = description or []
        self.current_rows: list[tuple] = []
        self.executed: list[tuple[str, dict]] = []
        self.count_value = count_value
        self.closed = False
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def close(self) -> None:
        self.closed = True

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class MemoryRecallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patch = patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "true"}, clear=False)
        self.env_patch.start()

    def tearDown(self) -> None:
        self.env_patch.stop()

    def test_disabled_memory_returns_skipped_without_db_call(self) -> None:
        with patch.dict(os.environ, {"AWR_MEMORY_ENABLED": "false"}, clear=False):
            with patch.object(memory_recall, "get_db_connection") as get_connection:
                result = memory_recall.recall_run_history()

        get_connection.assert_not_called()
        self.assertFalse(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["records"], [])
        self.assertEqual(result["skipped"], ["memory_disabled"])

    def test_recall_uses_select_only_and_does_not_mutate_memory(self) -> None:
        connection = FakeConnection(
            rows=[(1, "DB1", "TUNE_FIRST")],
            description=[
                ("RUN_HISTORY_ID",),
                ("DB_NAME",),
                ("DECISION_POSTURE",),
            ],
        )

        result = memory_recall.recall_run_history(
            db_name="DB1",
            limit=5,
            connection=connection,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["order"], "newest")
        self.assertEqual(result["records"][0]["run_history_id"], 1)
        self.assertEqual(result["records"][0]["db_name"], "DB1")
        self.assertFalse(connection.committed)
        self.assertFalse(connection.rolled_back)
        self.assertTrue(all(sql.strip().upper().startswith("SELECT") for sql, _ in connection.executed))

    def test_limit_is_enforced(self) -> None:
        connection = FakeConnection()

        result = memory_recall.recall_unknown_signals(
            review_status="NEW",
            limit=9999,
            connection=connection,
        )

        self.assertTrue(result["success"])
        sql, params = connection.executed[0]
        self.assertIn("FETCH FIRST 500 ROWS ONLY", sql)
        self.assertEqual(params["filter_0"], "NEW")
        self.assertEqual(result["order"], "newest")

    def test_oldest_order_changes_sql_ordering(self) -> None:
        connection = FakeConnection()

        result = memory_recall.recall_unknown_signals(
            review_status="NEW",
            limit=5,
            order="oldest",
            connection=connection,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["order"], "oldest")
        sql, _ = connection.executed[0]
        self.assertIn(
            "ORDER BY LAST_SEEN_TIMESTAMP ASC NULLS LAST, UNKNOWN_SIGNAL_ID ASC",
            sql,
        )
        self.assertIn("FETCH FIRST 5 ROWS ONLY", sql)

    def test_invalid_order_defaults_to_newest(self) -> None:
        connection = FakeConnection()

        result = memory_recall.recall_action_history(
            order="sideways",
            connection=connection,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["order"], "newest")
        sql, _ = connection.executed[0]
        self.assertIn(
            "ORDER BY CREATED_AT DESC NULLS LAST, ACTION_HISTORY_ID DESC",
            sql,
        )

    def test_filters_are_passed_to_query(self) -> None:
        connection = FakeConnection()

        memory_recall.recall_action_history(
            run_history_id=7,
            action_status="COMPLETED",
            action_type="SQL_TUNING",
            connection=connection,
        )

        sql, params = connection.executed[0]
        self.assertIn("RUN_HISTORY_ID = :filter_0", sql)
        self.assertIn("ACTION_STATUS = :filter_1", sql)
        self.assertIn("ACTION_TYPE = :filter_2", sql)
        self.assertEqual(params["filter_0"], 7)
        self.assertEqual(params["filter_1"], "COMPLETED")
        self.assertEqual(params["filter_2"], "SQL_TUNING")

    def test_unknown_signal_recall_returns_stable_shape(self) -> None:
        connection = FakeConnection(
            rows=[(10, "NEW", "IO")],
            description=[
                ("UNKNOWN_SIGNAL_ID",),
                ("REVIEW_STATUS",),
                ("REVIEW_CLASSIFICATION",),
            ],
        )

        result = memory_recall.recall_unknown_signals(connection=connection)

        self.assertTrue(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["order"], "newest")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["records"][0]["unknown_signal_id"], 10)
        self.assertEqual(result["records"][0]["review_status"], "NEW")

    def test_knowledge_request_and_artifact_recall_shapes(self) -> None:
        request_connection = FakeConnection(
            rows=[(2, "UNKNOWN_SIGNAL", "PENDING")],
            description=[("REQUEST_ID",), ("SOURCE_TYPE",), ("APPROVAL_STATUS",)],
        )
        artifact_connection = FakeConnection(
            rows=[(3, "SIGNAL_CLASSIFICATION", "INACTIVE")],
            description=[("ARTIFACT_ID",), ("ARTIFACT_TYPE",), ("ACTIVATION_STATUS",)],
        )

        request_result = memory_recall.recall_knowledge_requests(
            approval_status="PENDING",
            connection=request_connection,
        )
        artifact_result = memory_recall.recall_knowledge_artifacts(
            activation_status="INACTIVE",
            connection=artifact_connection,
        )

        self.assertTrue(request_result["success"])
        self.assertEqual(request_result["records"][0]["request_id"], 2)
        self.assertTrue(artifact_result["success"])
        self.assertEqual(artifact_result["records"][0]["artifact_id"], 3)

    def test_summary_recall_returns_expected_aggregate_keys(self) -> None:
        connection = FakeConnection(count_value=4)

        result = memory_recall.recall_memory_summary(connection=connection)

        self.assertTrue(result["success"])
        self.assertEqual(
            set(result["summary"].keys()),
            {
                "runs",
                "recommendations",
                "actions",
                "outcomes",
                "feedback",
                "unknown_signals",
                "knowledge_requests",
                "knowledge_artifacts",
            },
        )
        self.assertEqual(result["summary"]["runs"], 4)
        self.assertEqual(result["order"], "newest")
        self.assertEqual(len(connection.executed), 8)

    def test_orchestrator_exposes_recall_api(self) -> None:
        with patch.object(
            memory_orchestrator.memory_recall,
            "recall_action_history",
            return_value={"enabled": True, "success": True, "records": [], "count": 0},
        ) as recall_action_history:
            result = memory_orchestrator.recall_action_history(run_history_id=1)

        recall_action_history.assert_called_once_with(run_history_id=1)
        self.assertTrue(result["success"])

    def test_cli_argument_parsing_handles_unknown_signal_target(self) -> None:
        parser = recall_memory_cli.build_parser()
        args = parser.parse_args(
            [
                "--unknown-signals",
                "--status",
                "NEW",
                "--limit",
                "5",
                "--order",
                "oldest",
            ]
        )

        self.assertTrue(args.unknown_signals)
        self.assertEqual(args.status, "NEW")
        self.assertEqual(args.limit, 5)
        self.assertEqual(args.order, "oldest")


if __name__ == "__main__":
    unittest.main()
