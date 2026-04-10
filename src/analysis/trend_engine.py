"""Deterministic DB-scope metric trend and anomaly analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
import math
import os
from statistics import mean, pstdev
from typing import Any, Protocol

from src.analysis.engineered_metric_catalog import get_metric_definition

LOGGER = logging.getLogger(__name__)
MANDATORY_DB_SCOPE_METRICS = (
    "DB_CPU_PCT_DB_TIME",
    "REDO_GENERATION_PER_SEC",
    "CELL_SINGLE_BLOCK_LATENCY_MS",
)
ZERO_SENSITIVE_METRICS = {"REDO_GENERATION_PER_SEC"}
DEFAULT_WINDOW_SIZE = 3
DEFAULT_BASELINE_POINTS = 3


class DbCursor(Protocol):
    def __enter__(self) -> "DbCursor": ...
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None: ...
    def execute(self, statement: str, parameters: Any = ...) -> Any: ...
    def executemany(self, statement: str, parameters: Any) -> Any: ...
    def fetchall(self) -> Any: ...


class DbConnection(Protocol):
    def cursor(self, *args: Any, **kwargs: Any) -> DbCursor: ...


@dataclass(frozen=True, slots=True)
class MetricSeriesPoint:
    db_name: str
    dbid: int | None
    snap_begin_time: datetime
    snap_end_time: datetime | None
    metric_name: str
    metric_category: str | None
    metric_value_num: float | None
    snapshot_label: str | None
    data_quality_flag: str | None
    value_collapse_rule: str | None
    contributing_report_count: int | None
    awr_count: int | None


@dataclass(frozen=True, slots=True)
class MetricAnomalySemantics:
    metric_type: str
    min_abs_change: float = 0.0
    zero_sensitive: bool = False


FLAG_METRIC_NAMES = {
    "FAILOVER_EVENT_FLAG",
    "ROLE_TRANSITION_FLAG",
    "INTERCONNECT_STRESS_FLAG",
    "POST_FAILOVER_RECOVERY_FLAG",
    "REDO_TRANSPORT_ISSUE_FLAG",
    "RAC_CONTENTION_FLAG",
    "SMART_SCAN_FLAG",
    "EXADATA_IO_BENEFIT_FLAG",
    "FLASH_CACHE_HIT_FLAG",
}
LOW_VARIANCE_MIN_ABS_CHANGE = {
    "CELL_SINGLE_BLOCK_LATENCY_MS": 0.5,
    "READ_LATENCY_MS": 0.5,
    "LOG_FILE_SYNC_MS": 0.5,
}


def load_available_db_metrics(
    conn: DbConnection,
    db_name: str,
    dbid: int | None = None,
) -> list[str]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT METRIC_NAME
              FROM VW_AWR_FEATURE_METRIC_DB_SCOPE
             WHERE DB_NAME = :db_name
               AND (:dbid IS NULL OR DBID = :dbid)
             ORDER BY METRIC_NAME
            """,
            {
                "db_name": db_name,
                "dbid": dbid,
            },
        )
        rows = cursor.fetchall()

    metric_names = [str(row[0] or "").strip() for row in rows if str(row[0] or "").strip()]
    ordered = list(dict.fromkeys(metric_names))
    for metric_name in MANDATORY_DB_SCOPE_METRICS:
        if metric_name not in ordered:
            ordered.append(metric_name)
    return ordered


def load_db_metric_series(
    conn: DbConnection,
    db_name: str,
    metric_name: str,
    dbid: int | None = None,
) -> list[tuple[datetime, float | None]]:
    return [
        (row.snap_begin_time, row.metric_value_num)
        for row in load_db_metric_series_rows(
            conn=conn,
            db_name=db_name,
            metric_name=metric_name,
            dbid=dbid,
        )
    ]


