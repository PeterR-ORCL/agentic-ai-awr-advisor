"""Deterministic parsing utilities for Oracle AWR wait-event metrics."""

from __future__ import annotations

import re
from typing import Any

FOREGROUND_WAITS_HEADER = "foreground wait events"
BACKGROUND_WAITS_HEADER = "background wait events"
TOP_FOREGROUND_WAITS_HEADER = "top 10 foreground events by total wait time"
WAIT_CLASSES_TOTAL_HEADER = "wait classes by total wait time"

DB_CPU_ROW_PATTERN = re.compile(
    r"^\s*DB CPU\s+([0-9,]+(?:\.\d+)?)\s+([0-9,]+(?:\.\d+)?)\s+CPU\s*$"
)
WAIT_EVENT_ROW_PATTERN = re.compile(
    r"^\s*(.+?)\s+([0-9,]+)\s+([0-9,]+(?:\.\d+)?)\s+([0-9,]+(?:\.\d+)?)\s+"
    r"([0-9,]+(?:\.\d+)?)\s+([A-Za-z][A-Za-z /&-]*[A-Za-z])\s*$"
)
WAIT_EVENT_COLUMN_SPLIT_PATTERN = re.compile(r"\s{2,}")


def parse_waits_section(lines: list[str]) -> list[dict[str, Any]]:
    """Parse structured foreground wait events from synthetic and native AWR waits.

    Native AWR reports can include both:
    - "Top 10 Foreground Events by Total Wait Time"
    - later "Foreground Wait Events"

    When both exist, the later detailed block should win for duplicate events,
    but summary-only events from the earlier block must still be preserved.
    """

    wait_events: list[dict[str, Any]] = []
    in_foreground_waits = False
    has_detailed_foreground_waits = any(
        FOREGROUND_WAITS_HEADER in _normalize_line(line)
        and TOP_FOREGROUND_WAITS_HEADER not in _normalize_line(line)
        for line in lines
    )

    for line in lines:
        normalized_line = _normalize_line(line)
        if not normalized_line or _is_divider_line(line):
            continue

        if BACKGROUND_WAITS_HEADER in normalized_line:
            break

        if WAIT_CLASSES_TOTAL_HEADER in normalized_line:
            in_foreground_waits = False
            continue

        if (
            FOREGROUND_WAITS_HEADER in normalized_line
            or TOP_FOREGROUND_WAITS_HEADER in normalized_line
        ):
            in_foreground_waits = True
            continue

        if not in_foreground_waits:
            continue

        if normalized_line.startswith("event waits"):
            continue

        db_cpu_record = _parse_db_cpu_row(line)
        if db_cpu_record is not None:
            wait_events.append(db_cpu_record)
            continue

        wait_event_record = _parse_wait_event_row(line)
        if wait_event_record is not None:
            wait_events.append(wait_event_record)

    if not has_detailed_foreground_waits:
        return wait_events

    deduped_by_event: dict[str, dict[str, Any]] = {}
    ordered_event_names: list[str] = []
    for row in wait_events:
        event_name = str(row.get("event_name") or "").strip().lower()
        if not event_name:
            continue
        if event_name not in deduped_by_event:
            ordered_event_names.append(event_name)
        deduped_by_event[event_name] = row

    return [deduped_by_event[event_name] for event_name in ordered_event_names]


def _parse_db_cpu_row(line: str) -> dict[str, Any] | None:
    """Parse the special DB CPU foreground wait row."""

    match = DB_CPU_ROW_PATTERN.match(line)
    if not match:
        return None

    time_seconds = _to_float(match.group(1))
    pct_db_time = _to_float(match.group(2))
    if time_seconds is None or pct_db_time is None:
        return None

    return {
        "event_name": "DB CPU",
        "waits": None,
        "time_seconds": time_seconds,
        "avg_wait_ms": None,
        "pct_db_time": pct_db_time,
        "wait_class": "CPU",
        "source_section": "waits",
    }


