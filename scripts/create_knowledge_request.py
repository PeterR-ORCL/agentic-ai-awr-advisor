#!/usr/bin/env python3
"""CLI helper for creating Phase 6L knowledge update approval requests."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from src.memory import memory_orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a pending knowledge update governance request.",
    )
    parser.add_argument("--source-type", required=True)
    parser.add_argument("--source-id", required=True, type=int)
    parser.add_argument("--classification")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--details")
    parser.add_argument("--run-history-id", type=int)
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

    result = memory_orchestrator.create_knowledge_update_request(
        source_type=args.source_type,
        source_id=args.source_id,
        candidate_classification=args.classification,
        candidate_summary=args.summary,
        candidate_details=args.details,
        run_history_id=args.run_history_id,
        created_by=args.actor,
        metadata=metadata,
    )
    _print_result(result)
    if not result.get("enabled"):
        return 0
    return 0 if result.get("success") else 1


def _print_result(result: dict[str, Any]) -> None:
    print("Knowledge Update Request:")
    print(f"  enabled: {str(bool(result.get('enabled'))).lower()}")
    if not result.get("enabled"):
        skipped = result.get("skipped") or []
        print(f"  skipped: {', '.join(skipped) if skipped else 'none'}")
        return
    print(f"  success: {str(bool(result.get('success'))).lower()}")
    if result.get("success"):
        print(f"  request_id: {result.get('request_id')}")
        print(f"  source_type: {result.get('source_type')}")
        print(f"  source_id: {result.get('source_id')}")
        print(f"  approval_status: {result.get('approval_status')}")
    elif result.get("errors"):
        print(f"  error: {result['errors'][0]}")
    for warning in result.get("warnings") or []:
        print(f"  warning: {warning}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
