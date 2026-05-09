"""Read-only structured recall APIs for Phase 6 memory."""

from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.ingest.awr_adb_loader import get_db_connection

DISABLED_VALUES = {"0", "false", "no", "off"}
DEFAULT_LIMIT = 10
DEFAULT_UNKNOWN_SIGNAL_LIMIT = 25
MAX_LIMIT = 500
ORDER_VALUES = {"newest", "oldest"}


def recall_run_history(
    *,
    db_name: str | None = None,
    dbid: int | str | None = None,
    source_file_name: str | None = None,
    limit: int = DEFAULT_LIMIT,
    order: str = "newest",
    connection: Any | None = None,
) -> dict[str, Any]:
    """Recall recent run memory records.

    Recall is observational and read-only. It does not influence parser,
    scoring, recommendation, or runtime decision behavior.
    """

    return _recall_records(
        table="AWR_RUN_HISTORY",
        columns=(
            "RUN_HISTORY_ID",
            "SOURCE_FILE_NAME",
            "DB_NAME",
            "DBID",
            "INSTANCE_NAME",
            "AWR_BEGIN_TIME",
            "AWR_END_TIME",
            "DECISION_POSTURE",
            "RISK_LEVEL",
            "CONFIDENCE_SCORE",
            "PRIMARY_DOMAIN",
            "CREATED_AT",
        ),
        filters={
            "DB_NAME": db_name,
            "DBID": dbid,
            "SOURCE_FILE_NAME": source_file_name,
        },
        timestamp_column="CREATED_AT",
        primary_id_column="RUN_HISTORY_ID",
        limit=limit,
        order=order,
        connection=connection,
    )


def recall_recommendation_history(
    *,
    run_history_id: int | None = None,
    db_name: str | None = None,
    recommendation_status: str | None = None,
    limit: int = DEFAULT_LIMIT,
    order: str = "newest",
    connection: Any | None = None,
) -> dict[str, Any]:
    """Recall persisted recommendation memory records."""

    join = ""
    filters: dict[str, Any] = {
        "r.RUN_HISTORY_ID": run_history_id,
        "rh.DB_NAME": db_name,
        "r.SEVERITY": recommendation_status,
    }
    if db_name is not None:
        join = " JOIN AWR_RUN_HISTORY rh ON rh.RUN_HISTORY_ID = r.RUN_HISTORY_ID"
    return _recall_records(
        table="AWR_RECOMMENDATION_HISTORY r",
        columns=(
            "r.RECOMMENDATION_HISTORY_ID",
            "r.RUN_HISTORY_ID",
            "r.RECOMMENDATION_ID",
            "r.DOMAIN",
            "r.SEVERITY",
            "r.RECOMMENDATION_TYPE",
            "r.RECOMMENDATION_TEXT",
            "r.CONFIDENCE_SCORE",
            "r.RANK_ORDER",
            "r.CREATED_AT",
        ),
        filters=filters,
        timestamp_column="r.CREATED_AT",
        primary_id_column="r.RECOMMENDATION_HISTORY_ID",
        limit=limit,
        order=order,
        join_clause=join,
        connection=connection,
    )


def recall_action_history(
    *,
    run_history_id: int | None = None,
    action_status: str | None = None,
    action_type: str | None = None,
    limit: int = DEFAULT_LIMIT,
    order: str = "newest",
    connection: Any | None = None,
) -> dict[str, Any]:
    """Recall tracked action history records."""

    return _recall_records(
        table="AWR_ACTION_HISTORY",
        columns=(
            "ACTION_HISTORY_ID",
            "RUN_HISTORY_ID",
            "RECOMMENDATION_HISTORY_ID",
            "ACTION_TYPE",
            "ACTION_STATUS",
            "ACTION_DESCRIPTION",
            "ACTION_OWNER",
            "ACTION_TIMESTAMP",
            "CREATED_AT",
        ),
        filters={
            "RUN_HISTORY_ID": run_history_id,
            "ACTION_STATUS": action_status,
            "ACTION_TYPE": action_type,
        },
        timestamp_column="CREATED_AT",
        primary_id_column="ACTION_HISTORY_ID",
        limit=limit,
        order=order,
        connection=connection,
    )


