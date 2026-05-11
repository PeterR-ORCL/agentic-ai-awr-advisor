"""Curated semantic recall service for Phase 6N.3.

Semantic recall is non-authoritative analyst-assist context only.
It must never influence deterministic runtime diagnosis,
scoring, recommendations, governance approvals,
or dashboard truth.
"""

from __future__ import annotations

import json
import re
from typing import Any

from src.memory.oracle_agent_memory_adapter import (
    DEFAULT_DB_NAME,
    OracleAgentMemoryPrototypeAdapter,
)

SEMANTIC_ONLY_FLAGS = {
    "authoritative": False,
    "runtime_influence": False,
    "semantic_only": True,
}
MAX_RECALL_LIMIT = 25


def recall_by_db_name(
    db_name: str,
    limit: int = 5,
    *,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Recall curated semantic context by database name."""

    return _recall(
        query=db_name,
        limit=limit,
        rank_context="db_name",
        db_name=db_name,
        adapter=adapter,
    )


def recall_by_issue_type(
    issue_type: str,
    limit: int = 5,
    *,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Recall curated semantic context by issue type."""

    return _recall(
        query=issue_type,
        limit=limit,
        rank_context="issue_type",
        db_name=DEFAULT_DB_NAME,
        adapter=adapter,
    )


def recall_by_posture(
    posture: str,
    limit: int = 5,
    *,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Recall curated semantic context by deterministic posture text."""

    return _recall(
        query=posture,
        limit=limit,
        rank_context="posture",
        db_name=DEFAULT_DB_NAME,
        adapter=adapter,
    )


def recall_related_context(
    query: str,
    limit: int = 5,
    *,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Recall curated semantic context for analyst assistance only."""

    return _recall(
        query=query,
        limit=limit,
        rank_context="general",
        db_name=DEFAULT_DB_NAME,
        adapter=adapter,
    )


def build_curated_semantic_summary(
    query: str,
    limit: int = 5,
    *,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Build a non-authoritative semantic summary from recalled memories."""

    recall_result = recall_related_context(query, limit=limit, adapter=adapter)
    records = recall_result.get("records", [])
    summary = _summarize_records(records)
    return {
        "enabled": recall_result.get("enabled", True),
        "success": recall_result.get("success", False),
        "query": query,
        "summary": summary,
        "records": records,
        "count": len(records),
        **SEMANTIC_ONLY_FLAGS,
        "errors": recall_result.get("errors", []),
        "skipped": recall_result.get("skipped", []),
    }


def _recall(
    *,
    query: str,
    limit: int,
    rank_context: str,
    db_name: str,
    adapter: OracleAgentMemoryPrototypeAdapter | None,
) -> dict[str, Any]:
    normalized_query = str(query or "").strip()
    if not normalized_query:
        return {
            "enabled": True,
            "success": False,
            "query": normalized_query,
            "count": 0,
            "records": [],
            **SEMANTIC_ONLY_FLAGS,
            "errors": ["query is required for semantic recall"],
        }

    bounded_limit = _bounded_limit(limit)
    search_limit = min(max(bounded_limit * 3, bounded_limit), MAX_RECALL_LIMIT)
    recall_adapter = adapter or OracleAgentMemoryPrototypeAdapter()
    close_adapter = adapter is None
    try:
        raw_result = recall_adapter.search_memory(
            normalized_query,
            db_name=db_name or DEFAULT_DB_NAME,
            limit=search_limit,
        )
        if not raw_result.get("enabled", True):
            return {
                "enabled": False,
                "success": True,
                "query": normalized_query,
                "count": 0,
                "records": [],
                **SEMANTIC_ONLY_FLAGS,
                "skipped": raw_result.get("skipped", ["oracle_agent_memory_disabled"]),
                "errors": raw_result.get("errors", []),
            }
        if not raw_result.get("success"):
            return {
                "enabled": True,
                "success": False,
                "query": normalized_query,
                "count": 0,
                "records": [],
                **SEMANTIC_ONLY_FLAGS,
                "error": raw_result.get("error"),
                "errors": raw_result.get("errors", []),
            }

        ranked_records = _rank_records(
            raw_result.get("records", []),
            normalized_query,
            rank_context,
        )[:bounded_limit]
        return {
            "enabled": True,
            "success": True,
            "query": normalized_query,
            "count": len(ranked_records),
            "records": ranked_records,
            **SEMANTIC_ONLY_FLAGS,
            "errors": [],
        }
    finally:
        if close_adapter and hasattr(recall_adapter, "close"):
            recall_adapter.close()


def _rank_records(
    records: list[dict[str, Any]],
    query: str,
    rank_context: str,
) -> list[dict[str, Any]]:
    normalized_query = _normalize_match_text(query)

    def rank_key(indexed_record: tuple[int, dict[str, Any]]) -> tuple[int, int]:
        index, record = indexed_record
        payload = _record_payload(record)
        exact_match = _record_exact_match(payload, normalized_query, rank_context)
        return (0 if exact_match else 1, index)

    ranked = [
        _decorate_semantic_record(record)
        for _, record in sorted(enumerate(records), key=rank_key)
    ]
    return ranked


def _record_exact_match(
    payload: dict[str, Any],
    normalized_query: str,
    rank_context: str,
) -> bool:
    if rank_context == "db_name":
        return _normalize_match_text(payload.get("db_name")) == normalized_query
    if rank_context == "posture":
        return _normalize_match_text(payload.get("posture")) == normalized_query
    if rank_context == "issue_type":
        issue_values = [
            payload.get("primary_issue"),
            payload.get("secondary_issue"),
            payload.get("issue_type"),
        ]
        return any(_normalize_match_text(value) == normalized_query for value in issue_values)
    return False


def _decorate_semantic_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        **SEMANTIC_ONLY_FLAGS,
    }


def _summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    payloads = [_record_payload(record) for record in records]
    matched_db_names = _unique_sorted(payload.get("db_name") for payload in payloads)
    matched_postures = _unique_sorted(payload.get("posture") for payload in payloads)
    matched_issue_types = _unique_sorted(
        value
        for payload in payloads
        for value in (
            payload.get("primary_issue"),
            payload.get("secondary_issue"),
            payload.get("issue_type"),
        )
    )
    themes = _build_themes(matched_issue_types, matched_postures)
    observations = _build_observations(matched_db_names, matched_issue_types, matched_postures)
    return {
        "themes": themes,
        "matched_db_names": matched_db_names,
        "matched_postures": matched_postures,
        "matched_issue_types": matched_issue_types,
        "observations": observations,
    }


def _build_themes(issue_types: list[str], postures: list[str]) -> list[str]:
    themes = []
    for issue_type in issue_types:
        themes.append(f"semantic recall suggests prior entries referenced {issue_type}")
    for posture in postures:
        themes.append(f"historical semantic entries referenced posture {posture}")
    return themes


def _build_observations(
    db_names: list[str],
    issue_types: list[str],
    postures: list[str],
) -> list[str]:
    observations = []
    if db_names:
        observations.append(
            "retrieved memory context indicates DB names referenced in semantic entries: "
            + ", ".join(db_names)
        )
    if issue_types:
        observations.append(
            "semantic recall suggests repeated issue patterns: " + ", ".join(issue_types)
        )
    if postures:
        observations.append(
            "historical semantic entries referenced posture patterns: " + ", ".join(postures)
        )
    if not observations:
        observations.append("semantic recall returned no curated observations for this query")
    return observations


def _record_payload(record: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    content = record.get("content")
    if isinstance(content, str):
        try:
            decoded = json.loads(content)
            if isinstance(decoded, dict):
                payload.update(decoded)
        except json.JSONDecodeError:
            payload.update(_payload_from_free_text(content))
    elif isinstance(content, dict):
        payload.update(content)
    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        payload = {**metadata, **payload}
    return payload


def _payload_from_free_text(content: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    db_match = re.search(r"\b[A-Z][A-Z0-9_]{2,}\b", content)
    if db_match:
        payload["db_name"] = db_match.group(0)
    normalized_content = _normalize_match_text(content)
    for issue in ("io_pressure", "commit_pressure", "cpu_pressure", "memory_pressure"):
        if _normalize_match_text(issue) in normalized_content:
            payload.setdefault("primary_issue", issue)
    if "tune first" in normalized_content:
        payload["posture"] = "TUNE FIRST"
    return payload


def _unique_sorted(values: Any) -> list[str]:
    cleaned = {str(value).strip() for value in values if str(value or "").strip()}
    return sorted(cleaned)


def _bounded_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = 5
    return max(1, min(value, MAX_RECALL_LIMIT))


def _normalize_match_text(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", " ")
    return " ".join(text.split())
