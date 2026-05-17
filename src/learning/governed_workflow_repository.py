"""DB-backed governed workflow persistence repository for Phase 7CA.

The repository records workflow metadata, validation, audit, transaction, and
output artifact references. It deliberately does not execute analysis, import
runtime analysis code, regenerate dashboards, or mutate Phase 4I truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable


WORKFLOW_TRANSACTION_STATUSES = (
    "PENDING",
    "IN_PROGRESS",
    "COMMITTED",
    "FAILED",
    "DUPLICATE_REPLAY",
    "ROLLED_BACK",
)

WORKFLOW_REQUEST_STATUSES = (
    "PENDING",
    "VALIDATED",
    "FAILED",
    "COMPLETED",
    "DUPLICATE_REPLAY",
    "CANCELLED",
)

WORKFLOW_OUTPUT_ARTIFACT_TYPES = (
    "validation_response",
    "analysis_run_record",
    "phase4i_payload_reference",
    "dashboard_artifact_reference",
    "comparison_artifact",
    "error_artifact",
    "source_validation_artifact",
    "object_storage_load_artifact",
    "workflow_audit_artifact",
)

WORKFLOW_OUTPUT_STATUSES = (
    "RECORDED",
    "PENDING",
    "FAILED",
    "SUPERSEDED",
)

WORKFLOW_REQUEST_COLUMNS = (
    "WORKFLOW_REQUEST_ID",
    "TRANSACTION_GROUP_ID",
    "IDEMPOTENCY_KEY",
    "SOURCE_SCREEN",
    "WORKFLOW_TYPE",
    "REQUESTED_ACTION",
    "TARGET_TYPE",
    "TARGET_ID",
    "ACTOR_ID",
    "PAYLOAD_CLOB",
    "STATUS",
    "CREATED_AT",
    "UPDATED_AT",
    "ERROR_CLOB",
    "WARNING_CLOB",
    "NOTES",
)

WORKFLOW_TRANSACTION_COLUMNS = (
    "TRANSACTION_GROUP_ID",
    "IDEMPOTENCY_KEY",
    "TRANSACTION_SCOPE",
    "STATUS",
    "ROLLBACK_REFERENCE",
    "CREATED_AT",
    "UPDATED_AT",
    "NOTES",
)

WORKFLOW_AUDIT_COLUMNS = (
    "WORKFLOW_AUDIT_ID",
    "WORKFLOW_REQUEST_ID",
    "TRANSACTION_GROUP_ID",
    "ACTOR_ID",
    "ACTION",
    "AUDIT_SUMMARY",
    "PAYLOAD_HASH",
    "CREATED_AT",
    "NOTES",
)

WORKFLOW_OUTPUT_COLUMNS = (
    "WORKFLOW_OUTPUT_ID",
    "WORKFLOW_REQUEST_ID",
    "ARTIFACT_TYPE",
    "ARTIFACT_REFERENCE",
    "ARTIFACT_SUMMARY",
    "ARTIFACT_METADATA_CLOB",
    "STATUS",
    "CREATED_AT",
    "NOTES",
)

_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9]+")


class GovernedWorkflowRepositoryError(RuntimeError):
    """Raised when governed workflow persistence cannot be completed safely."""


@dataclass(frozen=True)
class PersistedWorkflowTransaction:
    """Transaction metadata for a governed workflow write bundle."""

    transaction_group_id: str
    idempotency_key: str
    transaction_scope: str
    rollback_reference: str
    status: str = "PENDING"
    created_at: Any | None = None
    updated_at: Any | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.transaction_scope, "transaction_scope")
        _require_text(self.rollback_reference, "rollback_reference")
        _require_supported(self.status, WORKFLOW_TRANSACTION_STATUSES, "status")
        _require_optional_text(self.notes, "notes")


@dataclass(frozen=True)
class PersistedWorkflowRequest:
    """Durable workflow request metadata."""

    workflow_request_id: str
    transaction_group_id: str
    idempotency_key: str
    source_screen: str
    workflow_type: str
    requested_action: str
    actor_id: str
    payload: dict[str, Any]
    target_type: str | None = None
    target_id: str | None = None
    status: str = "PENDING"
    created_at: Any | None = None
    updated_at: Any | None = None
    error: str | None = None
    warning: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.workflow_request_id, "workflow_request_id")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.source_screen, "source_screen")
        _require_text(self.workflow_type, "workflow_type")
        _require_text(self.requested_action, "requested_action")
        _require_text(self.actor_id, "actor_id")
        _require_mapping(self.payload, "payload")
        _require_optional_text(self.target_type, "target_type")
        _require_optional_text(self.target_id, "target_id")
        _require_supported(self.status, WORKFLOW_REQUEST_STATUSES, "status")
        _require_optional_text(self.error, "error")
        _require_optional_text(self.warning, "warning")
        _require_optional_text(self.notes, "notes")


@dataclass(frozen=True)
class PersistedWorkflowValidation:
    """Validation result metadata for one workflow request."""

    workflow_validation_id: str
    workflow_request_id: str
    validation_status: str
    valid_flag: bool
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    created_at: Any | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.workflow_validation_id, "workflow_validation_id")
        _require_text(self.workflow_request_id, "workflow_request_id")
        _require_text(self.validation_status, "validation_status")
        _require_bool(self.valid_flag, "valid_flag")
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_optional_text(self.notes, "notes")


@dataclass(frozen=True)
class PersistedWorkflowAudit:
    """Audit metadata written with a persisted workflow request."""

    workflow_audit_id: str
    workflow_request_id: str
    transaction_group_id: str
    actor_id: str
    action: str
    audit_summary: str
    payload_hash: str
    created_at: Any | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.workflow_audit_id, "workflow_audit_id")
        _require_text(self.workflow_request_id, "workflow_request_id")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_text(self.actor_id, "actor_id")
        _require_text(self.action, "action")
        _require_text(self.audit_summary, "audit_summary")
        _require_text(self.payload_hash, "payload_hash")
        _require_optional_text(self.notes, "notes")


@dataclass(frozen=True)
class PersistedWorkflowOutputArtifact:
    """Metadata reference for a future workflow output artifact."""

    workflow_output_id: str
    workflow_request_id: str
    artifact_type: str
    artifact_reference: str
    artifact_summary: str | None = None
    artifact_metadata: dict[str, Any] | None = None
    status: str = "RECORDED"
    created_at: Any | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.workflow_output_id, "workflow_output_id")
        _require_text(self.workflow_request_id, "workflow_request_id")
        _require_supported(
            self.artifact_type,
            WORKFLOW_OUTPUT_ARTIFACT_TYPES,
            "artifact_type",
        )
        _require_text(self.artifact_reference, "artifact_reference")
        _require_optional_text(self.artifact_summary, "artifact_summary")
        _require_optional_mapping(self.artifact_metadata, "artifact_metadata")
        _require_supported(self.status, WORKFLOW_OUTPUT_STATUSES, "status")
        _require_optional_text(self.notes, "notes")


@dataclass(frozen=True)
class AnalysisExecutionRecord:
    """Metadata-only references for a future analysis execution result."""

    workflow_request_id: str
    analysis_run_reference: str
    phase4i_payload_reference: str | None = None
    dashboard_artifact_reference: str | None = None
    comparison_artifact_reference: str | None = None
    source_validation_reference: str | None = None
    status: str = "RECORDED"
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.workflow_request_id, "workflow_request_id")
        _require_text(self.analysis_run_reference, "analysis_run_reference")
        _require_optional_text(
            self.phase4i_payload_reference,
            "phase4i_payload_reference",
        )
        _require_optional_text(
            self.dashboard_artifact_reference,
            "dashboard_artifact_reference",
        )
        _require_optional_text(
            self.comparison_artifact_reference,
            "comparison_artifact_reference",
        )
        _require_optional_text(
            self.source_validation_reference,
            "source_validation_reference",
        )
        _require_supported(self.status, WORKFLOW_OUTPUT_STATUSES, "status")
        _require_optional_text(self.notes, "notes")


@dataclass(frozen=True)
class WorkflowPersistenceResult:
    """Result of a governed workflow persistence attempt."""

    workflow_request_id: str
    transaction_group_id: str
    idempotency_key: str
    status: str
    duplicate: bool
    request: PersistedWorkflowRequest | None = None
    transaction: PersistedWorkflowTransaction | None = None
    validation: PersistedWorkflowValidation | None = None
    audit: PersistedWorkflowAudit | None = None
    output_artifacts: tuple[PersistedWorkflowOutputArtifact, ...] = ()
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class GovernedWorkflowRepository:
    """Repository for DB-backed governed workflow metadata.

    A connection object must be injected. This class never creates network
    connections, reads environment variables, imports runtime analysis code, or
    logs protected configuration values.
    """

    def __init__(self, connection: Any) -> None:
        if connection is None:
            raise GovernedWorkflowRepositoryError(
                "GovernedWorkflowRepository requires an injected connection."
            )
        if not hasattr(connection, "cursor"):
            raise GovernedWorkflowRepositoryError(
                "connection must expose a cursor() method."
            )
        self.connection = connection

    def validate_idempotency_key(self, idempotency_key: str) -> str:
        """Validate and return a normalized idempotency key."""

        return _require_text(idempotency_key, "idempotency_key")

    def get_workflow_request(
        self,
        workflow_request_id: str,
    ) -> PersistedWorkflowRequest | None:
        """Return one workflow request by deterministic request id."""

        _require_text(workflow_request_id, "workflow_request_id")
        sql = f"""
            select {", ".join(WORKFLOW_REQUEST_COLUMNS)}
              from AWR_WORKFLOW_REQUEST
             where WORKFLOW_REQUEST_ID = :workflow_request_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, {"workflow_request_id": workflow_request_id})
            row = cursor.fetchone()
        return _request_from_row(row)

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> PersistedWorkflowRequest | None:
        """Return an existing workflow request for an idempotency key."""

        self.validate_idempotency_key(idempotency_key)
        sql = f"""
            select {", ".join(WORKFLOW_REQUEST_COLUMNS)}
              from AWR_WORKFLOW_REQUEST
             where IDEMPOTENCY_KEY = :idempotency_key
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, {"idempotency_key": idempotency_key})
            row = cursor.fetchone()
        return _request_from_row(row)

    def create_workflow_transaction(
        self,
        transaction: PersistedWorkflowTransaction,
    ) -> PersistedWorkflowTransaction:
        """Create transaction metadata, returning existing metadata on replay."""

        transaction.__post_init__()
        existing = self._get_transaction_by_idempotency_key(
            transaction.idempotency_key
        )
        if existing is not None:
            return existing

        sql = """
            insert into AWR_WORKFLOW_TRANSACTION (
                TRANSACTION_GROUP_ID,
                IDEMPOTENCY_KEY,
                TRANSACTION_SCOPE,
                STATUS,
                ROLLBACK_REFERENCE,
                NOTES
            ) values (
                :transaction_group_id,
                :idempotency_key,
                :transaction_scope,
                :status,
                :rollback_reference,
                :notes
            )
        """
        params = {
            "transaction_group_id": transaction.transaction_group_id,
            "idempotency_key": transaction.idempotency_key,
            "transaction_scope": transaction.transaction_scope,
            "status": transaction.status,
            "rollback_reference": transaction.rollback_reference,
            "notes": transaction.notes,
        }
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
        except Exception as exc:  # noqa: BLE001
            existing = self._get_transaction_by_idempotency_key(
                transaction.idempotency_key
            )
            if existing is not None:
                return existing
            raise GovernedWorkflowRepositoryError(
                f"workflow transaction insert failed: {type(exc).__name__}: {exc}"
            ) from exc
        return self._get_transaction(transaction.transaction_group_id) or transaction

    def persist_workflow_request(
        self,
        request: PersistedWorkflowRequest,
    ) -> PersistedWorkflowRequest:
        """Persist a workflow request without creating duplicates on replay."""

        request.__post_init__()
        existing = self.get_by_idempotency_key(request.idempotency_key)
        if existing is not None:
            return existing

        sql = """
            insert into AWR_WORKFLOW_REQUEST (
                WORKFLOW_REQUEST_ID,
                TRANSACTION_GROUP_ID,
                IDEMPOTENCY_KEY,
                SOURCE_SCREEN,
                WORKFLOW_TYPE,
                REQUESTED_ACTION,
                TARGET_TYPE,
                TARGET_ID,
                ACTOR_ID,
                PAYLOAD_CLOB,
                STATUS,
                ERROR_CLOB,
                WARNING_CLOB,
                NOTES
            ) values (
                :workflow_request_id,
                :transaction_group_id,
                :idempotency_key,
                :source_screen,
                :workflow_type,
                :requested_action,
                :target_type,
                :target_id,
                :actor_id,
                :payload_clob,
                :status,
                :error_clob,
                :warning_clob,
                :notes
            )
        """
        params = {
            "workflow_request_id": request.workflow_request_id,
            "transaction_group_id": request.transaction_group_id,
            "idempotency_key": request.idempotency_key,
            "source_screen": request.source_screen,
            "workflow_type": request.workflow_type,
            "requested_action": request.requested_action,
            "target_type": request.target_type,
            "target_id": request.target_id,
            "actor_id": request.actor_id,
            "payload_clob": _json_dumps(request.payload),
            "status": request.status,
            "error_clob": request.error,
            "warning_clob": request.warning,
            "notes": request.notes,
        }
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
        except Exception as exc:  # noqa: BLE001
            existing = self.get_by_idempotency_key(request.idempotency_key)
            if existing is not None:
                return existing
            raise GovernedWorkflowRepositoryError(
                f"workflow request insert failed: {type(exc).__name__}: {exc}"
            ) from exc
        return self.get_workflow_request(request.workflow_request_id) or request

    def persist_workflow_validation(
        self,
        validation: PersistedWorkflowValidation,
    ) -> PersistedWorkflowValidation:
        """Persist validation metadata for a workflow request."""

        validation.__post_init__()
        existing = self._get_validation(validation.workflow_validation_id)
        if existing is not None:
            return existing

        sql = """
            insert into AWR_WORKFLOW_VALIDATION (
                WORKFLOW_VALIDATION_ID,
                WORKFLOW_REQUEST_ID,
                VALIDATION_STATUS,
                VALID_FLAG,
                DENIED_REASONS_CLOB,
                WARNINGS_CLOB,
                REQUIRED_NEXT_STEPS_CLOB,
                NOTES
            ) values (
                :workflow_validation_id,
                :workflow_request_id,
                :validation_status,
                :valid_flag,
                :denied_reasons_clob,
                :warnings_clob,
                :required_next_steps_clob,
                :notes
            )
        """
        params = {
            "workflow_validation_id": validation.workflow_validation_id,
            "workflow_request_id": validation.workflow_request_id,
            "validation_status": validation.validation_status,
            "valid_flag": "Y" if validation.valid_flag else "N",
            "denied_reasons_clob": _json_dumps(validation.denied_reasons),
            "warnings_clob": _json_dumps(validation.warnings),
            "required_next_steps_clob": _json_dumps(
                validation.required_next_steps
            ),
            "notes": validation.notes,
        }
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return self._get_validation(validation.workflow_validation_id) or validation

    def persist_workflow_audit(
        self,
        audit: PersistedWorkflowAudit,
    ) -> PersistedWorkflowAudit:
        """Persist an audit record for a request/transaction pair."""

        audit.__post_init__()
        existing = self._get_audit(audit.workflow_audit_id)
        if existing is not None:
            return existing

        sql = """
            insert into AWR_WORKFLOW_AUDIT (
                WORKFLOW_AUDIT_ID,
                WORKFLOW_REQUEST_ID,
                TRANSACTION_GROUP_ID,
                ACTOR_ID,
                ACTION,
                AUDIT_SUMMARY,
                PAYLOAD_HASH,
                NOTES
            ) values (
                :workflow_audit_id,
                :workflow_request_id,
                :transaction_group_id,
                :actor_id,
                :action,
                :audit_summary,
                :payload_hash,
                :notes
            )
        """
        params = {
            "workflow_audit_id": audit.workflow_audit_id,
            "workflow_request_id": audit.workflow_request_id,
            "transaction_group_id": audit.transaction_group_id,
            "actor_id": audit.actor_id,
            "action": audit.action,
            "audit_summary": audit.audit_summary,
            "payload_hash": audit.payload_hash,
            "notes": audit.notes,
        }
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return self._get_audit(audit.workflow_audit_id) or audit

    def persist_output_artifact(
        self,
        artifact: PersistedWorkflowOutputArtifact,
    ) -> PersistedWorkflowOutputArtifact:
        """Persist an output artifact reference without creating the artifact."""

        artifact.__post_init__()
        existing = self._get_output_artifact(artifact.workflow_output_id)
        if existing is not None:
            return existing

        sql = """
            insert into AWR_WORKFLOW_OUTPUT_ARTIFACT (
                WORKFLOW_OUTPUT_ID,
                WORKFLOW_REQUEST_ID,
                ARTIFACT_TYPE,
                ARTIFACT_REFERENCE,
                ARTIFACT_SUMMARY,
                ARTIFACT_METADATA_CLOB,
                STATUS,
                NOTES
            ) values (
                :workflow_output_id,
                :workflow_request_id,
                :artifact_type,
                :artifact_reference,
                :artifact_summary,
                :artifact_metadata_clob,
                :status,
                :notes
            )
        """
        params = {
            "workflow_output_id": artifact.workflow_output_id,
            "workflow_request_id": artifact.workflow_request_id,
            "artifact_type": artifact.artifact_type,
            "artifact_reference": artifact.artifact_reference,
            "artifact_summary": artifact.artifact_summary,
            "artifact_metadata_clob": (
                _json_dumps(artifact.artifact_metadata)
                if artifact.artifact_metadata is not None
                else None
            ),
            "status": artifact.status,
            "notes": artifact.notes,
        }
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return self._get_output_artifact(artifact.workflow_output_id) or artifact

    def persist_analysis_execution_record(
        self,
        record: AnalysisExecutionRecord,
    ) -> tuple[PersistedWorkflowOutputArtifact, ...]:
        """Persist metadata references for a future analysis execution."""

        record.__post_init__()
        artifacts = [
            PersistedWorkflowOutputArtifact(
                workflow_output_id=create_workflow_output_id(
                    record.workflow_request_id,
                    "analysis_run_record",
                    record.analysis_run_reference,
                ),
                workflow_request_id=record.workflow_request_id,
                artifact_type="analysis_run_record",
                artifact_reference=record.analysis_run_reference,
                artifact_summary="Analysis run record reference only.",
                artifact_metadata={"runtime_mutation": False},
                status=record.status,
                notes=record.notes,
            )
        ]
        optional_references = (
            ("phase4i_payload_reference", record.phase4i_payload_reference),
            ("dashboard_artifact_reference", record.dashboard_artifact_reference),
            ("comparison_artifact", record.comparison_artifact_reference),
            ("source_validation_artifact", record.source_validation_reference),
        )
        for artifact_type, reference in optional_references:
            if reference:
                artifacts.append(
                    PersistedWorkflowOutputArtifact(
                        workflow_output_id=create_workflow_output_id(
                            record.workflow_request_id,
                            artifact_type,
                            reference,
                        ),
                        workflow_request_id=record.workflow_request_id,
                        artifact_type=artifact_type,
                        artifact_reference=reference,
                        artifact_summary=f"{artifact_type} metadata reference only.",
                        artifact_metadata={"runtime_mutation": False},
                        status=record.status,
                        notes=record.notes,
                    )
                )
        return tuple(self.persist_output_artifact(artifact) for artifact in artifacts)

    def record_workflow_failure(
        self,
        *,
        transaction_group_id: str,
        idempotency_key: str,
        actor_id: str,
        action: str,
        error_message: str,
        rollback_reference: str,
        workflow_request_id: str | None = None,
        transaction_scope: str = "workflow_execution",
        notes: str | None = None,
        commit: bool = True,
    ) -> WorkflowPersistenceResult:
        """Record failure metadata for a governed workflow attempt."""

        _require_text(transaction_group_id, "transaction_group_id")
        self.validate_idempotency_key(idempotency_key)
        _require_text(actor_id, "actor_id")
        _require_text(action, "action")
        _require_text(error_message, "error_message")
        _require_text(rollback_reference, "rollback_reference")
        _require_optional_text(workflow_request_id, "workflow_request_id")
        _require_text(transaction_scope, "transaction_scope")
        _require_optional_text(notes, "notes")

        transaction = self._get_transaction_by_idempotency_key(idempotency_key)
        if transaction is None:
            transaction = self.create_workflow_transaction(
                PersistedWorkflowTransaction(
                    transaction_group_id=transaction_group_id,
                    idempotency_key=idempotency_key,
                    transaction_scope=transaction_scope,
                    rollback_reference=rollback_reference,
                    status="FAILED",
                    notes=notes,
                )
            )
        else:
            self._update_transaction_status(
                transaction.transaction_group_id,
                "FAILED",
                notes,
            )
            transaction = self._get_transaction(transaction.transaction_group_id)

        request = (
            self.get_workflow_request(workflow_request_id)
            if workflow_request_id
            else self.get_by_idempotency_key(idempotency_key)
        )
        audit = None
        artifacts: tuple[PersistedWorkflowOutputArtifact, ...] = ()
        if request is not None:
            self._update_request_failure(
                request.workflow_request_id,
                error_message,
                notes,
            )
            request = self.get_workflow_request(request.workflow_request_id) or request
            audit = self.persist_workflow_audit(
                PersistedWorkflowAudit(
                    workflow_audit_id=create_workflow_audit_id(
                        request.workflow_request_id,
                        "workflow_failure_recorded",
                    ),
                    workflow_request_id=request.workflow_request_id,
                    transaction_group_id=request.transaction_group_id,
                    actor_id=actor_id,
                    action=action,
                    audit_summary=(
                        "Workflow failure metadata recorded; runtime truth was not "
                        "mutated."
                    ),
                    payload_hash=hash_payload({"error": error_message}),
                    notes=notes,
                )
            )
            artifacts = (
                self.persist_output_artifact(
                    PersistedWorkflowOutputArtifact(
                        workflow_output_id=create_workflow_output_id(
                            request.workflow_request_id,
                            "error_artifact",
                            hash_payload({"error": error_message})[:16],
                        ),
                        workflow_request_id=request.workflow_request_id,
                        artifact_type="error_artifact",
                        artifact_reference=(
                            "governed-workflow-error:"
                            f"{hash_payload({'error': error_message})[:16]}"
                        ),
                        artifact_summary="Workflow failure metadata reference.",
                        artifact_metadata={"error": error_message},
                        status="FAILED",
                        notes=notes,
                    )
                ),
            )

        if commit:
            self._commit()
        return WorkflowPersistenceResult(
            workflow_request_id=request.workflow_request_id if request else "",
            transaction_group_id=transaction.transaction_group_id if transaction else transaction_group_id,
            idempotency_key=idempotency_key,
            status="FAILED",
            duplicate=False,
            request=request,
            transaction=transaction,
            audit=audit,
            output_artifacts=artifacts,
            errors=(error_message,),
        )

    def persist_workflow_bundle(
        self,
        *,
        request: PersistedWorkflowRequest,
        transaction: PersistedWorkflowTransaction | None = None,
        validation: PersistedWorkflowValidation | None = None,
        audit: PersistedWorkflowAudit | None = None,
        output_artifacts: Iterable[PersistedWorkflowOutputArtifact] | None = None,
        commit: bool = True,
    ) -> WorkflowPersistenceResult:
        """Persist request, transaction, audit, validation, and artifacts atomically."""

        request.__post_init__()
        if transaction is None:
            transaction = PersistedWorkflowTransaction(
                transaction_group_id=request.transaction_group_id,
                idempotency_key=request.idempotency_key,
                transaction_scope="workflow_execution",
                rollback_reference=_rollback_reference_from_payload(request.payload),
                status="IN_PROGRESS",
                notes=request.notes,
            )
        transaction.__post_init__()
        if transaction.idempotency_key != request.idempotency_key:
            raise GovernedWorkflowRepositoryError(
                "transaction and request idempotency keys must match."
            )
        if transaction.transaction_group_id != request.transaction_group_id:
            raise GovernedWorkflowRepositoryError(
                "transaction and request transaction_group_id values must match."
            )

        existing = self.get_by_idempotency_key(request.idempotency_key)
        if existing is not None:
            existing_transaction = self._get_transaction_by_idempotency_key(
                request.idempotency_key
            )
            return WorkflowPersistenceResult(
                workflow_request_id=existing.workflow_request_id,
                transaction_group_id=existing.transaction_group_id,
                idempotency_key=existing.idempotency_key,
                status="DUPLICATE_REPLAY",
                duplicate=True,
                request=existing,
                transaction=existing_transaction,
                warnings=("idempotency key already persisted; existing request returned.",),
            )

        try:
            persisted_transaction = self.create_workflow_transaction(transaction)
            persisted_request = self.persist_workflow_request(request)
            persisted_validation = (
                self.persist_workflow_validation(validation)
                if validation is not None
                else None
            )
            persisted_audit = self.persist_workflow_audit(
                audit
                if audit is not None
                else create_default_audit_record(persisted_request)
            )
            persisted_artifacts = tuple(
                self.persist_output_artifact(artifact)
                for artifact in (output_artifacts or ())
            )
            self._update_transaction_status(
                persisted_transaction.transaction_group_id,
                "COMMITTED",
                persisted_transaction.notes,
            )
            persisted_transaction = (
                self._get_transaction(persisted_transaction.transaction_group_id)
                or persisted_transaction
            )
            if commit:
                self._commit()
            return WorkflowPersistenceResult(
                workflow_request_id=persisted_request.workflow_request_id,
                transaction_group_id=persisted_request.transaction_group_id,
                idempotency_key=persisted_request.idempotency_key,
                status="PERSISTED",
                duplicate=False,
                request=persisted_request,
                transaction=persisted_transaction,
                validation=persisted_validation,
                audit=persisted_audit,
                output_artifacts=persisted_artifacts,
            )
        except Exception as exc:  # noqa: BLE001
            self._rollback()
            failure_error: str | None = None
            try:
                self.record_workflow_failure(
                    transaction_group_id=request.transaction_group_id,
                    idempotency_key=request.idempotency_key,
                    actor_id=request.actor_id,
                    action="workflow_bundle_persistence_failed",
                    error_message=f"{type(exc).__name__}: {exc}",
                    rollback_reference=transaction.rollback_reference,
                    workflow_request_id=request.workflow_request_id,
                    transaction_scope=transaction.transaction_scope,
                    notes=request.notes,
                    commit=commit,
                )
            except Exception as failure_exc:  # noqa: BLE001
                failure_error = (
                    f"; failure metadata recording failed: "
                    f"{type(failure_exc).__name__}: {failure_exc}"
                )
            raise GovernedWorkflowRepositoryError(
                "workflow bundle persistence failed: "
                f"{type(exc).__name__}: {exc}{failure_error or ''}"
            ) from exc

    def _get_transaction(
        self,
        transaction_group_id: str,
    ) -> PersistedWorkflowTransaction | None:
        _require_text(transaction_group_id, "transaction_group_id")
        sql = f"""
            select {", ".join(WORKFLOW_TRANSACTION_COLUMNS)}
              from AWR_WORKFLOW_TRANSACTION
             where TRANSACTION_GROUP_ID = :transaction_group_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, {"transaction_group_id": transaction_group_id})
            row = cursor.fetchone()
        return _transaction_from_row(row)

    def _get_transaction_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> PersistedWorkflowTransaction | None:
        self.validate_idempotency_key(idempotency_key)
        sql = f"""
            select {", ".join(WORKFLOW_TRANSACTION_COLUMNS)}
              from AWR_WORKFLOW_TRANSACTION
             where IDEMPOTENCY_KEY = :idempotency_key
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, {"idempotency_key": idempotency_key})
            row = cursor.fetchone()
        return _transaction_from_row(row)

    def _get_validation(
        self,
        workflow_validation_id: str,
    ) -> PersistedWorkflowValidation | None:
        _require_text(workflow_validation_id, "workflow_validation_id")
        sql = """
            select
                WORKFLOW_VALIDATION_ID,
                WORKFLOW_REQUEST_ID,
                VALIDATION_STATUS,
                VALID_FLAG,
                DENIED_REASONS_CLOB,
                WARNINGS_CLOB,
                REQUIRED_NEXT_STEPS_CLOB,
                CREATED_AT,
                NOTES
              from AWR_WORKFLOW_VALIDATION
             where WORKFLOW_VALIDATION_ID = :workflow_validation_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, {"workflow_validation_id": workflow_validation_id})
            row = cursor.fetchone()
        return _validation_from_row(row)

    def _get_audit(self, workflow_audit_id: str) -> PersistedWorkflowAudit | None:
        _require_text(workflow_audit_id, "workflow_audit_id")
        sql = f"""
            select {", ".join(WORKFLOW_AUDIT_COLUMNS)}
              from AWR_WORKFLOW_AUDIT
             where WORKFLOW_AUDIT_ID = :workflow_audit_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, {"workflow_audit_id": workflow_audit_id})
            row = cursor.fetchone()
        return _audit_from_row(row)

    def _get_output_artifact(
        self,
        workflow_output_id: str,
    ) -> PersistedWorkflowOutputArtifact | None:
        _require_text(workflow_output_id, "workflow_output_id")
        sql = f"""
            select {", ".join(WORKFLOW_OUTPUT_COLUMNS)}
              from AWR_WORKFLOW_OUTPUT_ARTIFACT
             where WORKFLOW_OUTPUT_ID = :workflow_output_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, {"workflow_output_id": workflow_output_id})
            row = cursor.fetchone()
        return _output_artifact_from_row(row)

    def _update_transaction_status(
        self,
        transaction_group_id: str,
        status: str,
        notes: str | None,
    ) -> None:
        _require_text(transaction_group_id, "transaction_group_id")
        _require_supported(status, WORKFLOW_TRANSACTION_STATUSES, "status")
        _require_optional_text(notes, "notes")
        sql = """
            update AWR_WORKFLOW_TRANSACTION
               set STATUS = :status,
                   UPDATED_AT = SYSTIMESTAMP,
                   NOTES = :notes
             where TRANSACTION_GROUP_ID = :transaction_group_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(
                sql,
                {
                    "status": status,
                    "notes": notes,
                    "transaction_group_id": transaction_group_id,
                },
            )

    def _update_request_failure(
        self,
        workflow_request_id: str,
        error_message: str,
        notes: str | None,
    ) -> None:
        _require_text(workflow_request_id, "workflow_request_id")
        _require_text(error_message, "error_message")
        _require_optional_text(notes, "notes")
        sql = """
            update AWR_WORKFLOW_REQUEST
               set STATUS = 'FAILED',
                   UPDATED_AT = SYSTIMESTAMP,
                   ERROR_CLOB = :error_clob,
                   NOTES = :notes
             where WORKFLOW_REQUEST_ID = :workflow_request_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(
                sql,
                {
                    "error_clob": error_message,
                    "notes": notes,
                    "workflow_request_id": workflow_request_id,
                },
            )

    def _commit(self) -> None:
        if hasattr(self.connection, "commit"):
            self.connection.commit()

    def _rollback(self) -> None:
        if hasattr(self.connection, "rollback"):
            self.connection.rollback()


