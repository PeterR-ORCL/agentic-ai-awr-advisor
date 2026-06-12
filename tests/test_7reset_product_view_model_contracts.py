import importlib
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest


_RUN_7RESET_CONTRACTS = os.environ.get("AWR_RUN_7RESET_CONTRACTS") == "1"

pytestmark = pytest.mark.skipif(
    not _RUN_7RESET_CONTRACTS,
    reason=(
        "7RESET product view-model contract gate is intentionally opt-in. "
        "Run with AWR_RUN_7RESET_CONTRACTS=1."
    ),
)


SELECTED_SCOPE_CANDIDATES = (
    "src.reporting.dashboard.contracts.selected_review_scope_contract",
    "src.reporting.dashboard.contracts.product_selected_review_scope_contract",
    "src.reporting.dashboard.view_models.product_scope_contracts",
)

EVIDENCE_PACK_CANDIDATES = (
    "src.reporting.dashboard.contracts.evidence_pack_contract",
    "src.reporting.dashboard.contracts.product_evidence_pack_contract",
    "src.reporting.dashboard.view_models.product_evidence_pack_contracts",
)

SCREEN3_CANDIDATES = (
    "src.reporting.dashboard.view_models.screen3_diagnostic_snapshot",
    "src.reporting.dashboard.view_models.screen3_view_model",
    "src.reporting.dashboard.view_models.product_screen3",
    "src.reporting.dashboard.view_models.product",
)

SCREEN4_CANDIDATES = (
    "src.reporting.dashboard.view_models.screen4_evidence_review",
    "src.reporting.dashboard.view_models.screen4_view_model",
    "src.reporting.dashboard.view_models.product_screen4",
    "src.reporting.dashboard.view_models.product",
)

SCREEN5_CANDIDATES = (
    "src.reporting.dashboard.view_models.screen5_recommendation_action",
    "src.reporting.dashboard.view_models.screen5_view_model",
    "src.reporting.dashboard.view_models.product_screen5",
    "src.reporting.dashboard.view_models.product",
)

SCREEN6_CANDIDATES = (
    "src.reporting.dashboard.view_models.screen6_learning_governance",
    "src.reporting.dashboard.view_models.screen6_view_model",
    "src.reporting.dashboard.view_models.product_screen6",
    "src.reporting.dashboard.view_models.product",
)

