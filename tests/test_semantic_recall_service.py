from __future__ import annotations

import json
import unittest

from src.memory.semantic_recall_service import (
    build_curated_semantic_summary,
    recall_by_db_name,
    recall_by_issue_type,
    recall_by_posture,
    recall_related_context,
)


class FakeSemanticAdapter:
    def __init__(self, *, enabled: bool = True, success: bool = True) -> None:
        self.enabled = enabled
        self.success = success
        self.searches: list[dict] = []
        self.closed = False

    def search_memory(self, query: str, *, db_name: str = "SPRTRN", limit: int = 5) -> dict:
        self.searches.append({"query": query, "db_name": db_name, "limit": limit})
        if not self.enabled:
            return {
                "enabled": False,
                "success": True,
                "skipped": ["oracle_agent_memory_disabled"],
                "records": [],
                "count": 0,
                "authoritative": False,
                "runtime_influence": False,
            }
        if not self.success:
            return {
                "enabled": True,
                "success": False,
                "error": "search failed",
                "errors": ["search failed"],
                "records": [],
                "count": 0,
                "authoritative": False,
                "runtime_influence": False,
            }
        records = [
            {
                "id": "memory-2",
                "content": json.dumps(
                    {
                        "db_name": "OTHERDB",
                        "primary_issue": "cpu_pressure",
                        "posture": "INVESTIGATE",
                    }
                ),
                "metadata": {"authoritative": False, "runtime_influence": False},
                "score": 0.99,
            },
            {
                "id": "memory-1",
                "content": json.dumps(
                    {
                        "db_name": "SPRTRN",
                        "primary_issue": "io_pressure",
                        "secondary_issue": "commit_pressure",
                        "posture": "TUNE FIRST",
                        "summary": "Repeated User I/O spikes with commit latency.",
                    }
                ),
                "metadata": {"authoritative": False, "runtime_influence": False},
                "score": 0.88,
            },
            {
                "id": "memory-3",
                "content": "SPRTRN io pressure TUNE FIRST",
                "metadata": {"authoritative": False, "runtime_influence": False},
                "score": 0.75,
            },
        ]
        return {
            "enabled": True,
            "success": True,
            "query": query,
            "records": records[:limit],
            "count": min(len(records), limit),
            "authoritative": False,
            "runtime_influence": False,
        }

    def close(self) -> None:
        self.closed = True


class SemanticRecallServiceTests(unittest.TestCase):
    def test_recall_by_db_name_returns_stable_non_authoritative_shape(self) -> None:
        adapter = FakeSemanticAdapter()

        result = recall_by_db_name("SPRTRN", limit=2, adapter=adapter)

        self.assertTrue(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["query"], "SPRTRN")
        self.assertEqual(result["count"], 2)
        self.assertFalse(result["authoritative"])
        self.assertFalse(result["runtime_influence"])
        self.assertTrue(result["semantic_only"])
        self.assertEqual(result["records"][0]["id"], "memory-1")
        self.assertFalse(adapter.closed)

    def test_recall_by_issue_type_ranks_exact_issue_match_first(self) -> None:
        adapter = FakeSemanticAdapter()

        result = recall_by_issue_type("io pressure", limit=3, adapter=adapter)

        self.assertEqual(result["records"][0]["id"], "memory-1")
        self.assertEqual(adapter.searches[0]["query"], "io pressure")

    def test_recall_by_posture_ranks_exact_posture_match_first(self) -> None:
        adapter = FakeSemanticAdapter()

        result = recall_by_posture("TUNE FIRST", limit=3, adapter=adapter)

        self.assertEqual(result["records"][0]["id"], "memory-1")
        self.assertEqual(adapter.searches[0]["query"], "TUNE FIRST")

    def test_related_context_preserves_semantic_order_when_no_exact_context(self) -> None:
        adapter = FakeSemanticAdapter()

        result = recall_related_context("operational context", limit=2, adapter=adapter)

        self.assertEqual([record["id"] for record in result["records"]], ["memory-2", "memory-1"])
        self.assertTrue(result["semantic_only"])

    def test_disabled_mode_returns_safe_shape(self) -> None:
        adapter = FakeSemanticAdapter(enabled=False)

        result = recall_related_context("SPRTRN", adapter=adapter)

        self.assertFalse(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["records"], [])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["skipped"], ["oracle_agent_memory_disabled"])
        self.assertTrue(result["semantic_only"])

    def test_failed_search_returns_structured_error(self) -> None:
        adapter = FakeSemanticAdapter(success=False)

        result = recall_related_context("SPRTRN", adapter=adapter)

        self.assertTrue(result["enabled"])
        self.assertFalse(result["success"])
        self.assertEqual(result["records"], [])
        self.assertEqual(result["errors"], ["search failed"])
        self.assertTrue(result["semantic_only"])

    def test_empty_query_fails_without_calling_adapter(self) -> None:
        adapter = FakeSemanticAdapter()

        result = recall_related_context("", adapter=adapter)

        self.assertFalse(result["success"])
        self.assertEqual(adapter.searches, [])
        self.assertIn("query is required", result["errors"][0])

    def test_limit_is_bounded_for_adapter_search_and_return_records(self) -> None:
        adapter = FakeSemanticAdapter()

        result = recall_related_context("SPRTRN", limit=100, adapter=adapter)

        self.assertEqual(adapter.searches[0]["limit"], 25)
        self.assertEqual(result["count"], 3)

    def test_curated_semantic_summary_aggregates_context_without_recommendations(self) -> None:
        adapter = FakeSemanticAdapter()

        result = build_curated_semantic_summary("SPRTRN", limit=3, adapter=adapter)

        self.assertTrue(result["success"])
        self.assertTrue(result["semantic_only"])
        self.assertEqual(result["summary"]["matched_db_names"], ["OTHERDB", "SPRTRN"])
        self.assertIn("TUNE FIRST", result["summary"]["matched_postures"])
        self.assertIn("io_pressure", result["summary"]["matched_issue_types"])
        rendered_summary = json.dumps(result["summary"]).lower()
        self.assertIn("semantic recall suggests", rendered_summary)
        self.assertNotIn("root cause is", rendered_summary)
        self.assertNotIn("scale now", rendered_summary)
        self.assertNotIn("do not scale", rendered_summary)


if __name__ == "__main__":
    unittest.main()
