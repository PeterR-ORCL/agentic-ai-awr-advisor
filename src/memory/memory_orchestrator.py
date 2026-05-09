"""Phase 6 memory orchestration for deterministic AWR analysis runs."""

from __future__ import annotations

import os
import json
import re
import traceback
from typing import Any

from src.memory import memory_agent, memory_recall

EXPECTED_PHASE4I_KEYS = (
    "metadata",
    "decision",
    "scores",
    "trends",
    "similarity_intelligence",
    "recommendations",
)

DISABLED_VALUES = {"0", "false", "no", "off"}
ENABLED_VALUES = {"1", "true", "yes", "on"}
ACTION_STATUS_VALUES = {
    "RECORDED",
    "PLANNED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
    "REJECTED",
}
ACTION_SUMMARY_MAX_LENGTH = 4000
OUTCOME_STATUS_VALUES = {
    "SUCCESS",
    "PARTIAL",
    "FAILED",
    "NO_CHANGE",
}
OUTCOME_SUMMARY_MAX_LENGTH = 4000
FEEDBACK_TYPE_VALUES = {
    "DIAGNOSIS_CORRECTNESS",
    "RECOMMENDATION_USEFULNESS",
    "ACTION_GUIDANCE_CLARITY",
    "OUTCOME_ASSESSMENT",
    "MISSED_SIGNAL",
    "FALSE_POSITIVE",
    "GENERAL",
}
FEEDBACK_RATING_VALUES = {
    "POSITIVE",
    "NEUTRAL",
    "NEGATIVE",
    "MIXED",
    "UNKNOWN",
}
FEEDBACK_SOURCE_VALUES = {
    "DBA",
    "ENGINEER",
    "ARCHITECT",
    "CUSTOMER",
    "SALES_ENGINEER",
    "CLOUD_ARCHITECT",
    "SYSTEM_REVIEW",
    "OTHER",
}
FEEDBACK_SUMMARY_MAX_LENGTH = 4000
UNKNOWN_SIGNAL_REVIEW_STATUS_VALUES = {
    "NEW",
    "REVIEWED",
    "CLASSIFIED",
    "IGNORED",
}
UNKNOWN_SIGNAL_REVIEW_CLASSIFICATION_VALUES = {
    "CPU",
    "IO",
    "MEMORY",
    "COMMIT",
    "RAC",
    "ADG",
    "OTHER",
}
UNKNOWN_SIGNAL_REVIEW_NOTES_MAX_LENGTH = 4000
KNOWLEDGE_SOURCE_TYPE_VALUES = {
    "UNKNOWN_SIGNAL",
    "FEEDBACK",
    "OUTCOME",
}
KNOWLEDGE_APPROVAL_STATUS_VALUES = {
    "PENDING",
    "APPROVED",
    "REJECTED",
    "NEEDS_REVIEW",
}
KNOWLEDGE_REQUEST_SUMMARY_MAX_LENGTH = 4000
KNOWLEDGE_ARTIFACT_TYPE_VALUES = {
    "SIGNAL_CLASSIFICATION",
    "RULE_HINT",
    "PATTERN",
    "OTHER",
}
KNOWLEDGE_ARTIFACT_SUMMARY_MAX_LENGTH = 4000


def persist_run_memory(
    phase4i_output: dict,
    source_context: dict,
    parser_output: Any | None = None,
    options: dict | None = None,
) -> dict[str, Any]:
    """Coordinate downstream Phase 6 memory persistence.

    Phase 4I remains the deterministic source of truth. This orchestrator is
    downstream-only and must never feed memory context back into parser,
    scoring, decision posture, or deterministic recommendation generation.
    """

    result = _base_result(enabled=_memory_enabled(options))
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        return result

    warnings = _validate_inputs(phase4i_output, source_context)
    result["warnings"].extend(warnings)
    if not isinstance(phase4i_output, dict):
        result["success"] = False
        result["errors"].append("phase4i_output must be a dict")
        return result

    safe_source_context = source_context if isinstance(source_context, dict) else {}
    try:
        run_history_id = memory_agent.persist_analysis(
            phase4i_output=phase4i_output,
            source_context=safe_source_context,
            parser_output=parser_output,
        )
        result["success"] = True
        result["run_history_id"] = run_history_id
        result["persisted"] = {
            "run_history": True,
            "recommendations": True,
            "unknown_signals": True,
            "actions": False,
            "outcomes": False,
            "feedback": False,
        }
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        if _memory_debug_enabled(options):
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def recall_run_history(**filters: Any) -> dict[str, Any]:
    """Read-only recall of run memory records.

    Recall is observational and read-only. It does not influence parser,
    scoring, recommendation, or runtime decision behavior.
    """

    return memory_recall.recall_run_history(**filters)