SHARED_SHAPE_CANDIDATES = (
    "src.reporting.dashboard.view_models.shared_product_shapes",
    "src.reporting.dashboard.view_models.visual_contracts",
    "src.reporting.dashboard.view_models.product_shapes",
    "src.reporting.dashboard.view_models.product",
    "src.reporting.dashboard.contracts.visual_contracts",
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (project_root() / relative_path).read_text(encoding="utf-8")


def expected_reset_doc_text() -> str:
    return read_text("docs/architecture/7reset_dashboard_product_recut.md")


def import_first_available(candidates: tuple[str, ...]):
    errors: list[str] = []
    for module_name in candidates:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            errors.append(f"{module_name}: {exc}")
    pytest.fail(
        "No candidate module for the 7RESET product contract exists. "
        f"Candidates: {candidates}. Import errors: {errors}"
    )


def load_named_contract(class_name: str, candidate_modules: tuple[str, ...]):
    import_errors: list[str] = []
    inspected_modules: list[str] = []
    schema_names = _schema_names(class_name)
    for module_name in candidate_modules:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            import_errors.append(f"{module_name}: {exc}")
            continue
        inspected_modules.append(module_name)
        for attr_name in (class_name, *schema_names):
            if hasattr(module, attr_name):
                return getattr(module, attr_name), module
        for registry_name in ("PRODUCT_CONTRACT_SCHEMAS", "PRODUCT_VIEW_MODEL_SCHEMAS", "VISUAL_CONTRACT_SCHEMAS"):
            registry = getattr(module, registry_name, None)
            if isinstance(registry, Mapping) and class_name in registry:
                return registry[class_name], module
    pytest.fail(
        f"{class_name} is missing from production source. 7RESET requires a real "
        "product-safe contract class/schema, not renderer output or generated HTML. "
        f"Inspected modules: {inspected_modules or 'none'}. Import errors: {import_errors}"
    )


def get_contract_annotations(obj: Any) -> dict[str, Any]:
    if isinstance(obj, Mapping):
        return dict(obj)
    annotations = getattr(obj, "__annotations__", None)
    if annotations:
        return dict(annotations)
    schema = getattr(obj, "schema", None)
    if isinstance(schema, Mapping):
        return dict(schema)
    fields = getattr(obj, "fields", None)
    if isinstance(fields, Mapping):
        return dict(fields)
    pytest.fail(
        f"{getattr(obj, '__name__', obj)!r} does not expose annotations or a schema. "
        "7RESET product contracts must be typed; raw untyped dict/list passthrough is not acceptable."
    )


def assert_required_fields(contract_name: str, fields: tuple[str | tuple[str, ...], ...], annotations_or_schema):
    actual = set(annotations_or_schema)
    missing: list[str] = []
    for field in fields:
        if isinstance(field, tuple):
            if not any(option in actual for option in field):
                missing.append(" or ".join(field))
        elif field not in actual:
            missing.append(field)
    assert not missing, (
        f"{contract_name} is missing required product-safe field(s): {missing}. "
        "Persisted/backend contracts must carry deterministic product truth explicitly."
    )


def assert_literal_values(contract_name: str, field_name: str, expected_values: tuple[str, ...], annotations_or_schema, source: str):
    haystack = " ".join(
        [
            str(annotations_or_schema.get(field_name, "")),
            source,
        ]
    )
    missing = [value for value in expected_values if value not in haystack]
    assert not missing, (
        f"{contract_name}.{field_name} does not declare required literal value(s): {missing}. "
        "The product contract must make supported states explicit instead of relying on renderer strings."
    )


def assert_not_product_field(contract_name: str, field_name: str, annotations_or_schema, reason: str):
    assert field_name not in annotations_or_schema, (
        f"{contract_name}.{field_name} must not be a top-level product field. {reason}"
    )


def assert_contract_has_guardrail_text_or_field(contract_name: str, source: str, guardrail: str):
    normalized_source = _normalize(source)
    required_tokens = _guardrail_tokens(guardrail)
    missing = [token for token in required_tokens if token not in normalized_source]
    assert not missing, (
        f"{contract_name} does not declare guardrail: {guardrail!r}. "
        f"Missing token(s): {missing}. Product contracts must preserve this architecture boundary."
    )


def assert_fields_not_raw_dict(contract_name: str, fields: tuple[str, ...], annotations_or_schema):
    raw_fields = []
    for field in fields:
        annotation = str(annotations_or_schema.get(field, "")).lower()
        if "dict" in annotation and "any" in annotation:
            raw_fields.append(field)
        if annotation in {"dict", "list", "tuple[dict[str, any], ...]", "list[dict[str, any]]"}:
            raw_fields.append(field)
    assert not raw_fields, (
        f"{contract_name} uses raw dict/list passthrough for product field(s): {sorted(set(raw_fields))}. "
        "Product view models must expose typed product-safe structures."
    )


def module_source(module) -> str:
    path = getattr(module, "__file__", None)
    return Path(path).read_text(encoding="utf-8") if path else ""


def contract_subject(class_name: str, candidates: tuple[str, ...]):
    obj, module = load_named_contract(class_name, candidates)
    annotations = get_contract_annotations(obj)
    return obj, module, annotations, module_source(module)


def _schema_names(class_name: str) -> tuple[str, ...]:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).upper()
    return (
        f"{class_name}Schema",
        f"{class_name}_SCHEMA",
        f"{snake}_SCHEMA",
        f"{snake}_CONTRACT",
    )


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower())


def _guardrail_tokens(guardrail: str) -> tuple[str, ...]:
    token_map = {
        "browser/localStorage/cache cannot create selected truth": ("browser", "localstorage", "cache", "truth"),
        "generated HTML cannot create selected truth": ("generated", "html", "truth"),
        "LLM cannot create selected truth": ("llm", "truth"),
        "single_awr scope cannot be polluted by historical_multi_snapshot context": (
            "single",
            "awr",
            "historical",
            "multi",
            "snapshot",
        ),
        "comparison is unavailable unless Target A/B are deterministically resolved": (
            "comparison",
            "target",
            "deterministic",
            "resolved",
        ),
        "predictive/comparative sizing are unavailable unless real sizing contracts exist": (
            "predictive",
            "comparative",
            "sizing",
            "contract",
        ),
        "selected diagnostic evidence is not supporting historical context": (
            "selected",
            "diagnostic",
            "historical",
            "context",
        ),
        "historical context must be labeled supporting/contextual": ("historical", "supporting", "context"),
        "comparison evidence requires deterministic comparison contract": ("comparison", "deterministic", "contract"),
        "deep analysis evidence requires real deep-analysis input contract": ("deep", "analysis", "input", "contract"),
        "visualization evidence is renderer input only": ("visualization", "renderer", "input"),
        "allowed_visualizations must never be user-facing evidence": ("allowed", "visualizations", "user", "evidence"),
        "debug/internal refs must not appear in first-fold product UI": ("debug", "internal", "first", "fold"),
    }
    return token_map[guardrail]