def load_db_metric_series_rows(
    conn: DbConnection,
    db_name: str,
    metric_name: str,
    dbid: int | None = None,
) -> list[MetricSeriesPoint]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                DB_NAME,
                DBID,
                SNAP_BEGIN_TIME,
                SNAP_END_TIME,
                METRIC_NAME,
                METRIC_CATEGORY,
                METRIC_VALUE_NUM,
                SNAPSHOT_LABEL,
                DATA_QUALITY_FLAG,
                VALUE_COLLAPSE_RULE,
                CONTRIBUTING_REPORT_COUNT,
                AWR_COUNT
            FROM VW_AWR_FEATURE_METRIC_DB_SCOPE
            WHERE DB_NAME = :db_name
              AND METRIC_NAME = :metric_name
              AND (:dbid IS NULL OR DBID = :dbid)
            ORDER BY SNAP_BEGIN_TIME
            """,
            {
                "db_name": db_name,
                "metric_name": metric_name,
                "dbid": dbid,
            },
        )
        rows = cursor.fetchall()

    return [
        MetricSeriesPoint(
            db_name=str(row[0] or db_name),
            dbid=_safe_int(row[1]),
            snap_begin_time=row[2],
            snap_end_time=row[3],
            metric_name=str(row[4] or metric_name),
            metric_category=str(row[5] or "").strip() or None,
            metric_value_num=_safe_float(row[6]),
            snapshot_label=str(row[7] or "").strip() or None,
            data_quality_flag=str(row[8] or "").strip() or None,
            value_collapse_rule=str(row[9] or "").strip() or None,
            contributing_report_count=_safe_int(row[10]),
            awr_count=_safe_int(row[11]),
        )
        for row in rows
    ]


def compute_trend_features(
    series: list[tuple[datetime, float | None]],
    window_size: int = DEFAULT_WINDOW_SIZE,
    baseline_points: int = DEFAULT_BASELINE_POINTS,
) -> list[dict[str, Any]]:
    numeric_values = [value for _, value in series if value is not None]
    baseline_sample = numeric_values[:baseline_points]
    baseline_mean = _series_mean(baseline_sample)
    baseline_std = _series_std(baseline_sample)

    features: list[dict[str, Any]] = []
    previous_numeric_value: float | None = None
    previous_slope: float | None = None
    previous_rolling_std: float | None = None
    history_points: list[tuple[int, float]] = []

    for index, (snap_begin_time, value) in enumerate(series):
        trailing_values = [point_value for _, point_value in history_points[-window_size:]]
        rolling_mean = _series_mean(trailing_values)
        rolling_std = _series_std(trailing_values)

        if value is not None:
            regression_points = history_points[-window_size:] + [(index, value)]
        else:
            regression_points = history_points[-window_size:]
        slope = _linear_slope(regression_points)

        if previous_numeric_value in {None, 0.0} or value is None:
            percent_change = None
        else:
            percent_change = round(
                ((value - previous_numeric_value) / abs(previous_numeric_value)) * 100.0,
                4,
            )

        moving_values = trailing_values + ([value] if value is not None else [])
        moving_min = min(moving_values) if moving_values else None
        moving_max = max(moving_values) if moving_values else None

        feature = {
            "snap_begin_time": snap_begin_time,
            "metric_value_num": value,
            "rolling_mean": _rounded(rolling_mean),
            "rolling_std": _rounded(rolling_std),
            "slope": _rounded(slope),
            "percent_change": _rounded(percent_change),
            "moving_min": _rounded(moving_min),
            "moving_max": _rounded(moving_max),
            "baseline_mean": _rounded(baseline_mean),
            "baseline_std": _rounded(baseline_std),
            "previous_slope": _rounded(previous_slope),
            "previous_rolling_std": _rounded(previous_rolling_std),
            "previous_value": _rounded(previous_numeric_value),
            "history_count": len(history_points),
        }
        features.append(feature)

        if value is not None:
            history_points.append((index, value))
            previous_numeric_value = value
        previous_slope = slope
        previous_rolling_std = rolling_std

    return features


def detect_anomalies(
    series: list[tuple[datetime, float | None]],
    trend_features: list[dict[str, Any]],
    metric_name: str,
) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    semantics = _metric_anomaly_semantics(metric_name)
    for (_, value), feature in zip(series, trend_features, strict=True):
        anomaly_flag = "N"
        anomaly_type = None
        anomaly_score = None

        if value is None:
            anomalies.append(
                {
                    "anomaly_flag": anomaly_flag,
                    "anomaly_type": anomaly_type,
                    "anomaly_score": anomaly_score,
                }
            )
            continue

        rolling_mean = feature.get("rolling_mean")
        rolling_std = feature.get("rolling_std")
        baseline_mean = feature.get("baseline_mean")
        baseline_std = feature.get("baseline_std")
        previous_slope = feature.get("previous_slope")
        previous_rolling_std = feature.get("previous_rolling_std")
        slope = feature.get("slope")
        percent_change = feature.get("percent_change")
        previous_value = feature.get("previous_value")
        history_count = feature.get("history_count")

        if semantics.metric_type == "STATE":
            state_anomaly = _detect_state_anomaly(value, previous_value)
            anomalies.append(state_anomaly)
            continue

        if semantics.zero_sensitive and _is_zero_anomaly(value, baseline_mean):
            anomaly_flag = "Y"
            anomaly_type = "ZERO_ANOMALY"
            anomaly_score = _score_zero_anomaly(percent_change, baseline_mean)
        elif _is_spike(
            value,
            rolling_mean,
            rolling_std,
            previous_value,
            semantics.min_abs_change,
        ):
            anomaly_flag = "Y"
            anomaly_type = "SPIKE"
            anomaly_score = _score_deviation(value, rolling_mean, rolling_std, percent_change)
        elif _is_drop(
            value,
            rolling_mean,
            rolling_std,
            previous_value,
            semantics.min_abs_change,
        ):
            anomaly_flag = "Y"
            anomaly_type = "DROP"
            anomaly_score = _score_deviation(value, rolling_mean, rolling_std, percent_change)
        elif _is_trend_shift(
            slope,
            previous_slope,
            baseline_mean,
            baseline_std,
            value,
            previous_value,
            semantics.min_abs_change,
            history_count,
        ):
            anomaly_flag = "Y"
            anomaly_type = "TREND_SHIFT"
            anomaly_score = _score_trend_shift(slope, previous_slope, baseline_mean)
        elif _is_volatility_increase(
            rolling_std,
            previous_rolling_std,
            baseline_std,
            history_count,
            semantics.min_abs_change,
        ):
            anomaly_flag = "Y"
            anomaly_type = "VOLATILITY_INCREASE"
            anomaly_score = _score_volatility_increase(
                rolling_std,
                previous_rolling_std,
                baseline_std,
            )

        anomalies.append(
            {
                "anomaly_flag": anomaly_flag,
                "anomaly_type": anomaly_type,
                "anomaly_score": anomaly_score,
            }
        )
    return anomalies


def build_db_metric_trend_rows(
    conn: DbConnection,
    db_name: str,
    dbid: int | None = None,
    metric_names: list[str] | None = None,
    window_size: int = DEFAULT_WINDOW_SIZE,
    baseline_points: int = DEFAULT_BASELINE_POINTS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidate_metric_names = metric_names or load_available_db_metrics(
        conn=conn,
        db_name=db_name,
        dbid=dbid,
    )
    candidate_metric_names = _apply_metric_name_filter(candidate_metric_names)
    rows: list[dict[str, Any]] = []
    summary_metrics: list[dict[str, Any]] = []
    rendered_domains: set[str] = set()

    for metric_name in candidate_metric_names:
        series_rows = load_db_metric_series_rows(
            conn=conn,
            db_name=db_name,
            metric_name=metric_name,
            dbid=dbid,
        )
        if not series_rows:
            summary_metrics.append(
                {
                    "metric_name": metric_name,
                    "row_count": 0,
                    "domain": _metric_domain(metric_name),
                    "status": "no_rows",
                }
            )
            continue

        series = [(row.snap_begin_time, row.metric_value_num) for row in series_rows]
        trend_features = compute_trend_features(
            series,
            window_size=window_size,
            baseline_points=baseline_points,
        )
        anomaly_features = detect_anomalies(
            series,
            trend_features,
            metric_name=metric_name,
        )

        domain = _metric_domain(metric_name)
        rendered_domains.add(domain)
        for series_row, trend_feature, anomaly_feature in zip(
            series_rows,
            trend_features,
            anomaly_features,
            strict=True,
        ):
            rows.append(
                {
                    "db_name": series_row.db_name,
                    "dbid": series_row.dbid,
                    "metric_name": series_row.metric_name,
                    "snap_begin_time": series_row.snap_begin_time,
                    "metric_value_num": _rounded(series_row.metric_value_num),
                    "rolling_mean": trend_feature["rolling_mean"],
                    "rolling_std": trend_feature["rolling_std"],
                    "slope": trend_feature["slope"],
                    "percent_change": trend_feature["percent_change"],
                    "anomaly_flag": anomaly_feature["anomaly_flag"],
                    "anomaly_type": anomaly_feature["anomaly_type"],
                    "anomaly_score": anomaly_feature["anomaly_score"],
                    "baseline_mean": trend_feature["baseline_mean"],
                    "baseline_std": trend_feature["baseline_std"],
                }
            )

        summary_metrics.append(
            {
                "metric_name": metric_name,
                "row_count": len(series_rows),
                "domain": domain,
                "status": "loaded",
            }
        )

    summary = {
        "db_name": db_name,
        "dbid": dbid,
        "metric_count": len([item for item in summary_metrics if item["status"] == "loaded"]),
        "row_count": len(rows),
        "metrics": summary_metrics,
        "domains": sorted(rendered_domains),
    }
    return rows, summary


def persist_db_metric_trends(
    conn: DbConnection,
    db_name: str,
    dbid: int | None = None,
    metric_names: list[str] | None = None,
    window_size: int = DEFAULT_WINDOW_SIZE,
    baseline_points: int = DEFAULT_BASELINE_POINTS,
) -> dict[str, Any]:
    trend_rows, summary = build_db_metric_trend_rows(
        conn=conn,
        db_name=db_name,
        dbid=dbid,
        metric_names=metric_names,
        window_size=window_size,
        baseline_points=baseline_points,
    )
    target_metric_names = list(
        dict.fromkeys(metric_names or [row["metric_name"] for row in trend_rows])
    )
    delete_db_metric_trends(
        conn=conn,
        db_name=db_name,
        dbid=dbid,
        metric_names=target_metric_names,
    )
    insert_db_metric_trends(conn, trend_rows)
    return {
        **summary,
        "deleted_metric_count": len(target_metric_names),
    }


def delete_db_metric_trends(
    conn: DbConnection,
    db_name: str,
    dbid: int | None,
    metric_names: list[str],
) -> None:
    if not metric_names:
        return
    placeholders = ", ".join(f":metric_name_{index}" for index, _ in enumerate(metric_names))
    binds: dict[str, Any] = {"db_name": db_name, "dbid": dbid}
    for index, metric_name in enumerate(metric_names):
        binds[f"metric_name_{index}"] = metric_name

    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            DELETE FROM AWR_DB_METRIC_TREND
             WHERE DB_NAME = :db_name
               AND (:dbid IS NULL OR DBID = :dbid)
               AND METRIC_NAME IN ({placeholders})
            """,
            binds,
        )


