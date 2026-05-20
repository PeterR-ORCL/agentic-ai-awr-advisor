"""Phase 7CM governed dashboard runtime interaction bridge.

The bridge validates dashboard workflow requests and records audit-safe request
files for local/demo handling. It does not mutate diagnostic truth, Phase 4I,
recommendation truth, parser output, scoring, or adaptive runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


DASHBOARD_RUNTIME_ACTION_STATUSES = (
    "accepted",
    "rejected",
)

DASHBOARD_RUNTIME_SCREEN_IDS = (
    "index_source_mode",
    "screen_1",
    "screen_2",
    "screen_3",
    "screen_4",
    "screen_5",
    "screen_6",
)

DASHBOARD_RUNTIME_ACTION_TYPES = (
    "source_selection_handoff",
    "parser_unknown_review",
    "parser_unknown_approve",
    "parser_unknown_reject",
    "parser_unknown_classify",
    "parser_unknown_route",
    "knowledge_artifact_review",
    "knowledge_artifact_approve",
    "knowledge_artifact_reject",
    "parser_mapping_approval_intent",
    "diagnostic_review",
    "screen3_active_reanalysis",
    "historical_review",
    "recommendation_decision",
    "action_assignment_tracking",
    "status_update",
    "outcome_capture",
    "feedback_learning_intent",
    "candidate_review",
    "materialization_review",
    "materialization_request",
    "model_registry_review",
    "runtime_gate_review",
    "runtime_eligibility_request",
)

SCREEN_REQUIRED_ACTION_TYPES: dict[str, tuple[str, ...]] = {
    "index_source_mode": ("source_selection_handoff",),
    "screen_1": (
        "parser_unknown_review",
        "parser_unknown_approve",
        "parser_unknown_reject",
        "parser_unknown_classify",
        "parser_unknown_route",
        "knowledge_artifact_review",
        "knowledge_artifact_approve",
        "knowledge_artifact_reject",
        "parser_mapping_approval_intent",
    ),
    "screen_2": ("diagnostic_review",),
    "screen_3": ("screen3_active_reanalysis",),
    "screen_4": ("historical_review",),
    "screen_5": (
        "recommendation_decision",
        "action_assignment_tracking",
        "status_update",
        "outcome_capture",
        "feedback_learning_intent",
    ),
    "screen_6": (
        "candidate_review",
        "materialization_review",
        "materialization_request",
        "model_registry_review",
        "runtime_gate_review",
        "runtime_eligibility_request",
    ),
}

_TOKEN_RE = re.compile(r"[^A-Za-z0-9_.:-]+")
INDEX_SOURCE_MODES = ("local_staged", "local_file", "existing_run", "object_storage")


class DashboardRuntimeInteractionError(ValueError):
    """Raised when a dashboard action request violates Phase 7CM rules."""


@dataclass(frozen=True)
class DashboardRuntimeActionRequest:
    """Governed dashboard action request submitted by the static UI bridge."""

    request_id: str
    screen_id: str
    action_type: str
    workflow_type: str
    actor_id: str
    requested_at: str
    target_type: str
    target_id: str
    idempotency_key: str
    payload: dict[str, Any] = field(default_factory=dict)
    governance_mode: str = "governed_request"
    execution_mode: str = "request_record_only"
    runtime_influence_granted: bool = False
    phase4i_mutation_allowed: bool = False
    phase8_behavior: bool = False
    direct_truth_mutation_allowed: bool = False
    run_analysis_coupling: bool = False
    future_run_influence_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_token(self.request_id, "request_id")
        _require_supported(self.screen_id, DASHBOARD_RUNTIME_SCREEN_IDS, "screen_id")
        _require_supported(self.action_type, DASHBOARD_RUNTIME_ACTION_TYPES, "action_type")
        _require_text(self.workflow_type, "workflow_type")
        _require_text(self.actor_id, "actor_id")
        _require_text(self.requested_at, "requested_at")
        _require_text(self.target_type, "target_type")
        _require_text(self.target_id, "target_id")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_mapping(self.payload, "payload")
        _require_text(self.governance_mode, "governance_mode")
        _require_text(self.execution_mode, "execution_mode")
        _reject_true(self.runtime_influence_granted, "runtime_influence_granted")
        _reject_true(self.phase4i_mutation_allowed, "phase4i_mutation_allowed")
        _reject_true(self.phase8_behavior, "phase8_behavior")
        _reject_true(
            self.direct_truth_mutation_allowed,
            "direct_truth_mutation_allowed",
        )
        _reject_true(self.run_analysis_coupling, "run_analysis_coupling")
        _require_mapping(
            self.future_run_influence_metadata,
            "future_run_influence_metadata",
        )
        _validate_future_run_influence_metadata(self.future_run_influence_metadata)
        if self.action_type not in SCREEN_REQUIRED_ACTION_TYPES[self.screen_id]:
            raise DashboardRuntimeInteractionError(
                f"action_type {self.action_type!r} is not allowed for {self.screen_id!r}"
            )
        if self.screen_id == "index_source_mode" and self.action_type == "source_selection_handoff":
            _validate_index_source_selection_payload(self.payload)
        if self.screen_id == "screen_1":
            _validate_screen1_parser_governance_payload(self)
        if self.screen_id == "screen_2":
            _validate_screen2_diagnostic_review_payload(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "screen_id": self.screen_id,
            "action_type": self.action_type,
            "workflow_type": self.workflow_type,
            "actor_id": self.actor_id,
            "requested_at": self.requested_at,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "idempotency_key": self.idempotency_key,
            "payload": dict(self.payload),
            "governance_mode": self.governance_mode,
            "execution_mode": self.execution_mode,
            "runtime_influence_granted": self.runtime_influence_granted,
            "phase4i_mutation_allowed": self.phase4i_mutation_allowed,
            "phase8_behavior": self.phase8_behavior,
            "direct_truth_mutation_allowed": self.direct_truth_mutation_allowed,
            "run_analysis_coupling": self.run_analysis_coupling,
            "future_run_influence_metadata": dict(self.future_run_influence_metadata),
        }


@dataclass(frozen=True)
class DashboardRuntimeActionResult:
    """Result returned by the governed dashboard action bridge."""

    status: str
    request_id: str
    audit_reference: str | None
    message: str
    persisted: bool
    queued: bool
    runtime_influence_granted: bool = False
    phase4i_mutated: bool = False
    phase8_behavior: bool = False
    direct_truth_mutation_performed: bool = False
    run_analysis_called: bool = False
    source_summary: dict[str, Any] = field(default_factory=dict)
    db_persistence_status: str = "not_attempted"
    db_persistence_mode: str = "json_audit_file"
    db_record_reference: str | None = None
    db_tables_touched: tuple[str, ...] = ()
    db_persistence_message: str | None = None
    screen6_candidate_created: bool = False
    errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_supported(self.status, DASHBOARD_RUNTIME_ACTION_STATUSES, "status")
        _require_text(self.request_id, "request_id")
        _require_optional_text(self.audit_reference, "audit_reference")
        _require_text(self.message, "message")
        _reject_true(self.runtime_influence_granted, "runtime_influence_granted")
        _reject_true(self.phase4i_mutated, "phase4i_mutated")
        _reject_true(self.phase8_behavior, "phase8_behavior")
        _reject_true(
            self.direct_truth_mutation_performed,
            "direct_truth_mutation_performed",
        )
        _reject_true(self.run_analysis_called, "run_analysis_called")
        _require_mapping(self.source_summary, "source_summary")
        _require_text(self.db_persistence_status, "db_persistence_status")
        _require_text(self.db_persistence_mode, "db_persistence_mode")
        _require_optional_text(self.db_record_reference, "db_record_reference")
        _require_string_tuple(self.db_tables_touched, "db_tables_touched")
        _require_optional_text(self.db_persistence_message, "db_persistence_message")
        _reject_true(self.screen6_candidate_created, "screen6_candidate_created")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "request_id": self.request_id,
            "audit_reference": self.audit_reference,
            "message": self.message,
            "persisted": self.persisted,
            "queued": self.queued,
            "runtime_influence_granted": self.runtime_influence_granted,
            "phase4i_mutated": self.phase4i_mutated,
            "phase8_behavior": self.phase8_behavior,
            "direct_truth_mutation_performed": self.direct_truth_mutation_performed,
            "run_analysis_called": self.run_analysis_called,
            "source_summary": dict(self.source_summary),
            "db_persistence_status": self.db_persistence_status,
            "db_persistence_mode": self.db_persistence_mode,
            "db_record_reference": self.db_record_reference,
            "db_tables_touched": list(self.db_tables_touched),
            "db_persistence_message": self.db_persistence_message,
            "screen6_candidate_created": self.screen6_candidate_created,
            "errors": list(self.errors),
        }


def request_from_payload(payload: dict[str, Any]) -> DashboardRuntimeActionRequest:
    """Build and validate a governed dashboard action request from JSON."""

    _require_mapping(payload, "payload")
    requested_at = str(payload.get("requested_at") or _utc_now())
    request_id = str(
        payload.get("request_id")
        or build_request_id(
            payload.get("screen_id"),
            payload.get("action_type"),
            payload.get("target_id"),
            requested_at,
        )
    )
    idempotency_key = str(
        payload.get("idempotency_key")
        or build_idempotency_key(
            payload.get("screen_id"),
            payload.get("action_type"),
            payload.get("target_id"),
            payload.get("payload") or {},
        )
    )
    return DashboardRuntimeActionRequest(
        request_id=request_id,
        screen_id=str(payload.get("screen_id") or ""),
        action_type=str(payload.get("action_type") or ""),
        workflow_type=str(payload.get("workflow_type") or ""),
        actor_id=str(payload.get("actor_id") or "ACTOR-LOCAL-DASHBOARD-REVIEWER"),
        requested_at=requested_at,
        target_type=str(payload.get("target_type") or "dashboard_control"),
        target_id=str(payload.get("target_id") or "dashboard-target"),
        idempotency_key=idempotency_key,
        payload=dict(payload.get("payload") or {}),
        governance_mode=str(payload.get("governance_mode") or "governed_request"),
        execution_mode=str(payload.get("execution_mode") or "request_record_only"),
        runtime_influence_granted=bool(payload.get("runtime_influence_granted", False)),
        phase4i_mutation_allowed=bool(payload.get("phase4i_mutation_allowed", False)),
        phase8_behavior=bool(payload.get("phase8_behavior", False)),
        direct_truth_mutation_allowed=bool(
            payload.get("direct_truth_mutation_allowed", False)
        ),
        run_analysis_coupling=bool(payload.get("run_analysis_coupling", False)),
        future_run_influence_metadata=dict(
            payload.get("future_run_influence_metadata") or {}
        ),
    )


def process_dashboard_action(
    payload: dict[str, Any],
    *,
    queue_dir: Path | None = None,
    connection_factory: Any | None = None,
    db_persistence_enabled: bool = False,
) -> DashboardRuntimeActionResult:
    """Validate and queue a governed dashboard action request."""

    try:
        request = request_from_payload(payload)
    except (DashboardRuntimeInteractionError, TypeError) as exc:
        request_id = str(payload.get("request_id") or "invalid-request")
        return DashboardRuntimeActionResult(
            status="rejected",
            request_id=request_id,
            audit_reference=None,
            message=f"Dashboard action request rejected by governed validation: {exc}",
            persisted=False,
            queued=False,
            errors=(str(exc),),
        )
    target_dir = queue_dir or default_action_queue_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    audit_reference = target_dir / f"{_safe_filename(request.request_id)}.json"
    envelope = {
        "phase": "Phase 7",
        "subphase": "7CM",
        "record_type": "governed_dashboard_action_request",
        "request": request.to_dict(),
        "audit": {
            "recorded_at": _utc_now(),
            "status": "queued_for_governed_phase7_handling",
            "screen3_uses_governed_execution_path": (
                request.action_type == "screen3_active_reanalysis"
            ),
            "runtime_influence_granted": False,
            "phase4i_mutated": False,
            "phase8_behavior": False,
            "run_analysis_called": False,
            "direct_truth_mutation_performed": False,
            "future_run_influence_metadata": request.future_run_influence_metadata,
            "future_run_influence_active": False,
            "future_run_influence_requires_materialization": True,
            "future_run_influence_requires_runtime_eligibility": True,
        },
    }
    audit_reference.write_text(
        json.dumps(envelope, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    db_persistence = _persist_screen1_parser_governance_review(
        request,
        audit_reference,
        connection_factory=connection_factory,
        db_persistence_enabled=db_persistence_enabled,
    )
    envelope["persistence"] = db_persistence
    audit_reference.write_text(
        json.dumps(envelope, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source_summary = _source_summary_for_request(request)
    if request.screen_id == "screen_1":
        source_summary.update(
            {
                "persistence_mode": db_persistence["mode"],
                "db_persistence_status": db_persistence["status"],
                "db_record_reference": db_persistence.get("record_reference"),
                "db_tables_touched": list(db_persistence.get("tables_touched") or ()),
                "db_persistence_message": db_persistence.get("message"),
                "json_audit_reference": str(audit_reference),
                "screen6_candidate_created": False,
                "runtime_influence": (
                    "Not applied to current run; pending separate "
                    "materialization/runtime-eligibility approval."
                ),
                "screen6_learning_governance_status": (
                    "Not activated by this submit. Eligible for downstream review "
                    "only from persisted governance context."
                ),
            }
        )
    message = "Governed dashboard action request queued for workflow handling."
    if request.screen_id == "screen_1":
        if db_persistence["status"] == "persisted":
            message = (
                "Accepted / queued for parser governance review. DB-backed "
                "parser governance record persisted; JSON audit envelope recorded."
            )
        elif db_persistence["status"] in {"unavailable", "failed"}:
            message = (
                "Accepted / queued for parser governance review. JSON audit fallback "
                "recorded because DB persistence was unavailable."
            )
    return DashboardRuntimeActionResult(
        status="accepted",
        request_id=request.request_id,
        audit_reference=str(audit_reference),
        message=message,
        persisted=True,
        queued=True,
        source_summary=source_summary,
        db_persistence_status=str(db_persistence["status"]),
        db_persistence_mode=str(db_persistence["mode"]),
        db_record_reference=db_persistence.get("record_reference"),
        db_tables_touched=tuple(str(item) for item in db_persistence.get("tables_touched") or ()),
        db_persistence_message=db_persistence.get("message"),
        screen6_candidate_created=False,
    )


def _persist_screen1_parser_governance_review(
    request: DashboardRuntimeActionRequest,
    audit_reference: Path,
    *,
    connection_factory: Any | None,
    db_persistence_enabled: bool,
) -> dict[str, Any]:
    """Persist Screen 1 parser governance review metadata when DB is available."""

    if request.screen_id != "screen_1":
        return {
            "status": "not_attempted",
            "mode": "json_audit_file",
            "record_reference": None,
            "tables_touched": [],
            "message": "DB persistence is not part of this dashboard action.",
            "screen6_candidate_created": False,
        }
    if not db_persistence_enabled:
        return {
            "status": "not_attempted",
            "mode": "json_audit_file",
            "record_reference": None,
            "tables_touched": [],
            "message": "JSON audit record queued; DB persistence was not requested by this service path.",
            "screen6_candidate_created": False,
        }

    connection = None
    try:
        if connection_factory is not None:
            connection = connection_factory()
        else:
            from src.ingest.awr_adb_loader import get_db_connection

            connection = get_db_connection()

        from src.learning.governed_workflow_repository import (
            GovernedWorkflowRepository,
            PersistedWorkflowOutputArtifact,
            PersistedWorkflowRequest,
            PersistedWorkflowTransaction,
            PersistedWorkflowValidation,
            create_transaction_group_id,
            create_workflow_audit_id,
            create_workflow_output_id,
            create_workflow_request_id,
            create_workflow_validation_id,
            hash_payload,
            PersistedWorkflowAudit,
        )

        repository = GovernedWorkflowRepository(connection)
        workflow_request_id = create_workflow_request_id(
            request.workflow_type,
            request.idempotency_key,
        )
        transaction_group_id = create_transaction_group_id(
            request.idempotency_key,
            "screen1_parser_governance_review",
        )
        rollback_reference = f"json-audit:{audit_reference.name}"
        persisted_payload = {
            "dashboard_request": request.to_dict(),
            "json_audit_reference": str(audit_reference),
            "rollback_reference": rollback_reference,
            "screen1_parser_governance_review": True,
            "database_persistence_performed": True,
            "screen6_candidate_created": False,
            "runtime_influence_granted": False,
            "future_run_influence_active": False,
            "requires_screen6_learning_governance": True,
            "requires_materialization_approval": True,
            "requires_runtime_eligibility_approval": True,
        }
        workflow_request = PersistedWorkflowRequest(
            workflow_request_id=workflow_request_id,
            transaction_group_id=transaction_group_id,
            idempotency_key=request.idempotency_key,
            source_screen=request.screen_id,
            workflow_type=request.workflow_type,
            requested_action=request.action_type,
            target_type=request.target_type,
            target_id=request.target_id,
            actor_id=request.actor_id,
            payload=persisted_payload,
            status="VALIDATED",
            notes=(
                "Screen 1 parser governance review persisted as governed workflow "
                "metadata only; no parser/runtime/ML/materialization mutation."
            ),
        )
        transaction = PersistedWorkflowTransaction(
            transaction_group_id=transaction_group_id,
            idempotency_key=request.idempotency_key,
            transaction_scope="screen1_parser_governance_review",
            rollback_reference=rollback_reference,
            status="IN_PROGRESS",
            notes="Non-mutating Screen 1 parser governance persistence.",
        )
        validation = PersistedWorkflowValidation(
            workflow_validation_id=create_workflow_validation_id(workflow_request_id),
            workflow_request_id=workflow_request_id,
            validation_status="screen1_parser_governance_valid_non_mutating",
            valid_flag=True,
            warnings=[
                "current parser output is unchanged",
                "future-run influence requires Screen 6 materialization/runtime eligibility",
            ],
            required_next_steps=[
                "review persisted parser-governance context",
                "route to Screen 6 learning/materialization governance only if implementation is accepted",
            ],
            notes="Screen 1 submit records governance context only.",
        )
        audit = PersistedWorkflowAudit(
            workflow_audit_id=create_workflow_audit_id(
                workflow_request_id,
                "screen1_parser_governance_review_persisted",
            ),
            workflow_request_id=workflow_request_id,
            transaction_group_id=transaction_group_id,
            actor_id=request.actor_id,
            action="screen1_parser_governance_review_persisted",
            audit_summary=(
                "Screen 1 parser governance review persisted; current parser output, "
                "diagnosis, scoring, recommendation, runtime, ML, materialization, "
                "runtime eligibility, and future-run behavior were not changed."
            ),
            payload_hash=hash_payload(persisted_payload),
            notes="DB-backed governance record plus JSON audit envelope.",
        )
        artifact = PersistedWorkflowOutputArtifact(
            workflow_output_id=create_workflow_output_id(
                workflow_request_id,
                "workflow_audit_artifact",
                str(audit_reference),
            ),
            workflow_request_id=workflow_request_id,
            artifact_type="workflow_audit_artifact",
            artifact_reference=str(audit_reference),
            artifact_summary="Screen 1 parser governance JSON audit envelope.",
            artifact_metadata={
                "json_audit_reference": str(audit_reference),
                "runtime_mutation": False,
                "screen6_candidate_created": False,
            },
            status="RECORDED",
            notes="Audit envelope only; not parser runtime state.",
        )
        result = repository.persist_workflow_bundle(
            request=workflow_request,
            transaction=transaction,
            validation=validation,
            audit=audit,
            output_artifacts=(artifact,),
        )
        return {
            "status": "persisted",
            "mode": "db_backed_workflow_record_and_json_audit",
            "record_reference": f"AWR_WORKFLOW_REQUEST:{result.workflow_request_id}",
            "workflow_request_id": result.workflow_request_id,
            "workflow_audit_id": audit.workflow_audit_id,
            "transaction_group_id": result.transaction_group_id,
            "tables_touched": [
                "AWR_WORKFLOW_TRANSACTION",
                "AWR_WORKFLOW_REQUEST",
                "AWR_WORKFLOW_VALIDATION",
                "AWR_WORKFLOW_AUDIT",
                "AWR_WORKFLOW_OUTPUT_ARTIFACT",
            ],
            "message": (
                "DB-backed parser governance record persisted; JSON audit envelope recorded. "
                "No Screen 6 candidate or runtime eligibility record was created."
            ),
            "duplicate": result.duplicate,
            "screen6_candidate_created": False,
        }
    except Exception as exc:  # noqa: BLE001 - fallback must stay non-disruptive
        return {
            "status": "unavailable",
            "mode": "json_audit_fallback_only",
            "record_reference": None,
            "tables_touched": [],
            "message": (
                "JSON audit fallback only - DB persistence unavailable. "
                f"{type(exc).__name__}: {exc}"
            ),
            "screen6_candidate_created": False,
        }
    finally:
        if connection is not None:
            close = getattr(connection, "close", None)
            if callable(close):
                close()


def lookup_existing_runs(
    payload: dict[str, Any],
    *,
    queue_dir: Path | None = None,
    connection_factory: Any | None = None,
) -> dict[str, Any]:
    """Query available existing runs through the governed service boundary."""

    try:
        _validate_source_service_request(payload, "existing_run_lookup")
    except DashboardRuntimeInteractionError as exc:
        return _source_service_rejection("existing-run-lookup", str(exc))

    managed_connection = True
    connection = None
    try:
        if connection_factory is not None:
            connection = connection_factory()
        else:
            from src.ingest.awr_adb_loader import get_db_connection

            connection = get_db_connection()
        limit = _normalize_limit(payload.get("limit"), default=10, maximum=50)
        runs = _query_existing_runs(connection, limit=limit)
    except Exception as exc:  # noqa: BLE001 - service reports unavailable without mutation
        return {
            "status": "pending",
            "validation_status": "unavailable",
            "request_id": build_request_id(
                "index_source_mode",
                "existing_run_lookup",
                "existing-run-lookup",
                _utc_now(),
            ),
            "audit_reference": None,
            "message": (
                "Existing run lookup unavailable. Governed workflow service is not connected to DB "
                "or returned no runs. "
                f"Lookup unavailable: {type(exc).__name__}: {exc}"
            ),
            "runs": [],
            "run_count": 0,
            "persisted": False,
            "queued": False,
            "browser_db_query_performed": False,
            "phase4i_mutated": False,
            "phase8_behavior": False,
        }
    finally:
        if managed_connection and connection is not None:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

    request_id = build_request_id(
        "index_source_mode",
        "existing_run_lookup",
        "existing-run-lookup",
        _utc_now(),
    )
    audit_reference = _write_source_service_audit(
        queue_dir=queue_dir,
        request_id=request_id,
        record_type="existing_run_lookup",
        payload=payload,
        result={"run_count": len(runs), "runs": runs[:10]},
    )
    return {
        "status": "accepted",
        "validation_status": "valid" if runs else "empty",
        "request_id": request_id,
        "audit_reference": str(audit_reference),
        "message": (
            f"Existing run lookup returned {len(runs)} selectable run option(s)."
            if runs
            else "No prior runs found in governed persistence."
        ),
        "runs": runs,
        "run_count": len(runs),
        "persisted": True,
        "queued": True,
        "browser_db_query_performed": False,
        "phase4i_mutated": False,
        "phase8_behavior": False,
    }


def validate_object_storage_source(
    payload: dict[str, Any],
    *,
    queue_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate Object Storage source metadata through the governed service."""

    try:
        _validate_source_service_request(payload, "object_storage_source_validation")
        for field_name in (
            "objectStorageNamespace",
            "objectStorageBucket",
            "objectStorageObjectName",
            "objectStorageRegion",
        ):
            _require_text(payload.get(field_name), f"payload.{field_name}")
        _reject_source_secret_fields(payload)
    except DashboardRuntimeInteractionError as exc:
        return _source_service_rejection("object-storage-validation", str(exc))

    request_id = build_request_id(
        "index_source_mode",
        "object_storage_source_validation",
        payload.get("objectStorageObjectName"),
        _utc_now(),
    )
    summary = {
        "objectStorageNamespace": payload.get("objectStorageNamespace"),
        "objectStorageBucket": payload.get("objectStorageBucket"),
        "objectStorageObjectName": payload.get("objectStorageObjectName"),
        "objectStorageRegion": payload.get("objectStorageRegion"),
        "object_availability": "metadata_valid_live_check_not_configured",
        "browser_object_storage_access_performed": False,
    }
    audit_reference = _write_source_service_audit(
        queue_dir=queue_dir,
        request_id=request_id,
        record_type="object_storage_source_validation",
        payload=payload,
        result=summary,
    )
    return {
        "status": "accepted",
        "validation_status": "valid",
        "request_id": request_id,
        "audit_reference": str(audit_reference),
        "message": (
            "Object Storage metadata accepted by governed backend validation. "
            "Object availability is checked by service configuration when live validation is enabled; "
            "no browser-side OCI access was performed."
        ),
        "source_summary": summary,
        "persisted": True,
        "queued": True,
        "browser_object_storage_access_performed": False,
        "phase4i_mutated": False,
        "phase8_behavior": False,
    }