def test_reset_control_document_preserves_positive_contract_sections():
    text = expected_reset_doc_text()

    for phrase in (
        "Exact proposed view model shapes",
        "Canonical SelectedReviewScopeContract shape",
        "Canonical EvidencePackContract shape",
        "Exact visual contracts",
        "Screen3DiagnosticSnapshotViewModel",
        "Screen4EvidenceReviewViewModel",
        "Screen5RecommendationActionViewModel",
        "Screen6LearningGovernanceViewModel",
        "ProductScopeSummary",
        "ExplanationBlock",
        "UnavailableVisualState",
        "TimeSeriesVisual",
        "DistributionVisual",
        "ViolinVisual",
        "ComparisonDeltaVisual",
    ):
        assert phrase in text, f"7RESET control artifact must retain positive contract language: {phrase}"


def test_selected_review_scope_contract_declares_authoritative_scope_shape():
    _, _, annotations, _ = contract_subject("SelectedReviewScopeContract", SELECTED_SCOPE_CANDIDATES)

    assert_required_fields(
        "SelectedReviewScopeContract",
        (
            "contract_type",
            "contract_version",
            "flow_kind",
            "selected_report",
            ("selected_snapshot", "selected_window"),
            "runtime_scope",
            "target_a",
            "target_b",
            ("fleet", "cohort", "fleet_cohort"),
            "source_of_truth",
            "validation_status",
            "freshness",
            "unsupported_states",
            "missing_states",
            "provenance",
            "internal_refs",
        ),
        annotations,
    )


def test_selected_review_scope_contract_declares_supported_flow_kinds_and_guardrails():
    _, _, annotations, source = contract_subject("SelectedReviewScopeContract", SELECTED_SCOPE_CANDIDATES)

    assert_literal_values(
        "SelectedReviewScopeContract",
        "flow_kind",
        (
            "single_awr",
            "runtime_scope",
            "historical_multi_snapshot",
            "comparison",
            "fleet",
            "predictive_sizing",
            "comparative_sizing",
            "healthcheck",
        ),
        annotations,
        source,
    )
    for guardrail in (
        "browser/localStorage/cache cannot create selected truth",
        "generated HTML cannot create selected truth",
        "LLM cannot create selected truth",
        "single_awr scope cannot be polluted by historical_multi_snapshot context",
        "comparison is unavailable unless Target A/B are deterministically resolved",
        "predictive/comparative sizing are unavailable unless real sizing contracts exist",
    ):
        assert_contract_has_guardrail_text_or_field("SelectedReviewScopeContract", source, guardrail)


def test_evidence_pack_contract_separates_selected_context_comparison_and_deep_evidence():
    _, _, annotations, _ = contract_subject("EvidencePackContract", EVIDENCE_PACK_CANDIDATES)

    assert_required_fields(
        "EvidencePackContract",
        (
            "contract_type",
            "contract_version",
            "selected_scope_ref",
            "selected_diagnostic_evidence",
            "supporting_historical_context",
            "comparison_evidence",
            "deep_analysis_evidence",
            "recommendation_evidence",
            "sizing_evidence",
            "healthcheck_evidence",
            "visualization_evidence",
            "confidence_basis",
            "missing_evidence",
            "unavailable_states",
            "provenance",
            "debug_metadata",
            "internal_refs",
        ),
        annotations,
    )


def test_evidence_pack_contract_declares_visualization_and_debug_guardrails():
    _, _, _, source = contract_subject("EvidencePackContract", EVIDENCE_PACK_CANDIDATES)

    for guardrail in (
        "selected diagnostic evidence is not supporting historical context",
        "historical context must be labeled supporting/contextual",
        "comparison evidence requires deterministic comparison contract",
        "deep analysis evidence requires real deep-analysis input contract",
        "visualization evidence is renderer input only",
        "allowed_visualizations must never be user-facing evidence",
        "debug/internal refs must not appear in first-fold product UI",
    ):
        assert_contract_has_guardrail_text_or_field("EvidencePackContract", source, guardrail)


