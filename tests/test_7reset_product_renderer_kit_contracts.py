import importlib
import inspect
import os
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import pytest


_RUN_7RESET_RENDERER_KIT = os.environ.get("AWR_RUN_7RESET_RENDERER_KIT") == "1"

pytestmark = pytest.mark.skipif(
    not _RUN_7RESET_RENDERER_KIT,
    reason=(
        "7RESET product renderer kit gate is intentionally opt-in. "
        "Run with AWR_RUN_7RESET_RENDERER_KIT=1."
    ),
)


RENDERER_KIT_MODULE_CANDIDATES = (
    "src.reporting.dashboard.renderers.product_kit",
    "src.reporting.dashboard.renderers.components",
    "src.reporting.dashboard.product_renderer_kit",
    "src.reporting.dashboard.rendering.product_kit",
)

REQUIRED_RENDER_EXPORTS = (
    "render_surface_card",
    "render_sub_card",
    "render_status_pill",
    "render_scope_summary",
    "render_unavailable_state",
    "render_evidence_table",
    "render_mode_tabs",
    "render_domain_lens",
    "render_visual_contract",
    "render_internal_refs_annex",
)

PRIMITIVE_EXPORT_CANDIDATES = {
    "SurfaceCard": ("SurfaceCard", "render_surface_card"),
    "SubCard": ("SubCard", "render_sub_card"),
    "StatusPill": ("StatusPill", "render_status_pill"),
    "ScopeSummaryCard": ("ScopeSummaryCard", "render_scope_summary"),
    "UnavailableStateCard": ("UnavailableStateCard", "render_unavailable_state"),
    "EvidenceTable": ("EvidenceTable", "render_evidence_table"),
    "ModeTabs": ("ModeTabs", "render_mode_tabs"),
    "DomainLens": ("DomainLens", "render_domain_lens"),
    "VisualContainer": ("VisualContainer", "render_visual_contract"),
    "InternalRefsAnnex": ("InternalRefsAnnex", "render_internal_refs_annex"),
}

