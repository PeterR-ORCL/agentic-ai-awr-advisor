"""Product-safe renderer kit for 7RESET dashboard handoff components.

This module renders small escaped HTML fragments from product handoff and view
model contracts. It does not render a dashboard shell, read artifacts, create
browser state, or call legacy renderer helpers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from html import escape
from typing import Any

from src.reporting.dashboard.product_handoff import HandoffOption, ProductScreenHandoff
from src.reporting.dashboard.view_models.shared_product_shapes import (
    EvidenceDisplayRow,
    ProductScopeSummary,
    UnavailableVisualState,
)
from src.reporting.dashboard.view_models.visual_contracts import (
    ComparisonDeltaVisual,
    DistributionVisual,
    TimeSeriesVisual,
    ViolinVisual,
)


PRODUCT_REVIEW_PRIMITIVES: tuple[str, ...] = (
    "SurfaceCard",
    "SubCard",
    "StatusPill",
    "ScopeSummaryCard",
    "UnavailableStateCard",
    "EvidenceTable",
    "ModeTabs",
    "DomainLens",
    "VisualContainer",
    "InternalRefsAnnex",
)

SUPPORTED_STATUS_VALUES: tuple[str, ...] = (
    "ready",
    "partial",
    "unavailable",
    "blocked",
    "valid",
    "invalid",
    "high",
    "medium",
    "low",
    "critical",
    "warning",
    "success",
    "neutral",
)

SUPPORTED_SCREEN4_MODES: tuple[str, ...] = ("historical", "comparative", "deep_analysis")
SUPPORTED_DOMAIN_LABELS: tuple[str, ...] = (
    "All Domains",
    "CPU",
    "IO",
    "MEMORY",
    "COMMIT",
    "RAC",
    "ADG",
)
EVIDENCE_ROW_FIELDS: tuple[str, ...] = (
    "label",
    "value",
    "unit",
    "interpretation",
    "evidence_ref_label",
    "freshness_status",
    "scope_classification",
)
REQUIRED_EVIDENCE_ROW_FIELDS: tuple[str, ...] = EVIDENCE_ROW_FIELDS[:-1]

FORBIDDEN_TEXT_MARKERS: tuple[str, ...] = (
    "selected_flow_id",
    "selected-flow-internal",
    "evidence_pack_id",
    "evidence-pack-internal",
    "allowed_visualizations",
    "Allowed Visualizations",
    "generated HTML as truth",
    "generated_html",
    "browser/localStorage/cache as authority",
    "localStorage creates truth",
    "LLM-created evidence",
    "LLM-created recommendation",
    "LLM-created learning/runtime eligibility",
    "fake-static-svg",
)

PRODUCT_SAFE_PLACEHOLDER = "Product-safe shaped content required."


def render_status_pill(status: str | None = None, *, label: str | None = None, tone: str | None = None, kind: str = "status") -> str:
    value = _safe_status(tone or status or label or "neutral")
    display_label = _safe_text(label or status or tone or value)
    attrs = {
        "product-component": "StatusPill",
        "status": value,
        "tone": value,
    }
    if kind == "confidence":
        attrs["confidence"] = value
    return (
        f'<span class="product-status-pill product-status-pill--{_attr(value)}"'
        f'{_data_attrs(attrs)}>{display_label}</span>'
    )


def render_surface_card(
    title: str,
    body: Any = "",
    *,
    status: str | None = None,
    data_attrs: Mapping[str, Any] | None = None,
) -> str:
    attrs = {"product-component": "SurfaceCard", **_safe_data_attrs(data_attrs)}
    status_html = render_status_pill(status) if status else ""
    return (
        f'<section class="product-surface-card" {_data_attrs(attrs)}>'
        f'<header class="product-card-header"><h3>{_safe_text(title)}</h3>{status_html}</header>'
        f'<div class="product-card-body">{_safe_body(body)}</div>'
        "</section>"
    )


def render_sub_card(title: str, body: Any = "", *, status: str | None = None) -> str:
    status_html = render_status_pill(status) if status else ""
    return (
        '<section class="product-sub-card" data-product-component="SubCard">'
        f'<header class="product-card-header"><h4>{_safe_text(title)}</h4>{status_html}</header>'
        f'<div class="product-card-body">{_safe_body(body)}</div>'
        "</section>"
    )


def render_scope_summary(scope_summary: ProductScopeSummary | Any) -> str:
    if not isinstance(scope_summary, ProductScopeSummary) and not _has_fields(scope_summary, ("label", "flow_kind")):
        raise ValueError("ScopeSummaryCard requires a ProductScopeSummary-shaped object.")
    rows = (
        ("Scope", _field(scope_summary, "label")),
        ("Database", _field(scope_summary, "database_label")),
        ("Instance", _field(scope_summary, "instance_label")),
        ("Window", _field(scope_summary, "snapshot_window_label")),
        ("Flow", _field(scope_summary, "flow_kind")),
        ("Validation", _field(scope_summary, "validation_status")),
    )
    body = "".join(
        f'<div class="product-scope-row" data-scope-field="{_attr(label)}">'
        f"<dt>{_safe_text(label)}</dt><dd>{_safe_text(value)}</dd></div>"
        for label, value in rows
        if _text(value)
    )
    return (
        '<dl class="product-scope-summary" data-product-component="ScopeSummaryCard">'
        f"{body}</dl>"
    )


def render_unavailable_state(state: UnavailableVisualState | Any = None, *, visual: Any = None) -> str:
    unavailable = state if state is not None else visual
    if not isinstance(unavailable, UnavailableVisualState) and not _has_fields(unavailable, ("title", "message")):
        raise ValueError("UnavailableStateCard requires an UnavailableVisualState-shaped object.")
    reason_code = _safe_text(_field(unavailable, "reason_code", "unavailable"))
    body = (
        f'<h4>{_safe_text(_field(unavailable, "title", "Unavailable"))}</h4>'
        f'<p>{_safe_text(_field(unavailable, "message"))}</p>'
        f'<p class="product-required-contract">{_safe_text(_field(unavailable, "required_contract"))}</p>'
        f"{render_status_pill('unavailable')}"
    )
    return (
        '<section class="product-unavailable-state-card" '
        f'data-product-component="UnavailableStateCard" data-reason-code="{_attr(reason_code)}">'
        f"{body}</section>"
    )


def render_evidence_table(rows: Sequence[EvidenceDisplayRow | Any]) -> str:
    shaped_rows = tuple(_normalize_evidence_row(row) for row in _as_sequence(rows))
    if not shaped_rows:
        return render_unavailable_state(
            UnavailableVisualState(
                reason_code="evidence_rows_missing",
                title="Evidence unavailable",
                message="Shaped product evidence rows are required.",
                required_contract="EvidenceDisplayRow",
            )
        )
    header = "".join(f"<th>{_safe_text(field)}</th>" for field in EVIDENCE_ROW_FIELDS)
    body = "".join(
        "<tr>"
        f"<td>{_safe_text(row.label)}</td>"
        f"<td>{_safe_text(row.value)}</td>"
        f"<td>{_safe_text(row.unit)}</td>"
        f"<td>{_safe_text(row.interpretation)}</td>"
        f"<td>{_safe_text(row.evidence_ref_label)}</td>"
        f"<td>{_safe_text(row.freshness_status)}</td>"
        f"<td>{_safe_text(row.scope_classification)}</td>"
        "</tr>"
        for row in shaped_rows
    )
    return (
        '<table class="product-evidence-table" data-product-component="EvidenceTable">'
        f"<thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"
    )


def render_mode_tabs(
    mode_tabs: Sequence[HandoffOption | Any],
    *,
    active_mode: str | None = None,
) -> str:
    tabs = tuple(_normalize_option(tab) for tab in _as_sequence(mode_tabs))
    if not tabs:
        raise ValueError("ModeTabs requires mode options.")
    rendered = []
    for tab in tabs:
        if tab.value not in SUPPORTED_SCREEN4_MODES:
            raise ValueError(f"Unsupported Screen 4 mode: {tab.value}")
        active = "true" if tab.value == active_mode else "false"
        rendered.append(
            '<button type="button" class="product-mode-tab" '
            f'data-product-component="ModeTabs" data-mode="{_attr(tab.value)}" '
            f'data-availability="{_attr(tab.availability)}" aria-selected="{active}">'
            f"{_safe_text(tab.label)} {render_status_pill(tab.availability)}</button>"
        )
    return '<nav class="product-mode-tabs" data-product-component="ModeTabs">' + "".join(rendered) + "</nav>"


def render_domain_lens(
    domain_lenses: Sequence[HandoffOption | Any] | None = None,
    *,
    lenses: Sequence[HandoffOption | Any] | None = None,
) -> str:
    options = tuple(_normalize_option(lens) for lens in _as_sequence(domain_lenses or lenses or ()))
    if not options:
        raise ValueError("DomainLens requires domain options.")
    rendered = []
    for option in options:
        if option.label not in SUPPORTED_DOMAIN_LABELS:
            raise ValueError(f"Unsupported domain lens label: {option.label}")
        rendered.append(
            '<button type="button" class="product-domain-lens" '
            f'data-product-component="DomainLens" data-domain-label="{_attr(option.label)}" '
            f'data-availability="{_attr(option.availability)}">'
            f"{_safe_text(option.label)} {render_status_pill(option.availability)}</button>"
        )
    return '<div class="product-domain-lens-group" data-product-component="DomainLens">' + "".join(rendered) + "</div>"


def render_visual_contract(visual: Any) -> str:
    if isinstance(visual, UnavailableVisualState):
        return render_unavailable_state(visual)
    if isinstance(visual, TimeSeriesVisual):
        return _render_visual_container(visual.title, "TimeSeriesVisual", visual.provenance)
    if isinstance(visual, DistributionVisual):
        return _render_visual_container(visual.title, "DistributionVisual", visual.provenance)
    if isinstance(visual, ViolinVisual):
        title = _field(_field(visual, "distribution"), "title", "Violin visual")
        return _render_visual_container(title, "ViolinVisual", ())
    if isinstance(visual, ComparisonDeltaVisual):
        return _render_visual_container(visual.title, "ComparisonDeltaVisual", visual.provenance)
    raise ValueError("VisualContainer accepts only explicit product visual contracts or UnavailableVisualState.")


def render_internal_refs_annex(internal_refs: Sequence[str] | None = None) -> str:
    refs = tuple(_safe_text(ref, allow_internal=True) for ref in _as_sequence(internal_refs or ()))
    if not refs:
        return ""
    items = "".join(f"<li>{ref}</li>" for ref in refs)
    return (
        '<details class="product-internal-refs-annex" data-product-component="InternalRefsAnnex" '
        'data-product-internal-refs="true">'
        "<summary>internal refs annex</summary>"
        f"<ul>{items}</ul></details>"
    )


def render_product_screen_handoff(screen_handoff: ProductScreenHandoff | Any) -> str:
    if not isinstance(screen_handoff, ProductScreenHandoff) and not _has_fields(screen_handoff, ("screen_id", "view_model")):
        raise ValueError("render_product_screen_handoff requires a ProductScreenHandoff-shaped object.")
    screen_role = _field(screen_handoff, "screen_role", "Product screen")
    view_model = _field(screen_handoff, "view_model")
    scope_summary = _field(screen_handoff, "selected_scope_summary") or _field(view_model, "scope_summary")
    sections = [
        render_surface_card(screen_role, _first_fold_summary(view_model), status=_field(screen_handoff, "flow_kind")),
    ]
    if scope_summary:
        sections.append(render_scope_summary(scope_summary))
    evidence_rows = _field(view_model, "evidence_table")
    if evidence_rows:
        sections.append(render_evidence_table(evidence_rows))
    for visual in _as_sequence(_field(screen_handoff, "visual_contracts")):
        sections.append(render_visual_contract(visual))
    for state in _as_sequence(_field(screen_handoff, "unavailable_states")):
        if isinstance(state, UnavailableVisualState):
            sections.append(render_unavailable_state(state))
    sections.append(render_internal_refs_annex(_field(screen_handoff, "internal_refs")))
    return (
        '<section class="product-screen-handoff" data-product-component="ProductScreenHandoff" '
        f'data-screen-id="{_attr(_field(screen_handoff, "screen_id"))}">'
        f"{''.join(sections)}</section>"
    )


SurfaceCard = render_surface_card
SubCard = render_sub_card
StatusPill = render_status_pill
ScopeSummaryCard = render_scope_summary
UnavailableStateCard = render_unavailable_state
EvidenceTable = render_evidence_table
ModeTabs = render_mode_tabs
DomainLens = render_domain_lens
VisualContainer = render_visual_contract
InternalRefsAnnex = render_internal_refs_annex


def _render_visual_container(title: str, visual_kind: str, provenance: Sequence[str]) -> str:
    provenance_items = "".join(f"<li>{_safe_text(item)}</li>" for item in _as_sequence(provenance))
    provenance_html = f'<ul class="product-visual-provenance">{provenance_items}</ul>' if provenance_items else ""
    return (
        '<section class="product-visual-container" data-product-component="VisualContainer" '
        f'data-visual-kind="{_attr(visual_kind)}">'
        f"<h4>{_safe_text(title)}</h4>"
        f"{render_status_pill('ready')}"
        "<p>Future chart drawing will consume this explicit visual contract.</p>"
        f"{provenance_html}</section>"
    )


def _normalize_evidence_row(row: Any) -> EvidenceDisplayRow:
    if isinstance(row, EvidenceDisplayRow):
        return row
    if isinstance(row, Mapping):
        if not set(REQUIRED_EVIDENCE_ROW_FIELDS).issubset(row):
            raise ValueError("EvidenceTable rows must be shaped EvidenceDisplayRow mappings.")
        return EvidenceDisplayRow(
            label=_text(row.get("label")),
            value=row.get("value"),
            unit=_text(row.get("unit")),
            interpretation=_text(row.get("interpretation")),
            evidence_ref_label=_text(row.get("evidence_ref_label")),
            freshness_status=_text(row.get("freshness_status")),
            scope_classification=_text(row.get("scope_classification"), "current_scope"),
        )
    if _has_fields(row, REQUIRED_EVIDENCE_ROW_FIELDS):
        return EvidenceDisplayRow(
            label=_text(_field(row, "label")),
            value=_field(row, "value"),
            unit=_text(_field(row, "unit")),
            interpretation=_text(_field(row, "interpretation")),
            evidence_ref_label=_text(_field(row, "evidence_ref_label")),
            freshness_status=_text(_field(row, "freshness_status")),
            scope_classification=_text(_field(row, "scope_classification"), "current_scope"),
        )
    raise ValueError("EvidenceTable accepts only shaped product evidence rows.")


def _normalize_option(value: Any) -> HandoffOption:
    if isinstance(value, HandoffOption):
        return value
    if isinstance(value, Mapping):
        return HandoffOption(
            label=_text(value.get("label")),
            value=_text(value.get("value")),
            availability=_text(value.get("availability"), "unavailable"),
            reason=_text(value.get("reason")),
        )
    if _has_fields(value, ("label", "value")):
        return HandoffOption(
            label=_text(_field(value, "label")),
            value=_text(_field(value, "value")),
            availability=_text(_field(value, "availability"), "unavailable"),
            reason=_text(_field(value, "reason")),
        )
    raise ValueError("ModeTabs and DomainLens require HandoffOption-shaped values.")


def _first_fold_summary(view_model: Any) -> str:
    first_fold = _field(view_model, "first_fold")
    if first_fold is not None:
        parts = []
        for field_name in ("status_label", "primary_issue_label", "missing_evidence_summary"):
            text = _text(_field(first_fold, field_name))
            if text:
                parts.append(text)
        if parts:
            return " | ".join(parts)
    section = _field(view_model, "first_fold") or _field(view_model, "governance_summary")
    title = _text(_field(section, "title"))
    if title:
        return title
    return _text(_field(view_model, "screen_id"), "Product screen")


def _safe_body(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _safe_text(value)
    if isinstance(value, EvidenceDisplayRow):
        return render_evidence_table((value,))
    if isinstance(value, UnavailableVisualState):
        return render_unavailable_state(value)
    if isinstance(value, ProductScopeSummary):
        return render_scope_summary(value)
    if isinstance(value, Mapping) or _is_sequence(value):
        return f'<p class="product-safe-placeholder">{_safe_text(PRODUCT_SAFE_PLACEHOLDER)}</p>'
    if is_dataclass(value):
        return f'<p class="product-safe-placeholder">{_safe_text(PRODUCT_SAFE_PLACEHOLDER)}</p>'
    return _safe_text(value)


def _safe_text(value: Any, *, allow_internal: bool = False) -> str:
    if _is_raw_payload(value):
        return escape(PRODUCT_SAFE_PLACEHOLDER, quote=True)
    text = _text(value)
    if not allow_internal and (_contains_forbidden_text(text) or _looks_like_object_repr(text)):
        text = "Blocked non-authoritative product content."
    return escape(text, quote=True)


def _safe_status(value: Any) -> str:
    text = _text(value, "neutral").lower().replace(" ", "_")
    return text if text in SUPPORTED_STATUS_VALUES else "neutral"


def _contains_forbidden_text(value: str) -> bool:
    normalized_value = value.lower()
    return any(marker.lower() in normalized_value for marker in FORBIDDEN_TEXT_MARKERS)


def _is_raw_payload(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return False
    if getattr(value, "value", None) is not None:
        return False
    return isinstance(value, Mapping) or _is_sequence(value) or is_dataclass(value)


def _looks_like_object_repr(value: str) -> bool:
    normalized = value.strip()
    return normalized.startswith("<") and " object at 0x" in normalized and normalized.endswith(">")


def _data_attrs(values: Mapping[str, Any]) -> str:
    parts = []
    for key, value in sorted(values.items()):
        attr_key = _attr(str(key).replace("_", "-"))
        attr_value = _safe_text(value)
        parts.append(f' data-{attr_key}="{attr_value}"')
    return "".join(parts)


def _safe_data_attrs(values: Mapping[str, Any] | None) -> dict[str, str]:
    if not values:
        return {}
    return {
        str(key): _text(value)
        for key, value in values.items()
        if not _contains_forbidden_text(str(key)) and not _contains_forbidden_text(_text(value))
    }


def _attr(value: Any) -> str:
    text = _text(value).lower().replace(" ", "-").replace("_", "-")
    return escape("".join(character for character in text if character.isalnum() or character == "-"), quote=True)


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return str(enum_value)
    text = str(value).strip()
    return text or default


def _field(value: Any, field_name: str, default: Any = "") -> Any:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _has_fields(value: Any, field_names: Sequence[str]) -> bool:
    if value is None:
        return False
    if isinstance(value, Mapping):
        return set(field_names).issubset(value)
    if is_dataclass(value):
        names = {field.name for field in fields(value)}
        return set(field_names).issubset(names)
    return all(hasattr(value, field_name) for field_name in field_names)


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if _is_sequence(value):
        return tuple(value)
    return (value,)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