def recall_outcome_history(
    *,
    run_history_id: int | None = None,
    action_history_id: int | None = None,
    outcome_status: str | None = None,
    limit: int = DEFAULT_LIMIT,
    order: str = "newest",
    connection: Any | None = None,
) -> dict[str, Any]:
    """Recall append-only action outcome records."""

    return _recall_records(
        table="AWR_ACTION_OUTCOME_HISTORY",
        columns=(
            "ACTION_OUTCOME_ID",
            "RUN_HISTORY_ID",
            "ACTION_HISTORY_ID",
            "OUTCOME_STATUS",
            "OUTCOME_SUMMARY",
            "IMPACT_SCORE",
            "RECORDED_AT",
            "RECORDED_BY",
        ),
        filters={
            "RUN_HISTORY_ID": run_history_id,
            "ACTION_HISTORY_ID": action_history_id,
            "OUTCOME_STATUS": outcome_status,
        },
        timestamp_column="RECORDED_AT",
        primary_id_column="ACTION_OUTCOME_ID",
        limit=limit,
        order=order,
        connection=connection,
    )


def recall_feedback_history(
    *,
    run_history_id: int | None = None,
    feedback_type: str | None = None,
    feedback_rating: str | None = None,
    limit: int = DEFAULT_LIMIT,
    order: str = "newest",
    connection: Any | None = None,
) -> dict[str, Any]:
    """Recall operator feedback records."""

    return _recall_records(
        table="AWR_FEEDBACK_HISTORY",
        columns=(
            "FEEDBACK_ID",
            "RUN_HISTORY_ID",
            "RECOMMENDATION_HISTORY_ID",
            "ACTION_HISTORY_ID",
            "ACTION_OUTCOME_ID",
            "FEEDBACK_TYPE",
            "FEEDBACK_RATING",
            "FEEDBACK_SUMMARY",
            "FEEDBACK_SOURCE",
            "RECORDED_BY",
            "RECORDED_AT",
        ),
        filters={
            "RUN_HISTORY_ID": run_history_id,
            "FEEDBACK_TYPE": feedback_type,
            "FEEDBACK_RATING": feedback_rating,
        },
        timestamp_column="RECORDED_AT",
        primary_id_column="FEEDBACK_ID",
        limit=limit,
        order=order,
        connection=connection,
    )


def recall_unknown_signals(
    *,
    review_status: str | None = None,
    review_classification: str | None = None,
    db_name: str | None = None,
    section_name: str | None = None,
    limit: int = DEFAULT_UNKNOWN_SIGNAL_LIMIT,
    order: str = "newest",
    connection: Any | None = None,
) -> dict[str, Any]:
    """Recall parser unknown and review records."""

    return _recall_records(
        table="AWR_UNKNOWN_SIGNAL_HISTORY",
        columns=(
            "UNKNOWN_SIGNAL_ID",
            "RUN_HISTORY_ID",
            "SOURCE_FILE_NAME",
            "DB_NAME",
            "DBID",
            "SECTION_NAME",
            "UNKNOWN_TYPE",
            "DETECTION_REASON",
            "FREQUENCY_COUNT",
            "FIRST_SEEN_TIMESTAMP",
            "LAST_SEEN_TIMESTAMP",
            "REVIEW_STATUS",
            "REVIEW_CLASSIFICATION",
            "REVIEWED_BY",
            "REVIEWED_AT",
        ),
        filters={
            "REVIEW_STATUS": review_status,
            "REVIEW_CLASSIFICATION": review_classification,
            "DB_NAME": db_name,
            "SECTION_NAME": section_name,
        },
        timestamp_column="LAST_SEEN_TIMESTAMP",
        primary_id_column="UNKNOWN_SIGNAL_ID",
        limit=limit,
        order=order,
        connection=connection,
    )


