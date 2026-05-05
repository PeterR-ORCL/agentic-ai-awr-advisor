#!/usr/bin/env python3
"""CLI helper for reviewing Phase 6 unknown parser signals."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from src.memory import memory_orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record human review metadata for a captured unknown signal.",
    )
    parser.add_argument("--unknown-signal-id", required=True, type=int)
    parser.add_argument("--review-status", required=True)
    parser.add_argument("--review-classification")
    parser.add_argument("--review-notes")
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

    result = memory_orchestrator.review_unknown_signal(
        unknown_signal_id=args.unknown_signal_id,
        review_status=args.review_status,
        review_classification=args.review_classification,
        review_notes=args.review_notes,
        reviewed_by=args.actor,
        metadata=metadata,
    )
    _print_result(result)
    if not result.get("enabled"):
        return 0
    return 0 if result.get("success") else 1


def _print_result(result: dict[str, Any]) -> None:
    print("Unknown Signal Review:")
    print(f"  enabled: {str(bool(result.get('enabled'))).lower()}")
    if not result.get("enabled"):
        skipped = result.get("skipped") or []
        print(f"  skipped: {', '.join(skipped) if skipped else 'none'}")
        return
    print(f"  success: {str(bool(result.get('success'))).lower()}")
    if result.get("success"):
        print(f"  unknown_signal_id: {result.get('unknown_signal_id')}")
        print(f"  review_status: {result.get('review_status')}")
        print(f"  review_classification: {result.get('review_classification')}")
    elif result.get("errors"):
        print(f"  error: {result['errors'][0]}")
    for warning in result.get("warnings") or []:
        print(f"  warning: {warning}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