SCREEN1_PARSER_GOVERNANCE_TARGETS: dict[str, tuple[str, ...]] = {
    "parser_unknown_review": ("parser_unknown_signal",),
    "parser_unknown_approve": ("parser_unknown_signal",),
    "parser_unknown_reject": ("parser_unknown_signal",),
    "parser_unknown_classify": ("parser_unknown_signal",),
    "parser_unknown_route": ("parser_unknown_signal",),
    "parser_mapping_approval_intent": (
        "parser_mapping_candidate",
        "parser_governance_item",
    ),
    "knowledge_artifact_review": ("knowledge_artifact",),
    "knowledge_artifact_approve": ("knowledge_artifact",),
    "knowledge_artifact_reject": ("knowledge_artifact",),
}


SCREEN1_GOVERNANCE_STATUSES = (
    "queued_request",
    "review_requested",
    "classification_requested",
    "route_requested",
    "approval_requested",
    "rejection_requested",
    "mapping_intent_requested",
)


SCREEN2_DIAGNOSTIC_REVIEW_TARGETS = (
    "diagnostic_domain",
    "diagnostic_evidence",
    "evidence_group",
    "metric_group",
    "wait_event_group",
    "sql_signal",
    "diagnostic_section",
)

SCREEN2_DIAGNOSTIC_REVIEW_DISPOSITIONS = (
    "confirm_evidence_reviewed",
    "flag_insufficient_evidence",
    "dispute_diagnostic_interpretation",
    "add_reviewer_note",
    "request_governed_diagnostic_review",
)