def create_workflow_request_id(workflow_type: str, idempotency_key: str) -> str:
    """Create a deterministic workflow request id."""

    return _stable_id("AWR-WORKFLOW-REQUEST", workflow_type, idempotency_key)


def create_workflow_validation_id(workflow_request_id: str) -> str:
    """Create a deterministic validation id for one request."""

    return _stable_id("AWR-WORKFLOW-VALIDATION", workflow_request_id)


def create_workflow_audit_id(workflow_request_id: str, action: str) -> str:
    """Create a deterministic audit id for one request action."""

    return _stable_id("AWR-WORKFLOW-AUDIT", workflow_request_id, action)


def create_workflow_output_id(
    workflow_request_id: str,
    artifact_type: str,
    artifact_reference: str,
) -> str:
    """Create a deterministic output artifact id."""

    _require_supported(artifact_type, WORKFLOW_OUTPUT_ARTIFACT_TYPES, "artifact_type")
    return _stable_id(
        "AWR-WORKFLOW-OUTPUT",
        workflow_request_id,
        artifact_type,
        artifact_reference,
    )


def create_transaction_group_id(idempotency_key: str, scope: str) -> str:
    """Create a deterministic transaction group id."""

    return _stable_id("AWR-WORKFLOW-TX", scope, idempotency_key)


