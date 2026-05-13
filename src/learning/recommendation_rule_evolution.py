"""Proposal-only Phase 7P recommendation rule evolution model.

Recommendation rule evolution records describe proposed recommendation rule
changes that originate from validated recommendation materialization artifacts.
They do not import, mutate, activate, or otherwise influence runtime
recommendations.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence

from src.learning.materialization_artifact import (
    MATERIALIZED,
    RECOMMENDATION_RULE_ARTIFACT,
    VALIDATED as MATERIALIZATION_VALIDATED,
    MaterializationArtifact,
    MaterializationArtifactError,
    is_runtime_sensitive_artifact_type,
    materialization_artifact_from_dict,
    validate_materialization_artifact,
)


RECOMMENDATION_WORDING_REVIEW = "recommendation_wording_review"
RECOMMENDATION_PRIORITY_REVIEW = "recommendation_priority_review"
RECOMMENDATION_DOMAIN_MAPPING_REVIEW = "recommendation_domain_mapping_review"
RECOMMENDATION_SUPPRESSION_REVIEW = "recommendation_suppression_review"
ACTION_SEQUENCING_REVIEW = "action_sequencing_review"
RISK_LABEL_REVIEW = "risk_label_review"
EVIDENCE_MAPPING_REVIEW = "evidence_mapping_review"
RECOMMENDATION_CATEGORY_REVIEW = "recommendation_category_review"
RECOMMENDATION_CONFIDENCE_WORDING_REVIEW = "recommendation_confidence_wording_review"
RECOMMENDATION_ESCALATION_REVIEW = "recommendation_escalation_review"

RECOMMENDATION_EVOLUTION_TYPES = (
    RECOMMENDATION_WORDING_REVIEW,
    RECOMMENDATION_PRIORITY_REVIEW,
    RECOMMENDATION_DOMAIN_MAPPING_REVIEW,
    RECOMMENDATION_SUPPRESSION_REVIEW,
    ACTION_SEQUENCING_REVIEW,
    RISK_LABEL_REVIEW,
    EVIDENCE_MAPPING_REVIEW,
    RECOMMENDATION_CATEGORY_REVIEW,
    RECOMMENDATION_CONFIDENCE_WORDING_REVIEW,
    RECOMMENDATION_ESCALATION_REVIEW,
)

PROPOSED = "PROPOSED"
UNDER_REVIEW = "UNDER_REVIEW"
APPROVED_FOR_VALIDATION = "APPROVED_FOR_VALIDATION"
VALIDATED = "VALIDATED"
REJECTED = "REJECTED"
ROLLED_BACK = "ROLLED_BACK"
CLOSED = "CLOSED"

PROPOSED_RECOMMENDATION_RULE_STATUSES = (
    PROPOSED,
    UNDER_REVIEW,
    APPROVED_FOR_VALIDATION,
    VALIDATED,
    REJECTED,
    ROLLED_BACK,
    CLOSED,
)

REQUIRED_RECOMMENDATION_VALIDATION_REQUIREMENTS = (
    "versioned recommendation rule/config",
    "recommendation regression tests",
    "evidence mapping validation",
    "Phase 4I recommendations contract validation",
    "rollback plan",
    "deterministic runtime remains authoritative",
)

RECOMMENDATION_RULE_EVOLUTION_FIELDS = (
    "evolution_id",
    "source_materialization_id",
    "source_candidate_id",
    "evolution_type",
    "affected_domain",
    "affected_component",
    "proposed_change_summary",
    "proposed_rule_version",
    "proposed_rule",
    "baseline_reference",
    "before_after_summary",
    "validation_requirements",
    "rollback_plan",
    "runtime_influence_requested",
    "runtime_influence_granted",
    "status",
    "actor",
    "created_at",
    "validation_reference",
    "source_evidence",
    "semantic_context",
)

PROPOSED_RECOMMENDATION_RULE_FIELDS = (
    "rule_id",
    "version",
    "rule_type",
    "affected_domain",
    "rule_payload",
    "evidence_requirements",
    "output_contract_requirements",
    "status",
    "runtime_active",
    "runtime_influence_granted",
    "source_evolution_id",
)

_BASE_VALIDATION_CONCEPTS = (
    ("versioned", "recommendation", "rule"),
    ("recommendation", "regression", "test"),
    ("evidence", "mapping"),
    ("phase", "4i", "recommendations", "contract"),
    ("rollback", "plan"),
    ("deterministic", "runtime", "remains", "authoritative"),
)

_SOURCE_ARTIFACT_VALIDATION_CONCEPTS = (
    ("versioned", "recommendation", "rule"),
    ("recommendation", "regression", "test"),
    ("evidence", "mapping"),
    ("phase", "4i", "recommendations", "contract"),
    ("rollback", "plan"),
)

_EVOLUTION_TYPE_VALIDATION_REQUIREMENTS = {
    RECOMMENDATION_WORDING_REVIEW: ("wording regression validation",),
    RECOMMENDATION_PRIORITY_REVIEW: ("priority/order regression validation",),
    RECOMMENDATION_DOMAIN_MAPPING_REVIEW: ("domain mapping validation",),
    RECOMMENDATION_SUPPRESSION_REVIEW: (
        "suppression false positive/false negative review",
    ),
    ACTION_SEQUENCING_REVIEW: ("action sequencing validation",),
    RISK_LABEL_REVIEW: ("risk label consistency validation",),
    EVIDENCE_MAPPING_REVIEW: ("evidence linkage validation",),
    RECOMMENDATION_CATEGORY_REVIEW: ("category consistency validation",),
    RECOMMENDATION_CONFIDENCE_WORDING_REVIEW: (
        "confidence wording calibration validation",
    ),
    RECOMMENDATION_ESCALATION_REVIEW: ("escalation/de-escalation validation",),
}

_EVOLUTION_TYPE_VALIDATION_CONCEPTS = {
    RECOMMENDATION_WORDING_REVIEW: (("wording", "regression"),),
    RECOMMENDATION_PRIORITY_REVIEW: (("priority", "order", "regression"),),
    RECOMMENDATION_DOMAIN_MAPPING_REVIEW: (("domain", "mapping"),),
    RECOMMENDATION_SUPPRESSION_REVIEW: (
        ("suppression", "false", "positive", "negative"),
    ),
    ACTION_SEQUENCING_REVIEW: (("action", "sequencing"),),
    RISK_LABEL_REVIEW: (("risk", "label", "consistency"),),
    EVIDENCE_MAPPING_REVIEW: (("evidence", "linkage"),),
    RECOMMENDATION_CATEGORY_REVIEW: (("category", "consistency"),),
    RECOMMENDATION_CONFIDENCE_WORDING_REVIEW: (
        ("confidence", "wording", "calibration"),
    ),
    RECOMMENDATION_ESCALATION_REVIEW: (("escalation", "de", "escalation"),),
}


class RecommendationRuleEvolutionError(ValueError):
    """Raised when a Phase 7P recommendation evolution violates proposal-only rules."""


@dataclass(frozen=True)
class RecommendationRuleEvolution:
    """Serializable proposal-only recommendation rule evolution record."""

    evolution_id: str
    source_materialization_id: str
    source_candidate_id: str
    evolution_type: str
    affected_domain: str | None
    affected_component: str | None
    proposed_change_summary: str
    proposed_rule_version: str
    proposed_rule: dict[str, object]
    baseline_reference: str | None
    before_after_summary: str
    validation_requirements: list[str]
    rollback_plan: str
    runtime_influence_requested: bool = False
    runtime_influence_granted: bool = False
    status: str = PROPOSED
    actor: str = ""
    created_at: str | None = None
    validation_reference: str | None = None
    source_evidence: list[dict[str, object]] = field(default_factory=list)
    semantic_context: dict[str, object] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.evolution_id, "evolution_id")
        _require_non_empty_string(
            self.source_materialization_id,
            "source_materialization_id",
        )
        _require_non_empty_string(self.source_candidate_id, "source_candidate_id")
        _validate_evolution_type(self.evolution_type)
        _validate_optional_string(self.affected_domain, "affected_domain")
        _validate_optional_string(self.affected_component, "affected_component")
        _require_non_empty_string(self.proposed_change_summary, "proposed_change_summary")
        _require_non_empty_string(self.proposed_rule_version, "proposed_rule_version")
        _validate_optional_string(self.baseline_reference, "baseline_reference")
        _require_non_empty_string(self.before_after_summary, "before_after_summary")
        _require_non_empty_string(self.rollback_plan, "rollback_plan")
        _validate_status(self.status)
        _require_non_empty_string(self.actor, "actor")
        _validate_optional_string(self.created_at, "created_at")
        _validate_optional_string(self.validation_reference, "validation_reference")

        if not isinstance(self.runtime_influence_requested, bool):
            raise RecommendationRuleEvolutionError(
                "runtime_influence_requested must be a bool."
            )
        if self.runtime_influence_granted is not False:
            raise RecommendationRuleEvolutionError(
                "Phase 7P recommendation rule evolution cannot grant runtime influence."
            )

        proposed_rule = _normalize_object_mapping(
            self.proposed_rule,
            "proposed_rule",
            allow_empty=False,
        )
        object.__setattr__(self, "proposed_rule", proposed_rule)

        requirements = _normalize_validation_requirements(self.validation_requirements)
        _validate_recommendation_validation_concepts(
            self.evolution_type,
            requirements,
        )
        object.__setattr__(self, "validation_requirements", requirements)
        object.__setattr__(
            self,
            "source_evidence",
            _normalize_source_evidence(self.source_evidence),
        )
        object.__setattr__(
            self,
            "semantic_context",
            _normalize_optional_object_mapping(self.semantic_context, "semantic_context"),
        )
        object.__setattr__(self, "runtime_influence_granted", False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic serializable dictionary for this evolution."""

        return {
            field_name: deepcopy(getattr(self, field_name))
            for field_name in RECOMMENDATION_RULE_EVOLUTION_FIELDS
        }


