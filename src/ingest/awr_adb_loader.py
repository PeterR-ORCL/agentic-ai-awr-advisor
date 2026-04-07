"""Batch loader for parsed Oracle AWR reports into ADB core tables."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import socket
import sys
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import re
from typing import Any, Protocol

from dotenv import load_dotenv

from src.analysis.derived_metric_extractor import (
    extract_derived_pressure_metrics,
)
from src.models.parse_result import ParseResult
from src.parser.awr_parser import parse_awr_file as parse_awr_report

LOGGER = logging.getLogger(__name__)

PIPELINE_NAME = "oci-awr-agentic-ai-sizing-advisor"
PIPELINE_VERSION = "1.0.0"
SNAPSHOT_TIME_FORMATS = (
    "%d-%b-%y %H:%M:%S",
    "%d-%b-%Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)
SNAP_ID_BEGIN_PATTERNS = (
    re.compile(r"begin snap:\s*(\d+)", re.IGNORECASE),
    re.compile(r"begin snap id\s*[:=]?\s*(\d+)", re.IGNORECASE),
)
SNAP_ID_END_PATTERNS = (
    re.compile(r"end snap:\s*(\d+)", re.IGNORECASE),
    re.compile(r"end snap id\s*[:=]?\s*(\d+)", re.IGNORECASE),
)
DB_VERSION_PATTERNS = (
    re.compile(r"release\s+([0-9][0-9A-Za-z\.\-_]+)", re.IGNORECASE),
    re.compile(r"version\s*[:=]\s*([0-9][0-9A-Za-z\.\-_]+)", re.IGNORECASE),
)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOTENV_PATH = PROJECT_ROOT / ".env"


def _load_project_env() -> None:
    """Load the project .env file from a stable repo-root location."""

    load_dotenv(dotenv_path=DOTENV_PATH, override=False)


class DbCursor(Protocol):
    def __enter__(self) -> "DbCursor": ...
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None: ...
    def execute(self, statement: str, parameters: Any = ...) -> Any: ...
    def executemany(self, statement: str, parameters: Any) -> Any: ...
    def fetchone(self) -> Any: ...


class DbConnection(Protocol):
    def cursor(self, *args: Any, **kwargs: Any) -> DbCursor: ...
    def commit(self) -> Any: ...
    def rollback(self) -> Any: ...
    def close(self) -> Any: ...


def get_db_connection() -> DbConnection:
    """Create a real python-oracledb connection to Autonomous Database."""

    _load_project_env()

    try:
        import oracledb
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "python-oracledb is required for ADB persistence. "
            "Install it with `pip install oracledb`."
        ) from exc

    user = os.getenv("ADB_USER")
    password = os.getenv("ADB_PASSWORD")
    dsn = os.getenv("ADB_DSN")
    config_dir = os.getenv("TNS_ADMIN")
    wallet_location = os.getenv("TNS_ADMIN")
    wallet_password = os.getenv("ADB_WALLET_PASSWORD")

    required_env = {
        "ADB_USER": user,
        "ADB_PASSWORD": password,
        "ADB_DSN": dsn,
        "TNS_ADMIN": config_dir,
        "ADB_WALLET_PASSWORD": wallet_password,
    }
    missing_env = [name for name, value in required_env.items() if not value]
    if missing_env:
        raise ValueError(
            "Missing required ADB environment variables: "
            + ", ".join(sorted(missing_env))
        )

    LOGGER.info("ADB connect config: user=%s dsn=%s", user, dsn)
    LOGGER.info(
        "ADB connect wallet: tns_admin=%s wallet_password_present=%s",
        config_dir,
        bool(wallet_password),
    )

    connect_kwargs: dict[str, Any] = {
        "user": user,
        "password": password,
        "dsn": dsn,
        "config_dir": config_dir,
        "wallet_location": wallet_location,
        "wallet_password": wallet_password,
    }

    conn = oracledb.connect(**connect_kwargs)
    LOGGER.info("ADB connection established")
    return conn


def load_awr_files(input_dir: str | Path) -> list[Path]:
    """Return all candidate AWR .out files in sorted order."""

    directory = Path(input_dir)
    if not directory.exists():
        raise FileNotFoundError(f"Input directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {directory}")

    files: list[Path] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".out":
            LOGGER.info("Skipping non-AWR file: %s", path)
            continue
        files.append(path)

    return files


def start_ingest_run(
    conn: Any,
    pipeline_name: str,
    pipeline_version: str,
    trigger_type: str,
) -> int:
    """Create one ingest-run audit record and return its identity."""

    run_guid = uuid.uuid4().hex
    params_json = _json_dumps(
        {
            "cwd": str(Path.cwd()),
            "execution_host": socket.gethostname(),
            "trigger_type": trigger_type,
        }
    )
    record = {
        "run_guid": run_guid,
        "pipeline_name": pipeline_name,
        "pipeline_version": pipeline_version,
        "trigger_type": trigger_type,
        "status": "STARTED",
        "requested_by": os.getenv("USER") or os.getenv("USERNAME"),
        "execution_host": socket.gethostname(),
        "notes": "AWR batch ingest started.",
        "parameters_json": params_json,
    }
    with conn.cursor() as cursor:
        cursor.execute(
            """
            insert into AWR_INGEST_RUN (
                RUN_GUID,
                PIPELINE_NAME,
                PIPELINE_VERSION,
                TRIGGER_TYPE,
                STATUS,
                REQUESTED_BY,
                EXECUTION_HOST,
                NOTES,
                PARAMETERS_JSON
            ) values (
                :run_guid,
                :pipeline_name,
                :pipeline_version,
                :trigger_type,
                :status,
                :requested_by,
                :execution_host,
                :notes,
                :parameters_json
            )
            """,
            record,
        )
    conn.commit()

    with conn.cursor() as cursor:
        cursor.execute(
            """
            select INGEST_RUN_ID
            from AWR_INGEST_RUN
            where RUN_GUID = :run_guid
            """,
            {"run_guid": run_guid},
        )
        row = cursor.fetchone()
    if not row:
        raise RuntimeError("Failed to create AWR_INGEST_RUN record.")
    ingest_run_id = int(row[0])
    LOGGER.info("Ingest run inserted: INGEST_RUN_ID=%s", ingest_run_id)
    return ingest_run_id


def finalize_ingest_run(
    conn: Any,
    ingest_run_id: int,
    status: str,
    file_count: int,
    success_count: int,
    error_count: int,
    notes: str | None = None,
    error_json: list[dict[str, Any]] | dict[str, Any] | None = None,
) -> None:
    """Finalize the ingest-run record with counts and optional errors."""

    with conn.cursor() as cursor:
        cursor.execute(
            """
            update AWR_INGEST_RUN
               set STATUS = :status,
                   ENDED_AT = SYSTIMESTAMP,
                   FILE_COUNT = :file_count,
                   SUCCESS_COUNT = :success_count,
                   ERROR_COUNT = :error_count,
                   NOTES = :notes,
                   ERROR_JSON = :error_json
             where INGEST_RUN_ID = :ingest_run_id
            """,
            {
                "status": status,
                "file_count": file_count,
                "success_count": success_count,
                "error_count": error_count,
                "notes": notes,
                "error_json": _json_dumps(error_json),
                "ingest_run_id": ingest_run_id,
            },
        )
    conn.commit()
    LOGGER.info(
        (
            "Ingest run finalized: INGEST_RUN_ID=%s STATUS=%s "
            "FILES=%s SUCCESS=%s ERRORS=%s"
        ),
        ingest_run_id,
        status,
        file_count,
        success_count,
        error_count,
    )


def parse_awr_file(file_path: str | Path) -> ParseResult:
    """Parse one AWR file through the existing parser stack."""

    return parse_awr_report(file_path)


def compute_file_hash(file_path: str | Path) -> str:
    """Return the SHA256 digest for one source file."""

    digest = hashlib.sha256()
    with Path(file_path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_source_system_record(parse_result: ParseResult) -> dict[str, Any]:
    """Map parsed metadata to one AWR_SOURCE_SYSTEM row."""

    metadata = parse_result.run_metadata
    db_name = metadata.database_name
    dbid = _to_int(metadata.db_id)
    instance_name = metadata.instance_name
    source_system_code = _build_source_system_code(
        dbid=dbid,
        db_name=db_name,
        instance_name=instance_name,
    )
    return {
        "source_system_code": source_system_code,
        "tenancy_name": None,
        "compartment_name": None,
        "environment_name": None,
        "customer_name": None,
        "application_name": _derive_application_name(parse_result),
        "db_name": db_name,
        "db_unique_name": db_name,
        "dbid": dbid,
        "platform_name": metadata.platform,
        "db_version": _extract_report_header_fields(
            metadata.source_file_path
        ).get("db_version"),
        "rac_flag": "N",
        "adg_flag": "N",
        "cdb_flag": "N",
        "exadata_flag": "N",
        "primary_host_name": metadata.host_name,
        "region_name": None,
        "availability_domain": None,
        "tags_json": _json_dumps(
            {
                "source": "awr_text",
                "instance_name": instance_name,
            }
        ),
    }


def upsert_source_system(
    conn: Any,
    source_system_record: dict[str, Any],
) -> int:
    """Insert or update one source-system record and return its identity."""

    lookup = {"source_system_code": source_system_record["source_system_code"]}
    with conn.cursor() as cursor:
        cursor.execute(
            """
            select SOURCE_SYSTEM_ID
              from AWR_SOURCE_SYSTEM
             where SOURCE_SYSTEM_CODE = :source_system_code
            """,
            lookup,
        )
        row = cursor.fetchone()
        if row:
            source_system_id = int(row[0])
            update_record = dict(source_system_record)
            update_record["source_system_id"] = source_system_id
            cursor.execute(
                """
                update AWR_SOURCE_SYSTEM
                   set TENANCY_NAME = :tenancy_name,
                       COMPARTMENT_NAME = :compartment_name,
                       ENVIRONMENT_NAME = :environment_name,
                       CUSTOMER_NAME = :customer_name,
                       APPLICATION_NAME = :application_name,
                       DB_NAME = :db_name,
                       DB_UNIQUE_NAME = :db_unique_name,
                       DBID = :dbid,
                       PLATFORM_NAME = :platform_name,
                       DB_VERSION = :db_version,
                       RAC_FLAG = :rac_flag,
                       ADG_FLAG = :adg_flag,
                       CDB_FLAG = :cdb_flag,
                       EXADATA_FLAG = :exadata_flag,
                       PRIMARY_HOST_NAME = :primary_host_name,
                       REGION_NAME = :region_name,
                       AVAILABILITY_DOMAIN = :availability_domain,
                       TAGS_JSON = :tags_json,
                       UPDATED_AT = SYSTIMESTAMP
                 where SOURCE_SYSTEM_ID = :source_system_id
                """,
                update_record,
            )
            LOGGER.info(
                "Source system upserted: SOURCE_SYSTEM_ID=%s CODE=%s",
                source_system_id,
                source_system_record["source_system_code"],
            )
            return source_system_id

        cursor.execute(
            """
            insert into AWR_SOURCE_SYSTEM (
                SOURCE_SYSTEM_CODE,
                TENANCY_NAME,
                COMPARTMENT_NAME,
                ENVIRONMENT_NAME,
                CUSTOMER_NAME,
                APPLICATION_NAME,
                DB_NAME,
                DB_UNIQUE_NAME,
                DBID,
                PLATFORM_NAME,
                DB_VERSION,
                RAC_FLAG,
                ADG_FLAG,
                CDB_FLAG,
                EXADATA_FLAG,
                PRIMARY_HOST_NAME,
                REGION_NAME,
                AVAILABILITY_DOMAIN,
                TAGS_JSON
            ) values (
                :source_system_code,
                :tenancy_name,
                :compartment_name,
                :environment_name,
                :customer_name,
                :application_name,
                :db_name,
                :db_unique_name,
                :dbid,
                :platform_name,
                :db_version,
                :rac_flag,
                :adg_flag,
                :cdb_flag,
                :exadata_flag,
                :primary_host_name,
                :region_name,
                :availability_domain,
                :tags_json
            )
            """,
            source_system_record,
        )

    with conn.cursor() as cursor:
        cursor.execute(
            """
            select SOURCE_SYSTEM_ID
              from AWR_SOURCE_SYSTEM
             where SOURCE_SYSTEM_CODE = :source_system_code
            """,
            lookup,
        )
        row = cursor.fetchone()
    if not row:
        raise RuntimeError("Failed to upsert AWR_SOURCE_SYSTEM record.")
    source_system_id = int(row[0])
    LOGGER.info(
        "Source system upserted: SOURCE_SYSTEM_ID=%s CODE=%s",
        source_system_id,
        source_system_record["source_system_code"],
    )
    return source_system_id


def build_report_record(
    parse_result: ParseResult,
    file_path: str | Path,
    file_hash: str,
    source_system_id: int,
    ingest_run_id: int,
) -> dict[str, Any]:
    """Map one parsed AWR file into an AWR_REPORT row."""

    metadata = parse_result.run_metadata
    file_path_obj = Path(file_path)
    header_fields = _extract_report_header_fields(file_path_obj)
    snap_begin = normalize_timestamp(metadata.begin_snapshot_time)
    snap_end = normalize_timestamp(metadata.end_snapshot_time)
    if snap_begin is None and metadata.begin_snapshot_time:
        LOGGER.warning(
            "Could not normalize SNAP_TIME_BEGIN for %s: %r",
            file_path_obj.name,
            metadata.begin_snapshot_time,
        )
    if snap_end is None and metadata.end_snapshot_time:
        LOGGER.warning(
            "Could not normalize SNAP_TIME_END for %s: %r",
            file_path_obj.name,
            metadata.end_snapshot_time,
        )
    elapsed_minutes = None
    if snap_begin and snap_end:
        elapsed_minutes = round(
            (snap_end - snap_begin).total_seconds() / 60.0,
            2,
        )

    parse_status = "PARTIAL" if parse_result.parse_warnings else "PARSED"
    report_record = {
        "source_system_id": source_system_id,
        "ingest_run_id": ingest_run_id,
        "replay_of_awr_id": None,
        "source_file_name": file_path_obj.name,
        "source_file_path": str(file_path_obj.resolve()),
        "object_store_uri": None,
        "file_hash_sha256": file_hash,
        "file_size_bytes": file_path_obj.stat().st_size,
        "report_format": "AWR_OUT",
        "ingest_mode": os.getenv("AWR_INGEST_MODE", "NORMAL").upper(),
        "db_name": metadata.database_name,
        "dbid": _to_int(metadata.db_id),
        "instance_name": metadata.instance_name,
        "instance_number": _to_int(metadata.instance_number),
        "host_name": metadata.host_name,
        "platform_name": metadata.platform,
        "db_version": header_fields.get("db_version"),
        "snap_id_begin": header_fields.get("snap_id_begin"),
        "snap_id_end": header_fields.get("snap_id_end"),
        "snap_time_begin": snap_begin,
        "snap_time_end": snap_end,
        "snap_elapsed_minutes": elapsed_minutes,
        "parse_status": parse_status,
        "report_class": None,
        "workload_class": _derive_workload_class(parse_result),
        "anomaly_flag": "N",
        "raw_metadata_json": _json_dumps(asdict(parse_result.run_metadata)),
        "raw_header_json": _json_dumps(header_fields),
        "parser_output_json": _json_dumps(parse_result.to_dict()),
        "parser_warnings_json": _json_dumps(parse_result.parse_warnings),
    }
    LOGGER.info(
        "Prepared report timestamps: snap_time_begin=%r (%s), snap_time_end=%r (%s)",
        report_record["snap_time_begin"],
        type(report_record["snap_time_begin"]).__name__,
        report_record["snap_time_end"],
        type(report_record["snap_time_end"]).__name__,
    )
    return report_record


def insert_report(conn: Any, report_record: dict[str, Any]) -> int:
    """Insert one AWR_REPORT row and return its identity."""

    timestamp_fields = (
        "snap_time_begin",
        "snap_time_end",
    )
    for field_name in timestamp_fields:
        field_value = report_record.get(field_name)
        LOGGER.info(
            "Report timestamp bind %s=%r type=%s",
            field_name,
            field_value,
            type(field_value).__name__,
        )

    with conn.cursor() as cursor:
        LOGGER.info(
            "Executing AWR_REPORT insert with timestamps: snap_time_begin=%r (%s), "
            "snap_time_end=%r (%s)",
            report_record.get("snap_time_begin"),
            type(report_record.get("snap_time_begin")).__name__,
            report_record.get("snap_time_end"),
            type(report_record.get("snap_time_end")).__name__,
        )
        cursor.execute(
            """
            insert into AWR_REPORT (
                SOURCE_SYSTEM_ID,
                INGEST_RUN_ID,
                REPLAY_OF_AWR_ID,
                SOURCE_FILE_NAME,
                SOURCE_FILE_PATH,
                OBJECT_STORE_URI,
                FILE_HASH_SHA256,
                FILE_SIZE_BYTES,
                REPORT_FORMAT,
                INGEST_MODE,
                DB_NAME,
                DBID,
                INSTANCE_NAME,
                INSTANCE_NUMBER,
                HOST_NAME,
                PLATFORM_NAME,
                DB_VERSION,
                SNAP_ID_BEGIN,
                SNAP_ID_END,
                SNAP_TIME_BEGIN,
                SNAP_TIME_END,
                SNAP_ELAPSED_MINUTES,
                PARSE_STATUS,
                REPORT_CLASS,
                WORKLOAD_CLASS,
                ANOMALY_FLAG,
                RAW_METADATA_JSON,
                RAW_HEADER_JSON,
                PARSER_OUTPUT_JSON,
                PARSER_WARNINGS_JSON
            ) values (
                :source_system_id,
                :ingest_run_id,
                :replay_of_awr_id,
                :source_file_name,
                :source_file_path,
                :object_store_uri,
                :file_hash_sha256,
                :file_size_bytes,
                :report_format,
                :ingest_mode,
                :db_name,
                :dbid,
                :instance_name,
                :instance_number,
                :host_name,
                :platform_name,
                :db_version,
                :snap_id_begin,
                :snap_id_end,
                :snap_time_begin,
                :snap_time_end,
                :snap_elapsed_minutes,
                :parse_status,
                :report_class,
                :workload_class,
                :anomaly_flag,
                :raw_metadata_json,
                :raw_header_json,
                :parser_output_json,
                :parser_warnings_json
            )
            """,
            report_record,
        )

    lookup_record = {
        "ingest_run_id": report_record["ingest_run_id"],
        "source_file_path": report_record["source_file_path"],
        "file_hash_sha256": report_record["file_hash_sha256"],
    }
    with conn.cursor() as cursor:
        cursor.execute(
            """
            select AWR_ID
              from AWR_REPORT
             where INGEST_RUN_ID = :ingest_run_id
               and SOURCE_FILE_PATH = :source_file_path
               and FILE_HASH_SHA256 = :file_hash_sha256
             order by AWR_ID desc
             fetch first 1 rows only
            """,
            lookup_record,
        )
        row = cursor.fetchone()
    if not row:
        raise RuntimeError("Failed to insert AWR_REPORT row.")
    awr_id = int(row[0])
    LOGGER.info(
        "Report inserted: AWR_ID=%s FILE=%s",
        awr_id,
        report_record["source_file_name"],
    )
    return awr_id


def build_metric_fact_rows(
    parse_result: ParseResult,
    awr_id: int,
    source_system_id: int,
) -> list[dict[str, Any]]:
    """Build useful normalized metric facts from the parsed report."""

    snap_begin, snap_end = _require_snapshot_window(parse_result)
    derived = extract_derived_pressure_metrics(parse_result)
    rows: list[dict[str, Any]] = []

    for metric in parse_result.cpu_metrics:
        metric_group = str(metric.get("metric_group") or "")
        metric_name = str(metric.get("metric_name") or "")
        if metric_group == "load_profile":
            rows.append(
                _metric_fact_row(
                    awr_id=awr_id,
                    source_system_id=source_system_id,
                    snap_begin=snap_begin,
                    snap_end=snap_end,
                    domain="load_profile",
                    name=metric_name,
                    value=metric.get("per_second"),
                    unit="per_second",
                    subtype="per_second",
                    metric_json=metric,
                )
            )
            if metric.get("per_transaction") is not None:
                rows.append(
                    _metric_fact_row(
                        awr_id=awr_id,
                        source_system_id=source_system_id,
                        snap_begin=snap_begin,
                        snap_end=snap_end,
                        domain="load_profile",
                        name=metric_name,
                        value=metric.get("per_transaction"),
                        unit="per_transaction",
                        subtype="per_transaction",
                        metric_json=metric,
                    )
                )
        elif metric_group in {"instance_efficiency", "host_cpu"}:
            rows.append(
                _metric_fact_row(
                    awr_id=awr_id,
                    source_system_id=source_system_id,
                    snap_begin=snap_begin,
                    snap_end=snap_end,
                    domain=metric_group,
                    name=metric_name,
                    value=metric.get("metric_value"),
                    unit=metric.get("metric_unit"),
                    metric_json=metric,
                )
            )

    for name, value, unit in (
        ("pga_spill_pressure", derived.get("pga_spill_pressure"), "ratio"),
        ("temp_io_pressure", derived.get("temp_io_pressure"), "per_second"),
        (
            "hard_parses_per_sec",
            derived.get("hard_parses_per_sec"),
            "per_second",
        ),
    ):
        if value is None:
            continue
        rows.append(
            _metric_fact_row(
                awr_id=awr_id,
                source_system_id=source_system_id,
                snap_begin=snap_begin,
                snap_end=snap_end,
                domain="derived",
                name=name,
                value=value,
                unit=unit,
                metric_json={
                    "raw": derived.get("raw"),
                    "availability": derived.get("availability"),
                },
            )
        )

    return [row for row in rows if row["metric_value_num"] is not None]


def insert_metric_facts(conn: Any, metric_rows: list[dict[str, Any]]) -> None:
    """Insert metric fact rows in bulk."""

    if not metric_rows:
        return
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            insert into AWR_METRIC_FACT (
                AWR_ID,
                SOURCE_SYSTEM_ID,
                SNAP_TIME_BEGIN,
                SNAP_TIME_END,
                METRIC_DOMAIN,
                METRIC_NAME,
                METRIC_SUBTYPE,
                DIMENSION_1,
                DIMENSION_2,
                DIMENSION_3,
                METRIC_VALUE_NUM,
                METRIC_VALUE_TXT,
                UNIT_OF_MEASURE,
                VALUE_DIRECTION,
                BASELINE_VALUE_NUM,
                DELTA_VALUE_NUM,
                ZSCORE_VALUE,
                PERCENTILE_VALUE,
                METRIC_JSON
            ) values (
                :awr_id,
                :source_system_id,
                :snap_time_begin,
                :snap_time_end,
                :metric_domain,
                :metric_name,
                :metric_subtype,
                :dimension_1,
                :dimension_2,
                :dimension_3,
                :metric_value_num,
                :metric_value_txt,
                :unit_of_measure,
                :value_direction,
                :baseline_value_num,
                :delta_value_num,
                :zscore_value,
                :percentile_value,
                :metric_json
            )
            """,
            metric_rows,
        )
    LOGGER.info("Metric facts inserted: %s", len(metric_rows))


