"""Phase 6 memory orchestration for deterministic AWR analysis runs."""

from __future__ import annotations

import os
import json
import re
import traceback
from typing import Any

from src.memory import memory_agent

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
# Phase 6J — Feedback Capture extension point.
# Phase 6L — Approval Workflow extension point.
# Phase 6M — Knowledge Update Workflow extension point.
# Phase 6N — Memory Recall APIs extension point.
# Phase 6N.1 — Oracle Agent Memory Adapter extension point.
# Oracle Agent Memory, if added in Phase 6N.1, is a non-authoritative recall and phrasing context layer. It must never influence scoring, parser behavior, decision posture, or deterministic recommendation generation.
