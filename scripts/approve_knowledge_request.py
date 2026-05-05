#!/usr/bin/env python3
"""CLI helper for approving Phase 6L knowledge update requests."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from src.memory import memory_orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update approval metadata for a knowledge update request.",
    )
    parser.add_argument("--request-id", required=True, type=int)
    parser.add_argument("--approval-status", required=True)
    parser.add_argument("--actor")
    parser.add_argument("--notes")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = memory_orchestrator.approve_knowledge_update_request(
        request_id=args.request_id,
        approval_status=args.approval_status,
        approved_by=args.actor,
        approval_notes=args.notes,
    )
    _print_result(result)
    if not result.get("enabled"):
        return 0
    return 0 if result.get("success") else 1


def _print_result(result: dict[str, Any]) -> None:
    print("Knowledge Request Approval:")
    print(f"  enabled: {str(bool(result.get('enabled'))).lower()}")
    if not result.get("enabled"):
        skipped = result.get("skipped") or []
        print(f"  skipped: {', '.join(skipped) if skipped else 'none'}")
        return
    print(f"  success: {str(bool(result.get('success'))).lower()}")
    if result.get("success"):
        print(f"  request_id: {result.get('request_id')}")
        print(f"  approval_status: {result.get('approval_status')}")
    elif result.get("errors"):
        print(f"  error: {result['errors'][0]}")
    for warning in result.get("warnings") or []:
        print(f"  warning: {warning}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