def build_top_sql_fact_rows(
    parse_result: ParseResult,
    awr_id: int,
    source_system_id: int,
) -> list[dict[str, Any]]:
    """Build top-SQL fact rows from parsed top SQL output."""

    if not parse_result.top_sql:
        return []

    snap_begin, snap_end = _require_snapshot_window(parse_result)
    rows: list[dict[str, Any]] = []
    for rank, sql_row in enumerate(parse_result.top_sql, start=1):
        sql_id = str(sql_row.get("sql_id") or "").strip()
        if not sql_id:
            continue
        elapsed_seconds = _safe_float(sql_row.get("elapsed_time_seconds"))
        executions = _safe_float(sql_row.get("executions"))
        cpu_per_exec = None
        if elapsed_seconds is not None and executions and executions > 0:
            cpu_per_exec = None
        rows.append(
            {
                "awr_id": awr_id,
                "source_system_id": source_system_id,
                "snap_time_begin": snap_begin,
                "snap_time_end": snap_end,
                "sql_id": sql_id,
                "plan_hash_value": _to_int(sql_row.get("plan_hash_value")),
                "module_name": sql_row.get("module"),
                "parsing_schema_name": sql_row.get("parsing_schema_name"),
                "rank_by_elapsed": rank,
                "rank_by_cpu": None,
                "rank_by_gets": None,
                "rank_by_reads": None,
                "rank_by_executions": None,
                "elapsed_time_sec": elapsed_seconds,
                "cpu_time_sec": _safe_float(sql_row.get("cpu_time_seconds")),
                "io_time_sec": _safe_float(sql_row.get("io_time_seconds")),
                "buffer_gets": _safe_float(sql_row.get("buffer_gets")),
                "disk_reads": _safe_float(sql_row.get("disk_reads")),
                "executions": executions,
                "rows_processed": _safe_float(sql_row.get("rows_processed")),
                "elapsed_per_exec_sec": _milliseconds_to_seconds(
                    sql_row.get("elapsed_per_exec_ms")
                ),
                "cpu_per_exec_sec": cpu_per_exec,
                "gets_per_exec": _per_exec(
                    sql_row.get("buffer_gets"),
                    sql_row.get("executions"),
                ),
                "reads_per_exec": _per_exec(
                    sql_row.get("disk_reads"),
                    sql_row.get("executions"),
                ),
                "sql_text_short": _truncate(
                    str(sql_row.get("sql_text_snippet") or ""),
                    4000,
                ),
                "sql_text_clob": (
                    str(sql_row.get("sql_text_snippet") or "") or None
                ),
                "sql_metrics_json": _json_dumps(sql_row),
            }
        )

    return rows


