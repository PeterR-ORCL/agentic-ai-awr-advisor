"""Phase 7V shadow ML model interface records.

This module defines deterministic, local-only shadow ML interface objects. It
represents ML-style score outputs for comparison without training, persisted
models, service calls, or runtime scoring influence.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence


SHADOW_MODEL_FAMILIES = (
    "tree",
    "neural_net",
    "hybrid_rule_ml",
    "linear",
    "baseline_mock",
    "external_placeholder",
)

SHADOW_ML_ADVISORY_STATUSES = (
    "SHADOW_ONLY",
    "ADVISORY_ONLY",
    "INSUFFICIENT_MODEL_CONTEXT",
    "INVALID_INPUT",
)

SHADOW_MODEL_METADATA_FIELDS = (
    "model_id",
    "model_family",
    "model_version",
    "feature_schema_version",
    "label_schema_version",
    "training_reference",
    "validation_reference",
    "runtime_active",
    "runtime_influence_granted",
    "notes",
)

SHADOW_ML_INPUT_FIELDS = (
    "input_id",
    "run_id",
    "awr_id",
    "feature_reference",
    "dataset_reference",
    "deterministic_score",
    "trend_aware_score",
    "feature_values",
    "model_id",
    "score_version",
    "runtime_influence",
    "runtime_active",
)

SHADOW_ML_OUTPUT_FIELDS = (
    "output_id",
    "input_id",
    "model_id",
    "model_family",
    "deterministic_score",
    "trend_aware_score",
    "shadow_ml_score",
    "ml_delta_from_deterministic",
    "ml_delta_from_trend_aware",
    "confidence",
    "advisory_status",
    "disagreement_summary",
    "boundary_summary",
    "runtime_influence",
    "runtime_active",
    "runtime_influence_granted",
    "deterministic_runtime_remains_authoritative",
)

MAX_PLACEHOLDER_CONFIDENCE = 0.95
MAX_TREND_BLEND_ADJUSTMENT = 8.0
MAX_RISK_FEATURE_ADJUSTMENT = 5.0


class ShadowMLInterfaceError(ValueError):
    """Raised when Phase 7V shadow ML interface rules are violated."""


@dataclass(frozen=True)
class ShadowModelMetadata:
    """Serializable model metadata for a non-active shadow ML interface."""

    model_id: str
    model_family: str
    model_version: str
    feature_schema_version: str | None
    label_schema_version: str | None
    training_reference: str | None
    validation_reference: str | None
    runtime_active: bool
    runtime_influence_granted: bool
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.model_id, "model_id")
        model_family = _normalize_model_family(self.model_family)
        _require_non_empty_string(self.model_version, "model_version")
        _validate_optional_string(
            self.feature_schema_version,
            "feature_schema_version",
        )
        _validate_optional_string(self.label_schema_version, "label_schema_version")
        _validate_optional_string(self.training_reference, "training_reference")
        _validate_optional_string(self.validation_reference, "validation_reference")
        _validate_optional_string(self.notes, "notes")
        if self.runtime_active is not False:
            raise ShadowMLInterfaceError(
                "Phase 7V shadow model metadata must keep runtime_active=false."
            )
        if self.runtime_influence_granted is not False:
            raise ShadowMLInterfaceError(
                "Phase 7V shadow model metadata must keep "
                "runtime_influence_granted=false."
            )
        object.__setattr__(self, "model_family", model_family)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)


@dataclass(frozen=True)
class ShadowMLInput:
    """Serializable local input record for a shadow Score_ml(x) contract."""

    input_id: str
    run_id: str | None
    awr_id: str | None
    feature_reference: str | None
    dataset_reference: str | None
    deterministic_score: float
    trend_aware_score: float | None
    feature_values: dict[str, object]
    model_id: str
    score_version: str
    runtime_influence: bool
    runtime_active: bool

    def __post_init__(self) -> None:
        _require_non_empty_string(self.input_id, "input_id")
        _validate_optional_string(self.run_id, "run_id")
        _validate_optional_string(self.awr_id, "awr_id")
        _require_any_identifier(self.run_id, self.awr_id)
        _validate_optional_string(self.feature_reference, "feature_reference")
        _validate_optional_string(self.dataset_reference, "dataset_reference")
        _validate_score(self.deterministic_score, "deterministic_score")
        if self.trend_aware_score is not None:
            _validate_score(self.trend_aware_score, "trend_aware_score")
        _validate_feature_values(self.feature_values)
        _require_non_empty_string(self.model_id, "model_id")
        _require_non_empty_string(self.score_version, "score_version")
        if self.runtime_influence is not False:
            raise ShadowMLInterfaceError(
                "Phase 7V shadow ML inputs must keep runtime_influence=false."
            )
        if self.runtime_active is not False:
            raise ShadowMLInterfaceError(
                "Phase 7V shadow ML inputs must keep runtime_active=false."
            )
        object.__setattr__(
            self,
            "deterministic_score",
            float(self.deterministic_score),
        )
        object.__setattr__(
            self,
            "trend_aware_score",
            None if self.trend_aware_score is None else float(self.trend_aware_score),
        )
        object.__setattr__(self, "feature_values", deepcopy(self.feature_values))
        object.__setattr__(self, "runtime_influence", False)
        object.__setattr__(self, "runtime_active", False)


@dataclass(frozen=True)
class ShadowMLOutput:
    """Serializable shadow ML output that never replaces runtime scoring."""

    output_id: str
    input_id: str
    model_id: str
    model_family: str
    deterministic_score: float
    trend_aware_score: float | None
    shadow_ml_score: float
    ml_delta_from_deterministic: float
    ml_delta_from_trend_aware: float | None
    confidence: float
    advisory_status: str
    disagreement_summary: str
    boundary_summary: str
    runtime_influence: bool
    runtime_active: bool
    runtime_influence_granted: bool
    deterministic_runtime_remains_authoritative: bool

    def __post_init__(self) -> None:
        _require_non_empty_string(self.output_id, "output_id")
        _require_non_empty_string(self.input_id, "input_id")
        _require_non_empty_string(self.model_id, "model_id")
        model_family = _normalize_model_family(self.model_family)
        _validate_score(self.deterministic_score, "deterministic_score")
        if self.trend_aware_score is not None:
            _validate_score(self.trend_aware_score, "trend_aware_score")
        _validate_score(self.shadow_ml_score, "shadow_ml_score")
        _validate_numeric(
            self.ml_delta_from_deterministic,
            "ml_delta_from_deterministic",
        )
        if self.ml_delta_from_trend_aware is not None:
            _validate_numeric(
                self.ml_delta_from_trend_aware,
                "ml_delta_from_trend_aware",
            )
        expected = compare_shadow_scores(
            self.deterministic_score,
            self.trend_aware_score,
            self.shadow_ml_score,
        )
        if (
            _round_score(self.ml_delta_from_deterministic)
            != expected["ml_delta_from_deterministic"]
        ):
            raise ShadowMLInterfaceError(
                "ml_delta_from_deterministic must equal shadow_ml_score minus "
                "deterministic_score."
            )
        if self.trend_aware_score is None:
            if self.ml_delta_from_trend_aware is not None:
                raise ShadowMLInterfaceError(
                    "ml_delta_from_trend_aware must be None when "
                    "trend_aware_score is None."
                )
        elif (
            _round_score(self.ml_delta_from_trend_aware)
            != expected["ml_delta_from_trend_aware"]
        ):
            raise ShadowMLInterfaceError(
                "ml_delta_from_trend_aware must equal shadow_ml_score minus "
                "trend_aware_score."
            )
        _validate_confidence(self.confidence)
        _validate_advisory_status(self.advisory_status)
        _require_non_empty_string(self.disagreement_summary, "disagreement_summary")
        _require_non_empty_string(self.boundary_summary, "boundary_summary")
        if self.runtime_influence is not False:
            raise ShadowMLInterfaceError(
                "Phase 7V shadow ML outputs must keep runtime_influence=false."
            )
        if self.runtime_active is not False:
            raise ShadowMLInterfaceError(
                "Phase 7V shadow ML outputs must keep runtime_active=false."
            )
        if self.runtime_influence_granted is not False:
            raise ShadowMLInterfaceError(
                "Phase 7V shadow ML outputs must keep "
                "runtime_influence_granted=false."
            )
        if self.deterministic_runtime_remains_authoritative is not True:
            raise ShadowMLInterfaceError(
                "Phase 7V requires deterministic runtime to remain authoritative."
            )
        object.__setattr__(self, "model_family", model_family)
        object.__setattr__(
            self,
            "deterministic_score",
            float(self.deterministic_score),
        )
        object.__setattr__(
            self,
            "trend_aware_score",
            None if self.trend_aware_score is None else float(self.trend_aware_score),
        )
        object.__setattr__(self, "shadow_ml_score", float(self.shadow_ml_score))
        object.__setattr__(
            self,
            "ml_delta_from_deterministic",
            float(self.ml_delta_from_deterministic),
        )
        object.__setattr__(
            self,
            "ml_delta_from_trend_aware",
            None
            if self.ml_delta_from_trend_aware is None
            else float(self.ml_delta_from_trend_aware),
        )
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(self, "runtime_influence", False)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)
        object.__setattr__(
            self,
            "deterministic_runtime_remains_authoritative",
            True,
        )


def create_shadow_model_id(
    model_family: str,
    model_version: str,
    feature_schema_version: str | None = None,
    label_schema_version: str | None = None,
) -> str:
    """Create a deterministic shadow model metadata identifier."""

    normalized_family = _normalize_model_family(model_family)
    _require_non_empty_string(model_version, "model_version")
    _validate_optional_string(feature_schema_version, "feature_schema_version")
    _validate_optional_string(label_schema_version, "label_schema_version")
    feature_schema = (
        feature_schema_version if _has_text(feature_schema_version) else "no-feature-schema"
    )
    label_schema = (
        label_schema_version if _has_text(label_schema_version) else "no-label-schema"
    )
    return (
        f"SHADOW-MODEL-{_identifier_fragment(normalized_family)}-"
        f"{_identifier_fragment(model_version)}-"
        f"{_identifier_fragment(feature_schema)}-"
        f"{_identifier_fragment(label_schema)}"
    )


def create_shadow_ml_input_id(
    run_id: str | None,
    awr_id: str | None,
    model_id: str,
    score_version: str,
) -> str:
    """Create a deterministic shadow ML input identifier."""

    _validate_optional_string(run_id, "run_id")
    _validate_optional_string(awr_id, "awr_id")
    _require_any_identifier(run_id, awr_id)
    _require_non_empty_string(model_id, "model_id")
    _require_non_empty_string(score_version, "score_version")
    source_id = run_id if _has_text(run_id) else awr_id
    return (
        f"SHADOW-INPUT-{_identifier_fragment(source_id)}-"
        f"{_identifier_fragment(model_id)}-"
        f"{_identifier_fragment(score_version)}"
    )


def create_shadow_ml_output_id(input_id: str, model_id: str) -> str:
    """Create a deterministic shadow ML output identifier."""

    _require_non_empty_string(input_id, "input_id")
    _require_non_empty_string(model_id, "model_id")
    return (
        f"SHADOW-OUTPUT-{_identifier_fragment(input_id)}-"
        f"{_identifier_fragment(model_id)}"
    )


def validate_shadow_model_metadata(
    metadata: ShadowModelMetadata | Mapping[str, Any],
) -> ShadowModelMetadata:
    """Validate and return shadow model metadata."""

    if isinstance(metadata, Mapping):
        return shadow_model_metadata_from_dict(metadata)
    if not isinstance(metadata, ShadowModelMetadata):
        raise ShadowMLInterfaceError("metadata must be ShadowModelMetadata.")
    return ShadowModelMetadata(**shadow_model_metadata_to_dict(metadata))


def validate_shadow_ml_input(
    input_record: ShadowMLInput | Mapping[str, Any],
) -> ShadowMLInput:
    """Validate and return a shadow ML input record."""

    if isinstance(input_record, Mapping):
        return shadow_ml_input_from_dict(input_record)
    if not isinstance(input_record, ShadowMLInput):
        raise ShadowMLInterfaceError("input_record must be ShadowMLInput.")
    return ShadowMLInput(**shadow_ml_input_to_dict(input_record))


def validate_shadow_ml_output(
    output: ShadowMLOutput | Mapping[str, Any],
) -> ShadowMLOutput:
    """Validate and return a shadow ML output record."""

    if isinstance(output, Mapping):
        return shadow_ml_output_from_dict(output)
    if not isinstance(output, ShadowMLOutput):
        raise ShadowMLInterfaceError("output must be ShadowMLOutput.")
    return ShadowMLOutput(**shadow_ml_output_to_dict(output))


def compute_placeholder_shadow_score(
    input_record: ShadowMLInput | Mapping[str, Any],
    model_metadata: ShadowModelMetadata | Mapping[str, Any],
) -> ShadowMLOutput:
    """Compute a deterministic placeholder shadow score without runtime mutation."""

    validated_input = validate_shadow_ml_input(input_record)
    metadata = validate_shadow_model_metadata(model_metadata)
    if validated_input.model_id != metadata.model_id:
        raise ShadowMLInterfaceError(
            "Shadow ML input model_id must match shadow model metadata model_id."
        )

    risk_adjustment, risk_signal_count = _risk_feature_adjustment(
        validated_input.feature_values,
        validated_input.deterministic_score,
    )
    trend_adjustment = _trend_blend_adjustment(
        validated_input.deterministic_score,
        validated_input.trend_aware_score,
    )
    shadow_ml_score = _round_score(
        _clamp(
            validated_input.deterministic_score + trend_adjustment + risk_adjustment,
            0.0,
            100.0,
        )
    )
    comparison = compare_shadow_scores(
        validated_input.deterministic_score,
        validated_input.trend_aware_score,
        shadow_ml_score,
    )
    advisory_status = _placeholder_advisory_status(
        validated_input,
        risk_signal_count,
    )
    confidence = _placeholder_confidence(
        validated_input,
        metadata,
        risk_signal_count,
        advisory_status,
    )
    output = ShadowMLOutput(
        output_id=create_shadow_ml_output_id(
            validated_input.input_id,
            metadata.model_id,
        ),
        input_id=validated_input.input_id,
        model_id=metadata.model_id,
        model_family=metadata.model_family,
        deterministic_score=validated_input.deterministic_score,
        trend_aware_score=validated_input.trend_aware_score,
        shadow_ml_score=shadow_ml_score,
        ml_delta_from_deterministic=comparison["ml_delta_from_deterministic"],
        ml_delta_from_trend_aware=comparison["ml_delta_from_trend_aware"],
        confidence=confidence,
        advisory_status=advisory_status,
        disagreement_summary=comparison["disagreement_summary"],
        boundary_summary=(
            "Phase 7V shadow ML output is non-authoritative; deterministic "
            "runtime remains authoritative; runtime_influence=false; "
            "runtime_active=false; runtime_influence_granted=false."
        ),
        runtime_influence=False,
        runtime_active=False,
        runtime_influence_granted=False,
        deterministic_runtime_remains_authoritative=True,
    )
    return validate_shadow_ml_output(output)


def compare_shadow_scores(
    deterministic_score: float,
    trend_aware_score: float | None,
    shadow_ml_score: float,
) -> dict[str, object]:
    """Compare deterministic, trend-aware, and shadow ML-style scores."""

    _validate_score(deterministic_score, "deterministic_score")
    if trend_aware_score is not None:
        _validate_score(trend_aware_score, "trend_aware_score")
    _validate_score(shadow_ml_score, "shadow_ml_score")
    deterministic_delta = _round_score(float(shadow_ml_score) - float(deterministic_score))
    trend_delta = (
        None
        if trend_aware_score is None
        else _round_score(float(shadow_ml_score) - float(trend_aware_score))
    )
    if trend_delta is None:
        summary = (
            "Shadow ML placeholder differs from deterministic score by "
            f"{_format_number(deterministic_delta)}; trend-aware score was not "
            "supplied. Deterministic runtime remains authoritative."
        )
    else:
        summary = (
            "Shadow ML placeholder differs from deterministic score by "
            f"{_format_number(deterministic_delta)} and trend-aware score by "
            f"{_format_number(trend_delta)}. Deterministic runtime remains "
            "authoritative."
        )
    return {
        "deterministic_score": float(deterministic_score),
        "trend_aware_score": None if trend_aware_score is None else float(trend_aware_score),
        "shadow_ml_score": float(shadow_ml_score),
        "ml_delta_from_deterministic": deterministic_delta,
        "ml_delta_from_trend_aware": trend_delta,
        "deterministic_disagreement_level": _disagreement_level(deterministic_delta),
        "trend_aware_disagreement_level": (
            None if trend_delta is None else _disagreement_level(trend_delta)
        ),
        "disagreement_summary": summary,
    }


def shadow_model_metadata_to_dict(
    metadata: ShadowModelMetadata,
) -> dict[str, object]:
    """Return a deterministic dictionary for shadow model metadata."""

    if not isinstance(metadata, ShadowModelMetadata):
        raise ShadowMLInterfaceError("metadata must be ShadowModelMetadata.")
    return {
        field_name: deepcopy(getattr(metadata, field_name))
        for field_name in SHADOW_MODEL_METADATA_FIELDS
    }


def shadow_model_metadata_from_dict(
    data: Mapping[str, Any],
) -> ShadowModelMetadata:
    """Reconstruct and validate shadow model metadata from dictionary data."""

    if not isinstance(data, Mapping):
        raise ShadowMLInterfaceError("shadow model metadata data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        SHADOW_MODEL_METADATA_FIELDS,
        optional_defaults={
            "feature_schema_version": None,
            "label_schema_version": None,
            "training_reference": None,
            "validation_reference": None,
            "runtime_active": False,
            "runtime_influence_granted": False,
            "notes": None,
        },
    )
    return ShadowModelMetadata(**values)


def shadow_ml_input_to_dict(input_record: ShadowMLInput) -> dict[str, object]:
    """Return a deterministic dictionary for a shadow ML input record."""

    if not isinstance(input_record, ShadowMLInput):
        raise ShadowMLInterfaceError("input_record must be ShadowMLInput.")
    return {
        field_name: deepcopy(getattr(input_record, field_name))
        for field_name in SHADOW_ML_INPUT_FIELDS
    }


def shadow_ml_input_from_dict(data: Mapping[str, Any]) -> ShadowMLInput:
    """Reconstruct and validate a shadow ML input record from dictionary data."""

    if not isinstance(data, Mapping):
        raise ShadowMLInterfaceError("shadow ML input data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        SHADOW_ML_INPUT_FIELDS,
        optional_defaults={
            "run_id": None,
            "awr_id": None,
            "feature_reference": None,
            "dataset_reference": None,
            "trend_aware_score": None,
            "runtime_influence": False,
            "runtime_active": False,
        },
    )
    return ShadowMLInput(**values)


def shadow_ml_output_to_dict(output: ShadowMLOutput) -> dict[str, object]:
    """Return a deterministic dictionary for a shadow ML output record."""

    if not isinstance(output, ShadowMLOutput):
        raise ShadowMLInterfaceError("output must be ShadowMLOutput.")
    return {
        field_name: deepcopy(getattr(output, field_name))
        for field_name in SHADOW_ML_OUTPUT_FIELDS
    }


def shadow_ml_output_from_dict(data: Mapping[str, Any]) -> ShadowMLOutput:
    """Reconstruct and validate a shadow ML output record from dictionary data."""

    if not isinstance(data, Mapping):
        raise ShadowMLInterfaceError("shadow ML output data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        SHADOW_ML_OUTPUT_FIELDS,
        optional_defaults={
            "runtime_influence": False,
            "runtime_active": False,
            "runtime_influence_granted": False,
            "deterministic_runtime_remains_authoritative": True,
        },
    )
    return ShadowMLOutput(**values)


def _normalize_model_family(value: Any) -> str:
    _require_non_empty_string(value, "model_family")
    normalized = str(value).strip().lower()
    if normalized not in SHADOW_MODEL_FAMILIES:
        raise ShadowMLInterfaceError(f"Unsupported model_family: {value!r}.")
    return normalized


def _validate_advisory_status(status: Any) -> None:
    if status not in SHADOW_ML_ADVISORY_STATUSES:
        raise ShadowMLInterfaceError(f"Unsupported advisory_status: {status!r}.")


def _validate_feature_values(feature_values: Any) -> None:
    if not isinstance(feature_values, dict):
        raise ShadowMLInterfaceError("feature_values must be a dict.")
    for key in feature_values:
        _require_non_empty_string(key, "feature_values key")


def _validate_score(value: Any, field_name: str) -> None:
    _validate_numeric(value, field_name)
    if value < 0.0 or value > 100.0:
        raise ShadowMLInterfaceError(f"{field_name} must be between 0.0 and 100.0.")


def _validate_confidence(value: Any) -> None:
    _validate_numeric(value, "confidence")
    if value < 0.0 or value > MAX_PLACEHOLDER_CONFIDENCE:
        raise ShadowMLInterfaceError(
            f"confidence must be between 0.0 and {MAX_PLACEHOLDER_CONFIDENCE}."
        )


def _validate_numeric(value: Any, field_name: str) -> None:
    if not _is_number(value):
        raise ShadowMLInterfaceError(f"{field_name} must be numeric.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ShadowMLInterfaceError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise ShadowMLInterfaceError(f"{field_name} must not be blank.")


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ShadowMLInterfaceError(f"{field_name} must be a non-empty string.")


def _require_any_identifier(run_id: str | None, awr_id: str | None) -> None:
    if not _has_text(run_id) and not _has_text(awr_id):
        raise ShadowMLInterfaceError(
            "At least one of run_id or awr_id is required."
        )


def _values_from_mapping(
    data: Mapping[str, Any],
    fields: Sequence[str],
    optional_defaults: Mapping[str, Any],
) -> dict[str, Any]:
    missing = [
        field_name
        for field_name in fields
        if field_name not in data and field_name not in optional_defaults
    ]
    if missing:
        raise ShadowMLInterfaceError(
            "Missing required fields: " + ", ".join(missing) + "."
        )
    return {
        field_name: deepcopy(data[field_name])
        if field_name in data
        else deepcopy(optional_defaults[field_name])
        for field_name in fields
    }


def _reject_runtime_activation_fields(data: Mapping[str, Any]) -> None:
    for field_name in (
        "runtime_influence",
        "runtime_active",
        "runtime_influence_granted",
    ):
        if data.get(field_name) is True:
            raise ShadowMLInterfaceError(
                f"{field_name} cannot be true on Phase 7V shadow ML records."
            )


def _trend_blend_adjustment(
    deterministic_score: float,
    trend_aware_score: float | None,
) -> float:
    if trend_aware_score is None:
        return 0.0
    adjustment = (float(trend_aware_score) - float(deterministic_score)) * 0.25
    return _round_score(
        _clamp(
            adjustment,
            -MAX_TREND_BLEND_ADJUSTMENT,
            MAX_TREND_BLEND_ADJUSTMENT,
        )
    )


def _risk_feature_adjustment(
    feature_values: Mapping[str, object],
    deterministic_score: float,
) -> tuple[float, int]:
    risk_scores = [
        _normalize_feature_score(value)
        for key, value in sorted(feature_values.items(), key=lambda item: str(item[0]))
        if _is_risk_feature_name(str(key)) and _is_number(value)
    ]
    if not risk_scores:
        return 0.0, 0
    average_risk_score = sum(risk_scores) / len(risk_scores)
    adjustment = (average_risk_score - float(deterministic_score)) * 0.08
    return (
        _round_score(
            _clamp(
                adjustment,
                -MAX_RISK_FEATURE_ADJUSTMENT,
                MAX_RISK_FEATURE_ADJUSTMENT,
            )
        ),
        len(risk_scores),
    )


def _normalize_feature_score(value: object) -> float:
    numeric_value = float(value)
    if 0.0 <= numeric_value <= 1.0:
        numeric_value *= 100.0
    return _clamp(numeric_value, 0.0, 100.0)


def _is_risk_feature_name(name: str) -> bool:
    normalized = name.strip().lower()
    return any(
        token in normalized
        for token in (
            "risk",
            "pressure",
            "severity",
            "wait",
            "latency",
            "bottleneck",
            "anomaly",
            "degradation",
        )
    )


def _placeholder_advisory_status(
    input_record: ShadowMLInput,
    risk_signal_count: int,
) -> str:
    if (
        input_record.trend_aware_score is None
        and risk_signal_count == 0
        and not input_record.feature_values
        and not _has_text(input_record.feature_reference)
        and not _has_text(input_record.dataset_reference)
    ):
        return "INSUFFICIENT_MODEL_CONTEXT"
    return "SHADOW_ONLY"


def _placeholder_confidence(
    input_record: ShadowMLInput,
    metadata: ShadowModelMetadata,
    risk_signal_count: int,
    advisory_status: str,
) -> float:
    confidence = 0.4
    if input_record.trend_aware_score is not None:
        confidence += 0.1
    if input_record.feature_values:
        confidence += 0.05
    if risk_signal_count:
        confidence += min(0.15, risk_signal_count * 0.05)
    if _has_text(input_record.feature_reference):
        confidence += 0.05
    if _has_text(input_record.dataset_reference):
        confidence += 0.05
    for value in (
        metadata.feature_schema_version,
        metadata.label_schema_version,
        metadata.training_reference,
        metadata.validation_reference,
    ):
        if _has_text(value):
            confidence += 0.05
    if advisory_status == "INSUFFICIENT_MODEL_CONTEXT":
        confidence = min(confidence * 0.7, 0.35)
    return _round_score(_clamp(confidence, 0.0, MAX_PLACEHOLDER_CONFIDENCE))


def _disagreement_level(delta: float) -> str:
    absolute_delta = abs(float(delta))
    if absolute_delta >= 15.0:
        return "material"
    if absolute_delta >= 5.0:
        return "moderate"
    if absolute_delta > 0.0:
        return "minor"
    return "none"


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _round_score(value: float) -> float:
    return round(float(value), 6)


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"


def _format_number(value: float) -> str:
    rounded = _round_score(value)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.6f}".rstrip("0").rstrip(".")
