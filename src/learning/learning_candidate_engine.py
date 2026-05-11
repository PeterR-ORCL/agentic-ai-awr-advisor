"""Deterministic Phase 7D learning candidate generation.

This module converts already-mined Phase 7B outcome patterns into Phase 7C
learning candidate proposals. It is local-only, read-only, and intentionally
isolated from runtime parser, scoring, decision, recommendation, and dashboard
truth paths.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from src.learning.learning_candidate_model import (
    DASHBOARD_WORDING_CANDIDATE,
    LearningCandidate,
    MAX_CANDIDATE_CONFIDENCE,
    PARSER_MAPPING_CANDIDATE,
    PROPOSED,
    RECOMMENDATION_RULE_CANDIDATE,
    SCORING_WEIGHT_REVIEW_CANDIDATE,
    VALIDATION_CANDIDATE,
    candidates_to_dicts,
    create_candidate_id,
    is_supported_candidate_type,
    validate_candidate,
)
from src.learning.outcome_pattern_miner import OutcomePatternMiner


CREATED_BY = "phase7_candidate_generation_engine"

PATTERN_TO_CANDIDATE_TYPE = {
    "repeated_rejected_recommendation": RECOMMENDATION_RULE_CANDIDATE,
    "poor_outcome_after_action": RECOMMENDATION_RULE_CANDIDATE,
    "recurring_issue_after_action": RECOMMENDATION_RULE_CANDIDATE,
    "repeated_unknown_signal": PARSER_MAPPING_CANDIDATE,
    "repeated_feedback_theme": DASHBOARD_WORDING_CANDIDATE,
    "recurring_domain_issue": SCORING_WEIGHT_REVIEW_CANDIDATE,
}

PATTERN_ORDER = {
    "repeated_rejected_recommendation": 10,
    "poor_outcome_after_action": 20,
    "recurring_issue_after_action": 30,
    "repeated_unknown_signal": 40,
    "repeated_feedback_theme": 50,
    "recurring_domain_issue": 60,
}


class LearningCandidateEngine:
    """Generate proposal-only learning candidates from outcome patterns."""

    def generate_candidates(self, patterns: Sequence[Any] | None) -> list[LearningCandidate]:
        """Return deterministic proposal candidates for supplied outcome patterns."""

        if not patterns:
            return []

        candidates: list[LearningCandidate] = []
        for pattern in sorted(list(patterns), key=_pattern_sort_key):
            candidate_type = _candidate_type_for_pattern(pattern)
            candidate = _candidate_from_pattern(pattern, candidate_type)
            candidates.append(validate_candidate(candidate))
        return deduplicate_candidates(candidates)

    def generate_candidates_from_memory(
        self,
        memory_records: Mapping[str, Sequence[Mapping[str, Any]]] | None,
    ) -> list[LearningCandidate]:
        """Mine local in-memory outcome patterns, then generate proposals."""

        if not memory_records:
            return []

        memory_copy = deepcopy(memory_records)
        patterns = OutcomePatternMiner().mine_patterns(memory_copy)
        return self.generate_candidates(patterns)


def generate_learning_candidates(patterns: Sequence[Any] | None) -> list[dict[str, Any]]:
    """Return serialized proposal candidates for supplied outcome patterns."""

    return candidates_to_dicts(LearningCandidateEngine().generate_candidates(patterns))


def generate_learning_candidates_from_memory(
    memory_records: Mapping[str, Sequence[Mapping[str, Any]]] | None,
) -> list[dict[str, Any]]:
    """Return serialized proposal candidates from local in-memory records."""

    return candidates_to_dicts(
        LearningCandidateEngine().generate_candidates_from_memory(memory_records)
    )


def deduplicate_candidates(
    candidates: Sequence[LearningCandidate] | None,
) -> list[LearningCandidate]:
    """Merge candidates with duplicate deterministic identifiers."""

    if not candidates:
        return []

    by_id: dict[str, LearningCandidate] = {}
    order: list[str] = []

    for candidate in candidates:
        validate_candidate(candidate)
        existing = by_id.get(candidate.candidate_id)
        if existing is None:
            by_id[candidate.candidate_id] = candidate
            order.append(candidate.candidate_id)
            continue
        by_id[candidate.candidate_id] = _merge_duplicate_candidates(existing, candidate)

    return [by_id[candidate_id] for candidate_id in order]


def _candidate_from_pattern(pattern: Any, candidate_type: str) -> LearningCandidate:
    source_evidence = _source_records(pattern)
    pattern_id = _optional_text(_pattern_value(pattern, "pattern_id"))
    pattern_type = _optional_text(_pattern_value(pattern, "pattern_type")) or "unknown_pattern"
    recurrence_count = _optional_int(_pattern_value(pattern, "recurrence_count"))
    affected_domain = _optional_text(_pattern_value(pattern, "affected_domain"))
    affected_component = _affected_component(pattern, candidate_type)
    title = _candidate_title(pattern, pattern_type, affected_component, affected_domain)
    description = _candidate_description(pattern, pattern_type, source_evidence)
    rationale = _candidate_rationale(pattern)

    candidate = LearningCandidate(
        candidate_id=_deterministic_candidate_id(
            candidate_type,
            title,
            affected_component,
            affected_domain,
            source_evidence,
            pattern_id,
        ),
        candidate_type=candidate_type,
        title=title,
        description=description,
        source_evidence=source_evidence,
        structured_sources=[
            {
                "source_type": "outcome_pattern",
                "pattern_id": pattern_id,
                "pattern_type": pattern_type,
                "recurrence_count": recurrence_count,
                "observed_effect": _optional_text(_pattern_value(pattern, "observed_effect")),
                "affected_component": affected_component,
                "affected_domain": affected_domain,
                "suggested_candidate_type": _optional_text(
                    _pattern_value(pattern, "suggested_candidate_type")
                ),
                "source_record_count": len(source_evidence),
            }
        ],
        semantic_context=None,
        affected_component=affected_component,
        affected_domain=affected_domain,
        confidence=_safe_confidence(_pattern_value(pattern, "confidence", 0.0)),
        rationale=rationale,
        requires_human_review=True,
        runtime_influence=False,
        status=PROPOSED,
        created_at=None,
        created_by=CREATED_BY,
        reviewed_by=None,
        review_notes=None,
        materialization_reference=None,
    )
    return validate_candidate(candidate)


def _candidate_type_for_pattern(pattern: Any) -> str:
    suggested = _optional_text(_pattern_value(pattern, "suggested_candidate_type"))
    if suggested and is_supported_candidate_type(suggested):
        return suggested

    pattern_type = _optional_text(_pattern_value(pattern, "pattern_type")) or ""
    if pattern_type == "repeated_feedback_theme":
        if _feedback_theme_relates_to_recommendation(pattern):
            return RECOMMENDATION_RULE_CANDIDATE
        return DASHBOARD_WORDING_CANDIDATE

    if pattern_type == "recurring_domain_issue":
        if _domain_issue_relates_to_recommendation(pattern):
            return RECOMMENDATION_RULE_CANDIDATE
        return SCORING_WEIGHT_REVIEW_CANDIDATE

    return PATTERN_TO_CANDIDATE_TYPE.get(pattern_type, VALIDATION_CANDIDATE)


def _affected_component(pattern: Any, candidate_type: str) -> str | None:
    explicit = _optional_text(_pattern_value(pattern, "affected_component"))
    if explicit:
        return explicit

    pattern_type = _optional_text(_pattern_value(pattern, "pattern_type")) or ""
    if pattern_type == "repeated_unknown_signal" or candidate_type == PARSER_MAPPING_CANDIDATE:
        return "parser"
    if candidate_type == RECOMMENDATION_RULE_CANDIDATE:
        return "recommendation"
    if pattern_type in {
        "repeated_rejected_recommendation",
        "poor_outcome_after_action",
        "recurring_issue_after_action",
    }:
        return "recommendation"
    if pattern_type == "repeated_feedback_theme":
        return "recommendation" if _feedback_theme_relates_to_recommendation(pattern) else "dashboard"
    if pattern_type == "recurring_domain_issue":
        return "recommendation" if _domain_issue_relates_to_recommendation(pattern) else "scoring"
    if candidate_type == DASHBOARD_WORDING_CANDIDATE:
        return "dashboard"
    if candidate_type == SCORING_WEIGHT_REVIEW_CANDIDATE:
        return "scoring"
    return None


def _candidate_title(
    pattern: Any,
    pattern_type: str,
    affected_component: str | None,
    affected_domain: str | None,
) -> str:
    subject = affected_domain or affected_component
    prefix = f"Review {_humanize(pattern_type)} pattern"
    if subject:
        prefix = f"{prefix} for {subject}"

    pattern_title = _optional_text(_pattern_value(pattern, "title"))
    if pattern_title and pattern_title.lower() not in prefix.lower():
        return f"{prefix}: {pattern_title}"
    return prefix


def _candidate_description(
    pattern: Any,
    pattern_type: str,
    source_evidence: Sequence[Any],
) -> str:
    recurrence_count = _optional_int(_pattern_value(pattern, "recurrence_count"))
    observed = [f"Observed {_humanize(pattern_type)} pattern"]
    if recurrence_count is not None:
        observed.append(f"with recurrence_count={recurrence_count}")
    if source_evidence:
        observed.append(f"across {len(source_evidence)} source records")
    pattern_description = _optional_text(_pattern_value(pattern, "description"))
    description = " ".join(observed) + "."
    if pattern_description:
        description = f"{description} Pattern description: {pattern_description}"
    return (
        f"{description} This is a proposal for human review only; it does not "
        "approve, implement, or activate runtime behavior."
    )


def _candidate_rationale(pattern: Any) -> str:
    pattern_rationale = _optional_text(_pattern_value(pattern, "rationale"))
    if pattern_rationale:
        return (
            f"Pattern rationale: {pattern_rationale} Human review is required "
            "before any approval, implementation, materialization, or activation."
        )
    return (
        "Pattern metadata was supplied for review. Human review is required before "
        "any approval, implementation, materialization, or activation."
    )


def _deterministic_candidate_id(
    candidate_type: str,
    title: str,
    affected_component: str | None,
    affected_domain: str | None,
    source_evidence: Sequence[Any],
    pattern_id: str | None,
) -> str:
    if pattern_id:
        seed = {
            "candidate_type": candidate_type,
            "pattern_id": pattern_id,
        }
        digest = _digest(seed)
        return f"CANDIDATE-{_identifier_fragment(candidate_type)}-{digest}"

    return create_candidate_id(
        candidate_type,
        title,
        affected_component=affected_component,
        affected_domain=affected_domain,
        source_evidence=source_evidence,
        pattern_id=None,
    )


def _merge_duplicate_candidates(
    left: LearningCandidate,
    right: LearningCandidate,
) -> LearningCandidate:
    data = left.to_dict()
    data["source_evidence"] = _merge_json_lists(left.source_evidence, right.source_evidence)
    data["structured_sources"] = _merge_json_lists(
        left.structured_sources,
        right.structured_sources,
    )
    data["confidence"] = _safe_confidence(max(left.confidence, right.confidence))
    data["status"] = PROPOSED
    data["requires_human_review"] = True
    data["runtime_influence"] = False
    data["semantic_context"] = None
    data["created_at"] = None
    data["created_by"] = CREATED_BY
    data["reviewed_by"] = None
    data["review_notes"] = None
    data["materialization_reference"] = None
    return validate_candidate(LearningCandidate.from_dict(data))


def _merge_json_lists(left: Sequence[Any], right: Sequence[Any]) -> list[Any]:
    merged: dict[str, Any] = {}
    for item in list(left) + list(right):
        safe_item = _json_safe(item)
        merged[_json_text(safe_item)] = safe_item
    return [deepcopy(merged[key]) for key in sorted(merged)]


def _pattern_sort_key(pattern: Any) -> tuple[Any, ...]:
    pattern_type = _optional_text(_pattern_value(pattern, "pattern_type")) or ""
    return (
        PATTERN_ORDER.get(pattern_type, 999),
        pattern_type,
        _optional_text(_pattern_value(pattern, "pattern_id")) or "",
        _optional_text(_pattern_value(pattern, "title")) or "",
        _json_text(_json_safe(_source_records(pattern))),
    )


def _source_records(pattern: Any) -> list[Any]:
    records = _pattern_value(pattern, "source_records", [])
    if records is None:
        return []
    if isinstance(records, list):
        return deepcopy(records)
    if isinstance(records, tuple):
        return [deepcopy(record) for record in records]
    return [deepcopy(records)]


def _feedback_theme_relates_to_recommendation(pattern: Any) -> bool:
    text = _combined_pattern_text(pattern)
    if any(
        phrase in text
        for phrase in (
            "recommendation not useful",
            "recommendation usefulness",
            "unhelpful recommendation",
            "not actionable",
            "false positive recommendation",
        )
    ):
        return True
    if "recommendation" not in text:
        return False
    return any(
        term in text
        for term in (
            "useful",
            "usefulness",
            "actionable",
            "relevant",
            "irrelevant",
            "helpful",
            "unhelpful",
            "false positive",
            "wrong",
        )
    )


def _domain_issue_relates_to_recommendation(pattern: Any) -> bool:
    text = _domain_issue_decision_text(pattern)
    if any(
        phrase in text
        for phrase in (
            "after action",
            "after recommendation",
            "same action",
            "action/domain",
            "action domain",
            "recommendation recurrence",
            "recurring recommendation",
        )
    ):
        return True
    return (
        ("recommendation" in text and ("recurr" in text or "repeat" in text))
        or ("action" in text and ("recurr" in text or "repeat" in text or "same" in text))
    )


def _domain_issue_decision_text(pattern: Any) -> str:
    parts = []
    for field_name in ("title", "observed_effect", "rationale"):
        value = _optional_text(_pattern_value(pattern, field_name))
        if value:
            parts.append(value)
    return " ".join(parts).lower()


def _combined_pattern_text(pattern: Any) -> str:
    parts = []
    for field_name in (
        "pattern_type",
        "title",
        "description",
        "observed_effect",
        "rationale",
    ):
        value = _optional_text(_pattern_value(pattern, field_name))
        if value:
            parts.append(value)
    return " ".join(parts).lower()


def _safe_confidence(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    if confidence >= 1.0:
        return MAX_CANDIDATE_CONFIDENCE
    return min(max(confidence, 0.0), MAX_CANDIDATE_CONFIDENCE)


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _pattern_value(pattern: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(pattern, Mapping):
        return pattern.get(field_name, default)
    return getattr(pattern, field_name, default)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _humanize(value: str | None) -> str:
    text = str(value or "unknown").strip().replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text or "unknown"


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNKNOWN"


def _digest(value: Any) -> str:
    return hashlib.sha256(_json_text(_json_safe(value)).encode("utf-8")).hexdigest()[
        :16
    ].upper()


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


__all__ = [
    "LearningCandidateEngine",
    "deduplicate_candidates",
    "generate_learning_candidates",
    "generate_learning_candidates_from_memory",
]