def recall_recommendation_history(**filters: Any) -> dict[str, Any]:
    """Read-only recall of recommendation memory records."""

    return memory_recall.recall_recommendation_history(**filters)


def recall_action_history(**filters: Any) -> dict[str, Any]:
    """Read-only recall of action history records."""

    return memory_recall.recall_action_history(**filters)


def recall_outcome_history(**filters: Any) -> dict[str, Any]:
    """Read-only recall of action outcome records."""

    return memory_recall.recall_outcome_history(**filters)


def recall_feedback_history(**filters: Any) -> dict[str, Any]:
    """Read-only recall of feedback records."""

    return memory_recall.recall_feedback_history(**filters)


def recall_unknown_signals(**filters: Any) -> dict[str, Any]:
    """Read-only recall of parser unknown and review records."""

    return memory_recall.recall_unknown_signals(**filters)


def recall_knowledge_requests(**filters: Any) -> dict[str, Any]:
    """Read-only recall of governance request records."""

    return memory_recall.recall_knowledge_requests(**filters)


def recall_knowledge_artifacts(**filters: Any) -> dict[str, Any]:
    """Read-only recall of materialized knowledge artifact records."""

    return memory_recall.recall_knowledge_artifacts(**filters)


def recall_memory_summary(**filters: Any) -> dict[str, Any]:
    """Read-only aggregate recall summary for Phase 6 memory."""

    return memory_recall.recall_memory_summary(**filters)


