import importlib
import inspect
import os
import re
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest


_RUN_7RESET_HANDOFF = os.environ.get("AWR_RUN_7RESET_HANDOFF") == "1"

pytestmark = pytest.mark.skipif(
    not _RUN_7RESET_HANDOFF,
    reason=(
        "7RESET product handoff bundle gate is intentionally opt-in. "
        "Run with AWR_RUN_7RESET_HANDOFF=1."
    ),
)


HANDOFF_MODULE_CANDIDATES = (
    "src.reporting.dashboard.product_handoff",
    "src.reporting.dashboard.handoff",
    "src.reporting.dashboard.view_models.handoff_bundle",
    "src.reporting.dashboard.product_handoff_bundle",
)

HANDOFF_ENTRYPOINTS = (
    "build_dashboard_product_handoff_bundle",
    "build_product_handoff_bundle",
    "DashboardProductHandoffBundle",
    "ProductScreenHandoffBundle",
    "ProductScreenHandoff",
)

SCREEN_BUILDER_NAMES = (
    "build_screen3_diagnostic_snapshot_view_model",
    "build_screen4_evidence_review_view_model",
    "build_screen5_recommendation_action_view_model",
    "build_screen6_learning_governance_view_model",
)

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
    "unavailable",
)

SCREEN_ROLES = {
    "screen3_diagnostic_snapshot": ("3", "Diagnostic Snapshot"),
    "screen4_evidence_review": ("4", "Evidence Review"),
    "screen5_recommendation_action": ("5", "Recommendation Action"),
    "screen6_learning_governance": ("6", "Learning Governance"),
}

VISUAL_CONTRACT_NAMES = (
    "TimeSeriesVisual",
    "DistributionVisual",
    "ViolinVisual",
    "ComparisonDeltaVisual",
    "UnavailableVisualState",
)