def hash_payload(payload: Any) -> str:
    """Return a stable SHA-256 hash for audit payload metadata."""

    encoded = _json_dumps(payload).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def create_default_audit_record(
    request: PersistedWorkflowRequest,
    *,
    action: str = "workflow_request_persisted",
) -> PersistedWorkflowAudit:
    """Create the default audit record required with a workflow request."""

    request.__post_init__()
    return PersistedWorkflowAudit(
        workflow_audit_id=create_workflow_audit_id(
            request.workflow_request_id,
            action,
        ),
        workflow_request_id=request.workflow_request_id,
        transaction_group_id=request.transaction_group_id,
        actor_id=request.actor_id,
        action=action,
        audit_summary=(
            "Governed workflow request persisted as workflow metadata only; "
            "runtime truth was not mutated."
        ),
        payload_hash=hash_payload(request.payload),
        notes=request.notes,
    )


def _request_from_row(row: Any | None) -> PersistedWorkflowRequest | None:
    if row is None:
        return None
    values = _row_values(row, WORKFLOW_REQUEST_COLUMNS)
    return PersistedWorkflowRequest(
        workflow_request_id=str(values["WORKFLOW_REQUEST_ID"]),
        transaction_group_id=str(values["TRANSACTION_GROUP_ID"]),
        idempotency_key=str(values["IDEMPOTENCY_KEY"]),
        source_screen=str(values["SOURCE_SCREEN"]),
        workflow_type=str(values["WORKFLOW_TYPE"]),
        requested_action=str(values["REQUESTED_ACTION"]),
        target_type=_optional_string(values.get("TARGET_TYPE")),
        target_id=_optional_string(values.get("TARGET_ID")),
        actor_id=str(values["ACTOR_ID"]),
        payload=_json_loads(values.get("PAYLOAD_CLOB"), default={}),
        status=str(values["STATUS"]),
        created_at=values.get("CREATED_AT"),
        updated_at=values.get("UPDATED_AT"),
        error=_optional_string(values.get("ERROR_CLOB")),
        warning=_optional_string(values.get("WARNING_CLOB")),
        notes=_optional_string(values.get("NOTES")),
    )