SCREEN2_FORBIDDEN_DISPOSITIONS = (
    "needs_parser_review",
    "needs_scoring_review",
    "needs_recommendation_review",
    "needs_learning_candidate",
    "execute_reanalysis",
    "promote_candidate",
    "materialize_rule",
    "change_runtime_eligibility",
    "capture_recommendation_outcome",
)


def _validate_screen1_parser_governance_payload(
    request: DashboardRuntimeActionRequest,
) -> None:
    payload = request.payload
    allowed_targets = SCREEN1_PARSER_GOVERNANCE_TARGETS.get(request.action_type)
    if not allowed_targets:
        raise DashboardRuntimeInteractionError(
            f"action_type {request.action_type!r} is not a Screen 1 parser governance action"
        )
    if request.target_type not in allowed_targets:
        raise DashboardRuntimeInteractionError(
            f"target_type for {request.action_type} must be one of {', '.join(allowed_targets)}"
        )
    _require_text(request.actor_id, "actor_id")
    _require_text(request.target_id, "target_id")
    if request.target_id in {"dashboard-target", "screen1-parser-governance"}:
        raise DashboardRuntimeInteractionError(
            "Screen 1 parser governance requests require a selected target id"
        )
    _require_text(
        payload.get("reviewer_actor_id") or payload.get("actor_id") or request.actor_id,
        "payload.reviewer_actor_id",
    )
    _require_supported(
        str(payload.get("governance_status") or ""),
        SCREEN1_GOVERNANCE_STATUSES,
        "payload.governance_status",
    )
    _require_text(payload.get("governance_intent"), "payload.governance_intent")
    selected_value = str(
        payload.get("selected_context_value")
        or payload.get("screen1_selected_target_id")
        or ""
    ).strip()
    if not selected_value:
        raise DashboardRuntimeInteractionError(
            "payload.selected_context_value must identify the selected Screen 1 target"
        )
    if request.action_type.startswith("parser_unknown_"):
        _require_text(
            payload.get("selectedUnknownSignal") or selected_value,
            "payload.selectedUnknownSignal",
        )
    if request.action_type == "parser_mapping_approval_intent":
        _require_text(
            payload.get("selectedGovernanceItem") or payload.get("selectedUnknownSignal") or selected_value,
            "payload.selectedGovernanceItem",
        )
    if request.action_type.startswith("knowledge_artifact_"):
        _require_text(
            payload.get("selectedArtifact") or selected_value,
            "payload.selectedArtifact",
        )
    forbidden_true_fields = (
        "parser_output_mutation_requested",
        "parser_output_mutation_allowed",
        "direct_parser_mutation_allowed",
        "parser_mapping_created",
        "parser_candidate_created",
        "parser_backlog_item_created",
        "classification_persisted",
        "artifact_approved",
        "artifact_rejected",
        "artifact_revision_persisted",
        "materialization_created",
        "phase4i_mutation_requested",
        "phase4i_mutation_allowed",
        "runtime_activation_requested",
        "runtime_activation_granted",
        "runtime_influence_granted",
        "future_run_influence_granted",
        "future_run_influence_active",
        "browser_db_query_attempted",
        "browser_object_storage_access_attempted",
        "browser_file_read_attempted",
        "run_analysis_coupling",
        "phase8_behavior",
        "em_extract_attempted",
    )
    for field_name in forbidden_true_fields:
        if payload.get(field_name) is True:
            raise DashboardRuntimeInteractionError(
                f"payload.{field_name} must remain false for Screen 1 parser governance"
            )
    if payload.get("future_run_influence_gated") is False:
        raise DashboardRuntimeInteractionError(
            "payload.future_run_influence_gated must remain true"
        )
    if str(payload.get("target_screen") or "").strip() not in {"", "screen_1"}:
        raise DashboardRuntimeInteractionError(
            "payload.target_screen must remain screen_1 for Screen 1 parser governance"
        )
    _reject_source_secret_fields(payload)


