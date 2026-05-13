"""Governed Phase 7T feature / label dataset model.

This module defines local deterministic records for future ML/adaptive
scoring datasets. A dataset is governed input, not a model. Validation does
not train, score, activate, or influence runtime behavior.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


SUPPORTED_FEATURE_TYPES = (
    "numeric",
    "categorical",
    "boolean",
    "text",
    "derived_numeric",
    "derived_categorical",
    "missing",
)

SUPPORTED_LABEL_TYPES = (
    "binary",
    "categorical",
    "ordinal",
    "numeric",
    "outcome_status",
    "review_status",
    "unknown",
)

SUPPORTED_LABEL_NAMES = (
    "tuning_success",
    "performance_improved",
    "performance_worsened",
    "recommendation_accepted",
    "recommendation_rejected",
    "issue_recurred",
    "risk_confirmed",
    "false_positive",
    "false_negative",
    "action_effective",
    "action_ineffective",
    "no_change",
    "unknown_outcome",
)

EXCLUDED_LABEL_NAMES = (
    "unknown_outcome",
)

SUPERVISED_LABEL_NAMES = tuple(
    label_name
    for label_name in SUPPORTED_LABEL_NAMES
    if label_name not in EXCLUDED_LABEL_NAMES
)

VALIDATED = "VALIDATED"
INVALID = "INVALID"
PROPOSED = "PROPOSED"

VALIDATION_STATUSES = (
    VALIDATED,
    INVALID,
    PROPOSED,
)

FEATURE_RECORD_FIELDS = (
    "feature_id",
    "run_id",
    "awr_id",
    "feature_name",
    "feature_domain",
    "feature_value",
    "feature_type",
    "source_component",
    "source_metric",
    "feature_schema_version",
    "evidence_reference",
    "created_at",
    "notes",
)

LABEL_RECORD_FIELDS = (
    "label_id",
    "run_id",
    "awr_id",
    "label_name",
    "label_value",
    "label_type",
    "outcome_source",
    "source_record_id",
    "label_schema_version",
    "confidence",
    "evidence_reference",
    "reviewed_by",
    "created_at",
    "notes",
)

FEATURE_SCHEMA_FIELDS = (
    "schema_id",
    "schema_version",
    "feature_names",
    "feature_domains",
    "required_features",
    "optional_features",
    "created_by",
    "notes",
)

LABEL_SCHEMA_FIELDS = (
    "schema_id",
    "schema_version",
    "label_names",
    "label_values",
    "supervised_labels",
    "excluded_labels",
    "created_by",
    "notes",
)

FEATURE_LABEL_DATASET_FIELDS = (
    "dataset_id",
    "dataset_name",
    "feature_schema_version",
    "label_schema_version",
    "features",
    "labels",
    "source_records",
    "dataset_purpose",
    "created_by",
    "created_at",
    "validation_status",
    "validation_notes",
    "train_split_reference",
    "test_split_reference",
    "runtime_influence",
    "runtime_active",
)


class FeatureLabelDatasetError(ValueError):
    """Raised when Phase 7T feature / label dataset rules are violated."""


@dataclass(frozen=True)
class FeatureRecord:
    """Serializable governed feature-vector record for X."""

    feature_id: str
    run_id: str | None
    awr_id: str | None
    feature_name: str
    feature_domain: str | None
    feature_value: object
    feature_type: str
    source_component: str | None
    source_metric: str | None
    feature_schema_version: str
    evidence_reference: str | None
    created_at: str | None
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.feature_id, "feature_id")
        _validate_optional_string(self.run_id, "run_id")
        _validate_optional_string(self.awr_id, "awr_id")
        _require_any_identifier(self.run_id, self.awr_id)
        _require_non_empty_string(self.feature_name, "feature_name")
        _validate_optional_string(self.feature_domain, "feature_domain")
        _validate_feature_type(self.feature_type)
        _validate_feature_value(self.feature_value, self.feature_type)
        _validate_optional_string(self.source_component, "source_component")
        _validate_optional_string(self.source_metric, "source_metric")
        _require_non_empty_string(
            self.feature_schema_version,
            "feature_schema_version",
        )
        _validate_optional_string(self.evidence_reference, "evidence_reference")
        _validate_optional_string(self.created_at, "created_at")
        _validate_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class LabelRecord:
    """Serializable governed observed-outcome record for y."""

    label_id: str
    run_id: str | None
    awr_id: str | None
    label_name: str
    label_value: object
    label_type: str
    outcome_source: str | None
    source_record_id: str | None
    label_schema_version: str
    confidence: float
    evidence_reference: str | None
    reviewed_by: str | None
    created_at: str | None
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.label_id, "label_id")
        _validate_optional_string(self.run_id, "run_id")
        _validate_optional_string(self.awr_id, "awr_id")
        _require_any_identifier(self.run_id, self.awr_id)
        _validate_label_name(self.label_name)
        _validate_label_type(self.label_type)
        _validate_label_value(self.label_value, self.label_type)
        _validate_optional_string(self.outcome_source, "outcome_source")
        _validate_optional_string(self.source_record_id, "source_record_id")
        _require_non_empty_string(self.label_schema_version, "label_schema_version")
        _validate_confidence(self.confidence)
        _validate_optional_string(self.evidence_reference, "evidence_reference")
        _validate_optional_string(self.reviewed_by, "reviewed_by")
        _validate_optional_string(self.created_at, "created_at")
        _validate_optional_string(self.notes, "notes")
        _validate_label_auditability(
            label_name=self.label_name,
            outcome_source=self.outcome_source,
            source_record_id=self.source_record_id,
            evidence_reference=self.evidence_reference,
        )


@dataclass(frozen=True)
class FeatureSchema:
    """Versioned metadata for feature vectors."""

    schema_id: str
    schema_version: str
    feature_names: list[str]
    feature_domains: list[str]
    required_features: list[str]
    optional_features: list[str]
    created_by: str | None
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.schema_id, "schema_id")
        _require_non_empty_string(self.schema_version, "schema_version")
        feature_names = _normalize_string_list(
            self.feature_names,
            "feature_names",
            allow_empty=False,
        )
        feature_domains = _normalize_string_list(
            self.feature_domains,
            "feature_domains",
            allow_empty=True,
        )
        required_features = _normalize_string_list(
            self.required_features,
            "required_features",
            allow_empty=True,
        )
        optional_features = _normalize_string_list(
            self.optional_features,
            "optional_features",
            allow_empty=True,
        )
        _validate_feature_schema_membership(feature_names, required_features)
        _validate_feature_schema_membership(feature_names, optional_features)
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.notes, "notes")
        object.__setattr__(self, "feature_names", feature_names)
        object.__setattr__(self, "feature_domains", feature_domains)
        object.__setattr__(self, "required_features", required_features)
        object.__setattr__(self, "optional_features", optional_features)


@dataclass(frozen=True)
class LabelSchema:
    """Versioned metadata for observed outcome labels."""

    schema_id: str
    schema_version: str
    label_names: list[str]
    label_values: list[str]
    supervised_labels: list[str]
    excluded_labels: list[str]
    created_by: str | None
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.schema_id, "schema_id")
        _require_non_empty_string(self.schema_version, "schema_version")
        label_names = _normalize_string_list(
            self.label_names,
            "label_names",
            allow_empty=False,
        )
        label_values = _normalize_string_list(
            self.label_values,
            "label_values",
            allow_empty=True,
        )
        supervised_labels = _normalize_string_list(
            self.supervised_labels,
            "supervised_labels",
            allow_empty=True,
        )
        excluded_labels = _normalize_string_list(
            self.excluded_labels,
            "excluded_labels",
            allow_empty=True,
        )
        for label_name in label_names + supervised_labels + excluded_labels:
            _validate_label_name(label_name)
        _validate_label_schema_membership(label_names, supervised_labels)
        _validate_label_schema_membership(label_names, excluded_labels)
        if "unknown_outcome" in supervised_labels:
            raise FeatureLabelDatasetError(
                "unknown_outcome must be excluded from supervised labels."
            )
        if "unknown_outcome" not in excluded_labels:
            raise FeatureLabelDatasetError(
                "unknown_outcome must be listed in excluded_labels."
            )
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.notes, "notes")
        object.__setattr__(self, "label_names", label_names)
        object.__setattr__(self, "label_values", label_values)
        object.__setattr__(self, "supervised_labels", supervised_labels)
        object.__setattr__(self, "excluded_labels", excluded_labels)


@dataclass(frozen=True)
class FeatureLabelDataset:
    """Governed local collection of X feature vectors and y observed outcomes."""

    dataset_id: str
    dataset_name: str
    feature_schema_version: str
    label_schema_version: str
    features: list[FeatureRecord]
    labels: list[LabelRecord]
    source_records: list[dict[str, object]]
    dataset_purpose: str
    created_by: str | None
    created_at: str | None
    validation_status: str
    validation_notes: list[str]
    train_split_reference: str | None
    test_split_reference: str | None
    runtime_influence: bool
    runtime_active: bool

    def __post_init__(self) -> None:
        _require_non_empty_string(self.dataset_id, "dataset_id")
        _require_non_empty_string(self.dataset_name, "dataset_name")
        _require_non_empty_string(
            self.feature_schema_version,
            "feature_schema_version",
        )
        _require_non_empty_string(self.label_schema_version, "label_schema_version")
        _require_non_empty_string(self.dataset_purpose, "dataset_purpose")
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.created_at, "created_at")
        _validate_validation_status(self.validation_status)
        _validate_optional_string(
            self.train_split_reference,
            "train_split_reference",
        )
        _validate_optional_string(self.test_split_reference, "test_split_reference")
        if self.runtime_influence is not False:
            raise FeatureLabelDatasetError(
                "Phase 7T datasets must keep runtime_influence=false."
            )
        if self.runtime_active is not False:
            raise FeatureLabelDatasetError(
                "Phase 7T datasets must keep runtime_active=false."
            )

        features = _normalize_features(self.features)
        labels = _normalize_labels(self.labels)
        if not features:
            raise FeatureLabelDatasetError("features list must not be empty.")
        if not labels:
            raise FeatureLabelDatasetError("labels list must not be empty.")
        _validate_dataset_schema_versions(
            self.feature_schema_version,
            self.label_schema_version,
            features,
            labels,
        )
        source_records = _normalize_source_records(self.source_records)
        validation_notes = _normalize_string_list(
            self.validation_notes,
            "validation_notes",
            allow_empty=True,
        )

        object.__setattr__(self, "features", features)
        object.__setattr__(self, "labels", labels)
        object.__setattr__(self, "source_records", source_records)
        object.__setattr__(self, "validation_notes", validation_notes)
        object.__setattr__(self, "runtime_influence", False)
        object.__setattr__(self, "runtime_active", False)


def create_feature_id(
    run_id: str | None,
    awr_id: str | None,
    feature_name: str,
    feature_schema_version: str,
) -> str:
    """Create a deterministic feature identifier from stable inputs."""

    _require_any_identifier(run_id, awr_id)
    _require_non_empty_string(feature_name, "feature_name")
    _require_non_empty_string(feature_schema_version, "feature_schema_version")
    run_or_awr = run_id if _has_text(run_id) else awr_id
    return (
        f"FEATURE-{_identifier_fragment(feature_schema_version)}-"
        f"{_identifier_fragment(run_or_awr)}-{_identifier_fragment(feature_name)}"
    )


def create_label_id(
    run_id: str | None,
    awr_id: str | None,
    label_name: str,
    label_schema_version: str,
) -> str:
    """Create a deterministic label identifier from stable inputs."""

    _require_any_identifier(run_id, awr_id)
    _validate_label_name(label_name)
    _require_non_empty_string(label_schema_version, "label_schema_version")
    run_or_awr = run_id if _has_text(run_id) else awr_id
    return (
        f"LABEL-{_identifier_fragment(label_schema_version)}-"
        f"{_identifier_fragment(run_or_awr)}-{_identifier_fragment(label_name)}"
    )


def create_feature_schema_id(schema_version: str, feature_names: Sequence[str]) -> str:
    """Create a deterministic feature schema identifier."""

    _require_non_empty_string(schema_version, "schema_version")
    names = _normalize_string_list(feature_names, "feature_names", allow_empty=False)
    return (
        f"FEATURE-SCHEMA-{_identifier_fragment(schema_version)}-"
        f"{_stable_hash(names)}"
    )


def create_label_schema_id(schema_version: str, label_names: Sequence[str]) -> str:
    """Create a deterministic label schema identifier."""

    _require_non_empty_string(schema_version, "schema_version")
    names = _normalize_string_list(label_names, "label_names", allow_empty=False)
    for label_name in names:
        _validate_label_name(label_name)
    return (
        f"LABEL-SCHEMA-{_identifier_fragment(schema_version)}-"
        f"{_stable_hash(names)}"
    )


def create_dataset_id(
    dataset_name: str,
    feature_schema_version: str,
    label_schema_version: str,
) -> str:
    """Create a deterministic dataset identifier from stable inputs."""

    _require_non_empty_string(dataset_name, "dataset_name")
    _require_non_empty_string(feature_schema_version, "feature_schema_version")
    _require_non_empty_string(label_schema_version, "label_schema_version")
    return (
        f"DATASET-{_identifier_fragment(dataset_name)}-"
        f"{_identifier_fragment(feature_schema_version)}-"
        f"{_identifier_fragment(label_schema_version)}"
    )


def validate_feature_record(
    feature: FeatureRecord | Mapping[str, Any],
) -> FeatureRecord:
    """Validate and return a governed feature record."""

    if isinstance(feature, Mapping):
        return feature_record_from_dict(feature)
    if not isinstance(feature, FeatureRecord):
        raise FeatureLabelDatasetError("feature must be a FeatureRecord.")
    return FeatureRecord(**feature_record_to_dict(feature))


def validate_label_record(label: LabelRecord | Mapping[str, Any]) -> LabelRecord:
    """Validate and return a governed label record."""

    if isinstance(label, Mapping):
        return label_record_from_dict(label)
    if not isinstance(label, LabelRecord):
        raise FeatureLabelDatasetError("label must be a LabelRecord.")
    return LabelRecord(**label_record_to_dict(label))


def validate_feature_schema(schema: FeatureSchema | Mapping[str, Any]) -> FeatureSchema:
    """Validate and return versioned feature schema metadata."""

    if isinstance(schema, Mapping):
        schema = _feature_schema_from_dict(schema)
    if not isinstance(schema, FeatureSchema):
        raise FeatureLabelDatasetError("schema must be a FeatureSchema.")
    validated = FeatureSchema(
        **{field_name: deepcopy(getattr(schema, field_name)) for field_name in FEATURE_SCHEMA_FIELDS}
    )
    expected_schema_id = create_feature_schema_id(
        validated.schema_version,
        validated.feature_names,
    )
    if validated.schema_id != expected_schema_id:
        raise FeatureLabelDatasetError(
            "feature schema_id must match deterministic feature schema ID."
        )
    return validated


def validate_label_schema(schema: LabelSchema | Mapping[str, Any]) -> LabelSchema:
    """Validate and return versioned label schema metadata."""

    if isinstance(schema, Mapping):
        schema = _label_schema_from_dict(schema)
    if not isinstance(schema, LabelSchema):
        raise FeatureLabelDatasetError("schema must be a LabelSchema.")
    validated = LabelSchema(
        **{field_name: deepcopy(getattr(schema, field_name)) for field_name in LABEL_SCHEMA_FIELDS}
    )
    expected_schema_id = create_label_schema_id(
        validated.schema_version,
        validated.label_names,
    )
    if validated.schema_id != expected_schema_id:
        raise FeatureLabelDatasetError(
            "label schema_id must match deterministic label schema ID."
        )
    return validated


def validate_feature_label_dataset(
    dataset: FeatureLabelDataset | Mapping[str, Any],
) -> FeatureLabelDataset:
    """Validate a dataset without training, scoring, or runtime activation."""

    if isinstance(dataset, Mapping):
        dataset = feature_label_dataset_from_dict(dataset)
    if not isinstance(dataset, FeatureLabelDataset):
        raise FeatureLabelDatasetError("dataset must be a FeatureLabelDataset.")

    validated = FeatureLabelDataset(**feature_label_dataset_to_dict(dataset))
    notes = list(validated.validation_notes)
    unmatched_feature_ids, unmatched_label_ids = _find_unmatched_records(
        validated.features,
        validated.labels,
    )
    if unmatched_feature_ids:
        notes.append(
            "Unmatched feature records: " + ", ".join(sorted(unmatched_feature_ids))
        )
    if unmatched_label_ids:
        notes.append(
            "Unmatched label records: " + ", ".join(sorted(unmatched_label_ids))
        )

    unknown_outcome_count = sum(
        1 for label in validated.labels if label.label_name == "unknown_outcome"
    )
    if unknown_outcome_count:
        notes.append(
            "unknown_outcome labels excluded from supervised truth: "
            f"{unknown_outcome_count}"
        )

    status = INVALID if unmatched_feature_ids or unmatched_label_ids else VALIDATED
    values = feature_label_dataset_to_dict(validated)
    values["validation_status"] = status
    values["validation_notes"] = _deduplicate_preserving_order(notes)
    return FeatureLabelDataset(**values)


def feature_record_to_dict(feature: FeatureRecord) -> dict[str, object]:
    """Return a deterministic dictionary for one feature record."""

    if not isinstance(feature, FeatureRecord):
        raise FeatureLabelDatasetError("feature must be a FeatureRecord.")
    return {field_name: deepcopy(getattr(feature, field_name)) for field_name in FEATURE_RECORD_FIELDS}


def feature_record_from_dict(data: Mapping[str, Any]) -> FeatureRecord:
    """Reconstruct and validate one feature record from dictionary data."""

    if not isinstance(data, Mapping):
        raise FeatureLabelDatasetError("feature data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        FEATURE_RECORD_FIELDS,
        optional_defaults={
            "run_id": None,
            "awr_id": None,
            "feature_domain": None,
            "source_component": None,
            "source_metric": None,
            "evidence_reference": None,
            "created_at": None,
            "notes": None,
        },
    )
    return FeatureRecord(**values)


def label_record_to_dict(label: LabelRecord) -> dict[str, object]:
    """Return a deterministic dictionary for one label record."""

    if not isinstance(label, LabelRecord):
        raise FeatureLabelDatasetError("label must be a LabelRecord.")
    return {field_name: deepcopy(getattr(label, field_name)) for field_name in LABEL_RECORD_FIELDS}


def label_record_from_dict(data: Mapping[str, Any]) -> LabelRecord:
    """Reconstruct and validate one label record from dictionary data."""

    if not isinstance(data, Mapping):
        raise FeatureLabelDatasetError("label data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        LABEL_RECORD_FIELDS,
        optional_defaults={
            "run_id": None,
            "awr_id": None,
            "outcome_source": None,
            "source_record_id": None,
            "evidence_reference": None,
            "reviewed_by": None,
            "created_at": None,
            "notes": None,
        },
    )
    return LabelRecord(**values)


def feature_label_dataset_to_dict(
    dataset: FeatureLabelDataset,
) -> dict[str, object]:
    """Return a deterministic dictionary for one feature / label dataset."""

    if not isinstance(dataset, FeatureLabelDataset):
        raise FeatureLabelDatasetError("dataset must be a FeatureLabelDataset.")
    return {
        "dataset_id": dataset.dataset_id,
        "dataset_name": dataset.dataset_name,
        "feature_schema_version": dataset.feature_schema_version,
        "label_schema_version": dataset.label_schema_version,
        "features": [feature_record_to_dict(feature) for feature in dataset.features],
        "labels": [label_record_to_dict(label) for label in dataset.labels],
        "source_records": deepcopy(dataset.source_records),
        "dataset_purpose": dataset.dataset_purpose,
        "created_by": dataset.created_by,
        "created_at": dataset.created_at,
        "validation_status": dataset.validation_status,
        "validation_notes": list(dataset.validation_notes),
        "train_split_reference": dataset.train_split_reference,
        "test_split_reference": dataset.test_split_reference,
        "runtime_influence": dataset.runtime_influence,
        "runtime_active": dataset.runtime_active,
    }


def feature_label_dataset_from_dict(data: Mapping[str, Any]) -> FeatureLabelDataset:
    """Reconstruct and validate one feature / label dataset from dictionary data."""

    if not isinstance(data, Mapping):
        raise FeatureLabelDatasetError("dataset data must be a mapping.")
    values = _values_from_mapping(
        data,
        FEATURE_LABEL_DATASET_FIELDS,
        optional_defaults={
            "source_records": [],
            "created_by": None,
            "created_at": None,
            "validation_status": PROPOSED,
            "validation_notes": [],
            "train_split_reference": None,
            "test_split_reference": None,
            "runtime_influence": False,
            "runtime_active": False,
        },
    )
    values["features"] = [
        feature_record_from_dict(feature)
        if isinstance(feature, Mapping)
        else validate_feature_record(feature)
        for feature in values["features"]
    ]
    values["labels"] = [
        label_record_from_dict(label)
        if isinstance(label, Mapping)
        else validate_label_record(label)
        for label in values["labels"]
    ]
    return FeatureLabelDataset(**values)


def join_features_labels(
    features: Sequence[FeatureRecord],
    labels: Sequence[LabelRecord],
) -> list[dict[str, object]]:
    """Join feature and label records by run_id and awr_id without mutation."""

    normalized_features = [validate_feature_record(feature) for feature in features]
    normalized_labels = [validate_label_record(label) for label in labels]
    groups: dict[str, dict[str, Any]] = {}
    token_to_group: dict[tuple[str, str], str] = {}

    for feature in normalized_features:
        _add_join_record(groups, token_to_group, feature, "features")
    for label in normalized_labels:
        _add_join_record(groups, token_to_group, label, "labels")

    joined: list[dict[str, object]] = []
    for group_key in sorted(groups):
        group = groups[group_key]
        run_ids = sorted(group["run_ids"])
        awr_ids = sorted(group["awr_ids"])
        group_features = [
            feature_record_to_dict(feature) for feature in group["features"]
        ]
        group_labels = [label_record_to_dict(label) for label in group["labels"]]
        joined.append(
            {
                "join_key": group_key,
                "run_id": run_ids[0] if run_ids else None,
                "awr_id": awr_ids[0] if awr_ids else None,
                "feature_count": len(group_features),
                "label_count": len(group_labels),
                "features": group_features,
                "labels": group_labels,
                "matched": bool(group_features and group_labels),
            }
        )
    return joined


def dataset_summary(dataset: FeatureLabelDataset) -> dict[str, object]:
    """Return a deterministic local summary of dataset contents."""

    validated = validate_feature_label_dataset(dataset)
    supervised_count = sum(
        1 for label in validated.labels if label.label_name in SUPERVISED_LABEL_NAMES
    )
    unknown_count = sum(
        1 for label in validated.labels if label.label_name == "unknown_outcome"
    )
    joined = join_features_labels(validated.features, validated.labels)
    return {
        "dataset_id": validated.dataset_id,
        "dataset_name": validated.dataset_name,
        "feature_schema_version": validated.feature_schema_version,
        "label_schema_version": validated.label_schema_version,
        "feature_count": len(validated.features),
        "label_count": len(validated.labels),
        "supervised_label_count": supervised_count,
        "unknown_outcome_count": unknown_count,
        "join_group_count": len(joined),
        "unmatched_group_count": sum(1 for group in joined if not group["matched"]),
        "validation_status": validated.validation_status,
        "validation_notes": list(validated.validation_notes),
        "runtime_influence": False,
        "runtime_active": False,
        "dataset_is_model": False,
        "training_implemented": False,
        "runtime_scoring_changed": False,
    }


def _feature_schema_from_dict(data: Mapping[str, Any]) -> FeatureSchema:
    values = _values_from_mapping(
        data,
        FEATURE_SCHEMA_FIELDS,
        optional_defaults={
            "feature_domains": [],
            "required_features": [],
            "optional_features": [],
            "created_by": None,
            "notes": None,
        },
    )
    return FeatureSchema(**values)


def _label_schema_from_dict(data: Mapping[str, Any]) -> LabelSchema:
    values = _values_from_mapping(
        data,
        LABEL_SCHEMA_FIELDS,
        optional_defaults={
            "label_values": [],
            "supervised_labels": list(SUPERVISED_LABEL_NAMES),
            "excluded_labels": list(EXCLUDED_LABEL_NAMES),
            "created_by": None,
            "notes": None,
        },
    )
    return LabelSchema(**values)


def _validate_feature_type(feature_type: Any) -> None:
    if feature_type not in SUPPORTED_FEATURE_TYPES:
        raise FeatureLabelDatasetError(f"Unsupported feature_type: {feature_type!r}.")


def _validate_label_type(label_type: Any) -> None:
    if label_type not in SUPPORTED_LABEL_TYPES:
        raise FeatureLabelDatasetError(f"Unsupported label_type: {label_type!r}.")


def _validate_label_name(label_name: Any) -> None:
    if label_name not in SUPPORTED_LABEL_NAMES:
        raise FeatureLabelDatasetError(f"Unsupported label_name: {label_name!r}.")


def _validate_validation_status(status: Any) -> None:
    if status not in VALIDATION_STATUSES:
        raise FeatureLabelDatasetError(f"Unsupported validation_status: {status!r}.")


def _validate_feature_value(value: Any, feature_type: str) -> None:
    if feature_type in ("numeric", "derived_numeric"):
        if not _is_number(value):
            raise FeatureLabelDatasetError(
                f"{feature_type} feature_value must be numeric."
            )
    elif feature_type in ("categorical", "derived_categorical", "text"):
        if not isinstance(value, str):
            raise FeatureLabelDatasetError(
                f"{feature_type} feature_value must be a string."
            )
    elif feature_type == "boolean":
        if not isinstance(value, bool):
            raise FeatureLabelDatasetError("boolean feature_value must be a bool.")
    elif feature_type == "missing":
        if value is not None:
            raise FeatureLabelDatasetError("missing feature_value must be None.")


def _validate_label_value(value: Any, label_type: str) -> None:
    if label_type == "binary":
        if not isinstance(value, bool):
            raise FeatureLabelDatasetError("binary label_value must be a bool.")
    elif label_type in ("numeric", "ordinal"):
        if not _is_number(value):
            raise FeatureLabelDatasetError(
                f"{label_type} label_value must be numeric."
            )
    elif label_type in ("categorical", "outcome_status", "review_status"):
        if not isinstance(value, str):
            raise FeatureLabelDatasetError(
                f"{label_type} label_value must be a string."
            )
    elif label_type == "unknown":
        if value is not None and not isinstance(value, str):
            raise FeatureLabelDatasetError(
                "unknown label_value must be None or a string."
            )


def _validate_confidence(confidence: Any) -> None:
    if not _is_number(confidence):
        raise FeatureLabelDatasetError("confidence must be numeric.")
    if confidence < 0.0 or confidence > 1.0:
        raise FeatureLabelDatasetError("confidence must be between 0.0 and 1.0.")


def _validate_label_auditability(
    label_name: str,
    outcome_source: str | None,
    source_record_id: str | None,
    evidence_reference: str | None,
) -> None:
    if label_name not in SUPERVISED_LABEL_NAMES:
        return
    if _has_text(outcome_source) or _has_text(source_record_id) or _has_text(evidence_reference):
        return
    raise FeatureLabelDatasetError(
        "supervised labels require outcome_source, source_record_id, or "
        "evidence_reference for auditability."
    )


def _validate_feature_schema_membership(
    feature_names: Sequence[str],
    referenced_names: Sequence[str],
) -> None:
    allowed = set(feature_names)
    for feature_name in referenced_names:
        if feature_name not in allowed:
            raise FeatureLabelDatasetError(
                f"Feature {feature_name!r} is not declared in feature_names."
            )


def _validate_label_schema_membership(
    label_names: Sequence[str],
    referenced_names: Sequence[str],
) -> None:
    allowed = set(label_names)
    for label_name in referenced_names:
        if label_name not in allowed:
            raise FeatureLabelDatasetError(
                f"Label {label_name!r} is not declared in label_names."
            )


def _validate_dataset_schema_versions(
    feature_schema_version: str,
    label_schema_version: str,
    features: Sequence[FeatureRecord],
    labels: Sequence[LabelRecord],
) -> None:
    for feature in features:
        if feature.feature_schema_version != feature_schema_version:
            raise FeatureLabelDatasetError(
                "Feature record schema version does not match dataset "
                "feature_schema_version."
            )
    for label in labels:
        if label.label_schema_version != label_schema_version:
            raise FeatureLabelDatasetError(
                "Label record schema version does not match dataset "
                "label_schema_version."
            )


def _normalize_features(features: Any) -> list[FeatureRecord]:
    if not isinstance(features, list):
        raise FeatureLabelDatasetError("features must be a list.")
    return [validate_feature_record(feature) for feature in features]


def _normalize_labels(labels: Any) -> list[LabelRecord]:
    if not isinstance(labels, list):
        raise FeatureLabelDatasetError("labels must be a list.")
    return [validate_label_record(label) for label in labels]


def _normalize_source_records(source_records: Any) -> list[dict[str, object]]:
    if not isinstance(source_records, list):
        raise FeatureLabelDatasetError("source_records must be a list.")
    normalized: list[dict[str, object]] = []
    for source_record in source_records:
        if not isinstance(source_record, Mapping):
            raise FeatureLabelDatasetError(
                "source_records must contain mapping objects only."
            )
        normalized.append(deepcopy(dict(source_record)))
    return normalized


def _find_unmatched_records(
    features: Sequence[FeatureRecord],
    labels: Sequence[LabelRecord],
) -> tuple[list[str], list[str]]:
    label_identity_sets = [_identity_tokens(label) for label in labels]
    feature_identity_sets = [_identity_tokens(feature) for feature in features]
    unmatched_feature_ids = [
        feature.feature_id
        for feature, feature_tokens in zip(features, feature_identity_sets)
        if not any(feature_tokens.intersection(label_tokens) for label_tokens in label_identity_sets)
    ]
    unmatched_label_ids = [
        label.label_id
        for label, label_tokens in zip(labels, label_identity_sets)
        if not any(label_tokens.intersection(feature_tokens) for feature_tokens in feature_identity_sets)
    ]
    return unmatched_feature_ids, unmatched_label_ids


def _add_join_record(
    groups: dict[str, dict[str, Any]],
    token_to_group: dict[tuple[str, str], str],
    record: FeatureRecord | LabelRecord,
    collection_name: str,
) -> None:
    tokens = sorted(_identity_tokens(record))
    existing_groups = sorted(
        {token_to_group[token] for token in tokens if token in token_to_group}
    )
    if existing_groups:
        group_key = existing_groups[0]
        for other_group_key in existing_groups[1:]:
            _merge_join_groups(groups, token_to_group, group_key, other_group_key)
    else:
        group_key = _join_group_key(tokens[0])
        groups[group_key] = {
            "tokens": set(),
            "run_ids": set(),
            "awr_ids": set(),
            "features": [],
            "labels": [],
        }

    group = groups[group_key]
    for token in tokens:
        group["tokens"].add(token)
        token_to_group[token] = group_key
        if token[0] == "RUN":
            group["run_ids"].add(token[1])
        elif token[0] == "AWR":
            group["awr_ids"].add(token[1])
    group[collection_name].append(record)


def _merge_join_groups(
    groups: dict[str, dict[str, Any]],
    token_to_group: dict[tuple[str, str], str],
    target_key: str,
    source_key: str,
) -> None:
    if target_key == source_key:
        return
    target = groups[target_key]
    source = groups.pop(source_key)
    target["tokens"].update(source["tokens"])
    target["run_ids"].update(source["run_ids"])
    target["awr_ids"].update(source["awr_ids"])
    target["features"].extend(source["features"])
    target["labels"].extend(source["labels"])
    for token in source["tokens"]:
        token_to_group[token] = target_key


def _identity_tokens(record: FeatureRecord | LabelRecord) -> set[tuple[str, str]]:
    tokens: set[tuple[str, str]] = set()
    if _has_text(record.run_id):
        tokens.add(("RUN", str(record.run_id).strip()))
    if _has_text(record.awr_id):
        tokens.add(("AWR", str(record.awr_id).strip()))
    if not tokens:
        raise FeatureLabelDatasetError("record must include run_id or awr_id.")
    return tokens


def _join_group_key(token: tuple[str, str]) -> str:
    return f"{token[0]}:{_identifier_fragment(token[1])}"


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
        raise FeatureLabelDatasetError(
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
            raise FeatureLabelDatasetError(
                f"{field_name} cannot be true on Phase 7T dataset inputs."
            )


def _normalize_string_list(
    values: Any,
    field_name: str,
    allow_empty: bool,
) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise FeatureLabelDatasetError(f"{field_name} must be a list of strings.")
    if not values and not allow_empty:
        raise FeatureLabelDatasetError(f"{field_name} must not be empty.")
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise FeatureLabelDatasetError(
                f"{field_name} must contain non-empty strings."
            )
        normalized.append(value.strip())
    return normalized


def _deduplicate_preserving_order(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduplicated.append(value)
    return deduplicated


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise FeatureLabelDatasetError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise FeatureLabelDatasetError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise FeatureLabelDatasetError(f"{field_name} must not be blank.")


def _require_any_identifier(run_id: str | None, awr_id: str | None) -> None:
    if not _has_text(run_id) and not _has_text(awr_id):
        raise FeatureLabelDatasetError("At least one of run_id or awr_id is required.")


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"


def _stable_hash(values: Sequence[str]) -> str:
    payload = json.dumps(sorted(values), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12].upper()