FORBIDDEN_CONTENT_POLICY_TOKENS = (
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


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (project_root() / relative_path).read_text(encoding="utf-8")


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def import_handoff_module():
    errors: list[str] = []
    for module_name in HANDOFF_MODULE_CANDIDATES:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            errors.append(f"{module_name}: {exc}")
    pytest.fail(
        "Missing 7RESET renderer-neutral product handoff bundle layer. "
        "A handoff module must package presenter view models for future product renderers "
        "without importing renderers, html_dashboard, generated artifacts, browser state, or LLM/DB/network services. "
        f"Candidates: {HANDOFF_MODULE_CANDIDATES}. Import errors: {errors}"
    )


def module_source(module: Any) -> str:
    path = getattr(module, "__file__", None)
    return Path(path).read_text(encoding="utf-8") if path else ""


def source_for_object(obj: Any) -> str:
    try:
        return inspect.getsource(obj)
    except (OSError, TypeError):
        return ""


def handoff_source_and_public_objects() -> tuple[Any, str]:
    module = import_handoff_module()
    parts = [module_source(module)]
    for name in HANDOFF_ENTRYPOINTS:
        candidate = getattr(module, name, None)
        if candidate is not None:
            parts.append(source_for_object(candidate))
            try:
                parts.append(str(inspect.signature(candidate)))
            except (TypeError, ValueError):
                pass
    return module, "\n".join(parts)


def lookup_attr(module: Any, names: tuple[str, ...]) -> Any | None:
    for name in names:
        candidate = getattr(module, name, None)
        if candidate is not None:
            return candidate
    return None


def get_annotations_or_schema(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    annotations = getattr(obj, "__annotations__", None)
    if annotations:
        return dict(annotations)
    if is_dataclass(obj):
        return {field.name: field.type for field in fields(obj)}
    if isinstance(obj, dict):
        schema = obj.get("fields") or obj.get("properties") or obj.get("schema") or obj
        if isinstance(schema, dict):
            return schema
    return {}


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


def assert_required_fields(contract_name: str, annotations_or_schema: dict[str, Any], fields_: tuple[str, ...]) -> None:
    missing = [field_name for field_name in fields_ if field_name not in annotations_or_schema]
    assert not missing, (
        f"{contract_name} must expose renderer-neutral product handoff fields. Missing: {missing}"
    )


def deterministic_scope(flow_kind: str, **overrides: Any) -> dict[str, Any]:
    scope = {
        "contract_type": "selected_review_scope_contract",
        "contract_version": "7reset.selected_review_scope.v1",
        "selected_flow_id": f"handoff-selected-flow-{flow_kind}",
        "flow_kind": flow_kind,
        "validation_status": "valid",
        "source_of_truth": {"authority": "database_contract"},
        "provenance": {"source_system": "handoff_scope_fixture"},
        "selected_report": {"report_id": "awr-current", "label": "AWR current"},
        "selected_window": {"window_id": "snap-100-101"},
        "runtime_scope": {"scope_id": "runtime-current", "label": "Runtime scope"},
    }
    scope.update(overrides)
    return scope


def deterministic_evidence_pack(**channels: Any) -> dict[str, Any]:
    pack = {
        "contract_type": "evidence_pack_contract",
        "contract_version": "7reset.evidence_pack.v1",
        "evidence_pack_id": "handoff-evidence-pack",
        "provenance": {"source_system": "handoff_evidence_fixture"},
        "selected_diagnostic_evidence": {
            "summary": "Selected deterministic diagnosis",
            "rows": ({"row_id": "diag-1", "metric": "DB CPU", "values": {"value": 91}},),
        },
        "missing_evidence": (),
        "unavailable_states": (),
    }
    pack.update(channels)
    return pack


def all_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return " ".join(all_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(all_text(item) for item in value)
    if is_dataclass(value):
        return " ".join(all_text(getattr(value, field.name)) for field in fields(value))
    return str(value)


def product_handoff_builder(module: Any):
    builder = lookup_attr(
        module,
        ("build_dashboard_product_handoff_bundle", "build_product_handoff_bundle"),
    )
    assert callable(builder), (
        "Product handoff module must expose build_dashboard_product_handoff_bundle "
        "or build_product_handoff_bundle so renderers consume presenter view models, not source contracts directly."
    )
    return builder


def screen_bundles_from(bundle: Any) -> tuple[Any, ...]:
    screen_bundles = getattr(bundle, "screen_bundles", None)
    if screen_bundles is None and isinstance(bundle, dict):
        screen_bundles = bundle.get("screen_bundles")
    assert screen_bundles is not None, "DashboardProductHandoffBundle must expose screen_bundles."
    if isinstance(screen_bundles, dict):
        return tuple(screen_bundles.values())
    return tuple(screen_bundles)


def view_model_from(screen_handoff: Any) -> Any:
    if isinstance(screen_handoff, dict):
        return screen_handoff.get("view_model")
    return getattr(screen_handoff, "view_model", None)


def field_value(obj: Any, field_name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(field_name)
    return getattr(obj, field_name, None)


def test_handoff_module_exists_and_dependency_purity():
    module, source = handoff_source_and_public_objects()

    assert any(getattr(module, name, None) is not None for name in HANDOFF_ENTRYPOINTS), (
        "Handoff module must expose a dashboard bundle builder or product handoff bundle classes."
    )
    assert_not_contains_any(
        source,
        (
            "src.reporting.html_dashboard",
            "src.reporting.dashboard.renderers",
            "src.reporting.dashboard.adapters",
            "scripts.run_analysis",
            "run_analysis(",
            "oci.generative_ai",
            "oci.genai",
            "requests.",
            "httpx",
            "urllib.request",
            "oracledb",
            "cx_Oracle",
            "subprocess",
            "window.localStorage",
            "localStorage.getItem",
            "browser_cache",
            "awr_dashboard/",
        ),
        "Product handoff bundle must stay renderer-, artifact-, browser/cache-, DB/network-, OCI-, and script-independent.",
    )
    assert_contains_any(
        source,
        ("src.reporting.dashboard.presenters", "build_screen3_diagnostic_snapshot_view_model"),
        "Handoff layer should consume deterministic product presenters or their product-safe view models.",
    )


def test_dashboard_handoff_bundle_declares_renderer_neutral_shape_and_guardrails():
    module, source = handoff_source_and_public_objects()
    bundle_obj = lookup_attr(module, ("DashboardProductHandoffBundle", "PRODUCT_HANDOFF_BUNDLE_SCHEMA"))
    schema = get_annotations_or_schema(bundle_obj)

    assert_required_fields(
        "DashboardProductHandoffBundle",
        schema,
        (
            "contract_type",
            "contract_version",
            "selected_scope_ref",
            "evidence_pack_ref",
            "source_of_truth",
            "freshness",
            "provenance",
            "screen_bundles",
            "unavailable_states",
            "internal_refs",
        ),
    )
    assert_contains_all(
        source,
        (
            "dashboard_product_handoff_bundle",
            "generated HTML is not source truth",
            "browser/localStorage/cache is not source truth",
            "LLM explanation is not evidence",
            "renderers consume this bundle but do not create truth",
            "internal refs are not first-fold product content",
        ),
        "Dashboard handoff bundle must declare source-of-truth and renderer-consumption guardrails.",
    )


def test_product_screen_handoff_declares_screen_shape_roles_and_payload_policy():
    module, source = handoff_source_and_public_objects()
    screen_obj = lookup_attr(module, ("ProductScreenHandoff", "ProductScreenHandoffBundle", "PRODUCT_SCREEN_HANDOFF_SCHEMA"))
    schema = get_annotations_or_schema(screen_obj)

    assert_required_fields(
        "ProductScreenHandoff",
        schema,
        (
            "screen_id",
            "screen_number",
            "screen_role",
            "selected_scope_summary",
            "flow_kind",
            "view_model",
            "render_policy",
            "component_contracts",
            "visual_contracts",
            "unavailable_states",
            "interaction_contract",
            "forbidden_content_policy",
            "provenance",
            "internal_refs",
        ),
    )
    for screen_id, (screen_number, screen_role) in SCREEN_ROLES.items():
        assert_contains_all(
            source,
            (screen_id, screen_number, screen_role),
            f"Screen handoff must preserve Screen {screen_number} role and product-visible identity.",
        )
    assert_contains_all(
        source,
        ("raw dict/list/pre", "debug objects", "not screen view model payloads"),
        "Screen handoff must reject raw dict/list/preformatted debug objects as product view-model payloads.",
    )


def test_handoff_builder_consumes_presenters_not_renderers_and_returns_no_html():
    _, source = handoff_source_and_public_objects()

    assert_contains_all(
        source,
        SCREEN_BUILDER_NAMES,
        "Handoff builder must consume Screen 3/4/5/6 presenter outputs.",
    )
    assert_not_contains_any(
        source,
        (
            "render_screen3",
            "render_screen4",
            "render_screen5",
            "render_screen6",
            "render_dashboard",
            "render_html",
            "content_html",
            "<section",
            "<div",
        ),
        "Handoff builder must not call renderers or return HTML strings.",
    )


def test_handoff_preserves_dynamic_selected_scope_flow_kinds_and_boundaries():
    _, source = handoff_source_and_public_objects()

    assert_contains_all(
        source,
        FLOW_KINDS,
        "Handoff bundle must preserve Screen 2 deterministic selected flow kind through Screens 3/4/5/6.",
    )
    assert_contains_all(
        source,
        (
            "multi_awr_set remains distinct from comparison",
            "multi_awr_set does not require Target A/B",
            "comparison requires deterministic comparison evidence",
            "resolved targets",
            "multi_target_comparison supports 2+ targets",
            "unavailable states, not fabricated content",
        ),
        "Handoff flow policy must preserve multi-AWR, comparison, and unsupported-mode boundaries.",
    )


def test_screen4_handoff_declares_dynamic_interaction_contract():
    _, source = handoff_source_and_public_objects()

    assert_contains_all(
        source,
        (
            "mode_tabs",
            "active_mode",
            "domain_lenses",
            "subsection_options",
            "mode_availability",
            "visual_availability",
            "unavailable_states",
            "All Domains",
            "CPU",
            "IO",
            "MEMORY",
            "COMMIT",
            "RAC",
            "ADG",
        ),
        "Screen 4 handoff must expose renderer-neutral dynamic interaction metadata.",
    )
    assert_contains_all(
        source,
        (
            "derived from Screen4EvidenceReviewViewModel",
            "evidence availability",
            "browser/localStorage cannot create domain/subsection truth",
            "unavailable domains/modes must remain visible",
            "allowed_visualizations must not appear",
            "trend IDs and point counts are not subsection labels",
        ),
        "Screen 4 interaction contract must remain deterministic and must not hide unavailable modes/domains.",
    )


def test_visual_handoff_policy_allows_only_explicit_visual_contracts():
    _, source = handoff_source_and_public_objects()

    assert_contains_all(
        source,
        VISUAL_CONTRACT_NAMES,
        "Handoff visual policy must pass only explicit product visual contracts.",
    )
    assert_contains_all(
        source,
        (
            "allowed_visualizations is not product UI",
            "chart metadata is not visual evidence",
            "fake/static SVG is not evidence",
            "generated HTML chart fragments are prohibited",
            "raw JSON visual configs are prohibited",
            "missing visual evidence must be represented as UnavailableVisualState",
        ),
        "Visual handoff policy must reject metadata-only, fake, generated, or raw config visuals.",
    )


def test_forbidden_content_policy_covers_product_poison_rules():
    _, source = handoff_source_and_public_objects()

    assert_contains_all(
        source,
        FORBIDDEN_CONTENT_POLICY_TOKENS,
        "Handoff bundle and each screen handoff must carry a forbidden-content policy for product renderer recut.",
    )


def test_source_of_truth_policy_rejects_browser_cache_and_generated_html_authority():
    _, source = handoff_source_and_public_objects()

    assert_contains_all(
        source,
        (
            "source_of_truth",
            "deterministic",
            "persisted",
            "contract-backed",
            "browser/cache/generated_html cannot create selected truth",
            "LLM cannot create evidence",
        ),
        "Handoff source-of-truth policy must keep browser/cache/generated HTML and LLM text non-authoritative.",
    )


def test_runtime_fixture_handoff_builder_returns_four_product_screen_bundles():
    module = import_handoff_module()
    builder = product_handoff_builder(module)
    scope = deterministic_scope("single_awr")
    evidence_pack = deterministic_evidence_pack(
        deep_analysis_evidence={
            "summary": "Deep detail evidence exists",
            "rows": ({"row_id": "deep-1", "metric": "SQL detail", "values": {"value": "ready"}},),
        }
    )

    bundle = builder(scope, evidence_pack)
    bundles = screen_bundles_from(bundle)

    assert field_value(bundle, "contract_type") == "dashboard_product_handoff_bundle"
    assert len(bundles) == 4, "Handoff bundle must include exactly four screen handoffs for Screens 3/4/5/6."
    screen_ids = {field_value(screen_handoff, "screen_id") for screen_handoff in bundles}
    assert set(SCREEN_ROLES) == screen_ids

    for screen_handoff in bundles:
        view_model = view_model_from(screen_handoff)
        assert view_model is not None, "Each screen handoff must carry its product view model."
        assert not isinstance(view_model, str), "Screen handoff view_model must not be HTML or renderer output."
        assert "<" not in all_text(view_model), "Screen handoff must not contain HTML fragments."
        assert field_value(screen_handoff, "flow_kind") == "single_awr"
        assert field_value(screen_handoff, "internal_refs") is not None

    assert "browser" not in normalize(all_text(field_value(bundle, "source_of_truth")))
    assert "cache" not in normalize(all_text(field_value(bundle, "source_of_truth")))
    assert "generated html" not in normalize(all_text(field_value(bundle, "source_of_truth")))


def test_handoff_keeps_internal_refs_out_of_first_fold_product_fields():
    module = import_handoff_module()
    builder = product_handoff_builder(module)
    bundle = builder(deterministic_scope("single_awr"), deterministic_evidence_pack())

    for screen_handoff in screen_bundles_from(bundle):
        view_model = view_model_from(screen_handoff)
        first_fold = getattr(view_model, "first_fold", None)
        first_fold_text = all_text(first_fold)
        assert "handoff-selected-flow-" not in first_fold_text, (
            "selected_flow_id must remain internal and must not appear in first-fold product content."
        )
        assert "handoff-evidence-pack" not in first_fold_text, (
            "evidence_pack_id must remain internal and must not appear in first-fold product content."
        )


def test_7reset_ph_contract_gate_does_not_use_generated_html_or_renderers_as_truth():
    test_source = Path(__file__).read_text(encoding="utf-8")

    forbidden_patterns = (
        r"read_text\([^)]*awr_dashboard",
        r"Path\([^)]*awr_dashboard",
        r"^\s*(from|import)\s+src\.reporting\.html_dashboard",
        r"^\s*(from|import)\s+src\.reporting\.dashboard\.renderers",
        r"window\.localStorage\.",
        r"localStorage\.getItem\(",
        r"browser_cache\s*=",
        r"generated_html\s*=",
    )
    violations = [
        pattern
        for pattern in forbidden_patterns
        if re.search(pattern, test_source, flags=re.MULTILINE)
    ]
    assert not violations, (
        "7RESET-PH must remain a source-contract handoff gate: it must not read generated HTML, "
        "import renderers/html_dashboard, or inspect browser/cache state as authority. "
        f"Violating pattern(s): {violations}"
    )
