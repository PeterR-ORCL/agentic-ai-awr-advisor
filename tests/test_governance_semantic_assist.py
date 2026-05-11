from __future__ import annotations

import json
import unittest

from src.memory.governance_semantic_assist import (
    assist_artifact_review,
    assist_knowledge_request_review,
    assist_parser_governance_review,
    assist_unknown_signal_review,
)


class FakeGovernanceSemanticAdapter:
    def __init__(self, *, enabled: bool = True, success: bool = True) -> None:
        self.enabled = enabled
        self.success = success
        self.searches: list[dict] = []

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
                "semantic_only": True,
            }
        if not self.success:
            return {
                "enabled": True,
                "success": False,
                "error": "semantic search failed",
                "errors": ["semantic search failed"],
                "records": [],
                "count": 0,
                "authoritative": False,
                "runtime_influence": False,
                "semantic_only": True,
            }
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
                            "secondary_issue": "commit_pressure",
                            "posture": "TUNE FIRST",
                            "summary": "Repeated User I/O context for reviewer assistance.",
                        }
                    ),
                    "metadata": {
                        "authoritative": False,
                        "runtime_influence": False,
                        "semantic_only": True,
                    },
                    "score": 0.91,
                }
            ],
            "count": 1,
            "authoritative": False,
            "runtime_influence": False,
            "semantic_only": True,
        }

    def close(self) -> None:
        pass


class GovernanceSemanticAssistTests(unittest.TestCase):
    def test_unknown_signal_assist_returns_reviewer_context_only(self) -> None:
        adapter = FakeGovernanceSemanticAdapter()

        result = assist_unknown_signal_review(
            {
                "SECTION_NAME": "io",
                "UNKNOWN_TYPE": "MISSING_EXPECTED_SECTION",
                "DB_NAME": "SPRTRN",
                "DETECTION_REASON": "Optional parser section was missing",
            },
            limit=3,
            adapter=adapter,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["review_type"], "unknown_signal")
        self.assertIn("MISSING_EXPECTED_SECTION", result["query"])
        self.assertIn("Optional parser section was missing", result["query"])
        self.assertFalse(result["authoritative"])
        self.assertFalse(result["runtime_influence"])
        self.assertTrue(result["semantic_only"])
        self.assertTrue(result["reviewer_assist_only"])
        self.assertIn("io_pressure", result["semantic_context"]["matched_issue_types"])

    def test_knowledge_request_assist_builds_governance_query(self) -> None:
        adapter = FakeGovernanceSemanticAdapter()

        result = assist_knowledge_request_review(
            {
                "SOURCE_TYPE": "UNKNOWN_SIGNAL",
                "CANDIDATE_CLASSIFICATION": "IO",
                "CANDIDATE_SUMMARY": "Unknown IO section consistently detected",
                "DB_NAME": "SPRTRN",
                "POSTURE": "TUNE FIRST",
            },
            adapter=adapter,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["review_type"], "knowledge_request")
        self.assertIn("UNKNOWN_SIGNAL", result["query"])
        self.assertIn("TUNE FIRST", result["query"])
        self.assertEqual(result["semantic_context"]["matched_db_names"], ["SPRTRN"])

    def test_artifact_assist_uses_artifact_context(self) -> None:
        adapter = FakeGovernanceSemanticAdapter()

        result = assist_artifact_review(
            {
                "ARTIFACT_TYPE": "SIGNAL_CLASSIFICATION",
                "ARTIFACT_CLASSIFICATION": "IO",
                "ARTIFACT_SUMMARY": "Approved IO classification",
            },
            adapter=adapter,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["review_type"], "artifact")
        self.assertIn("SIGNAL_CLASSIFICATION", result["query"])
        self.assertIn("Approved IO classification", result["query"])

    def test_parser_governance_assist_uses_stage_and_classification_hint(self) -> None:
        adapter = FakeGovernanceSemanticAdapter()

        result = assist_parser_governance_review(
            {
                "parser_stage": "section_discovery",
                "classification_hint": "IO",
                "section_context": "File IO Stats",
            },
            adapter=adapter,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["review_type"], "parser_governance")
        self.assertIn("section_discovery", result["query"])
        self.assertIn("File IO Stats", result["query"])

    def test_disabled_mode_remains_clean_and_read_only(self) -> None:
        adapter = FakeGovernanceSemanticAdapter(enabled=False)

        result = assist_unknown_signal_review({"DB_NAME": "SPRTRN"}, adapter=adapter)

        self.assertFalse(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["records"], [])
        self.assertEqual(result["skipped"], ["oracle_agent_memory_disabled"])
        self.assertTrue(result["reviewer_assist_only"])

    def test_missing_context_returns_validation_error_without_search(self) -> None:
        adapter = FakeGovernanceSemanticAdapter()

        result = assist_artifact_review({}, adapter=adapter)

        self.assertFalse(result["success"])
        self.assertEqual(adapter.searches, [])
        self.assertEqual(result["records"], [])
        self.assertIn("semantic assist query context is required", result["errors"])

    def test_observations_do_not_include_governance_decision_language(self) -> None:
        adapter = FakeGovernanceSemanticAdapter()

        result = assist_unknown_signal_review({"DB_NAME": "SPRTRN"}, adapter=adapter)
        rendered = json.dumps(result["semantic_context"]).lower()

        self.assertIn("semantic recall suggests", rendered)
        self.assertNotIn("approve this", rendered)
        self.assertNotIn("reject this", rendered)
        self.assertNotIn("system determined", rendered)
        self.assertNotIn("root cause is", rendered)
        self.assertNotIn("materialize artifact", rendered)
        self.assertNotIn("recommended action is", rendered)
        self.assertNotIn("parser should", rendered)


if __name__ == "__main__":
    unittest.main()
