"""Explicit product visual contracts for the 7RESET dashboard recut."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .shared_product_shapes import ScopeClassification, UnavailableVisualState


VISUAL_CONTRACT_GUARDRAILS: tuple[str, ...] = (
    "allowed_visualizations is not a visual contract",
    "chart metadata is not rendered evidence",
    "fake static svg is not evidence",
    "missing data must produce UnavailableVisualState",
    "source evidence refs exist at series or point level or visual provenance level",
)


@dataclass(frozen=True)
class AxisSpec:
    label: str = ""
    unit: str = ""


@dataclass(frozen=True)
class VisualDataPoint:
    x: str | int | float = ""
    y: int | float | None = None
    unit: str = ""
    evidence_ref_label: str = ""
    completeness_status: str = "unknown"


@dataclass(frozen=True)
class TimeSeriesVisualSeries:
    label: str = ""
    unit: str = ""
    points: tuple[VisualDataPoint, ...] = field(default_factory=tuple)
    evidence_ref_label: str = ""


@dataclass(frozen=True)
class DistributionGroup:
    label: str = ""
    unit: str = ""
    values: tuple[int | float, ...] = field(default_factory=tuple)
    evidence_ref_label: str = ""


@dataclass(frozen=True)
class ComparisonDeltaRow:
    label: str = ""
    target_a_value: str | int | float | None = None
    target_b_value: str | int | float | None = None
    delta_value: str | int | float | None = None
    unit: str = ""
    evidence_ref_label: str = ""


@dataclass(frozen=True)
class TimeSeriesVisual:
    visual_id: str = ""
    visual_kind: Literal["time_series"] = "time_series"
    title: str = ""
    scope_classification: ScopeClassification = "current_scope"
    x_axis: AxisSpec = field(default_factory=AxisSpec)
    y_axis: AxisSpec = field(default_factory=AxisSpec)
    series: tuple[TimeSeriesVisualSeries, ...] = field(default_factory=tuple)
    minimum_point_count: int = 2
    interpolation_allowed: Literal[False] = False
    synthetic_data_allowed: Literal[False] = False
    provenance: tuple[str, ...] = field(default_factory=tuple)
    unavailable_state: UnavailableVisualState | None = None


@dataclass(frozen=True)
class DistributionVisual:
    visual_id: str = ""
    visual_kind: Literal["distribution"] = "distribution"
    title: str = ""
    scope_classification: ScopeClassification = "current_scope"
    metric_name: str = ""
    groups: tuple[DistributionGroup, ...] = field(default_factory=tuple)
    synthetic_data_allowed: Literal[False] = False
    provenance: tuple[str, ...] = field(default_factory=tuple)
    unavailable_state: UnavailableVisualState | None = None


@dataclass(frozen=True)
class ViolinVisual:
    visual_id: str = ""
    visual_kind: Literal["violin"] = "violin"
    distribution: DistributionVisual = field(default_factory=DistributionVisual)
    density_method: str = ""
    density_points: tuple[VisualDataPoint, ...] = field(default_factory=tuple)
    synthetic_data_allowed: Literal[False] = False


@dataclass(frozen=True)
class ComparisonDeltaVisual:
    visual_id: str = ""
    visual_kind: Literal["comparison_delta"] = "comparison_delta"
    title: str = ""
    scope_classification: ScopeClassification = "comparative_output"
    target_a: str = ""
    target_b: str = ""
    delta_rows: tuple[ComparisonDeltaRow, ...] = field(default_factory=tuple)
    synthetic_data_allowed: Literal[False] = False
    provenance: tuple[str, ...] = field(default_factory=tuple)
    unavailable_state: UnavailableVisualState | None = None