def _transaction_from_row(row: Any | None) -> PersistedWorkflowTransaction | None:
    if row is None:
        return None
    values = _row_values(row, WORKFLOW_TRANSACTION_COLUMNS)
    return PersistedWorkflowTransaction(
        transaction_group_id=str(values["TRANSACTION_GROUP_ID"]),
        idempotency_key=str(values["IDEMPOTENCY_KEY"]),
        transaction_scope=str(values["TRANSACTION_SCOPE"]),
        status=str(values["STATUS"]),
        rollback_reference=str(values["ROLLBACK_REFERENCE"]),
        created_at=values.get("CREATED_AT"),
        updated_at=values.get("UPDATED_AT"),
        notes=_optional_string(values.get("NOTES")),
    )


def _validation_from_row(row: Any | None) -> PersistedWorkflowValidation | None:
    if row is None:
        return None
    columns = (
        "WORKFLOW_VALIDATION_ID",
        "WORKFLOW_REQUEST_ID",
        "VALIDATION_STATUS",
        "VALID_FLAG",
        "DENIED_REASONS_CLOB",
        "WARNINGS_CLOB",
        "REQUIRED_NEXT_STEPS_CLOB",
        "CREATED_AT",
        "NOTES",
    )
    values = _row_values(row, columns)
    return PersistedWorkflowValidation(
        workflow_validation_id=str(values["WORKFLOW_VALIDATION_ID"]),
        workflow_request_id=str(values["WORKFLOW_REQUEST_ID"]),
        validation_status=str(values["VALIDATION_STATUS"]),
        valid_flag=str(values["VALID_FLAG"]).upper() == "Y",
        denied_reasons=_json_loads(values.get("DENIED_REASONS_CLOB"), default=[]),
        warnings=_json_loads(values.get("WARNINGS_CLOB"), default=[]),
        required_next_steps=_json_loads(
            values.get("REQUIRED_NEXT_STEPS_CLOB"),
            default=[],
        ),
        created_at=values.get("CREATED_AT"),
        notes=_optional_string(values.get("NOTES")),
    )


