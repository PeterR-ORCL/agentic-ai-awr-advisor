"""Controlled Phase 7N materialization artifact model.

Materialization artifacts are local governed work items created from already
approved learning candidates. They do not activate runtime behavior, write
state, call services, or modify parser, scoring, decision, recommendation,
dashboard, or CLI code.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence

from src.learning.learning_candidate_model import APPROVED_FOR_IMPLEMENTATION, LearningCandidate
from src.learning.materialization_boundary import validate_materialization_boundary


PROPOSED = "PROPOSED"
APPROVED_FOR_MATERIALIZATION = "APPROVED_FOR_MATERIALIZATION"
MATERIALIZED = "MATERIALIZED"
VALIDATED = "VALIDATED"
REJECTED = "REJECTED"
ROLLED_BACK = "ROLLED_BACK"
CLOSED = "CLOSED"

MATERIALIZATION_STATUSES = (
    PROPOSED,
    APPROVED_FOR_MATERIALIZATION,
    MATERIALIZED,
    VALIDATED,
    REJECTED,
    ROLLED_BACK,
    CLOSED,
)

PARSER_MAPPING_ARTIFACT = "parser_mapping_artifact"
SCORING_REVIEW_ARTIFACT = "scoring_review_artifact"
RECOMMENDATION_RULE_ARTIFACT = "recommendation_rule_artifact"
DASHBOARD_WORDING_ARTIFACT = "dashboard_wording_artifact"
DASHBOARD_INTERACTION_ARTIFACT = "dashboard_interaction_artifact"
GOVERNANCE_WORKFLOW_ARTIFACT = "governance_workflow_artifact"
SEMANTIC_SUMMARY_ARTIFACT = "semantic_summary_artifact"
DOCUMENTATION_ARTIFACT = "documentation_artifact"
VALIDATION_ARTIFACT = "validation_artifact"

MATERIALIZATION_ARTIFACT_TYPES = (
    PARSER_MAPPING_ARTIFACT,
    SCORING_REVIEW_ARTIFACT,
    RECOMMENDATION_RULE_ARTIFACT,
    DASHBOARD_WORDING_ARTIFACT,
    DASHBOARD_INTERACTION_ARTIFACT,
    GOVERNANCE_WORKFLOW_ARTIFACT,
    SEMANTIC_SUMMARY_ARTIFACT,
    DOCUMENTATION_ARTIFACT,
    VALIDATION_ARTIFACT,
)

RUNTIME_SENSITIVE_ARTIFACT_TYPES = (
    PARSER_MAPPING_ARTIFACT,
    SCORING_REVIEW_ARTIFACT,
    RECOMMENDATION_RULE_ARTIFACT,
)

CANDIDATE_TYPE_TO_ARTIFACT_TYPE = {
    "parser_mapping_candidate": PARSER_MAPPING_ARTIFACT,
    "scoring_weight_review_candidate": SCORING_REVIEW_ARTIFACT,
    "recommendation_rule_candidate": RECOMMENDATION_RULE_ARTIFACT,
    "dashboard_wording_candidate": DASHBOARD_WORDING_ARTIFACT,
    "dashboard_interaction_candidate": DASHBOARD_INTERACTION_ARTIFACT,
    "governance_workflow_candidate": GOVERNANCE_WORKFLOW_ARTIFACT,
    "semantic_summary_candidate": SEMANTIC_SUMMARY_ARTIFACT,
    "documentation_candidate": DOCUMENTATION_ARTIFACT,
    "validation_candidate": VALIDATION_ARTIFACT,
}

MATERIALIZATION_ARTIFACT_FIELDS = (
    "materialization_id",
    "source_candidate_id",
    "candidate_type",
    "affected_component",
    "affected_domain",
    "proposed_change_summary",
    "proposed_artifact_type",
    "implementation_reference",
    "validation_requirements",
    "rollback_plan",
    "runtime_influence_requested",
    "runtime_influence_granted",
    "status",
    "actor",
    "approval_reference",
    "created_at",
    "reviewed_by",
    "validation_reference",
    "source_evidence",
    "semantic_context",
)

_REQUIRED_VALIDATION_REQUIREMENTS = {
    PARSER_MAPPING_ARTIFACT: (
        "parser tests",
        "AWR regression validation",
        "Phase 4I contract validation",
        "unknown signal safety",
        "scoring regression check",
    ),
    SCORING_REVIEW_ARTIFACT: (
        "versioned scoring config",
        "before/after comparison",
        "scoring regression tests",
        "Phase 4I scores contract validation",
        "rollback plan",
    ),
    RECOMMENDATION_RULE_ARTIFACT: (
        "versioned recommendation rule/config",
        "recommendation regression tests",
        "evidence mapping validation",
        "Phase 4I recommendations contract validation",
        "rollback plan",
    ),
    DASHBOARD_WORDING_ARTIFACT: (
        "dashboard rendering validation",
        "safety label preservation if applicable",
        "read-only behavior preservation if applicable",
    ),
    DASHBOARD_INTERACTION_ARTIFACT: (
        "dashboard rendering validation",
        "safety label preservation if applicable",
        "read-only behavior preservation if applicable",
    ),
    GOVERNANCE_WORKFLOW_ARTIFACT: (
        "actor requirement validation",
        "approval boundary validation",
        "audit trail validation",
    ),
    SEMANTIC_SUMMARY_ARTIFACT: (
        "reviewer-assist only validation",
        "non-authoritative validation",
        "not source evidence validation",
    ),
    DOCUMENTATION_ARTIFACT: (
        "doc review",
        "boundary language preservation",
    ),
    VALIDATION_ARTIFACT: (
        "validation command update",
        "regression test coverage",
    ),
}

_REQUIRED_VALIDATION_CONCEPTS = {
    PARSER_MAPPING_ARTIFACT: (
        ("parser", "test"),
        ("awr", "regression"),
        ("phase", "4i", "contract"),
        ("unknown", "signal", "safety"),
        ("scoring", "regression"),
    ),
    SCORING_REVIEW_ARTIFACT: (
        ("versioned", "scoring", "config"),
        ("before", "after", "comparison"),
        ("scoring", "regression", "test"),
        ("phase", "4i", "scores", "contract"),
        ("rollback", "plan"),
    ),
    RECOMMENDATION_RULE_ARTIFACT: (
        ("versioned", "recommendation", "rule"),
        ("recommendation", "regression", "test"),
        ("evidence", "mapping"),
        ("phase", "4i", "recommendations", "contract"),
        ("rollback", "plan"),
    ),
    DASHBOARD_WORDING_ARTIFACT: (
        ("dashboard", "rendering"),
        ("safety", "label"),
        ("read", "only", "behavior"),
    ),
    DASHBOARD_INTERACTION_ARTIFACT: (
        ("dashboard", "rendering"),
        ("safety", "label"),
        ("read", "only", "behavior"),
    ),
    GOVERNANCE_WORKFLOW_ARTIFACT: (
        ("actor", "requirement"),
        ("approval", "boundary"),
        ("audit", "trail"),
    ),
    SEMANTIC_SUMMARY_ARTIFACT: (
        ("reviewer", "assist"),
        ("non", "authoritative"),
        ("not", "source", "evidence"),
    ),
    DOCUMENTATION_ARTIFACT: (
        ("doc", "review"),
        ("boundary", "language"),
    ),
    VALIDATION_ARTIFACT: (
        ("validation", "command"),
        ("regression", "test", "coverage"),
    ),
}


class MaterializationArtifactError(ValueError):
    """Raised when a Phase 7N materialization artifact violates boundary rules."""


@dataclass(frozen=True)
class MaterializationArtifact:
    """Serializable local work item for approved learning candidate materialization."""

    materialization_id: str
    source_candidate_id: str
    candidate_type: str
    affected_component: str | None
    affected_domain: str | None
    proposed_change_summary: str
    proposed_artifact_type: str
    implementation_reference: str | None = None
    validation_requirements: list[str] = field(default_factory=list)
    rollback_plan: str = ""
    runtime_influence_requested: bool = False
    runtime_influence_granted: bool = False
    status: str = PROPOSED
    actor: str = ""
    approval_reference: str | None = None
    created_at: str | None = None
    reviewed_by: str | None = None
    validation_reference: str | None = None
    source_evidence: list[dict[str, object]] = field(default_factory=list)
    semantic_context: dict[str, object] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.materialization_id, "materialization_id")
        _require_non_empty_string(self.source_candidate_id, "source_candidate_id")
        _validate_candidate_type(self.candidate_type)
        _validate_optional_string(self.affected_component, "affected_component")
        _validate_optional_string(self.affected_domain, "affected_domain")
        _require_non_empty_string(self.proposed_change_summary, "proposed_change_summary")
        _validate_artifact_type(self.proposed_artifact_type)
        _validate_candidate_artifact_match(self.candidate_type, self.proposed_artifact_type)
        _validate_optional_string(self.implementation_reference, "implementation_reference")
        _validate_optional_string(self.approval_reference, "approval_reference")
        _validate_optional_string(self.created_at, "created_at")
        _validate_optional_string(self.reviewed_by, "reviewed_by")
        _validate_optional_string(self.validation_reference, "validation_reference")
        _require_non_empty_string(self.actor, "actor")
        _validate_status(self.status)

        if not isinstance(self.runtime_influence_requested, bool):
            raise MaterializationArtifactError("runtime_influence_requested must be a bool.")
        if self.runtime_influence_granted is not False:
            raise MaterializationArtifactError(
                "Phase 7N materialization artifacts cannot grant runtime influence."
            )

        requirements = _normalize_validation_requirements(self.validation_requirements)
        _validate_required_validation_requirements(
            self.candidate_type,
            self.proposed_artifact_type,
            requirements,
        )
        object.__setattr__(self, "validation_requirements", requirements)

        rollback_plan = "" if self.rollback_plan is None else str(self.rollback_plan).strip()
        if is_runtime_sensitive_artifact_type(self.proposed_artifact_type):
            _require_non_empty_string(rollback_plan, "rollback_plan")
        object.__setattr__(self, "rollback_plan", rollback_plan)

        source_evidence = _normalize_source_evidence(self.source_evidence)
        object.__setattr__(self, "source_evidence", source_evidence)

        if self.semantic_context is not None and not isinstance(self.semantic_context, Mapping):
            raise MaterializationArtifactError("semantic_context must be None or a mapping.")
        object.__setattr__(
            self,
            "semantic_context",
            None if self.semantic_context is None else deepcopy(dict(self.semantic_context)),
        )

        object.__setattr__(self, "runtime_influence_granted", False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic serializable dictionary for this artifact."""

        return {
            field_name: deepcopy(getattr(self, field_name))
            for field_name in MATERIALIZATION_ARTIFACT_FIELDS
        }