@dataclass(frozen=True)
class ProposedRecommendationRule:
    """Inactive versioned recommendation rule proposal."""

    rule_id: str
    version: str
    rule_type: str
    affected_domain: str | None
    rule_payload: dict[str, object]
    evidence_requirements: list[str]
    output_contract_requirements: list[str]
    status: str = PROPOSED
    runtime_active: bool = False
    runtime_influence_granted: bool = False
    source_evolution_id: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.rule_id, "rule_id")
        _require_non_empty_string(self.version, "version")
        _require_non_empty_string(self.rule_type, "rule_type")
        _validate_optional_string(self.affected_domain, "affected_domain")
        _validate_status(self.status)
        _validate_optional_string(self.source_evolution_id, "source_evolution_id")
        if self.runtime_active is not False:
            raise RecommendationRuleEvolutionError(
                "Phase 7P proposed recommendation rules cannot be runtime active."
            )
        if self.runtime_influence_granted is not False:
            raise RecommendationRuleEvolutionError(
                "Phase 7P proposed recommendation rules cannot grant runtime influence."
            )

        object.__setattr__(
            self,
            "rule_payload",
            _normalize_object_mapping(
                self.rule_payload,
                "rule_payload",
                allow_empty=False,
            ),
        )
        evidence_requirements = _normalize_validation_requirements(
            self.evidence_requirements
        )
        _validate_any_concept(
            evidence_requirements,
            (("evidence", "mapping"), ("evidence", "linkage")),
            "evidence_requirements",
        )
        object.__setattr__(self, "evidence_requirements", evidence_requirements)

        output_contract_requirements = _normalize_validation_requirements(
            self.output_contract_requirements
        )
        _validate_required_concepts(
            output_contract_requirements,
            (
                ("phase", "4i", "recommendations", "contract"),
                ("deterministic", "runtime", "remains", "authoritative"),
            ),
            "output_contract_requirements",
        )
        object.__setattr__(
            self,
            "output_contract_requirements",
            output_contract_requirements,
        )
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic serializable dictionary for this rule proposal."""

        return {
            field_name: deepcopy(getattr(self, field_name))
            for field_name in PROPOSED_RECOMMENDATION_RULE_FIELDS
        }


def create_recommendation_rule_evolution(
    materialization_artifact: MaterializationArtifact | Mapping[str, Any],
    actor: str,
    evolution_type: str,
    proposed_rule: Mapping[str, Any],
    proposed_rule_version: str,
    proposed_change_summary: str,
    before_after_summary: str,
    validation_requirements: Sequence[str] | None = None,
    rollback_plan: str | None = None,
    runtime_influence_requested: bool = False,
    baseline_reference: str | None = None,
) -> RecommendationRuleEvolution:
    """Create an inactive recommendation evolution from a materialization artifact."""

    source = _coerce_source_artifact(materialization_artifact)
    _validate_source_artifact_for_evolution(source)
    _require_non_empty_string(actor, "actor")
    _validate_evolution_type(evolution_type)
    _require_non_empty_string(proposed_rule_version, "proposed_rule_version")
    _require_non_empty_string(proposed_change_summary, "proposed_change_summary")
    _require_non_empty_string(before_after_summary, "before_after_summary")
    _require_non_empty_string(rollback_plan, "rollback_plan")

    requirements = (
        required_recommendation_validation_requirements(evolution_type)
        if validation_requirements is None
        else list(validation_requirements)
    )

    evolution = RecommendationRuleEvolution(
        evolution_id=create_recommendation_evolution_id(
            source.materialization_id,
            evolution_type,
            proposed_rule_version,
        ),
        source_materialization_id=source.materialization_id,
        source_candidate_id=source.source_candidate_id,
        evolution_type=evolution_type,
        affected_domain=source.affected_domain,
        affected_component=source.affected_component,
        proposed_change_summary=proposed_change_summary,
        proposed_rule_version=proposed_rule_version,
        proposed_rule=deepcopy(proposed_rule),
        baseline_reference=baseline_reference,
        before_after_summary=before_after_summary,
        validation_requirements=requirements,
        rollback_plan="" if rollback_plan is None else rollback_plan,
        runtime_influence_requested=runtime_influence_requested,
        runtime_influence_granted=False,
        status=PROPOSED,
        actor=actor,
        created_at=None,
        validation_reference=None,
        source_evidence=deepcopy(source.source_evidence),
        semantic_context=deepcopy(source.semantic_context),
    )
    return validate_recommendation_rule_evolution(evolution)


def validate_recommendation_rule_evolution(
    evolution: RecommendationRuleEvolution,
) -> RecommendationRuleEvolution:
    """Validate and return a recommendation evolution without activating runtime."""

    if not isinstance(evolution, RecommendationRuleEvolution):
        raise RecommendationRuleEvolutionError(
            "evolution must be a RecommendationRuleEvolution."
        )
    RecommendationRuleEvolution(**evolution.to_dict())
    return evolution


def recommendation_rule_evolution_to_dict(
    evolution: RecommendationRuleEvolution,
) -> dict[str, Any]:
    """Return a deterministic dictionary for one recommendation evolution."""

    return validate_recommendation_rule_evolution(evolution).to_dict()


def recommendation_rule_evolution_from_dict(
    data: Mapping[str, Any],
) -> RecommendationRuleEvolution:
    """Reconstruct and validate one recommendation evolution from dictionary data."""

    if not isinstance(data, Mapping):
        raise RecommendationRuleEvolutionError("evolution data must be a mapping.")
    missing = [
        field_name
        for field_name in (
            "evolution_id",
            "source_materialization_id",
            "source_candidate_id",
            "evolution_type",
            "proposed_change_summary",
            "proposed_rule_version",
            "proposed_rule",
            "before_after_summary",
            "validation_requirements",
            "rollback_plan",
            "actor",
        )
        if field_name not in data
    ]
    if missing:
        raise RecommendationRuleEvolutionError(
            f"Missing recommendation rule evolution fields: {', '.join(missing)}."
        )
    values = {
        field_name: deepcopy(data[field_name])
        for field_name in RECOMMENDATION_RULE_EVOLUTION_FIELDS
        if field_name in data
    }
    return RecommendationRuleEvolution(**values)


def recommendation_rule_evolutions_to_dicts(
    evolutions: Sequence[RecommendationRuleEvolution],
) -> list[dict[str, Any]]:
    """Return deterministic dictionaries for recommendation evolutions."""

    return [recommendation_rule_evolution_to_dict(evolution) for evolution in evolutions]


def create_recommendation_evolution_id(
    materialization_id: str,
    evolution_type: str,
    proposed_rule_version: str,
) -> str:
    """Create a deterministic recommendation evolution identifier."""

    _require_non_empty_string(materialization_id, "materialization_id")
    _validate_evolution_type(evolution_type)
    _require_non_empty_string(proposed_rule_version, "proposed_rule_version")
    return (
        f"RECO-EVO-{_identifier_fragment(evolution_type)}-"
        f"{_identifier_fragment(materialization_id)}-"
        f"{_identifier_fragment(proposed_rule_version)}"
    )


def create_proposed_recommendation_rule(
    evolution: RecommendationRuleEvolution,
    rule_type: str = "recommendation_rule_review",
) -> ProposedRecommendationRule:
    """Create an inactive versioned proposed recommendation rule."""

    evolution = validate_recommendation_rule_evolution(evolution)
    _require_non_empty_string(rule_type, "rule_type")
    rule = ProposedRecommendationRule(
        rule_id=_create_proposed_recommendation_rule_id(
            rule_type,
            evolution.proposed_rule_version,
            evolution.evolution_id,
        ),
        version=evolution.proposed_rule_version,
        rule_type=rule_type,
        affected_domain=evolution.affected_domain,
        rule_payload=deepcopy(evolution.proposed_rule),
        evidence_requirements=[
            "evidence mapping validation",
            "evidence linkage validation",
        ],
        output_contract_requirements=[
            "Phase 4I recommendations contract validation",
            "deterministic runtime remains authoritative",
        ],
        status=PROPOSED,
        runtime_active=False,
        runtime_influence_granted=False,
        source_evolution_id=evolution.evolution_id,
    )
    return validate_proposed_recommendation_rule(rule)


def validate_proposed_recommendation_rule(
    rule: ProposedRecommendationRule,
) -> ProposedRecommendationRule:
    """Validate and return a proposed recommendation rule without activating it."""

    if not isinstance(rule, ProposedRecommendationRule):
        raise RecommendationRuleEvolutionError(
            "rule must be a ProposedRecommendationRule."
        )
    ProposedRecommendationRule(**rule.to_dict())
    return rule


def proposed_recommendation_rule_to_dict(
    rule: ProposedRecommendationRule,
) -> dict[str, Any]:
    """Return a deterministic dictionary for one proposed recommendation rule."""

    return validate_proposed_recommendation_rule(rule).to_dict()


def proposed_recommendation_rule_from_dict(
    data: Mapping[str, Any],
) -> ProposedRecommendationRule:
    """Reconstruct and validate one proposed recommendation rule from dictionary data."""

    if not isinstance(data, Mapping):
        raise RecommendationRuleEvolutionError("rule data must be a mapping.")
    missing = [
        field_name
        for field_name in (
            "rule_id",
            "version",
            "rule_type",
            "rule_payload",
            "evidence_requirements",
            "output_contract_requirements",
        )
        if field_name not in data
    ]
    if missing:
        raise RecommendationRuleEvolutionError(
            f"Missing proposed recommendation rule fields: {', '.join(missing)}."
        )
    values = {
        field_name: deepcopy(data[field_name])
        for field_name in PROPOSED_RECOMMENDATION_RULE_FIELDS
        if field_name in data
    }
    return ProposedRecommendationRule(**values)


def required_recommendation_validation_requirements(evolution_type: str) -> list[str]:
    """Return required recommendation validation requirements for one evolution type."""

    _validate_evolution_type(evolution_type)
    requirements = list(REQUIRED_RECOMMENDATION_VALIDATION_REQUIREMENTS)
    requirements.extend(_EVOLUTION_TYPE_VALIDATION_REQUIREMENTS[evolution_type])
    return requirements


def is_supported_recommendation_evolution_type(evolution_type: str) -> bool:
    """Return True when evolution_type is supported by Phase 7P."""

    return evolution_type in RECOMMENDATION_EVOLUTION_TYPES


def _coerce_source_artifact(
    materialization_artifact: MaterializationArtifact | Mapping[str, Any],
) -> MaterializationArtifact:
    if isinstance(materialization_artifact, MaterializationArtifact):
        source = materialization_artifact
    elif isinstance(materialization_artifact, Mapping):
        try:
            source = materialization_artifact_from_dict(materialization_artifact)
        except MaterializationArtifactError as exc:
            raise RecommendationRuleEvolutionError(str(exc)) from exc
    else:
        raise RecommendationRuleEvolutionError(
            "materialization_artifact must be a MaterializationArtifact or mapping."
        )

    try:
        return validate_materialization_artifact(source)
    except MaterializationArtifactError as exc:
        raise RecommendationRuleEvolutionError(str(exc)) from exc


def _validate_source_artifact_for_evolution(source: MaterializationArtifact) -> None:
    if source.proposed_artifact_type != RECOMMENDATION_RULE_ARTIFACT:
        raise RecommendationRuleEvolutionError(
            "Recommendation rule evolution requires a recommendation_rule_artifact source."
        )
    if not is_runtime_sensitive_artifact_type(source.proposed_artifact_type):
        raise RecommendationRuleEvolutionError(
            "Recommendation rule evolution source artifact must be runtime-sensitive."
        )
    if source.runtime_influence_granted is not False:
        raise RecommendationRuleEvolutionError(
            "Recommendation rule evolution source cannot have runtime influence granted."
        )
    if source.status not in (MATERIALIZED, MATERIALIZATION_VALIDATED):
        raise RecommendationRuleEvolutionError(
            "Recommendation rule evolution source must be MATERIALIZED or VALIDATED."
        )
    _validate_source_artifact_validation_concepts(source.validation_requirements)


def _create_proposed_recommendation_rule_id(
    rule_type: str,
    version: str,
    source_evolution_id: str,
) -> str:
    _require_non_empty_string(rule_type, "rule_type")
    _require_non_empty_string(version, "version")
    _require_non_empty_string(source_evolution_id, "source_evolution_id")
    return (
        f"RECO-RULE-{_identifier_fragment(rule_type)}-"
        f"{_identifier_fragment(version)}-{_identifier_fragment(source_evolution_id)}"
    )


def _validate_source_artifact_validation_concepts(
    requirements: Sequence[str],
) -> None:
    _validate_required_concepts(
        requirements,
        _SOURCE_ARTIFACT_VALIDATION_CONCEPTS,
        "source artifact validation_requirements",
    )


def _validate_recommendation_validation_concepts(
    evolution_type: str,
    requirements: Sequence[str],
) -> None:
    concepts = list(_BASE_VALIDATION_CONCEPTS)
    concepts.extend(_EVOLUTION_TYPE_VALIDATION_CONCEPTS[evolution_type])
    _validate_required_concepts(requirements, concepts, "validation_requirements")


def _validate_evolution_type(evolution_type: Any) -> None:
    if evolution_type not in RECOMMENDATION_EVOLUTION_TYPES:
        raise RecommendationRuleEvolutionError(
            f"Unsupported recommendation evolution type: {evolution_type!r}."
        )


def _validate_status(status: Any) -> None:
    if status not in PROPOSED_RECOMMENDATION_RULE_STATUSES:
        raise RecommendationRuleEvolutionError(
            f"Unsupported recommendation rule status: {status!r}."
        )


def _normalize_validation_requirements(requirements: Any) -> list[str]:
    if not isinstance(requirements, list):
        raise RecommendationRuleEvolutionError(
            "validation_requirements must be a list."
        )
    if not requirements:
        raise RecommendationRuleEvolutionError(
            "validation_requirements must not be empty."
        )
    normalized: list[str] = []
    for requirement in requirements:
        if not isinstance(requirement, str) or not requirement.strip():
            raise RecommendationRuleEvolutionError(
                "validation_requirements must contain non-empty strings."
            )
        normalized.append(requirement.strip())
    return normalized


def _normalize_source_evidence(source_evidence: Any) -> list[dict[str, object]]:
    if source_evidence is None:
        return []
    if not isinstance(source_evidence, list):
        raise RecommendationRuleEvolutionError("source_evidence must be a list.")
    normalized: list[dict[str, object]] = []
    for item in source_evidence:
        if not isinstance(item, Mapping):
            raise RecommendationRuleEvolutionError(
                "source_evidence must contain mapping objects only."
            )
        normalized.append(deepcopy(dict(item)))
    return normalized


def _normalize_object_mapping(
    data: Any,
    field_name: str,
    allow_empty: bool = True,
) -> dict[str, object]:
    if data is None:
        data = {}
    if not isinstance(data, Mapping):
        raise RecommendationRuleEvolutionError(f"{field_name} must be a mapping.")
    normalized = deepcopy(dict(data))
    if not allow_empty and not normalized:
        raise RecommendationRuleEvolutionError(f"{field_name} must not be empty.")
    return normalized


def _normalize_optional_object_mapping(
    data: Any,
    field_name: str,
) -> dict[str, object] | None:
    if data is None:
        return None
    return _normalize_object_mapping(data, field_name)


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RecommendationRuleEvolutionError(
            f"{field_name} must be a non-empty string."
        )


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise RecommendationRuleEvolutionError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise RecommendationRuleEvolutionError(f"{field_name} must not be blank.")


def _validate_required_concepts(
    requirements: Sequence[str],
    concepts: Sequence[Sequence[str]],
    field_name: str,
) -> None:
    normalized_requirements = [_normalize_text(requirement) for requirement in requirements]
    for concept in concepts:
        if not any(
            all(token in normalized_requirement for token in concept)
            for normalized_requirement in normalized_requirements
        ):
            raise RecommendationRuleEvolutionError(
                f"{field_name} missing required concept: {' '.join(concept)}."
            )


def _validate_any_concept(
    requirements: Sequence[str],
    concepts: Sequence[Sequence[str]],
    field_name: str,
) -> None:
    normalized_requirements = [_normalize_text(requirement) for requirement in requirements]
    if not any(
        all(token in normalized_requirement for token in concept)
        for concept in concepts
        for normalized_requirement in normalized_requirements
    ):
        raise RecommendationRuleEvolutionError(
            f"{field_name} missing required recommendation evidence concept."
        )


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"


def _normalize_text(value: str) -> str:
    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