def insert_top_sql_facts(conn: Any, sql_rows: list[dict[str, Any]]) -> None:
    """Insert top-SQL fact rows in bulk."""

    if not sql_rows:
        return
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            insert into AWR_TOP_SQL_FACT (
                AWR_ID,
                SOURCE_SYSTEM_ID,
                SNAP_TIME_BEGIN,
                SNAP_TIME_END,
                SQL_ID,
                PLAN_HASH_VALUE,
                MODULE_NAME,
                PARSING_SCHEMA_NAME,
                RANK_BY_ELAPSED,
                RANK_BY_CPU,
                RANK_BY_GETS,
                RANK_BY_READS,
                RANK_BY_EXECUTIONS,
                ELAPSED_TIME_SEC,
                CPU_TIME_SEC,
                IO_TIME_SEC,
                BUFFER_GETS,
                DISK_READS,
                EXECUTIONS,
                ROWS_PROCESSED,
                ELAPSED_PER_EXEC_SEC,
                CPU_PER_EXEC_SEC,
                GETS_PER_EXEC,
                READS_PER_EXEC,
                SQL_TEXT_SHORT,
                SQL_TEXT_CLOB,
                SQL_METRICS_JSON
            ) values (
                :awr_id,
                :source_system_id,
                :snap_time_begin,
                :snap_time_end,
                :sql_id,
                :plan_hash_value,
                :module_name,
                :parsing_schema_name,
                :rank_by_elapsed,
                :rank_by_cpu,
                :rank_by_gets,
                :rank_by_reads,
                :rank_by_executions,
                :elapsed_time_sec,
                :cpu_time_sec,
                :io_time_sec,
                :buffer_gets,
                :disk_reads,
                :executions,
                :rows_processed,
                :elapsed_per_exec_sec,
                :cpu_per_exec_sec,
                :gets_per_exec,
                :reads_per_exec,
                :sql_text_short,
                :sql_text_clob,
                :sql_metrics_json
            )
            """,
            sql_rows,
        )
    LOGGER.info("Top SQL facts inserted: %s", len(sql_rows))


def build_wait_event_fact_rows(
    parse_result: ParseResult,
    awr_id: int,
    source_system_id: int,
) -> list[dict[str, Any]]:
    """Build wait-event fact rows from parsed foreground waits."""

    if not parse_result.wait_events:
        return []

    snap_begin, snap_end = _require_snapshot_window(parse_result)
    ranked_events = sorted(
        parse_result.wait_events,
        key=lambda row: _safe_float(row.get("pct_db_time")) or 0.0,
        reverse=True,
    )
    rows: list[dict[str, Any]] = []
    for rank, wait_row in enumerate(ranked_events, start=1):
        event_name = str(wait_row.get("event_name") or "").strip()
        wait_class = str(wait_row.get("wait_class") or "").strip()
        if not event_name or not wait_class:
            continue
        rows.append(
            {
                "awr_id": awr_id,
                "source_system_id": source_system_id,
                "snap_time_begin": snap_begin,
                "snap_time_end": snap_end,
                "wait_class": wait_class,
                "event_name": event_name,
                "total_waits": _safe_float(wait_row.get("waits")),
                "total_timeouts": _safe_float(wait_row.get("timeouts")),
                "time_waited_sec": _safe_float(wait_row.get("time_seconds")),
                "avg_wait_ms": _safe_float(wait_row.get("avg_wait_ms")),
                "pct_db_time": _safe_float(wait_row.get("pct_db_time")),
                "rank_in_awr": rank,
                "foreground_flag": "Y",
                "wait_metrics_json": _json_dumps(wait_row),
            }
        )
    return rows


def insert_wait_event_facts(
    conn: Any,
    wait_rows: list[dict[str, Any]],
) -> None:
    """Insert wait-event fact rows in bulk."""

    if not wait_rows:
        return
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            insert into AWR_WAIT_EVENT_FACT (
                AWR_ID,
                SOURCE_SYSTEM_ID,
                SNAP_TIME_BEGIN,
                SNAP_TIME_END,
                WAIT_CLASS,
                EVENT_NAME,
                TOTAL_WAITS,
                TOTAL_TIMEOUTS,
                TIME_WAITED_SEC,
                AVG_WAIT_MS,
                PCT_DB_TIME,
                RANK_IN_AWR,
                FOREGROUND_FLAG,
                WAIT_METRICS_JSON
            ) values (
                :awr_id,
                :source_system_id,
                :snap_time_begin,
                :snap_time_end,
                :wait_class,
                :event_name,
                :total_waits,
                :total_timeouts,
                :time_waited_sec,
                :avg_wait_ms,
                :pct_db_time,
                :rank_in_awr,
                :foreground_flag,
                :wait_metrics_json
            )
            """,
            wait_rows,
        )
    LOGGER.info("Wait event facts inserted: %s", len(wait_rows))