def _parse_wait_event_row(line: str) -> dict[str, Any] | None:
    """Parse a standard foreground wait-event row."""

    parsed_columns = _parse_wait_event_columns(line)
    if parsed_columns is not None:
        return parsed_columns

    match = WAIT_EVENT_ROW_PATTERN.match(line)
    if not match:
        return None

    event_name = match.group(1).strip()
    waits = _to_int(match.group(2))
    time_seconds = _to_float(match.group(3))
    avg_wait_ms = _to_float(match.group(4))
    pct_db_time = _to_float(match.group(5))
    wait_class = match.group(6).strip()

    if not event_name or wait_class in {
        FOREGROUND_WAITS_HEADER,
        BACKGROUND_WAITS_HEADER,
    }:
        return None

    if (
        waits is None
        or time_seconds is None
        or avg_wait_ms is None
        or pct_db_time is None
    ):
        return None

    return {
        "event_name": event_name,
        "waits": waits,
        "time_seconds": time_seconds,
        "avg_wait_ms": avg_wait_ms,
        "pct_db_time": pct_db_time,
        "wait_class": wait_class,
        "source_section": "waits",
    }


def _parse_wait_event_columns(line: str) -> dict[str, Any] | None:
    """Parse split-column wait rows, including native rows without wait class."""

    columns = [
        part.strip()
        for part in WAIT_EVENT_COLUMN_SPLIT_PATTERN.split(line.strip())
        if part.strip()
    ]
    if not columns or len(columns) < 6:
        return None

    event_name = columns[0]
    if not event_name or event_name.lower() in {
        FOREGROUND_WAITS_HEADER,
        BACKGROUND_WAITS_HEADER,
    }:
        return None

    if len(columns) == 6 and not _is_numeric(columns[-1]):
        waits = _to_int(columns[1])
        time_seconds = _to_float(columns[2])
        avg_wait_ms = _to_float(columns[3])
        pct_db_time = _to_float(columns[4])
        wait_class = columns[5]
    elif len(columns) == 7 and _is_numeric(columns[-1]):
        waits = _to_int(columns[1])
        time_seconds = _to_float(columns[3])
        avg_wait_ms = _to_float(columns[4])
        pct_db_time = _to_float(columns[6])
        wait_class = _infer_wait_class(event_name)
    else:
        return None

    if (
        waits is None
        or time_seconds is None
        or avg_wait_ms is None
        or pct_db_time is None
    ):
        return None

    return {
        "event_name": event_name,
        "waits": waits,
        "time_seconds": time_seconds,
        "avg_wait_ms": avg_wait_ms,
        "pct_db_time": pct_db_time,
        "wait_class": wait_class,
        "source_section": "waits",
    }


def _infer_wait_class(event_name: str) -> str | None:
    """Infer a wait class for native wait rows that omit it."""

    normalized_name = event_name.strip().lower()
    if normalized_name.startswith(("gc ", "ges ", "gcs ")):
        return "Cluster"
    if normalized_name == "log file sync":
        return "Commit"
    if normalized_name in {"remote log write", "rfs write", "rfs random i/o"}:
        return "Network"
    if normalized_name == "db file parallel write":
        return "System I/O"
    if normalized_name.startswith(
        (
            "db file sequential read",
            "db file scattered read",
            "read by other session",
            "direct path read",
            "cell single block physical read",
            "cell multiblock physical read",
        )
    ):
        return "User I/O"
    return None


def _is_divider_line(line: str) -> bool:
    """Return True when a line is only a visual divider."""

    stripped_line = line.strip()
    if not stripped_line:
        return False
    return bool(re.fullmatch(r"[-=\s]+", stripped_line))


def _normalize_line(line: str) -> str:
    """Normalize a line for deterministic header detection."""

    return " ".join(line.strip().lower().split())


def _to_float(value: str) -> float | None:
    """Convert a numeric string to float, tolerating commas."""

    try:
        return float(value.replace(",", ""))
    except (AttributeError, ValueError):
        return None


def _to_int(value: str) -> int | None:
    """Convert a numeric string to int, tolerating commas."""

    try:
        return int(value.replace(",", ""))
    except (AttributeError, ValueError):
        return None


def _is_numeric(value: str) -> bool:
    """Return True when the given token is a parseable numeric value."""

    return _to_float(value) is not None
