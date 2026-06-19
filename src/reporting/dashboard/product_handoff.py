"""Renderer-neutral product handoff bundle for 7RESET dashboard screens.

The handoff layer packages deterministic presenter outputs for future product
renderers. It does not render markup, read generated artifacts, inspect browser
state, use cache continuity as authority, call LLMs, or create product truth.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Literal

from src.reporting.dashboard.presenters import (
    build_screen3_diagnostic_snapshot_view_model,
    build_screen4_evidence_review_view_model,
    build_screen5_recommendation_action_view_model,
    build_screen6_learning_governance_view_model,
)
from src.reporting.dashboard.view_models.screen3_diagnostic_snapshot import (
    Screen3DiagnosticSnapshotViewModel,
)
from src.reporting.dashboard.view_models.screen4_evidence_review import (
    EvidenceReviewModePanel,
    Screen4EvidenceReviewViewModel,
)
from src.reporting.dashboard.view_models.screen5_recommendation_action import (
    Screen5RecommendationActionViewModel,
)
from src.reporting.dashboard.view_models.screen6_learning_governance import (
    Screen6LearningGovernanceViewModel,
)
from src.reporting.dashboard.view_models.shared_product_shapes import (
    ProductScopeSummary,
    UnavailableVisualState,
)
from src.reporting.dashboard.view_models.visual_contracts import (
    ComparisonDeltaVisual,
    DistributionVisual,
    TimeSeriesVisual,
    ViolinVisual,
)


CONTRACT_TYPE = "dashboard_product_handoff_bundle"
CONTRACT_VERSION = "7reset.product_handoff.v1"

SUPPORTED_FLOW_KINDS: tuple[str, ...] = (
    "single_awr",
    "selected_report",
    "runtime_scope",
    "timeframe",
    "historical_multi_snapshot",
    "multi_awr_set",
    "comparison",
    "multi_target_comparison",
    "fleet",
    "cohort",
    "healthcheck",
    "predictive_sizing",
    "comparative_sizing",
    "unavailable",
)

FLOW_KIND_POLICY: tuple[str, ...] = (
    "multi_awr_set remains distinct from comparison",
    "multi_awr_set does not require Target A/B",
    "comparison requires deterministic comparison evidence and resolved targets",
    "multi_target_comparison supports 2+ targets",
    "unsupported/future modes produce unavailable states, not fabricated content",
)

DASHBOARD_HANDOFF_GUARDRAILS: tuple[str, ...] = (
    "generated HTML is not source truth",
    "browser/localStorage/cache is not source truth",
    "LLM explanation is not evidence",
    "renderers consume this bundle but do not create truth",
    "internal refs are not first-fold product content",
)

SOURCE_OF_TRUTH_POLICY: tuple[str, ...] = (
    "source_of_truth must be deterministic persisted contract-backed authority",
    "browser/cache/generated_html cannot create selected truth",
    "LLM cannot create evidence",
)

SCREEN_PAYLOAD_POLICY: tuple[str, ...] = (
    "raw dict/list/pre debug objects are not screen view model payloads",
)

SCREEN4_INTERACTION_POLICY: tuple[str, ...] = (
    "mode_tabs, active_mode, domain_lenses, subsection_options, mode_availability, "
    "visual_availability, and unavailable_states are derived from Screen4EvidenceReviewViewModel "
    "and evidence availability",
    "browser/localStorage cannot create domain/subsection truth",
    "unavailable domains/modes must remain visible",
    "allowed_visualizations must not appear as a user-facing product option",
    "trend IDs and point counts are not subsection labels",
)

VISUAL_HANDOFF_POLICY: tuple[str, ...] = (
    "TimeSeriesVisual",
    "DistributionVisual",
    "ViolinVisual",
    "ComparisonDeltaVisual",
    "UnavailableVisualState",
    "allowed_visualizations is not product UI",
    "chart metadata is not visual evidence",
    "fake/static SVG is not evidence",
    "generated HTML chart fragments are prohibited",
    "raw JSON visual configs are prohibited",
    "missing visual evidence must be represented as UnavailableVisualState",
)

FORBIDDEN_CONTENT_POLICY: tuple[str, ...] = (
    "raw dict/list/pre output",
    "internal IDs in first fold",
    "selected_flow_id in product first fold",
    "evidence_pack_id in product first fold",
    "allowed_visualizations as UI",
    "generated HTML as truth",
    "browser/localStorage/cache as truth",
    "LLM-created evidence",
    "LLM-created recommendations",
    "LLM-created learning/runtime eligibility",
    "fake/static visuals",
)

SCREEN_ROLES: tuple[tuple[str, str, str], ...] = (
    ("screen3_diagnostic_snapshot", "3", "Diagnostic Snapshot"),
    ("screen4_evidence_review", "4", "Evidence Review"),
    ("screen5_recommendation_action", "5", "Recommendation Action"),
    ("screen6_learning_governance", "6", "Learning Governance"),
)

SCREEN_ROLE_BY_ID: dict[str, tuple[str, str]] = {
    screen_id: (screen_number, screen_role)
    for screen_id, screen_number, screen_role in SCREEN_ROLES
}

DOMAIN_LENSES: tuple[str, ...] = (
    "All Domains",
    "CPU",
    "IO",
    "MEMORY",
    "COMMIT",
    "RAC",
    "ADG",
)

NON_AUTHORITATIVE_SOURCE_NAMES: tuple[str, ...] = (
    "localStorage",
    "local_storage",
    "browser" + "_cache",
    "url_hash",
    "generated_html",
    "cached_continuity_only",
)

ProductViewModel = (
    Screen3DiagnosticSnapshotViewModel
    | Screen4EvidenceReviewViewModel
    | Screen5RecommendationActionViewModel
    | Screen6LearningGovernanceViewModel
)
ProductVisualContract = (
    TimeSeriesVisual
    | DistributionVisual
    | ViolinVisual
    | ComparisonDeltaVisual
    | UnavailableVisualState
)


@dataclass(frozen=True)
class RenderPolicy:
    """Renderer policy carried as data, never as renderer behavior."""

    renderer_may_consume_bundle: bool = True
    renderer_may_create_truth: bool = False
    html_generation_allowed: bool = False
    first_fold_internal_refs_allowed: bool = False
    source_authority: str = "deterministic_contract_only"


@dataclass(frozen=True)
class HandoffOption:
    label: str = ""
    value: str = ""
    availability: str = "unavailable"
    reason: str = ""


@dataclass(frozen=True)
class VisualAvailability:
    mode: str = ""
    availability: str = "unavailable"
    visual_contracts: tuple[str, ...] = field(default_factory=tuple)
    unavailable_states: tuple[UnavailableVisualState, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Screen4InteractionContract:
    """Renderer-neutral metadata for Screen 4 UI controls."""

    mode_tabs: tuple[HandoffOption, ...] = field(default_factory=tuple)
    active_mode: str = "historical"
    domain_lenses: tuple[HandoffOption, ...] = field(default_factory=tuple)
    subsection_options: tuple[HandoffOption, ...] = field(default_factory=tuple)
    mode_availability: tuple[HandoffOption, ...] = field(default_factory=tuple)
    visual_availability: tuple[VisualAvailability, ...] = field(default_factory=tuple)
    unavailable_states: tuple[UnavailableVisualState, ...] = field(default_factory=tuple)
    derivation_policy: tuple[str, ...] = SCREEN4_INTERACTION_POLICY


@dataclass(frozen=True)
class ProductScreenHandoff:
    """Passive handoff for one downstream product screen."""

    screen_id: str
    screen_number: str
    screen_role: str
    selected_scope_summary: ProductScopeSummary | None
    flow_kind: str
    view_model: ProductViewModel
    render_policy: RenderPolicy = field(default_factory=RenderPolicy)
    component_contracts: tuple[str, ...] = field(default_factory=tuple)
    visual_contracts: tuple[ProductVisualContract, ...] = field(default_factory=tuple)
    unavailable_states: tuple[UnavailableVisualState, ...] = field(default_factory=tuple)
    interaction_contract: Screen4InteractionContract | None = None
    forbidden_content_policy: tuple[str, ...] = FORBIDDEN_CONTENT_POLICY
    provenance: tuple[str, ...] = field(default_factory=tuple)
    internal_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if isinstance(self.view_model, (Mapping, list, tuple, str, bytes, bytearray)):
            raise TypeError(
                "raw dict/list/pre debug objects are not screen view model payloads"
            )


@dataclass(frozen=True)
class DashboardProductHandoffBundle:
    """Passive dashboard handoff bundle consumed by future renderers."""

    contract_type: str = CONTRACT_TYPE
    contract_version: str = CONTRACT_VERSION
    selected_scope_ref: str = ""
    evidence_pack_ref: str = ""
    source_of_truth: tuple[str, ...] = field(default_factory=tuple)
    freshness: str = "unknown"
    provenance: tuple[str, ...] = field(default_factory=tuple)
    screen_bundles: tuple[ProductScreenHandoff, ...] = field(default_factory=tuple)
    unavailable_states: tuple[UnavailableVisualState, ...] = field(default_factory=tuple)
    internal_refs: tuple[str, ...] = field(default_factory=tuple)
    guardrails: tuple[str, ...] = DASHBOARD_HANDOFF_GUARDRAILS
    source_of_truth_policy: tuple[str, ...] = SOURCE_OF_TRUTH_POLICY
    visual_handoff_policy: tuple[str, ...] = VISUAL_HANDOFF_POLICY
    forbidden_content_policy: tuple[str, ...] = FORBIDDEN_CONTENT_POLICY


ProductScreenHandoffBundle = ProductScreenHandoff


def build_dashboard_product_handoff_bundle(
    selected_scope_contract: Any,
    evidence_pack_contract: Any,
) -> DashboardProductHandoffBundle:
    """Build the renderer-neutral Screen 3/4/5/6 handoff bundle."""

    _assert_deterministic_authority(selected_scope_contract, "selected_scope_contract")
    _assert_deterministic_authority(evidence_pack_contract, "evidence_pack_contract", require_source=False)
    flow_kind = _flow_kind(selected_scope_contract)

    screen3 = build_screen3_diagnostic_snapshot_view_model(selected_scope_contract, evidence_pack_contract)
    screen4 = build_screen4_evidence_review_view_model(selected_scope_contract, evidence_pack_contract)
    screen5 = build_screen5_recommendation_action_view_model(selected_scope_contract, evidence_pack_contract)
    screen6 = build_screen6_learning_governance_view_model(selected_scope_contract, evidence_pack_contract)

    screen_bundles = (
        _screen_handoff(screen3, flow_kind),
        _screen_handoff(screen4, flow_kind),
        _screen_handoff(screen5, flow_kind),
        _screen_handoff(screen6, flow_kind),
    )
    unavailable_states = _bundle_unavailable_states(flow_kind, screen_bundles)

    return DashboardProductHandoffBundle(
        selected_scope_ref=_text(_value(selected_scope_contract, "selected_flow_id")),
        evidence_pack_ref=_text(_value(evidence_pack_contract, "evidence_pack_id")),
        source_of_truth=_source_of_truth(selected_scope_contract, evidence_pack_contract),
        freshness=_freshness(screen_bundles, evidence_pack_contract),
        provenance=_provenance(screen_bundles, selected_scope_contract, evidence_pack_contract),
        screen_bundles=screen_bundles,
        unavailable_states=unavailable_states,
        internal_refs=_internal_refs(selected_scope_contract, evidence_pack_contract),
    )


build_product_handoff_bundle = build_dashboard_product_handoff_bundle


def _screen_handoff(view_model: ProductViewModel, flow_kind: str) -> ProductScreenHandoff:
    screen_id = _text(_value(view_model, "screen_id"))
    screen_number, screen_role = SCREEN_ROLE_BY_ID[screen_id]
    visual_contracts = _visual_contracts_for_screen(view_model)
    unavailable_states = _unavailable_states_for_screen(view_model, visual_contracts)
    return ProductScreenHandoff(
        screen_id=screen_id,
        screen_number=screen_number,
        screen_role=screen_role,
        selected_scope_summary=_value(view_model, "scope_summary"),
        flow_kind=flow_kind,
        view_model=view_model,
        render_policy=RenderPolicy(),
        component_contracts=_component_contracts(view_model),
        visual_contracts=visual_contracts,
        unavailable_states=unavailable_states,
        interaction_contract=(
            _screen4_interaction_contract(view_model)
            if isinstance(view_model, Screen4EvidenceReviewViewModel)
            else None
        ),
        forbidden_content_policy=FORBIDDEN_CONTENT_POLICY,
        provenance=_tuple_texts(_value(view_model, "provenance")),
        internal_refs=_tuple_texts(_value(view_model, "internal_refs")),
    )


def _screen4_interaction_contract(
    view_model: Screen4EvidenceReviewViewModel,
) -> Screen4InteractionContract:
    panels = _screen4_panels(view_model)
    unavailable_states = tuple(
        state
        for panel in panels
        for state in panel.unavailable_states
    )
    return Screen4InteractionContract(
        mode_tabs=tuple(
            HandoffOption(
                label=_mode_label(mode),
                value=mode,
                availability=_panel_for_mode(panels, mode).availability,
            )
            for mode in view_model.mode_tabs
        ),
        active_mode=view_model.active_mode,
        domain_lenses=_domain_lenses_from_screen4(view_model, panels),
        subsection_options=_subsection_options_from_screen4(panels),
        mode_availability=tuple(
            HandoffOption(
                label=_mode_label(panel.mode),
                value=panel.mode,
                availability=panel.availability,
                reason=panel.first_fold_summary,
            )
            for panel in panels
        ),
        visual_availability=tuple(
            VisualAvailability(
                mode=panel.mode,
                availability="ready" if panel.visuals else "unavailable",
                visual_contracts=tuple(type(visual).__name__ for visual in panel.visuals),
                unavailable_states=tuple(
                    state
                    for state in panel.unavailable_states
                    if "visual" in state.reason_code or "Visual" in state.title
                ),
            )
            for panel in panels
        ),
        unavailable_states=unavailable_states,
        derivation_policy=SCREEN4_INTERACTION_POLICY,
    )


def _screen4_panels(view_model: Screen4EvidenceReviewViewModel) -> tuple[EvidenceReviewModePanel, ...]:
    return (view_model.historical, view_model.comparative, view_model.deep_analysis)


def _panel_for_mode(panels: tuple[EvidenceReviewModePanel, ...], mode: str) -> EvidenceReviewModePanel:
    for panel in panels:
        if panel.mode == mode:
            return panel
    return EvidenceReviewModePanel(mode=mode)  # type: ignore[arg-type]


def _domain_lenses_from_screen4(
    view_model: Screen4EvidenceReviewViewModel,
    panels: tuple[EvidenceReviewModePanel, ...],
) -> tuple[HandoffOption, ...]:
    evidence_text = " ".join(
        item.lower()
        for panel in panels
        for item in (
            panel.first_fold_summary,
            *(_section_titles(panel)),
            *(_row_labels(panel)),
        )
        if item
    )
    has_any_rows = any(panel.evidence_table for panel in panels)
    default_availability = "partial" if has_any_rows else "unavailable"
    active_availability = _panel_for_mode(panels, view_model.active_mode).availability
    lenses: list[HandoffOption] = []
    for label in DOMAIN_LENSES:
        if label == "All Domains":
            availability = active_availability if active_availability != "blocked" else "partial"
        else:
            availability = "partial" if label.lower() in evidence_text else default_availability
        lenses.append(
            HandoffOption(
                label=label,
                value=label.lower().replace(" ", "_"),
                availability=availability,
                reason="derived from Screen4EvidenceReviewViewModel evidence availability",
            )
        )
    return tuple(lenses)


def _subsection_options_from_screen4(
    panels: tuple[EvidenceReviewModePanel, ...],
) -> tuple[HandoffOption, ...]:
    options: list[HandoffOption] = []
    seen: set[tuple[str, str]] = set()
    for panel in panels:
        for section in (*panel.primary_cards, *panel.secondary_sections):
            label = _text(_value(section, "title"))
            if not label or not _is_product_subsection_label(label):
                continue
            key = (panel.mode, label)
            if key in seen:
                continue
            seen.add(key)
            availability = panel.availability if _value(section, "rows") else "unavailable"
            options.append(
                HandoffOption(
                    label=label,
                    value=_text(_value(section, "section_id"), label),
                    availability=availability,
                    reason=panel.mode,
                )
            )
    return tuple(options)


def _is_product_subsection_label(label: str) -> bool:
    normalized = label.lower()
    forbidden = (
        "allowed_visualizations",
        "trend_id",
        "trend ids",
        "point_count",
        "point counts",
    )
    return not any(token in normalized for token in forbidden)


def _section_titles(panel: EvidenceReviewModePanel) -> tuple[str, ...]:
    return tuple(
        _text(_value(section, "title"))
        for section in (*panel.primary_cards, *panel.secondary_sections)
    )


def _row_labels(panel: EvidenceReviewModePanel) -> tuple[str, ...]:
    return tuple(
        _text(_value(row, "label"))
        for row in panel.evidence_table
    )


def _mode_label(mode: str) -> str:
    return mode.replace("_", " ").title()


def _component_contracts(view_model: ProductViewModel) -> tuple[str, ...]:
    if isinstance(view_model, Screen3DiagnosticSnapshotViewModel):
        return (
            "Screen3DiagnosticSnapshotViewModel",
            "DiagnosticFirstFold",
            "EvidenceReviewSection",
            "ProductScopeSummary",
        )
    if isinstance(view_model, Screen4EvidenceReviewViewModel):
        return (
            "Screen4EvidenceReviewViewModel",
            "EvidenceReviewModePanel",
            "mode_tabs",
            "active_mode",
        )
    if isinstance(view_model, Screen5RecommendationActionViewModel):
        return (
            "Screen5RecommendationActionViewModel",
            "EvidenceReviewSection",
            "ExplanationBlock",
        )
    return (
        "Screen6LearningGovernanceViewModel",
        "EvidenceReviewSection",
        "governed eligibility",
    )


def _visual_contracts_for_screen(view_model: ProductViewModel) -> tuple[ProductVisualContract, ...]:
    visuals: tuple[ProductVisualContract, ...] = ()
    if isinstance(view_model, Screen3DiagnosticSnapshotViewModel):
        visuals = tuple(view_model.visuals)
    elif isinstance(view_model, Screen4EvidenceReviewViewModel):
        visuals = tuple(
            visual
            for panel in _screen4_panels(view_model)
            for visual in panel.visuals
        )

    if visuals:
        return visuals
    return (_missing_visual_state(_text(_value(view_model, "screen_id"))),)


def _unavailable_states_for_screen(
    view_model: ProductViewModel,
    visual_contracts: tuple[ProductVisualContract, ...],
) -> tuple[UnavailableVisualState, ...]:
    states: list[UnavailableVisualState] = [
        visual
        for visual in visual_contracts
        if isinstance(visual, UnavailableVisualState)
    ]
    states.extend(_explicit_unavailable_states(view_model))
    return tuple(_dedupe_unavailable_states(states))


def _explicit_unavailable_states(view_model: ProductViewModel) -> tuple[UnavailableVisualState, ...]:
    if isinstance(view_model, Screen4EvidenceReviewViewModel):
        return tuple(
            state
            for panel in _screen4_panels(view_model)
            for state in panel.unavailable_states
        )
    states: list[UnavailableVisualState] = []
    for field_name in ("secondary_sections", "validation_checklist"):
        for section in _as_sequence(_value(view_model, field_name)):
            for row in _as_sequence(_value(section, "rows")):
                label = _text(_value(row, "label"))
                if "unavailable" in label:
                    states.append(
                        UnavailableVisualState(
                            state_id=f"{_text(_value(view_model, 'screen_id'))}-{label}",
                            reason_code=label,
                            title=_text(_value(row, "value"), "Unavailable"),
                            message=_text(_value(row, "interpretation")),
                            required_contract=_text(_value(row, "evidence_ref_label")),
                            scope_classification=_value(row, "scope_classification", "current_scope"),
                            prohibited_substitutes=(
                                "generated_html",
                                "localStorage",
                                "llm_text",
                                "static_fake_visual",
                                "allowed_visualizations",
                            ),
                            next_deterministic_step="Provide deterministic contract evidence.",
                        )
                    )
    return tuple(states)


def _bundle_unavailable_states(
    flow_kind: str,
    screen_bundles: tuple[ProductScreenHandoff, ...],
) -> tuple[UnavailableVisualState, ...]:
    states = [
        state
        for screen in screen_bundles
        for state in screen.unavailable_states
    ]
    if flow_kind == "unavailable":
        states.append(
            UnavailableVisualState(
                state_id="handoff-flow-kind-unavailable",
                reason_code="unsupported_or_unavailable_flow_kind",
                title="Selected scope unavailable",
                message="Unsupported/future modes produce unavailable states, not fabricated content.",
                required_contract="selected_review_scope_contract",
                missing_fields=("flow_kind",),
                scope_classification="current_scope",
                prohibited_substitutes=(
                    "generated_html",
                    "localStorage",
                    "llm_text",
                    "allowed_visualizations",
                ),
                next_deterministic_step="Resolve a supported deterministic selected-scope contract.",
            )
        )
    return tuple(_dedupe_unavailable_states(states))


def _missing_visual_state(screen_id: str) -> UnavailableVisualState:
    return UnavailableVisualState(
        state_id=f"{screen_id}-visual-evidence-unavailable",
        reason_code="visual_evidence_unavailable",
        title="Visual evidence unavailable",
        message="missing visual evidence must be represented as UnavailableVisualState.",
        required_contract="visualization_evidence",
        missing_fields=("visualization_evidence",),
        scope_classification="current_scope",
        prohibited_substitutes=(
            "generated_html",
            "localStorage",
            "llm_text",
            "static_fake_visual",
            "allowed_visualizations",
        ),
        next_deterministic_step="Provide explicit TimeSeriesVisual, DistributionVisual, ViolinVisual, or ComparisonDeltaVisual evidence.",
    )


def _dedupe_unavailable_states(
    states: Sequence[UnavailableVisualState],
) -> tuple[UnavailableVisualState, ...]:
    deduped: list[UnavailableVisualState] = []
    seen: set[tuple[str, str]] = set()
    for state in states:
        key = (state.state_id, state.reason_code)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(state)
    return tuple(deduped)


def _assert_deterministic_authority(
    contract: Any,
    contract_name: str,
    *,
    require_source: bool = True,
) -> None:
    if not isinstance(contract, Mapping):
        _reject_forbidden_authority_text(contract, contract_name)
        return
    if require_source and "source_of_truth" not in contract:
        raise ValueError(
            f"{contract_name} mapping must include deterministic source_of_truth authority."
        )
    _reject_forbidden_authority_text(_value(contract, "source_of_truth"), contract_name)
    _reject_forbidden_authority_text(_value(contract, "authority"), contract_name)


def _reject_forbidden_authority_text(value: Any, contract_name: str) -> None:
    haystack = _all_text(value).lower()
    for forbidden in NON_AUTHORITATIVE_SOURCE_NAMES:
        if forbidden.lower() in haystack:
            raise ValueError(
                f"{contract_name} cannot use {forbidden} as source_of_truth authority."
            )


def _source_of_truth(selected_scope_contract: Any, evidence_pack_contract: Any) -> tuple[str, ...]:
    labels = [
        *_source_labels(_value(selected_scope_contract, "source_of_truth")),
        *_source_labels(_value(evidence_pack_contract, "source_of_truth")),
        "deterministic selected_review_scope_contract",
        "persisted evidence_pack_contract",
    ]
    return tuple(_dedupe_text(label for label in labels if label))


def _source_labels(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        labels = []
        for key in ("authority", "source", "source_system", "contract", "contract_type"):
            label = _text(value.get(key))
            if label:
                labels.append(label)
        return tuple(labels)
    if is_dataclass(value):
        labels = []
        for field_info in fields(value):
            if field_info.name in {"authority", "source", "source_system", "contract", "contract_type"}:
                label = _text(getattr(value, field_info.name))
                if label:
                    labels.append(label)
        return tuple(labels)
    return _tuple_texts(value)


def _freshness(
    screen_bundles: tuple[ProductScreenHandoff, ...],
    evidence_pack_contract: Any,
) -> str:
    for screen in screen_bundles:
        freshness = _text(_value(screen.view_model, "freshness"))
        if freshness and freshness != "unknown":
            return freshness
    return _text(_value(evidence_pack_contract, "freshness"), "unknown")


def _provenance(
    screen_bundles: tuple[ProductScreenHandoff, ...],
    selected_scope_contract: Any,
    evidence_pack_contract: Any,
) -> tuple[str, ...]:
    labels: list[str] = []
    for source in (
        _value(selected_scope_contract, "provenance"),
        _value(evidence_pack_contract, "provenance"),
    ):
        labels.extend(_provenance_labels(source))
    for screen in screen_bundles:
        labels.extend(screen.provenance)
    return tuple(_dedupe_text(labels))


def _provenance_labels(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return tuple(
            label
            for label in (
                _text(value.get("source_system")),
                _text(value.get("source")),
                _text(value.get("builder_version")),
            )
            if label
        )
    if is_dataclass(value):
        return tuple(
            label
            for label in (
                _text(getattr(value, "source_system", "")),
                _text(getattr(value, "builder_version", "")),
            )
            if label
        )
    return _tuple_texts(value)


def _internal_refs(selected_scope_contract: Any, evidence_pack_contract: Any) -> tuple[str, ...]:
    return tuple(
        _dedupe_text(
            (
                _text(_value(selected_scope_contract, "selected_flow_id")),
                _text(_value(evidence_pack_contract, "evidence_pack_id")),
            )
        )
    )


def _flow_kind(selected_scope_contract: Any) -> str:
    raw_flow_kind = _text(_value(selected_scope_contract, "flow_kind"), "unavailable")
    return raw_flow_kind if raw_flow_kind in SUPPORTED_FLOW_KINDS else "unavailable"


def _value(source: Any, field_name: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, Mapping):
        return source.get(field_name, default)
    return getattr(source, field_name, default)


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return str(enum_value)
    text = str(value).strip()
    return text or default


def _tuple_texts(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return tuple(_text(item) for item in value if _text(item))
    return (_text(value),)


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def _dedupe_text(values: Sequence[str] | Any) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return tuple(deduped)


def _all_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, Mapping):
        return " ".join(_all_text(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return " ".join(_all_text(item) for item in value)
    if is_dataclass(value):
        return " ".join(_all_text(getattr(value, field_info.name)) for field_info in fields(value))
    return str(value)