def build_feature_vector_record(
    parse_result: ParseResult,
    awr_id: int,
    source_system_id: int,
) -> dict[str, Any]:
    """Build one feature-vector record with FEATURE_JSON populated."""

    _, snap_end = _require_snapshot_window(parse_result)
    derived = extract_derived_pressure_metrics(parse_result)
    feature_json = {
        "cpu_pct": _compute_cpu_pct(parse_result),
        "user_io_pct": _sum_wait_class_pct(parse_result, "User I/O"),
        "commit_pct": _sum_wait_class_pct(parse_result, "Commit"),
        "concurrency_pct": _sum_wait_class_pct(parse_result, "Concurrency"),
        "read_iops": _extract_load_profile_metric(
            parse_result,
            "Physical reads",
        ),
        "write_iops": _extract_load_profile_metric(
            parse_result,
            "Physical writes",
        ),
        "read_mb_per_sec": _aggregate_datafile_metric(
            parse_result,
            "read_mb",
        ),
        "write_mb_per_sec": _aggregate_datafile_metric(
            parse_result,
            "write_mb",
        ),
        "hard_parses_per_sec": derived.get("hard_parses_per_sec"),
        "temp_io_pressure": derived.get("temp_io_pressure"),
        "pga_spill_pressure": derived.get("pga_spill_pressure"),
        "log_file_sync_ms": _extract_log_file_sync_ms(parse_result),
        "top_sql_concentration": _top_sql_concentration(parse_result),
    }
    return {
        "awr_id": awr_id,
        "source_system_id": source_system_id,
        "observed_at": snap_end,
        "vector_version": "1.0.0",
        "feature_set_name": "awr_core_metrics",
        "feature_set_version": "1.0.0",
        "workload_class": _derive_workload_class(parse_result),
        "vector_status": "ACTIVE",
        "feature_vector": None,
        "narrative_embedding": None,
        "feature_json": _json_dumps(feature_json),
        "normalization_json": None,
        "explanation_json": _json_dumps(
            {"derived_metrics": derived, "feature_keys": sorted(feature_json)}
        ),
        "source_lineage_json": _json_dumps(
            {
                "source_file_name": parse_result.run_metadata.source_file_name,
                "source_file_path": parse_result.run_metadata.source_file_path,
                "parser_sections": sorted(parse_result.sections_found),
            }
        ),
    }


