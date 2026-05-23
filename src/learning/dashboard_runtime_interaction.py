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
    "blocked",
    "completed",
    "failed_safely",
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
SCREEN3_RUNTIME_ACTIONS = (
    "analyze_selection",
    "rerun_analysis",
    "build_comparison",
    "load_from_object_storage",
)
SCREEN3_APPROVED_EXECUTION_MODES = (
    "local_backend_execution",
    "governed_request_only",
    "validation_only",
)


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
        if self.screen_id == "screen_3":
            _validate_screen3_runtime_action_payload(self)

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
    screen_id = str(payload.get("screen_id") or "")
    requested_at = str(payload.get("requested_at") or _utc_now())
    execution_mode = str(
        payload.get("execution_mode")
        or (
            "local_backend_execution"
            if screen_id == "screen_3"
            else "request_record_only"
        )
    )
    request_id = str(
        payload.get("request_id")
        or build_request_id(
            screen_id,
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
        screen_id=screen_id,
        action_type=str(payload.get("action_type") or ""),
        workflow_type=str(payload.get("workflow_type") or ""),
        actor_id=str(payload.get("actor_id") or "ACTOR-LOCAL-DASHBOARD-REVIEWER"),
        requested_at=requested_at,
        target_type=str(payload.get("target_type") or "dashboard_control"),
        target_id=str(payload.get("target_id") or "dashboard-target"),
        idempotency_key=idempotency_key,
        payload=dict(payload.get("payload") or {}),
        governance_mode=str(payload.get("governance_mode") or "governed_request"),
        execution_mode=execution_mode,
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
    if request.screen_id == "screen_1":
        db_persistence = _persist_screen1_parser_governance_review(
            request,
            audit_reference,
            connection_factory=connection_factory,
            db_persistence_enabled=db_persistence_enabled,
        )
    elif request.screen_id == "screen_3":
        db_persistence = _persist_screen3_runtime_control_request(
            request,
            audit_reference,
            connection_factory=connection_factory,
            db_persistence_enabled=db_persistence_enabled,
        )
    else:
        db_persistence = {
            "status": "not_attempted",
            "mode": "json_audit_file",
            "record_reference": None,
            "tables_touched": [],
            "message": "DB persistence is not part of this dashboard action.",
            "screen6_candidate_created": False,
        }
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
    if request.screen_id == "screen_3":
        source_summary.update(_screen3_runtime_summary_for_request(request, db_persistence))
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
    result_status = "accepted"
    if request.screen_id == "screen_3":
        requested_action = _screen3_requested_action(request.payload)
        missing_gates = list(db_persistence.get("missing_execution_gates") or [])
        execution_performed = bool(db_persistence.get("execution_performed"))
        result_status = "completed" if execution_performed and not missing_gates else "blocked"
        if db_persistence.get("status") == "persisted":
            if result_status == "completed":
                message = (
                    f"Screen 3 governed {requested_action} completed through the governed "
                    "backend wrapper. Existing run truth is unchanged; any output is represented "
                    "as a new artifact/reference."
                )
            else:
                message = db_persistence.get("message") or (
                    f"Screen 3 governed {requested_action} request persisted. "
                    "Execution is blocked until required backend gates are available. "
                    "Existing run truth is unchanged."
                )
        else:
            message = (
                f"Screen 3 governed {requested_action} request recorded as JSON audit fallback only. "
                "DB-backed workflow persistence is unavailable, so execution remains blocked. "
                "Existing run truth is unchanged."
            )
    return DashboardRuntimeActionResult(
        status=result_status,
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


def _persist_screen3_runtime_control_request(
    request: DashboardRuntimeActionRequest,
    audit_reference: Path,
    *,
    connection_factory: Any | None,
    db_persistence_enabled: bool,
) -> dict[str, Any]:
    """Persist a governed Screen 3 runtime-control request and blocked gates."""

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
            PersistedWorkflowAudit,
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
        )

        repository = GovernedWorkflowRepository(connection)
        delegated = _persist_screen3_with_governed_execution_modules(
            request,
            audit_reference,
            repository,
        )
        if delegated is not None:
            return delegated

        requested_action = _screen3_requested_action(request.payload)
        source_mode = _screen3_source_mode(request.payload)
        missing_gates = _screen3_missing_execution_gates(request.payload)
        workflow_request_id = create_workflow_request_id(
            request.workflow_type,
            request.idempotency_key,
        )
        transaction_group_id = create_transaction_group_id(
            request.idempotency_key,
            "screen3_runtime_control_center",
        )
        rollback_reference = f"json-audit:{audit_reference.name}"
        validation_status = (
            "screen3_runtime_valid_blocked_missing_execution_gate"
            if missing_gates
            else "screen3_runtime_valid_metadata_only"
        )
        persisted_payload = {
            "dashboard_request": request.to_dict(),
            "json_audit_reference": str(audit_reference),
            "rollback_reference": rollback_reference,
            "screen3_runtime_control_request": True,
            "requested_screen3_action": requested_action,
            "selected_source_mode": source_mode,
            "database_persistence_performed": True,
            "execution_blocked": bool(missing_gates),
            "missing_execution_gates": missing_gates,
            "current_run_truth_mutated": False,
            "deterministic_truth_changed": False,
            "parser_mutated": False,
            "learning_candidate_created": False,
            "materialization_changed": False,
            "runtime_eligibility_changed": False,
            "phase8_started": False,
            "llm_changed_status": False,
            "llm_changed_validation": False,
            "llm_changed_execution": False,
            "llm_changed_truth": False,
        }
        workflow_request = PersistedWorkflowRequest(
            workflow_request_id=workflow_request_id,
            transaction_group_id=transaction_group_id,
            idempotency_key=request.idempotency_key,
            source_screen=request.screen_id,
            workflow_type=request.workflow_type,
            requested_action=requested_action,
            target_type=request.target_type,
            target_id=request.target_id,
            actor_id=request.actor_id,
            payload=persisted_payload,
            status="VALIDATED",
            notes=(
                "Screen 3 runtime-control request persisted as governed workflow "
                "metadata; existing deterministic truth was not mutated."
            ),
        )
        transaction = PersistedWorkflowTransaction(
            transaction_group_id=transaction_group_id,
            idempotency_key=request.idempotency_key,
            transaction_scope="screen3_runtime_control_center",
            rollback_reference=rollback_reference,
            status="IN_PROGRESS",
            notes="Non-mutating Screen 3 governed runtime-control persistence.",
        )
        validation = PersistedWorkflowValidation(
            workflow_validation_id=create_workflow_validation_id(workflow_request_id),
            workflow_request_id=workflow_request_id,
            validation_status=validation_status,
            valid_flag=True,
            warnings=[
                "existing run truth is unchanged",
                "execution remains blocked unless all server-side governance gates are available",
            ],
            required_next_steps=missing_gates or [
                "review governed Screen 3 runtime-control metadata",
            ],
            notes="Screen 3 validates and records selected source/run/scope action context.",
        )
        audit = PersistedWorkflowAudit(
            workflow_audit_id=create_workflow_audit_id(
                workflow_request_id,
                f"screen3_{requested_action}_runtime_control_recorded",
            ),
            workflow_request_id=workflow_request_id,
            transaction_group_id=transaction_group_id,
            actor_id=request.actor_id,
            action=f"screen3_{requested_action}_runtime_control_recorded",
            audit_summary=(
                f"Screen 3 {requested_action} request persisted. Existing run truth, "
                "diagnosis, scoring, recommendation, parser output, runtime behavior, "
                "ML, materialization, runtime eligibility, and Phase 8 state were not changed."
            ),
            payload_hash=hash_payload(persisted_payload),
            notes="DB-backed Screen 3 workflow record plus JSON audit envelope.",
        )
        artifact_payload = {
            "requested_screen3_action": requested_action,
            "selected_source_mode": source_mode,
            "execution_blocked": bool(missing_gates),
            "missing_execution_gates": missing_gates,
            "current_run_truth_mutated": False,
            "deterministic_truth_changed": False,
            "new_run_output_reference": None,
        }
        artifact = PersistedWorkflowOutputArtifact(
            workflow_output_id=create_workflow_output_id(
                workflow_request_id,
                "validation_response",
                f"screen3-runtime-validation:{workflow_request_id}",
            ),
            workflow_request_id=workflow_request_id,
            artifact_type="validation_response",
            artifact_reference=f"screen3-runtime-validation:{workflow_request_id}",
            artifact_summary="Screen 3 runtime-control validation response.",
            artifact_metadata=artifact_payload,
            status="RECORDED",
            notes="Validation artifact only; not a deterministic run output.",
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
            "workflow_validation_id": validation.workflow_validation_id,
            "workflow_audit_id": audit.workflow_audit_id,
            "transaction_group_id": result.transaction_group_id,
            "output_artifact_reference": artifact.artifact_reference,
            "tables_touched": [
                "AWR_WORKFLOW_TRANSACTION",
                "AWR_WORKFLOW_REQUEST",
                "AWR_WORKFLOW_VALIDATION",
                "AWR_WORKFLOW_AUDIT",
                "AWR_WORKFLOW_OUTPUT_ARTIFACT",
            ],
            "message": (
                "DB-backed Screen 3 workflow record persisted; JSON audit envelope recorded. "
                "No current-run truth, learning, materialization, runtime eligibility, or Phase 8 state changed."
            ),
            "duplicate": result.duplicate,
            "screen6_candidate_created": False,
            "requested_screen3_action": requested_action,
            "selected_source_mode": source_mode,
            "missing_execution_gates": missing_gates,
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
            "requested_screen3_action": _screen3_requested_action(request.payload),
            "selected_source_mode": _screen3_source_mode(request.payload),
            "missing_execution_gates": _screen3_missing_execution_gates(request.payload),
        }
    finally:
        if connection is not None:
            close = getattr(connection, "close", None)
            if callable(close):
                close()


def _persist_screen3_with_governed_execution_modules(
    request: DashboardRuntimeActionRequest,
    audit_reference: Path,
    repository: Any,
) -> dict[str, Any] | None:
    """Delegate Screen 3 actions to existing governed execution wrappers when safe."""

    requested_action = _screen3_requested_action(request.payload)
    if requested_action in {"analyze_selection", "rerun_analysis"}:
        return _persist_screen3_deterministic_execution_request(
            request,
            audit_reference,
            repository,
            requested_action,
        )
    if requested_action == "build_comparison" and _screen3_comparison_inputs(request.payload):
        return _persist_screen3_comparison_execution_request(
            request,
            audit_reference,
            repository,
        )
    if requested_action == "load_from_object_storage" and _screen3_source_mode(request.payload) == "object_storage":
        return _persist_screen3_object_storage_metadata_request(
            request,
            audit_reference,
            repository,
        )
    return None


def _persist_screen3_deterministic_execution_request(
    request: DashboardRuntimeActionRequest,
    audit_reference: Path,
    repository: Any,
    requested_action: str,
) -> dict[str, Any]:
    from src.learning.governed_workflow_repository import (
        create_transaction_group_id,
        create_workflow_audit_id,
        create_workflow_request_id,
        create_workflow_validation_id,
    )
    from src.learning.screen3_deterministic_execution import (
        DeterministicExecutionRequestEnvelope,
        create_deterministic_execution_id,
        deterministic_execution_result_to_dict,
        execute_deterministic_reanalysis,
    )

    source_mode = _screen3_source_mode(request.payload)
    reanalysis_request = _screen3_reanalysis_request_from_dashboard_request(
        request,
        requested_action,
    )
    transaction_group_id = create_transaction_group_id(
        request.idempotency_key,
        "screen3_deterministic_reanalysis",
    )
    execution_id = create_deterministic_execution_id(
        reanalysis_request.request_id,
        request.idempotency_key,
    )
    result = execute_deterministic_reanalysis(
        DeterministicExecutionRequestEnvelope(
            execution_id=execution_id,
            reanalysis_request=reanalysis_request,
            actor_id=request.actor_id,
            actor_audit_context=_screen3_actor_audit_context(request),
            idempotency_key=request.idempotency_key,
            transaction_group_id=transaction_group_id,
            source_mode=source_mode,
            requested_action=requested_action,
            dry_run=False,
            validation_reference=f"json-audit:{audit_reference.name}",
            rollback_reference=_screen3_rollback_reference(request, audit_reference),
            notes=(
                "7CP governed Screen 3 deterministic action. Existing run truth "
                "remains immutable; runner invocation requires an injected runner."
            ),
        ),
        repository,
        runner=None,
    )
    result_dict = deterministic_execution_result_to_dict(result)
    workflow_request_id = create_workflow_request_id(
        "screen3_deterministic_reanalysis",
        request.idempotency_key,
    )
    output_reference = _screen3_first_output_reference(result_dict)
    missing_gates = _screen3_missing_execution_gates(request.payload)
    if result_dict.get("execution_status") == "blocked_no_runner":
        missing_gates = [
            "capability gap: no injected deterministic runner is configured for the dashboard workflow service",
            "capability gap: new run/output artifact lifecycle is not connected for Screen 3 deterministic execution",
        ]
    return _screen3_db_persistence_result(
        request=request,
        mode="db_backed_deterministic_execution_wrapper_and_json_audit",
        workflow_request_id=workflow_request_id,
        workflow_validation_id=create_workflow_validation_id(workflow_request_id),
        workflow_audit_id=create_workflow_audit_id(
            workflow_request_id,
            "screen3_deterministic_execution_recorded",
        ),
        transaction_group_id=result_dict.get("transaction_group_id") or transaction_group_id,
        output_artifact_reference=output_reference,
        requested_action=requested_action,
        source_mode=source_mode,
        missing_gates=missing_gates,
        execution_module="screen3_deterministic_execution",
        execution_status=str(result_dict.get("execution_status") or "blocked_no_runner"),
        execution_performed=bool(result_dict.get("deterministic_execution_performed")),
        extra={
            "deterministic_execution_result": result_dict,
            "runner_invoked": bool(result_dict.get("runner_invoked")),
        },
    )


def _persist_screen3_comparison_execution_request(
    request: DashboardRuntimeActionRequest,
    audit_reference: Path,
    repository: Any,
) -> dict[str, Any]:
    from src.learning.governed_workflow_repository import (
        create_transaction_group_id,
        create_workflow_audit_id,
        create_workflow_request_id,
        create_workflow_validation_id,
    )
    from src.learning.screen3_comparison_execution import (
        ComparisonExecutionRequestEnvelope,
        comparison_execution_result_to_dict,
        create_comparison_execution_id,
        execute_awr_report_comparison,
    )

    requested_action = "build_comparison"
    source_mode = _screen3_source_mode(request.payload)
    reanalysis_request = _screen3_reanalysis_request_from_dashboard_request(
        request,
        requested_action,
    )
    comparison_inputs = _screen3_comparison_inputs(request.payload)
    transaction_group_id = create_transaction_group_id(
        request.idempotency_key,
        "screen3_comparison_execution",
    )
    comparison_execution_id = create_comparison_execution_id(
        reanalysis_request.request_id,
        request.idempotency_key,
    )
    result = execute_awr_report_comparison(
        ComparisonExecutionRequestEnvelope(
            comparison_execution_id=comparison_execution_id,
            reanalysis_request=reanalysis_request,
            actor_id=request.actor_id,
            actor_audit_context=_screen3_actor_audit_context(request),
            idempotency_key=request.idempotency_key,
            transaction_group_id=transaction_group_id,
            comparison_name=str(
                request.payload.get("comparison_name")
                or request.payload.get("selectedComparisonBaseline")
                or "Screen 3 governed comparison"
            ),
            comparison_inputs=comparison_inputs,
            baseline_reference=_screen3_optional_text(
                request.payload.get("baseline_reference")
                or request.payload.get("selectedComparisonBaseline")
            ),
            requested_action=requested_action,
            source_mode=source_mode,
            dry_run=False,
            validation_reference=f"json-audit:{audit_reference.name}",
            rollback_reference=_screen3_rollback_reference(request, audit_reference),
            notes="7CP governed Screen 3 comparison request.",
        ),
        repository,
    )
    result_dict = comparison_execution_result_to_dict(result)
    workflow_request_id = create_workflow_request_id(
        "screen3_comparison_execution",
        request.idempotency_key,
    )
    missing_gates = list(result_dict.get("denied_reasons") or [])
    execution_status = str(result_dict.get("execution_status") or "blocked_insufficient_inputs")
    if execution_status.startswith("blocked") and not missing_gates:
        missing_gates = _screen3_missing_execution_gates(request.payload)
    return _screen3_db_persistence_result(
        request=request,
        mode="db_backed_comparison_execution_wrapper_and_json_audit",
        workflow_request_id=workflow_request_id,
        workflow_validation_id=create_workflow_validation_id(workflow_request_id),
        workflow_audit_id=create_workflow_audit_id(
            workflow_request_id,
            "screen3_comparison_execution_recorded",
        ),
        transaction_group_id=result_dict.get("transaction_group_id") or transaction_group_id,
        output_artifact_reference=_screen3_first_output_reference(result_dict),
        requested_action=requested_action,
        source_mode=source_mode,
        missing_gates=missing_gates,
        execution_module="screen3_comparison_execution",
        execution_status=execution_status,
        execution_performed=bool(result_dict.get("comparison_built")),
        extra={"comparison_execution_result": result_dict},
    )


def _persist_screen3_object_storage_metadata_request(
    request: DashboardRuntimeActionRequest,
    audit_reference: Path,
    repository: Any,
) -> dict[str, Any]:
    from src.learning.governed_workflow_repository import (
        create_transaction_group_id,
        create_workflow_audit_id,
        create_workflow_request_id,
        create_workflow_validation_id,
    )
    from src.learning.object_storage_config_validation import (
        ObjectStorageConfiguration,
        ObjectStorageConfigurationValidation,
        create_object_storage_config_id,
        create_object_storage_config_validation_id,
    )
    from src.learning.object_storage_load_execution import (
        ObjectStorageLoadRequestEnvelope,
        create_object_storage_load_execution_id,
        execute_object_storage_load,
        object_storage_load_result_to_dict,
    )

    payload = request.payload
    requested_action = "load_from_object_storage"
    source_mode = "object_storage"
    namespace = str(payload.get("objectStorageNamespace") or "").strip()
    bucket = str(payload.get("objectStorageBucket") or "").strip()
    object_name = str(payload.get("objectStorageObjectName") or "").strip()
    region = str(payload.get("objectStorageRegion") or "").strip()
    config_id = create_object_storage_config_id(
        namespace=namespace,
        bucket=bucket,
        object_name=object_name,
        region=region,
    )
    config = ObjectStorageConfiguration(
        config_id=config_id,
        namespace=namespace,
        bucket=bucket,
        object_name=object_name,
        region=region,
        credential_mode="unknown",
        configured_hint=True,
        notes="Screen 3 metadata-only Object Storage governance wrapper.",
    )
    validation = ObjectStorageConfigurationValidation(
        validation_id=create_object_storage_config_validation_id(config_id),
        config_id=config_id,
        valid_metadata=True,
        validation_status="VALID_METADATA_ONLY",
        namespace_present=True,
        bucket_present=True,
        object_or_prefix_present=True,
        region_present=True,
        compartment_present=False,
        credential_mode_supported=True,
        credential_validation_performed=False,
        object_storage_call_performed=False,
        bucket_list_performed=False,
        object_download_performed=False,
        can_attempt_future_access=False,
        execution_blocked=True,
        denied_reasons=[
            "full Object Storage load-to-analysis requires server-side client, parser/ingest, new-run, deterministic runner, and artifact lifecycle gates"
        ],
        required_next_steps=[
            "connect governed server-side Object Storage client before full load",
            "connect parser/ingest/new-run deterministic analysis pipeline before load-to-analysis",
        ],
        notes="Index validation is active; full load-to-analysis remains gated.",
    )
    transaction_group_id = create_transaction_group_id(
        request.idempotency_key,
        "screen3_object_storage_load",
    )
    load_execution_id = create_object_storage_load_execution_id(
        request.idempotency_key,
        object_name=object_name,
    )
    result = execute_object_storage_load(
        ObjectStorageLoadRequestEnvelope(
            load_execution_id=load_execution_id,
            source_selection=_screen3_source_selection_payload(payload, request.actor_id),
            object_storage_config=config,
            object_storage_validation=validation,
            actor_id=request.actor_id,
            actor_audit_context=_screen3_actor_audit_context(request),
            idempotency_key=request.idempotency_key,
            transaction_group_id=transaction_group_id,
            requested_object_name=object_name,
            load_mode="metadata_only",
            expected_file_type="awr",
            validation_reference=f"json-audit:{audit_reference.name}",
            rollback_reference=_screen3_rollback_reference(request, audit_reference),
            dry_run=False,
            notes="7CP Screen 3 metadata-only Object Storage governance wrapper.",
        ),
        repository,
        client=None,
    )
    result_dict = object_storage_load_result_to_dict(result)
    workflow_request_id = create_workflow_request_id(
        "screen3_object_storage_load",
        request.idempotency_key,
    )
    return _screen3_db_persistence_result(
        request=request,
        mode="db_backed_object_storage_metadata_wrapper_and_json_audit",
        workflow_request_id=workflow_request_id,
        workflow_validation_id=create_workflow_validation_id(workflow_request_id),
        workflow_audit_id=create_workflow_audit_id(
            workflow_request_id,
            "screen3_object_storage_load_recorded",
        ),
        transaction_group_id=result_dict.get("transaction_group_id") or transaction_group_id,
        output_artifact_reference=_screen3_first_output_reference(result_dict),
        requested_action=requested_action,
        source_mode=source_mode,
        missing_gates=_screen3_missing_execution_gates(request.payload),
        execution_module="object_storage_load_execution",
        execution_status=str(result_dict.get("load_status") or "metadata_validated"),
        execution_performed=False,
        extra={
            "object_storage_load_result": result_dict,
            "object_storage_metadata_validated": True,
            "full_load_to_analysis_blocked": True,
        },
    )


def _screen3_db_persistence_result(
    *,
    request: DashboardRuntimeActionRequest,
    mode: str,
    workflow_request_id: str,
    workflow_validation_id: str,
    workflow_audit_id: str,
    transaction_group_id: str,
    output_artifact_reference: str | None,
    requested_action: str,
    source_mode: str,
    missing_gates: list[str],
    execution_module: str,
    execution_status: str,
    execution_performed: bool,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    first_gate = missing_gates[0] if missing_gates else ""
    if requested_action == "build_comparison" and first_gate:
        result_message = (
            f"Screen 3 Build Comparison request was recorded but blocked: {first_gate}. "
            "Target A and Target B must resolve to comparable persisted data before Screen 4 evidence can be built."
        )
    elif requested_action in {"analyze_selection", "rerun_analysis"} and first_gate:
        result_message = (
            f"Screen 3 {requested_action} request was recorded but blocked: {first_gate}. "
            "Connect deterministic runner and output lifecycle before execution."
        )
    elif requested_action == "load_from_object_storage" and first_gate:
        result_message = (
            f"Screen 3 external target preparation request was recorded but blocked: {first_gate}. "
            "Connect server-side load/read, parser/ingest, analysis, and artifact lifecycle first."
        )
    else:
        result_message = (
            f"DB-backed Screen 3 {requested_action} workflow persisted through "
            f"{execution_module}; existing truth and downstream governance state were not mutated."
        )
    return {
        "status": "persisted",
        "mode": mode,
        "record_reference": f"AWR_WORKFLOW_REQUEST:{workflow_request_id}",
        "workflow_request_id": workflow_request_id,
        "workflow_validation_id": workflow_validation_id,
        "workflow_audit_id": workflow_audit_id,
        "transaction_group_id": transaction_group_id,
        "output_artifact_reference": output_artifact_reference,
        "tables_touched": [
            "AWR_WORKFLOW_TRANSACTION",
            "AWR_WORKFLOW_REQUEST",
            "AWR_WORKFLOW_VALIDATION",
            "AWR_WORKFLOW_AUDIT",
            "AWR_WORKFLOW_OUTPUT_ARTIFACT",
        ],
        "message": result_message,
        "duplicate": False,
        "screen6_candidate_created": False,
        "requested_screen3_action": requested_action,
        "selected_source_mode": source_mode,
        "missing_execution_gates": missing_gates,
        "execution_module": execution_module,
        "execution_status": execution_status,
        "execution_performed": execution_performed,
        "current_run_truth_mutated": False,
        "deterministic_truth_changed": False,
        "parser_mutated": False,
        "learning_candidate_created": False,
        "materialization_changed": False,
        "runtime_eligibility_changed": False,
        "phase8_started": False,
        "llm_changed_status": False,
        "llm_changed_validation": False,
        "llm_changed_execution": False,
        "llm_changed_truth": False,
        **(extra or {}),
    }


def _screen3_runtime_summary_for_request(
    request: DashboardRuntimeActionRequest,
    db_persistence: dict[str, Any],
) -> dict[str, Any]:
    payload = request.payload
    missing_gates = list(db_persistence.get("missing_execution_gates") or _screen3_missing_execution_gates(payload))
    requested_action = _screen3_requested_action(payload)
    source_mode = _screen3_source_mode(payload)
    return {
        "screen_id": request.screen_id,
        "action_type": request.action_type,
        "requested_screen3_action": requested_action,
        "selectedSourceMode": source_mode,
        "sourceSelectionMethod": payload.get("sourceSelectionMethod") or payload.get("source_selection_method"),
        "execution_mode": request.execution_mode,
        "validation_status": (
            "blocked_missing_execution_gate"
            if missing_gates
            else "valid_metadata_only"
        ),
        "execution_status": "blocked" if missing_gates else "accepted_metadata_only",
        "backend_execution_module": db_persistence.get("execution_module"),
        "backend_execution_status": db_persistence.get("execution_status"),
        "backend_execution_performed": bool(db_persistence.get("execution_performed")),
        "missing_execution_gates": missing_gates,
        "transaction_group_id": db_persistence.get("transaction_group_id"),
        "workflow_request_id": db_persistence.get("workflow_request_id"),
        "workflow_validation_id": db_persistence.get("workflow_validation_id"),
        "workflow_audit_id": db_persistence.get("workflow_audit_id"),
        "output_artifact_reference": db_persistence.get("output_artifact_reference"),
        "current_run_truth_mutated": False,
        "deterministic_truth_changed": False,
        "parser_mutated": False,
        "learning_candidate_created": False,
        "materialization_changed": False,
        "runtime_eligibility_changed": False,
        "phase8_started": False,
        "llm_changed_status": False,
        "llm_changed_validation": False,
        "llm_changed_execution": False,
        "llm_changed_truth": False,
        "new_run_output_reference": None,
        "objectStorageNamespace": payload.get("objectStorageNamespace"),
        "objectStorageBucket": payload.get("objectStorageBucket"),
        "objectStorageObjectName": payload.get("objectStorageObjectName"),
        "objectStorageRegion": payload.get("objectStorageRegion"),
        "objectStorageValidationStatus": payload.get("objectStorageValidationStatus"),
        "objectStorageValidationMessage": payload.get("objectStorageValidationMessage"),
        "selectedRunReference": payload.get("selectedRunReference"),
        "existingRunLookupStatus": payload.get("existingRunLookupStatus"),
        "selectedComparisonTargetA": payload.get("selectedComparisonTargetA"),
        "selectedComparisonTargetB": payload.get("selectedComparisonTargetB"),
        "selectedComparisonTargetASourceType": payload.get("selectedComparisonTargetASourceType"),
        "selectedComparisonTargetBSourceType": payload.get("selectedComparisonTargetBSourceType"),
        "selectedComparisonTargetAScopeType": payload.get("selectedComparisonTargetAScopeType"),
        "selectedComparisonTargetBScopeType": payload.get("selectedComparisonTargetBScopeType"),
        "selectedComparisonTargetAScopeValue": payload.get("selectedComparisonTargetAScopeValue"),
        "selectedComparisonTargetBScopeValue": payload.get("selectedComparisonTargetBScopeValue"),
        "selectedComparisonTargetATimeWindow": payload.get("selectedComparisonTargetATimeWindow"),
        "selectedComparisonTargetBTimeWindow": payload.get("selectedComparisonTargetBTimeWindow"),
        "selectedComparisonTargetAReadinessState": payload.get("selectedComparisonTargetAReadinessState"),
        "selectedComparisonTargetBReadinessState": payload.get("selectedComparisonTargetBReadinessState"),
        "selectedSourcePath": payload.get("selectedSourcePath"),
        "selectedLocalFileName": payload.get("selectedLocalFileName"),
        "selectedLocalFolderSampleFiles": payload.get("selectedLocalFolderSampleFiles"),
    }


def _screen3_missing_execution_gates(payload: dict[str, Any]) -> list[str]:
    requested_action = _screen3_requested_action(payload)
    source_mode = _screen3_source_mode(payload)
    if requested_action in {"analyze_selection", "rerun_analysis"}:
        gates = [
            "capability gap: no injected deterministic runner is configured for the dashboard workflow service",
            "capability gap: new run/output artifact lifecycle is not connected for Screen 3 execution",
        ]
        if source_mode == "object_storage":
            gates.append(
                "capability gap: Object Storage load/parse/analyze chain is not connected to the deterministic runner"
            )
        return gates
    if requested_action == "build_comparison":
        return _screen3_comparison_missing_gates(payload)
    if requested_action == "load_from_object_storage":
        return [
            "capability gap: external target server-side load client is not configured for full load",
            "capability gap: external target load to parser/ingestion chain is not connected",
            "capability gap: new run/report creation is not connected for external target preparation",
            "capability gap: deterministic analysis runner and dashboard artifact lifecycle are not connected for external target preparation",
        ]
    return ["unsupported Screen 3 action"]


def _screen3_comparison_missing_gates(payload: dict[str, Any]) -> list[str]:
    gates: list[str] = []
    target_a = _screen3_comparison_target_from_payload(payload, "A")
    target_b = _screen3_comparison_target_from_payload(payload, "B")
    for label, target in (("Target A", target_a), ("Target B", target_b)):
        if not target["has_target"]:
            gates.append(f"comparison gap: {label} unresolved")
            continue
        readiness = target["readiness_state"]
        if readiness == "comparable":
            continue
        if readiness == "load_required":
            gates.append(
                f"comparison gap: {label} load_required - load/parse/ingest/analyze target first"
            )
        elif readiness == "ingest_required":
            gates.append(f"comparison gap: {label} ingest_required before comparison")
        elif readiness == "analysis_required":
            gates.append(f"comparison gap: {label} analysis_required before comparison")
        elif readiness == "blocked":
            gates.append(f"comparison gap: {label} blocked: {target['missing_gates'] or 'missing target gate'}")
        elif readiness == "unavailable":
            gates.append(f"comparison gap: {label} unavailable")
        else:
            gates.append(f"comparison gap: {label} readiness unresolved")

    if gates:
        return gates
    if (
        target_a.get("source_type") == target_b.get("source_type")
        and target_a.get("scope_type") == target_b.get("scope_type")
        and target_a.get("scope_value") == target_b.get("scope_value")
        and target_a.get("time_window") == target_b.get("time_window")
    ):
        gates.append(
            "comparison gap: Target B must resolve to a distinct run, report, snapshot, window, or broader scope"
        )
        return gates
    if not _screen3_comparison_inputs(payload):
        gates.append(
            "capability gap: structured comparison payload missing for resolved targets"
        )
    gates.append(
        "capability gap: comparison artifact lifecycle and Screen 4 handoff are not connected for this dashboard request"
    )
    return gates


def _screen3_comparison_target_from_payload(
    payload: dict[str, Any],
    suffix: str,
) -> dict[str, Any]:
    prefix = f"selectedComparisonTarget{suffix}"
    target_value = _screen3_optional_text(payload.get(prefix))
    source_type = _screen3_optional_text(payload.get(f"{prefix}SourceType"))
    scope_type = _screen3_optional_text(payload.get(f"{prefix}ScopeType"))
    scope_value = _screen3_optional_text(payload.get(f"{prefix}ScopeValue"))
    time_window = _screen3_optional_text(payload.get(f"{prefix}TimeWindow"))
    readiness_state = str(payload.get(f"{prefix}ReadinessState") or "").strip()
    missing_gates = _screen3_target_missing_gates_from_payload(payload.get(f"{prefix}MissingGates"))
    awr_count = _screen3_count_from_payload(payload.get(f"{prefix}AwrCount"))
    snapshot_count = _screen3_count_from_payload(payload.get(f"{prefix}SnapshotCount"))
    has_target = any((target_value, source_type, scope_type, scope_value, time_window))
    if has_target and readiness_state == "comparable":
        if awr_count <= 0:
            readiness_state = "unavailable"
            missing_gates.append(f"Target {suffix} resolved AWR count is 0")
        elif snapshot_count <= 0 and scope_type not in {
            "application",
            "db_name",
            "dbid",
            "instance",
            "host",
            "system",
            "fleet_group",
            "cluster_context",
            "similar_awr_set",
        }:
            readiness_state = "analysis_required"
            missing_gates.append(f"Target {suffix} resolved snapshot/window count is 0")
    return {
        "has_target": has_target,
        "target_value": target_value,
        "source_type": source_type,
        "scope_type": scope_type,
        "scope_value": scope_value,
        "time_window": time_window,
        "readiness_state": readiness_state or ("comparable" if target_value and not missing_gates else ""),
        "missing_gates": "; ".join(missing_gates),
        "awr_count": awr_count,
        "snapshot_count": snapshot_count,
    }


def _screen3_count_from_payload(value: Any) -> int:
    try:
        return int(str(value or "0").strip())
    except (TypeError, ValueError):
        return 0


def _screen3_target_missing_gates_from_payload(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    text = str(value or "").strip()
    if not text:
        return []
    return [item.strip() for item in re.split(r"[;\n]+", text) if item.strip()]


def _screen3_reanalysis_request_from_dashboard_request(
    request: DashboardRuntimeActionRequest,
    requested_action: str,
):
    from src.learning.screen3_reanalysis_request import (
        BackendReAnalysisRequest,
        Screen3SelectedState,
    )

    payload = request.payload
    selected_state = Screen3SelectedState(
        selected_state_id=f"SCREEN3-SELECTED-STATE-{_normalize_token(request.request_id)}",
        selected_awr=_screen3_optional_text(payload.get("selectedAwr")),
        selected_run=_screen3_optional_text(
            payload.get("selectedRun") or payload.get("selectedRunReference")
        ),
        selected_database=_screen3_optional_text(
            payload.get("selectedDb") or payload.get("selectedDatabase")
        ),
        selected_system=_screen3_optional_text(
            payload.get("selectedSystem") or payload.get("selectedHost")
        ),
        selected_snapshot=_screen3_optional_text(payload.get("selectedSnapshot")),
        selected_comparison_baseline=_screen3_optional_text(
            payload.get("selectedComparisonBaseline")
        ),
        selected_issue_domain=_screen3_normalized_domain(payload.get("selectedDomain")),
        selected_severity_status=_screen3_optional_text(payload.get("selectedSeverity")),
        selected_source_mode=_screen3_source_mode(payload),
        selected_execution_mode="local_backend_execution",
        selected_object_storage_reference=_screen3_optional_text(
            payload.get("objectStorageObjectName")
        ),
        selected_local_source_reference=_screen3_optional_text(
            payload.get("selectedSourcePath") or payload.get("selectedLocalFileName")
        ),
        selected_existing_run_reference=_screen3_optional_text(
            payload.get("selectedRunReference")
        ),
        notes="Screen 3 selected state submitted through governed dashboard service.",
    )
    return BackendReAnalysisRequest(
        request_id=request.request_id,
        requested_action=requested_action,
        selected_state=selected_state,
        source_selection=_screen3_source_selection_payload(payload, request.actor_id),
        backend_execution_request={
            "request_id": request.request_id,
            "execution_mode": "local_backend_execution",
            "requested_action": requested_action,
            "target_screen": "screen_3",
            "deterministic_default": True,
            "adaptive_runtime_requested": False,
            "requires_validation": True,
            "requires_actor": True,
            "requires_audit": True,
        },
        actor_audit_context=_screen3_actor_audit_context(request),
        execution_mode="local_backend_execution",
        adaptive_runtime_requested=False,
        deterministic_default=True,
        requires_validation=True,
        requires_actor=True,
        requires_source_validation=True,
        requires_backend_execution_validation=True,
        phase4i_contract_required=True,
        created_at=request.requested_at,
        notes="Governed Screen 3 runtime-control request.",
    )


def _screen3_source_selection_payload(
    payload: dict[str, Any],
    actor_id: str,
) -> dict[str, Any]:
    mode = _screen3_source_mode(payload)
    source_label = (
        payload.get("selectedSourcePath")
        or payload.get("selectedLocalFileName")
        or payload.get("selectedRunReference")
        or payload.get("objectStorageObjectName")
        or mode
    )
    selection: dict[str, Any] = {
        "source_selection_id": f"SCREEN3-SOURCE-SELECTION-{_normalize_token(mode)}-{_normalize_token(source_label)}",
        "source_mode": mode,
        "source_label": _screen3_optional_text(source_label),
        "selected_by_actor_id": actor_id,
        "validation_status": "VALID_METADATA_ONLY",
        "notes": "Source context received from index handoff.",
    }
    if mode in {"local_staged", "local_file"}:
        selected_path = payload.get("selectedSourcePath")
        file_name = payload.get("selectedLocalFileName") or selected_path
        selection["local_source"] = {
            "local_source_id": f"LOCAL-SOURCE-{_normalize_token(file_name or selected_path or mode)}",
            "local_path": _screen3_optional_text(selected_path),
            "file_name": _screen3_optional_text(file_name),
            "expected_file_type": "awr",
            "exists_hint": None,
            "notes": "Local source metadata only; browser did not upload file contents.",
        }
    elif mode == "existing_run":
        run_ref = payload.get("selectedRunReference")
        selection["existing_run_source"] = {
            "run_source_id": f"EXISTING-RUN-SOURCE-{_normalize_token(run_ref)}",
            "run_id": _screen3_optional_text(run_ref),
            "awr_id": _screen3_optional_text(payload.get("selectedAwr")),
            "dbid": _screen3_optional_text(payload.get("selectedDbid") or payload.get("dbid")),
            "database_name": _screen3_optional_text(payload.get("selectedDb")),
            "snapshot_label": _screen3_optional_text(payload.get("selectedSnapshot")),
            "notes": "Existing run reference from governed index lookup.",
        }
    elif mode == "object_storage":
        selection["object_storage_source"] = {
            "object_source_id": (
                f"OBJECT-SOURCE-{_normalize_token(payload.get('objectStorageNamespace'))}-"
                f"{_normalize_token(payload.get('objectStorageBucket'))}-"
                f"{_normalize_token(payload.get('objectStorageObjectName'))}-"
                f"{_normalize_token(payload.get('objectStorageRegion'))}"
            ),
            "namespace": str(payload.get("objectStorageNamespace") or "").strip(),
            "bucket": str(payload.get("objectStorageBucket") or "").strip(),
            "object_name": str(payload.get("objectStorageObjectName") or "").strip(),
            "region": str(payload.get("objectStorageRegion") or "").strip(),
            "credential_mode": "unknown",
            "configured_hint": True,
            "notes": "Object Storage metadata validated through index/service path.",
        }
    return selection


def _screen3_actor_audit_context(
    request: DashboardRuntimeActionRequest,
) -> dict[str, Any]:
    return {
        "audit_context_id": f"ACTOR-AUDIT-{_normalize_token(request.actor_id)}-SCREEN3-RUNTIME-CONTROL",
        "actor_id": request.actor_id,
        "display_name": str(
            request.payload.get("reviewer")
            or request.payload.get("reviewer_actor_id")
            or request.actor_id
        ),
        "role": "operator",
        "actor_source": "dashboard",
        "permission_scope": "execute",
        "authenticated": False,
        "audit_reference": None,
        "action_scope": "screen3_runtime_control",
        "notes": "Actor identity metadata only; authorization is not inferred from this context.",
    }


def _screen3_rollback_reference(
    request: DashboardRuntimeActionRequest,
    audit_reference: Path,
) -> str:
    existing = (
        request.payload.get("selectedRunReference")
        or request.payload.get("selectedRun")
        or request.target_id
    )
    return f"existing-truth-unchanged:{_normalize_token(existing)}:{audit_reference.name}"


def _screen3_comparison_inputs(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_inputs = payload.get("comparison_inputs") or payload.get("comparisonInputs") or []
    if not isinstance(raw_inputs, list):
        return []
    return [item for item in raw_inputs if isinstance(item, dict)]


def _screen3_first_output_reference(result_dict: dict[str, Any]) -> str | None:
    refs = result_dict.get("output_references")
    if isinstance(refs, list):
        for ref in refs:
            if isinstance(ref, dict):
                value = ref.get("artifact_reference") or ref.get("output_reference_id")
                if value:
                    return str(value)
    return None


def _screen3_optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _screen3_normalized_domain(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    if text in {"CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG"}:
        return text
    if text == "I/O":
        return "IO"
    return None


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


def load_screen3_runtime_options(
    payload: dict[str, Any],
    *,
    queue_dir: Path | None = None,
    connection_factory: Any | None = None,
) -> dict[str, Any]:
    """Load DB-backed Screen 3 runtime selector options through the governed service."""

    try:
        _validate_screen3_runtime_options_request(payload)
    except DashboardRuntimeInteractionError as exc:
        result = _source_service_rejection("screen3-runtime-options", str(exc))
        result.update(
            {
                "runtime_options_loaded": False,
                "options": _empty_screen3_runtime_options(),
                "option_count": 0,
                "target_resolution": {
                    "target_model": (
                        "source_type + scope_type + scope_value + time_window + "
                        "resolution_state + readiness_state"
                    ),
                    "target_scope_options": [],
                    "comparison_target_resolutions": [],
                },
                "comparison_readiness": {
                    "target_a_readiness": "blocked",
                    "target_b_readiness": "blocked",
                    "both_targets_comparable": False,
                    "missing_gates": ["invalid Screen 3 runtime options request"],
                    "status": "blocked",
                    "next_step": "Submit a governed Screen 3 runtime options request.",
                },
                "missing_gates": ["invalid Screen 3 runtime options request"],
            }
        )
        return result

    managed_connection = True
    connection = None
    limit = _normalize_limit(payload.get("limit"), default=250, maximum=500)
    try:
        if connection_factory is not None:
            connection = connection_factory()
        else:
            from src.ingest.awr_adb_loader import get_db_connection

            connection = get_db_connection()
        source_table_coverage = _query_screen3_runtime_source_table_coverage(connection)
        run_history_error = None
        report_error = None
        try:
            run_history_runs = _query_existing_runs(connection, limit=limit)
        except Exception as exc:  # noqa: BLE001 - optional source table may be absent
            run_history_runs = []
            run_history_error = exc
        try:
            report_runs = _query_awr_report_runtime_options(connection, limit=limit)
        except Exception as exc:  # noqa: BLE001 - optional source table may be absent
            report_runs = []
            report_error = exc
        _mark_screen3_runtime_source_table(
            source_table_coverage,
            table_name="AWR_RUN_HISTORY",
            returned_count=len(run_history_runs),
            included=bool(run_history_runs),
            error=run_history_error,
        )
        _mark_screen3_runtime_source_table(
            source_table_coverage,
            table_name="AWR_REPORT",
            returned_count=len(report_runs),
            included=bool(report_runs),
            error=report_error,
        )
        runs = _merge_screen3_runtime_option_runs(
            run_history_runs,
            report_runs,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001 - service reports unavailable without mutation
        source_table_coverage = _empty_screen3_runtime_source_table_coverage(
            reason=f"DB connection unavailable: {type(exc).__name__}: {exc}"
        )
        return {
            "status": "pending",
            "validation_status": "unavailable",
            "request_id": build_request_id(
                "screen_3",
                "screen3_load_runtime_options",
                "runtime-options",
                _utc_now(),
            ),
            "audit_reference": None,
            "message": (
                "Screen 3 runtime options are unavailable because the governed workflow service "
                "could not query DB-backed run history. "
                f"Runtime options unavailable: {type(exc).__name__}: {exc}"
            ),
            "service_status": "available",
            "runtime_options_loaded": False,
            "options": _empty_screen3_runtime_options(),
            "option_count": 0,
            "metadata": {
                "option_count": 0,
                "generated_at": _utc_now(),
                "source": "AWR_RUN_HISTORY,AWR_REPORT",
                "runtime_options_source_tables": source_table_coverage,
                "runtime_options_source_note": (
                    "Screen 3 could not query DB-backed runtime option tables because DB connectivity "
                    "or service configuration is unavailable."
                ),
                "runtime_options_filters_used": _screen3_runtime_options_filters_used(payload, limit=limit),
                "runtime_options_rows_returned": 0,
                "runtime_options_query_limit": limit,
                "fallback_used": False,
                "missing_gates": [
                    "DB-backed runtime options unavailable",
                    "existing AWR/run list unavailable",
                    "comparison candidates unavailable",
                ],
            },
            "target_resolution": {
                "target_model": (
                    "source_type + scope_type + scope_value + time_window + "
                    "resolution_state + readiness_state"
                ),
                "target_scope_options": [],
                "comparison_target_resolutions": [],
            },
            "comparison_readiness": {
                "target_a_readiness": "unavailable",
                "target_b_readiness": "unavailable",
                "both_targets_comparable": False,
                "missing_gates": [
                    "DB-backed runtime options unavailable",
                    "target resolution unavailable",
                ],
                "status": "blocked",
                "next_step": "Restore DB-backed runtime options before comparison target resolution.",
            },
            "runs": [],
            "run_count": 0,
            "persisted": False,
            "queued": False,
            "db_persistence_status": "unavailable",
            "service_db_query_performed": False,
            "browser_db_query_performed": False,
            "browser_object_storage_access_performed": False,
            "current_run_truth_mutated": False,
            "deterministic_truth_changed": False,
            "parser_mutated": False,
            "learning_candidate_created": False,
            "materialization_changed": False,
            "runtime_eligibility_changed": False,
            "phase4i_mutated": False,
            "phase8_behavior": False,
            "phase8_started": False,
            "llm_changed_status": False,
            "llm_changed_validation": False,
            "llm_changed_execution": False,
            "llm_changed_truth": False,
            "missing_gates": [
                "DB-backed runtime options unavailable",
                "existing AWR/run list unavailable",
                "comparison candidates unavailable",
            ],
            "runtime_options_source_tables": source_table_coverage,
            "runtime_options_filters_used": _screen3_runtime_options_filters_used(payload, limit=limit),
        }
    finally:
        if managed_connection and connection is not None:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

    options = _build_screen3_runtime_options(runs, payload)
    option_count = sum(len(value) for value in options.values() if isinstance(value, list))
    validation_status = "valid" if runs else "empty"
    missing_gates = _screen3_runtime_option_missing_gates(options, runs)
    source_note = _screen3_runtime_source_note(source_table_coverage, runs)
    comparison_readiness = _screen3_comparison_readiness_from_target_options(
        options.get("target_scope_options") or []
    )
    request_id = build_request_id(
        "screen_3",
        "screen3_load_runtime_options",
        "runtime-options",
        _utc_now(),
    )
    audit_reference = _write_source_service_audit(
        queue_dir=queue_dir,
        request_id=request_id,
        record_type="screen3_runtime_options_lookup",
        payload=payload,
        result={
            "run_count": len(runs),
            "option_count": option_count,
            "missing_gates": missing_gates,
            "runtime_options_source_tables": source_table_coverage,
        },
    )
    return {
        "status": "accepted",
        "validation_status": validation_status,
        "request_id": request_id,
        "audit_reference": str(audit_reference),
        "message": (
            f"Screen 3 runtime options loaded from {len(runs)} DB-backed row(s). {source_note}"
            if runs
            else f"No DB-backed AWR runs were found for Screen 3 runtime selection. {source_note}"
        ),
        "service_status": "available",
        "runtime_options_loaded": bool(runs),
        "options": options,
        "option_count": option_count,
        "metadata": {
            "option_count": option_count,
            "generated_at": _utc_now(),
            "source": "AWR_RUN_HISTORY,AWR_REPORT",
            "runtime_options_source_tables": source_table_coverage,
            "runtime_options_source_note": source_note,
            "runtime_options_filters_used": _screen3_runtime_options_filters_used(payload, limit=limit),
            "runtime_options_rows_returned": len(runs),
            "runtime_options_query_limit": limit,
            "fallback_used": False,
            "missing_gates": missing_gates,
        },
        "target_resolution": {
            "target_model": (
                "source_type + scope_type + scope_value + time_window + "
                "resolution_state + readiness_state"
            ),
            "target_scope_options": options.get("target_scope_options") or [],
            "comparison_target_resolutions": options.get("comparison_target_resolutions") or [],
        },
        "comparison_readiness": comparison_readiness,
        "runs": runs,
        "run_count": len(runs),
        "persisted": True,
        "queued": True,
        "db_persistence_status": "available",
        "service_db_query_performed": True,
        "browser_db_query_performed": False,
        "browser_object_storage_access_performed": False,
        "current_run_truth_mutated": False,
        "deterministic_truth_changed": False,
        "parser_mutated": False,
        "learning_candidate_created": False,
        "materialization_changed": False,
        "runtime_eligibility_changed": False,
        "phase4i_mutated": False,
        "phase8_behavior": False,
        "phase8_started": False,
        "llm_changed_status": False,
        "llm_changed_validation": False,
        "llm_changed_execution": False,
        "llm_changed_truth": False,
        "missing_gates": missing_gates,
        "runtime_options_source_tables": source_table_coverage,
        "runtime_options_source_note": source_note,
        "runtime_options_filters_used": _screen3_runtime_options_filters_used(payload, limit=limit),
        "runtime_options_rows_returned": len(runs),
        "runtime_options_query_limit": limit,
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


SCREEN3_RUNTIME_TARGET_TYPES = (
    "backend_execution_request",
    "screen3_runtime_action",
    "source_execution_request",
    "reanalysis_request",
    "dashboard_control",
)


def _validate_screen3_runtime_action_payload(
    request: DashboardRuntimeActionRequest,
) -> None:
    payload = request.payload
    if request.action_type != "screen3_active_reanalysis":
        raise DashboardRuntimeInteractionError(
            f"action_type {request.action_type!r} is not a Screen 3 runtime action"
        )
    if request.target_type not in SCREEN3_RUNTIME_TARGET_TYPES:
        raise DashboardRuntimeInteractionError(
            "target_type for Screen 3 runtime action must be one of "
            + ", ".join(SCREEN3_RUNTIME_TARGET_TYPES)
        )
    _require_text(request.actor_id, "actor_id")
    _require_text(request.target_id, "target_id")
    _require_supported(
        _screen3_requested_action(payload),
        SCREEN3_RUNTIME_ACTIONS,
        "payload.requested_screen3_action",
    )
    _require_supported(
        request.execution_mode,
        SCREEN3_APPROVED_EXECUTION_MODES,
        "execution_mode",
    )
    _require_supported(_screen3_source_mode(payload), INDEX_SOURCE_MODES, "payload.selectedSourceMode")
    target_screen = str(payload.get("target_screen") or "").strip()
    if target_screen not in {"", "screen3", "screen_3"}:
        raise DashboardRuntimeInteractionError(
            "payload.target_screen must remain screen3 for Screen 3 runtime actions"
        )
    _validate_screen3_source_context(payload)
    _require_text(
        payload.get("reviewer_actor_id") or payload.get("actor_id") or request.actor_id,
        "payload.reviewer_actor_id",
    )
    forbidden_true_fields = (
        "runtime_influence_granted",
        "runtime_activation_granted",
        "current_run_truth_mutated",
        "deterministic_truth_changed",
        "diagnostic_truth_mutation_requested",
        "diagnostic_truth_mutation_allowed",
        "phase4i_mutation_requested",
        "phase4i_mutation_allowed",
        "score_mutation_requested",
        "score_mutation_allowed",
        "recommendation_mutation_requested",
        "recommendation_truth_mutation_allowed",
        "parser_output_mutation_requested",
        "parser_output_mutation_allowed",
        "direct_parser_mutation_allowed",
        "parser_mutated",
        "learning_candidate_created",
        "candidate_created",
        "materialization_created",
        "materialization_changed",
        "runtime_eligibility_changed",
        "browser_db_query_attempted",
        "browser_object_storage_access_attempted",
        "browser_file_read_attempted",
        "browser_file_upload_performed",
        "browser_parsing_performed",
        "direct_object_storage_execution_attempted",
        "run_analysis_coupling",
        "phase8_behavior",
        "phase8_started",
        "em_extract_attempted",
        "llm_changed_status",
        "llm_changed_validation",
        "llm_changed_execution",
        "llm_changed_truth",
        "llm_changed_service_behavior",
    )
    for field_name in forbidden_true_fields:
        if payload.get(field_name) is True:
            raise DashboardRuntimeInteractionError(
                f"payload.{field_name} must remain false for Screen 3 runtime control"
            )
    _reject_source_secret_fields(payload)


def _validate_screen3_source_context(payload: dict[str, Any]) -> None:
    mode = _screen3_source_mode(payload)
    method = str(payload.get("sourceSelectionMethod") or payload.get("source_selection_method") or "").strip()
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
                "payload.existingRunLookupStatus must be valid before Screen 3 existing-run action"
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
                "payload.objectStorageValidationStatus must be valid before Screen 3 Object Storage action"
            )


def _screen3_requested_action(payload: dict[str, Any]) -> str:
    return str(
        payload.get("requested_screen3_action")
        or payload.get("requestedScreen3Action")
        or payload.get("requested_action")
        or payload.get("screen3_action")
        or ""
    ).strip()


def _screen3_source_mode(payload: dict[str, Any]) -> str:
    return str(
        payload.get("selectedSourceMode")
        or payload.get("selected_source_mode")
        or payload.get("source_mode")
        or ""
    ).strip()


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


def _validate_screen3_runtime_options_request(payload: dict[str, Any]) -> None:
    _require_mapping(payload, "payload")
    if str(payload.get("screen_id") or "").strip() != "screen_3":
        raise DashboardRuntimeInteractionError("payload.screen_id must be screen_3")
    if str(payload.get("action_type") or "").strip() != "screen3_load_runtime_options":
        raise DashboardRuntimeInteractionError(
            "payload.action_type must be 'screen3_load_runtime_options'"
        )
    target_screen = str(payload.get("target_screen") or "screen3").strip()
    if target_screen not in {"screen3", "screen_3"}:
        raise DashboardRuntimeInteractionError("payload.target_screen must be screen3")
    for field_name in (
        "direct_truth_mutation_allowed",
        "phase4i_mutation_allowed",
        "phase8_behavior",
        "phase8_started",
        "run_analysis_coupling",
        "browser_db_query_attempted",
        "browser_object_storage_access_attempted",
        "direct_object_storage_execution_attempted",
        "em_extract_attempted",
        "current_run_truth_mutated",
        "deterministic_truth_changed",
        "parser_mutated",
        "learning_candidate_created",
        "materialization_changed",
        "runtime_eligibility_changed",
    ):
        if payload.get(field_name) is True:
            raise DashboardRuntimeInteractionError(f"payload.{field_name} must remain false")
    _reject_source_secret_fields(payload)
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
                   ANALYSIS_RUN_ID,
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
        record["source_table"] = "AWR_RUN_HISTORY"
        record["source_table_label"] = "AWR_RUN_HISTORY"
        record["snapshot_count"] = 1 if (
            record.get("awr_begin_time") or record.get("awr_end_time")
        ) else 0
        record["readiness_state"] = (
            "comparable" if record["snapshot_count"] else "analysis_required"
        )
        results.append(record)
    return results


SCREEN3_RUNTIME_OPTION_SOURCE_TABLES = (
    "AWR_RUN_HISTORY",
    "AWR_REPORT",
    "AWR_SNAPSHOT",
    "AWR_INGEST_RUN",
    "AWR_SOURCE_SYSTEM",
    "AWR_RECOMMENDATION_HISTORY",
    "AWR_ACTION_HISTORY",
    "AWR_OUTCOME_HISTORY",
    "AWR_METRIC_FACT",
    "AWR_WAIT_EVENT_FACT",
    "AWR_TOP_SQL_FACT",
    "AWR_FEATURE_VECTOR",
)

SCREEN3_RUNTIME_OPTION_SOURCE_TABLE_KEY_COLUMNS: dict[str, tuple[str, ...]] = {
    "AWR_RUN_HISTORY": (
        "RUN_HISTORY_ID",
        "SOURCE_FILE_NAME",
        "DB_NAME",
        "DBID",
        "INSTANCE_NAME",
        "AWR_BEGIN_TIME",
        "AWR_END_TIME",
    ),
    "AWR_REPORT": (
        "AWR_ID",
        "SOURCE_SYSTEM_ID",
        "SOURCE_FILE_NAME",
        "DB_NAME",
        "DBID",
        "INSTANCE_NAME",
        "HOST_NAME",
        "SNAP_ID_BEGIN",
        "SNAP_ID_END",
        "SNAP_TIME_BEGIN",
        "SNAP_TIME_END",
    ),
    "AWR_SNAPSHOT": (
        "DBID",
        "INSTANCE_NAME",
        "SNAP_ID",
        "BEGIN_INTERVAL_TIME",
        "END_INTERVAL_TIME",
    ),
    "AWR_INGEST_RUN": (
        "INGEST_RUN_ID",
        "SOURCE_SYSTEM_ID",
        "STATUS",
        "CREATED_AT",
    ),
    "AWR_SOURCE_SYSTEM": (
        "SOURCE_SYSTEM_ID",
        "APPLICATION_NAME",
        "SOURCE_SYSTEM_CODE",
        "PRIMARY_HOST_NAME",
    ),
    "AWR_METRIC_FACT": (
        "AWR_ID",
        "SOURCE_SYSTEM_ID",
        "SNAP_TIME_BEGIN",
        "SNAP_TIME_END",
        "METRIC_DOMAIN",
        "METRIC_NAME",
        "METRIC_VALUE_NUM",
    ),
    "AWR_WAIT_EVENT_FACT": (
        "AWR_ID",
        "SOURCE_SYSTEM_ID",
        "SNAP_TIME_BEGIN",
        "SNAP_TIME_END",
        "EVENT_NAME",
        "WAIT_CLASS",
    ),
    "AWR_TOP_SQL_FACT": (
        "AWR_ID",
        "SOURCE_SYSTEM_ID",
        "SNAP_TIME_BEGIN",
        "SNAP_TIME_END",
        "SQL_ID",
        "ELAPSED_TIME_SEC",
    ),
    "AWR_FEATURE_VECTOR": (
        "AWR_ID",
        "SOURCE_SYSTEM_ID",
        "OBSERVED_AT",
        "FEATURE_SET_NAME",
        "VECTOR_STATUS",
    ),
    "AWR_RECOMMENDATION_HISTORY": (
        "RECOMMENDATION_HISTORY_ID",
        "RUN_HISTORY_ID",
        "RECOMMENDATION_ID",
        "CREATED_AT",
    ),
    "AWR_ACTION_HISTORY": (
        "ACTION_HISTORY_ID",
        "RUN_HISTORY_ID",
        "ACTION_ID",
        "CREATED_AT",
    ),
    "AWR_OUTCOME_HISTORY": (
        "OUTCOME_HISTORY_ID",
        "RUN_HISTORY_ID",
        "OUTCOME_ID",
        "CREATED_AT",
    ),
}


def _query_awr_report_runtime_options(connection: Any, *, limit: int) -> list[dict[str, Any]]:
    joined_query = """
        SELECT r.AWR_ID,
               r.SOURCE_FILE_NAME,
               r.DB_NAME,
               r.DBID,
               r.INSTANCE_NAME,
               r.HOST_NAME,
               r.SNAP_TIME_BEGIN,
               r.SNAP_TIME_END,
               r.PARSE_STATUS,
               r.CREATED_AT,
               r.SNAP_ID_BEGIN,
               r.SNAP_ID_END,
               s.APPLICATION_NAME,
               s.SOURCE_SYSTEM_CODE,
               r.INGEST_RUN_ID
          FROM AWR_REPORT r
          LEFT JOIN AWR_SOURCE_SYSTEM s
            ON s.SOURCE_SYSTEM_ID = r.SOURCE_SYSTEM_ID
         ORDER BY r.SNAP_TIME_END DESC NULLS LAST,
                  r.AWR_ID DESC
         FETCH FIRST :limit ROWS ONLY
    """
    fallback_query = """
        SELECT r.AWR_ID,
               r.SOURCE_FILE_NAME,
               r.DB_NAME,
               r.DBID,
               r.INSTANCE_NAME,
               r.HOST_NAME,
               r.SNAP_TIME_BEGIN,
               r.SNAP_TIME_END,
               r.PARSE_STATUS,
               r.CREATED_AT,
               r.SNAP_ID_BEGIN,
               r.SNAP_ID_END,
               CAST(NULL AS VARCHAR2(256)) AS APPLICATION_NAME,
               CAST(NULL AS VARCHAR2(100)) AS SOURCE_SYSTEM_CODE,
               r.INGEST_RUN_ID
          FROM AWR_REPORT r
         ORDER BY r.SNAP_TIME_END DESC NULLS LAST,
                  r.AWR_ID DESC
         FETCH FIRST :limit ROWS ONLY
    """
    rows, descriptions = _execute_screen3_runtime_option_query(
        connection,
        joined_query,
        fallback_query=fallback_query,
        limit=limit,
    )
    column_names = [str(item[0]).lower() for item in descriptions]
    if "awr_id" not in column_names:
        return []
    results: list[dict[str, Any]] = []
    for row in rows:
        record = {
            column: _json_safe(value)
            for column, value in zip(column_names, row, strict=False)
        }
        awr_id = str(record.get("awr_id") or "").strip()
        if not awr_id:
            continue
        record["report_id"] = awr_id
        record["run_reference"] = f"AWR_ID:{awr_id}"
        record["run_history_id"] = None
        record["analysis_run_id"] = None
        record["awr_begin_time"] = record.get("snap_time_begin")
        record["awr_end_time"] = record.get("snap_time_end")
        record["application"] = record.get("application_name")
        record["source_table"] = "AWR_REPORT"
        record["source_table_label"] = "AWR_REPORT"
        record["snapshot_count"] = 1 if (
            record.get("snap_time_begin") or record.get("snap_time_end")
        ) else 0
        record["readiness_state"] = (
            "comparable" if record["snapshot_count"] else "analysis_required"
        )
        results.append(record)
    return results


def _execute_screen3_runtime_option_query(
    connection: Any,
    query: str,
    *,
    fallback_query: str | None = None,
    limit: int,
) -> tuple[list[Any], Any]:
    with connection.cursor() as cursor:
        try:
            cursor.execute(query, {"limit": limit})
        except Exception:
            if fallback_query is None:
                raise
            cursor.execute(fallback_query, {"limit": limit})
        rows = cursor.fetchall()
        descriptions = cursor.description or []
    return rows, descriptions


def _merge_screen3_runtime_option_runs(
    run_history_runs: list[dict[str, Any]],
    report_runs: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for run in [*run_history_runs, *report_runs]:
        source_table = str(run.get("source_table") or "UNKNOWN").strip()
        identity = str(
            run.get("run_reference")
            or run.get("report_id")
            or run.get("run_history_id")
            or run.get("source_file_name")
            or ""
        ).strip()
        key = (source_table, identity)
        if not identity or key in seen:
            continue
        seen.add(key)
        merged.append(run)
        if len(merged) >= limit:
            break
    return merged


def _empty_screen3_runtime_source_table_coverage(reason: str = "not checked") -> list[dict[str, Any]]:
    return [
        {
            "table_name": table_name,
            "table_exists": "unknown",
            "queried": False,
            "row_count": None,
            "included_in_options": False,
            "included_in_screen3_runtime_options": False,
            "returned_option_count": 0,
            "selectable_row_count": 0,
            "key_columns_used": list(
                SCREEN3_RUNTIME_OPTION_SOURCE_TABLE_KEY_COLUMNS.get(table_name, ())
            ),
            "columns_found": [],
            "missing_columns": list(
                SCREEN3_RUNTIME_OPTION_SOURCE_TABLE_KEY_COLUMNS.get(table_name, ())
            ),
            "application_non_null_count": None,
            "reason_if_not_used": reason,
        }
        for table_name in SCREEN3_RUNTIME_OPTION_SOURCE_TABLES
    ]


def _query_screen3_runtime_source_table_coverage(connection: Any) -> list[dict[str, Any]]:
    coverage = _empty_screen3_runtime_source_table_coverage("not queried for options")
    for entry in coverage:
        table_name = str(entry["table_name"])
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}", {})
                row = cursor.fetchone()
            entry["table_exists"] = "yes"
            entry["queried"] = True
            entry["row_count"] = int(row[0]) if row and row[0] is not None else 0
            columns = _query_screen3_table_columns(connection, table_name)
            expected_columns = [
                str(column).upper()
                for column in SCREEN3_RUNTIME_OPTION_SOURCE_TABLE_KEY_COLUMNS.get(table_name, ())
            ]
            entry["columns_found"] = columns
            entry["missing_columns"] = [
                column for column in expected_columns if column not in set(columns)
            ]
            if table_name == "AWR_SOURCE_SYSTEM" and "APPLICATION_NAME" in set(columns):
                entry["application_non_null_count"] = _query_screen3_table_non_null_count(
                    connection,
                    table_name,
                    "APPLICATION_NAME",
                )
            entry["reason_if_not_used"] = "table counted; not included in runtime options"
        except Exception as exc:  # noqa: BLE001 - source table may not exist in all deployments
            error_text = str(exc).lower()
            entry["table_exists"] = (
                "no"
                if "ora-00942" in error_text or "does not exist" in error_text
                else "unknown"
            )
            entry["queried"] = True
            entry["row_count"] = None
            entry["columns_found"] = []
            entry["missing_columns"] = list(entry.get("key_columns_used") or [])
            entry["reason_if_not_used"] = f"count unavailable: {type(exc).__name__}"
    return coverage


def _query_screen3_table_columns(connection: Any, table_name: str) -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COLUMN_NAME
              FROM USER_TAB_COLUMNS
             WHERE TABLE_NAME = :table_name
             ORDER BY COLUMN_ID
            """,
            {"table_name": table_name.upper()},
        )
        rows = cursor.fetchall()
    return [str(row[0]).upper() for row in rows if row and row[0]]


def _query_screen3_table_non_null_count(
    connection: Any,
    table_name: str,
    column_name: str,
) -> int | None:
    safe_table = "".join(ch for ch in table_name.upper() if ch.isalnum() or ch == "_")
    safe_column = "".join(ch for ch in column_name.upper() if ch.isalnum() or ch == "_")
    if safe_table != table_name.upper() or safe_column != column_name.upper():
        return None
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) FROM {safe_table} WHERE {safe_column} IS NOT NULL",
                {},
            )
            row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception:  # noqa: BLE001 - optional diagnostic only
        return None


def _mark_screen3_runtime_source_table(
    coverage: list[dict[str, Any]],
    *,
    table_name: str,
    returned_count: int,
    included: bool,
    error: Exception | None,
) -> None:
    entry = next(
        (item for item in coverage if item.get("table_name") == table_name),
        None,
    )
    if entry is None:
        return
    entry["queried"] = True
    entry["returned_option_count"] = int(returned_count)
    entry["selectable_row_count"] = int(returned_count)
    entry["included_in_options"] = bool(included)
    entry["included_in_screen3_runtime_options"] = bool(included)
    if error is not None:
        entry["reason_if_not_used"] = f"option query unavailable: {type(error).__name__}: {error}"
    elif included:
        entry["reason_if_not_used"] = "included in Screen 3 runtime options"
    elif entry.get("row_count") == 0:
        entry["reason_if_not_used"] = "no rows found"
    else:
        entry["reason_if_not_used"] = "query returned no selectable Screen 3 rows"


def _screen3_runtime_source_note(
    coverage: list[dict[str, Any]],
    runs: list[dict[str, Any]],
) -> str:
    row_count = len(runs)
    included = [
        str(item.get("table_name"))
        for item in coverage
        if item.get("included_in_options")
    ]
    included_text = ", ".join(included) if included else "no source tables"
    wired_tables = {"AWR_RUN_HISTORY", "AWR_REPORT"}
    counted_supporting_tables = [
        f"{item.get('table_name')} ({item.get('row_count')} row(s))"
        for item in coverage
        if not item.get("included_in_options")
        and isinstance(item.get("row_count"), int)
        and int(item.get("row_count") or 0) > 0
        and str(item.get("table_name")) not in wired_tables
    ]
    wired_but_returned_no_rows = [
        f"{item.get('table_name')} ({item.get('row_count')} row(s) counted, {item.get('returned_option_count')} selectable)"
        for item in coverage
        if str(item.get("table_name")) in wired_tables
        and not item.get("included_in_options")
        and isinstance(item.get("row_count"), int)
        and int(item.get("row_count") or 0) > 0
    ]
    unwired_text = (
        " Supporting persistence tables also contain rows but are not used as primary selectable AWR/run/report rows: "
        + ", ".join(counted_supporting_tables)
        + "."
        if counted_supporting_tables
        else ""
    )
    wired_gap_text = (
        " Wired source tables counted rows but returned no selectable Screen 3 rows: "
        + ", ".join(wired_but_returned_no_rows)
        + ". Check column availability, filters, and service query shape."
        if wired_but_returned_no_rows
        else ""
    )
    if row_count == 1:
        return (
            "1 DB-backed row returned by current service query. "
            f"Included source table(s): {included_text}.{unwired_text}{wired_gap_text}"
        )
    if row_count > 1:
        return (
            f"{row_count} DB-backed rows returned by current service query. "
            f"Included source table(s): {included_text}.{unwired_text}{wired_gap_text}"
        )
    return (
        "0 DB-backed rows returned by current service query. "
        f"Included source table(s): {included_text}.{unwired_text}{wired_gap_text}"
    )


def _screen3_runtime_options_filters_used(payload: dict[str, Any], *, limit: int) -> dict[str, Any]:
    """Describe service-side filters without exposing DB credentials or sensitive config."""

    return {
        "limit": limit,
        "application": _screen3_optional_text(payload.get("screen3RuntimeFilterApplication")),
        "db_name": _screen3_optional_text(payload.get("screen3RuntimeFilterDb") or payload.get("selectedDb")),
        "dbid": _screen3_optional_text(payload.get("screen3RuntimeFilterDbid") or payload.get("selectedDbid")),
        "instance": _screen3_optional_text(
            payload.get("screen3RuntimeFilterInstance") or payload.get("selectedInstance")
        ),
        "host": _screen3_optional_text(payload.get("screen3RuntimeFilterHost") or payload.get("selectedHost")),
        "source_type": _screen3_optional_text(payload.get("screen3RuntimeFilterSourceType")),
        "time_range": _screen3_optional_text(
            payload.get("screen3RuntimeFilterTimeRange") or payload.get("selectedTimeWindow")
        ),
        "search": _screen3_optional_text(payload.get("screen3RuntimeFilterSearch")),
        "note": (
            "Current Screen 3 runtime-options query applies the safety limit and returns selectable "
            "rows from wired runtime option sources; browser-side filters narrow the displayed list."
        ),
    }


def _empty_screen3_runtime_options() -> dict[str, list[dict[str, Any]]]:
    return {
        "applications": [],
        "databases": [],
        "dbids": [],
        "hosts": [],
        "instances": [],
        "systems": [],
        "runs": [],
        "reports": [],
        "snapshots": [],
        "intervals": [],
        "historical_windows": [],
        "comparison_candidates": [],
        "target_scope_options": [],
        "comparison_target_resolutions": [],
        "similar_awrs": [],
        "cluster_baselines": [],
        "fleet_baselines": [],
    }


def _build_screen3_runtime_options(
    runs: list[dict[str, Any]],
    payload: dict[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    options = _empty_screen3_runtime_options()
    applications: dict[str, dict[str, Any]] = {}
    databases: dict[str, dict[str, Any]] = {}
    dbids: dict[str, dict[str, Any]] = {}
    hosts: dict[str, dict[str, Any]] = {}
    instances: dict[str, dict[str, Any]] = {}
    systems: dict[str, dict[str, Any]] = {}
    run_options: list[dict[str, Any]] = []
    interval_options: list[dict[str, Any]] = []
    comparison_candidates: list[dict[str, Any]] = []

    for index, run in enumerate(runs):
        run_reference = _screen3_optional_text(
            run.get("run_reference")
            or (
                f"RUN_HISTORY_ID:{run.get('run_history_id')}"
                if _screen3_optional_text(run.get("run_history_id"))
                else None
            )
        )
        db_name = _screen3_optional_text(run.get("db_name"))
        dbid = _screen3_optional_text(run.get("dbid"))
        host_name = _screen3_optional_text(run.get("host_name") or run.get("primary_host_name"))
        instance_name = _screen3_optional_text(run.get("instance_name"))
        application = _screen3_optional_text(run.get("application") or run.get("application_name"))
        awr_begin = _screen3_optional_text(run.get("awr_begin_time") or run.get("snap_time_begin"))
        awr_end = _screen3_optional_text(run.get("awr_end_time") or run.get("snap_time_end"))
        source_file = _screen3_optional_text(run.get("source_file_name"))
        source_table = _screen3_optional_text(run.get("source_table")) or "AWR_RUN_HISTORY"
        snapshot_count = int(run.get("snapshot_count") or (1 if (awr_begin or awr_end) else 0))
        readiness_state = _screen3_optional_text(run.get("readiness_state")) or (
            "comparable" if snapshot_count else "analysis_required"
        )
        run_label = _join_screen3_option_values(
            [
                run_reference,
                db_name,
                instance_name,
                source_file,
            ]
        ) or f"DB-backed run {index + 1}"
        run_option = {
            "label": run_label,
            "value": run_reference or run_label,
            "run_reference": run_reference,
            "run_history_id": run.get("run_history_id"),
            "analysis_run_id": run.get("analysis_run_id"),
            "report_id": run.get("report_id") or run.get("awr_id"),
            "source_table": source_table,
            "source_file_name": source_file,
            "application": application,
            "db_name": db_name,
            "dbid": dbid,
            "host_name": host_name,
            "instance_name": instance_name,
            "snapshot_begin": awr_begin,
            "snapshot_end": awr_end,
            "snapshot_count": snapshot_count,
            "readiness_state": readiness_state,
            "time_window": _format_screen3_runtime_window(awr_begin, awr_end),
            "decision_posture": run.get("decision_posture"),
            "risk_level": run.get("risk_level"),
            "created_at": run.get("created_at"),
        }
        run_options.append(run_option)
        comparison_candidates.append(
            {
                **run_option,
                "label": f"Comparison candidate: {run_label}",
                "comparison_target": run_reference or run_label,
            }
        )
        if awr_begin or awr_end:
            interval_options.append(
                {
                    "label": _format_screen3_runtime_window(awr_begin, awr_end)
                    or f"Interval for {run_label}",
                    "value": _format_screen3_runtime_window(awr_begin, awr_end)
                    or run_reference
                    or run_label,
                    "run_reference": run_reference,
                    "source_table": source_table,
                    "snapshot_begin": awr_begin,
                    "snapshot_end": awr_end,
                    "db_name": db_name,
                    "dbid": dbid,
                    "snapshot_count": 1,
                    "readiness_state": readiness_state,
                }
            )
        if db_name:
            databases.setdefault(
                db_name,
                {"label": db_name, "value": db_name, "db_name": db_name, "dbid": dbid},
            )
        if application:
            applications.setdefault(
                application,
                {
                    "label": application,
                    "value": application,
                    "application": application,
                    "db_name": db_name,
                    "dbid": dbid,
                },
            )
        if dbid:
            dbids.setdefault(
                dbid,
                {"label": dbid, "value": dbid, "dbid": dbid, "db_name": db_name},
            )
        if host_name:
            hosts.setdefault(
                host_name,
                {"label": host_name, "value": host_name, "host_name": host_name},
            )
        if instance_name:
            instances.setdefault(
                instance_name,
                {
                    "label": instance_name,
                    "value": instance_name,
                    "instance_name": instance_name,
                    "db_name": db_name,
                    "dbid": dbid,
                },
            )
        system_label = _join_screen3_option_values([host_name, instance_name])
        if system_label:
            systems.setdefault(
                system_label,
                {
                    "label": system_label,
                    "value": system_label,
                    "host_name": host_name,
                    "instance_name": instance_name,
                },
            )

    options["applications"] = list(applications.values())
    options["databases"] = list(databases.values())
    options["dbids"] = list(dbids.values())
    options["hosts"] = list(hosts.values())
    options["instances"] = list(instances.values())
    options["systems"] = list(systems.values())
    options["runs"] = run_options
    options["reports"] = [
        option for option in run_options if _screen3_optional_text(option.get("report_id"))
    ]
    options["snapshots"] = interval_options
    options["intervals"] = interval_options
    options["comparison_candidates"] = comparison_candidates
    target_scope_options = _screen3_target_scope_options(run_options, payload or {})
    options["target_scope_options"] = target_scope_options
    options["comparison_target_resolutions"] = target_scope_options
    options["historical_windows"] = _screen3_historical_window_options(run_options, interval_options)
    return options


def _format_screen3_runtime_window(begin: Any, end: Any) -> str | None:
    begin_text = _screen3_optional_text(begin)
    end_text = _screen3_optional_text(end)
    if begin_text and end_text:
        return f"{begin_text} -> {end_text}"
    return begin_text or end_text


def _join_screen3_option_values(values: list[Any]) -> str | None:
    parts = [str(value).strip() for value in values if str(value or "").strip()]
    return " | ".join(parts) if parts else None


def _screen3_historical_window_options(
    runs: list[dict[str, Any]],
    intervals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    if intervals:
        latest = intervals[0]
        options.append({**latest, "label": f"Latest interval: {latest['label']}", "window_type": "latest"})
    if len(intervals) > 1:
        prior = intervals[1]
        options.append({**prior, "label": f"Prior interval: {prior['label']}", "window_type": "prior"})
    if runs:
        risk_order = {"critical": 5, "high": 4, "warning": 3, "medium": 2, "low": 1}
        worst = max(
            runs,
            key=lambda item: risk_order.get(str(item.get("risk_level") or "").lower(), 0),
        )
        if worst.get("time_window"):
            options.append(
                {
                    **worst,
                    "label": f"Worst interval candidate: {worst['time_window']}",
                    "value": worst["time_window"],
                    "window_type": "worst",
                }
            )
    if intervals:
        begin_values = [item.get("snapshot_begin") for item in intervals if item.get("snapshot_begin")]
        end_values = [item.get("snapshot_end") for item in intervals if item.get("snapshot_end")]
        if begin_values or end_values:
            full_window = _format_screen3_runtime_window(
                begin_values[-1] if begin_values else None,
                end_values[0] if end_values else None,
            )
            if full_window:
                options.append(
                    {
                        "label": f"Full window: {full_window}",
                        "value": full_window,
                        "window_type": "full",
                    }
                )
    return options


def _screen3_target_scope_options(
    runs: list[dict[str, Any]],
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build scope-based target resolution choices from persisted run history."""

    target_options: list[dict[str, Any]] = []

    def add_target(
        *,
        source_type: str,
        scope_type: str,
        scope_value: Any,
        matching_runs: list[dict[str, Any]],
        time_window: Any = None,
        label: str | None = None,
        readiness_state: str = "comparable",
        missing_gates: list[str] | None = None,
    ) -> None:
        scope_text = _screen3_optional_text(scope_value)
        if not scope_text:
            return
        windows = [
            _screen3_optional_text(run.get("time_window"))
            for run in matching_runs
            if _screen3_optional_text(run.get("time_window"))
        ]
        selected_window = _screen3_optional_text(time_window) or (windows[0] if windows else None)
        run_ids = [
            str(run.get("run_reference") or run.get("run_history_id") or run.get("analysis_run_id"))
            for run in matching_runs
            if _screen3_optional_text(
                run.get("run_reference") or run.get("run_history_id") or run.get("analysis_run_id")
            )
        ]
        report_ids = [
            str(run.get("report_id"))
            for run in matching_runs
            if _screen3_optional_text(run.get("report_id"))
        ]
        db_names = sorted(
            {
                str(run.get("db_name"))
                for run in matching_runs
                if _screen3_optional_text(run.get("db_name"))
            }
        )
        dbids = sorted(
            {
                str(run.get("dbid"))
                for run in matching_runs
                if _screen3_optional_text(run.get("dbid"))
            }
        )
        hosts = sorted(
            {
                str(run.get("host_name"))
                for run in matching_runs
                if _screen3_optional_text(run.get("host_name"))
            }
        )
        instances = sorted(
            {
                str(run.get("instance_name"))
                for run in matching_runs
                if _screen3_optional_text(run.get("instance_name"))
            }
        )
        awr_count = len(matching_runs)
        snapshot_count = len({window for window in windows if window})
        gates = list(missing_gates or [])
        if readiness_state == "comparable" and awr_count < 1:
            readiness_state = "unavailable"
            gates.append("target data does not exist in DB-backed run history")
        if readiness_state == "comparable" and snapshot_count < 1:
            readiness_state = "blocked"
            gates.append("snapshot/time-window context unavailable for target")
        resolution_state = (
            "resolved_persisted_data"
            if readiness_state == "comparable"
            else "unresolved_or_external"
        )
        resolution_summary = (
            f"{awr_count} AWR/run record(s) / {snapshot_count} snapshot window(s)"
            if awr_count or snapshot_count
            else "No persisted comparable data resolved"
        )
        value = "|".join(
            [
                source_type,
                scope_type,
                scope_text,
                selected_window or "",
            ]
        )
        target_options.append(
            {
                "label": label or f"{scope_type}: {scope_text}",
                "value": value,
                "source_type": source_type,
                "scope_type": scope_type,
                "scope_value": scope_text,
                "time_window": selected_window,
                "resolution_state": resolution_state,
                "resolution_summary": resolution_summary,
                "readiness_state": readiness_state,
                "readiness": readiness_state,
                "missing_gates": gates,
                "awr_count": awr_count,
                "snapshot_count": snapshot_count,
                "run_ids": run_ids,
                "report_ids": report_ids,
                "db_name": db_names[0] if len(db_names) == 1 else None,
                "dbid": dbids[0] if len(dbids) == 1 else None,
                "host": hosts[0] if len(hosts) == 1 else None,
                "instance": instances[0] if len(instances) == 1 else None,
                "begin_time": matching_runs[0].get("snapshot_begin") if matching_runs else None,
                "end_time": matching_runs[0].get("snapshot_end") if matching_runs else None,
            }
        )

    for run in runs:
        run_ref = _screen3_optional_text(run.get("run_reference") or run.get("value"))
        add_target(
            source_type="db_backed",
            scope_type="run",
            scope_value=run_ref,
            matching_runs=[run],
            time_window=run.get("time_window"),
            label=f"Run scope: {run_ref}",
        )
        if _screen3_optional_text(run.get("report_id")):
            add_target(
                source_type="db_backed",
                scope_type="report",
                scope_value=run.get("report_id"),
                matching_runs=[run],
                time_window=run.get("time_window"),
                label=f"Report scope: {run.get('report_id')}",
            )
        if _screen3_optional_text(run.get("time_window")):
            add_target(
                source_type="db_backed",
                scope_type="time_window",
                scope_value=run.get("time_window"),
                matching_runs=[run],
                time_window=run.get("time_window"),
                label=f"Window scope: {run.get('time_window')}",
            )

    for scope_type, field_name in (
        ("application", "application"),
        ("db_name", "db_name"),
        ("dbid", "dbid"),
        ("instance", "instance_name"),
        ("host", "host_name"),
        ("system", "host_name"),
    ):
        grouped: dict[str, list[dict[str, Any]]] = {}
        for run in runs:
            value = _screen3_optional_text(run.get(field_name))
            if value:
                grouped.setdefault(value, []).append(run)
        for value, matching in grouped.items():
            add_target(
                source_type="db_backed",
                scope_type=scope_type,
                scope_value=value,
                matching_runs=matching,
                label=f"{scope_type.replace('_', ' ').title()} scope: {value}",
            )

    target_options.extend(_screen3_external_target_scope_options(payload))
    return target_options


def _screen3_external_target_scope_options(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Represent local/Object Storage handoff context as load-required targets."""

    options: list[dict[str, Any]] = []

    def add_external(source_type: str, scope_value: Any, label: str) -> None:
        value = _screen3_optional_text(scope_value)
        if not value:
            return
        options.append(
            {
                "label": label,
                "value": f"{source_type}|external_source|{value}|",
                "source_type": source_type,
                "scope_type": "external_source",
                "scope_value": value,
                "time_window": None,
                "resolution_state": "not_persisted",
                "resolution_summary": "External source is not persisted as comparable AWR data",
                "readiness_state": "load_required",
                "readiness": "load_required",
                "missing_gates": [
                    "load/parse/ingest/analyze target before comparison",
                    "persist comparable run/report/feature context before comparison",
                ],
                "awr_count": 0,
                "snapshot_count": 0,
                "run_ids": [],
                "report_ids": [],
            }
        )

    add_external(
        "local_staged_file",
        payload.get("selectedSourcePath") or payload.get("selectedLocalFolderSampleFiles"),
        "Local staged source target",
    )
    add_external(
        "local_selected_file",
        payload.get("selectedLocalFileName"),
        "Local selected file target",
    )
    add_external(
        "object_storage_object",
        payload.get("objectStorageObjectName"),
        "Object Storage object target",
    )
    return options


def _screen3_comparison_readiness_from_target_options(
    target_options: list[dict[str, Any]],
) -> dict[str, Any]:
    comparable_count = sum(
        1
        for option in target_options
        if str(option.get("readiness_state") or "") == "comparable"
    )
    missing_gates: list[str] = []
    if comparable_count < 1:
        missing_gates.append("Target A is not resolved to comparable persisted data")
    if comparable_count < 2:
        missing_gates.append("Target B is not resolved to comparable persisted data")
    if not target_options:
        missing_gates.append("No target scope options are available")
    return {
        "target_a_readiness": "selectable" if comparable_count >= 1 else "not_resolved",
        "target_b_readiness": "selectable" if comparable_count >= 2 else "not_resolved",
        "both_targets_comparable": comparable_count >= 2,
        "missing_gates": missing_gates,
        "status": "ready_to_select" if comparable_count >= 2 else "blocked",
        "next_step": (
            "Select two comparable persisted targets, then submit Build Comparison."
            if comparable_count >= 2
            else "Resolve two comparable persisted targets before Build Comparison."
        ),
    }


def _screen3_runtime_option_missing_gates(
    options: dict[str, list[dict[str, Any]]],
    runs: list[dict[str, Any]],
) -> list[str]:
    gates: list[str] = []
    if not runs:
        gates.append("DB-backed existing AWR/run options unavailable")
    if not options.get("applications"):
        gates.append("application metadata unavailable in runtime option source tables")
    if not options.get("hosts"):
        gates.append("host/system metadata unavailable in runtime option source tables")
    if len(options.get("runs") or []) < 2:
        gates.append("second AWR/run candidate unavailable for two-AWR comparison")
    if len(options.get("intervals") or []) < 2:
        gates.append("second snapshot/window unavailable for period comparison")
    gates.extend(
        [
            "similarity candidates unavailable",
            "cluster baseline unavailable",
            "fleet baseline unavailable",
            "server-side Object Storage load-to-analysis chain unavailable",
        ]
    )
    return gates


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
        "browser_db_query_performed": False,
        "browser_object_storage_access_performed": False,
        "current_run_truth_mutated": False,
        "deterministic_truth_changed": False,
        "parser_mutated": False,
        "learning_candidate_created": False,
        "materialization_changed": False,
        "runtime_eligibility_changed": False,
        "phase4i_mutated": False,
        "phase8_behavior": False,
        "phase8_started": False,
        "llm_changed_status": False,
        "llm_changed_validation": False,
        "llm_changed_execution": False,
        "llm_changed_truth": False,
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
