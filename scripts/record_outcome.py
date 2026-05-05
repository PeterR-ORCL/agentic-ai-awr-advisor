#!/usr/bin/env python3
"""CLI helper for recording Phase 6 action outcome history rows."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from src.memory import memory_orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record an observed outcome for a previously recorded AWR action.",
    )
    parser.add_argument("--run-history-id", required=True, type=int)
    parser.add_argument("--action-history-id", required=True, type=int)
    parser.add_argument("--outcome-status", required=True)
    parser.add_argument("--outcome-summary", required=True)
    parser.add_argument("--impact-score", type=float)
    parser.add_argument("--actor")
    parser.add_argument("--before-metrics")
    parser.add_argument("--after-metrics")
    parser.add_argument("--notes")
    return parser


def parse_json_object(raw_value: str | None, flag_name: str) -> dict[str, Any] | None:
    if raw_value is None:
        return None
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{flag_name} must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError(f"{flag_name} must be a JSON object")
    return parsed


def parse_notes(raw_notes: str | None) -> dict[str, Any] | str | None:
    if raw_notes is None:
        return None
    text = raw_notes.strip()
    if not text:
        return None
    if not text.startswith("{"):
        return text
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    return parsed if isinstance(parsed, dict) else text


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        before_metrics = parse_json_object(args.before_metrics, "--before-metrics")
        after_metrics = parse_json_object(args.after_metrics, "--after-metrics")
        notes = parse_notes(args.notes)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    result = memory_orchestrator.record_outcome(
        run_history_id=args.run_history_id,
        action_history_id=args.action_history_id,
        outcome_status=args.outcome_status,
        outcome_summary=args.outcome_summary,
        before_metrics=before_metrics,
        after_metrics=after_metrics,
        impact_score=args.impact_score,
        recorded_by=args.actor,
        notes=notes,
    )
    _print_result(result)
    if not result.get("enabled"):
        return 0
    return 0 if result.get("success") else 1


def _print_result(result: dict[str, Any]) -> None:
    print("Outcome Tracking:")
    print(f"  enabled: {str(bool(result.get('enabled'))).lower()}")
    if not result.get("enabled"):
        skipped = result.get("skipped") or []
        print(f"  skipped: {', '.join(skipped) if skipped else 'none'}")
        return
    print(f"  success: {str(bool(result.get('success'))).lower()}")
    if result.get("success"):
        print(f"  outcome_id: {result.get('outcome_id')}")
        print(f"  run_history_id: {result.get('run_history_id')}")
        print(f"  action_history_id: {result.get('action_history_id')}")
        print(f"  outcome_status: {result.get('outcome_status')}")
    elif result.get("errors"):
        print(f"  error: {result['errors'][0]}")
    for warning in result.get("warnings") or []:
        print(f"  warning: {warning}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
