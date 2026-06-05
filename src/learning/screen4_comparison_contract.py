"""Screen 4 deterministic comparison output contract adapter.

This module adapts trusted backend comparison artifacts into the strict Screen 4
contract required by the 7CX Comparative Review guard. It performs pure data
transformation and validation only. It does not read files, call parsers, query
databases, regenerate dashboards, invoke LLMs, or compute anything in the
browser.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from src.learning.governed_workflow_repository import PersistedWorkflowOutputArtifact
from src.learning.screen3_comparison_execution import (
    ComparisonExecutionResult,
    ComparisonOutputReference,
    comparison_execution_result_to_dict,
    comparison_output_reference_to_dict,
)
from src.learning.screen3_reanalysis_controller import (
    AWRReportComparisonArtifact,
    awr_report_comparison_artifact_from_dict,
    awr_report_comparison_artifact_to_dict,
)


SCREEN4_COMPARISON_CONTRACT_TYPE = "deterministic_comparison_output"
SCREEN4_COMPARISON_CONTRACT_VERSION = "7cx.screen4.comparison.v1"
SCREEN4_COMPARISON_ADAPTER_VERSION = "7cx-adapter-v1"
DETERMINISTIC_COMPARISON_ENGINE_VERSION = "phase7-am-comparison-v1"

ALLOWED_SOURCE_SCOPES = {
    "single_awr",
    "same_db_historical",
    "fleet",
    "population",
    "prepared_context",
}
ALLOWED_COMPARISON_SCOPES = {"target_a_vs_target_b", "period", "run", "report"}
CONSERVATIVE_VISUALIZATIONS = {
    "metric_delta_table",
    "domain_delta_summary",
    "confidence_basis_panel",
    "missing_evidence_panel",
}
BLOCKED_VISUALIZATIONS = {
    "time_series_overlay",
    "distribution_violin",
    "wait_class_movement_table",
    "top_sql_movement_table",
    "top_event_movement_table",
}
REQUIRED_CONTRACT_FIELDS = (
    "screen4_contract_type",
    "contract_version",
    "adapter_version",
    "comparison_id",
    "baseline_run_id",
    "candidate_run_id",
    "target_a_identity",
    "target_b_identity",
    "target_alignment",
    "source_scope",
    "comparison_scope",
    "generated_by",
    "generated_at",
    "deterministic_engine_version",
    "metric_deltas",
    "domain_deltas",
    "evidence_rows",
    "confidence_basis",
    "missing_evidence",
    "allowed_visualizations",
    "validation_status",
)

IDENTITY_KEYS = (
    "run_id",
    "awr_id",
    "db_name",
    "database_name",
    "dbid",
    "instance",
    "instance_name",
    "host",
    "host_name",
    "snapshot",
    "snapshot_label",
    "window",
    "time_window",
    "source_type",
    "scope_type",
    "scope_value",
)


@dataclass(frozen=True)
class Screen4ComparisonAdapterMessage:
    """Validation or adaptation message for Screen 4 comparison contracts."""

    code: str
    message: str
    severity: str = "error"
    field: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.code, "code")
        _require_text(self.message, "message")
        _require_text(self.severity, "severity")
        if self.severity not in {"error", "warning", "info"}:
            raise ValueError("severity must be error, warning, or info.")
        if self.field is not None:
            _require_text(self.field, "field")

    def to_dict(self) -> dict[str, str]:
        payload = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        if self.field:
            payload["field"] = self.field
        return payload


@dataclass(frozen=True)
class Screen4ComparisonAdapterResult:
    """Result returned by the Screen 4 comparison contract adapter."""

    contract: dict[str, Any] | None
    validation_status: str
    output_ready: bool
    messages: list[Screen4ComparisonAdapterMessage]
    allowed_visualizations: list[str]

    def __post_init__(self) -> None:
        if self.validation_status not in {"valid", "invalid"}:
            raise ValueError("validation_status must be valid or invalid.")
        if not isinstance(self.output_ready, bool):
            raise ValueError("output_ready must be boolean.")
        if not isinstance(self.messages, list) or not all(
            isinstance(item, Screen4ComparisonAdapterMessage)
            for item in self.messages
        ):
            raise ValueError("messages must be adapter message instances.")
        if not isinstance(self.allowed_visualizations, list) or not all(
            isinstance(item, str) for item in self.allowed_visualizations
        ):
            raise ValueError("allowed_visualizations must be a list of strings.")
        if self.output_ready and self.contract is None:
            raise ValueError("output_ready requires a contract.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "validation_status": self.validation_status,
            "output_ready": self.output_ready,
            "messages": [message.to_dict() for message in self.messages],
            "allowed_visualizations": list(self.allowed_visualizations),
        }


def adapt_screen4_deterministic_comparison_output(
    comparison_source: Any,
    *,
    prepared_target_context: dict[str, Any] | None = None,
    workflow_metadata: dict[str, Any] | None = None,
    generated_at: str | None = None,
    deterministic_engine_version: str | None = DETERMINISTIC_COMPARISON_ENGINE_VERSION,
    source_scope: str | None = None,
    comparison_scope: str | None = None,
) -> Screen4ComparisonAdapterResult:
    """Adapt trusted comparison metadata into the Screen 4 output contract."""

    workflow = _workflow_metadata_from_source(comparison_source)
    if isinstance(workflow_metadata, dict):
        workflow.update(workflow_metadata)

    artifact, source_messages = _extract_comparison_artifact(comparison_source)
    messages = list(source_messages)
    if artifact is None:
        return _invalid(messages or [_message("comparison_artifact_missing", "A trusted comparison artifact is required.")])

    prepared_context = prepared_target_context if isinstance(prepared_target_context, dict) else {}
    target_a = _prepared_target_identity(prepared_context, "A")
    target_b = _prepared_target_identity(prepared_context, "B")
    if not target_a:
        messages.append(_message("target_a_identity_missing", "Target A identity is required.", field="target_a_identity"))
    elif not _has_text(target_a.get("run_id")):
        messages.append(_message("target_a_run_id_missing", "Target A run_id is required for Screen 4 alignment.", field="target_a_identity.run_id"))
    if not target_b:
        messages.append(_message("target_b_identity_missing", "Target B identity is required.", field="target_b_identity"))
    elif not _has_text(target_b.get("run_id")):
        messages.append(_message("target_b_run_id_missing", "Target B run_id is required for Screen 4 alignment.", field="target_b_identity.run_id"))

    baseline_run_id = _resolve_baseline_run_id(artifact)
    candidate_run_id = _resolve_candidate_run_id(artifact)
    if not _has_text(baseline_run_id):
        messages.append(_message("baseline_run_id_unresolved", "Baseline run id could not be resolved.", field="baseline_run_id"))
    if not _has_text(candidate_run_id):
        messages.append(_message("candidate_run_id_unresolved", "Candidate run id could not be resolved.", field="candidate_run_id"))

    target_alignment_messages = _target_alignment_messages(
        artifact,
        target_a,
        target_b,
        baseline_run_id,
        candidate_run_id,
    )
    messages.extend(target_alignment_messages)

    resolved_source_scope = _resolve_source_scope(
        source_scope,
        workflow,
        prepared_context,
    )
    messages.extend(
        _scope_mismatch_messages(
            "source_scope",
            source_scope,
            workflow.get("source_scope"),
            prepared_context.get("source_scope"),
        )
    )
    if resolved_source_scope not in ALLOWED_SOURCE_SCOPES:
        messages.append(_message("source_scope_invalid", "Screen 4 source scope is missing or unsupported.", field="source_scope"))

    resolved_comparison_scope = _resolve_comparison_scope(
        comparison_scope,
        workflow,
        prepared_context,
    )
    messages.extend(
        _scope_mismatch_messages(
            "comparison_scope",
            comparison_scope,
            workflow.get("comparison_scope"),
            prepared_context.get("comparison_scope"),
        )
    )
    if resolved_comparison_scope not in ALLOWED_COMPARISON_SCOPES:
        messages.append(_message("comparison_scope_invalid", "Screen 4 comparison scope is missing or unsupported.", field="comparison_scope"))

    generated_at_value = _first_text(
        generated_at,
        workflow.get("generated_at"),
        workflow.get("created_at"),
    )
    if not generated_at_value:
        messages.append(_message("generated_at_missing", "A backend generated_at timestamp is required.", field="generated_at"))
    if not _has_text(deterministic_engine_version):
        messages.append(_message("deterministic_engine_version_missing", "Deterministic comparison engine version is required.", field="deterministic_engine_version"))

    if any(message.severity == "error" for message in messages):
        return _invalid(messages)

    metric_deltas, evidence_rows = _build_metric_and_evidence_rows(
        artifact,
        baseline_run_id,
        candidate_run_id,
    )
    domain_deltas = _build_domain_deltas(metric_deltas)
    missing_evidence = _build_missing_evidence(artifact)
    confidence_basis = {
        "basis_type": "deterministic_evidence",
        "sample_count": artifact.get("compared_report_count") or 0,
        "evidence_row_count": len(evidence_rows),
        "missing_evidence_count": len(missing_evidence),
        "limitations": list(artifact.get("comparison_limitations") or []),
    }
    allowed_visualizations = _allowed_visualizations(
        metric_deltas,
        domain_deltas,
        missing_evidence,
        confidence_basis,
    )
    target_alignment = {
        "status": "aligned",
        "basis": [
            "baseline_run_id matches Target A run_id",
            "candidate_run_id matches Target B run_id",
        ],
    }
    if target_a.get("awr_id") and artifact.get("compared_awr_ids"):
        target_alignment["basis"].append("Target A AWR identity checked")
    if target_b.get("awr_id") and artifact.get("compared_awr_ids"):
        target_alignment["basis"].append("Target B AWR identity checked")

    contract: dict[str, Any] = {
        "screen4_contract_type": SCREEN4_COMPARISON_CONTRACT_TYPE,
        "contract_version": SCREEN4_COMPARISON_CONTRACT_VERSION,
        "adapter_version": SCREEN4_COMPARISON_ADAPTER_VERSION,
        "comparison_id": artifact["comparison_id"],
        "baseline_run_id": baseline_run_id,
        "candidate_run_id": candidate_run_id,
        "target_a_identity": target_a,
        "target_b_identity": target_b,
        "target_alignment": target_alignment,
        "source_scope": resolved_source_scope,
        "comparison_scope": resolved_comparison_scope,
        "artifact_source": _first_text(workflow.get("artifact_source"), "phase7cc_comparison_execution"),
        "artifact_reference": _first_text(
            workflow.get("artifact_reference"),
            f"comparison:{artifact['comparison_id']}",
        ),
        "workflow_request_id": _first_text(workflow.get("workflow_request_id"), workflow.get("request_id")),
        "workflow_transaction_id": _first_text(workflow.get("workflow_transaction_id"), workflow.get("transaction_group_id")),
        "comparison_execution_id": _first_text(workflow.get("comparison_execution_id")),
        "input_artifact_ids": _input_artifact_ids(workflow),
        "input_snapshot_range": _input_snapshot_range(target_a, target_b),
        "generated_from_hash": _generated_from_hash(artifact, target_a, target_b, workflow),
        "generated_by": "deterministic_engine",
        "generated_at": generated_at_value,
        "deterministic_engine_version": deterministic_engine_version,
        "metric_deltas": metric_deltas,
        "domain_deltas": domain_deltas,
        "evidence_rows": evidence_rows,
        "confidence_basis": confidence_basis,
        "missing_evidence": missing_evidence,
        "allowed_visualizations": allowed_visualizations,
        "validation_status": "valid",
        "adapter_validation_messages": [message.to_dict() for message in messages],
    }
    if artifact.get("created_by"):
        contract["artifact_created_by"] = artifact.get("created_by")
    if workflow.get("actor_id"):
        contract["request_actor"] = workflow.get("actor_id")
    if not evidence_rows:
        contract["no_change_evidence"] = {
            "basis_type": "deterministic_evidence",
            "explanation": "Deterministic adapter found no displayable difference rows for this comparison artifact.",
        }

    validation = validate_screen4_comparison_contract(contract, prepared_target_context=prepared_context)
    if not validation.output_ready:
        return validation
    return Screen4ComparisonAdapterResult(
        contract=contract,
        validation_status="valid",
        output_ready=True,
        messages=messages,
        allowed_visualizations=allowed_visualizations,
    )


def validate_screen4_comparison_contract(
    contract: Any,
    *,
    prepared_target_context: dict[str, Any] | None = None,
) -> Screen4ComparisonAdapterResult:
    """Validate a Screen 4 deterministic comparison output contract."""

    if not isinstance(contract, dict) or not contract:
        return _invalid([_message("contract_missing", "Screen 4 comparison contract is required.")])

    messages: list[Screen4ComparisonAdapterMessage] = []
    for field in REQUIRED_CONTRACT_FIELDS:
        if field not in contract or not _field_present(contract.get(field)):
            messages.append(_message("required_field_missing", f"{field} is required.", field=field))

    if contract.get("screen4_contract_type") != SCREEN4_COMPARISON_CONTRACT_TYPE:
        messages.append(_message("contract_type_invalid", "screen4_contract_type must be deterministic_comparison_output.", field="screen4_contract_type"))
    if contract.get("contract_version") != SCREEN4_COMPARISON_CONTRACT_VERSION:
        messages.append(_message("contract_version_invalid", "Unsupported Screen 4 comparison contract version.", field="contract_version"))
    if not _has_text(contract.get("adapter_version")):
        messages.append(_message("adapter_version_missing", "adapter_version is required.", field="adapter_version"))
    if contract.get("generated_by") != "deterministic_engine":
        messages.append(_message("generated_by_invalid", "generated_by must be deterministic_engine.", field="generated_by"))
    if contract.get("source_scope") not in ALLOWED_SOURCE_SCOPES:
        messages.append(_message("source_scope_invalid", "source_scope is unsupported.", field="source_scope"))
    if contract.get("comparison_scope") not in ALLOWED_COMPARISON_SCOPES:
        messages.append(_message("comparison_scope_invalid", "comparison_scope is unsupported.", field="comparison_scope"))
    if contract.get("validation_status") != "valid":
        messages.append(_message("validation_status_invalid", "validation_status must be valid.", field="validation_status"))

    for field in ("metric_deltas", "domain_deltas", "evidence_rows", "missing_evidence", "allowed_visualizations"):
        if field in contract and not isinstance(contract.get(field), list):
            messages.append(_message("list_field_invalid", f"{field} must be a list.", field=field))

    confidence_basis = contract.get("confidence_basis")
    if not isinstance(confidence_basis, dict):
        messages.append(_message("confidence_basis_invalid", "confidence_basis must be a mapping.", field="confidence_basis"))
    else:
        if confidence_basis.get("basis_type") != "deterministic_evidence":
            messages.append(_message("confidence_basis_invalid", "confidence_basis.basis_type must be deterministic_evidence.", field="confidence_basis.basis_type"))
        if "sample_count" not in confidence_basis:
            messages.append(_message("confidence_sample_count_missing", "confidence_basis.sample_count is required.", field="confidence_basis.sample_count"))
        if not isinstance(confidence_basis.get("limitations"), list):
            messages.append(_message("confidence_limitations_invalid", "confidence_basis.limitations must be a list.", field="confidence_basis.limitations"))

    target_alignment = contract.get("target_alignment")
    if not isinstance(target_alignment, dict) or target_alignment.get("status") != "aligned":
        messages.append(_message("target_alignment_invalid", "target_alignment.status must be aligned.", field="target_alignment.status"))
    if not isinstance(contract.get("target_a_identity"), dict) or not contract.get("target_a_identity"):
        messages.append(_message("target_a_identity_missing", "target_a_identity is required.", field="target_a_identity"))
    elif not _has_text(contract["target_a_identity"].get("run_id")):
        messages.append(_message("target_a_run_id_missing", "target_a_identity.run_id is required.", field="target_a_identity.run_id"))
    if not isinstance(contract.get("target_b_identity"), dict) or not contract.get("target_b_identity"):
        messages.append(_message("target_b_identity_missing", "target_b_identity is required.", field="target_b_identity"))
    elif not _has_text(contract["target_b_identity"].get("run_id")):
        messages.append(_message("target_b_run_id_missing", "target_b_identity.run_id is required.", field="target_b_identity.run_id"))

    evidence_rows = contract.get("evidence_rows")
    if isinstance(evidence_rows, list):
        if not evidence_rows and not _has_empty_evidence_explanation(contract):
            messages.append(_message("evidence_rows_missing", "evidence_rows or deterministic empty evidence explanation is required.", field="evidence_rows"))
        if _evidence_rows_contain_llm(evidence_rows):
            messages.append(_message("llm_evidence_rejected", "LLM text cannot satisfy deterministic evidence rows.", field="evidence_rows"))

    allowed_visualizations = contract.get("allowed_visualizations")
    if isinstance(allowed_visualizations, list):
        for visualization in allowed_visualizations:
            if visualization in BLOCKED_VISUALIZATIONS:
                messages.append(_message("visualization_not_supported", f"{visualization} is not supported by the 7CX-D adapter.", field="allowed_visualizations"))

    prepared_context = prepared_target_context if isinstance(prepared_target_context, dict) else {}
    if prepared_context:
        target_a = _prepared_target_identity(prepared_context, "A")
        target_b = _prepared_target_identity(prepared_context, "B")
        baseline = str(contract.get("baseline_run_id") or "").strip()
        candidate = str(contract.get("candidate_run_id") or "").strip()
        if target_a and target_a.get("run_id") and baseline != target_a.get("run_id"):
            messages.append(_message("target_a_mismatch", "baseline_run_id does not match prepared Target A.", field="baseline_run_id"))
        if target_b and target_b.get("run_id") and candidate != target_b.get("run_id"):
            messages.append(_message("target_b_mismatch", "candidate_run_id does not match prepared Target B.", field="candidate_run_id"))

    if any(message.severity == "error" for message in messages):
        return _invalid(messages)
    return Screen4ComparisonAdapterResult(
        contract=contract,
        validation_status="valid",
        output_ready=True,
        messages=messages,
        allowed_visualizations=list(contract.get("allowed_visualizations") or []),
    )


def _extract_comparison_artifact(
    source: Any,
) -> tuple[dict[str, Any] | None, list[Screen4ComparisonAdapterMessage]]:
    messages: list[Screen4ComparisonAdapterMessage] = []
    artifact_data: Any = None

    if isinstance(source, ComparisonExecutionResult):
        result = comparison_execution_result_to_dict(source)
        artifact_data = result.get("comparison_artifact")
    elif isinstance(source, AWRReportComparisonArtifact):
        artifact_data = awr_report_comparison_artifact_to_dict(source)
    elif isinstance(source, PersistedWorkflowOutputArtifact):
        artifact_metadata = source.artifact_metadata or {}
        artifact_data = artifact_metadata.get("comparison_artifact")
    elif isinstance(source, dict):
        artifact_data = _artifact_data_from_dict(source)
    else:
        messages.append(_message("source_type_rejected", "Unsupported comparison source type."))

    if not isinstance(artifact_data, dict):
        messages.append(_message("comparison_artifact_missing", "A serialized 7AM/7CC comparison artifact is required."))
        return None, messages

    try:
        artifact = awr_report_comparison_artifact_from_dict(artifact_data)
        return awr_report_comparison_artifact_to_dict(artifact), messages
    except Exception as exc:  # noqa: BLE001
        messages.append(_message("comparison_artifact_invalid", f"Comparison artifact is invalid: {type(exc).__name__}."))
        return None, messages


def _artifact_data_from_dict(source: dict[str, Any]) -> Any:
    if isinstance(source.get("comparison_execution_result"), dict):
        return _artifact_data_from_dict(source["comparison_execution_result"])
    if isinstance(source.get("comparison_artifact"), dict):
        return source.get("comparison_artifact")
    if isinstance(source.get("artifact_metadata"), dict):
        return _artifact_data_from_dict(source["artifact_metadata"])
    if "comparison_id" in source and "score_differences" in source:
        return source
    return None


def _workflow_metadata_from_source(source: Any) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if isinstance(source, ComparisonExecutionResult):
        result = comparison_execution_result_to_dict(source)
        metadata.update(
            {
                "comparison_execution_id": result.get("comparison_execution_id"),
                "request_id": result.get("request_id"),
                "idempotency_key": result.get("idempotency_key"),
                "transaction_group_id": result.get("transaction_group_id"),
                "workflow_transaction_id": result.get("transaction_group_id"),
                "artifact_source": "phase7cc_comparison_execution",
            }
        )
        refs = result.get("output_references") or []
        if refs:
            first_ref = refs[0]
            if isinstance(first_ref, dict):
                metadata.update(first_ref)
                metadata["input_artifact_ids"] = [
                    ref.get("output_reference_id")
                    for ref in refs
                    if isinstance(ref, dict) and _has_text(ref.get("output_reference_id"))
                ]
    elif isinstance(source, ComparisonOutputReference):
        metadata.update(comparison_output_reference_to_dict(source))
    elif isinstance(source, PersistedWorkflowOutputArtifact):
        metadata.update(
            {
                "workflow_output_id": source.workflow_output_id,
                "workflow_request_id": source.workflow_request_id,
                "artifact_type": source.artifact_type,
                "artifact_reference": source.artifact_reference,
                "created_at": source.created_at,
                "artifact_source": "phase7cc_comparison_execution",
                "input_artifact_ids": [source.workflow_output_id],
            }
        )
    elif isinstance(source, dict):
        for key in (
            "comparison_execution_id",
            "request_id",
            "workflow_request_id",
            "workflow_transaction_id",
            "transaction_group_id",
            "artifact_reference",
            "artifact_source",
            "workflow_output_id",
            "created_at",
            "generated_at",
            "actor_id",
            "source_mode",
            "source_scope",
            "comparison_scope",
            "input_artifact_ids",
        ):
            if key in source:
                metadata[key] = source[key]
        if isinstance(source.get("comparison_execution_result"), dict):
            metadata.update(_workflow_metadata_from_source(source["comparison_execution_result"]))
        if isinstance(source.get("artifact_metadata"), dict):
            nested = source["artifact_metadata"]
            for key in ("comparison_execution_id", "request_id", "transaction_group_id"):
                if key in nested and key not in metadata:
                    metadata[key] = nested[key]
    return metadata


def _prepared_target_identity(
    prepared_context: dict[str, Any],
    suffix: str,
) -> dict[str, Any]:
    candidates = (
        prepared_context.get(f"target_{suffix.lower()}_identity"),
        prepared_context.get(f"target_{suffix.lower()}"),
        prepared_context.get(f"target{suffix}Identity"),
        prepared_context.get(f"target{suffix}"),
    )
    for candidate in candidates:
        if isinstance(candidate, dict):
            identity = {
                key: _json_safe(candidate.get(key))
                for key in IDENTITY_KEYS
                if _field_present(candidate.get(key))
            }
            if "db_name" not in identity and _has_text(candidate.get("database_name")):
                identity["db_name"] = str(candidate["database_name"]).strip()
            if "window" not in identity and _has_text(candidate.get("time_window")):
                identity["window"] = str(candidate["time_window"]).strip()
            if identity:
                return identity
    return {}


def _target_alignment_messages(
    artifact: dict[str, Any],
    target_a: dict[str, Any],
    target_b: dict[str, Any],
    baseline_run_id: str | None,
    candidate_run_id: str | None,
) -> list[Screen4ComparisonAdapterMessage]:
    messages: list[Screen4ComparisonAdapterMessage] = []
    if target_a and target_a.get("run_id") and baseline_run_id != target_a.get("run_id"):
        messages.append(_message("target_a_mismatch", "Comparison artifact baseline does not match prepared Target A.", field="target_a_identity.run_id"))
    if target_b and target_b.get("run_id") and candidate_run_id != target_b.get("run_id"):
        messages.append(_message("target_b_mismatch", "Comparison artifact candidate does not match prepared Target B.", field="target_b_identity.run_id"))
    awr_ids = list(artifact.get("compared_awr_ids") or [])
    if target_a and target_a.get("awr_id") and awr_ids and target_a.get("awr_id") != awr_ids[0]:
        messages.append(_message("target_a_awr_mismatch", "Comparison artifact AWR id does not match prepared Target A.", field="target_a_identity.awr_id"))
    if target_b and target_b.get("awr_id") and len(awr_ids) > 1 and target_b.get("awr_id") != awr_ids[1]:
        messages.append(_message("target_b_awr_mismatch", "Comparison artifact AWR id does not match prepared Target B.", field="target_b_identity.awr_id"))
    return messages


def _resolve_baseline_run_id(artifact: dict[str, Any]) -> str | None:
    run_ids = list(artifact.get("compared_run_ids") or [])
    return _first_text(run_ids[0] if run_ids else None, artifact.get("baseline_reference"))


def _resolve_candidate_run_id(artifact: dict[str, Any]) -> str | None:
    run_ids = list(artifact.get("compared_run_ids") or [])
    target_references = list(artifact.get("target_references") or [])
    return _first_text(
        run_ids[1] if len(run_ids) > 1 else None,
        target_references[0] if target_references else None,
    )


def _resolve_source_scope(
    explicit: str | None,
    workflow: dict[str, Any],
    prepared_context: dict[str, Any],
) -> str:
    source_scope = _first_text(
        explicit,
        workflow.get("source_scope"),
        prepared_context.get("source_scope"),
    )
    if source_scope:
        return source_scope
    source_mode = _first_text(workflow.get("source_mode"), prepared_context.get("source_mode"))
    if source_mode in {"existing_run", "db_backed", "same_db_historical"}:
        return "same_db_historical"
    if source_mode in {"fleet", "population"}:
        return source_mode
    return "same_db_historical"


def _resolve_comparison_scope(
    explicit: str | None,
    workflow: dict[str, Any],
    prepared_context: dict[str, Any],
) -> str:
    return _first_text(
        explicit,
        workflow.get("comparison_scope"),
        prepared_context.get("comparison_scope"),
        "target_a_vs_target_b",
    ) or ""


def _scope_mismatch_messages(
    field: str,
    *values: Any,
) -> list[Screen4ComparisonAdapterMessage]:
    present = [str(value).strip() for value in values if _has_text(value)]
    if len(set(present)) > 1:
        return [
            _message(
                f"{field}_mismatch",
                f"{field} values from trusted workflow metadata and prepared context do not align.",
                field=field,
            )
        ]
    return []


def _build_metric_and_evidence_rows(
    artifact: dict[str, Any],
    baseline_run_id: str,
    candidate_run_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    metric_deltas: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    sections = (
        ("score", "score_differences"),
        ("wait_event", "wait_event_differences"),
        ("sql_concentration", "sql_concentration_differences"),
        ("trend", "trend_differences"),
        ("anomaly", "anomaly_differences"),
        ("topology", "topology_differences"),
        ("platform_target", "platform_target_differences"),
        ("data_availability", "data_availability_differences.supplied_data_availability"),
    )
    for category, field_name in sections:
        section = _nested_get(artifact, field_name)
        if not isinstance(section, dict):
            continue
        for metric_name, payload in sorted(section.items()):
            rows = _rows_from_difference_payload(
                category,
                field_name,
                metric_name,
                payload,
                baseline_run_id,
                candidate_run_id,
            )
            evidence_rows.extend(rows)
            if category in {"score", "wait_event", "sql_concentration"}:
                metric_deltas.extend(rows)
    return metric_deltas, evidence_rows


def _rows_from_difference_payload(
    category: str,
    source_field: str,
    metric_name: str,
    payload: Any,
    baseline_run_id: str,
    candidate_run_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    targets = payload.get("targets")
    if not isinstance(targets, list):
        return []
    rows = []
    for target in targets:
        if not isinstance(target, dict):
            continue
        row = {
            "category": category,
            "metric": metric_name,
            "baseline_run_id": baseline_run_id,
            "candidate_run_id": candidate_run_id,
            "candidate_reference": _first_text(target.get("reference"), candidate_run_id),
            "baseline_value": _json_safe(target.get("baseline")),
            "candidate_value": _json_safe(target.get("value")),
            "evidence_source": source_field,
        }
        if "difference" in target:
            row["delta"] = _json_safe(target.get("difference"))
        if "changed" in target:
            row["changed"] = bool(target.get("changed"))
        rows.append(row)
    return rows


def _build_domain_deltas(metric_deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domains: dict[str, dict[str, Any]] = {}
    for row in metric_deltas:
        domain = _domain_from_metric(str(row.get("metric") or ""))
        if not domain:
            continue
        item = domains.setdefault(
            domain,
            {
                "domain": domain,
                "metric_count": 0,
                "metrics": [],
                "evidence_source": "metric_deltas",
            },
        )
        item["metric_count"] += 1
        item["metrics"].append(row.get("metric"))
    return list(domains.values())


def _domain_from_metric(metric_name: str) -> str | None:
    upper = metric_name.upper()
    for domain in ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG"):
        if f".{domain.lower()}" in metric_name.lower() or upper.endswith(domain):
            return domain
    if "IO" in upper or "I/O" in upper:
        return "IO"
    return None


def _build_missing_evidence(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    data_availability = artifact.get("data_availability_differences")
    if isinstance(data_availability, dict):
        for item in data_availability.get("missing_values") or []:
            if isinstance(item, dict):
                missing.append(
                    {
                        "type": "missing_field",
                        "reference": _first_text(item.get("reference"), "unknown"),
                        "field": _first_text(item.get("field"), "unknown"),
                    }
                )
    for limitation in artifact.get("comparison_limitations") or []:
        if _has_text(limitation):
            missing.append(
                {
                    "type": "limitation",
                    "message": str(limitation).strip(),
                }
            )
    return missing


def _allowed_visualizations(
    metric_deltas: list[dict[str, Any]],
    domain_deltas: list[dict[str, Any]],
    missing_evidence: list[dict[str, Any]],
    confidence_basis: dict[str, Any],
) -> list[str]:
    allowed = []
    if metric_deltas:
        allowed.append("metric_delta_table")
    if domain_deltas:
        allowed.append("domain_delta_summary")
    if confidence_basis.get("basis_type") == "deterministic_evidence":
        allowed.append("confidence_basis_panel")
    if missing_evidence:
        allowed.append("missing_evidence_panel")
    return [item for item in allowed if item in CONSERVATIVE_VISUALIZATIONS]


def _input_artifact_ids(workflow: dict[str, Any]) -> list[str]:
    values = workflow.get("input_artifact_ids")
    if isinstance(values, list):
        return [str(item) for item in values if _has_text(item)]
    value = _first_text(workflow.get("workflow_output_id"), workflow.get("output_reference_id"))
    return [value] if value else []


def _input_snapshot_range(
    target_a: dict[str, Any],
    target_b: dict[str, Any],
) -> dict[str, Any]:
    return {
        "target_a_snapshot": _first_text(target_a.get("snapshot"), target_a.get("snapshot_label")),
        "target_b_snapshot": _first_text(target_b.get("snapshot"), target_b.get("snapshot_label")),
        "target_a_window": _first_text(target_a.get("window"), target_a.get("time_window")),
        "target_b_window": _first_text(target_b.get("window"), target_b.get("time_window")),
    }


def _generated_from_hash(
    artifact: dict[str, Any],
    target_a: dict[str, Any],
    target_b: dict[str, Any],
    workflow: dict[str, Any],
) -> str:
    payload = {
        "artifact": artifact,
        "target_a": target_a,
        "target_b": target_b,
        "workflow": workflow,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _nested_get(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _has_empty_evidence_explanation(contract: dict[str, Any]) -> bool:
    no_change = contract.get("no_change_evidence")
    if isinstance(no_change, dict):
        return no_change.get("basis_type") == "deterministic_evidence" and _has_text(
            no_change.get("explanation")
        )
    return _has_text(contract.get("empty_evidence_explanation"))


def _evidence_rows_contain_llm(evidence_rows: list[Any]) -> bool:
    for row in evidence_rows:
        if not isinstance(row, dict):
            continue
        if "llm_explanation" in row:
            return True
        for key in ("source", "evidence_source", "generated_by"):
            value = str(row.get(key) or "").strip().lower()
            if value in {"llm", "llm_explanation", "browser_llm"}:
                return True
    return False


def _field_present(value: Any) -> bool:
    if isinstance(value, (dict, list, tuple, set)):
        return value is not None
    return _has_text(value)


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _first_text(*values: Any) -> str | None:
    for value in values:
        if _has_text(value):
            return str(value).strip()
    return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


def _message(
    code: str,
    text: str,
    *,
    field: str | None = None,
    severity: str = "error",
) -> Screen4ComparisonAdapterMessage:
    return Screen4ComparisonAdapterMessage(
        code=code,
        message=text,
        field=field,
        severity=severity,
    )


def _invalid(
    messages: list[Screen4ComparisonAdapterMessage],
) -> Screen4ComparisonAdapterResult:
    return Screen4ComparisonAdapterResult(
        contract=None,
        validation_status="invalid",
        output_ready=False,
        messages=messages,
        allowed_visualizations=[],
    )


def _require_text(value: Any, field_name: str) -> str:
    if not _has_text(value):
        raise ValueError(f"{field_name} is required.")
    return str(value).strip()


__all__ = [
    "DETERMINISTIC_COMPARISON_ENGINE_VERSION",
    "SCREEN4_COMPARISON_ADAPTER_VERSION",
    "SCREEN4_COMPARISON_CONTRACT_TYPE",
    "SCREEN4_COMPARISON_CONTRACT_VERSION",
    "Screen4ComparisonAdapterMessage",
    "Screen4ComparisonAdapterResult",
    "adapt_screen4_deterministic_comparison_output",
    "validate_screen4_comparison_contract",
]