def _validate_screen2_diagnostic_review_payload(
    request: DashboardRuntimeActionRequest,
) -> None:
    payload = request.payload
    if request.action_type != "diagnostic_review":
        raise DashboardRuntimeInteractionError(
            f"action_type {request.action_type!r} is not a Screen 2 diagnostic review action"
        )
    if request.target_type not in SCREEN2_DIAGNOSTIC_REVIEW_TARGETS:
        raise DashboardRuntimeInteractionError(
            "target_type for diagnostic_review must be one of "
            + ", ".join(SCREEN2_DIAGNOSTIC_REVIEW_TARGETS)
        )
    _require_text(request.actor_id, "actor_id")
    _require_text(request.target_id, "target_id")
    if request.target_id in {"dashboard-target", "screen2-diagnostic-review"}:
        raise DashboardRuntimeInteractionError(
            "Screen 2 diagnostic review requests require a selected diagnostic or evidence target"
        )
    disposition = str(
        payload.get("screen2_review_disposition")
        or payload.get("review_disposition")
        or payload.get("review_decision")
        or ""
    ).strip()
    _require_supported(
        disposition,
        SCREEN2_DIAGNOSTIC_REVIEW_DISPOSITIONS,
        "payload.screen2_review_disposition",
    )
    for forbidden in SCREEN2_FORBIDDEN_DISPOSITIONS:
        if forbidden in {
            disposition,
            str(payload.get("review_decision") or "").strip(),
            str(payload.get("requested_action") or "").strip(),
        }:
            raise DashboardRuntimeInteractionError(
                f"Screen 2 diagnostic review cannot request {forbidden!r}"
            )
    _require_text(
        payload.get("reviewer_actor_id") or payload.get("actor_id") or request.actor_id,
        "payload.reviewer_actor_id",
    )
    selected_value = str(
        payload.get("selected_context_value")
        or payload.get("selectedEvidenceGroup")
        or payload.get("selectedMetricGroup")
        or payload.get("selectedWaitEventGroup")
        or payload.get("selectedSqlSignal")
        or payload.get("selectedDiagnosticSection")
        or payload.get("selectedDomain")
        or ""
    ).strip()
    if not selected_value:
        raise DashboardRuntimeInteractionError(
            "payload.selected_context_value must identify selected Screen 2 diagnostic evidence"
        )
    _require_mapping(
        payload.get("deterministic_diagnosis_context") or {},
        "payload.deterministic_diagnosis_context",
    )
    forbidden_true_fields = (
        "diagnostic_truth_mutation_requested",
        "diagnostic_truth_mutation_allowed",
        "phase4i_mutation_requested",
        "phase4i_mutation_allowed",
        "score_mutation_requested",
        "score_mutation_allowed",
        "severity_mutation_requested",
        "confidence_mutation_requested",
        "recommendation_mutation_requested",
        "recommendation_truth_mutation_allowed",
        "parser_output_mutation_requested",
        "parser_output_mutation_allowed",
        "parser_mapping_created",
        "reanalysis_execution_requested",
        "runtime_execution_requested",
        "learning_candidate_created",
        "candidate_created",
        "materialization_created",
        "runtime_eligibility_changed",
        "runtime_activation_requested",
        "runtime_activation_granted",
        "runtime_influence_granted",
        "future_run_influence_granted",
        "future_run_influence_active",
        "browser_db_query_attempted",
        "browser_object_storage_access_attempted",
        "browser_file_read_attempted",
        "run_analysis_coupling",
        "phase8_behavior",
        "em_extract_attempted",
    )
    for field_name in forbidden_true_fields:
        if payload.get(field_name) is True:
            raise DashboardRuntimeInteractionError(
                f"payload.{field_name} must remain false for Screen 2 diagnostic review"
            )
    if payload.get("non_mutating_diagnostic_review_intent") is False:
        raise DashboardRuntimeInteractionError(
            "payload.non_mutating_diagnostic_review_intent must remain true"
        )
    if str(payload.get("target_screen") or "").strip() not in {"", "screen_2"}:
        raise DashboardRuntimeInteractionError(
            "payload.target_screen must remain screen_2 for Screen 2 diagnostic review"
        )
    _reject_source_secret_fields(payload)