def create_materialization_artifact(
    candidate: LearningCandidate | Mapping[str, Any],
    actor: str,
    proposed_change_summary: str,
    proposed_artifact_type: str | None = None,
    implementation_reference: str | None = None,
    validation_requirements: Sequence[str] | None = None,
    rollback_plan: str | None = None,
    runtime_influence_requested: bool = False,
    approval_reference: str | None = None,
) -> MaterializationArtifact:
    """Create a local materialization artifact from one approved candidate."""

    _require_non_empty_string(actor, "actor")
    _require_non_empty_string(proposed_change_summary, "proposed_change_summary")
    candidate_data = _candidate_data_for_materialization(candidate)
    boundary = validate_materialization_boundary(
        candidate_data["candidate_type"],
        candidate_data.get("affected_component"),
    )
    artifact_type = proposed_artifact_type or infer_artifact_type(
        candidate_data["candidate_type"],
        candidate_data.get("affected_component"),
    )
    required_validation_requirements(candidate_data["candidate_type"], artifact_type)

    requirements = (
        list(required_validation_requirements(candidate_data["candidate_type"], artifact_type))
        if validation_requirements is None
        else list(validation_requirements)
    )
    component = candidate_data.get("affected_component") or boundary.affected_component

    artifact = MaterializationArtifact(
        materialization_id=create_materialization_id(
            candidate_data["candidate_id"],
            artifact_type,
            affected_component=component,
        ),
        source_candidate_id=candidate_data["candidate_id"],
        candidate_type=candidate_data["candidate_type"],
        affected_component=component,
        affected_domain=candidate_data.get("affected_domain"),
        proposed_change_summary=proposed_change_summary,
        proposed_artifact_type=artifact_type,
        implementation_reference=implementation_reference,
        validation_requirements=requirements,
        rollback_plan="" if rollback_plan is None else rollback_plan,
        runtime_influence_requested=runtime_influence_requested,
        runtime_influence_granted=False,
        status=APPROVED_FOR_MATERIALIZATION,
        actor=actor,
        approval_reference=approval_reference,
        created_at=None,
        reviewed_by=None,
        validation_reference=None,
        source_evidence=deepcopy(candidate_data.get("source_evidence", [])),
        semantic_context=deepcopy(candidate_data.get("semantic_context")),
    )
    return validate_materialization_artifact(artifact)