def insert_db_metric_trends(
    conn: DbConnection,
    trend_rows: list[dict[str, Any]],
) -> None:
    if not trend_rows:
        return
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO AWR_DB_METRIC_TREND (
                DB_NAME,
                DBID,
                METRIC_NAME,
                SNAP_BEGIN_TIME,
                METRIC_VALUE_NUM,
                ROLLING_MEAN,
                ROLLING_STD,
                SLOPE,
                PERCENT_CHANGE,
                ANOMALY_FLAG,
                ANOMALY_TYPE,
                ANOMALY_SCORE,
                BASELINE_MEAN,
                BASELINE_STD
            ) VALUES (
                :db_name,
                :dbid,
                :metric_name,
                :snap_begin_time,
                :metric_value_num,
                :rolling_mean,
                :rolling_std,
                :slope,
                :percent_change,
                :anomaly_flag,
                :anomaly_type,
                :anomaly_score,
                :baseline_mean,
                :baseline_std
            )
            """,
            trend_rows,
        )

def _is_spike(
    value: float,
    rolling_mean: float | None,
    rolling_std: float | None,
    previous_value: float | None,
    min_abs_change: float,
) -> bool:
    if rolling_mean is None or rolling_std is None or rolling_std <= 0:
        return False
    if not _has_meaningful_absolute_change(
        value,
        (rolling_mean, previous_value),
        min_abs_change,
    ):
        return False
    return value > rolling_mean + (2.0 * rolling_std)


def _is_drop(
    value: float,
    rolling_mean: float | None,
    rolling_std: float | None,
    previous_value: float | None,
    min_abs_change: float,
) -> bool:
    if rolling_mean is None or rolling_std is None or rolling_std <= 0:
        return False
    if not _has_meaningful_absolute_change(
        value,
        (rolling_mean, previous_value),
        min_abs_change,
    ):
        return False
    return value < rolling_mean - (2.0 * rolling_std)


def _is_zero_anomaly(value: float, baseline_mean: float | None) -> bool:
    if value != 0:
        return False
    if baseline_mean is None:
        return False
    return baseline_mean > 0


def _is_trend_shift(
    slope: float | None,
    previous_slope: float | None,
    baseline_mean: float | None,
    baseline_std: float | None,
    value: float | None,
    previous_value: float | None,
    min_abs_change: float,
    history_count: int | None,
) -> bool:
    if slope is None or previous_slope is None or (history_count or 0) < DEFAULT_WINDOW_SIZE:
        return False
    if value is None:
        return False
    if not _has_meaningful_absolute_change(
        value,
        (previous_value, baseline_mean),
        min_abs_change,
    ):
        return False
    slope_delta = abs(slope - previous_slope)
    threshold = max(
        abs(baseline_mean or 0.0) * 0.15,
        (baseline_std or 0.0),
        0.01,
    )
    sign_changed = slope * previous_slope < 0
    return sign_changed and slope_delta > threshold


def _is_volatility_increase(
    rolling_std: float | None,
    previous_rolling_std: float | None,
    baseline_std: float | None,
    history_count: int | None,
    min_abs_change: float,
) -> bool:
    if (
        rolling_std is None
        or previous_rolling_std is None
        or rolling_std <= 0
        or (history_count or 0) < DEFAULT_WINDOW_SIZE
    ):
        return False
    baseline_reference = baseline_std if baseline_std is not None and baseline_std > 0 else 0.0
    std_increase = rolling_std - max(previous_rolling_std, baseline_reference)
    minimum_increase = max(min_abs_change / 2.0, 0.01)
    return (
        rolling_std > max(previous_rolling_std * 1.5, baseline_reference * 1.5, 0.01)
        and std_increase >= minimum_increase
    )


def _score_deviation(
    value: float,
    rolling_mean: float | None,
    rolling_std: float | None,
    percent_change: float | None,
) -> str:
    if rolling_mean is None or rolling_std is None or rolling_std <= 0:
        return "LOW"
    z_score = abs((value - rolling_mean) / rolling_std)
    if z_score >= 4 or (percent_change is not None and abs(percent_change) >= 100):
        return "HIGH"
    if z_score >= 3 or (percent_change is not None and abs(percent_change) >= 50):
        return "MEDIUM"
    return "LOW"


def _score_zero_anomaly(
    percent_change: float | None,
    baseline_mean: float | None,
) -> str:
    if percent_change is not None and percent_change <= -95:
        return "HIGH"
    if baseline_mean is not None and baseline_mean > 0:
        return "MEDIUM"
    return "LOW"


def _score_trend_shift(
    slope: float | None,
    previous_slope: float | None,
    baseline_mean: float | None,
) -> str:
    if slope is None or previous_slope is None:
        return "LOW"
    delta = abs(slope - previous_slope)
    normalized_delta = delta / max(abs(baseline_mean or 0.0), 1.0)
    if normalized_delta >= 0.5:
        return "HIGH"
    if normalized_delta >= 0.25:
        return "MEDIUM"
    return "LOW"


def _score_volatility_increase(
    rolling_std: float | None,
    previous_rolling_std: float | None,
    baseline_std: float | None,
) -> str:
    if rolling_std is None or previous_rolling_std is None:
        return "LOW"
    reference = max(previous_rolling_std, baseline_std or 0.0, 0.01)
    ratio = rolling_std / reference
    if ratio >= 2.0:
        return "HIGH"
    if ratio >= 1.5:
        return "MEDIUM"
    return "LOW"


def _linear_slope(points: list[tuple[int, float]]) -> float | None:
    if len(points) < 2:
        return None
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    x_mean = mean(xs)
    y_mean = mean(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator <= 0:
        return None
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=True))
    return numerator / denominator


def _series_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return mean(values)


def _series_std(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    return pstdev(values)


def _metric_domain(metric_name: str) -> str:
    definition = get_metric_definition(metric_name)
    return definition.domain if definition is not None else "UNKNOWN"


def _metric_anomaly_semantics(metric_name: str) -> MetricAnomalySemantics:
    normalized_metric_name = metric_name.strip().upper()
    if normalized_metric_name in FLAG_METRIC_NAMES or normalized_metric_name.endswith("_FLAG"):
        return MetricAnomalySemantics(metric_type="STATE")
    return MetricAnomalySemantics(
        metric_type="CONTINUOUS",
        min_abs_change=LOW_VARIANCE_MIN_ABS_CHANGE.get(normalized_metric_name, 0.0),
        zero_sensitive=normalized_metric_name in ZERO_SENSITIVE_METRICS,
    )


def _detect_state_anomaly(
    value: float,
    previous_value: float | None,
) -> dict[str, Any]:
    if previous_value is None or value == previous_value:
        return {
            "anomaly_flag": "N",
            "anomaly_type": None,
            "anomaly_score": None,
        }

    previous_is_active = _is_active_state(previous_value)
    current_is_active = _is_active_state(value)
    if not previous_is_active and current_is_active:
        anomaly_type = "ACTIVATED"
        anomaly_score = "MEDIUM"
    elif previous_is_active and not current_is_active:
        anomaly_type = "CLEARED"
        anomaly_score = "LOW"
    else:
        anomaly_type = "STATE_CHANGE"
        anomaly_score = "LOW"

    return {
        "anomaly_flag": "Y",
        "anomaly_type": anomaly_type,
        "anomaly_score": anomaly_score,
    }


def _is_active_state(value: float | None) -> bool:
    if value is None:
        return False
    return value != 0.0


def _has_meaningful_absolute_change(
    value: float,
    references: tuple[float | None, ...],
    min_abs_change: float,
) -> bool:
    if min_abs_change <= 0:
        return True
    deltas = [abs(value - reference) for reference in references if reference is not None]
    if not deltas:
        return False
    return max(deltas) >= min_abs_change


def _apply_metric_name_filter(metric_names: list[str]) -> list[str]:
    raw_filter = os.getenv("AWR_TREND_METRIC_NAME", "").strip()
    if not raw_filter:
        return metric_names

    requested_metrics = [
        token.strip().upper()
        for token in raw_filter.split(",")
        if token.strip()
    ]
    if not requested_metrics:
        LOGGER.warning(
            "Ignoring empty AWR_TREND_METRIC_NAME after parsing; continuing with all %s metrics",
            len(metric_names),
        )
        return metric_names

    available_metric_map = {metric_name.upper(): metric_name for metric_name in metric_names}
    filtered_metric_names = [
        available_metric_map[metric_name]
        for metric_name in requested_metrics
        if metric_name in available_metric_map
    ]
    unknown_metrics = [
        metric_name
        for metric_name in requested_metrics
        if metric_name not in available_metric_map
    ]

    LOGGER.info(
        "Applying DB trend metric filter: requested=%s before=%s after=%s",
        ",".join(requested_metrics),
        len(metric_names),
        len(filtered_metric_names),
    )
    if unknown_metrics:
        LOGGER.warning(
            "Ignoring unknown DB trend metric filter value(s): %s",
            ", ".join(unknown_metrics),
        )
    if not filtered_metric_names:
        LOGGER.warning(
            "No DB trend metrics matched AWR_TREND_METRIC_NAME for the selected scope; skipping trend analysis"
        )
        return []

    return list(dict.fromkeys(filtered_metric_names))


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _rounded(value: float | None) -> float | None:
    if value is None or math.isnan(value) or math.isinf(value):
        return None
    return round(value, 6)
