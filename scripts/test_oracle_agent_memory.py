#!/usr/bin/env python3
"""Run the isolated Phase 6N.1 Oracle Agent Memory prototype."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from src.memory.oracle_agent_memory_adapter import (
    DEFAULT_DB_NAME,
    run_phase6n1_prototype,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prototype-only Oracle Agent Memory semantic recall test.",
    )
    parser.add_argument("--db-name", default=DEFAULT_DB_NAME)
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="Semantic recall query. May be supplied multiple times.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_phase6n1_prototype(db_name=args.db_name, queries=args.queries)
    _print_result(result)
    if not result.get("enabled", True):
        return 0
    return 0 if result.get("success") else 1


def _print_result(result: dict[str, Any]) -> None:
    print("Oracle Agent Memory Prototype:")
    print(json.dumps(_json_safe(result), indent=2, sort_keys=True))


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {key: _json_safe(item) for key, item in value.items() if key != "thread"}
        if isinstance(value, list):
            return [_json_safe(item) for item in value]
        return str(value)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
