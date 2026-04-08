"""Data model for parsed Oracle AWR run-level metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RunMetadata:
    """Canonical Day 1 run metadata extracted from an AWR report."""

    source_file_name: str
    source_file_path: str
    parse_timestamp: str
    database_name: str | None = None
    db_id: str | None = None
    instance_name: str | None = None
    instance_number: str | None = None
    host_name: str | None = None
    platform: str | None = None
    db_version: str | None = None
    cpu_count: int | None = None
    core_count: int | None = None
    socket_count: int | None = None
    memory_gb: float | None = None
    begin_snapshot_time: str | None = None
    end_snapshot_time: str | None = None