def insert_feature_vector(
    conn: Any,
    feature_vector_record: dict[str, Any],
) -> None:
    """Insert one feature vector row."""

    with conn.cursor() as cursor:
        cursor.execute(
            """
            insert into AWR_FEATURE_VECTOR (
                AWR_ID,
                SOURCE_SYSTEM_ID,
                OBSERVED_AT,
                VECTOR_VERSION,
                FEATURE_SET_NAME,
                FEATURE_SET_VERSION,
                WORKLOAD_CLASS,
                VECTOR_STATUS,
                FEATURE_VECTOR,
                NARRATIVE_EMBEDDING,
                FEATURE_JSON,
                NORMALIZATION_JSON,
                EXPLANATION_JSON,
                SOURCE_LINEAGE_JSON
            ) values (
                :awr_id,
                :source_system_id,
                :observed_at,
                :vector_version,
                :feature_set_name,
                :feature_set_version,
                :workload_class,
                :vector_status,
                :feature_vector,
                :narrative_embedding,
                :feature_json,
                :normalization_json,
                :explanation_json,
                :source_lineage_json
            )
            """,
            feature_vector_record,
        )
    LOGGER.info(
        "Feature vector inserted: AWR_ID=%s SOURCE_SYSTEM_ID=%s",
        feature_vector_record["awr_id"],
        feature_vector_record["source_system_id"],
    )


