"""Governance-assisted semantic recall for Phase 6N.4.

Governance semantic assistance is non-authoritative reviewer context only.
It must never determine governance outcomes,
approval status, parser classification,
runtime diagnosis, scoring, recommendations,
or dashboard truth.
"""

from __future__ import annotations

from typing import Any

from src.memory.oracle_agent_memory_adapter import OracleAgentMemoryPrototypeAdapter
from src.memory.semantic_recall_service import (
    build_curated_semantic_summary,
    semantic_boundary_flags,
)

REVIEWER_ASSIST_FLAGS = {
    **semantic_boundary_flags(),
    "reviewer_assist_only": True,
}


def assist_unknown_signal_review(
    unknown_signal: dict,
    limit: int = 5,
    *,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Retrieve non-authoritative semantic context for unknown signal review."""

    query_context = _query_context(
        unknown_signal,
        {
            "section_name": ("SECTION_NAME", "section_name", "section"),
            "unknown_type": ("UNKNOWN_TYPE", "unknown_type", "type"),
            "db_name": ("DB_NAME", "db_name"),
            "detection_reason": ("DETECTION_REASON", "detection_reason", "reason"),
        },
    )
    return _assist(
        review_type="unknown_signal",
        query_context=query_context,
        limit=limit,
        adapter=adapter,
    )


def assist_knowledge_request_review(
    request: dict,
    limit: int = 5,
    *,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Retrieve non-authoritative semantic context for knowledge request review."""

    query_context = _query_context(
        request,
        {
            "candidate_classification": (
                "CANDIDATE_CLASSIFICATION",
                "candidate_classification",
                "classification",
            ),
            "issue_type": ("ISSUE_TYPE", "issue_type", "primary_issue"),
            "db_name": ("DB_NAME", "db_name"),
            "posture": ("POSTURE", "posture"),
            "source_type": ("SOURCE_TYPE", "source_type"),
            "candidate_summary": ("CANDIDATE_SUMMARY", "candidate_summary", "summary"),
        },
    )
    return _assist(
        review_type="knowledge_request",
        query_context=query_context,
        limit=limit,
        adapter=adapter,
    )


def assist_artifact_review(
    artifact: dict,
    limit: int = 5,
    *,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Retrieve non-authoritative semantic context for artifact review."""

    query_context = _query_context(
        artifact,
        {
            "artifact_type": ("ARTIFACT_TYPE", "artifact_type"),
            "artifact_classification": (
                "ARTIFACT_CLASSIFICATION",
                "artifact_classification",
                "classification",
            ),
            "issue_type": ("ISSUE_TYPE", "issue_type", "primary_issue"),
            "db_name": ("DB_NAME", "db_name"),
            "artifact_summary": ("ARTIFACT_SUMMARY", "artifact_summary", "summary"),
        },
    )
    return _assist(
        review_type="artifact",
        query_context=query_context,
        limit=limit,
        adapter=adapter,
    )


def assist_parser_governance_review(
    parser_context: dict,
    limit: int = 5,
    *,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Retrieve non-authoritative semantic context for parser governance review."""

    query_context = _query_context(
        parser_context,
        {
            "parser_stage": ("PARSER_STAGE", "parser_stage", "stage"),
            "classification_hint": (
                "CLASSIFICATION_HINT",
                "classification_hint",
                "candidate_classification",
            ),
            "section_context": ("SECTION_NAME", "section_name", "section_context", "section"),
            "db_name": ("DB_NAME", "db_name"),
            "detection_reason": ("DETECTION_REASON", "detection_reason", "reason"),
        },
    )
    return _assist(
        review_type="parser_governance",
        query_context=query_context,
        limit=limit,
        adapter=adapter,
    )


def _assist(
    *,
    review_type: str,
    query_context: dict[str, Any],
    limit: int,
    adapter: OracleAgentMemoryPrototypeAdapter | None,
) -> dict[str, Any]:
    query = _build_query(query_context)
    if not query:
        return {
            "enabled": True,
            "success": False,
            "review_type": review_type,
            "query_context": query_context,
            "semantic_context": _empty_semantic_context(),
            "records": [],
            **REVIEWER_ASSIST_FLAGS,
            "errors": ["semantic assist query context is required"],
        }

    summary_result = build_curated_semantic_summary(query, limit=limit, adapter=adapter)
    semantic_context = summary_result.get("summary") or _empty_semantic_context()
    return {
        "enabled": summary_result.get("enabled", True),
        "success": summary_result.get("success", False),
        "review_type": review_type,
        "query_context": query_context,
        "query": query,
        "semantic_context": semantic_context,
        "records": summary_result.get("records", []),
        "count": summary_result.get("count", 0),
        **REVIEWER_ASSIST_FLAGS,
        "errors": summary_result.get("errors", []),
        "skipped": summary_result.get("skipped", []),
    }


def _query_context(source: dict, field_map: dict[str, tuple[str, ...]]) -> dict[str, Any]:
    return {
        output_key: _first_present(source, aliases)
        for output_key, aliases in field_map.items()
    }


def _first_present(source: dict, aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        value = source.get(alias)
        if value not in (None, "", [], {}):
            return value
    return None


def _build_query(query_context: dict[str, Any]) -> str:
    parts = [
        str(value).strip()
        for value in query_context.values()
        if str(value or "").strip()
    ]
    return " ".join(parts)


def _empty_semantic_context() -> dict[str, list[Any]]:
    return {
        "matched_db_names": [],
        "matched_issue_types": [],
        "matched_postures": [],
        "themes": [],
        "observations": [],
    }
