from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.awr_memory_cli as awr_memory_cli
from src.memory import memory_recall
from src.memory.governance_semantic_assist import assist_unknown_signal_review
from src.memory.oracle_agent_memory_adapter import verify_runtime_isolation
from src.memory.semantic_recall_service import recall_related_context


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT / "awr_dashboard"
RUNTIME_FORBIDDEN_IMPORTS = (
    "oracle_agent_memory_adapter",
    "semantic_recall_service",
    "governance_semantic_assist",
    "oracleagentmemory",
)


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self.description = connection.description

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # noqa: ANN001
        return None

    def execute(self, sql: str, params: dict | None = None) -> None:
        self.connection.executed.append((sql, params or {}))
        self.connection.current_rows = self.connection.rows

    def fetchall(self) -> list[tuple]:
        return list(self.connection.current_rows)


class FakeConnection:
    def __init__(self) -> None:
        self.rows = [(1, "SPRTRN", "NEW")]
        self.description = [
            ("UNKNOWN_SIGNAL_ID",),
            ("DB_NAME",),
            ("REVIEW_STATUS",),
        ]
        self.current_rows: list[tuple] = []
        self.executed: list[tuple[str, dict]] = []
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class FakeSemanticAdapter:
    def __init__(self) -> None:
        self.searches: list[dict] = []

    def search_memory(self, query: str, *, db_name: str = "SPRTRN", limit: int = 5) -> dict:
        self.searches.append({"query": query, "db_name": db_name, "limit": limit})
        return {
            "enabled": True,
            "success": True,
            "query": query,
            "records": [
                {
                    "id": "memory-1",
                    "content": json.dumps(
                        {
                            "db_name": "SPRTRN",
                            "primary_issue": "io_pressure",
                            "posture": "TUNE FIRST",
                        }
                    ),
                    "metadata": {"authoritative": False, "runtime_influence": False},
                }
            ],
            "count": 1,
            "authoritative": False,
            "runtime_influence": False,
        }

    def close(self) -> None:
        pass