REQUIRED_STATUS_VALUES = (
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

DOMAIN_LENS_LABELS = (
    "All Domains",
    "CPU",
    "IO",
    "MEMORY",
    "COMMIT",
    "RAC",
    "ADG",
)

FORBIDDEN_OUTPUT_TOKENS = (
    "<pre",
    "{'",
    "'debug'",
    "{ debug:",
    "{ row_id:",
    "[raw, list]",
    "selected-flow-internal",
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


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def import_renderer_kit():
    errors: list[str] = []
    for module_name in RENDERER_KIT_MODULE_CANDIDATES:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            errors.append(f"{module_name}: {exc}")
    pytest.fail(
        "Missing 7RESET product renderer kit layer. Expected one of "
        f"{RENDERER_KIT_MODULE_CANDIDATES}. The kit must render product handoff "
        "bundles through safe primitives, not legacy renderers or generated artifacts. "
        f"Import errors: {errors}"
    )


def module_source(module: Any) -> str:
    path = getattr(module, "__file__", None)
    return Path(path).read_text(encoding="utf-8") if path else ""


def source_for_object(obj: Any) -> str:
    try:
        return inspect.getsource(obj)
    except (OSError, TypeError):
        return ""


def renderer_kit_source_and_module() -> tuple[Any, str]:
    module = import_renderer_kit()
    parts = [module_source(module)]
    for export_name in (*REQUIRED_RENDER_EXPORTS, *PRIMITIVE_EXPORT_CANDIDATES):
        candidate = getattr(module, export_name, None)
        if candidate is not None:
            parts.append(source_for_object(candidate))
    return module, "\n".join(parts)


def lookup_attr(module: Any, names: tuple[str, ...]) -> Any | None:
    for name in names:
        candidate = getattr(module, name, None)
        if candidate is not None:
            return candidate
    return None


def html_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    for method_name in ("render", "to_html", "__html__"):
        method = getattr(value, method_name, None)
        if callable(method):
            rendered = method()
            return rendered if isinstance(rendered, str) else str(rendered)
    return str(value)


def visible_text(html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = (
        text.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#x27;", "'")
    )
    return re.sub(r"\s+", " ", text).strip()


def call_component(module: Any, names: tuple[str, ...], variants: tuple[tuple[tuple[Any, ...], dict[str, Any]], ...]) -> str:
    target = lookup_attr(module, names)
    assert target is not None, f"Renderer kit must expose one of {names}."
    errors: list[str] = []
    for args, kwargs in variants:
        try:
            if inspect.isclass(target):
                return html_text(target(*args, **kwargs))
            return html_text(target(*args, **kwargs))
        except TypeError as exc:
            errors.append(str(exc))
    pytest.fail(f"Renderer kit component {names} did not accept product-safe call shapes: {errors}")


def assert_product_safe_output(html: str, *, allow_internal_refs: bool = False) -> None:
    assert isinstance(html, str), "Renderer-kit primitives must return HTML strings or string-renderable fragments."
    assert "<pre" not in html.lower(), "Product renderer kit must not emit <pre> for product content."
    visible = visible_text(html)
    forbidden = list(FORBIDDEN_OUTPUT_TOKENS)
    if allow_internal_refs:
        forbidden = [
            token
            for token in forbidden
            if token not in {"selected-flow-internal", "evidence-pack-internal"}
        ]
    found = [token for token in forbidden if token in visible or token in html]
    assert not found, f"Renderer-kit output leaked forbidden product content: {found}"
    assert not re.search(r"\{[' ][^}]*[' ]:[^}]*\}", visible), (
        "Renderer-kit output must not expose raw Python dict repr or flattened mapping dumps."
    )


def assert_escaped(html: str, dangerous_text: str) -> None:
    assert dangerous_text not in html, "Renderer kit must HTML-escape product text before output."
    assert "&lt;script&gt;" in html or "&lt;" in html, "Escaped output should preserve safe readable text."


def sample_evidence_row():
    from src.reporting.dashboard.view_models.shared_product_shapes import EvidenceDisplayRow

    return EvidenceDisplayRow(
        label="DB CPU",
        value=91,
        unit="pct",
        interpretation="CPU pressure is above baseline.",
        evidence_ref_label="diagnostic_evidence",
        freshness_status="fresh",
        scope_classification="current_scope",
    )


def sample_unavailable_state():
    from src.reporting.dashboard.view_models.shared_product_shapes import UnavailableVisualState

    return UnavailableVisualState(
        state_id="visual-unavailable",
        reason_code="visual_evidence_missing",
        title="Visual evidence unavailable",
        message="Deterministic visualization_evidence is required before rendering a chart.",
        required_contract="visualization_evidence",
        missing_fields=("visualization_evidence",),
        scope_classification="current_scope",
        prohibited_substitutes=("allowed_visualizations", "generated_html", "fake_static_svg"),
        next_deterministic_step="Provide explicit visual evidence.",
    )


def sample_scope_summary():
    from src.reporting.dashboard.view_models.shared_product_shapes import ProductScopeSummary

    return ProductScopeSummary(
        label="Runtime scope",
        database_label="AWRDB",
        instance_label="inst1",
        snapshot_window_label="100-101",
        flow_kind="single_awr",
        validation_status="valid",
    )


def sample_time_series_visual():
    from src.reporting.dashboard.view_models.visual_contracts import (
        AxisSpec,
        TimeSeriesVisual,
        TimeSeriesVisualSeries,
        VisualDataPoint,
    )

    return TimeSeriesVisual(
        visual_id="cpu-series",
        title="DB CPU Trend",
        x_axis=AxisSpec(label="Snapshot"),
        y_axis=AxisSpec(label="DB CPU", unit="pct"),
        series=(
            TimeSeriesVisualSeries(
                label="DB CPU",
                unit="pct",
                points=(
                    VisualDataPoint(x="100", y=78, unit="pct", evidence_ref_label="cpu-100"),
                    VisualDataPoint(x="101", y=91, unit="pct", evidence_ref_label="cpu-101"),
                ),
                evidence_ref_label="cpu-series-evidence",
            ),
        ),
        provenance=("visualization_evidence",),
    )


def sample_handoff_screen():
    from src.reporting.dashboard.product_handoff import build_dashboard_product_handoff_bundle

    scope = {
        "contract_type": "selected_review_scope_contract",
        "contract_version": "7reset.selected_review_scope.v1",
        "selected_flow_id": "selected-flow-internal",
        "flow_kind": "single_awr",
        "validation_status": "valid",
        "source_of_truth": {"authority": "database_contract"},
        "provenance": {"source_system": "renderer_kit_test_scope"},
        "selected_report": {"report_id": "awr-current", "label": "AWR current"},
        "selected_window": {"window_id": "snap-100-101"},
        "runtime_scope": {"scope_id": "runtime-current", "label": "Runtime scope"},
    }
    evidence_pack = {
        "contract_type": "evidence_pack_contract",
        "contract_version": "7reset.evidence_pack.v1",
        "evidence_pack_id": "evidence-pack-internal",
        "provenance": {"source_system": "renderer_kit_test_evidence"},
        "selected_diagnostic_evidence": {
            "summary": "Selected deterministic diagnosis",
            "rows": ({"row_id": "diag-1", "metric": "DB CPU", "values": {"value": 91}},),
        },
        "missing_evidence": (),
        "unavailable_states": (),
    }
    bundle = build_dashboard_product_handoff_bundle(scope, evidence_pack)
    return bundle.screen_bundles[0]


def test_renderer_kit_module_exists_and_dependency_purity():
    _, source = renderer_kit_source_and_module()
    artifact_dir = "awr_" + "dashboard"

    forbidden_tokens = (
        "src.reporting.html_dashboard",
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
        "Path(" + '"' + artifact_dir,
        "read_text(" + '"' + artifact_dir,
    )
    found = [token for token in forbidden_tokens if token in source]
    assert not found, (
        "Product renderer kit must stay independent from html_dashboard, adapters, scripts, "
        f"DB/network/OCI/browser/cache APIs, and generated artifacts. Found: {found}"
    )


def test_renderer_kit_declares_required_primitive_contracts():
    module, source = renderer_kit_source_and_module()

    missing_exports = [
        export_name
        for export_name in REQUIRED_RENDER_EXPORTS
        if getattr(module, export_name, None) is None
    ]
    assert not missing_exports, f"Renderer kit is missing required render exports: {missing_exports}"

    missing_primitives = [
        primitive
        for primitive, candidates in PRIMITIVE_EXPORT_CANDIDATES.items()
        if lookup_attr(module, candidates) is None
    ]
    assert not missing_primitives, f"Renderer kit is missing primitive contracts: {missing_primitives}"

    required_contract_tokens = (
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
        "escape",
        "data-",
    )
    missing_tokens = [token for token in required_contract_tokens if token not in source]
    assert not missing_tokens, (
        "Renderer kit primitives must declare product-safe component contracts. "
        f"Missing source token(s): {missing_tokens}"
    )


def test_primitive_components_escape_and_avoid_raw_debug_output():
    module = import_renderer_kit()
    dangerous_title = "<script>alert('x')</script>"
    raw_debug_payload = {
        "debug": ["raw", "list"],
        "selected_flow_id": "selected-flow-internal",
        "allowed_visualizations": ("fake",),
    }

    html = call_component(
        module,
        ("render_surface_card", "SurfaceCard"),
        (
            ((dangerous_title, "Safe product summary"), {"status": "ready", "data_attrs": {"product": "surface"}}),
            ((), {"title": dangerous_title, "body": "Safe product summary", "status": "ready"}),
        ),
    )
    assert_escaped(html, dangerous_title)
    assert_product_safe_output(html)
    assert "data-" in html or "class=" in html, "SurfaceCard must expose stable review selectors."

    sub_card_html = call_component(
        module,
        ("render_sub_card", "SubCard"),
        (
            (("Evidence", raw_debug_payload), {"status": "partial"}),
            ((), {"title": "Evidence", "body": raw_debug_payload, "status": "partial"}),
        ),
    )
    assert_product_safe_output(sub_card_html)


def test_forbidden_renderer_output_tokens_are_blocked_from_product_components():
    module = import_renderer_kit()
    poison_text = (
        "selected_flow_id selected-flow-internal evidence_pack_id evidence-pack-internal "
        "allowed_visualizations generated HTML as truth browser/localStorage/cache as authority "
        "LLM-created evidence LLM-created recommendation LLM-created learning/runtime eligibility fake-static-svg"
    )

    html = call_component(
        module,
        ("render_surface_card", "SurfaceCard"),
        (
            (("Poison probe", poison_text), {"status": "blocked"}),
            ((), {"title": "Poison probe", "body": poison_text, "status": "blocked"}),
        ),
    )
    assert_product_safe_output(html)


def test_status_pill_supports_status_and_confidence_states():
    module = import_renderer_kit()

    for status in REQUIRED_STATUS_VALUES:
        html = call_component(
            module,
            ("render_status_pill", "StatusPill"),
            (
                ((status,), {}),
                ((), {"status": status}),
                ((), {"label": status, "tone": status}),
            ),
        )
        visible = visible_text(html).lower()
        assert status in visible or status in html.lower(), f"StatusPill must represent {status!r}."
        assert "class=" in html or "data-status" in html or "data-tone" in html, (
            "StatusPill must not render status/confidence as plain text only."
        )
        assert_product_safe_output(html)

    confidence_html = call_component(
        module,
        ("render_status_pill", "StatusPill"),
        (
            (("high",), {"kind": "confidence"}),
            ((), {"status": "high", "kind": "confidence"}),
        ),
    )
    assert "confidence" in confidence_html.lower() or "data-confidence" in confidence_html.lower(), (
        "Confidence must be visibly encoded as a pill/status component, not plain text only."
    )


def test_evidence_table_accepts_only_shaped_product_evidence_rows():
    module = import_renderer_kit()
    shaped_row = sample_evidence_row()

    html = call_component(
        module,
        ("render_evidence_table", "EvidenceTable"),
        (
            (((shaped_row,),), {}),
            ((), {"rows": (shaped_row,)}),
        ),
    )
    visible = visible_text(html)
    for token in ("DB CPU", "91", "pct", "CPU pressure", "diagnostic_evidence", "fresh"):
        assert token in visible, f"EvidenceTable must render shaped evidence field {token!r}."
    assert_product_safe_output(html)

    generic_mapping = {
        "row_id": "raw-row",
        "debug": ["raw", "list"],
        "selected_flow_id": "selected-flow-internal",
        "unexpected": "raw generic mapping",
    }
    target = lookup_attr(module, ("render_evidence_table", "EvidenceTable"))
    assert target is not None
    try:
        generic_html = html_text(target(rows=(generic_mapping,)))
    except (TypeError, ValueError):
        return
    assert_product_safe_output(generic_html)
    assert "unexpected" not in visible_text(generic_html), (
        "EvidenceTable must not render arbitrary mapping keys without product shaping."
    )


def test_visual_contract_renderer_accepts_only_explicit_product_visual_contracts():
    module = import_renderer_kit()

    visual_html = call_component(
        module,
        ("render_visual_contract", "VisualContainer"),
        (
            ((sample_time_series_visual(),), {}),
            ((), {"visual": sample_time_series_visual()}),
        ),
    )
    assert "DB CPU Trend" in visible_text(visual_html)
    assert_product_safe_output(visual_html)

    unavailable_html = call_component(
        module,
        ("render_visual_contract", "VisualContainer", "render_unavailable_state", "UnavailableStateCard"),
        (
            ((sample_unavailable_state(),), {}),
            ((), {"visual": sample_unavailable_state()}),
            ((), {"state": sample_unavailable_state()}),
        ),
    )
    assert "Visual evidence unavailable" in visible_text(unavailable_html)
    assert_product_safe_output(unavailable_html)

    invalid_visuals = (
        {"allowed_visualizations": ("line", "bar")},
        {"chart_metadata": {"kind": "line", "points": 2}},
        {"svg": "<svg><path /></svg>", "title": "fake/static SVG"},
        {"config": {"mark": "line", "encoding": {"x": "snap"}}},
        "<div class='generated-chart'>generated HTML chart fragment</div>",
    )
    target = lookup_attr(module, ("render_visual_contract", "VisualContainer"))
    assert target is not None
    for invalid_visual in invalid_visuals:
        try:
            invalid_html = html_text(target(invalid_visual))
        except (TypeError, ValueError):
            continue
        assert_product_safe_output(invalid_html)
        assert visible_text(invalid_html), (
            "Invalid or missing visual evidence must render a visible unavailable state, not disappear silently."
        )


def test_screen4_mode_tabs_and_domain_lens_contracts():
    module = import_renderer_kit()
    from src.reporting.dashboard.product_handoff import HandoffOption

    mode_tabs = (
        HandoffOption(label="Historical", value="historical", availability="partial"),
        HandoffOption(label="Comparative", value="comparative", availability="blocked"),
        HandoffOption(label="Deep Analysis", value="deep_analysis", availability="unavailable"),
    )
    tabs_html = call_component(
        module,
        ("render_mode_tabs", "ModeTabs"),
        (
            ((mode_tabs,), {"active_mode": "historical"}),
            ((), {"mode_tabs": mode_tabs, "active_mode": "historical"}),
        ),
    )
    tabs_visible = visible_text(tabs_html)
    for token in ("Historical", "Comparative", "Deep Analysis", "partial", "blocked", "unavailable"):
        assert token in tabs_visible, f"ModeTabs must keep Screen 4 mode/status visible: {token}"
    assert_product_safe_output(tabs_html)

    domain_lenses = tuple(
        HandoffOption(label=label, value=label.lower().replace(" ", "_"), availability="unavailable")
        for label in DOMAIN_LENS_LABELS
    )
    domain_html = call_component(
        module,
        ("render_domain_lens", "DomainLens"),
        (
            ((domain_lenses,), {}),
            ((), {"domain_lenses": domain_lenses}),
            ((), {"lenses": domain_lenses}),
        ),
    )
    domain_visible = visible_text(domain_html)
    for label in DOMAIN_LENS_LABELS:
        assert label in domain_visible, f"DomainLens must keep domain visible even when unavailable: {label}"
    assert "unavailable" in domain_visible.lower(), "Unavailable domains must remain visible."
    assert_product_safe_output(domain_html)

    invalid_lens = HandoffOption(label="dg_transport_lag_trend", value="contractual_raciness", availability="partial")
    target = lookup_attr(module, ("render_domain_lens", "DomainLens"))
    assert target is not None
    try:
        invalid_html = html_text(target(domain_lenses=(invalid_lens,)))
    except (TypeError, ValueError):
        return
    assert "dg_transport_lag_trend" not in visible_text(invalid_html), (
        "DomainLens must use exact domain labels, not trend IDs, point counts, or substring-derived labels."
    )
    assert "contractual_raciness" not in visible_text(invalid_html), (
        "Browser/localStorage or arbitrary values must not create mode/domain truth."
    )


def test_product_screen_handoff_renderer_boundary():
    module = import_renderer_kit()
    screen_handoff = sample_handoff_screen()
    before = asdict(screen_handoff) if is_dataclass(screen_handoff) else repr(screen_handoff)

    html = call_component(
        module,
        ("render_product_screen_handoff",),
        (
            ((screen_handoff,), {}),
            ((), {"screen_handoff": screen_handoff}),
        ),
    )
    after = asdict(screen_handoff) if is_dataclass(screen_handoff) else repr(screen_handoff)

    assert before == after, "render_product_screen_handoff must not mutate the handoff object."
    assert "<html" not in html.lower() and "<body" not in html.lower() and "<!doctype" not in html.lower(), (
        "Renderer kit must not return complete dashboard shell HTML."
    )
    assert "ProductScreenHandoff(" not in html and "Screen3DiagnosticSnapshotViewModel(" not in html, (
        "Renderer kit must not return raw dataclass repr."
    )
    if "selected-flow-internal" in html or "evidence-pack-internal" in html:
        annex_markers = ("internal refs annex", "data-product-internal-refs", "InternalRefsAnnex", "<details")
        assert any(marker in html for marker in annex_markers), (
            "Internal refs may render only in a collapsed/annex area, never first-fold product content."
        )
    assert_product_safe_output(html, allow_internal_refs=True)


def test_renderer_kit_gate_does_not_use_generated_html_or_browser_truth():
    test_source = Path(__file__).read_text(encoding="utf-8")
    artifact_dir = "awr_" + "dashboard"

    violations: list[str] = []
    for line_number, line in enumerate(test_source.splitlines(), start=1):
        stripped = line.strip()
        if artifact_dir in stripped and ("read_text(" in stripped or "Path(" in stripped):
            violations.append(f"line {line_number}: generated artifact read/path")
        if re.match(r"^(from|import)\s+src\.reporting\.html_dashboard", stripped):
            violations.append(f"line {line_number}: html_dashboard import")
        if re.match(
            r"^(from|import)\s+src\.reporting\.dashboard\.renderers\."
            r"(common|screen3_renderer|screen4_renderer|screen5_renderer|screen6_renderer)",
            stripped,
        ):
            violations.append(f"line {line_number}: legacy renderer import")
        if re.search(r"window\.localStorage\.|localStorage\.getItem\(|browser_cache\s*=|generated_html\s*=", stripped):
            violations.append(f"line {line_number}: browser/cache/generated HTML authority")
    assert not violations, (
        "7RESET-RK-T must test the future product renderer kit from source contracts only. "
        "It must not read generated HTML, import legacy renderers/html_dashboard as truth, "
        f"or inspect browser/cache state as authority. Violating pattern(s): {violations}"
    )
