"""Local Phase 7W ML training / backtesting harness records.

This module defines deterministic, offline training and backtesting evaluation
records over governed Phase 7T feature / label datasets. It does not train real
ML models, save model artifacts, register models, activate models, alter
runtime scoring, call services, write databases, or import parser/scoring/
decision/recommendation runtime paths.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import math
import re
from typing import Any, Mapping, Sequence

from src.learning.feature_label_dataset import (
    EXCLUDED_LABEL_NAMES,
    FeatureLabelDataset,
    LabelRecord,
    feature_label_dataset_from_dict,
    validate_feature_label_dataset,
)


TRAINING_MODEL_FAMILIES = (
    "baseline_majority",
    "baseline_numeric_mean",
    "shadow_placeholder",
    "tree",
    "neural_net",
    "hybrid_rule_ml",
    "linear",
)

LOCAL_HELPER_MODEL_FAMILIES = (
    "baseline_majority",
    "baseline_numeric_mean",
    "shadow_placeholder",
)

TRAINING_STATUSES = (
    "PLANNED",
    "TRAINED",
    "VALIDATED",
    "REJECTED",
    "INSUFFICIENT_DATA",
)

BACKTEST_STATUSES = (
    "BACKTESTED",
    "VALIDATED",
    "REJECTED",
    "INSUFFICIENT_DATA",
)

SPLIT_STRATEGIES = (
    "deterministic_holdout",
    "chronological_holdout",
    "full_backtest",
    "no_split",
)

METRIC_NAMES = (
    "accuracy",
    "precision",
    "recall",
    "mean_absolute_error",
    "baseline_accuracy",
    "disagreement_rate",
    "insufficient_label_count",
    "excluded_label_count",
)

DATASET_SPLIT_FIELDS = (
    "split_id",
    "dataset_id",
    "split_strategy",
    "train_record_ids",
    "test_record_ids",
    "validation_record_ids",
    "split_seed",
    "notes",
)

ML_TRAINING_PLAN_FIELDS = (
    "training_plan_id",
    "dataset_id",
    "dataset_name",
    "model_family",
    "feature_schema_version",
    "label_schema_version",
    "target_label_name",
    "split_strategy",
    "required_metrics",
    "created_by",
    "notes",
    "runtime_influence",
    "runtime_active",
)

ML_TRAINING_RESULT_FIELDS = (
    "training_id",
    "training_plan_id",
    "dataset_id",
    "model_family",
    "target_label_name",
    "split_id",
    "metrics",
    "training_status",
    "insufficient_label_count",
    "excluded_label_count",
    "validation_notes",
    "runtime_active",
    "runtime_influence_granted",
    "deterministic_runtime_remains_authoritative",
)

ML_BACKTEST_RESULT_FIELDS = (
    "backtest_id",
    "training_id",
    "dataset_id",
    "split_id",
    "test_record_count",
    "metrics",
    "baseline_comparison",
    "disagreement_count",
    "backtest_status",
    "validation_notes",
    "runtime_active",
    "runtime_influence_granted",
    "deterministic_runtime_remains_authoritative",
)

CLASSIFICATION_LABEL_TYPES = (
    "binary",
    "categorical",
    "outcome_status",
    "review_status",
)

NUMERIC_LABEL_TYPES = (
    "numeric",
    "ordinal",
)

SCORE_REFERENCE_ALIASES = {
    "deterministic_score": (
        "deterministic_score",
        "baseline_score",
        "deterministic_runtime_score",
    ),
    "trend_aware_score": (
        "trend_aware_score",
        "trend_score",
        "score_x_t",
    ),
    "shadow_ml_score": (
        "shadow_ml_score",
        "shadow_score",
        "score_ml",
    ),
}


class MLTrainingBacktestingError(ValueError):
    """Raised when Phase 7W training / backtesting rules are violated."""


@dataclass(frozen=True)
class DatasetSplit:
    """Deterministic train/test/validation partition for a governed dataset."""

    split_id: str
    dataset_id: str
    split_strategy: str
    train_record_ids: list[str]
    test_record_ids: list[str]
    validation_record_ids: list[str]
    split_seed: int | None
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.split_id, "split_id")
        _require_non_empty_string(self.dataset_id, "dataset_id")
        split_strategy = _normalize_split_strategy(self.split_strategy)
        train_record_ids = _normalize_string_list(
            self.train_record_ids,
            "train_record_ids",
            allow_empty=True,
        )
        test_record_ids = _normalize_string_list(
            self.test_record_ids,
            "test_record_ids",
            allow_empty=True,
        )
        validation_record_ids = _normalize_string_list(
            self.validation_record_ids,
            "validation_record_ids",
            allow_empty=True,
        )
        _validate_split_seed(self.split_seed)
        _validate_optional_string(self.notes, "notes")
        _validate_disjoint_ids(train_record_ids, test_record_ids, "train", "test")
        _validate_disjoint_ids(
            train_record_ids,
            validation_record_ids,
            "train",
            "validation",
        )
        _validate_disjoint_ids(
            test_record_ids,
            validation_record_ids,
            "test",
            "validation",
        )
        expected_split_id = create_split_id(
            self.dataset_id,
            split_strategy,
            self.split_seed,
        )
        if self.split_id != expected_split_id:
            raise MLTrainingBacktestingError(
                "split_id must match deterministic split ID."
            )
        object.__setattr__(self, "split_strategy", split_strategy)
        object.__setattr__(self, "train_record_ids", train_record_ids)
        object.__setattr__(self, "test_record_ids", test_record_ids)
        object.__setattr__(self, "validation_record_ids", validation_record_ids)


@dataclass(frozen=True)
class MLTrainingPlan:
    """Local metadata-only training evaluation plan."""

    training_plan_id: str
    dataset_id: str
    dataset_name: str | None
    model_family: str
    feature_schema_version: str
    label_schema_version: str
    target_label_name: str
    split_strategy: str
    required_metrics: list[str]
    created_by: str | None
    notes: str | None
    runtime_influence: bool
    runtime_active: bool

    def __post_init__(self) -> None:
        _require_non_empty_string(self.training_plan_id, "training_plan_id")
        _require_non_empty_string(self.dataset_id, "dataset_id")
        _validate_optional_string(self.dataset_name, "dataset_name")
        model_family = _normalize_model_family(self.model_family)
        _require_non_empty_string(
            self.feature_schema_version,
            "feature_schema_version",
        )
        _require_non_empty_string(self.label_schema_version, "label_schema_version")
        _require_non_empty_string(self.target_label_name, "target_label_name")
        split_strategy = _normalize_split_strategy(self.split_strategy)
        required_metrics = _normalize_metric_names(self.required_metrics)
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.notes, "notes")
        if self.runtime_influence is not False:
            raise MLTrainingBacktestingError(
                "Phase 7W training plans must keep runtime_influence=false."
            )
        if self.runtime_active is not False:
            raise MLTrainingBacktestingError(
                "Phase 7W training plans must keep runtime_active=false."
            )
        expected_plan_id = create_training_plan_id(
            self.dataset_id,
            model_family,
            self.target_label_name,
        )
        if self.training_plan_id != expected_plan_id:
            raise MLTrainingBacktestingError(
                "training_plan_id must match deterministic training plan ID."
            )
        object.__setattr__(self, "model_family", model_family)
        object.__setattr__(self, "split_strategy", split_strategy)
        object.__setattr__(self, "required_metrics", required_metrics)
        object.__setattr__(self, "runtime_influence", False)
        object.__setattr__(self, "runtime_active", False)


@dataclass(frozen=True)
class MLTrainingResult:
    """Deterministic local result from mock/baseline training evaluation."""

    training_id: str
    training_plan_id: str
    dataset_id: str
    model_family: str
    target_label_name: str
    split_id: str
    metrics: dict[str, float]
    training_status: str
    insufficient_label_count: int
    excluded_label_count: int
    validation_notes: list[str]
    runtime_active: bool
    runtime_influence_granted: bool
    deterministic_runtime_remains_authoritative: bool

    def __post_init__(self) -> None:
        _require_non_empty_string(self.training_id, "training_id")
        _require_non_empty_string(self.training_plan_id, "training_plan_id")
        _require_non_empty_string(self.dataset_id, "dataset_id")
        model_family = _normalize_model_family(self.model_family)
        _require_non_empty_string(self.target_label_name, "target_label_name")
        _require_non_empty_string(self.split_id, "split_id")
        metrics = _normalize_metrics(self.metrics)
        training_status = _normalize_training_status(self.training_status)
        _validate_nonnegative_int(
            self.insufficient_label_count,
            "insufficient_label_count",
        )
        _validate_nonnegative_int(self.excluded_label_count, "excluded_label_count")
        validation_notes = _normalize_string_list(
            self.validation_notes,
            "validation_notes",
            allow_empty=True,
        )
        if self.runtime_active is not False:
            raise MLTrainingBacktestingError(
                "Phase 7W training results must keep runtime_active=false."
            )
        if self.runtime_influence_granted is not False:
            raise MLTrainingBacktestingError(
                "Phase 7W training results must keep "
                "runtime_influence_granted=false."
            )
        if self.deterministic_runtime_remains_authoritative is not True:
            raise MLTrainingBacktestingError(
                "Phase 7W requires deterministic runtime to remain authoritative."
            )
        expected_training_id = create_training_id(
            self.training_plan_id,
            self.split_id,
        )
        if self.training_id != expected_training_id:
            raise MLTrainingBacktestingError(
                "training_id must match deterministic training result ID."
            )
        object.__setattr__(self, "model_family", model_family)
        object.__setattr__(self, "metrics", metrics)
        object.__setattr__(self, "training_status", training_status)
        object.__setattr__(self, "validation_notes", validation_notes)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)
        object.__setattr__(
            self,
            "deterministic_runtime_remains_authoritative",
            True,
        )


@dataclass(frozen=True)
class MLBacktestResult:
    """Deterministic local backtesting evidence record."""

    backtest_id: str
    training_id: str
    dataset_id: str
    split_id: str
    test_record_count: int
    metrics: dict[str, float]
    baseline_comparison: dict[str, object]
    disagreement_count: int
    backtest_status: str
    validation_notes: list[str]
    runtime_active: bool
    runtime_influence_granted: bool
    deterministic_runtime_remains_authoritative: bool

    def __post_init__(self) -> None:
        _require_non_empty_string(self.backtest_id, "backtest_id")
        _require_non_empty_string(self.training_id, "training_id")
        _require_non_empty_string(self.dataset_id, "dataset_id")
        _require_non_empty_string(self.split_id, "split_id")
        _validate_nonnegative_int(self.test_record_count, "test_record_count")
        metrics = _normalize_metrics(self.metrics)
        if not isinstance(self.baseline_comparison, dict):
            raise MLTrainingBacktestingError(
                "baseline_comparison must be a dictionary."
            )
        baseline_comparison = deepcopy(self.baseline_comparison)
        _validate_nonnegative_int(self.disagreement_count, "disagreement_count")
        backtest_status = _normalize_backtest_status(self.backtest_status)
        validation_notes = _normalize_string_list(
            self.validation_notes,
            "validation_notes",
            allow_empty=True,
        )
        if self.runtime_active is not False:
            raise MLTrainingBacktestingError(
                "Phase 7W backtest results must keep runtime_active=false."
            )
        if self.runtime_influence_granted is not False:
            raise MLTrainingBacktestingError(
                "Phase 7W backtest results must keep "
                "runtime_influence_granted=false."
            )
        if self.deterministic_runtime_remains_authoritative is not True:
            raise MLTrainingBacktestingError(
                "Phase 7W requires deterministic runtime to remain authoritative."
            )
        expected_backtest_id = create_backtest_id(self.training_id, self.split_id)
        if self.backtest_id != expected_backtest_id:
            raise MLTrainingBacktestingError(
                "backtest_id must match deterministic backtest ID."
            )
        object.__setattr__(self, "metrics", metrics)
        object.__setattr__(self, "baseline_comparison", baseline_comparison)
        object.__setattr__(self, "backtest_status", backtest_status)
        object.__setattr__(self, "validation_notes", validation_notes)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)
        object.__setattr__(
            self,
            "deterministic_runtime_remains_authoritative",
            True,
        )


def create_dataset_split(
    dataset: FeatureLabelDataset | Mapping[str, Any],
    split_strategy: str = "deterministic_holdout",
    split_seed: int | None = None,
) -> DatasetSplit:
    """Create a deterministic local split for a Phase 7T dataset."""

    validated_dataset = _normalize_dataset(dataset)
    split_strategy = _normalize_split_strategy(split_strategy)
    _validate_split_seed(split_seed)
    record_ids = _ordered_record_ids(validated_dataset, split_strategy, split_seed)

    if split_strategy == "no_split":
        train_record_ids = record_ids
        test_record_ids: list[str] = []
    elif split_strategy == "full_backtest":
        train_record_ids = []
        test_record_ids = record_ids
    else:
        train_record_ids, test_record_ids = _holdout_partition(record_ids)

    split = DatasetSplit(
        split_id=create_split_id(
            validated_dataset.dataset_id,
            split_strategy,
            split_seed,
        ),
        dataset_id=validated_dataset.dataset_id,
        split_strategy=split_strategy,
        train_record_ids=train_record_ids,
        test_record_ids=test_record_ids,
        validation_record_ids=[],
        split_seed=split_seed,
        notes=(
            "Phase 7W local deterministic split; evaluation records only; "
            "no runtime activation."
        ),
    )
    return validate_dataset_split(split)


def validate_dataset_split(split: DatasetSplit | Mapping[str, Any]) -> DatasetSplit:
    """Validate and return a local dataset split record."""

    if isinstance(split, Mapping):
        return dataset_split_from_dict(split)
    if not isinstance(split, DatasetSplit):
        raise MLTrainingBacktestingError("split must be a DatasetSplit.")
    return DatasetSplit(**dataset_split_to_dict(split))


def create_training_plan(
    dataset: FeatureLabelDataset | Mapping[str, Any],
    model_family: str,
    target_label_name: str,
    required_metrics: list[str] | None = None,
    split_strategy: str = "deterministic_holdout",
    created_by: str | None = None,
) -> MLTrainingPlan:
    """Create a metadata-only local training plan for governed input data."""

    validated_dataset = _normalize_dataset(dataset)
    model_family = _normalize_model_family(model_family)
    _require_non_empty_string(target_label_name, "target_label_name")
    split_strategy = _normalize_split_strategy(split_strategy)
    metrics = (
        list(METRIC_NAMES)
        if required_metrics is None
        else _normalize_metric_names(required_metrics)
    )
    plan = MLTrainingPlan(
        training_plan_id=create_training_plan_id(
            validated_dataset.dataset_id,
            model_family,
            target_label_name,
        ),
        dataset_id=validated_dataset.dataset_id,
        dataset_name=validated_dataset.dataset_name,
        model_family=model_family,
        feature_schema_version=validated_dataset.feature_schema_version,
        label_schema_version=validated_dataset.label_schema_version,
        target_label_name=target_label_name,
        split_strategy=split_strategy,
        required_metrics=metrics,
        created_by=created_by,
        notes=(
            "Phase 7W training plan is local evaluation metadata only; "
            "training/backtesting artifacts are evaluation records only."
        ),
        runtime_influence=False,
        runtime_active=False,
    )
    return validate_training_plan(plan)


def validate_training_plan(
    plan: MLTrainingPlan | Mapping[str, Any],
) -> MLTrainingPlan:
    """Validate and return a local metadata-only training plan."""

    if isinstance(plan, Mapping):
        return training_plan_from_dict(plan)
    if not isinstance(plan, MLTrainingPlan):
        raise MLTrainingBacktestingError("plan must be an MLTrainingPlan.")
    return MLTrainingPlan(**training_plan_to_dict(plan))


def run_baseline_training(
    plan: MLTrainingPlan | Mapping[str, Any],
    dataset: FeatureLabelDataset | Mapping[str, Any],
    split: DatasetSplit | Mapping[str, Any],
) -> MLTrainingResult:
    """Evaluate a deterministic baseline/mock training plan without real ML."""

    validated_plan = validate_training_plan(plan)
    validated_dataset = _normalize_dataset(dataset)
    validated_split = validate_dataset_split(split)
    _validate_plan_dataset_split(validated_plan, validated_dataset, validated_split)
    if validated_plan.model_family not in LOCAL_HELPER_MODEL_FAMILIES:
        raise MLTrainingBacktestingError(
            "Phase 7W local helpers only support baseline_majority, "
            "baseline_numeric_mean, and shadow_placeholder."
        )

    notes = [
        "No real ML model was trained.",
        "No model artifact was saved.",
        "Training/backtesting artifacts are evaluation records only.",
        "Deterministic runtime remains authoritative.",
    ]
    label_summary = _collect_target_labels(
        validated_dataset,
        validated_plan.target_label_name,
        validated_split.train_record_ids,
        validated_plan.model_family,
    )
    metrics: dict[str, float] = {
        "insufficient_label_count": float(label_summary["insufficient_label_count"]),
        "excluded_label_count": float(label_summary["excluded_label_count"]),
    }
    training_status = "INSUFFICIENT_DATA"

    rows = label_summary["rows"]
    baseline = _fit_baseline(validated_plan.model_family, rows)
    if baseline["status"] == "ok":
        if baseline["mode"] == "classification":
            predicted_values = [baseline["prediction"] for _row in rows]
            metrics.update(
                _classification_metrics(
                    [row.label.label_value for row in rows],
                    predicted_values,
                    _rows_are_binary(rows),
                )
            )
            metrics["baseline_accuracy"] = metrics["accuracy"]
        elif baseline["mode"] == "numeric":
            predicted_values = [baseline["prediction"] for _row in rows]
            metrics.update(
                _numeric_metrics(
                    [float(row.label.label_value) for row in rows],
                    predicted_values,
                )
            )
        training_status = "TRAINED"
        notes.append(str(baseline["note"]))
    else:
        notes.append(str(baseline["note"]))

    result = MLTrainingResult(
        training_id=create_training_id(
            validated_plan.training_plan_id,
            validated_split.split_id,
        ),
        training_plan_id=validated_plan.training_plan_id,
        dataset_id=validated_dataset.dataset_id,
        model_family=validated_plan.model_family,
        target_label_name=validated_plan.target_label_name,
        split_id=validated_split.split_id,
        metrics=metrics,
        training_status=training_status,
        insufficient_label_count=int(label_summary["insufficient_label_count"]),
        excluded_label_count=int(label_summary["excluded_label_count"]),
        validation_notes=_deduplicate_preserving_order(notes),
        runtime_active=False,
        runtime_influence_granted=False,
        deterministic_runtime_remains_authoritative=True,
    )
    return validate_training_result(result)


def validate_training_result(
    result: MLTrainingResult | Mapping[str, Any],
) -> MLTrainingResult:
    """Validate and return a local training result record."""

    if isinstance(result, Mapping):
        return training_result_from_dict(result)
    if not isinstance(result, MLTrainingResult):
        raise MLTrainingBacktestingError("result must be an MLTrainingResult.")
    return MLTrainingResult(**training_result_to_dict(result))


def run_backtest(
    training_result: MLTrainingResult | Mapping[str, Any],
    dataset: FeatureLabelDataset | Mapping[str, Any],
    split: DatasetSplit | Mapping[str, Any],
) -> MLBacktestResult:
    """Run deterministic baseline backtesting over held-out records."""

    validated_training_result = validate_training_result(training_result)
    validated_dataset = _normalize_dataset(dataset)
    validated_split = validate_dataset_split(split)
    _validate_result_dataset_split(
        validated_training_result,
        validated_dataset,
        validated_split,
    )
    notes = [
        "Backtesting success is not runtime activation.",
        "No runtime scoring changes are applied.",
        "Deterministic runtime remains authoritative.",
    ]
    metrics: dict[str, float] = {}
    disagreement_count = 0
    test_record_count = len(validated_split.test_record_ids)
    backtest_status = "INSUFFICIENT_DATA"

    train_summary = _collect_target_labels(
        validated_dataset,
        validated_training_result.target_label_name,
        validated_split.train_record_ids,
        validated_training_result.model_family,
    )
    test_summary = _collect_target_labels(
        validated_dataset,
        validated_training_result.target_label_name,
        validated_split.test_record_ids,
        validated_training_result.model_family,
    )
    metrics["insufficient_label_count"] = float(
        test_summary["insufficient_label_count"]
    )
    metrics["excluded_label_count"] = float(test_summary["excluded_label_count"])

    baseline = _fit_baseline(validated_training_result.model_family, train_summary["rows"])
    test_rows = test_summary["rows"]
    baseline_comparison = _baseline_comparison(
        validated_training_result,
        validated_dataset,
        validated_split,
        baseline,
    )

    if baseline["status"] == "ok" and test_rows:
        if baseline["mode"] == "classification":
            predicted_values = [baseline["prediction"] for _row in test_rows]
            actual_values = [row.label.label_value for row in test_rows]
            metrics.update(
                _classification_metrics(
                    actual_values,
                    predicted_values,
                    _rows_are_binary(test_rows),
                )
            )
            metrics["baseline_accuracy"] = metrics["accuracy"]
            disagreement_count = sum(
                1
                for actual, predicted in zip(actual_values, predicted_values)
                if actual != predicted
            )
        elif baseline["mode"] == "numeric":
            predicted_values = [baseline["prediction"] for _row in test_rows]
            actual_values = [float(row.label.label_value) for row in test_rows]
            metrics.update(_numeric_metrics(actual_values, predicted_values))
            disagreement_count = sum(
                1
                for actual, predicted in zip(actual_values, predicted_values)
                if _round_metric(abs(float(actual) - float(predicted))) > 0.0
            )
        metrics["disagreement_rate"] = _safe_rate(disagreement_count, len(test_rows))
        backtest_status = "BACKTESTED"
        notes.append(str(baseline["note"]))
    else:
        notes.append(str(baseline["note"]))
        if not test_rows:
            notes.append("No held-out target labels were available for backtesting.")

    result = MLBacktestResult(
        backtest_id=create_backtest_id(
            validated_training_result.training_id,
            validated_split.split_id,
        ),
        training_id=validated_training_result.training_id,
        dataset_id=validated_dataset.dataset_id,
        split_id=validated_split.split_id,
        test_record_count=test_record_count,
        metrics=metrics,
        baseline_comparison=baseline_comparison,
        disagreement_count=disagreement_count,
        backtest_status=backtest_status,
        validation_notes=_deduplicate_preserving_order(notes),
        runtime_active=False,
        runtime_influence_granted=False,
        deterministic_runtime_remains_authoritative=True,
    )
    return validate_backtest_result(result)


def validate_backtest_result(
    result: MLBacktestResult | Mapping[str, Any],
) -> MLBacktestResult:
    """Validate and return a local backtesting result record."""

    if isinstance(result, Mapping):
        return backtest_result_from_dict(result)
    if not isinstance(result, MLBacktestResult):
        raise MLTrainingBacktestingError("result must be an MLBacktestResult.")
    return MLBacktestResult(**backtest_result_to_dict(result))


def training_plan_to_dict(plan: MLTrainingPlan) -> dict[str, object]:
    """Return a deterministic dictionary for a training plan."""

    if not isinstance(plan, MLTrainingPlan):
        raise MLTrainingBacktestingError("plan must be an MLTrainingPlan.")
    return {
        field_name: deepcopy(getattr(plan, field_name))
        for field_name in ML_TRAINING_PLAN_FIELDS
    }


def training_plan_from_dict(data: Mapping[str, Any]) -> MLTrainingPlan:
    """Reconstruct and validate a training plan from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLTrainingBacktestingError("training plan data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        ML_TRAINING_PLAN_FIELDS,
        optional_defaults={
            "dataset_name": None,
            "required_metrics": list(METRIC_NAMES),
            "created_by": None,
            "notes": None,
            "runtime_influence": False,
            "runtime_active": False,
        },
    )
    return MLTrainingPlan(**values)