def validate_materialization_artifact(
    artifact: MaterializationArtifact,
) -> MaterializationArtifact:
    """Validate and return a materialization artifact without activating runtime."""

    if not isinstance(artifact, MaterializationArtifact):
        raise MaterializationArtifactError("artifact must be a MaterializationArtifact.")
    MaterializationArtifact(**artifact.to_dict())
    return artifact


def materialization_artifact_to_dict(artifact: MaterializationArtifact) -> dict[str, Any]:
    """Return a deterministic dictionary for one materialization artifact."""

    return validate_materialization_artifact(artifact).to_dict()


def materialization_artifact_from_dict(data: Mapping[str, Any]) -> MaterializationArtifact:
    """Reconstruct and validate one materialization artifact from dictionary data."""

    if not isinstance(data, Mapping):
        raise MaterializationArtifactError("artifact data must be a mapping.")
    missing = [
        field_name
        for field_name in (
            "materialization_id",
            "source_candidate_id",
            "candidate_type",
            "affected_component",
            "affected_domain",
            "proposed_change_summary",
            "proposed_artifact_type",
        )
        if field_name not in data
    ]
    if missing:
        raise MaterializationArtifactError(
            f"Missing materialization artifact fields: {', '.join(missing)}."
        )
    values = {
        field_name: deepcopy(data[field_name])
        for field_name in MATERIALIZATION_ARTIFACT_FIELDS
        if field_name in data
    }
    return MaterializationArtifact(**values)