def build_request_id(
    screen_id: Any,
    action_type: Any,
    target_id: Any,
    requested_at: Any,
) -> str:
    token = "-".join(
        _normalize_token(value)
        for value in (screen_id, action_type, target_id, requested_at)
    )
    return f"PHASE7CM-DASHBOARD-ACTION-{token[:96]}"


def build_idempotency_key(
    screen_id: Any,
    action_type: Any,
    target_id: Any,
    payload: dict[str, Any],
) -> str:
    raw = json.dumps(
        {
            "screen_id": screen_id,
            "action_type": action_type,
            "target_id": target_id,
            "payload": payload,
        },
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"phase7cm:{_normalize_token(screen_id)}:{_normalize_token(action_type)}:{digest}"


def default_action_queue_dir() -> Path:
    configured = os.getenv("AWR_PHASE7_DASHBOARD_ACTION_QUEUE")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(tempfile.gettempdir()) / "awr_phase7_dashboard_actions"


def _validate_source_service_request(payload: dict[str, Any], action_type: str) -> None:
    _require_mapping(payload, "payload")
    if str(payload.get("action_type") or "").strip() != action_type:
        raise DashboardRuntimeInteractionError(
            f"payload.action_type must be {action_type!r}"
        )
    if str(payload.get("screen_id") or "").strip() != "index_source_mode":
        raise DashboardRuntimeInteractionError("payload.screen_id must be index_source_mode")
    if str(payload.get("target_screen") or "").strip() != "screen3":
        raise DashboardRuntimeInteractionError("payload.target_screen must be screen3")
    for field_name in (
        "direct_truth_mutation_allowed",
        "phase4i_mutation_allowed",
        "phase8_behavior",
        "run_analysis_coupling",
        "browser_db_query_attempted",
        "browser_object_storage_access_attempted",
        "direct_object_storage_execution_attempted",
        "em_extract_attempted",
    ):
        if payload.get(field_name) is True:
            raise DashboardRuntimeInteractionError(f"payload.{field_name} must remain false")
    if _payload_contains_em_extract_attempt(payload):
        raise DashboardRuntimeInteractionError("EM Extract runtime support remains Phase 8")


def _payload_contains_em_extract_attempt(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_payload_contains_em_extract_attempt(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_payload_contains_em_extract_attempt(item) for item in value)
    if isinstance(value, str):
        normalized = value.lower()
        return "em_extract" in normalized or "em extract" in normalized
    return False


def _query_existing_runs(connection: Any, *, limit: int) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT RUN_HISTORY_ID,
                   SOURCE_FILE_NAME,
                   DB_NAME,
                   DBID,
                   INSTANCE_NAME,
                   AWR_BEGIN_TIME,
                   AWR_END_TIME,
                   DECISION_POSTURE,
                   RISK_LEVEL,
                   CREATED_AT
              FROM AWR_RUN_HISTORY
             ORDER BY CREATED_AT DESC, RUN_HISTORY_ID DESC
             FETCH FIRST :limit ROWS ONLY
            """,
            {"limit": limit},
        )
        rows = cursor.fetchall()
        descriptions = cursor.description or []
    column_names = [str(item[0]).lower() for item in descriptions]
    results: list[dict[str, Any]] = []
    for row in rows:
        record = {
            column: _json_safe(value)
            for column, value in zip(column_names, row, strict=False)
        }
        run_history_id = str(record.get("run_history_id") or "").strip()
        if run_history_id:
            record["run_reference"] = f"RUN_HISTORY_ID:{run_history_id}"
        results.append(record)
    return results


def _write_source_service_audit(
    *,
    queue_dir: Path | None,
    request_id: str,
    record_type: str,
    payload: dict[str, Any],
    result: dict[str, Any],
) -> Path:
    target_dir = queue_dir or default_action_queue_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    audit_reference = target_dir / f"{_safe_filename(request_id)}.json"
    audit_reference.write_text(
        json.dumps(
            {
                "phase": "Phase 7",
                "subphase": "7CM",
                "record_type": record_type,
                "request_id": request_id,
                "payload": payload,
                "result": result,
                "audit": {
                    "recorded_at": _utc_now(),
                    "runtime_influence_granted": False,
                    "phase4i_mutated": False,
                    "phase8_behavior": False,
                    "run_analysis_called": False,
                    "direct_truth_mutation_performed": False,
                },
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    return audit_reference


def _source_service_rejection(request_id: str, reason: str) -> dict[str, Any]:
    return {
        "status": "rejected",
        "validation_status": "invalid",
        "request_id": request_id,
        "audit_reference": None,
        "message": f"Phase 7CM source service request rejected: {reason}",
        "runs": [],
        "run_count": 0,
        "persisted": False,
        "queued": False,
        "phase4i_mutated": False,
        "phase8_behavior": False,
    }


def _normalize_limit(value: Any, *, default: int, maximum: int) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return default
    return max(1, min(parsed, maximum))


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime,)):
        return value.isoformat()
    return str(value) if value is not None else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_filename(value: str) -> str:
    return _normalize_token(value)[:120] or "dashboard-action"


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip()
    normalized = _TOKEN_RE.sub("-", text).strip("-")
    return normalized or "value"


def _require_text(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DashboardRuntimeInteractionError(f"{field_name} must be a non-empty string")


def _require_optional_text(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise DashboardRuntimeInteractionError(f"{field_name} must be a string or None")


def _require_token(value: Any, field_name: str) -> None:
    _require_text(value, field_name)
    if any(char in str(value) for char in "<>"):
        raise DashboardRuntimeInteractionError(f"{field_name} may not contain markup")


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise DashboardRuntimeInteractionError(f"{field_name} must be a mapping")


def _require_string_tuple(value: Any, field_name: str) -> None:
    if not isinstance(value, tuple) or not all(isinstance(item, str) for item in value):
        raise DashboardRuntimeInteractionError(f"{field_name} must be a tuple of strings")


def _require_supported(value: str, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise DashboardRuntimeInteractionError(
            f"{field_name} must be one of {', '.join(supported)}"
        )


def _reject_true(value: Any, field_name: str) -> None:
    if value is True:
        raise DashboardRuntimeInteractionError(f"{field_name} must remain false")


def _validate_index_source_selection_payload(payload: dict[str, Any]) -> None:
    mode = str(
        payload.get("selectedSourceMode")
        or payload.get("selected_source_mode")
        or payload.get("source_mode")
        or ""
    ).strip()
    if mode not in INDEX_SOURCE_MODES:
        raise DashboardRuntimeInteractionError(
            "index source-selection payload must include a supported selectedSourceMode"
        )
    method = str(payload.get("sourceSelectionMethod") or payload.get("source_selection_method") or "").strip()
    if str(payload.get("target_screen") or "").strip() != "screen3":
        raise DashboardRuntimeInteractionError(
            "index source-selection payload must target screen3"
        )
    forbidden_true_fields = (
        "browser_parsing_performed",
        "browser_file_read_attempted",
        "browser_file_upload_performed",
        "browser_object_storage_access_attempted",
        "direct_awr_parse_attempted",
        "direct_file_read_attempted",
        "direct_object_storage_execution_attempted",
        "em_extract_attempted",
        "phase8_behavior",
        "run_analysis_coupling",
    )
    for field_name in forbidden_true_fields:
        if payload.get(field_name) is True:
            raise DashboardRuntimeInteractionError(
                f"index source-selection payload field {field_name} must remain false"
            )
    if "em_extract" in mode.lower() or "em extract" in mode.lower():
        raise DashboardRuntimeInteractionError("EM Extract source mode remains Phase 8")
    if mode == "local_staged":
        if method == "os_folder_picker":
            _require_positive_int(
                payload.get("selectedLocalFolderFileCount"),
                "payload.selectedLocalFolderFileCount",
            )
            _require_positive_int(
                payload.get("selectedLocalFolderCandidateCount")
                or payload.get("selectedLocalFolderAwrCandidateCount"),
                "payload.selectedLocalFolderCandidateCount",
            )
            _require_positive_int(
                payload.get("selectedLocalFolderAwrCandidateCount")
                or payload.get("selectedLocalFolderCandidateCount"),
                "payload.selectedLocalFolderAwrCandidateCount",
            )
            _require_non_negative_int(
                payload.get("selectedLocalFolderOutFileCount"),
                "payload.selectedLocalFolderOutFileCount",
            )
            _require_text(
                payload.get("selectedLocalFolderSampleFiles")
                or payload.get("selectedLocalRelativePaths"),
                "payload.selectedLocalFolderSampleFiles",
            )
            if str(payload.get("selectedLocalFolderValidationStatus") or "").lower().startswith("invalid"):
                raise DashboardRuntimeInteractionError(
                    "payload.selectedLocalFolderValidationStatus must not be invalid"
                )
        elif method in {"backend_path", ""}:
            _require_text(payload.get("selectedSourcePath"), "payload.selectedSourcePath")
        else:
            raise DashboardRuntimeInteractionError(
                "local_staged sourceSelectionMethod must be os_folder_picker or backend_path"
            )
    elif mode == "local_file":
        if method == "os_file_picker":
            file_name = payload.get("selectedLocalFileName")
            _require_text(file_name, "payload.selectedLocalFileName")
            _require_allowed_local_file_name(file_name, "payload.selectedLocalFileName")
            _require_non_negative_int(
                payload.get("selectedLocalFileSize"),
                "payload.selectedLocalFileSize",
            )
            if str(payload.get("selectedLocalFileValidationStatus") or "").lower().startswith("invalid"):
                raise DashboardRuntimeInteractionError(
                    "payload.selectedLocalFileValidationStatus must not be invalid"
                )
        elif method == "backend_path":
            path = payload.get("selectedSourcePath")
            _require_text(path, "payload.selectedSourcePath")
            _require_allowed_local_file_name(path, "payload.selectedSourcePath")
        else:
            raise DashboardRuntimeInteractionError(
                "local_file sourceSelectionMethod must be os_file_picker or backend_path"
            )
    elif mode == "existing_run":
        if method not in {"existing_run_reference", ""}:
            raise DashboardRuntimeInteractionError(
                "existing_run sourceSelectionMethod must be existing_run_reference"
            )
        _require_text(payload.get("selectedRunReference"), "payload.selectedRunReference")
        if str(payload.get("existingRunLookupStatus") or "").strip() != "valid":
            raise DashboardRuntimeInteractionError(
                "payload.existingRunLookupStatus must be valid before existing_run handoff"
            )
    elif mode == "object_storage":
        if method not in {"object_storage_metadata", ""}:
            raise DashboardRuntimeInteractionError(
                "object_storage sourceSelectionMethod must be object_storage_metadata"
            )
        for field_name in (
            "objectStorageNamespace",
            "objectStorageBucket",
            "objectStorageObjectName",
            "objectStorageRegion",
        ):
            _require_text(payload.get(field_name), f"payload.{field_name}")
        if str(payload.get("objectStorageValidationStatus") or "").strip() != "valid":
            raise DashboardRuntimeInteractionError(
                "payload.objectStorageValidationStatus must be valid before object_storage handoff"
            )
    _reject_source_secret_fields(payload)


def _source_summary_for_request(request: DashboardRuntimeActionRequest) -> dict[str, Any]:
    if request.screen_id != "index_source_mode" or request.action_type != "source_selection_handoff":
        if request.screen_id == "screen_1":
            return _screen1_governance_summary_for_request(request)
        if request.screen_id == "screen_2":
            return _screen2_diagnostic_review_summary_for_request(request)
        return {}
    payload = request.payload
    mode = str(
        payload.get("selectedSourceMode")
        or payload.get("selected_source_mode")
        or payload.get("source_mode")
        or ""
    )
    summary: dict[str, Any] = {
        "selectedSourceMode": mode,
        "sourceSelectionMethod": payload.get("sourceSelectionMethod")
        or payload.get("source_selection_method")
        or "",
        "target_screen": payload.get("target_screen"),
    }
    for field_name in (
        "selectedSourcePath",
        "selectedLocalFolderFileCount",
        "selectedLocalFolderOutFileCount",
        "selectedLocalFolderSampleFiles",
        "selectedLocalRelativePaths",
        "selectedLocalTotalBytes",
        "selectedLocalFolderCandidateCount",
        "selectedLocalFolderAwrCandidateCount",
        "selectedLocalFolderRejectedCount",
        "selectedLocalFolderValidationStatus",
        "selectedLocalFolderValidationMessages",
        "selectedLocalFileName",
        "selectedLocalFileSize",
        "selectedLocalFileType",
        "selectedLocalFileExtension",
        "selectedLocalFileValidationStatus",
        "selectedRunReference",
        "existingRunLookupStatus",
        "existingRunLookupMessage",
        "existingRunLookupCount",
        "objectStorageNamespace",
        "objectStorageBucket",
        "objectStorageObjectName",
        "objectStorageRegion",
        "objectStorageValidationStatus",
        "objectStorageValidationMessage",
        "source_mode",
        "source_selection_method",
        "backend_visible_path",
        "existing_run_reference",
        "object_storage_namespace",
        "object_storage_bucket",
        "object_storage_object_name",
        "object_storage_region",
        "picker_file_manifest",
        "uploaded_file_manifest",
        "awr_signature_validation",
    ):
        if payload.get(field_name) not in ("", None):
            summary[field_name] = payload.get(field_name)
    summary["validation_status"] = _source_validation_status(payload)
    summary["validation_messages"] = _source_validation_messages(payload)
    return summary


def _screen1_governance_summary_for_request(
    request: DashboardRuntimeActionRequest,
) -> dict[str, Any]:
    payload = request.payload
    return {
        "screen_id": request.screen_id,
        "action_type": request.action_type,
        "workflow_type": request.workflow_type,
        "target_type": request.target_type,
        "target_id": request.target_id,
        "selected_context_key": payload.get("selected_context_key"),
        "selected_context_value": payload.get("selected_context_value"),
        "selectedUnknownSignal": payload.get("selectedUnknownSignal"),
        "selectedGovernanceItem": payload.get("selectedGovernanceItem"),
        "selectedKnowledgeRequest": payload.get("selectedKnowledgeRequest"),
        "selectedArtifact": payload.get("selectedArtifact"),
        "governance_intent": payload.get("governance_intent"),
        "governance_status": payload.get("governance_status"),
        "future_run_influence_gated": payload.get("future_run_influence_gated"),
        "runtime_activation_granted": False,
        "phase4i_mutation_allowed": False,
        "parser_output_mutation_allowed": False,
    }


def _screen2_diagnostic_review_summary_for_request(
    request: DashboardRuntimeActionRequest,
) -> dict[str, Any]:
    payload = request.payload
    return {
        "screen_id": request.screen_id,
        "action_type": request.action_type,
        "workflow_type": request.workflow_type,
        "target_type": request.target_type,
        "target_id": request.target_id,
        "selected_context_key": payload.get("selected_context_key"),
        "selected_context_value": payload.get("selected_context_value"),
        "selectedDomain": payload.get("selectedDomain"),
        "selectedEvidenceGroup": payload.get("selectedEvidenceGroup"),
        "selectedMetricGroup": payload.get("selectedMetricGroup"),
        "selectedWaitEventGroup": payload.get("selectedWaitEventGroup"),
        "selectedSqlSignal": payload.get("selectedSqlSignal"),
        "selectedDiagnosticSection": payload.get("selectedDiagnosticSection"),
        "screen2_review_disposition": payload.get("screen2_review_disposition"),
        "reviewer_actor_id": payload.get("reviewer_actor_id"),
        "non_mutating_diagnostic_review_intent": payload.get("non_mutating_diagnostic_review_intent"),
        "diagnostic_truth_mutation_allowed": False,
        "score_mutation_allowed": False,
        "recommendation_truth_mutation_allowed": False,
        "parser_output_mutation_allowed": False,
        "runtime_activation_granted": False,
    }


def _reject_source_secret_fields(payload: dict[str, Any]) -> None:
    sensitive_markers = ("password", "secret", "private_key", "token", "credential")
    for key, value in payload.items():
        normalized_key = str(key).lower()
        if any(marker in normalized_key for marker in sensitive_markers):
            if value not in ("", None, False):
                raise DashboardRuntimeInteractionError(
                    f"payload.{key} must not include secrets or credentials"
                )


def _source_validation_status(payload: dict[str, Any]) -> str:
    mode = str(payload.get("selectedSourceMode") or payload.get("selected_source_mode") or "")
    if mode == "local_staged" and payload.get("sourceSelectionMethod") == "os_folder_picker":
        return str(payload.get("selectedLocalFolderValidationStatus") or "warning-backend-validation-pending")
    if mode == "local_file" and payload.get("sourceSelectionMethod") == "os_file_picker":
        return str(payload.get("selectedLocalFileValidationStatus") or "warning-backend-validation-pending")
    return "accepted"


def _source_validation_messages(payload: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    folder_message = payload.get("selectedLocalFolderValidationMessages")
    if folder_message:
        messages.append(str(folder_message))
    awr_signature = payload.get("awr_signature_validation")
    if awr_signature:
        messages.append(f"awr_signature_validation={awr_signature}")
    if not messages:
        messages.append("Source metadata accepted for governed backend validation.")
    return messages


def _require_positive_int(value: Any, field_name: str) -> None:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        raise DashboardRuntimeInteractionError(f"{field_name} must be a positive integer")
    if parsed <= 0:
        raise DashboardRuntimeInteractionError(f"{field_name} must be a positive integer")


def _require_non_negative_int(value: Any, field_name: str) -> None:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        raise DashboardRuntimeInteractionError(f"{field_name} must be a non-negative integer")
    if parsed < 0:
        raise DashboardRuntimeInteractionError(f"{field_name} must be a non-negative integer")


def _require_allowed_local_file_name(value: Any, field_name: str) -> None:
    _require_text(value, field_name)
    suffix = str(value).strip().lower().rsplit(".", 1)
    extension = suffix[-1] if len(suffix) == 2 else ""
    if extension in {"html", "htm"}:
        raise DashboardRuntimeInteractionError(
            "HTML AWR input is not supported by the current governed handoff. "
            "Planned for a future parser/source adapter."
        )
    if extension not in {"out"}:
        raise DashboardRuntimeInteractionError(
            f"{field_name} must end with .out for governed source handoff"
        )


def _validate_future_run_influence_metadata(metadata: dict[str, Any]) -> None:
    forbidden_true_fields = (
        "runtime_activation_granted",
        "runtime_influence_granted",
        "immediate_runtime_mutation",
        "phase4i_mutation_allowed",
        "parser_mutation_applied",
        "scoring_mutation_applied",
        "trend_aware_runtime_activation",
        "trend_aware_scoring_runtime_active",
        "trend_aware_score_runtime_truth",
        "recommendation_truth_mutation_applied",
        "phase8_behavior",
    )
    for field_name in forbidden_true_fields:
        if metadata.get(field_name) is True:
            raise DashboardRuntimeInteractionError(
                f"future_run_influence_metadata.{field_name} must remain false"
            )