def test_screen3_diagnostic_snapshot_view_model_declares_product_safe_shape():
    _, _, annotations, source = contract_subject("Screen3DiagnosticSnapshotViewModel", SCREEN3_CANDIDATES)

    assert_required_fields(
        "Screen3DiagnosticSnapshotViewModel",
        (
            "screen_id",
            "contract_version",
            "scope_summary",
            "first_fold",
            "primary_cards",
            "secondary_sections",
            "visuals",
            "evidence_table",
            "missing_evidence",
            "llm_explanation",
            "provenance",
            "freshness",
            "internal_refs",
        ),
        annotations,
    )
    assert_literal_values(
        "Screen3DiagnosticSnapshotViewModel",
        "screen_id",
        ("screen3_diagnostic_snapshot",),
        annotations,
        source,
    )
    assert_fields_not_raw_dict(
        "Screen3DiagnosticSnapshotViewModel",
        ("first_fold", "primary_cards", "secondary_sections", "evidence_table"),
        annotations,
    )


def test_screen3_first_fold_excludes_internal_ids_and_raw_debug_payloads():
    _, _, annotations, source = contract_subject("Screen3DiagnosticSnapshotViewModel", SCREEN3_CANDIDATES)
    _, _, first_fold_annotations, _ = contract_subject("DiagnosticFirstFold", SCREEN3_CANDIDATES + SHARED_SHAPE_CANDIDATES)

    assert_required_fields(
        "DiagnosticFirstFold",
        (
            "status_label",
            "primary_issue_label",
            "severity_score",
            "confidence_score",
            "top_driver_labels",
            "missing_evidence_summary",
        ),
        first_fold_annotations,
    )
    for field_name in ("selected_flow_id", "evidence_pack_id"):
        assert_not_product_field(
            "Screen3DiagnosticSnapshotViewModel",
            field_name,
            annotations,
            "Internal IDs may exist only under internal_refs, provenance, or debug_metadata.",
        )
    assert "historical_multi_snapshot" in source and "single_awr" in source, (
        "Screen3DiagnosticSnapshotViewModel must explicitly guard single-AWR diagnostic truth "
        "from historical_multi_snapshot context."
    )


def test_screen3_llm_explanation_is_not_evidence():
    _, _, annotations, source = contract_subject("Screen3DiagnosticSnapshotViewModel", SCREEN3_CANDIDATES)
    _, _, explanation_annotations, explanation_source = contract_subject(
        "ExplanationBlock",
        SCREEN3_CANDIDATES + SHARED_SHAPE_CANDIDATES,
    )

    assert "llm_explanation" in annotations, "Screen 3 must expose LLM explanation only as a bounded explanation block."
    assert_required_fields(
        "ExplanationBlock",
        ("eligibility", "explanation_text", "explains_refs", "prohibited_as_evidence"),
        explanation_annotations,
    )
    assert "prohibited_as_evidence" in explanation_source and "true" in _normalize(explanation_source + source), (
        "ExplanationBlock must explicitly prohibit LLM explanation from becoming diagnostic evidence."
    )


def test_screen4_evidence_review_view_model_declares_three_distinct_modes():
    _, _, annotations, source = contract_subject("Screen4EvidenceReviewViewModel", SCREEN4_CANDIDATES)

    assert_required_fields(
        "Screen4EvidenceReviewViewModel",
        (
            "screen_id",
            "contract_version",
            "scope_summary",
            "active_mode",
            "mode_tabs",
            "historical",
            "comparative",
            "deep_analysis",
            "cross_mode_warnings",
            "provenance",
            "freshness",
            "internal_refs",
        ),
        annotations,
    )
    assert_literal_values(
        "Screen4EvidenceReviewViewModel",
        "screen_id",
        ("screen4_evidence_review",),
        annotations,
        source,
    )
    assert_literal_values(
        "Screen4EvidenceReviewViewModel",
        "active_mode",
        ("historical", "comparative", "deep_analysis"),
        annotations,
        source,
    )


