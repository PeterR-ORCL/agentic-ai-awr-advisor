"""Screen 4 Comparative Review visual eligibility guardrails.

This module decides whether future Screen 4 comparative visuals have enough
validated deterministic evidence to render. It does not render charts, create
samples, infer time-series points, or compute comparison truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Any


STATUS_ELIGIBLE = "eligible"
STATUS_BLOCKED = "blocked"
STATUS_OMITTED = "omitted"
STATUS_NOT_REQUESTED = "not_requested"
STATUS_NOT_SUPPORTED = "not_supported"
VALID_STATUSES = {
    STATUS_ELIGIBLE,
    STATUS_BLOCKED,
    STATUS_OMITTED,
    STATUS_NOT_REQUESTED,
    STATUS_NOT_SUPPORTED,
}

TIME_SERIES_OVERLAY = "time_series_overlay"
DISTRIBUTION_VIOLIN = "distribution_violin"
TOP_SQL_MOVEMENT_TABLE = "top_sql_movement_table"
WAIT_CLASS_MOVEMENT_TABLE = "wait_class_movement_table"
TOP_EVENT_MOVEMENT_TABLE = "top_event_movement_table"

SUPPORTED_VISUALIZATIONS = {
    TIME_SERIES_OVERLAY,
    DISTRIBUTION_VIOLIN,
    TOP_SQL_MOVEMENT_TABLE,
    WAIT_CLASS_MOVEMENT_TABLE,
    TOP_EVENT_MOVEMENT_TABLE,
}
DEFAULT_VISUALIZATION_ORDER = (
    TIME_SERIES_OVERLAY,
    DISTRIBUTION_VIOLIN,
    TOP_SQL_MOVEMENT_TABLE,
    WAIT_CLASS_MOVEMENT_TABLE,
    TOP_EVENT_MOVEMENT_TABLE,
)

VISUALIZATION_LABELS = {
    TIME_SERIES_OVERLAY: "Time-series Overlay",
    DISTRIBUTION_VIOLIN: "Distribution / Violin Evidence",
    TOP_SQL_MOVEMENT_TABLE: "SQL Movement",
    WAIT_CLASS_MOVEMENT_TABLE: "Wait/Event Movement",
    TOP_EVENT_MOVEMENT_TABLE: "Top Event Movement",
}

MIN_DISTRIBUTION_SAMPLES_PER_TARGET = 3


@dataclass(frozen=True)
class Screen4ComparativeVisualEligibility:
    """Eligibility result for one Screen 4 comparative visualization."""

    visualization_name: str
    status: str
    rendering_allowed: bool
    reason_code: str
    reason: str
    required_fields: tuple[str, ...] = ()
    evidence_count: int = 0
    missing_fields: tuple[str, ...] = ()
    supported: bool = True
    notes: tuple[str, ...] = ()
    visualization_label: str = ""

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Unsupported visual eligibility status: {self.status}")
        if self.rendering_allowed and self.status != STATUS_ELIGIBLE:
            raise ValueError("rendering_allowed requires eligible status.")
        if not self.visualization_name:
            raise ValueError("visualization_name is required.")
        if not self.reason_code:
            raise ValueError("reason_code is required.")
        if not self.reason:
            raise ValueError("reason is required.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "visualization_name": self.visualization_name,
            "visualization_label": self.visualization_label,
            "status": self.status,
            "rendering_allowed": self.rendering_allowed,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "required_fields": list(self.required_fields),
            "evidence_count": self.evidence_count,
            "missing_fields": list(self.missing_fields),
            "supported": self.supported,
            "notes": list(self.notes),
        }


def evaluate_screen4_comparative_visual_eligibility(
    contract: Any,
    visualization_name: str,
) -> Screen4ComparativeVisualEligibility:
    """Return eligibility for one future Screen 4 comparative visualization."""

    visualization = str(visualization_name or "").strip()
    if not visualization:
        return _result(
            visualization_name="unknown",
            status=STATUS_NOT_SUPPORTED,
            reason_code="visualization_name_missing",
            reason="Visualization name is required.",
            supported=False,
        )

    if _is_fleet_or_population_visualization(visualization):
        return _fleet_result(contract, visualization)
    if visualization not in SUPPORTED_VISUALIZATIONS:
        return _result(
            visualization_name=visualization,
            status=STATUS_NOT_SUPPORTED,
            reason_code="visualization_not_supported",
            reason=f"{_label(visualization)} is outside the 7CX-G visual eligibility scope.",
            supported=False,
        )

    if not _is_screen4_deterministic_contract(contract):
        return _result(
            visualization_name=visualization,
            status=STATUS_BLOCKED,
            reason_code="deterministic_contract_invalid",
            reason=(
                f"{_label(visualization)} is blocked because a validated deterministic "
                "comparison output contract is required."
            ),
            required_fields=("screen4_contract_type", "generated_by", "validation_status"),
            missing_fields=_contract_boundary_missing_fields(contract),
        )

    if visualization not in _allowed_visualizations(contract):
        return _result(
            visualization_name=visualization,
            status=STATUS_NOT_REQUESTED,
            reason_code="allowed_visualization_missing",
            reason=f"{_label(visualization)} is not requested by allowed_visualizations.",
            required_fields=("allowed_visualizations",),
            missing_fields=(visualization,),
        )

    if visualization == TIME_SERIES_OVERLAY:
        return _evaluate_time_series_overlay(contract)
    if visualization == DISTRIBUTION_VIOLIN:
        return _evaluate_distribution_violin(contract)
    if visualization == TOP_SQL_MOVEMENT_TABLE:
        return _evaluate_sql_movement(contract)
    if visualization in {WAIT_CLASS_MOVEMENT_TABLE, TOP_EVENT_MOVEMENT_TABLE}:
        return _evaluate_event_movement(contract, visualization)

    return _result(
        visualization_name=visualization,
        status=STATUS_NOT_SUPPORTED,
        reason_code="visualization_not_supported",
        reason=f"{_label(visualization)} is outside the 7CX-G visual eligibility scope.",
        supported=False,
    )


def build_screen4_comparative_visual_eligibility(
    contract: Any,
    visualization_names: list[str] | tuple[str, ...] | None = None,
    *,
    include_not_requested: bool = False,
) -> list[Screen4ComparativeVisualEligibility]:
    """Evaluate multiple comparative visuals without producing render markup."""

    names = list(
        DEFAULT_VISUALIZATION_ORDER
        if visualization_names is None
        else visualization_names
    )
    results = [
        evaluate_screen4_comparative_visual_eligibility(contract, name)
        for name in names
    ]
    if include_not_requested:
        return results
    return [
        result
        for result in results
        if result.status not in {STATUS_NOT_REQUESTED, STATUS_OMITTED}
    ]


def _evaluate_time_series_overlay(
    contract: dict[str, Any],
) -> Screen4ComparativeVisualEligibility:
    rows = _time_series_rows(contract)
    required = (
        "allowed_visualizations",
        "time_series_rows[].timestamp",
        "time_series_rows[].metric_key",
        "time_series_rows[].target_a_value",
        "time_series_rows[].target_b_value",
    )
    if not rows:
        return _blocked(
            TIME_SERIES_OVERLAY,
            "aligned_time_series_rows_missing",
            "Time-series overlay is blocked because aligned time-series rows are missing.",
            required_fields=required,
            missing_fields=("time_series_rows",),
        )

    for row in rows:
        if not _has_text(row.get("metric_key")):
            return _blocked(
                TIME_SERIES_OVERLAY,
                "missing_metric_identity",
                "Time-series overlay is blocked because a metric key is missing.",
                required_fields=required,
                missing_fields=("metric_key",),
                evidence_count=len(rows),
            )
        if not _has_text(row.get("timestamp")):
            return _blocked(
                TIME_SERIES_OVERLAY,
                "missing_timestamp",
                "Time-series overlay is blocked because a timestamp is missing.",
                required_fields=required,
                missing_fields=("timestamp",),
                evidence_count=len(rows),
            )
        if not _has_value(row.get("target_a_value")):
            return _blocked(
                TIME_SERIES_OVERLAY,
                "missing_target_a_value",
                "Time-series overlay is blocked because a Target A value is missing.",
                required_fields=required,
                missing_fields=("target_a_value",),
                evidence_count=len(rows),
            )
        if not _has_value(row.get("target_b_value")):
            return _blocked(
                TIME_SERIES_OVERLAY,
                "missing_target_b_value",
                "Time-series overlay is blocked because a Target B value is missing.",
                required_fields=required,
                missing_fields=("target_b_value",),
                evidence_count=len(rows),
            )
        if not _is_number(row.get("target_a_value")) or not _is_number(row.get("target_b_value")):
            return _blocked(
                TIME_SERIES_OVERLAY,
                "non_numeric_time_series_value",
                "Time-series overlay is blocked because Target A/B values must be numeric.",
                required_fields=required,
                missing_fields=("target_a_value", "target_b_value"),
                evidence_count=len(rows),
            )

    metric_counts: dict[str, int] = {}
    for row in rows:
        metric_key = str(row["metric_key"]).strip()
        metric_counts[metric_key] = metric_counts.get(metric_key, 0) + 1
    evidence_count = max(metric_counts.values()) if metric_counts else 0
    if evidence_count < 2:
        return _blocked(
            TIME_SERIES_OVERLAY,
            "insufficient_time_series_points",
            "Time-series overlay is blocked because at least two aligned points are required for one metric.",
            required_fields=required,
            evidence_count=evidence_count,
        )
    return _eligible(
        TIME_SERIES_OVERLAY,
        "aligned_time_series_rows_present",
        "Time-series overlay has aligned numeric Target A/B points for at least one metric.",
        required_fields=required,
        evidence_count=evidence_count,
    )


def _evaluate_distribution_violin(
    contract: dict[str, Any],
) -> Screen4ComparativeVisualEligibility:
    rows = _distribution_rows(contract)
    required = (
        "allowed_visualizations",
        "distribution_rows[].metric_key",
        "distribution_rows[].target_a_samples",
        "distribution_rows[].target_b_samples",
    )
    if not rows:
        return _blocked(
            DISTRIBUTION_VIOLIN,
            "distribution_samples_missing",
            "Distribution violin is blocked because distribution sample rows are missing.",
            required_fields=required,
            missing_fields=("distribution_rows",),
        )

    separate_samples: dict[str, dict[str, list[Any]]] = {}
    separate_metric_order: list[str] = []
    for row in rows:
        metric_key = row.get("metric_key")
        if not _has_text(metric_key):
            return _blocked(
                DISTRIBUTION_VIOLIN,
                "missing_metric_identity",
                "Distribution violin is blocked because a metric key is missing.",
                required_fields=required,
                missing_fields=("metric_key",),
                evidence_count=len(rows),
            )
        metric = str(metric_key).strip()
        target_a_samples = row.get("target_a_samples")
        target_b_samples = row.get("target_b_samples")
        if target_a_samples is not None or target_b_samples is not None:
            if not _has_samples(target_a_samples):
                return _blocked(
                    DISTRIBUTION_VIOLIN,
                    "target_a_samples_missing",
                    "Distribution violin is blocked because Target A samples are missing.",
                    required_fields=required,
                    missing_fields=("target_a_samples",),
                    evidence_count=len(rows),
                )
            if not _has_samples(target_b_samples):
                return _blocked(
                    DISTRIBUTION_VIOLIN,
                    "target_b_samples_missing",
                    "Distribution violin is blocked because Target B samples are missing.",
                    required_fields=required,
                    missing_fields=("target_b_samples",),
                    evidence_count=len(rows),
                )
            invalid_sample = _non_numeric_sample(target_a_samples) or _non_numeric_sample(target_b_samples)
            if invalid_sample:
                return _blocked(
                    DISTRIBUTION_VIOLIN,
                    "non_numeric_distribution_sample",
                    "Distribution violin is blocked because samples must be numeric.",
                    required_fields=required,
                    missing_fields=("samples",),
                    evidence_count=len(rows),
                )
            if (
                len(target_a_samples) < MIN_DISTRIBUTION_SAMPLES_PER_TARGET
                or len(target_b_samples) < MIN_DISTRIBUTION_SAMPLES_PER_TARGET
            ):
                return _blocked(
                    DISTRIBUTION_VIOLIN,
                    "insufficient_distribution_samples",
                    "Distribution violin is blocked because at least three samples per target are required.",
                    required_fields=required,
                    evidence_count=min(len(target_a_samples), len(target_b_samples)),
                )
            return _eligible(
                DISTRIBUTION_VIOLIN,
                "distribution_samples_present",
                "Distribution violin has numeric Target A/B sample arrays for one metric.",
                required_fields=required,
                evidence_count=min(len(target_a_samples), len(target_b_samples)),
            )

        target = _normalize_target_side(row.get("target"))
        samples = row.get("samples")
        if target not in {"A", "B"}:
            return _blocked(
                DISTRIBUTION_VIOLIN,
                "target_a_samples_missing",
                "Distribution violin is blocked because separate sample rows must identify Target A or Target B.",
                required_fields=required,
                missing_fields=("target",),
                evidence_count=len(rows),
            )
        if not _has_samples(samples):
            missing_code = "target_a_samples_missing" if target == "A" else "target_b_samples_missing"
            return _blocked(
                DISTRIBUTION_VIOLIN,
                missing_code,
                f"Distribution violin is blocked because Target {target} samples are missing.",
                required_fields=required,
                missing_fields=("samples",),
                evidence_count=len(rows),
            )
        if _non_numeric_sample(samples):
            return _blocked(
                DISTRIBUTION_VIOLIN,
                "non_numeric_distribution_sample",
                "Distribution violin is blocked because samples must be numeric.",
                required_fields=required,
                missing_fields=("samples",),
                evidence_count=len(rows),
            )
        if metric not in separate_samples:
            separate_samples[metric] = {}
            separate_metric_order.append(metric)
        separate_samples[metric][target] = list(samples)

    for metric in separate_metric_order:
        samples_by_target = separate_samples[metric]
        if "A" not in samples_by_target:
            return _blocked(
                DISTRIBUTION_VIOLIN,
                "target_a_samples_missing",
                "Distribution violin is blocked because Target A samples are missing.",
                required_fields=required,
                missing_fields=("target_a_samples",),
                evidence_count=len(rows),
            )
        if "B" not in samples_by_target:
            return _blocked(
                DISTRIBUTION_VIOLIN,
                "target_b_samples_missing",
                "Distribution violin is blocked because Target B samples are missing.",
                required_fields=required,
                missing_fields=("target_b_samples",),
                evidence_count=len(rows),
            )
        a_count = len(samples_by_target["A"])
        b_count = len(samples_by_target["B"])
        if a_count < MIN_DISTRIBUTION_SAMPLES_PER_TARGET or b_count < MIN_DISTRIBUTION_SAMPLES_PER_TARGET:
            return _blocked(
                DISTRIBUTION_VIOLIN,
                "insufficient_distribution_samples",
                "Distribution violin is blocked because at least three samples per target are required.",
                required_fields=required,
                evidence_count=min(a_count, b_count),
            )
        return _eligible(
            DISTRIBUTION_VIOLIN,
            "distribution_samples_present",
            "Distribution violin has numeric Target A/B sample rows for one metric.",
            required_fields=required,
            evidence_count=min(a_count, b_count),
        )

    return _blocked(
        DISTRIBUTION_VIOLIN,
        "distribution_samples_missing",
        "Distribution violin is blocked because distribution sample rows are missing.",
        required_fields=required,
        missing_fields=("distribution_rows",),
    )


def _evaluate_sql_movement(
    contract: dict[str, Any],
) -> Screen4ComparativeVisualEligibility:
    return _evaluate_movement_rows(
        contract,
        TOP_SQL_MOVEMENT_TABLE,
        identity_keys=("stable_sql_identity", "sql_id", "sql_signature", "sql_plan_hash"),
        missing_identity_code="stable_sql_identity_missing",
        missing_identity_reason="SQL movement is blocked because persistent SQL identity is missing.",
    )


def _evaluate_event_movement(
    contract: dict[str, Any],
    visualization: str,
) -> Screen4ComparativeVisualEligibility:
    return _evaluate_movement_rows(
        contract,
        visualization,
        identity_keys=(
            "stable_event_identity",
            "event_id",
            "event_name",
            "wait_event_id",
            "wait_event",
            "wait_class",
        ),
        missing_identity_code="stable_event_identity_missing",
        missing_identity_reason=(
            f"{_label(visualization)} is blocked because persistent event/wait identity is missing."
        ),
    )


def _evaluate_movement_rows(
    contract: dict[str, Any],
    visualization: str,
    *,
    identity_keys: tuple[str, ...],
    missing_identity_code: str,
    missing_identity_reason: str,
) -> Screen4ComparativeVisualEligibility:
    rows = _movement_rows(contract, visualization)
    required = (
        "allowed_visualizations",
        "evidence_rows[].stable_identity",
        "evidence_rows[].target_a_value",
        "evidence_rows[].target_b_value",
    )
    if not rows:
        return _blocked(
            visualization,
            "movement_rows_missing",
            f"{_label(visualization)} is blocked because movement evidence rows are missing.",
            required_fields=required,
            missing_fields=("evidence_rows",),
        )
    for row in rows:
        if not any(_has_text(row.get(key)) for key in identity_keys):
            return _blocked(
                visualization,
                missing_identity_code,
                missing_identity_reason,
                required_fields=required,
                missing_fields=identity_keys,
                evidence_count=len(rows),
            )
        target_a = _first_present(row.get("target_a_value"), row.get("baseline_value"))
        target_b = _first_present(row.get("target_b_value"), row.get("candidate_value"))
        if not _has_value(target_a) or not _has_value(target_b):
            return _blocked(
                visualization,
                "movement_values_missing",
                f"{_label(visualization)} is blocked because Target A/B values are missing.",
                required_fields=required,
                missing_fields=("target_a_value", "target_b_value"),
                evidence_count=len(rows),
            )
        if not _is_number(target_a) or not _is_number(target_b):
            return _blocked(
                visualization,
                "non_numeric_movement_value",
                f"{_label(visualization)} is blocked because Target A/B values must be numeric.",
                required_fields=required,
                missing_fields=("target_a_value", "target_b_value"),
                evidence_count=len(rows),
            )
    return _eligible(
        visualization,
        "movement_rows_present",
        f"{_label(visualization)} has persistent identity and numeric Target A/B values.",
        required_fields=required,
        evidence_count=len(rows),
    )


def _time_series_rows(contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key in (
        "time_series_rows",
        "aligned_time_series_rows",
        "time_series_evidence_rows",
    ):
        rows.extend(_dict_rows(contract.get(key)))
    rows.extend(_visual_evidence_rows(contract, TIME_SERIES_OVERLAY))
    rows.extend(
        row
        for row in _dict_rows(contract.get("evidence_rows"))
        if _row_visualization(row) == TIME_SERIES_OVERLAY
    )
    return rows


def _distribution_rows(contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key in (
        "distribution_rows",
        "distribution_sample_rows",
        "distribution_evidence_rows",
    ):
        rows.extend(_dict_rows(contract.get(key)))
    rows.extend(_visual_evidence_rows(contract, DISTRIBUTION_VIOLIN))
    rows.extend(
        row
        for row in _dict_rows(contract.get("evidence_rows"))
        if _row_visualization(row) == DISTRIBUTION_VIOLIN
    )
    return rows


def _movement_rows(contract: dict[str, Any], visualization: str) -> list[dict[str, Any]]:
    rows = []
    for key in ("movement_rows", "visual_movement_rows"):
        rows.extend(
            row
            for row in _dict_rows(contract.get(key))
            if _row_visualization(row) in {"", visualization}
        )
    rows.extend(_visual_evidence_rows(contract, visualization))
    evidence_rows = _dict_rows(contract.get("evidence_rows"))
    if visualization == TOP_SQL_MOVEMENT_TABLE:
        rows.extend(
            row
            for row in evidence_rows
            if _row_visualization(row) == visualization
            or _row_category(row) == "sql"
            or any(_has_text(row.get(key)) for key in ("sql_id", "stable_sql_identity", "sql_signature"))
        )
    else:
        rows.extend(
            row
            for row in evidence_rows
            if _row_visualization(row) == visualization
            or _row_category(row) in {"wait", "event", "wait_event"}
            or any(_has_text(row.get(key)) for key in ("event_id", "event_name", "wait_event", "stable_event_identity"))
        )
    return rows


def _visual_evidence_rows(contract: dict[str, Any], visualization: str) -> list[dict[str, Any]]:
    rows = []
    for key in ("visual_evidence", "comparative_visual_evidence", "visualization_evidence"):
        value = contract.get(key)
        if isinstance(value, dict):
            rows.extend(_dict_rows(value.get(visualization)))
    return rows


def _fleet_result(
    contract: Any,
    visualization: str,
) -> Screen4ComparativeVisualEligibility:
    if not isinstance(contract, dict):
        return _result(
            visualization_name=visualization,
            status=STATUS_NOT_SUPPORTED,
            reason_code="fleet_contract_missing",
            reason=f"{_label(visualization)} is not supported without a fleet/population evidence contract.",
            supported=False,
            required_fields=("fleet_evidence_contract",),
            missing_fields=("fleet_evidence_contract",),
        )
    fleet_contract = contract.get("fleet_evidence_contract")
    if (
        not isinstance(fleet_contract, dict)
        or not _has_text(fleet_contract.get("contract_id"))
        or fleet_contract.get("generated_by") != "deterministic_engine"
    ):
        return _result(
            visualization_name=visualization,
            status=STATUS_NOT_SUPPORTED,
            reason_code="fleet_contract_missing",
            reason=f"{_label(visualization)} is not supported without a fleet/population evidence contract.",
            supported=False,
            required_fields=("fleet_evidence_contract",),
            missing_fields=("fleet_evidence_contract",),
        )
    return _result(
        visualization_name=visualization,
        status=STATUS_NOT_SUPPORTED,
        reason_code="fleet_visual_not_in_7cx_g_scope",
        reason=f"{_label(visualization)} remains outside the 7CX-G scope.",
        supported=False,
        required_fields=("fleet_evidence_contract",),
    )


def _eligible(
    visualization: str,
    reason_code: str,
    reason: str,
    *,
    required_fields: tuple[str, ...],
    evidence_count: int,
    notes: tuple[str, ...] = (),
) -> Screen4ComparativeVisualEligibility:
    return _result(
        visualization_name=visualization,
        status=STATUS_ELIGIBLE,
        rendering_allowed=True,
        reason_code=reason_code,
        reason=reason,
        required_fields=required_fields,
        evidence_count=evidence_count,
        notes=notes,
    )


def _blocked(
    visualization: str,
    reason_code: str,
    reason: str,
    *,
    required_fields: tuple[str, ...],
    missing_fields: tuple[str, ...] = (),
    evidence_count: int = 0,
    notes: tuple[str, ...] = (),
) -> Screen4ComparativeVisualEligibility:
    return _result(
        visualization_name=visualization,
        status=STATUS_BLOCKED,
        reason_code=reason_code,
        reason=reason,
        required_fields=required_fields,
        missing_fields=missing_fields,
        evidence_count=evidence_count,
        notes=notes,
    )


def _result(
    *,
    visualization_name: str,
    status: str,
    reason_code: str,
    reason: str,
    rendering_allowed: bool = False,
    required_fields: tuple[str, ...] = (),
    evidence_count: int = 0,
    missing_fields: tuple[str, ...] = (),
    supported: bool = True,
    notes: tuple[str, ...] = (),
) -> Screen4ComparativeVisualEligibility:
    return Screen4ComparativeVisualEligibility(
        visualization_name=visualization_name,
        visualization_label=_label(visualization_name),
        status=status,
        rendering_allowed=rendering_allowed,
        reason_code=reason_code,
        reason=reason,
        required_fields=required_fields,
        evidence_count=evidence_count,
        missing_fields=missing_fields,
        supported=supported,
        notes=notes,
    )


def _is_screen4_deterministic_contract(contract: Any) -> bool:
    if not isinstance(contract, dict):
        return False
    if contract.get("screen4_contract_type") != "deterministic_comparison_output":
        return False
    if contract.get("generated_by") != "deterministic_engine":
        return False
    if contract.get("validation_status") != "valid":
        return False
    return isinstance(contract.get("allowed_visualizations"), list)


def _contract_boundary_missing_fields(contract: Any) -> tuple[str, ...]:
    if not isinstance(contract, dict):
        return ("screen4_contract_type", "generated_by", "validation_status")
    missing = []
    if contract.get("screen4_contract_type") != "deterministic_comparison_output":
        missing.append("screen4_contract_type")
    if contract.get("generated_by") != "deterministic_engine":
        missing.append("generated_by")
    if contract.get("validation_status") != "valid":
        missing.append("validation_status")
    if not isinstance(contract.get("allowed_visualizations"), list):
        missing.append("allowed_visualizations")
    return tuple(missing)


def _allowed_visualizations(contract: dict[str, Any]) -> set[str]:
    value = contract.get("allowed_visualizations")
    if not isinstance(value, list):
        return set()
    return {
        str(item).strip()
        for item in value
        if _has_text(item)
    }


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict) and row]


def _row_visualization(row: dict[str, Any]) -> str:
    return str(
        row.get("visualization")
        or row.get("visualization_name")
        or row.get("visual_type")
        or ""
    ).strip()


def _row_category(row: dict[str, Any]) -> str:
    return str(row.get("category") or row.get("type") or "").strip().lower()


def _label(visualization: str) -> str:
    if visualization in VISUALIZATION_LABELS:
        return VISUALIZATION_LABELS[visualization]
    return str(visualization or "Unknown Visualization").replace("_", " ").title()


def _is_fleet_or_population_visualization(visualization: str) -> bool:
    normalized = visualization.lower()
    return "fleet" in normalized or "population" in normalized


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_value(value: Any) -> bool:
    return value is not None and value != ""


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _has_samples(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _non_numeric_sample(value: Any) -> bool:
    if not isinstance(value, list):
        return True
    return any(not _is_number(item) for item in value)


def _normalize_target_side(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"a", "target_a", "target a", "baseline", "target-a"}:
        return "A"
    if text in {"b", "target_b", "target b", "candidate", "target-b"}:
        return "B"
    return ""


def _first_present(*values: Any) -> Any:
    for value in values:
        if _has_value(value):
            return value
    return None
