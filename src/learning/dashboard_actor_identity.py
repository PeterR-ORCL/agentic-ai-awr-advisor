"""Local Phase 7AE dashboard actor/reviewer identity model.

This module defines deterministic identity and audit-context metadata for
future governed dashboard workflows. It does not implement authentication,
authorization enforcement, dashboard UI, backend execution, write paths,
database writes, network calls, or runtime mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


ACTOR_ROLES = (
    "viewer",
    "reviewer",
    "approver",
    "operator",
    "admin",
    "system",
)

ACTOR_SOURCES = (
    "local",
    "cli",
    "dashboard",
    "system",
    "unknown",
)

PERMISSION_SCOPES = (
    "read_only",
    "review",
    "approve",
    "execute",
    "administer",
)

_FORBIDDEN_IDENTITY_FIELDS = (
    "runtime_influence",
    "runtime_active",
    "runtime_authority",
    "authorization_granted",
    "mutation_authorized",
)


class DashboardActorIdentityError(ValueError):
    """Raised when actor identity metadata violates Phase 7AE rules."""


@dataclass(frozen=True)
class DashboardActorIdentity:
    """Local actor identity metadata for future dashboard workflows."""

    actor_id: str
    display_name: str
    role: str
    actor_source: str
    permission_scope: str
    authenticated: bool
    email: str | None = None
    organization: str | None = None
    audit_reference: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.actor_id, "actor_id")
        _require_nonempty_string(self.display_name, "display_name")
        _require_supported(self.role, ACTOR_ROLES, "role")
        _require_supported(self.actor_source, ACTOR_SOURCES, "actor_source")
        _require_supported(self.permission_scope, PERMISSION_SCOPES, "permission_scope")
        _require_boolean(self.authenticated, "authenticated")
        _require_optional_string(self.email, "email")
        _require_optional_string(self.organization, "organization")
        _require_optional_string(self.audit_reference, "audit_reference")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class ActorAuditContext:
    """Actor metadata copied into future audit records.

    The context is trace metadata only. It does not authorize action by itself.
    """

    audit_context_id: str
    actor_id: str
    display_name: str
    role: str
    actor_source: str
    permission_scope: str
    authenticated: bool
    audit_reference: str | None = None
    action_scope: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.audit_context_id, "audit_context_id")
        _require_nonempty_string(self.actor_id, "actor_id")
        _require_nonempty_string(self.display_name, "display_name")
        _require_supported(self.role, ACTOR_ROLES, "role")
        _require_supported(self.actor_source, ACTOR_SOURCES, "actor_source")
        _require_supported(self.permission_scope, PERMISSION_SCOPES, "permission_scope")
        _require_boolean(self.authenticated, "authenticated")
        _require_optional_string(self.audit_reference, "audit_reference")
        _require_optional_string(self.action_scope, "action_scope")
        _require_optional_string(self.notes, "notes")


def create_actor_id(
    display_name: str,
    actor_source: str = "local",
    email: str | None = None,
) -> str:
    """Create a deterministic actor id from source and display/email metadata."""

    _require_nonempty_string(display_name, "display_name")
    _require_supported(actor_source, ACTOR_SOURCES, "actor_source")
    _require_optional_string(email, "email")
    subject = email if email else display_name
    return f"ACTOR-{_normalize_token(actor_source)}-{_normalize_token(subject)}"


def create_audit_context_id(actor_id: str, action_scope: str | None = None) -> str:
    """Create a deterministic actor audit context id."""

    _require_nonempty_string(actor_id, "actor_id")
    _require_optional_string(action_scope, "action_scope")
    action_token = action_scope if action_scope else "general"
    return (
        f"ACTOR-AUDIT-{_normalize_token(actor_id)}-"
        f"{_normalize_token(action_token)}"
    )


def validate_dashboard_actor_identity(
    actor: DashboardActorIdentity,
) -> DashboardActorIdentity:
    """Validate and return local actor identity metadata."""

    if not isinstance(actor, DashboardActorIdentity):
        raise DashboardActorIdentityError(
            "actor must be a DashboardActorIdentity instance."
        )
    actor.__post_init__()
    return actor


def validate_actor_audit_context(context: ActorAuditContext) -> ActorAuditContext:
    """Validate and return local actor audit context metadata."""

    if not isinstance(context, ActorAuditContext):
        raise DashboardActorIdentityError(
            "context must be an ActorAuditContext instance."
        )
    context.__post_init__()
    return context


def dashboard_actor_identity_to_dict(
    actor: DashboardActorIdentity,
) -> dict[str, Any]:
    """Serialize actor identity metadata to a deterministic dictionary."""

    actor = validate_dashboard_actor_identity(actor)
    return {
        "actor_id": actor.actor_id,
        "display_name": actor.display_name,
        "role": actor.role,
        "actor_source": actor.actor_source,
        "permission_scope": actor.permission_scope,
        "authenticated": actor.authenticated,
        "email": actor.email,
        "organization": actor.organization,
        "audit_reference": actor.audit_reference,
        "created_at": actor.created_at,
        "notes": actor.notes,
    }


def dashboard_actor_identity_from_dict(
    data: dict[str, Any],
) -> DashboardActorIdentity:
    """Deserialize actor identity metadata from a dictionary."""

    _require_mapping(data, "actor")
    _reject_forbidden_fields(data, "actor")
    return DashboardActorIdentity(
        actor_id=data.get("actor_id"),
        display_name=data.get("display_name"),
        role=data.get("role"),
        actor_source=data.get("actor_source"),
        permission_scope=data.get("permission_scope"),
        authenticated=data.get("authenticated"),
        email=data.get("email"),
        organization=data.get("organization"),
        audit_reference=data.get("audit_reference"),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def actor_audit_context_to_dict(context: ActorAuditContext) -> dict[str, Any]:
    """Serialize actor audit context metadata to a deterministic dictionary."""

    context = validate_actor_audit_context(context)
    return {
        "audit_context_id": context.audit_context_id,
        "actor_id": context.actor_id,
        "display_name": context.display_name,
        "role": context.role,
        "actor_source": context.actor_source,
        "permission_scope": context.permission_scope,
        "authenticated": context.authenticated,
        "audit_reference": context.audit_reference,
        "action_scope": context.action_scope,
        "notes": context.notes,
    }


def actor_audit_context_from_dict(data: dict[str, Any]) -> ActorAuditContext:
    """Deserialize actor audit context metadata from a dictionary."""

    _require_mapping(data, "context")
    _reject_forbidden_fields(data, "context")
    return ActorAuditContext(
        audit_context_id=data.get("audit_context_id"),
        actor_id=data.get("actor_id"),
        display_name=data.get("display_name"),
        role=data.get("role"),
        actor_source=data.get("actor_source"),
        permission_scope=data.get("permission_scope"),
        authenticated=data.get("authenticated"),
        audit_reference=data.get("audit_reference"),
        action_scope=data.get("action_scope"),
        notes=data.get("notes"),
    )


def create_system_actor(notes: str | None = None) -> DashboardActorIdentity:
    """Create deterministic system actor metadata for system-generated context."""

    _require_optional_string(notes, "notes")
    return DashboardActorIdentity(
        actor_id=create_actor_id("System", actor_source="system"),
        display_name="System",
        role="system",
        actor_source="system",
        permission_scope="read_only",
        authenticated=False,
        notes=notes,
    )


def create_unknown_actor(notes: str | None = None) -> DashboardActorIdentity:
    """Create deterministic unknown actor metadata for safe fallback context."""

    _require_optional_string(notes, "notes")
    return DashboardActorIdentity(
        actor_id=create_actor_id("Unknown Actor", actor_source="unknown"),
        display_name="Unknown Actor",
        role="viewer",
        actor_source="unknown",
        permission_scope="read_only",
        authenticated=False,
        notes=notes,
    )


def create_actor_audit_context(
    actor: DashboardActorIdentity,
    action_scope: str | None = None,
    notes: str | None = None,
) -> ActorAuditContext:
    """Create deterministic audit context metadata from an actor."""

    actor = validate_dashboard_actor_identity(actor)
    _require_optional_string(action_scope, "action_scope")
    _require_optional_string(notes, "notes")
    return ActorAuditContext(
        audit_context_id=create_audit_context_id(actor.actor_id, action_scope),
        actor_id=actor.actor_id,
        display_name=actor.display_name,
        role=actor.role,
        actor_source=actor.actor_source,
        permission_scope=actor.permission_scope,
        authenticated=actor.authenticated,
        audit_reference=actor.audit_reference,
        action_scope=action_scope,
        notes=notes,
    )


def actor_can_request_review(actor: DashboardActorIdentity) -> bool:
    """Return conservative review-request metadata; this is not authorization."""

    actor = validate_dashboard_actor_identity(actor)
    return (
        actor.role in {"reviewer", "approver", "operator", "admin"}
        and actor.permission_scope in {"review", "approve", "execute", "administer"}
    )


def actor_can_request_approval(actor: DashboardActorIdentity) -> bool:
    """Return conservative approval-request metadata; this is not authorization."""

    actor = validate_dashboard_actor_identity(actor)
    return (
        actor.role in {"approver", "admin"}
        and actor.permission_scope in {"approve", "administer"}
    )


def actor_can_request_execution(actor: DashboardActorIdentity) -> bool:
    """Return conservative execution-request metadata; this is not authorization."""

    actor = validate_dashboard_actor_identity(actor)
    return (
        actor.role in {"operator", "admin"}
        and actor.permission_scope in {"execute", "administer"}
    )


def _normalize_token(value: str) -> str:
    _require_nonempty_string(value, "value")
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "UNKNOWN"


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DashboardActorIdentityError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise DashboardActorIdentityError(f"{field_name} must be a string or None.")
    return value


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> str:
    if not isinstance(value, str) or value not in supported:
        raise DashboardActorIdentityError(f"Unsupported {field_name}: {value!r}.")
    return value


def _require_boolean(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise DashboardActorIdentityError(f"{field_name} must be boolean.")
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DashboardActorIdentityError(f"{field_name} must be a dictionary.")
    return value


def _reject_forbidden_fields(data: dict[str, Any], field_name: str) -> None:
    present = sorted(field for field in _FORBIDDEN_IDENTITY_FIELDS if field in data)
    if present:
        raise DashboardActorIdentityError(
            f"{field_name} contains forbidden runtime authority fields: {present}"
        )
