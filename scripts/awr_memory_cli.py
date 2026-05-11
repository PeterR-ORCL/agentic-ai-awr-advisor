#!/usr/bin/env python3
"""Unified Phase 6 memory, governance, recall, and semantic-assist CLI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable

from src.memory import memory_orchestrator
from src.memory.oracle_agent_memory_adapter import load_config_from_env
from src.memory import governance_semantic_assist, semantic_recall_service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified Phase 6 operational CLI for memory, governance, recall, and semantic assist.",
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    parser.add_argument("--format", choices=("json",), default="json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_recall_commands(subparsers)
    _add_review_commands(subparsers)
    _add_governance_commands(subparsers)
    _add_artifact_commands(subparsers)
    _add_semantic_commands(subparsers)
    subparsers.add_parser("status", help="Show overall Phase 6 operational status.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = dispatch(args)
    _print_json(result, compact=bool(args.compact))
    if not result.get("enabled", True):
        return 0
    return 0 if result.get("success", False) else 1


def dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "status":
        return _status_result()
    if args.command == "recall":
        return _dispatch_recall(args)
    if args.command == "review":
        return _dispatch_review(args)
    if args.command == "governance":
        return _dispatch_governance(args)
    if args.command == "artifact":
        return _dispatch_artifact(args)
    if args.command == "semantic":
        return _dispatch_semantic(args)
    return _error("unknown command")


def _add_recall_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    recall = subparsers.add_parser("recall", help="Read-only structured memory recall.")
    recall_sub = recall.add_subparsers(dest="recall_command", required=True)
    for name in (
        "summary",
        "runs",
        "recommendations",
        "actions",
        "outcomes",
        "feedback",
        "unknown-signals",
        "knowledge-requests",
        "knowledge-artifacts",
    ):
        command = recall_sub.add_parser(name)
        _add_common_recall_filters(command)


def _add_review_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    review = subparsers.add_parser("review", help="Explicit parser review operations.")
    review_sub = review.add_subparsers(dest="review_command", required=True)
    unknown = review_sub.add_parser("unknown-signal")
    unknown.add_argument("--unknown-signal-id", required=True, type=int)
    unknown.add_argument("--review-status", required=True)
    unknown.add_argument("--review-classification")
    unknown.add_argument("--review-notes")
    unknown.add_argument("--actor", required=True)
    unknown.add_argument("--metadata", type=_json_object)


def _add_governance_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    governance = subparsers.add_parser("governance", help="Explicit governance operations.")
    governance_sub = governance.add_subparsers(dest="governance_command", required=True)

    create = governance_sub.add_parser("create-request")
    create.add_argument("--source-type", required=True)
    create.add_argument("--source-id", required=True, type=int)
    create.add_argument("--classification")
    create.add_argument("--summary", required=True)
    create.add_argument("--details")
    create.add_argument("--run-history-id", type=int)
    create.add_argument("--actor", required=True)
    create.add_argument("--metadata", type=_json_object)

    approve = governance_sub.add_parser("approve-request")
    approve.add_argument("--request-id", required=True, type=int)
    approve.add_argument("--approval-status", required=True)
    approve.add_argument("--actor", required=True)
    approve.add_argument("--notes")


def _add_artifact_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    artifact = subparsers.add_parser("artifact", help="Knowledge artifact operations.")
    artifact_sub = artifact.add_subparsers(dest="artifact_command", required=True)

    materialize = artifact_sub.add_parser("materialize")
    materialize.add_argument("--request-id", required=True, type=int)
    materialize.add_argument("--artifact-type", required=True)
    materialize.add_argument("--classification")
    materialize.add_argument("--summary")
    materialize.add_argument("--details")
    materialize.add_argument("--actor", required=True)
    materialize.add_argument("--metadata", type=_json_object)

    list_cmd = artifact_sub.add_parser("list")
    list_cmd.add_argument("--status")
    list_cmd.add_argument("--type")
    list_cmd.add_argument("--classification")
    list_cmd.add_argument("--run-history-id", type=int)
    list_cmd.add_argument("--limit", type=int, default=10)
    list_cmd.add_argument("--order", choices=("newest", "oldest"), default="newest")


def _add_semantic_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    semantic = subparsers.add_parser("semantic", help="Read-only semantic recall and reviewer assist.")
    semantic_sub = semantic.add_subparsers(dest="semantic_command", required=True)

    semantic_sub.add_parser("status")

    recall = semantic_sub.add_parser("recall")
    recall.add_argument("--query", required=True)
    recall.add_argument("--limit", type=int, default=5)

    unknown = semantic_sub.add_parser("assist-unknown-signal")
    unknown.add_argument("--unknown-signal-id", required=True, type=int)
    unknown.add_argument("--limit", type=int, default=5)

    knowledge = semantic_sub.add_parser("assist-knowledge-request")
    knowledge.add_argument("--request-id", type=int)
    knowledge.add_argument("--source-type")
    knowledge.add_argument("--source-id", type=int)
    knowledge.add_argument("--classification")
    knowledge.add_argument("--summary")
    knowledge.add_argument("--db-name")
    knowledge.add_argument("--posture")
    knowledge.add_argument("--limit", type=int, default=5)

    artifact = semantic_sub.add_parser("assist-artifact")
    artifact.add_argument("--artifact-id", type=int)
    artifact.add_argument("--artifact-type")
    artifact.add_argument("--classification")
    artifact.add_argument("--summary")
    artifact.add_argument("--db-name")
    artifact.add_argument("--limit", type=int, default=5)

    parser_review = semantic_sub.add_parser("assist-parser-governance")
    parser_review.add_argument("--parser-stage")
    parser_review.add_argument("--classification-hint")
    parser_review.add_argument("--section-context")
    parser_review.add_argument("--db-name")
    parser_review.add_argument("--detection-reason")
    parser_review.add_argument("--limit", type=int, default=5)


def _add_common_recall_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-history-id", type=int)
    parser.add_argument("--action-history-id", type=int)
    parser.add_argument("--db-name")
    parser.add_argument("--dbid")
    parser.add_argument("--source-file-name")
    parser.add_argument("--section-name")
    parser.add_argument("--status")
    parser.add_argument("--type")
    parser.add_argument("--classification")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--order", choices=("newest", "oldest"), default="newest")


def _dispatch_recall(args: argparse.Namespace) -> dict[str, Any]:
    command = args.recall_command
    if command == "summary":
        return memory_orchestrator.recall_memory_summary(order=args.order)
    recall_map: dict[str, tuple[Callable[..., dict[str, Any]], dict[str, Any]]] = {
        "runs": (
            memory_orchestrator.recall_run_history,
            {
                "db_name": args.db_name,
                "dbid": args.dbid,
                "source_file_name": args.source_file_name,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        "recommendations": (
            memory_orchestrator.recall_recommendation_history,
            {
                "run_history_id": args.run_history_id,
                "db_name": args.db_name,
                "recommendation_status": args.status,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        "actions": (
            memory_orchestrator.recall_action_history,
            {
                "run_history_id": args.run_history_id,
                "action_status": args.status,
                "action_type": args.type,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        "outcomes": (
            memory_orchestrator.recall_outcome_history,
            {
                "run_history_id": args.run_history_id,
                "action_history_id": args.action_history_id,
                "outcome_status": args.status,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        "feedback": (
            memory_orchestrator.recall_feedback_history,
            {
                "run_history_id": args.run_history_id,
                "feedback_type": args.type,
                "feedback_rating": args.status,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        "unknown-signals": (
            memory_orchestrator.recall_unknown_signals,
            {
                "review_status": args.status,
                "review_classification": args.classification,
                "db_name": args.db_name,
                "section_name": args.section_name,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        "knowledge-requests": (
            memory_orchestrator.recall_knowledge_requests,
            {
                "approval_status": args.status,
                "source_type": args.type,
                "run_history_id": args.run_history_id,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        "knowledge-artifacts": (
            memory_orchestrator.recall_knowledge_artifacts,
            {
                "activation_status": args.status,
                "artifact_type": args.type,
                "artifact_classification": args.classification,
                "run_history_id": args.run_history_id,
                "limit": args.limit,
                "order": args.order,
            },
        ),
    }
    callback, kwargs = recall_map[command]
    return callback(**kwargs)


def _dispatch_review(args: argparse.Namespace) -> dict[str, Any]:
    if args.review_command != "unknown-signal":
        return _error("unknown review command")
    return memory_orchestrator.review_unknown_signal(
        unknown_signal_id=args.unknown_signal_id,
        review_status=args.review_status,
        review_classification=args.review_classification,
        review_notes=args.review_notes,
        reviewed_by=args.actor,
        metadata=args.metadata,
    )


def _dispatch_governance(args: argparse.Namespace) -> dict[str, Any]:
    if args.governance_command == "create-request":
        return memory_orchestrator.create_knowledge_update_request(
            source_type=args.source_type,
            source_id=args.source_id,
            candidate_classification=args.classification,
            candidate_summary=args.summary,
            candidate_details=args.details,
            run_history_id=args.run_history_id,
            created_by=args.actor,
            metadata=args.metadata,
        )
    if args.governance_command == "approve-request":
        return memory_orchestrator.approve_knowledge_update_request(
            request_id=args.request_id,
            approval_status=args.approval_status,
            approved_by=args.actor,
            approval_notes=args.notes,
        )
    return _error("unknown governance command")


def _dispatch_artifact(args: argparse.Namespace) -> dict[str, Any]:
    if args.artifact_command == "materialize":
        return memory_orchestrator.materialize_knowledge_artifact(
            request_id=args.request_id,
            artifact_type=args.artifact_type,
            artifact_classification=args.classification,
            artifact_summary=args.summary,
            artifact_details=args.details,
            created_by=args.actor,
            metadata=args.metadata,
        )
    if args.artifact_command == "list":
        return memory_orchestrator.recall_knowledge_artifacts(
            activation_status=args.status,
            artifact_type=args.type,
            artifact_classification=args.classification,
            run_history_id=args.run_history_id,
            limit=args.limit,
            order=args.order,
        )
    return _error("unknown artifact command")


def _dispatch_semantic(args: argparse.Namespace) -> dict[str, Any]:
    if args.semantic_command == "status":
        return _semantic_status_result()
    if args.semantic_command == "recall":
        return semantic_recall_service.recall_related_context(args.query, limit=args.limit)
    if args.semantic_command == "assist-unknown-signal":
        unknown_signal = _recall_unknown_signal_by_id(args.unknown_signal_id)
        if not unknown_signal.get("success"):
            return unknown_signal
        return governance_semantic_assist.assist_unknown_signal_review(
            unknown_signal["record"],
            limit=args.limit,
        )
    if args.semantic_command == "assist-knowledge-request":
        return governance_semantic_assist.assist_knowledge_request_review(
            {
                "REQUEST_ID": args.request_id,
                "SOURCE_TYPE": args.source_type,
                "SOURCE_ID": args.source_id,
                "CANDIDATE_CLASSIFICATION": args.classification,
                "CANDIDATE_SUMMARY": args.summary,
                "DB_NAME": args.db_name,
                "POSTURE": args.posture,
            },
            limit=args.limit,
        )
    if args.semantic_command == "assist-artifact":
        return governance_semantic_assist.assist_artifact_review(
            {
                "ARTIFACT_ID": args.artifact_id,
                "ARTIFACT_TYPE": args.artifact_type,
                "ARTIFACT_CLASSIFICATION": args.classification,
                "ARTIFACT_SUMMARY": args.summary,
                "DB_NAME": args.db_name,
            },
            limit=args.limit,
        )
    if args.semantic_command == "assist-parser-governance":
        return governance_semantic_assist.assist_parser_governance_review(
            {
                "PARSER_STAGE": args.parser_stage,
                "CLASSIFICATION_HINT": args.classification_hint,
                "SECTION_NAME": args.section_context,
                "DB_NAME": args.db_name,
                "DETECTION_REASON": args.detection_reason,
            },
            limit=args.limit,
        )
    return _error("unknown semantic command")


def _recall_unknown_signal_by_id(unknown_signal_id: int) -> dict[str, Any]:
    result = memory_orchestrator.recall_unknown_signals(limit=500, order="newest")
    if not result.get("enabled", True):
        return result
    if not result.get("success"):
        return result
    for record in result.get("records", []):
        if _record_int(record, "UNKNOWN_SIGNAL_ID", "unknown_signal_id") == int(unknown_signal_id):
            return {
                "enabled": True,
                "success": True,
                "record": record,
                "authoritative": False,
                "runtime_influence": False,
                "semantic_only": True,
                "reviewer_assist_only": True,
            }
    return {
        "enabled": True,
        "success": False,
        "error": f"unknown_signal_id {unknown_signal_id} was not found",
        "records": [],
        "errors": [f"unknown_signal_id {unknown_signal_id} was not found"],
    }


def _status_result() -> dict[str, Any]:
    summary = memory_orchestrator.recall_memory_summary()
    semantic_status = _semantic_status_result()
    return {
        "enabled": summary.get("enabled", True),
        "success": bool(summary.get("success", False) and semantic_status.get("success", False)),
        "memory_enabled": bool(summary.get("enabled", True)),
        "structured_recall_available": bool(summary.get("success", False)),
        "semantic_recall_enabled": bool(semantic_status.get("semantic_recall_enabled")),
        "governance_apis_available": True,
        "artifact_apis_available": True,
        "runtime_influence": False,
        "semantic_authoritative": False,
        "summary": summary.get("summary"),
        "semantic": semantic_status,
        "errors": list(summary.get("errors", [])) + list(semantic_status.get("errors", [])),
    }


def _semantic_status_result() -> dict[str, Any]:
    config = load_config_from_env()
    missing = []
    if config.enabled:
        adapter = __import__(
            "src.memory.oracle_agent_memory_adapter",
            fromlist=["OracleAgentMemoryPrototypeAdapter"],
        ).OracleAgentMemoryPrototypeAdapter(config)
        missing = adapter.validate_config()
    return {
        "enabled": True,
        "success": True,
        "semantic_recall_enabled": bool(config.enabled),
        "provider": "Oracle Agent Memory",
        "mode": "curated semantic recall",
        "authoritative": False,
        "runtime_influence": False,
        "semantic_only": True,
        "reviewer_assist_only": True,
        "missing_configuration": missing,
        "skipped": [] if config.enabled else ["oracle_agent_memory_disabled"],
    }


def _record_int(record: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        if key in record:
            try:
                return int(record[key])
            except (TypeError, ValueError):
                return None
    return None


def _json_object(raw_value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("must be a JSON object")
    return parsed


def _print_json(result: dict[str, Any], *, compact: bool) -> None:
    if compact:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))


def _error(message: str) -> dict[str, Any]:
    return {
        "enabled": True,
        "success": False,
        "error": message,
        "errors": [message],
    }


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