def materialization_artifacts_to_dicts(
    artifacts: Sequence[MaterializationArtifact],
) -> list[dict[str, Any]]:
    """Return deterministic dictionaries for materialization artifacts."""

    return [materialization_artifact_to_dict(artifact) for artifact in artifacts]


def create_materialization_id(
    candidate_id: str,
    artifact_type: str,
    affected_component: str | None = None,
) -> str:
    """Create a deterministic materialization identifier from stable inputs."""

    _require_non_empty_string(candidate_id, "candidate_id")
    _validate_artifact_type(artifact_type)
    component_fragment = _identifier_fragment(affected_component or "unspecified")
    return (
        f"MAT-{_identifier_fragment(artifact_type)}-"
        f"{_identifier_fragment(candidate_id)}-{component_fragment}"
    )


def infer_artifact_type(candidate_type: str, affected_component: str | None = None) -> str:
    """Return the controlled materialization artifact type for a candidate type."""

    if candidate_type not in CANDIDATE_TYPE_TO_ARTIFACT_TYPE:
        raise MaterializationArtifactError(f"Unsupported candidate_type: {candidate_type!r}.")
    validate_materialization_boundary(candidate_type, affected_component)
    return CANDIDATE_TYPE_TO_ARTIFACT_TYPE[candidate_type]


def required_validation_requirements(candidate_type: str, artifact_type: str) -> list[str]:
    """Return required validation requirements for a candidate/artifact pairing."""

    _validate_candidate_type(candidate_type)
    _validate_artifact_type(artifact_type)
    _validate_candidate_artifact_match(candidate_type, artifact_type)
    return list(_REQUIRED_VALIDATION_REQUIREMENTS[artifact_type])


def is_runtime_sensitive_artifact_type(artifact_type: str) -> bool:
    """Return True when the artifact type could affect runtime in a future phase."""

    _validate_artifact_type(artifact_type)
    return artifact_type in RUNTIME_SENSITIVE_ARTIFACT_TYPES