def record_action(
    run_history_id: int,
    action_type: str,
    action_summary: str,
    action_status: str = "RECORDED",
    recommendation_history_id: int | None = None,
    actor: str | None = None,
    notes: str | None = None,
    action_metadata: dict | None = None,
) -> dict[str, Any]:
    """Record a downstream human/operator action for an advisory run."""

    result = _base_action_result(enabled=_memory_enabled())
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        return result

    normalized, warnings, errors = _validate_action_inputs(
        run_history_id=run_history_id,
        action_type=action_type,
        action_summary=action_summary,
        action_status=action_status,
        recommendation_history_id=recommendation_history_id,
        actor=actor,
        notes=notes,
        action_metadata=action_metadata,
    )
    result["warnings"].extend(warnings)
    if errors:
        result["success"] = False
        result["errors"].extend(errors)
        return result

    try:
        action_history_id = memory_agent.insert_action_history(
            run_history_id=normalized["run_history_id"],
            recommendation_history_id=normalized["recommendation_history_id"],
            action_type=normalized["action_type"],
            action_status=normalized["action_status"],
            action_description=normalized["action_summary"],
            action_owner=normalized["actor"],
            action_notes=normalized["notes"],
        )
        result.update(
            {
                "success": True,
                "action_history_id": action_history_id,
                "run_history_id": normalized["run_history_id"],
                "recommendation_history_id": normalized["recommendation_history_id"],
                "action_type": normalized["action_type"],
                "action_status": normalized["action_status"],
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        if _memory_debug_enabled():
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def record_outcome(
    run_history_id: int,
    action_history_id: int,
    outcome_status: str,
    outcome_summary: str,
    before_metrics: dict | None = None,
    after_metrics: dict | None = None,
    impact_score: float | None = None,
    recorded_by: str | None = None,
    notes: dict | str | None = None,
) -> dict[str, Any]:
    """Record an append-only downstream outcome for a human/operator action."""

    result = _base_outcome_result(enabled=_memory_enabled())
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        result["message"] = "memory_disabled"
        return result

    normalized, warnings, errors = _validate_outcome_inputs(
        run_history_id=run_history_id,
        action_history_id=action_history_id,
        outcome_status=outcome_status,
        outcome_summary=outcome_summary,
        before_metrics=before_metrics,
        after_metrics=after_metrics,
        impact_score=impact_score,
        recorded_by=recorded_by,
        notes=notes,
    )
    result["warnings"].extend(warnings)
    if errors:
        result["success"] = False
        result["errors"].extend(errors)
        result["message"] = errors[0]
        return result

    try:
        outcome_id = memory_agent.insert_action_outcome_history(
            run_history_id=normalized["run_history_id"],
            action_history_id=normalized["action_history_id"],
            outcome_status=normalized["outcome_status"],
            outcome_summary=normalized["outcome_summary"],
            before_metrics=normalized["before_metrics"],
            after_metrics=normalized["after_metrics"],
            impact_score=normalized["impact_score"],
            recorded_by=normalized["recorded_by"],
            outcome_notes=normalized["notes"],
        )
        result.update(
            {
                "success": True,
                "outcome_id": outcome_id,
                "action_outcome_id": outcome_id,
                "run_history_id": normalized["run_history_id"],
                "action_history_id": normalized["action_history_id"],
                "outcome_status": normalized["outcome_status"],
                "message": "outcome_recorded",
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        result["message"] = result["errors"][0]
        if _memory_debug_enabled():
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def record_feedback(
    run_history_id: int,
    feedback_type: str,
    feedback_rating: str,
    feedback_summary: str,
    recommendation_history_id: int | None = None,
    action_history_id: int | None = None,
    action_outcome_id: int | None = None,
    feedback_detail: str | None = None,
    feedback_source: str | None = None,
    recorded_by: str | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]:
    """Record append-only human/operator feedback for an advisory run."""

    result = _base_feedback_result(enabled=_memory_enabled())
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        return result

    normalized, warnings, errors = _validate_feedback_inputs(
        run_history_id=run_history_id,
        recommendation_history_id=recommendation_history_id,
        action_history_id=action_history_id,
        action_outcome_id=action_outcome_id,
        feedback_type=feedback_type,
        feedback_rating=feedback_rating,
        feedback_summary=feedback_summary,
        feedback_detail=feedback_detail,
        feedback_source=feedback_source,
        recorded_by=recorded_by,
        metadata=metadata,
    )
    result["warnings"].extend(warnings)
    if errors:
        result["success"] = False
        result["errors"].extend(errors)
        return result

    try:
        feedback_id = memory_agent.insert_feedback_history(
            run_history_id=normalized["run_history_id"],
            recommendation_history_id=normalized["recommendation_history_id"],
            action_history_id=normalized["action_history_id"],
            action_outcome_id=normalized["action_outcome_id"],
            feedback_type=normalized["feedback_type"],
            feedback_rating=normalized["feedback_rating"],
            feedback_summary=normalized["feedback_summary"],
            feedback_detail=normalized["feedback_detail"],
            feedback_source=normalized["feedback_source"],
            recorded_by=normalized["recorded_by"],
            feedback_metadata=normalized["metadata"],
        )
        result.update(
            {
                "success": True,
                "feedback_id": feedback_id,
                "run_history_id": normalized["run_history_id"],
                "feedback_type": normalized["feedback_type"],
                "feedback_rating": normalized["feedback_rating"],
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        if _memory_debug_enabled():
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def review_unknown_signal(
    unknown_signal_id: int,
    review_status: str,
    review_classification: str | None = None,
    review_notes: str | None = None,
    reviewed_by: str | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]:
    """Record manual review metadata for a captured unknown parser signal."""

    result = _base_unknown_signal_review_result(enabled=_memory_enabled())
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        return result

    normalized, warnings, errors = _validate_unknown_signal_review_inputs(
        unknown_signal_id=unknown_signal_id,
        review_status=review_status,
        review_classification=review_classification,
        review_notes=review_notes,
        reviewed_by=reviewed_by,
        metadata=metadata,
    )
    result["warnings"].extend(warnings)
    if errors:
        result["success"] = False
        result["errors"].extend(errors)
        return result

    try:
        update_result = memory_agent.update_unknown_signal_review(
            unknown_signal_id=normalized["unknown_signal_id"],
            review_status=normalized["review_status"],
            review_classification=normalized["review_classification"],
            review_notes=normalized["review_notes"],
            reviewed_by=normalized["reviewed_by"],
            metadata=normalized["metadata"],
        )
        previous_status = _normalize_token(update_result.get("previous_review_status"))
        if previous_status in {"CLASSIFIED", "IGNORED"}:
            result["warnings"].append("overwriting existing review classification")
        result.update(
            {
                "success": True,
                "unknown_signal_id": normalized["unknown_signal_id"],
                "review_status": normalized["review_status"],
                "review_classification": normalized["review_classification"],
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        if _memory_debug_enabled():
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def create_knowledge_update_request(
    source_type: str,
    source_id: int,
    candidate_classification: str | None,
    candidate_summary: str,
    candidate_details: str | None = None,
    run_history_id: int | None = None,
    created_by: str | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]:
    """Create a pending governance request for future knowledge update eligibility."""

    result = _base_knowledge_request_result(enabled=_memory_enabled())
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        return result

    normalized, warnings, errors = _validate_knowledge_request_inputs(
        source_type=source_type,
        source_id=source_id,
        candidate_classification=candidate_classification,
        candidate_summary=candidate_summary,
        candidate_details=candidate_details,
        run_history_id=run_history_id,
        created_by=created_by,
        metadata=metadata,
    )
    result["warnings"].extend(warnings)
    if errors:
        result["success"] = False
        result["errors"].extend(errors)
        return result

    try:
        request_id = memory_agent.insert_knowledge_update_request(
            source_type=normalized["source_type"],
            source_id=normalized["source_id"],
            run_history_id=normalized["run_history_id"],
            candidate_classification=normalized["candidate_classification"],
            candidate_summary=normalized["candidate_summary"],
            candidate_details=normalized["candidate_details"],
            created_by=normalized["created_by"],
            metadata=normalized["metadata"],
        )
        result.update(
            {
                "success": True,
                "request_id": request_id,
                "source_type": normalized["source_type"],
                "source_id": normalized["source_id"],
                "approval_status": "PENDING",
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        if _memory_debug_enabled():
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def approve_knowledge_update_request(
    request_id: int,
    approval_status: str,
    approved_by: str | None = None,
    approval_notes: str | None = None,
) -> dict[str, Any]:
    """Update governance approval metadata without applying knowledge changes."""

    result = _base_knowledge_approval_result(enabled=_memory_enabled())
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        return result

    normalized, warnings, errors = _validate_knowledge_approval_inputs(
        request_id=request_id,
        approval_status=approval_status,
        approved_by=approved_by,
        approval_notes=approval_notes,
    )
    result["warnings"].extend(warnings)
    if errors:
        result["success"] = False
        result["errors"].extend(errors)
        return result

    try:
        updated_request_id = memory_agent.update_knowledge_update_request_status(
            request_id=normalized["request_id"],
            approval_status=normalized["approval_status"],
            approved_by=normalized["approved_by"],
            approval_notes=normalized["approval_notes"],
        )
        result.update(
            {
                "success": True,
                "request_id": updated_request_id,
                "approval_status": normalized["approval_status"],
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        if _memory_debug_enabled():
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def materialize_knowledge_artifact(
    request_id: int,
    artifact_type: str,
    artifact_classification: str | None = None,
    artifact_summary: str | None = None,
    artifact_details: str | None = None,
    created_by: str | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]:
    """Materialize an approved request into an inactive knowledge artifact."""

    result = _base_knowledge_artifact_result(enabled=_memory_enabled())
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        return result

    normalized, warnings, errors = _validate_knowledge_artifact_inputs(
        request_id=request_id,
        artifact_type=artifact_type,
        artifact_classification=artifact_classification,
        artifact_summary=artifact_summary,
        artifact_details=artifact_details,
        created_by=created_by,
        metadata=metadata,
    )
    result["warnings"].extend(warnings)
    if errors:
        result["success"] = False
        result["errors"].extend(errors)
        return result

    try:
        artifact_id = memory_agent.insert_knowledge_artifact(
            request_id=normalized["request_id"],
            artifact_type=normalized["artifact_type"],
            artifact_classification=normalized["artifact_classification"],
            artifact_summary=normalized["artifact_summary"],
            artifact_details=normalized["artifact_details"],
            created_by=normalized["created_by"],
            metadata=normalized["metadata"],
        )
        result.update(
            {
                "success": True,
                "artifact_id": artifact_id,
                "request_id": normalized["request_id"],
                "artifact_type": normalized["artifact_type"],
                "activation_status": "INACTIVE",
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        if _memory_debug_enabled():
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def list_knowledge_artifacts(limit: int = 50) -> dict[str, Any]:
    """List materialized knowledge artifacts for inspection only."""

    result = {
        "enabled": _memory_enabled(),
        "success": True,
        "artifacts": [],
        "skipped": [],
        "warnings": [],
        "errors": [],
    }
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        return result
    try:
        result["artifacts"] = memory_agent.list_knowledge_artifacts(limit=limit)
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        if _memory_debug_enabled():
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def get_knowledge_artifact(artifact_id: int) -> dict[str, Any]:
    """Return one materialized knowledge artifact for inspection only."""

    result = {
        "enabled": _memory_enabled(),
        "success": True,
        "artifact": None,
        "skipped": [],
        "warnings": [],
        "errors": [],
    }
    if not result["enabled"]:
        result["skipped"].append("memory_disabled")
        return result
    normalized_artifact_id = _positive_int(artifact_id)
    if normalized_artifact_id is None:
        result["success"] = False
        result["errors"].append("artifact_id is required and must be an integer greater than 0")
        return result
    try:
        artifact = memory_agent.get_knowledge_artifact(artifact_id=normalized_artifact_id)
        if artifact is None:
            result["success"] = False
            result["errors"].append("artifact_id must reference an existing knowledge artifact")
            return result
        result["artifact"] = artifact
        return result
    except Exception as exc:  # noqa: BLE001
        result["success"] = False
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        if _memory_debug_enabled():
            result["diagnostics"] = {
                "traceback": traceback.format_exc(),
            }
        return result


def _base_result(enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "success": True,
        "run_history_id": None,
        "persisted": {},
        "skipped": [],
        "warnings": [],
        "errors": [],
    }


def _base_action_result(enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "success": True,
        "action_history_id": None,
        "run_history_id": None,
        "recommendation_history_id": None,
        "action_type": None,
        "action_status": None,
        "skipped": [],
        "warnings": [],
        "errors": [],
    }


def _base_outcome_result(enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "success": True,
        "outcome_id": None,
        "action_outcome_id": None,
        "run_history_id": None,
        "action_history_id": None,
        "outcome_status": None,
        "message": "",
        "skipped": [],
        "warnings": [],
        "errors": [],
    }


def _base_feedback_result(enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "success": True,
        "feedback_id": None,
        "run_history_id": None,
        "feedback_type": None,
        "feedback_rating": None,
        "skipped": [],
        "warnings": [],
        "errors": [],
    }


def _base_unknown_signal_review_result(enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "success": True,
        "unknown_signal_id": None,
        "review_status": None,
        "review_classification": None,
        "skipped": [],
        "warnings": [],
        "errors": [],
    }


def _base_knowledge_request_result(enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "success": True,
        "request_id": None,
        "source_type": None,
        "source_id": None,
        "approval_status": None,
        "skipped": [],
        "warnings": [],
        "errors": [],
    }


def _base_knowledge_approval_result(enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "success": True,
        "request_id": None,
        "approval_status": None,
        "skipped": [],
        "warnings": [],
        "errors": [],
    }


def _base_knowledge_artifact_result(enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "success": True,
        "artifact_id": None,
        "request_id": None,
        "artifact_type": None,
        "activation_status": None,
        "skipped": [],
        "warnings": [],
        "errors": [],
    }


def _memory_enabled(options: dict | None = None) -> bool:
    option_value = (options or {}).get("enabled")
    if isinstance(option_value, bool):
        return option_value
    env_value = str(os.getenv("AWR_MEMORY_ENABLED", "") or "").strip().lower()
    if env_value in DISABLED_VALUES:
        return False
    if env_value in ENABLED_VALUES:
        return True
    return True


def _memory_debug_enabled(options: dict | None = None) -> bool:
    option_value = (options or {}).get("debug")
    if isinstance(option_value, bool):
        return option_value
    return str(os.getenv("AWR_MEMORY_DEBUG", "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _validate_inputs(phase4i_output: Any, source_context: Any) -> list[str]:
    warnings: list[str] = []
    if not isinstance(phase4i_output, dict):
        warnings.append("phase4i_output is not a dict")
        return warnings
    if not isinstance(source_context, dict):
        warnings.append("source_context is not a dict; using empty context")
    for key in EXPECTED_PHASE4I_KEYS:
        if key not in phase4i_output:
            warnings.append(f"phase4i_output missing key: {key}")
    return warnings


def _validate_action_inputs(
    *,
    run_history_id: Any,
    action_type: Any,
    action_summary: Any,
    action_status: Any,
    recommendation_history_id: Any,
    actor: Any,
    notes: Any,
    action_metadata: Any,
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized: dict[str, Any] = {}

    normalized["run_history_id"] = _positive_int(run_history_id)
    if normalized["run_history_id"] is None:
        errors.append("run_history_id is required and must be an integer greater than 0")

    normalized["recommendation_history_id"] = None
    if recommendation_history_id is not None:
        normalized["recommendation_history_id"] = _positive_int(recommendation_history_id)
        if normalized["recommendation_history_id"] is None:
            errors.append("recommendation_history_id must be an integer greater than 0")

    normalized["action_type"] = _normalize_token(action_type)
    if not normalized["action_type"]:
        errors.append("action_type is required")

    summary = str(action_summary or "").strip()
    if not summary:
        errors.append("action_summary is required")
    elif len(summary) > ACTION_SUMMARY_MAX_LENGTH:
        errors.append(f"action_summary must be {ACTION_SUMMARY_MAX_LENGTH} characters or fewer")
    normalized["action_summary"] = summary

    normalized["action_status"] = _normalize_token(action_status or "RECORDED")
    if not normalized["action_status"]:
        normalized["action_status"] = "RECORDED"
    if normalized["action_status"] not in ACTION_STATUS_VALUES:
        errors.append(
            "action_status must be one of: "
            + ", ".join(sorted(ACTION_STATUS_VALUES))
        )

    normalized["actor"] = _default_actor(actor)
    normalized["notes"] = _compose_action_notes(notes, action_metadata, warnings)
    return normalized, warnings, errors


def _validate_outcome_inputs(
    *,
    run_history_id: Any,
    action_history_id: Any,
    outcome_status: Any,
    outcome_summary: Any,
    before_metrics: Any,
    after_metrics: Any,
    impact_score: Any,
    recorded_by: Any,
    notes: Any,
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized: dict[str, Any] = {}

    normalized["run_history_id"] = _positive_int(run_history_id)
    if normalized["run_history_id"] is None:
        errors.append("run_history_id is required and must be an integer greater than 0")

    normalized["action_history_id"] = _positive_int(action_history_id)
    if normalized["action_history_id"] is None:
        errors.append("action_history_id is required and must be an integer greater than 0")

    normalized["outcome_status"] = _normalize_token(outcome_status)
    if normalized["outcome_status"] not in OUTCOME_STATUS_VALUES:
        errors.append(
            "outcome_status must be one of: "
            + ", ".join(sorted(OUTCOME_STATUS_VALUES))
        )

    summary = str(outcome_summary or "").strip()
    if not summary:
        errors.append("outcome_summary is required")
    elif len(summary) > OUTCOME_SUMMARY_MAX_LENGTH:
        errors.append(f"outcome_summary must be {OUTCOME_SUMMARY_MAX_LENGTH} characters or fewer")
    normalized["outcome_summary"] = summary

    normalized["before_metrics"] = _optional_dict(
        before_metrics,
        "before_metrics",
        warnings,
        errors,
    )
    normalized["after_metrics"] = _optional_dict(
        after_metrics,
        "after_metrics",
        warnings,
        errors,
    )
    normalized["impact_score"] = _optional_float(impact_score, errors)
    normalized["recorded_by"] = _default_actor(recorded_by)
    normalized["notes"] = _compose_outcome_notes(notes, warnings, errors)
    return normalized, warnings, errors


def _validate_feedback_inputs(
    *,
    run_history_id: Any,
    recommendation_history_id: Any,
    action_history_id: Any,
    action_outcome_id: Any,
    feedback_type: Any,
    feedback_rating: Any,
    feedback_summary: Any,
    feedback_detail: Any,
    feedback_source: Any,
    recorded_by: Any,
    metadata: Any,
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized: dict[str, Any] = {}

    normalized["run_history_id"] = _positive_int(run_history_id)
    if normalized["run_history_id"] is None:
        errors.append("run_history_id is required and must be an integer greater than 0")

    for field_name, raw_value in (
        ("recommendation_history_id", recommendation_history_id),
        ("action_history_id", action_history_id),
        ("action_outcome_id", action_outcome_id),
    ):
        normalized[field_name] = None
        if raw_value is not None:
            normalized[field_name] = _positive_int(raw_value)
            if normalized[field_name] is None:
                errors.append(f"{field_name} must be an integer greater than 0")

    normalized["feedback_type"] = _normalize_token(feedback_type)
    if not normalized["feedback_type"]:
        errors.append("feedback_type is required")
    elif normalized["feedback_type"] not in FEEDBACK_TYPE_VALUES:
        warnings.append(
            f"unsupported feedback_type {normalized['feedback_type']}; using GENERAL"
        )
        normalized["feedback_type"] = "GENERAL"

    normalized["feedback_rating"] = _normalize_token(feedback_rating)
    if normalized["feedback_rating"] not in FEEDBACK_RATING_VALUES:
        errors.append(
            "feedback_rating must be one of: "
            + ", ".join(sorted(FEEDBACK_RATING_VALUES))
        )

    summary = str(feedback_summary or "").strip()
    if not summary:
        errors.append("feedback_summary is required")
    elif len(summary) > FEEDBACK_SUMMARY_MAX_LENGTH:
        errors.append(f"feedback_summary must be {FEEDBACK_SUMMARY_MAX_LENGTH} characters or fewer")
    normalized["feedback_summary"] = summary

    detail = str(feedback_detail or "").strip()
    normalized["feedback_detail"] = detail or None

    normalized["feedback_source"] = _normalize_token(feedback_source or "OTHER")
    if normalized["feedback_source"] not in FEEDBACK_SOURCE_VALUES:
        warnings.append(
            f"unsupported feedback_source {normalized['feedback_source']}; using OTHER"
        )
        normalized["feedback_source"] = "OTHER"

    normalized["recorded_by"] = _default_actor(recorded_by)
    normalized["metadata"] = _optional_dict(metadata, "metadata", warnings, errors)
    return normalized, warnings, errors


def _validate_unknown_signal_review_inputs(
    *,
    unknown_signal_id: Any,
    review_status: Any,
    review_classification: Any,
    review_notes: Any,
    reviewed_by: Any,
    metadata: Any,
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized: dict[str, Any] = {}

    normalized["unknown_signal_id"] = _positive_int(unknown_signal_id)
    if normalized["unknown_signal_id"] is None:
        errors.append("unknown_signal_id is required and must be an integer greater than 0")

    normalized["review_status"] = _normalize_token(review_status)
    if normalized["review_status"] not in UNKNOWN_SIGNAL_REVIEW_STATUS_VALUES:
        errors.append(
            "review_status must be one of: "
            + ", ".join(sorted(UNKNOWN_SIGNAL_REVIEW_STATUS_VALUES))
        )

    normalized["review_classification"] = None
    if review_classification is not None and str(review_classification).strip():
        normalized["review_classification"] = _normalize_token(review_classification)
        if normalized["review_classification"] not in UNKNOWN_SIGNAL_REVIEW_CLASSIFICATION_VALUES:
            errors.append(
                "review_classification must be one of: "
                + ", ".join(sorted(UNKNOWN_SIGNAL_REVIEW_CLASSIFICATION_VALUES))
            )

    notes = str(review_notes or "").strip()
    if len(notes) > UNKNOWN_SIGNAL_REVIEW_NOTES_MAX_LENGTH:
        errors.append(
            f"review_notes must be {UNKNOWN_SIGNAL_REVIEW_NOTES_MAX_LENGTH} characters or fewer"
        )
    normalized["review_notes"] = notes or None
    normalized["reviewed_by"] = _default_actor(reviewed_by)
    normalized["metadata"] = _optional_dict(metadata, "metadata", warnings, errors)
    return normalized, warnings, errors


def _validate_knowledge_request_inputs(
    *,
    source_type: Any,
    source_id: Any,
    candidate_classification: Any,
    candidate_summary: Any,
    candidate_details: Any,
    run_history_id: Any,
    created_by: Any,
    metadata: Any,
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized: dict[str, Any] = {}

    normalized["source_type"] = _normalize_token(source_type)
    if normalized["source_type"] not in KNOWLEDGE_SOURCE_TYPE_VALUES:
        errors.append(
            "source_type must be one of: "
            + ", ".join(sorted(KNOWLEDGE_SOURCE_TYPE_VALUES))
        )

    normalized["source_id"] = _positive_int(source_id)
    if normalized["source_id"] is None:
        errors.append("source_id is required and must be an integer greater than 0")

    normalized["run_history_id"] = None
    if run_history_id is not None:
        normalized["run_history_id"] = _positive_int(run_history_id)
        if normalized["run_history_id"] is None:
            errors.append("run_history_id must be an integer greater than 0")

    classification = _normalize_token(candidate_classification)
    normalized["candidate_classification"] = classification or None

    summary = str(candidate_summary or "").strip()
    if not summary:
        errors.append("candidate_summary is required")
    elif len(summary) > KNOWLEDGE_REQUEST_SUMMARY_MAX_LENGTH:
        errors.append(
            f"candidate_summary must be {KNOWLEDGE_REQUEST_SUMMARY_MAX_LENGTH} characters or fewer"
        )
    normalized["candidate_summary"] = summary

    details = str(candidate_details or "").strip()
    normalized["candidate_details"] = details or None
    normalized["created_by"] = _default_actor(created_by)
    normalized["metadata"] = _optional_dict(metadata, "metadata", warnings, errors)
    return normalized, warnings, errors


def _validate_knowledge_approval_inputs(
    *,
    request_id: Any,
    approval_status: Any,
    approved_by: Any,
    approval_notes: Any,
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized: dict[str, Any] = {}

    normalized["request_id"] = _positive_int(request_id)
    if normalized["request_id"] is None:
        errors.append("request_id is required and must be an integer greater than 0")

    normalized["approval_status"] = _normalize_token(approval_status)
    if normalized["approval_status"] not in KNOWLEDGE_APPROVAL_STATUS_VALUES:
        errors.append(
            "approval_status must be one of: "
            + ", ".join(sorted(KNOWLEDGE_APPROVAL_STATUS_VALUES))
        )

    normalized["approved_by"] = _default_actor(approved_by)
    notes = str(approval_notes or "").strip()
    normalized["approval_notes"] = notes or None
    return normalized, warnings, errors


def _validate_knowledge_artifact_inputs(
    *,
    request_id: Any,
    artifact_type: Any,
    artifact_classification: Any,
    artifact_summary: Any,
    artifact_details: Any,
    created_by: Any,
    metadata: Any,
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized: dict[str, Any] = {}

    normalized["request_id"] = _positive_int(request_id)
    if normalized["request_id"] is None:
        errors.append("request_id is required and must be an integer greater than 0")

    normalized["artifact_type"] = _normalize_token(artifact_type)
    if normalized["artifact_type"] not in KNOWLEDGE_ARTIFACT_TYPE_VALUES:
        errors.append(
            "artifact_type must be one of: "
            + ", ".join(sorted(KNOWLEDGE_ARTIFACT_TYPE_VALUES))
        )

    classification = _normalize_token(artifact_classification)
    normalized["artifact_classification"] = classification or None

    summary = str(artifact_summary or "").strip()
    if len(summary) > KNOWLEDGE_ARTIFACT_SUMMARY_MAX_LENGTH:
        errors.append(
            f"artifact_summary must be {KNOWLEDGE_ARTIFACT_SUMMARY_MAX_LENGTH} characters or fewer"
        )
    normalized["artifact_summary"] = summary or None

    details = str(artifact_details or "").strip()
    normalized["artifact_details"] = details or None
    normalized["created_by"] = _default_actor(created_by)
    normalized["metadata"] = _optional_dict(metadata, "metadata", warnings, errors)
    return normalized, warnings, errors


def _positive_int(value: Any) -> int | None:
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return None
    return integer if integer > 0 else None


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "_", text)
    return text.strip("_")


def _default_actor(actor: Any) -> str:
    text = str(actor or "").strip()
    if text:
        return text
    return (
        os.getenv("USER")
        or os.getenv("USERNAME")
        or "unknown"
    )


def _compose_action_notes(
    notes: Any,
    action_metadata: Any,
    warnings: list[str],
) -> str | None:
    parts = []
    notes_text = str(notes or "").strip()
    if notes_text:
        parts.append(notes_text)
    if action_metadata is not None:
        if isinstance(action_metadata, dict):
            metadata_json = json.dumps(action_metadata, sort_keys=True)
            if "client_request_id" in action_metadata:
                warnings.append(
                    "client_request_id received; action tracking is append-only because the current schema has no idempotency column"
                )
            parts.append(f"Action metadata JSON: {metadata_json}")
        else:
            warnings.append("action_metadata ignored because it is not a dict")
    return "\n\n".join(parts) if parts else None


def _optional_dict(
    value: Any,
    field_name: str,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    errors.append(f"{field_name} must be a dict when provided")
    return None


def _optional_float(value: Any, errors: list[str]) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append("impact_score must be numeric when provided")
        return None


def _compose_outcome_notes(
    notes: Any,
    warnings: list[str],
    errors: list[str],
) -> str | None:
    if notes is None:
        return None
    if isinstance(notes, dict):
        return json.dumps(notes, sort_keys=True)
    text = str(notes).strip()
    return text or None


# Phase 6H — Action Tracking extension point.
# Phase 6I — Outcome Tracking records append-only observed outcomes; it is
# downstream-only and must not influence deterministic advisory behavior.
# Phase 6J — Feedback Capture records append-only human/operator review and is
# downstream-only; it must not influence scoring, parser behavior, decision
# posture, or deterministic recommendation generation.
# Phase 6K — Unknown Signal Review captures human classifications for parser
# improvement candidates. It must not modify parser behavior or runtime analysis.
# Phase 6L — Approval Workflow is the only governance gateway for future
# knowledge update eligibility. Approval must not apply changes or influence
# runtime analysis.
# Phase 6M — Controlled Knowledge Update materializes approved requests as
# inactive artifacts only. Activation is a future phase and must not affect
# runtime analysis here.
# Phase 6N — Memory Recall APIs extension point.
# Phase 6N.1 — Oracle Agent Memory Adapter extension point.
# Oracle Agent Memory, if added in Phase 6N.1, is a non-authoritative recall and phrasing context layer. It must never influence scoring, parser behavior, decision posture, or deterministic recommendation generation.
