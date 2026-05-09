#!/usr/bin/env python3
"""Read-only CLI for Phase 6 structured memory recall."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable

from src.memory import memory_orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect Phase 6 memory records through read-only recall APIs.",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--summary", action="store_true")
    target.add_argument("--runs", action="store_true")
    target.add_argument("--recommendations", action="store_true")
    target.add_argument("--actions", action="store_true")
    target.add_argument("--outcomes", action="store_true")
    target.add_argument("--feedback", action="store_true")
    target.add_argument("--unknown-signals", action="store_true")
    target.add_argument("--knowledge-requests", action="store_true")
    target.add_argument("--knowledge-artifacts", action="store_true")

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
    parser.add_argument(
        "--order",
        choices=("newest", "oldest"),
        default="newest",
        help="Recall ordering for collection results.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = _dispatch(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result.get("enabled", True):
        return 0
    return 0 if result.get("success") else 1


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.summary:
        return memory_orchestrator.recall_memory_summary(order=args.order)

    dispatch_table: list[tuple[str, Callable[..., dict[str, Any]], dict[str, Any]]] = [
        (
            "runs",
            memory_orchestrator.recall_run_history,
            {
                "db_name": args.db_name,
                "dbid": args.dbid,
                "source_file_name": args.source_file_name,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        (
            "recommendations",
            memory_orchestrator.recall_recommendation_history,
            {
                "run_history_id": args.run_history_id,
                "db_name": args.db_name,
                "recommendation_status": args.status,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        (
            "actions",
            memory_orchestrator.recall_action_history,
            {
                "run_history_id": args.run_history_id,
                "action_status": args.status,
                "action_type": args.type,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        (
            "outcomes",
            memory_orchestrator.recall_outcome_history,
            {
                "run_history_id": args.run_history_id,
                "action_history_id": args.action_history_id,
                "outcome_status": args.status,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        (
            "feedback",
            memory_orchestrator.recall_feedback_history,
            {
                "run_history_id": args.run_history_id,
                "feedback_type": args.type,
                "feedback_rating": args.status,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        (
            "unknown_signals",
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
        (
            "knowledge_requests",
            memory_orchestrator.recall_knowledge_requests,
            {
                "approval_status": args.status,
                "source_type": args.type,
                "run_history_id": args.run_history_id,
                "limit": args.limit,
                "order": args.order,
            },
        ),
        (
            "knowledge_artifacts",
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
    ]
    for flag_name, callback, kwargs in dispatch_table:
        if getattr(args, flag_name):
            return callback(**kwargs)
    return {
        "enabled": True,
        "success": False,
        "error": "no recall target selected",
        "records": [],
        "count": 0,
    }


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