def _candidate_data_for_materialization(
    candidate: LearningCandidate | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(candidate, LearningCandidate):
        data = candidate.to_dict()
    elif isinstance(candidate, Mapping):
        data = deepcopy(dict(candidate))
    else:
        raise MaterializationArtifactError(
            "candidate must be a LearningCandidate or candidate mapping."
        )

    for field_name in (
        "candidate_id",
        "candidate_type",
        "status",
        "runtime_influence",
        "requires_human_review",
    ):
        if field_name not in data:
            raise MaterializationArtifactError(f"candidate must include {field_name}.")

    _require_non_empty_string(data["candidate_id"], "candidate_id")
    _validate_candidate_type(data["candidate_type"])
    if data["status"] != APPROVED_FOR_IMPLEMENTATION:
        raise MaterializationArtifactError(
            "candidate must be APPROVED_FOR_IMPLEMENTATION before materialization."
        )
    if data["runtime_influence"] is not False:
        raise MaterializationArtifactError(
            "candidate runtime_influence must be false for materialization."
        )
    if data["requires_human_review"] is not True:
        raise MaterializationArtifactError(
            "candidate requires_human_review must be true for materialization."
        )
    return data


def _validate_candidate_type(candidate_type: Any) -> None:
    if candidate_type not in CANDIDATE_TYPE_TO_ARTIFACT_TYPE:
        raise MaterializationArtifactError(f"Unsupported candidate_type: {candidate_type!r}.")


def _validate_artifact_type(artifact_type: Any) -> None:
    if artifact_type not in MATERIALIZATION_ARTIFACT_TYPES:
        raise MaterializationArtifactError(f"Unsupported artifact_type: {artifact_type!r}.")


def _validate_candidate_artifact_match(candidate_type: str, artifact_type: str) -> None:
    expected = infer_artifact_type(candidate_type)
    if artifact_type != expected:
        raise MaterializationArtifactError(
            f"candidate_type {candidate_type!r} requires artifact_type {expected!r}."
        )


def _validate_status(status: Any) -> None:
    if status not in MATERIALIZATION_STATUSES:
        raise MaterializationArtifactError(f"Unsupported materialization status: {status!r}.")


def _normalize_validation_requirements(requirements: Any) -> list[str]:
    if not isinstance(requirements, list):
        raise MaterializationArtifactError("validation_requirements must be a list.")
    if not requirements:
        raise MaterializationArtifactError("validation_requirements must not be empty.")
    normalized: list[str] = []
    for requirement in requirements:
        if not isinstance(requirement, str) or not requirement.strip():
            raise MaterializationArtifactError(
                "validation_requirements must contain non-empty strings."
            )
        normalized.append(requirement.strip())
    return normalized


def _validate_required_validation_requirements(
    candidate_type: str,
    artifact_type: str,
    requirements: Sequence[str],
) -> None:
    required_validation_requirements(candidate_type, artifact_type)
    normalized_requirements = [_normalize_text(requirement) for requirement in requirements]
    for concept in _REQUIRED_VALIDATION_CONCEPTS[artifact_type]:
        if not any(
            all(token in normalized_requirement for token in concept)
            for normalized_requirement in normalized_requirements
        ):
            raise MaterializationArtifactError(
                "validation_requirements missing required concept: "
                f"{' '.join(concept)}."
            )


def _normalize_source_evidence(source_evidence: Any) -> list[dict[str, object]]:
    if source_evidence is None:
        return []
    if not isinstance(source_evidence, list):
        raise MaterializationArtifactError("source_evidence must be a list.")
    normalized: list[dict[str, object]] = []
    for item in source_evidence:
        if not isinstance(item, Mapping):
            raise MaterializationArtifactError(
                "source_evidence must contain mapping objects only."
            )
        normalized.append(deepcopy(dict(item)))
    return normalized


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MaterializationArtifactError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise MaterializationArtifactError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise MaterializationArtifactError(f"{field_name} must not be blank.")


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"


def _normalize_text(value: str) -> str:
    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