def test_screen4_mode_panels_require_availability_and_scope_classification():
    _, _, mode_annotations, source = contract_subject("EvidenceReviewModePanel", SCREEN4_CANDIDATES + SHARED_SHAPE_CANDIDATES)
    _, _, section_annotations, _ = contract_subject("EvidenceReviewSection", SCREEN4_CANDIDATES + SHARED_SHAPE_CANDIDATES)

    assert_required_fields(
        "EvidenceReviewModePanel",
        (
            "mode",
            "availability",
            "first_fold_summary",
            "primary_cards",
            "secondary_sections",
            "visuals",
            "evidence_table",
            "unavailable_states",
            "llm_explanation",
        ),
        mode_annotations,
    )
    assert_literal_values(
        "EvidenceReviewModePanel",
        "availability",
        ("ready", "partial", "unavailable", "blocked"),
        mode_annotations,
        source,
    )
    assert "scope_classification" in section_annotations, (
        "Screen 4 evidence rows/sections must expose scope_classification so historical, comparative, "
        "and deep-analysis evidence cannot collapse into an untyped generic list."
    )


def test_screen4_comparative_and_deep_modes_require_deterministic_input_contracts():
    _, _, _, source = contract_subject("Screen4EvidenceReviewViewModel", SCREEN4_CANDIDATES)

    for required in (
        "deterministic Target A/B comparison evidence",
        "deterministic deep-analysis input evidence",
        "historical context cannot be represented as selected-scope truth",
        "unavailable state",
        "trend IDs and point counts are not sufficient product evidence rows",
    ):
        tokens = _normalize(required).split()
        missing = [token for token in tokens if token not in _normalize(source)]
        assert not missing, (
            "Screen4EvidenceReviewViewModel must declare mode-boundary guardrail "
            f"{required!r}; missing token(s): {missing}."
        )


def test_screen5_recommendation_action_view_model_requires_deterministic_recommendation_evidence():
    _, _, annotations, source = contract_subject("Screen5RecommendationActionViewModel", SCREEN5_CANDIDATES)

    assert_required_fields(
        "Screen5RecommendationActionViewModel",
        (
            "screen_id",
            "contract_version",
            "scope_summary",
            "first_fold",
            "recommendation_decision",
            "action_plan",
            "validation_checklist",
            "risk_impact",
            "owner_status",
            "outcome_capture",
            "secondary_sections",
            "llm_explanation",
            "provenance",
            "freshness",
            "internal_refs",
        ),
        annotations,
    )
    for phrase in ("deterministic recommendation", "llm explanation is not recommendation evidence", "browser", "cache"):
        assert phrase in _normalize(source), (
            "Screen5RecommendationActionViewModel must require deterministic recommendation evidence "
            "and block LLM/browser/cache-created action readiness."
        )


def test_screen6_learning_governance_view_model_requires_governed_eligibility():
    _, _, annotations, source = contract_subject("Screen6LearningGovernanceViewModel", SCREEN6_CANDIDATES)

    assert_required_fields(
        "Screen6LearningGovernanceViewModel",
        (
            "screen_id",
            "contract_version",
            "governance_summary",
            "candidate_queue",
            "governance_status",
            "materialization_gate",
            "runtime_eligibility",
            "memory_policy",
            "audit_timeline",
            "secondary_sections",
            "provenance",
            "freshness",
            "internal_refs",
        ),
        annotations,
    )
    for phrase in ("governed eligibility", "semantic recall", "materialization", "llm cannot approve"):
        assert phrase in _normalize(source), (
            "Screen6LearningGovernanceViewModel must require governed runtime eligibility and "
            "must block memory/LLM-created learning or materialization state."
        )


def test_shared_product_shapes_require_scope_evidence_explanation_and_unavailable_state_contracts():
    shape_requirements = {
        "ProductScopeSummary": ("label", "database_label", "instance_label", "snapshot_window_label", "flow_kind", "validation_status"),
        "EvidenceReviewSection": ("section_id", "title", "scope_classification", "rows", "limitations"),
        "EvidenceDisplayRow": ("label", "value", "unit", "interpretation", "evidence_ref_label", "freshness_status"),
        "ExplanationBlock": ("eligibility", "explanation_text", "explains_refs", "prohibited_as_evidence"),
        "UnavailableVisualState": (
            "state_id",
            "reason_code",
            "title",
            "message",
            "required_contract",
            "missing_fields",
            "scope_classification",
            "prohibited_substitutes",
            "next_deterministic_step",
        ),
    }

    combined_source = ""
    for shape_name, fields in shape_requirements.items():
        _, module, annotations, source = contract_subject(shape_name, SHARED_SHAPE_CANDIDATES)
        combined_source += "\n" + source
        assert_required_fields(shape_name, fields, annotations)
    for value in (
        "current_scope",
        "historical_supporting_context",
        "comparative_output",
        "deep_analysis_current_scope",
        "governance_persisted",
    ):
        assert value in combined_source, f"Shared product shapes must declare scope classification: {value}"