def _audit_from_row(row: Any | None) -> PersistedWorkflowAudit | None:
    if row is None:
        return None
    values = _row_values(row, WORKFLOW_AUDIT_COLUMNS)
    return PersistedWorkflowAudit(
        workflow_audit_id=str(values["WORKFLOW_AUDIT_ID"]),
        workflow_request_id=str(values["WORKFLOW_REQUEST_ID"]),
        transaction_group_id=str(values["TRANSACTION_GROUP_ID"]),
        actor_id=str(values["ACTOR_ID"]),
        action=str(values["ACTION"]),
        audit_summary=str(values["AUDIT_SUMMARY"]),
        payload_hash=str(values["PAYLOAD_HASH"]),
        created_at=values.get("CREATED_AT"),
        notes=_optional_string(values.get("NOTES")),
    )


def _output_artifact_from_row(
    row: Any | None,
) -> PersistedWorkflowOutputArtifact | None:
    if row is None:
        return None
    values = _row_values(row, WORKFLOW_OUTPUT_COLUMNS)
    return PersistedWorkflowOutputArtifact(
        workflow_output_id=str(values["WORKFLOW_OUTPUT_ID"]),
        workflow_request_id=str(values["WORKFLOW_REQUEST_ID"]),
        artifact_type=str(values["ARTIFACT_TYPE"]),
        artifact_reference=str(values["ARTIFACT_REFERENCE"]),
        artifact_summary=_optional_string(values.get("ARTIFACT_SUMMARY")),
        artifact_metadata=_json_loads(
            values.get("ARTIFACT_METADATA_CLOB"),
            default=None,
        ),
        status=str(values["STATUS"]),
        created_at=values.get("CREATED_AT"),
        notes=_optional_string(values.get("NOTES")),
    )


