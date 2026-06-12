import importlib
import inspect
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest


_RUN_7RESET_PRESENTERS = os.environ.get("AWR_RUN_7RESET_PRESENTERS") == "1"

pytestmark = pytest.mark.skipif(
    not _RUN_7RESET_PRESENTERS,
    reason=(
        "7RESET product presenter/builder gate is intentionally opt-in. "
        "Run with AWR_RUN_7RESET_PRESENTERS=1."
    ),
)


PRESENTER_CANDIDATES = (
    "src.reporting.dashboard.presenters",
    "src.reporting.dashboard.view_models.builders",
    "src.reporting.dashboard.product_presenters",
)

BUILDER_NAMES = (
    "build_screen3_diagnostic_snapshot_view_model",
    "build_screen4_evidence_review_view_model",
    "build_screen5_recommendation_action_view_model",
    "build_screen6_learning_governance_view_model",
)

BUILDER_CLASS_CANDIDATES = {
    "build_screen3_diagnostic_snapshot_view_model": (
        "Screen3DiagnosticSnapshotPresenter",
        "Screen3DiagnosticSnapshotViewModelBuilder",
    ),
    "build_screen4_evidence_review_view_model": (
        "Screen4EvidenceReviewPresenter",
        "Screen4EvidenceReviewViewModelBuilder",
    ),
    "build_screen5_recommendation_action_view_model": (
        "Screen5RecommendationActionPresenter",
        "Screen5RecommendationActionViewModelBuilder",
    ),
    "build_screen6_learning_governance_view_model": (
        "Screen6LearningGovernancePresenter",
        "Screen6LearningGovernanceViewModelBuilder",
    ),
}

FLOW_KINDS = (
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
)

EVIDENCE_CHANNELS = (
    "selected_diagnostic_evidence",
    "selected_set_evidence",
    "member_diagnostic_evidence",
    "aggregate_evidence",
    "temporal_evidence",
    "supporting_historical_context",
    "comparison_evidence",
    "fleet_or_cohort_evidence",
    "recommendation_evidence",
    "governance_evidence",
    "visualization_evidence",
    "missing_evidence",
    "unavailable_states",
)

