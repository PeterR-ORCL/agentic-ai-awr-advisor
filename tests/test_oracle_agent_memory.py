from __future__ import annotations

import os
import unittest
from dataclasses import dataclass
from unittest.mock import patch

from src.memory.oracle_agent_memory_adapter import (
    OracleAgentMemoryConfig,
    OracleAgentMemoryPrototypeAdapter,
    build_curated_memory_payload,
    load_config_from_env,
    run_phase6n1_prototype,
)


@dataclass
class FakeRecord:
    id: str
    content: str
    metadata: dict


@dataclass
class FakeSearchResult:
    record: FakeRecord
    score: float


class FakeClient:
    def __init__(self) -> None:
        self.created_threads: list[dict] = []
        self.memories: list[dict] = []
        self.searches: list[dict] = []
        self.thread_exists = False

    def get_thread(self, thread_id: str) -> dict:
        if not self.thread_exists:
            raise KeyError(thread_id)
        return {"thread_id": thread_id}

    def create_thread(self, **kwargs) -> dict:
        self.thread_exists = True
        self.created_threads.append(kwargs)
        return {"thread_id": kwargs["thread_id"]}

    def add_memory(self, content: str, **kwargs) -> str:
        self.memories.append({"content": content, **kwargs})
        return "memory-1"

    def search(self, query: str, **kwargs) -> list[FakeSearchResult]:
        self.searches.append({"query": query, **kwargs})
        return [
            FakeSearchResult(
                record=FakeRecord(
                    id="memory-1",
                    content="SPRTRN io pressure TUNE FIRST",
                    metadata={"authoritative": False, "runtime_influence": False},
                ),
                score=0.99,
            )
        ]


def _enabled_config() -> OracleAgentMemoryConfig:
    return OracleAgentMemoryConfig(
        enabled=True,
        user="tester",
        password="secret",
        dsn="testdb",
        agent_endpoint="mock-embedder",
    )


class OracleAgentMemoryPrototypeTests(unittest.TestCase):
    def test_disabled_mode_returns_safe_skipped_response(self) -> None:
        adapter = OracleAgentMemoryPrototypeAdapter(
            OracleAgentMemoryConfig(enabled=False),
            client_factory=lambda config: FakeClient(),
        )

        result = adapter.initialize()

        self.assertFalse(result["enabled"])
        self.assertTrue(result["success"])
        self.assertEqual(result["skipped"], ["oracle_agent_memory_disabled"])
        self.assertFalse(result["authoritative"])
        self.assertFalse(result["runtime_influence"])

    def test_environment_config_uses_explicit_enable_flag(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ORACLE_AGENT_MEMORY_ENABLED": "true",
                "ORACLE_AGENT_MEMORY_AGENT_ENDPOINT": "endpoint",
                "ORACLE_AGENT_MEMORY_USER": "user1",
                "ORACLE_AGENT_MEMORY_PASSWORD": "secret",
                "ORACLE_AGENT_MEMORY_DSN": "dsn1",
            },
            clear=False,
        ):
            config = load_config_from_env()

        self.assertTrue(config.enabled)
        self.assertEqual(config.agent_endpoint, "endpoint")
        self.assertEqual(config.user, "user1")
        self.assertEqual(config.dsn, "dsn1")

    def test_curated_payload_shape_and_isolation_flags(self) -> None:
        payload = build_curated_memory_payload("SPRTRN")

        self.assertEqual(payload["db_name"], "SPRTRN")
        self.assertEqual(payload["primary_issue"], "io_pressure")
        self.assertEqual(payload["secondary_issue"], "commit_pressure")
        self.assertEqual(payload["posture"], "TUNE FIRST")
        self.assertEqual(payload["source"], "phase6n1_prototype")
        self.assertFalse(payload["authoritative"])
        self.assertFalse(payload["runtime_influence"])

    def test_adapter_initialization_uses_client_factory(self) -> None:
        fake_client = FakeClient()
        adapter = OracleAgentMemoryPrototypeAdapter(
            _enabled_config(),
            client_factory=lambda config: fake_client,
        )

        result = adapter.initialize()

        self.assertTrue(result["success"])
        self.assertFalse(result["authoritative"])
        self.assertFalse(result["runtime_influence"])

    def test_create_thread_and_write_curated_memory(self) -> None:
        fake_client = FakeClient()
        adapter = OracleAgentMemoryPrototypeAdapter(
            _enabled_config(),
            client_factory=lambda config: fake_client,
        )

        thread_result = adapter.get_or_create_thread("SPRTRN")
        payload = build_curated_memory_payload("SPRTRN")
        write_result = adapter.write_curated_memory(
            payload,
            thread_id=thread_result["thread_id"],
        )

        self.assertTrue(thread_result["success"])
        self.assertEqual(thread_result["thread_id"], "awr-db-sprtrn")
        self.assertEqual(fake_client.created_threads[0]["metadata"]["db_name"], "SPRTRN")
        self.assertEqual(fake_client.created_threads[0]["extract_memories"], False)
        self.assertTrue(write_result["success"])
        self.assertEqual(write_result["memory_id"], "memory-1")
        self.assertFalse(write_result["payload"]["authoritative"])
        self.assertFalse(write_result["payload"]["runtime_influence"])

    def test_rejects_authoritative_payload(self) -> None:
        fake_client = FakeClient()
        adapter = OracleAgentMemoryPrototypeAdapter(
            _enabled_config(),
            client_factory=lambda config: fake_client,
        )
        payload = build_curated_memory_payload("SPRTRN")
        payload["authoritative"] = True

        result = adapter.write_curated_memory(payload)

        self.assertFalse(result["success"])
        self.assertIn("authoritative=false", result["errors"][0])

    def test_search_request_generation(self) -> None:
        fake_client = FakeClient()
        adapter = OracleAgentMemoryPrototypeAdapter(
            _enabled_config(),
            client_factory=lambda config: fake_client,
        )

        result = adapter.search_memory("io pressure", db_name="SPRTRN", limit=3)

        self.assertTrue(result["success"])
        self.assertEqual(result["query"], "io pressure")
        self.assertEqual(result["thread_id"], "awr-db-sprtrn")
        self.assertEqual(fake_client.searches[0]["thread_id"], "awr-db-sprtrn")
        self.assertEqual(fake_client.searches[0]["max_results"], 3)
        self.assertTrue(fake_client.searches[0]["exact_thread_match"])
        self.assertFalse(result["records"][0]["authoritative"])
        self.assertFalse(result["records"][0]["runtime_influence"])

    def test_run_prototype_preserves_isolation(self) -> None:
        fake_client = FakeClient()
        adapter = OracleAgentMemoryPrototypeAdapter(
            _enabled_config(),
            client_factory=lambda config: fake_client,
        )

        result = run_phase6n1_prototype(adapter=adapter)

        self.assertTrue(result["success"])
        self.assertEqual(result["thread_id"], "awr-db-sprtrn")
        self.assertEqual(result["memory_id"], "memory-1")
        self.assertFalse(result["authoritative"])
        self.assertFalse(result["runtime_influence"])
        self.assertEqual(set(result["search_results"].keys()), {"SPRTRN", "io pressure", "TUNE FIRST"})


if __name__ == "__main__":
    unittest.main()