def dataset_split_to_dict(split: DatasetSplit) -> dict[str, object]:
    """Return a deterministic dictionary for a dataset split."""

    if not isinstance(split, DatasetSplit):
        raise MLTrainingBacktestingError("split must be a DatasetSplit.")
    return {
        field_name: deepcopy(getattr(split, field_name))
        for field_name in DATASET_SPLIT_FIELDS
    }


def dataset_split_from_dict(data: Mapping[str, Any]) -> DatasetSplit:
    """Reconstruct and validate a dataset split from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLTrainingBacktestingError("dataset split data must be a mapping.")
    _reject_split_runtime_fields(data)
    values = _values_from_mapping(
        data,
        DATASET_SPLIT_FIELDS,
        optional_defaults={
            "train_record_ids": [],
            "test_record_ids": [],
            "validation_record_ids": [],
            "split_seed": None,
            "notes": None,
        },
    )
    return DatasetSplit(**values)


def training_result_to_dict(result: MLTrainingResult) -> dict[str, object]:
    """Return a deterministic dictionary for a training result."""

    if not isinstance(result, MLTrainingResult):
        raise MLTrainingBacktestingError("result must be an MLTrainingResult.")
    return {
        field_name: deepcopy(getattr(result, field_name))
        for field_name in ML_TRAINING_RESULT_FIELDS
    }


def training_result_from_dict(data: Mapping[str, Any]) -> MLTrainingResult:
    """Reconstruct and validate a training result from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLTrainingBacktestingError("training result data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        ML_TRAINING_RESULT_FIELDS,
        optional_defaults={
            "metrics": {},
            "insufficient_label_count": 0,
            "excluded_label_count": 0,
            "validation_notes": [],
            "runtime_active": False,
            "runtime_influence_granted": False,
            "deterministic_runtime_remains_authoritative": True,
        },
    )
    return MLTrainingResult(**values)