def test_explanation_block_is_explicitly_prohibited_as_evidence():
    _, _, annotations, source = contract_subject("ExplanationBlock", SHARED_SHAPE_CANDIDATES)

    assert_required_fields(
        "ExplanationBlock",
        ("eligibility", "explanation_text", "explains_refs", "prohibited_as_evidence"),
        annotations,
    )
    assert "prohibited_as_evidence" in source and "true" in _normalize(source), (
        "ExplanationBlock must make LLM text explanatory only; it cannot create evidence or decisions."
    )


def test_visual_contracts_require_data_provenance_units_and_unavailable_state():
    requirements = {
        "TimeSeriesVisual": (
            "visual_id",
            "visual_kind",
            "title",
            "scope_classification",
            "x_axis",
            "y_axis",
            "series",
            "minimum_point_count",
            "interpolation_allowed",
            "synthetic_data_allowed",
            "provenance",
            "unavailable_state",
        ),
        "DistributionVisual": (
            "visual_id",
            "visual_kind",
            "title",
            "scope_classification",
            "metric_name",
            "groups",
            "synthetic_data_allowed",
            "provenance",
            "unavailable_state",
        ),
        "ViolinVisual": (
            "visual_id",
            "visual_kind",
            "distribution",
            "density_method",
            "density_points",
            "synthetic_data_allowed",
        ),
        "ComparisonDeltaVisual": (
            "visual_id",
            "visual_kind",
            "title",
            "scope_classification",
            "target_a",
            "target_b",
            "delta_rows",
            "synthetic_data_allowed",
            "provenance",
            "unavailable_state",
        ),
    }
    expected_kinds = {
        "TimeSeriesVisual": "time_series",
        "DistributionVisual": "distribution",
        "ViolinVisual": "violin",
        "ComparisonDeltaVisual": "comparison_delta",
    }

    for contract_name, fields in requirements.items():
        _, _, annotations, source = contract_subject(contract_name, SHARED_SHAPE_CANDIDATES)
        assert_required_fields(contract_name, fields, annotations)
        assert_literal_values(contract_name, "visual_kind", (expected_kinds[contract_name],), annotations, source)
        assert "evidence_ref" in source or "provenance" in source, (
            f"{contract_name} must include evidence references or visual provenance; chart metadata alone is not evidence."
        )


def test_visual_contracts_forbid_synthetic_and_metadata_only_visuals():
    for contract_name in ("TimeSeriesVisual", "DistributionVisual", "ViolinVisual", "ComparisonDeltaVisual"):
        _, _, annotations, source = contract_subject(contract_name, SHARED_SHAPE_CANDIDATES)
        assert "allowed_visualizations" not in annotations, (
            f"{contract_name} must be a real data/provenance contract; allowed_visualizations is renderer metadata."
        )
        normalized_source = _normalize(source)
        for phrase in ("synthetic_data_allowed", "false", "unavailable_state"):
            assert _normalize(phrase).strip() in normalized_source, (
                f"{contract_name} must forbid synthetic/static visuals and require unavailable state for missing data."
            )
        assert "svg" not in normalized_source or "fake static svg is not evidence" in normalized_source, (
            f"{contract_name} must not treat fake/static SVG as evidence."
        )


def test_7reset_v_contract_gate_does_not_use_generated_html_as_truth():
    text = Path(__file__).read_text(encoding="utf-8")

    forbidden = (
        "awr_" + "dashboard/",
        "screen_3_" + "analysis.html",
        "screen_4_" + "historical_review.html",
        "src.reporting.dashboard." + "renderers",
        "screen3_" + "renderer",
        "screen4_" + "renderer",
        "render_" + "screen",
    )
    found = [token for token in forbidden if token in text]
    assert not found, (
        "7RESET-V must stay a source-contract gate. It must not inspect generated HTML "
        f"or import renderers as product-contract truth. Found: {found}"
    )