def recall_knowledge_requests(
    *,
    approval_status: str | None = None,
    source_type: str | None = None,
    run_history_id: int | None = None,
    limit: int = DEFAULT_LIMIT,
    order: str = "newest",
    connection: Any | None = None,
) -> dict[str, Any]:
    """Recall approval and governance request records."""

    return _recall_records(
        table="AWR_KNOWLEDGE_UPDATE_REQUEST",
        columns=(
            "REQUEST_ID",
            "SOURCE_TYPE",
            "SOURCE_ID",
            "RUN_HISTORY_ID",
            "CANDIDATE_CLASSIFICATION",
            "CANDIDATE_SUMMARY",
            "APPROVAL_STATUS",
            "APPROVED_BY",
            "APPROVED_AT",
            "CREATED_BY",
            "CREATED_AT",
        ),
        filters={
            "APPROVAL_STATUS": approval_status,
            "SOURCE_TYPE": source_type,
            "RUN_HISTORY_ID": run_history_id,
        },
        timestamp_column="CREATED_AT",
        primary_id_column="REQUEST_ID",
        limit=limit,
        order=order,
        connection=connection,
    )


def recall_knowledge_artifacts(
    *,
    activation_status: str | None = None,
    artifact_type: str | None = None,
    artifact_classification: str | None = None,
    run_history_id: int | None = None,
    limit: int = DEFAULT_LIMIT,
    order: str = "newest",
    connection: Any | None = None,
) -> dict[str, Any]:
    """Recall materialized knowledge artifact records."""

    return _recall_records(
        table="AWR_KNOWLEDGE_ARTIFACT",
        columns=(
            "ARTIFACT_ID",
            "REQUEST_ID",
            "SOURCE_TYPE",
            "SOURCE_ID",
            "RUN_HISTORY_ID",
            "ARTIFACT_TYPE",
            "ARTIFACT_CLASSIFICATION",
            "ARTIFACT_SUMMARY",
            "ACTIVATION_STATUS",
            "CREATED_BY",
            "CREATED_AT",
            "VERSION_NUMBER",
        ),
        filters={
            "ACTIVATION_STATUS": activation_status,
            "ARTIFACT_TYPE": artifact_type,
            "ARTIFACT_CLASSIFICATION": artifact_classification,
            "RUN_HISTORY_ID": run_history_id,
        },
        timestamp_column="CREATED_AT",
        primary_id_column="ARTIFACT_ID",
        limit=limit,
        order=order,
        connection=connection,
    )


def recall_memory_summary(
    *,
    order: str = "newest",
    connection: Any | None = None,
) -> dict[str, Any]:
    """Return aggregate read-only Phase 6 memory counts."""

    safe_order = _normalize_order(order)
    if not _memory_enabled():
        return _disabled_result(summary=_empty_summary(), order=safe_order)

    managed_connection = connection is None
    if connection is None:
        try:
            connection = get_db_connection()
        except Exception as exc:  # noqa: BLE001
            return _error_result(exc, summary=_empty_summary(), order=safe_order)

    warnings: list[str] = []
    try:
        summary = {
            "runs": _count_table(connection, "AWR_RUN_HISTORY", warnings),
            "recommendations": _count_table(connection, "AWR_RECOMMENDATION_HISTORY", warnings),
            "actions": _count_table(connection, "AWR_ACTION_HISTORY", warnings),
            "outcomes": _count_table(connection, "AWR_ACTION_OUTCOME_HISTORY", warnings),
            "feedback": _count_table(connection, "AWR_FEEDBACK_HISTORY", warnings),
            "unknown_signals": _count_table(connection, "AWR_UNKNOWN_SIGNAL_HISTORY", warnings),
            "knowledge_requests": _count_table(connection, "AWR_KNOWLEDGE_UPDATE_REQUEST", warnings),
            "knowledge_artifacts": _count_table(connection, "AWR_KNOWLEDGE_ARTIFACT", warnings),
        }
        return {
            "enabled": True,
            "success": True,
            "summary": summary,
            "records": [],
            "count": 0,
            "order": safe_order,
            "warnings": warnings,
            "errors": [],
        }
    except Exception as exc:  # noqa: BLE001
        return _error_result(exc, summary=_empty_summary(), order=safe_order)
    finally:
        if managed_connection and connection is not None:
            connection.close()