def backtest_result_to_dict(result: MLBacktestResult) -> dict[str, object]:
    """Return a deterministic dictionary for a backtest result."""

    if not isinstance(result, MLBacktestResult):
        raise MLTrainingBacktestingError("result must be an MLBacktestResult.")
    return {
        field_name: deepcopy(getattr(result, field_name))
        for field_name in ML_BACKTEST_RESULT_FIELDS
    }


def backtest_result_from_dict(data: Mapping[str, Any]) -> MLBacktestResult:
    """Reconstruct and validate a backtest result from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLTrainingBacktestingError("backtest result data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        ML_BACKTEST_RESULT_FIELDS,
        optional_defaults={
            "metrics": {},
            "baseline_comparison": {},
            "disagreement_count": 0,
            "validation_notes": [],
            "runtime_active": False,
            "runtime_influence_granted": False,
            "deterministic_runtime_remains_authoritative": True,
        },
    )
    return MLBacktestResult(**values)


def create_training_plan_id(
    dataset_id: str,
    model_family: str,
    target_label_name: str,
) -> str:
    """Create a deterministic training plan identifier."""

    _require_non_empty_string(dataset_id, "dataset_id")
    model_family = _normalize_model_family(model_family)
    _require_non_empty_string(target_label_name, "target_label_name")
    return (
        f"TRAINING-PLAN-{_identifier_fragment(dataset_id)}-"
        f"{_identifier_fragment(model_family)}-"
        f"{_identifier_fragment(target_label_name)}"
    )


def create_split_id(
    dataset_id: str,
    split_strategy: str,
    split_seed: int | None = None,
) -> str:
    """Create a deterministic dataset split identifier."""

    _require_non_empty_string(dataset_id, "dataset_id")
    split_strategy = _normalize_split_strategy(split_strategy)
    _validate_split_seed(split_seed)
    seed_fragment = "NO-SEED" if split_seed is None else str(split_seed)
    return (
        f"SPLIT-{_identifier_fragment(dataset_id)}-"
        f"{_identifier_fragment(split_strategy)}-"
        f"{_identifier_fragment(seed_fragment)}"
    )


def create_training_id(training_plan_id: str, split_id: str) -> str:
    """Create a deterministic training result identifier."""

    _require_non_empty_string(training_plan_id, "training_plan_id")
    _require_non_empty_string(split_id, "split_id")
    return (
        f"TRAINING-RESULT-{_identifier_fragment(training_plan_id)}-"
        f"{_identifier_fragment(split_id)}"
    )


def create_backtest_id(training_id: str, split_id: str) -> str:
    """Create a deterministic backtest result identifier."""

    _require_non_empty_string(training_id, "training_id")
    _require_non_empty_string(split_id, "split_id")
    return (
        f"BACKTEST-{_identifier_fragment(training_id)}-"
        f"{_identifier_fragment(split_id)}"
    )


@dataclass(frozen=True)
class _LabelRow:
    record_id: str
    label: LabelRecord


def _normalize_dataset(
    dataset: FeatureLabelDataset | Mapping[str, Any],
) -> FeatureLabelDataset:
    if isinstance(dataset, Mapping):
        dataset = feature_label_dataset_from_dict(dataset)
    if not isinstance(dataset, FeatureLabelDataset):
        raise MLTrainingBacktestingError(
            "dataset must be a FeatureLabelDataset or mapping."
        )
    return validate_feature_label_dataset(dataset)


def _validate_plan_dataset_split(
    plan: MLTrainingPlan,
    dataset: FeatureLabelDataset,
    split: DatasetSplit,
) -> None:
    if plan.dataset_id != dataset.dataset_id:
        raise MLTrainingBacktestingError("training plan dataset_id must match dataset.")
    if split.dataset_id != dataset.dataset_id:
        raise MLTrainingBacktestingError("dataset split dataset_id must match dataset.")
    if plan.split_strategy != split.split_strategy:
        raise MLTrainingBacktestingError(
            "training plan split_strategy must match dataset split."
        )


def _validate_result_dataset_split(
    result: MLTrainingResult,
    dataset: FeatureLabelDataset,
    split: DatasetSplit,
) -> None:
    if result.dataset_id != dataset.dataset_id:
        raise MLTrainingBacktestingError(
            "training result dataset_id must match dataset."
        )
    if split.dataset_id != dataset.dataset_id:
        raise MLTrainingBacktestingError("dataset split dataset_id must match dataset.")
    if result.split_id != split.split_id:
        raise MLTrainingBacktestingError(
            "training result split_id must match dataset split."
        )


def _ordered_record_ids(
    dataset: FeatureLabelDataset,
    split_strategy: str,
    split_seed: int | None,
) -> list[str]:
    record_ids = sorted(_dataset_record_ids(dataset))
    if split_strategy == "deterministic_holdout" and split_seed is not None:
        return sorted(
            record_ids,
            key=lambda record_id: (
                _stable_split_hash(record_id, split_seed),
                record_id,
            ),
        )
    if split_strategy == "chronological_holdout":
        order_hints = _source_record_order_hints(dataset)
        return sorted(
            record_ids,
            key=lambda record_id: (order_hints.get(record_id, record_id), record_id),
        )
    return record_ids


def _dataset_record_ids(dataset: FeatureLabelDataset) -> set[str]:
    record_ids: set[str] = set()
    for feature in dataset.features:
        record_ids.add(_record_id(feature.run_id, feature.awr_id))
    for label in dataset.labels:
        record_ids.add(_record_id(label.run_id, label.awr_id))
    for source_record in dataset.source_records:
        record_id = _source_record_id(source_record)
        if record_id is not None:
            record_ids.add(record_id)
    return record_ids


def _source_record_order_hints(dataset: FeatureLabelDataset) -> dict[str, str]:
    hints: dict[str, str] = {}
    for source_record in dataset.source_records:
        record_id = _source_record_id(source_record)
        if record_id is None:
            continue
        hint = source_record.get("created_at")
        if hint is None:
            hint = source_record.get("snapshot_time")
        if hint is None:
            hint = source_record.get("record_time")
        if isinstance(hint, str) and hint.strip():
            hints[record_id] = hint.strip()
    return hints


def _source_record_id(source_record: Mapping[str, object]) -> str | None:
    for field_name in ("record_id", "run_id", "awr_id", "id"):
        value = source_record.get(field_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _holdout_partition(record_ids: Sequence[str]) -> tuple[list[str], list[str]]:
    ids = list(record_ids)
    if len(ids) <= 1:
        return ids, []
    test_count = max(1, len(ids) // 5)
    return ids[:-test_count], ids[-test_count:]


def _collect_target_labels(
    dataset: FeatureLabelDataset,
    target_label_name: str,
    record_ids: Sequence[str],
    model_family: str,
) -> dict[str, object]:
    selected_ids = set(record_ids)
    target_labels = [
        label
        for label in sorted(
            dataset.labels,
            key=lambda value: (_record_id(value.run_id, value.awr_id), value.label_id),
        )
        if label.label_name == target_label_name
        and _record_id(label.run_id, label.awr_id) in selected_ids
    ]
    rows: list[_LabelRow] = []
    excluded_label_count = 0
    for label in target_labels:
        if _label_is_valid_for_model(label, model_family):
            rows.append(_LabelRow(_record_id(label.run_id, label.awr_id), label))
        else:
            excluded_label_count += 1
    valid_record_ids = {row.record_id for row in rows}
    insufficient_label_count = len(selected_ids - valid_record_ids)
    return {
        "rows": rows,
        "insufficient_label_count": insufficient_label_count,
        "excluded_label_count": excluded_label_count,
    }


def _label_is_valid_for_model(label: LabelRecord, model_family: str) -> bool:
    if label.label_name in EXCLUDED_LABEL_NAMES:
        return False
    if label.label_type == "unknown" or label.label_value is None:
        return False
    mode = _model_family_mode(model_family, [label])
    if mode == "classification":
        return label.label_type in CLASSIFICATION_LABEL_TYPES
    if mode == "numeric":
        return label.label_type in NUMERIC_LABEL_TYPES and _is_number(label.label_value)
    return False


def _fit_baseline(model_family: str, rows: Sequence[_LabelRow]) -> dict[str, object]:
    if not rows:
        return {
            "status": "insufficient",
            "mode": None,
            "prediction": None,
            "note": "Insufficient governed labels for baseline evaluation.",
        }
    mode = _model_family_mode(model_family, [row.label for row in rows])
    if mode == "classification":
        counter = Counter(row.label.label_value for row in rows)
        prediction = sorted(
            counter,
            key=lambda value: (-counter[value], _stable_value_key(value)),
        )[0]
        return {
            "status": "ok",
            "mode": "classification",
            "prediction": prediction,
            "note": "Deterministic majority-label baseline evaluated.",
        }
    if mode == "numeric":
        numeric_values = [float(row.label.label_value) for row in rows]
        prediction = _round_metric(sum(numeric_values) / len(numeric_values))
        return {
            "status": "ok",
            "mode": "numeric",
            "prediction": prediction,
            "note": "Deterministic numeric-mean baseline evaluated.",
        }
    return {
        "status": "insufficient",
        "mode": None,
        "prediction": None,
        "note": "No supported label type was available for baseline evaluation.",
    }


def _model_family_mode(
    model_family: str,
    labels: Sequence[LabelRecord],
) -> str | None:
    if model_family == "baseline_majority":
        return "classification"
    if model_family == "baseline_numeric_mean":
        return "numeric"
    if model_family == "shadow_placeholder":
        if labels and all(label.label_type in NUMERIC_LABEL_TYPES for label in labels):
            return "numeric"
        return "classification"
    return None


def _classification_metrics(
    actual_values: Sequence[object],
    predicted_values: Sequence[object],
    binary: bool,
) -> dict[str, float]:
    if not actual_values:
        return {}
    correct_count = sum(
        1 for actual, predicted in zip(actual_values, predicted_values) if actual == predicted
    )
    metrics = {
        "accuracy": _safe_rate(correct_count, len(actual_values)),
    }
    if binary:
        true_positive = sum(
            1
            for actual, predicted in zip(actual_values, predicted_values)
            if actual is True and predicted is True
        )
        predicted_positive = sum(1 for value in predicted_values if value is True)
        actual_positive = sum(1 for value in actual_values if value is True)
        metrics["precision"] = _safe_rate(true_positive, predicted_positive)
        metrics["recall"] = _safe_rate(true_positive, actual_positive)
    return metrics


def _numeric_metrics(
    actual_values: Sequence[float],
    predicted_values: Sequence[float],
) -> dict[str, float]:
    if not actual_values:
        return {}
    absolute_error_sum = sum(
        abs(float(actual) - float(predicted))
        for actual, predicted in zip(actual_values, predicted_values)
    )
    return {
        "mean_absolute_error": _round_metric(
            absolute_error_sum / len(actual_values)
        )
    }


def _baseline_comparison(
    result: MLTrainingResult,
    dataset: FeatureLabelDataset,
    split: DatasetSplit,
    baseline: Mapping[str, object],
) -> dict[str, object]:
    score_summary = _score_reference_summary(dataset, split.test_record_ids)
    comparison = {
        "model_family": result.model_family,
        "target_label_name": result.target_label_name,
        "split_id": split.split_id,
        "comparison_scope": "held_out_test_records",
        "baseline_mode": baseline.get("mode"),
        "baseline_prediction": baseline.get("prediction"),
        "baseline_note": baseline.get("note"),
        "score_reference_summary": score_summary,
        "runtime_boundary": (
            "Backtest comparisons are evidence only; deterministic runtime "
            "remains authoritative."
        ),
    }
    return comparison


def _score_reference_summary(
    dataset: FeatureLabelDataset,
    record_ids: Sequence[str],
) -> dict[str, object]:
    selected_ids = set(record_ids)
    values_by_name: dict[str, list[float]] = {
        name: [] for name in SCORE_REFERENCE_ALIASES
    }
    for feature in dataset.features:
        record_id = _record_id(feature.run_id, feature.awr_id)
        if record_id not in selected_ids:
            continue
        normalized_name = str(feature.feature_name).strip().lower()
        for score_name, aliases in SCORE_REFERENCE_ALIASES.items():
            if normalized_name in aliases and _is_number(feature.feature_value):
                values_by_name[score_name].append(float(feature.feature_value))
    for source_record in dataset.source_records:
        record_id = _source_record_id(source_record)
        if record_id not in selected_ids:
            continue
        for score_name, aliases in SCORE_REFERENCE_ALIASES.items():
            for alias in aliases:
                value = source_record.get(alias)
                if _is_number(value):
                    values_by_name[score_name].append(float(value))

    summary: dict[str, object] = {
        "deterministic_runtime_remains_authoritative": True,
    }
    for score_name, values in values_by_name.items():
        summary[f"{score_name}_available_count"] = len(values)
        summary[f"{score_name}_mean"] = (
            None if not values else _round_metric(sum(values) / len(values))
        )
    deterministic_mean = summary["deterministic_score_mean"]
    trend_mean = summary["trend_aware_score_mean"]
    shadow_mean = summary["shadow_ml_score_mean"]
    summary["trend_delta_from_deterministic"] = _optional_delta(
        trend_mean,
        deterministic_mean,
    )
    summary["shadow_delta_from_deterministic"] = _optional_delta(
        shadow_mean,
        deterministic_mean,
    )
    return summary


def _rows_are_binary(rows: Sequence[_LabelRow]) -> bool:
    return bool(rows) and all(row.label.label_type == "binary" for row in rows)


def _record_id(run_id: str | None, awr_id: str | None) -> str:
    if _has_text(run_id):
        return str(run_id).strip()
    if _has_text(awr_id):
        return str(awr_id).strip()
    raise MLTrainingBacktestingError("At least one of run_id or awr_id is required.")


def _normalize_model_family(value: Any) -> str:
    _require_non_empty_string(value, "model_family")
    normalized = str(value).strip().lower()
    if normalized not in TRAINING_MODEL_FAMILIES:
        raise MLTrainingBacktestingError(f"Unsupported model_family: {value!r}.")
    return normalized


def _normalize_split_strategy(value: Any) -> str:
    _require_non_empty_string(value, "split_strategy")
    normalized = str(value).strip().lower()
    if normalized not in SPLIT_STRATEGIES:
        raise MLTrainingBacktestingError(f"Unsupported split_strategy: {value!r}.")
    return normalized


def _normalize_training_status(value: Any) -> str:
    _require_non_empty_string(value, "training_status")
    normalized = str(value).strip().upper()
    if normalized not in TRAINING_STATUSES:
        raise MLTrainingBacktestingError(f"Unsupported training_status: {value!r}.")
    return normalized


def _normalize_backtest_status(value: Any) -> str:
    _require_non_empty_string(value, "backtest_status")
    normalized = str(value).strip().upper()
    if normalized not in BACKTEST_STATUSES:
        raise MLTrainingBacktestingError(f"Unsupported backtest_status: {value!r}.")
    return normalized


def _normalize_metric_names(values: Any) -> list[str]:
    metric_names = _normalize_string_list(
        values,
        "required_metrics",
        allow_empty=False,
    )
    normalized: list[str] = []
    for metric_name in metric_names:
        token = metric_name.strip().lower()
        if token not in METRIC_NAMES:
            raise MLTrainingBacktestingError(
                f"Unsupported metric name: {metric_name!r}."
            )
        normalized.append(token)
    return _deduplicate_preserving_order(normalized)


def _normalize_metrics(values: Any) -> dict[str, float]:
    if not isinstance(values, Mapping):
        raise MLTrainingBacktestingError("metrics must be a mapping.")
    normalized: dict[str, float] = {}
    for key, value in values.items():
        if key not in METRIC_NAMES:
            raise MLTrainingBacktestingError(f"Unsupported metric: {key!r}.")
        _validate_metric_value(key, value)
        normalized[key] = _round_metric(float(value))
    return normalized


def _validate_metric_value(metric_name: str, value: Any) -> None:
    if not _is_number(value) or not math.isfinite(float(value)):
        raise MLTrainingBacktestingError(f"{metric_name} metric must be numeric.")
    if float(value) < 0.0:
        raise MLTrainingBacktestingError(f"{metric_name} metric must be non-negative.")
    if metric_name in ("accuracy", "precision", "recall", "baseline_accuracy", "disagreement_rate"):
        if float(value) > 1.0:
            raise MLTrainingBacktestingError(
                f"{metric_name} metric must be between 0.0 and 1.0."
            )


def _validate_split_seed(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool):
        raise MLTrainingBacktestingError("split_seed must be None or an integer.")
    if value < 0:
        raise MLTrainingBacktestingError("split_seed must be non-negative.")


def _validate_nonnegative_int(value: Any, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise MLTrainingBacktestingError(f"{field_name} must be an integer.")
    if value < 0:
        raise MLTrainingBacktestingError(f"{field_name} must be non-negative.")


def _validate_disjoint_ids(
    left_ids: Sequence[str],
    right_ids: Sequence[str],
    left_name: str,
    right_name: str,
) -> None:
    overlap = set(left_ids).intersection(right_ids)
    if overlap:
        raise MLTrainingBacktestingError(
            f"{left_name} and {right_name} record ids must not overlap: "
            + ", ".join(sorted(overlap))
        )


def _normalize_string_list(
    values: Any,
    field_name: str,
    allow_empty: bool,
) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise MLTrainingBacktestingError(f"{field_name} must be a list of strings.")
    if not values and not allow_empty:
        raise MLTrainingBacktestingError(f"{field_name} must not be empty.")
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise MLTrainingBacktestingError(
                f"{field_name} must contain non-empty strings."
            )
        normalized.append(value.strip())
    return _deduplicate_preserving_order(normalized)


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MLTrainingBacktestingError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise MLTrainingBacktestingError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise MLTrainingBacktestingError(f"{field_name} must not be blank.")


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
        raise MLTrainingBacktestingError(
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
            raise MLTrainingBacktestingError(
                f"{field_name} cannot be true on Phase 7W evaluation records."
            )
    if data.get("deterministic_runtime_remains_authoritative") is False:
        raise MLTrainingBacktestingError(
            "deterministic_runtime_remains_authoritative cannot be false on "
            "Phase 7W evaluation records."
        )


def _reject_split_runtime_fields(data: Mapping[str, Any]) -> None:
    for field_name in (
        "runtime_influence",
        "runtime_active",
        "runtime_influence_granted",
        "deterministic_runtime_remains_authoritative",
    ):
        if field_name in data:
            raise MLTrainingBacktestingError(
                f"{field_name} is not a DatasetSplit field in Phase 7W."
            )


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return _round_metric(float(numerator) / float(denominator))


def _optional_delta(left: object, right: object) -> float | None:
    if left is None or right is None:
        return None
    return _round_metric(float(left) - float(right))


def _round_metric(value: float) -> float:
    return round(float(value), 6)


def _stable_split_hash(record_id: str, split_seed: int) -> str:
    payload = f"{split_seed}:{record_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _stable_value_key(value: object) -> str:
    if isinstance(value, bool):
        return "1:true" if value else "0:false"
    return repr(value)


def _deduplicate_preserving_order(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduplicated.append(value)
    return deduplicated


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"