def _row_values(row: Any, columns: tuple[str, ...]) -> dict[str, Any]:
    if isinstance(row, dict):
        return {column: row.get(column) or row.get(column.lower()) for column in columns}
    return {column: row[index] for index, column in enumerate(columns)}


def _rollback_reference_from_payload(payload: dict[str, Any]) -> str:
    rollback_reference = payload.get("rollback_reference")
    if not rollback_reference:
        raise GovernedWorkflowRepositoryError(
            "rollback_reference is required for workflow bundle persistence."
        )
    return _require_text(str(rollback_reference), "rollback_reference")


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default)


def _json_loads(value: Any, *, default: Any) -> Any:
    value = _read_db_value(value)
    if value is None:
        return default
    if isinstance(value, dict | list):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if not isinstance(value, str):
        value = str(value)
    if not value.strip():
        return default
    return json.loads(value)


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _stable_id(prefix: str, *parts: str) -> str:
    tokens = [_normalize_token(prefix)]
    tokens.extend(_normalize_token(_require_text(part, "id_part")) for part in parts)
    raw_id = "-".join(token for token in tokens if token)
    if len(raw_id) <= 140:
        return raw_id
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24].upper()
    return f"{tokens[0]}-{digest}"


def _normalize_token(value: str) -> str:
    normalized = _TOKEN_PATTERN.sub("-", value.strip().upper()).strip("-")
    return normalized or "UNSPECIFIED"


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernedWorkflowRepositoryError(f"{field_name} is required.")
    return value.strip()


def _require_optional_text(value: Any | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise GovernedWorkflowRepositoryError(f"{field_name} must be text when set.")
    if not value.strip():
        raise GovernedWorkflowRepositoryError(f"{field_name} cannot be blank when set.")
    return value.strip()


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise GovernedWorkflowRepositoryError(f"{field_name} must be a mapping.")


def _require_optional_mapping(value: Any | None, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise GovernedWorkflowRepositoryError(f"{field_name} must be a mapping.")


def _require_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise GovernedWorkflowRepositoryError(f"{field_name} must be boolean.")


def _require_string_list(values: Any, field_name: str) -> None:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise GovernedWorkflowRepositoryError(f"{field_name} must be a list of text.")


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise GovernedWorkflowRepositoryError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _optional_string(value: Any | None) -> str | None:
    value = _read_db_value(value)
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _read_db_value(value: Any) -> Any:
    read = getattr(value, "read", None)
    if callable(read):
        return read()
    return value