def _recall_records(
    *,
    table: str,
    columns: tuple[str, ...],
    filters: dict[str, Any],
    timestamp_column: str,
    primary_id_column: str,
    limit: int,
    order: str,
    join_clause: str = "",
    connection: Any | None = None,
) -> dict[str, Any]:
    safe_order = _normalize_order(order)
    if not _memory_enabled():
        return _disabled_result(order=safe_order)

    safe_limit = _normalize_limit(limit)
    managed_connection = connection is None
    if connection is None:
        try:
            connection = get_db_connection()
        except Exception as exc:  # noqa: BLE001
            return _error_result(exc, order=safe_order)

    try:
        sql, params = _build_select_sql(
            table=table,
            columns=columns,
            filters=filters,
            order_by=_build_order_by(
                timestamp_column=timestamp_column,
                primary_id_column=primary_id_column,
                order=safe_order,
            ),
            limit=safe_limit,
            join_clause=join_clause,
        )
        records = _execute_select(connection, sql, params)
        return {
            "enabled": True,
            "success": True,
            "records": records,
            "count": len(records),
            "limit": safe_limit,
            "order": safe_order,
            "warnings": [],
            "errors": [],
        }
    except Exception as exc:  # noqa: BLE001
        return _error_result(exc, order=safe_order)
    finally:
        if managed_connection and connection is not None:
            connection.close()


def _build_select_sql(
    *,
    table: str,
    columns: tuple[str, ...],
    filters: dict[str, Any],
    order_by: str,
    limit: int,
    join_clause: str = "",
) -> tuple[str, dict[str, Any]]:
    params: dict[str, Any] = {}
    where_clauses: list[str] = []
    for index, (column, value) in enumerate(filters.items()):
        if value is None:
            continue
        bind_name = f"filter_{index}"
        where_clauses.append(f"{column} = :{bind_name}")
        params[bind_name] = value

    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    selected_columns = ", ".join(columns)
    return (
        f"SELECT {selected_columns} FROM {table}{join_clause}{where_sql} "
        f"ORDER BY {order_by} FETCH FIRST {limit} ROWS ONLY",
        params,
    )


def _execute_select(connection: Any, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        column_names = [
            str(description[0]).lower()
            for description in (cursor.description or [])
        ]
    return [
        {
            column_name: _serialize_value(value)
            for column_name, value in zip(column_names, row, strict=False)
        }
        for row in rows
    ]


def _count_table(connection: Any, table_name: str, warnings: list[str]) -> int:
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row = cursor.fetchone()
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"{table_name} unavailable: {type(exc).__name__}: {exc}")
        return 0
    if not row:
        return 0
    value = row[0]
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_limit(limit: Any) -> int:
    try:
        normalized = int(limit)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(normalized, MAX_LIMIT))


def _normalize_order(order: Any) -> str:
    normalized = str(order or "newest").strip().lower()
    return normalized if normalized in ORDER_VALUES else "newest"


def _build_order_by(
    *,
    timestamp_column: str,
    primary_id_column: str,
    order: str,
) -> str:
    direction = "ASC" if order == "oldest" else "DESC"
    return (
        f"{timestamp_column} {direction} NULLS LAST, "
        f"{primary_id_column} {direction}"
    )


def _memory_enabled() -> bool:
    raw_value = os.getenv("AWR_MEMORY_ENABLED")
    if raw_value is None:
        return True
    return raw_value.strip().lower() not in DISABLED_VALUES


def _disabled_result(
    summary: dict[str, int] | None = None,
    order: str = "newest",
) -> dict[str, Any]:
    result = {
        "enabled": False,
        "success": True,
        "records": [],
        "count": 0,
        "order": _normalize_order(order),
        "skipped": ["memory_disabled"],
        "warnings": [],
        "errors": [],
    }
    if summary is not None:
        result["summary"] = summary
    return result


def _error_result(
    exc: Exception,
    *,
    summary: dict[str, int] | None = None,
    order: str = "newest",
) -> dict[str, Any]:
    result = {
        "enabled": True,
        "success": False,
        "error": f"{type(exc).__name__}: {exc}",
        "records": [],
        "count": 0,
        "order": _normalize_order(order),
        "warnings": [],
        "errors": [f"{type(exc).__name__}: {exc}"],
    }
    if summary is not None:
        result["summary"] = summary
    return result


def _empty_summary() -> dict[str, int]:
    return {
        "runs": 0,
        "recommendations": 0,
        "actions": 0,
        "outcomes": 0,
        "feedback": 0,
        "unknown_signals": 0,
        "knowledge_requests": 0,
        "knowledge_artifacts": 0,
    }


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if hasattr(value, "read") and callable(value.read):
        return value.read()
    return value