def process_awr_batch(
    input_dir: str | Path,
    conn: DbConnection | None = None,
) -> dict[str, Any]:
    """Process and load all AWR .out files from one directory."""

    managed_connection = conn is None
    db_conn: DbConnection | None = conn
    ingest_run_id: int | None = None
    try:
        if db_conn is None:
            db_conn = get_db_connection()

        LOGGER.info("Entering DB ingest flow")
        awr_files = load_awr_files(input_dir)
        ingest_run_id = start_ingest_run(
            conn=db_conn,
            pipeline_name=PIPELINE_NAME,
            pipeline_version=PIPELINE_VERSION,
            trigger_type=os.getenv("AWR_TRIGGER_TYPE", "MANUAL"),
        )

        file_count = len(awr_files)
        success_count = 0
        error_count = 0
        errors: list[dict[str, Any]] = []

        for file_path in awr_files:
            LOGGER.info("Processing AWR file: %s", file_path)
            try:
                parse_result = parse_awr_file(file_path)
                file_hash = compute_file_hash(file_path)
                source_system_record = build_source_system_record(parse_result)
                source_system_id = upsert_source_system(
                    db_conn,
                    source_system_record,
                )

                report_record = build_report_record(
                    parse_result=parse_result,
                    file_path=file_path,
                    file_hash=file_hash,
                    source_system_id=source_system_id,
                    ingest_run_id=ingest_run_id,
                )
                awr_id = insert_report(db_conn, report_record)

                metric_rows = build_metric_fact_rows(
                    parse_result=parse_result,
                    awr_id=awr_id,
                    source_system_id=source_system_id,
                )
                insert_metric_facts(db_conn, metric_rows)

                sql_rows = build_top_sql_fact_rows(
                    parse_result=parse_result,
                    awr_id=awr_id,
                    source_system_id=source_system_id,
                )
                insert_top_sql_facts(db_conn, sql_rows)

                wait_rows = build_wait_event_fact_rows(
                    parse_result=parse_result,
                    awr_id=awr_id,
                    source_system_id=source_system_id,
                )
                insert_wait_event_facts(db_conn, wait_rows)

                feature_vector_record = build_feature_vector_record(
                    parse_result=parse_result,
                    awr_id=awr_id,
                    source_system_id=source_system_id,
                )
                insert_feature_vector(db_conn, feature_vector_record)

                db_conn.commit()
                LOGGER.info(
                    "Commit complete: file=%s awr_id=%s",
                    Path(file_path).name,
                    awr_id,
                )
                success_count += 1
            except Exception as exc:  # noqa: BLE001
                db_conn.rollback()
                LOGGER.exception(
                    "Per-file ingest failure; rollback complete for %s",
                    file_path,
                )
                error_count += 1
                error_entry = {
                    "file_name": Path(file_path).name,
                    "file_path": str(Path(file_path).resolve()),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
                errors.append(error_entry)

        if error_count and success_count:
            final_status = "COMPLETED_WITH_ERRORS"
        elif error_count and not success_count:
            final_status = "FAILED"
        else:
            final_status = "COMPLETED"

        finalize_ingest_run(
            conn=db_conn,
            ingest_run_id=ingest_run_id,
            status=final_status,
            file_count=file_count,
            success_count=success_count,
            error_count=error_count,
            notes=(
                f"Processed {file_count} file(s); "
                f"{success_count} succeeded, {error_count} failed."
            ),
            error_json=errors or None,
        )
        LOGGER.info("ADB persistence complete")
        return {
            "ingest_run_id": ingest_run_id,
            "status": final_status,
            "file_count": file_count,
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors,
        }
    except Exception:  # noqa: BLE001
        if db_conn is not None:
            db_conn.rollback()
            LOGGER.exception("Batch-level ingest failure; rollback complete")
            if ingest_run_id is not None:
                try:
                    finalize_ingest_run(
                        conn=db_conn,
                        ingest_run_id=ingest_run_id,
                        status="FAILED",
                        file_count=0,
                        success_count=0,
                        error_count=1,
                        notes="Batch failed before completion.",
                        error_json={"ingest_run_id": ingest_run_id},
                    )
                except Exception:  # noqa: BLE001
                    LOGGER.exception(
                        "Failed to finalize ingest run after batch failure"
                    )
        raise
    finally:
        if managed_connection and db_conn is not None:
            db_conn.close()


def _build_source_system_code(
    dbid: int | None,
    db_name: str | None,
    instance_name: str | None,
) -> str:
    parts = [
        str(dbid) if dbid is not None else "unknown_dbid",
        (db_name or "unknown_db").strip().lower(),
        (instance_name or "unknown_instance").strip().lower(),
    ]
    return ":".join(parts)


def _derive_application_name(parse_result: ParseResult) -> str | None:
    if not parse_result.top_sql:
        return None
    for sql_row in parse_result.top_sql:
        module = str(sql_row.get("module") or "").strip()
        if module:
            return module
    return None


def _derive_workload_class(parse_result: ParseResult) -> str | None:
    cpu_pct = _compute_cpu_pct(parse_result)
    user_io_pct = _sum_wait_class_pct(parse_result, "User I/O")
    if cpu_pct is not None and cpu_pct >= 50:
        return "CPU_BOUND"
    if user_io_pct is not None and user_io_pct >= 30:
        return "IO_BOUND"
    if parse_result.top_sql:
        return "MIXED"
    return None


def _metric_fact_row(
    awr_id: int,
    source_system_id: int,
    snap_begin: datetime,
    snap_end: datetime,
    domain: str,
    name: str,
    value: Any,
    unit: str | None,
    subtype: str | None = None,
    metric_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "awr_id": awr_id,
        "source_system_id": source_system_id,
        "snap_time_begin": snap_begin,
        "snap_time_end": snap_end,
        "metric_domain": domain,
        "metric_name": name,
        "metric_subtype": subtype,
        "dimension_1": None,
        "dimension_2": None,
        "dimension_3": None,
        "metric_value_num": _safe_float(value),
        "metric_value_txt": None,
        "unit_of_measure": unit,
        "value_direction": None,
        "baseline_value_num": None,
        "delta_value_num": None,
        "zscore_value": None,
        "percentile_value": None,
        "metric_json": _json_dumps(metric_json),
    }


def _require_snapshot_window(
    parse_result: ParseResult,
) -> tuple[datetime, datetime]:
    snap_begin = normalize_timestamp(
        parse_result.run_metadata.begin_snapshot_time
    )
    snap_end = normalize_timestamp(
        parse_result.run_metadata.end_snapshot_time
    )
    if snap_begin is None or snap_end is None:
        raise ValueError(
            "Parsed AWR report does not include usable snapshot timestamps."
        )
    return snap_begin, snap_end


def normalize_timestamp(value: Any) -> datetime | None:
    """Normalize parsed timestamp values for Oracle TIMESTAMP binds."""

    if isinstance(value, datetime):
        return value if 1 <= value.year <= 9999 else None
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    cleaned_candidate = re.sub(r"^\d+\s+", "", candidate)
    if cleaned_candidate != candidate:
        LOGGER.info(
            "Cleaned snapshot timestamp raw=%r cleaned=%r",
            candidate,
            cleaned_candidate,
        )
    for fmt in SNAPSHOT_TIME_FORMATS:
        try:
            parsed = datetime.strptime(cleaned_candidate, fmt)
        except ValueError:
            continue
        if 1 <= parsed.year <= 9999:
            LOGGER.info(
                "Parsed snapshot timestamp cleaned=%r parsed=%r",
                cleaned_candidate,
                parsed,
            )
            return parsed
    LOGGER.warning(
        "Could not parse snapshot timestamp raw=%r cleaned=%r",
        candidate,
        cleaned_candidate,
    )
    return None


def _extract_report_header_fields(file_path: str | Path) -> dict[str, Any]:
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    return {
        "snap_id_begin": _first_int_match(text, SNAP_ID_BEGIN_PATTERNS),
        "snap_id_end": _first_int_match(text, SNAP_ID_END_PATTERNS),
        "db_version": _first_str_match(text, DB_VERSION_PATTERNS),
    }


def _first_int_match(
    text: str,
    patterns: tuple[re.Pattern[str], ...],
) -> int | None:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return _to_int(match.group(1))
    return None


def _first_str_match(
    text: str,
    patterns: tuple[re.Pattern[str], ...],
) -> str | None:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def _extract_load_profile_metric(
    parse_result: ParseResult,
    metric_name: str,
) -> float | None:
    for metric in parse_result.cpu_metrics:
        if metric.get("metric_group") != "load_profile":
            continue
        if str(metric.get("metric_name") or "").strip() != metric_name:
            continue
        return _safe_float(metric.get("per_second"))
    return None


def _compute_cpu_pct(parse_result: ParseResult) -> float | None:
    db_cpu = _extract_load_profile_metric(parse_result, "DB CPU(s)")
    db_time = _extract_load_profile_metric(parse_result, "DB Time(s)")
    if db_cpu is None or db_time is None or db_time <= 0:
        return None
    return round((db_cpu / db_time) * 100.0, 4)


def _sum_wait_class_pct(
    parse_result: ParseResult,
    wait_class: str,
) -> float | None:
    values: list[float | None] = [
        _safe_float(row.get("pct_db_time"))
        for row in parse_result.wait_events
        if str(row.get("wait_class") or "") == wait_class
    ]
    numeric_values = _compact_floats(values)
    if not numeric_values:
        return None
    return round(sum(numeric_values), 4)


def _extract_log_file_sync_ms(parse_result: ParseResult) -> float | None:
    for row in parse_result.wait_events:
        if str(row.get("event_name") or "") != "log file sync":
            continue
        return _safe_float(row.get("avg_wait_ms"))
    return None


def _top_sql_concentration(parse_result: ParseResult) -> float | None:
    pct_values = _compact_floats(
        [
            _safe_float(row.get("pct_total"))
            for row in parse_result.top_sql[:2]
            if _safe_float(row.get("pct_total")) is not None
        ]
    )
    if not pct_values:
        return None
    return round(sum(pct_values), 4)


def _aggregate_datafile_metric(
    parse_result: ParseResult,
    key: str,
) -> float | None:
    values = _compact_floats(
        [
            _safe_float(row.get(key))
            for row in parse_result.datafile_io_stats
            if _safe_float(row.get(key)) is not None
        ]
    )
    if not values:
        return None
    return round(sum(values), 4)


def _compact_floats(values: list[float | None]) -> list[float]:
    return [value for value in values if value is not None]


def _milliseconds_to_seconds(value: Any) -> float | None:
    numeric_value = _safe_float(value)
    if numeric_value is None:
        return None
    return round(numeric_value / 1000.0, 6)


def _per_exec(numerator: Any, executions: Any) -> float | None:
    numeric_numerator = _safe_float(numerator)
    numeric_executions = _safe_float(executions)
    if numeric_numerator is None or numeric_executions is None:
        return None
    if numeric_executions <= 0:
        return None
    return round(numeric_numerator / numeric_executions, 6)


def _truncate(value: str, max_length: int) -> str | None:
    normalized = value.strip()
    if not normalized:
        return None
    return normalized[:max_length]


def _safe_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return None


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        normalized = value.replace(",", "").strip()
        if not normalized:
            return None
        try:
            return int(float(normalized))
        except ValueError:
            return None
    return None


def _json_dumps(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, default=str, sort_keys=True)


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=os.getenv("AWR_INGEST_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    args = argv if argv is not None else sys.argv[1:]
    input_dir = (
        Path(args[0])
        if args
        else Path(os.getenv("AWR_INPUT_DIR", "data/input"))
    )
    result = process_awr_batch(input_dir=input_dir)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