VISUAL_CONTRACTS = (
    "TimeSeriesVisual",
    "DistributionVisual",
    "ViolinVisual",
    "ComparisonDeltaVisual",
    "UnavailableVisualState",
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (project_root() / relative_path).read_text(encoding="utf-8")


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def import_presenter_module():
    errors: list[str] = []
    for module_name in PRESENTER_CANDIDATES:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            errors.append(f"{module_name}: {exc}")
    pytest.fail(
        "Missing 7RESET deterministic product presenter/builder module. "
        "Presenters must map database-backed selected/evidence contracts into "
        "product view models before renderer recut work begins. "
        f"Candidates: {PRESENTER_CANDIDATES}. Import errors: {errors}"
    )


def module_source(module: Any) -> str:
    path = getattr(module, "__file__", None)
    return Path(path).read_text(encoding="utf-8") if path else ""


def lookup_builder(module: Any, builder_name: str) -> Any | None:
    direct = getattr(module, builder_name, None)
    if callable(direct):
        return direct

    for registry_name in ("PRODUCT_PRESENTERS", "PRODUCT_PRESENTER_BUILDERS", "PRESENTER_BUILDERS"):
        registry = getattr(module, registry_name, None)
        if isinstance(registry, Mapping):
            candidate = registry.get(builder_name)
            if callable(candidate):
                return candidate

    for class_name in BUILDER_CLASS_CANDIDATES.get(builder_name, ()):
        candidate = getattr(module, class_name, None)
        if callable(candidate):
            return candidate
    return None


def required_builder(module: Any, builder_name: str) -> Any:
    builder = lookup_builder(module, builder_name)
    assert builder is not None, (
        f"{builder_name} is missing. 7RESET presenters must expose deterministic "
        "builders for Screens 3/4/5/6 instead of relying on renderers or generated HTML."
    )
    return builder


def source_for_object(obj: Any) -> str:
    try:
        return inspect.getsource(obj)
    except (OSError, TypeError):
        return ""


def presenter_source_and_signatures() -> tuple[Any, str]:
    module = import_presenter_module()
    parts = [module_source(module)]
    for builder_name in BUILDER_NAMES:
        builder = lookup_builder(module, builder_name)
        if builder is None:
            continue
        try:
            parts.append(str(inspect.signature(builder)))
        except (TypeError, ValueError):
            pass
        parts.append(source_for_object(builder))
    return module, "\n".join(parts)


def assert_contains_all(text: str, required_tokens: tuple[str, ...], rule: str) -> None:
    normalized_text = normalize(text)
    missing = [token for token in required_tokens if normalize(token) not in normalized_text]
    assert not missing, f"{rule} Missing required token(s): {missing}"


def assert_contains_any(text: str, options: tuple[str, ...], rule: str) -> None:
    normalized_text = normalize(text)
    assert any(normalize(option) in normalized_text for option in options), (
        f"{rule} Expected at least one of: {options}"
    )


def assert_not_contains_any(text: str, forbidden_tokens: tuple[str, ...], rule: str) -> None:
    found = [token for token in forbidden_tokens if token in text]
    assert not found, f"{rule} Violating token(s): {found}"


def test_presenter_builder_module_exists_and_declares_required_builders():
    module = import_presenter_module()
    missing = [builder_name for builder_name in BUILDER_NAMES if lookup_builder(module, builder_name) is None]

    assert not missing, (
        "7RESET product presenter/builder layer must expose all Screen 3/4/5/6 builders. "
        f"Missing: {missing}"
    )


def test_presenter_builder_module_dependency_purity():
    _, source = presenter_source_and_signatures()

    forbidden_imports = (
        "from src.reporting." + "html_dashboard",
        "import src.reporting." + "html_dashboard",
        "src.reporting.dashboard." + "renderers",
        "scripts.run_analysis",
        "oci.generative_ai",
        "oci.genai",
        "requests.",
        "httpx",
        "urllib.request",
        "oracledb",
        "cx_Oracle",
        "subprocess",
        "run_analysis(",
        "local" + "Storage.getItem",
        "window.local" + "Storage",
        "document.",
        "awr_" + "dashboard/",
    )
    assert_not_contains_any(
        source,
        forbidden_imports,
        "Product presenters must be dependency-pure and independent of renderers, browser state, artifacts, DB/network calls, OCI GenAI, and scripts.",
    )


def test_presenter_builders_require_deterministic_selected_scope_contract_not_browser_state():
    _, source = presenter_source_and_signatures()

    assert_contains_any(
        source,
        ("selected_review_scope_contract", "SelectedReviewScopeContract", "selected_scope_contract"),
        "Presenter APIs must accept selected scope from deterministic selected_review_scope_contract authority.",
    )
    assert_contains_any(
        source,
        ("evidence_pack_contract", "EvidencePackContract", "evidence_pack"),
        "Presenter APIs must accept deterministic evidence_pack_contract authority.",
    )
    assert_not_contains_any(
        source,
        (
            "browser_state_as_truth",
            "local_storage_as_truth",
            "hash_state_as_truth",
            "generated_html_as_truth",
            "artifact_path_as_truth",
            "cache_as_truth",
        ),
        "Screen 2 selected-scope truth cannot be created by browser/localStorage/hash/cache/generated HTML.",
    )


def test_screen2_selected_scope_authority_declares_required_flow_kinds():
    _, source = presenter_source_and_signatures()

    assert_contains_all(
        source,
        FLOW_KINDS,
        "Presenter builders must route all canonical Screen 2 selected-scope flow kinds.",
    )


def test_multi_awr_analysis_set_is_distinct_from_comparison():
    _, source = presenter_source_and_signatures()

    assert_contains_all(
        source,
        ("multi_awr_set", "multi_target_comparison", "target_a", "target_b"),
        "Presenters must distinguish multi-AWR analysis sets from comparison flows.",
    )
    assert_contains_any(
        source,
        ("selected_scope_analysis_set", "analysis_set_not_comparison", "multi_awr_set does not require target_a"),
        "multi_awr_set must produce selected-scope analysis set truth, not implicit comparison truth.",
    )
    assert_contains_any(
        source,
        ("two or more targets", "n_way", "n-way", "multi target"),
        "multi_target_comparison must support two or more targets, not only Target A/B.",
    )


def test_screen3_builder_declares_dynamic_projection_by_flow_kind():
    module, source = presenter_source_and_signatures()
    required_builder(module, "build_screen3_diagnostic_snapshot_view_model")

    assert_contains_all(
        source,
        (
            "Screen3DiagnosticSnapshotViewModel",
            "single_awr",
            "historical_multi_snapshot",
            "timeframe",
            "multi_awr_set",
            "comparison",
            "multi_target_comparison",
            "fleet",
            "cohort",
            "unavailable",
        ),
        "Screen 3 builder must not be hard-coded to single-AWR Diagnostic Snapshot.",
    )
    assert_contains_all(
        source,
        ("selected_count", "aggregate_posture", "repeated_drivers", "outlier_members", "delta_drivers"),
        "Screen 3 dynamic projection must expose set, trend, outlier, and comparison posture fields.",
    )


def test_screen4_builder_declares_dynamic_mode_availability_by_scope():
    module, source = presenter_source_and_signatures()
    required_builder(module, "build_screen4_evidence_review_view_model")

    assert_contains_all(
        source,
        (
            "Screen4EvidenceReviewViewModel",
            "historical",
            "comparative",
            "deep_analysis",
            "single_awr",
            "historical_multi_snapshot",
            "multi_awr_set",
            "comparison",
            "multi_target_comparison",
            "fleet",
            "cohort",
            "unavailable",
        ),
        "Screen 4 builder must route Evidence Review modes by selected scope, not hard-code historical-only or Target A/B-only behavior.",
    )
    assert_contains_any(
        source,
        ("deep analysis ready if detail evidence exists", "deep_analysis_detail_evidence", "detail evidence exists"),
        "Screen 4 single-AWR Deep Analysis availability must depend on deterministic detail evidence.",
    )
    assert_contains_any(
        source,
        ("n_way", "n-way", "multi target comparison"),
        "Screen 4 multi-target comparison must not collapse to Target A/B only.",
    )


def test_screen5_builder_declares_dynamic_recommendation_projection_by_scope():
    module, source = presenter_source_and_signatures()
    required_builder(module, "build_screen5_recommendation_action_view_model")

    assert_contains_all(
        source,
        (
            "Screen5RecommendationActionViewModel",
            "recommendation_evidence",
            "single_awr",
            "timeframe",
            "multi_awr_set",
            "comparison",
            "multi_target_comparison",
            "fleet",
            "cohort",
            "unavailable",
        ),
        "Screen 5 builder must project deterministic recommendation evidence by selected scope.",
    )
    assert_not_contains_any(
        source,
        ("llm_recommendation_as_evidence", "llm_created_recommendation", "llm_text_as_recommendation"),
        "LLM text cannot create Screen 5 recommendation evidence.",
    )


def test_screen6_builder_declares_dynamic_learning_governance_projection_by_scope():
    module, source = presenter_source_and_signatures()
    required_builder(module, "build_screen6_learning_governance_view_model")

    assert_contains_all(
        source,
        (
            "Screen6LearningGovernanceViewModel",
            "governance_evidence",
            "single_awr",
            "timeframe",
            "multi_awr_set",
            "comparison",
            "multi_target_comparison",
            "fleet",
            "cohort",
            "runtime_eligibility",
        ),
        "Screen 6 builder must project governed learning/runtime eligibility by selected scope.",
    )
    assert_contains_any(
        source,
        ("governed eligibility", "governance_status", "materialization_gate"),
        "Screen 6 runtime eligibility must come from governed deterministic state.",
    )
    assert_not_contains_any(
        source,
        ("semantic_recall_as_evidence", "memory_as_diagnostic_evidence", "llm_approves_runtime_eligibility"),
        "Memory, semantic recall, or LLM text cannot become diagnostic/recommendation/runtime eligibility evidence.",
    )


def test_presenters_keep_evidence_pack_channels_separate():
    _, source = presenter_source_and_signatures()

    assert_contains_all(
        source,
        EVIDENCE_CHANNELS,
        "Presenter builders must keep selected, set, member, temporal, comparison, recommendation, governance, visual, missing, and unavailable evidence channels separate.",
    )
    assert_contains_any(
        source,
        ("historical context is supporting", "supporting_historical_context_not_selected_truth", "contextual not selected truth"),
        "Supporting historical context must not become selected-scope diagnostic truth.",
    )
    assert_contains_any(
        source,
        ("comparison requires deterministic comparison contract", "deterministic comparison contract", "comparison_contract_required"),
        "Comparison evidence must not render without deterministic comparison authority.",
    )


def test_presenters_route_visuals_through_explicit_visual_contracts_only():
    _, source = presenter_source_and_signatures()

    assert_contains_all(
        source,
        VISUAL_CONTRACTS,
        "Presenter builders must route visuals through explicit product visual contracts.",
    )
    assert_contains_any(
        source,
        ("allowed_visualizations is not product content", "allowed_visualizations_not_product_ui", "allowed_visualizations metadata only"),
        "allowed_visualizations metadata must not become user-facing visual evidence.",
    )
    assert_contains_any(
        source,
        ("chart metadata is not evidence", "chart_metadata_not_evidence", "metadata only is not visual evidence"),
        "Chart metadata alone must not count as rendered evidence.",
    )
    assert_contains_any(
        source,
        ("fake static svg is not evidence", "static svg not evidence", "synthetic_data_allowed"),
        "Fake/static visuals must not count as evidence.",
    )
    assert_contains_any(
        source,
        ("UnavailableVisualState", "missing visual evidence", "unavailable_state"),
        "Missing visual evidence must produce UnavailableVisualState rather than silent omission.",
    )


def test_presenter_builders_return_product_view_models_not_renderer_html():
    module, source = presenter_source_and_signatures()
    expected_models = {
        "build_screen3_diagnostic_snapshot_view_model": "Screen3DiagnosticSnapshotViewModel",
        "build_screen4_evidence_review_view_model": "Screen4EvidenceReviewViewModel",
        "build_screen5_recommendation_action_view_model": "Screen5RecommendationActionViewModel",
        "build_screen6_learning_governance_view_model": "Screen6LearningGovernanceViewModel",
    }

    for builder_name, view_model_name in expected_models.items():
        required_builder(module, builder_name)
        assert view_model_name in source, (
            f"{builder_name} must build {view_model_name}, not HTML fragments or renderer-specific output."
        )
    assert_not_contains_any(
        source,
        ("<section", "<div", "render_screen", "content_html=", "screen3_html", "screen4_html"),
        "Product presenters must produce product view models, not renderer HTML or generated fragment readiness.",
    )


def test_7reset_pb_gate_does_not_use_generated_html_or_renderers_as_truth():
    text = Path(__file__).read_text(encoding="utf-8")

    forbidden_snippets = (
        "read_text(\"awr_" + "dashboard/",
        "Path(\"awr_" + "dashboard/",
        "open(\"awr_" + "dashboard/",
        "src.reporting.dashboard." + "renderers",
        "from src.reporting.dashboard." + "renderers",
        "src.reporting." + "html_dashboard",
        "local" + "Storage.getItem",
        "window.local" + "Storage",
    )
    assert_not_contains_any(
        text,
        forbidden_snippets,
        "7RESET-PB must remain a source-contract presenter gate, not a generated-artifact, renderer, html_dashboard, or browser-state gate.",
    )

