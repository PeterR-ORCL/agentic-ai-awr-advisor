#!/usr/bin/env python3
"""CLI helper for materializing approved Phase 6M knowledge artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from src.memory import memory_orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize an approved knowledge request into an inactive artifact.",
    )
    parser.add_argument("--request-id", required=True, type=int)
    parser.add_argument("--artifact-type", required=True)
    parser.add_argument("--classification")
    parser.add_argument("--summary")
    parser.add_argument("--details")
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

    result = memory_orchestrator.materialize_knowledge_artifact(
        request_id=args.request_id,
        artifact_type=args.artifact_type,
        artifact_classification=args.classification,
        artifact_summary=args.summary,
        artifact_details=args.details,
        created_by=args.actor,
        metadata=metadata,
    )
    _print_result(result)
    if not result.get("enabled"):
        return 0
    return 0 if result.get("success") else 1


def _print_result(result: dict[str, Any]) -> None:
    print("Knowledge Materialization:")
    print(f"  enabled: {str(bool(result.get('enabled'))).lower()}")
    if not result.get("enabled"):
        skipped = result.get("skipped") or []
        print(f"  skipped: {', '.join(skipped) if skipped else 'none'}")
        return
    print(f"  success: {str(bool(result.get('success'))).lower()}")
    if result.get("success"):
        print(f"  artifact_id: {result.get('artifact_id')}")
        print(f"  request_id: {result.get('request_id')}")
        print(f"  artifact_type: {result.get('artifact_type')}")
        print(f"  activation_status: {result.get('activation_status')}")
    elif result.get("errors"):
        print(f"  error: {result['errors'][0]}")
    for warning in result.get("warnings") or []:
        print(f"  warning: {warning}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
