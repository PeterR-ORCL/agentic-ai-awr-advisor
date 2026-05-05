#!/usr/bin/env python3
"""CLI helper for recording Phase 6 human/operator feedback."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from src.memory import memory_orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record human/operator feedback for an AWR advisory run.",
    )
    parser.add_argument("--run-history-id", required=True, type=int)
    parser.add_argument("--recommendation-history-id", type=int)
    parser.add_argument("--action-history-id", type=int)
    parser.add_argument("--action-outcome-id", type=int)
    parser.add_argument("--feedback-type", required=True)
    parser.add_argument("--feedback-rating", required=True)
    parser.add_argument("--feedback-summary", required=True)
    parser.add_argument("--feedback-detail")
    parser.add_argument("--feedback-source")
    parser.add_argument("--actor")
    parser.add_argument("--metadata")
    return parser


def parse_metadata(raw_metadata: str | None) -> dict[str, Any] | None:
    if raw_metadata is None:
        return None
    try:
        parsed = json.loads(raw_metadata)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"--metadata must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("--metadata must be a JSON object")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metadata = parse_metadata(args.metadata)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    result = memory_orchestrator.record_feedback(
        run_history_id=args.run_history_id,
        recommendation_history_id=args.recommendation_history_id,
        action_history_id=args.action_history_id,
        action_outcome_id=args.action_outcome_id,
        feedback_type=args.feedback_type,
        feedback_rating=args.feedback_rating,
        feedback_summary=args.feedback_summary,
        feedback_detail=args.feedback_detail,
        feedback_source=args.feedback_source,
        recorded_by=args.actor,
        metadata=metadata,
    )
    _print_result(result)
    if not result.get("enabled"):
        return 0
    return 0 if result.get("success") else 1


def _print_result(result: dict[str, Any]) -> None:
    print("Feedback Capture:")
    print(f"  enabled: {str(bool(result.get('enabled'))).lower()}")
    if not result.get("enabled"):
        skipped = result.get("skipped") or []
        print(f"  skipped: {', '.join(skipped) if skipped else 'none'}")
        return
    print(f"  success: {str(bool(result.get('success'))).lower()}")
    if result.get("success"):
        print(f"  feedback_id: {result.get('feedback_id')}")
        print(f"  run_history_id: {result.get('run_history_id')}")
        print(f"  feedback_type: {result.get('feedback_type')}")
        print(f"  feedback_rating: {result.get('feedback_rating')}")
    elif result.get("errors"):
        print(f"  error: {result['errors'][0]}")
    for warning in result.get("warnings") or []:
        print(f"  warning: {warning}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