class Phase6ValidationTests(unittest.TestCase):
    def test_runtime_isolation_static_source_paths(self) -> None:
        checked_paths = [
            ROOT / "scripts" / "run_analysis.py",
            ROOT / "src" / "analysis" / "decision_engine.py",
            ROOT / "src" / "analysis" / "recommendation_engine.py",
            ROOT / "src" / "reporting" / "html_dashboard.py",
        ]
        for path in checked_paths:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for forbidden in RUNTIME_FORBIDDEN_IMPORTS:
                self.assertNotIn(forbidden, text, f"{forbidden} leaked into {path}")

    def test_importing_runtime_modules_does_not_activate_semantic_modules(self) -> None:
        for module_name in (
            "src.memory.oracle_agent_memory_adapter",
            "src.memory.semantic_recall_service",
            "src.memory.governance_semantic_assist",
        ):
            sys.modules.pop(module_name, None)

        __import__("scripts.run_analysis")

        self.assertNotIn("src.memory.oracle_agent_memory_adapter", sys.modules)
        self.assertNotIn("src.memory.semantic_recall_service", sys.modules)
        self.assertNotIn("src.memory.governance_semantic_assist", sys.modules)

    def test_oracle_agent_memory_runtime_isolation_report(self) -> None:
        result = verify_runtime_isolation(repo_root=ROOT)

        self.assertTrue(result["isolation_verified"])
        self.assertFalse(result["deterministic_tables_modified"])
        self.assertFalse(result["parser_called"])
        self.assertFalse(result["scoring_called"])
        self.assertFalse(result["decision_engine_called"])
        self.assertFalse(result["recommendation_engine_called"])

    def test_semantic_recall_is_non_authoritative_and_read_only(self) -> None:
        adapter = FakeSemanticAdapter()

        result = recall_related_context("SPRTRN io pressure", adapter=adapter)

        self.assertTrue(result["success"])
        self.assertFalse(result["authoritative"])
        self.assertFalse(result["runtime_influence"])
        self.assertTrue(result["semantic_only"])
        self.assertEqual(adapter.searches[0]["query"], "SPRTRN io pressure")

    def test_governance_assist_is_reviewer_assist_only_without_decision_language(self) -> None:
        result = assist_unknown_signal_review(
            {
                "SECTION_NAME": "io",
                "UNKNOWN_TYPE": "MISSING_EXPECTED_SECTION",
                "DB_NAME": "SPRTRN",
            },
            adapter=FakeSemanticAdapter(),
        )

        self.assertTrue(result["success"])
        self.assertFalse(result["authoritative"])
        self.assertFalse(result["runtime_influence"])
        self.assertTrue(result["semantic_only"])
        self.assertTrue(result["reviewer_assist_only"])
        rendered = json.dumps(result).lower()
        for forbidden in (
            "approve this",
            "reject this",
            "recommended action is",
            "materialize artifact",
            "parser should",
            "system determined",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_dashboard_semantic_visibility_is_screen6_only(self) -> None:
        screen_6 = (DASHBOARD_DIR / "screen_6_fleet_overview.html").read_text(encoding="utf-8")
        self.assertIn("Semantic Recall Visibility", screen_6)
        self.assertIn("Phase 6 Semantic Memory", screen_6)
        self.assertIn("reviewer-assist context only", screen_6)
        self.assertIn("Runtime influence", screen_6)
        self.assertIn("false", screen_6)

        for file_name in ("screen_2_analysis.html", "screen_5_recommendation_action.html"):
            text = (DASHBOARD_DIR / file_name).read_text(encoding="utf-8")
            self.assertNotIn("Semantic Recall Visibility", text)
            self.assertNotIn("Phase 6 Semantic Memory", text)

    def test_dashboard_preserves_governed_memory_and_semantic_boundary_wording(self) -> None:
        index_text = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        screen_6 = (DASHBOARD_DIR / "screen_6_fleet_overview.html").read_text(encoding="utf-8")

        self.assertIn("Governed Memory:", index_text)
        self.assertNotIn("Memory: Active", index_text)
        self.assertIn("non-authoritative", screen_6)
        self.assertIn("does not change deterministic diagnosis", screen_6)
        self.assertIn("artifact activation", screen_6)

    def test_memory_recall_shape_ordering_limit_and_no_writes(self) -> None:
        connection = FakeConnection()

        result = memory_recall.recall_unknown_signals(
            review_status="NEW",
            limit=5,
            order="oldest",
            connection=connection,
        )

        self.assertTrue(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertIsInstance(result["records"], list)
        self.assertEqual(result["order"], "oldest")
        self.assertFalse(connection.committed)
        self.assertFalse(connection.rolled_back)
        sql, params = connection.executed[0]
        self.assertTrue(sql.strip().upper().startswith("SELECT"))
        self.assertIn("FETCH FIRST 5 ROWS ONLY", sql)
        self.assertEqual(params["filter_0"], "NEW")

    def test_cli_write_commands_require_actor_and_do_not_call_semantic_recall(self) -> None:
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            awr_memory_cli.main(
                [
                    "governance",
                    "approve-request",
                    "--request-id",
                    "1",
                    "--approval-status",
                    "APPROVED",
                ]
            )

        with patch.object(
            awr_memory_cli.memory_orchestrator,
            "review_unknown_signal",
            return_value={"enabled": True, "success": True},
        ), patch.object(
            awr_memory_cli.semantic_recall_service,
            "recall_related_context",
        ) as semantic_recall, contextlib.redirect_stdout(io.StringIO()):
            exit_code = awr_memory_cli.main(
                [
                    "review",
                    "unknown-signal",
                    "--unknown-signal-id",
                    "1",
                    "--review-status",
                    "CLASSIFIED",
                    "--actor",
                    "probev",
                ]
            )

        self.assertEqual(exit_code, 0)
        semantic_recall.assert_not_called()

    def test_cli_read_commands_and_compact_json_are_safe(self) -> None:
        with patch.object(
            awr_memory_cli.memory_orchestrator,
            "recall_unknown_signals",
            return_value={
                "enabled": True,
                "success": True,
                "records": [],
                "count": 0,
                "order": "oldest",
            },
        ) as recall_unknowns:
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = awr_memory_cli.main(
                    [
                        "--compact",
                        "recall",
                        "unknown-signals",
                        "--status",
                        "NEW",
                        "--limit",
                        "5",
                        "--order",
                        "oldest",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertNotIn("\n", buffer.getvalue().strip())
        recall_unknowns.assert_called_once_with(
            review_status="NEW",
            review_classification=None,
            db_name=None,
            section_name=None,
            limit=5,
            order="oldest",
        )


if __name__ == "__main__":
    unittest.main()
