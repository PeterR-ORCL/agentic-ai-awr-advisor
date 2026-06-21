import importlib
import inspect
import os
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest


_RUN_7RESET_SCREEN3_RENDERER = os.environ.get("AWR_RUN_7RESET_SCREEN3_RENDERER") == "1"

pytestmark = pytest.mark.skipif(
    not _RUN_7RESET_SCREEN3_RENDERER,
    reason=(
        "7RESET Screen 3 product renderer gate is intentionally opt-in. "
        "Run with AWR_RUN_7RESET_SCREEN3_RENDERER=1."
    ),
)


SCREEN3_RENDERER_MODULE_CANDIDATES = (
    "src.reporting.dashboard.renderers.screen3_product",
    "src.reporting.dashboard.renderers.screen3_diagnostic_snapshot",
    "src.reporting.dashboard.renderers.screen3_diagnostic_snapshot_product",
    "src.reporting.dashboard.screen_renderers.screen3_diagnostic_snapshot",
)

SCREEN3_RENDER_EXPORTS = (
    "render_screen3_diagnostic_snapshot",
    "render_screen3_product_handoff",
)

REQUIRED_KIT_PRIMITIVES = (
    "render_surface_card",
    "render_sub_card",
    "render_status_pill",
    "render_scope_summary",
    "render_unavailable_state",
    "render_evidence_table",
    "render_visual_contract",
    "render_internal_refs_annex",
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

PRODUCT_MARKERS = (
    "product-screen3-diagnostic-snapshot",
    "product-scope-summary",
    "product-diagnostic-first-fold",
    "product-diagnostic-driver",
    "product-evidence-table",
    "product-unavailable-state",
    "product-internal-refs-annex",
)

LOCAL_STORAGE_TEXT = "local" + "Storage"
CACHE_TEXT = "cache"
HTML_TEXT = "HT" + "ML"
ARTIFACT_DIR = "awr_" + "dashboard"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def import_screen3_renderer():
    errors: list[str] = []
    for module_name in SCREEN3_RENDERER_MODULE_CANDIDATES:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            errors.append(f"{module_name}: {exc}")
    pytest.fail(
        "Missing 7RESET Screen 3 product renderer layer. Expected one of "
        f"{SCREEN3_RENDERER_MODULE_CANDIDATES}. The renderer must consume "
        "ProductScreenHandoff for screen3_diagnostic_snapshot and render through "
        f"product_kit primitives. Import errors: {errors}"
    )


def module_source(module: Any) -> str:
    path = getattr(module, "__file__", None)
    return Path(path).read_text(encoding="utf-8") if path else ""


def source_for_object(obj: Any) -> str:
    try:
        return inspect.getsource(obj)
    except (OSError, TypeError):
        return ""


def screen3_renderer_source_and_module() -> tuple[Any, str]:
    module = import_screen3_renderer()
    parts = [module_source(module)]
    for export_name in SCREEN3_RENDER_EXPORTS:
        candidate = getattr(module, export_name, None)
        if candidate is not None:
            parts.append(source_for_object(candidate))
            try:
                parts.append(str(inspect.signature(candidate)))
            except (TypeError, ValueError):
                pass
    return module, "\n".join(parts)


def renderer_entrypoint(module: Any):
    for export_name in SCREEN3_RENDER_EXPORTS:
        candidate = getattr(module, export_name, None)
        if callable(candidate):
            return candidate
    pytest.fail(
        "Screen 3 product renderer must expose render_screen3_diagnostic_snapshot "
        "or render_screen3_product_handoff."
    )


def render_screen3(module: Any, handoff: Any) -> str:
    target = renderer_entrypoint(module)
    result = target(handoff)
    if isinstance(result, str):
        return result
    for method_name in ("render", "to_html", "__html__"):
        method = getattr(result, method_name, None)
        if callable(method):
            rendered = method()
            return rendered if isinstance(rendered, str) else str(rendered)
    return str(result)


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


def first_fold_html(html: str) -> str:
    for marker in ('class="product-internal-refs-annex"', "<details"):
        if marker in html:
            return html.split(marker, 1)[0]
    return html


def first_fold_text(html: str) -> str:
    return visible_text(first_fold_html(html))


def forbidden_output_tokens() -> tuple[str, ...]:
    return (
        "<pre",
        "{'",
        "{ debug:",
        "{ row_id:",
        "[raw, list]",
        "selected_flow_id",
        "selected-flow-internal",
        "evidence_pack_id",
        "evidence-pack-internal",
        "internal-debug-ref",
        "allowed_visualizations",
        "Allowed Visualizations",
        "dg_transport_lag_trend",
        "Point Count",
        "generated " + HTML_TEXT + " as truth",
        "generated_" + HTML_TEXT.lower(),
        "browser/" + LOCAL_STORAGE_TEXT + "/" + CACHE_TEXT,
        LOCAL_STORAGE_TEXT + " creates truth",
        "LLM-created diagnosis",
        "fake-static-svg",
        "<svg",
    )


def assert_product_safe(html: str, *, allow_annex_refs: bool = False) -> None:
    assert isinstance(html, str), "Screen 3 product renderer must return an HTML fragment string."
    assert "<html" not in html.lower() and "<body" not in html.lower(), (
        "Screen 3 product renderer must not return a full dashboard shell."
    )
    assert "<pre" not in html.lower(), "Screen 3 product renderer must not render product content in <pre>."
    text = visible_text(html)
    tokens = list(forbidden_output_tokens())
    if allow_annex_refs:
        tokens = [
            token
            for token in tokens
            if token not in {"selected-flow-internal", "evidence-pack-internal", "internal-debug-ref"}
        ]
    found = [token for token in tokens if token in html or token in text]
    assert not found, f"Screen 3 product renderer leaked forbidden output: {found}"
    assert not re.search(r"\{[' ][^}]*[' ]:[^}]*\}", text), (
        "Screen 3 product renderer must not expose raw Python dict/list repr or mapping dumps."
    )


def assert_rejects_or_blocks(module: Any, payload: Any, blocked_tokens: tuple[str, ...]) -> None:
    try:
        html = render_screen3(module, payload)
    except (TypeError, ValueError, AssertionError):
        return
    text = visible_text(html)
    assert any(token in text.lower() for token in ("unavailable", "blocked", "invalid", "requires")), (
        "Invalid Screen 3 renderer input must be rejected or rendered as a visible blocked/unavailable state."
    )
    found = [token for token in blocked_tokens if token in html or token in text]
    assert not found, f"Invalid input was rendered as product truth: {found}"


def evidence_row(label: str = "DB CPU", value: Any = 91, *, interpretation: str = "CPU pressure is above baseline."):
    from src.reporting.dashboard.view_models.shared_product_shapes import EvidenceDisplayRow

    return EvidenceDisplayRow(
        label=label,
        value=value,
        unit="percent",
        interpretation=interpretation,
        evidence_ref_label="current diagnostic evidence",
        freshness_status="fresh",
        scope_classification="current_scope",
    )


def scope_summary(flow_kind: str, *, label: str | None = None, window: str = "Snapshots 100-101"):
    from src.reporting.dashboard.view_models.shared_product_shapes import ProductScopeSummary

    return ProductScopeSummary(
        label=label or flow_kind.replace("_", " "),
        database_label="AWRDB",
        instance_label="inst1",
        snapshot_window_label=window,
        flow_kind=flow_kind,
        validation_status="valid",
    )


def unavailable_state(reason_code: str = "diagnostic_visual_missing", title: str = "Diagnostic visual unavailable"):
    from src.reporting.dashboard.view_models.shared_product_shapes import UnavailableVisualState

    return UnavailableVisualState(
        state_id=reason_code,
        reason_code=reason_code,
        title=title,
        message="Deterministic current-scope visual evidence is required before rendering this product visual.",
        required_contract="TimeSeriesVisual",
        missing_fields=("visualization_evidence",),
        prohibited_substitutes=("allowed_visualizations", "fake_static_svg", "generated_html"),
        next_deterministic_step="Provide explicit current-scope visual evidence.",
    )


def time_series_visual():
    from src.reporting.dashboard.view_models.visual_contracts import (
        AxisSpec,
        TimeSeriesVisual,
        TimeSeriesVisualSeries,
        VisualDataPoint,
    )

    return TimeSeriesVisual(
        visual_id="current-cpu-series",
        title="Current DB CPU trend",
        x_axis=AxisSpec(label="Snapshot"),
        y_axis=AxisSpec(label="DB CPU", unit="percent"),
        series=(
            TimeSeriesVisualSeries(
                label="DB CPU",
                unit="percent",
                points=(
                    VisualDataPoint(x="100", y=78, unit="percent", evidence_ref_label="cpu-100"),
                    VisualDataPoint(x="101", y=91, unit="percent", evidence_ref_label="cpu-101"),
                ),
                evidence_ref_label="current diagnostic evidence",
            ),
        ),
        provenance=("visualization_evidence",),
    )


def screen3_view_model(
    flow_kind: str = "single_awr",
    *,
    primary_issue: str = "CPU pressure from deterministic evidence",
    status_label: str = "point-in-time diagnostic snapshot",
    top_drivers: tuple[str, ...] = ("DB CPU", "log file sync"),
    missing_summary: str = "No temporal trend evidence for this selected scope.",
    rows: tuple[Any, ...] | None = None,
    visuals: tuple[Any, ...] | None = None,
    explanation_text: str = "This explanation summarizes deterministic CPU evidence.",
):
    from src.reporting.dashboard.view_models.screen3_diagnostic_snapshot import (
        DiagnosticFirstFold,
        Screen3DiagnosticSnapshotViewModel,
    )
    from src.reporting.dashboard.view_models.shared_product_shapes import (
        EvidenceReviewSection,
        ExplanationBlock,
    )

    evidence_rows = rows if rows is not None else (evidence_row(),)
    return Screen3DiagnosticSnapshotViewModel(
        scope_summary=scope_summary(flow_kind),
        first_fold=DiagnosticFirstFold(
            status_label=status_label,
            primary_issue_label=primary_issue,
            severity_score=0.82,
            confidence_score=0.91,
            top_driver_labels=top_drivers,
            missing_evidence_summary=missing_summary,
        ),
        primary_cards=(
            EvidenceReviewSection(
                section_id="current-diagnostic-drivers",
                title="Top diagnostic drivers",
                rows=evidence_rows,
            ),
        ),
        visuals=visuals if visuals is not None else (time_series_visual(),),
        evidence_table=evidence_rows,
        missing_evidence=(missing_summary,),
        llm_explanation=ExplanationBlock(
            eligibility="eligible",
            explanation_text=explanation_text,
            explains_refs=("current diagnostic evidence",),
            prohibited_as_evidence=True,
        ),
        provenance=("deterministic_screen3_presenter",),
        freshness="fresh",
        internal_refs=("selected_flow_id:selected-flow-internal", "evidence_pack_id:evidence-pack-internal"),
    )


def screen3_handoff(
    flow_kind: str = "single_awr",
    *,
    view_model: Any | None = None,
    visual_contracts: tuple[Any, ...] | None = None,
    unavailable_states: tuple[Any, ...] | None = None,
    internal_refs: tuple[str, ...] = (
        "selected_flow_id:selected-flow-internal",
        "evidence_pack_id:evidence-pack-internal",
        "internal-debug-ref",
    ),
):
    from src.reporting.dashboard.product_handoff import ProductScreenHandoff

    vm = view_model if view_model is not None else screen3_view_model(flow_kind)
    return ProductScreenHandoff(
        screen_id="screen3_diagnostic_snapshot",
        screen_number="3",
        screen_role="Diagnostic Snapshot",
        selected_scope_summary=scope_summary(flow_kind),
        flow_kind=flow_kind,
        view_model=vm,
        component_contracts=(
            "product-diagnostic-first-fold",
            "product-diagnostic-driver",
            "product-evidence-table",
        ),
        visual_contracts=visual_contracts if visual_contracts is not None else tuple(getattr(vm, "visuals", ())),
        unavailable_states=unavailable_states or (),
        provenance=("deterministic_product_handoff",),
        internal_refs=internal_refs,
    )


def test_screen3_product_renderer_module_exists_and_dependency_purity():
    _, source = screen3_renderer_source_and_module()
    html_dashboard = "src.reporting.html_" + "dashboard"
    legacy_common = "src.reporting.dashboard.renderers." + "common"
    legacy_screen3 = "src.reporting.dashboard.renderers." + "screen3_" + "renderer"
    artifact_path = ARTIFACT_DIR + "/"

    forbidden_tokens = (
        html_dashboard,
        "src.reporting.dashboard.adapters",
        legacy_common,
        legacy_screen3,
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
        "window." + LOCAL_STORAGE_TEXT,
        LOCAL_STORAGE_TEXT + ".getItem",
        "browser_" + CACHE_TEXT,
        artifact_path,
    )
    found = [token for token in forbidden_tokens if token in source]
    assert not found, (
        "Screen 3 product renderer must be independent from shell, adapters, legacy renderers, "
        f"scripts, DB/network/OCI/browser/cache APIs, and generated artifacts. Found: {found}"
    )
    assert "product_kit" in source, "Screen 3 product renderer must render through product_kit primitives."
    assert "ProductScreenHandoff" in source, "Screen 3 product renderer must consume ProductScreenHandoff."


def test_screen3_product_renderer_exposes_entrypoint_and_uses_required_product_kit_primitives():
    module, source = screen3_renderer_source_and_module()

    assert callable(renderer_entrypoint(module))
    missing = [primitive for primitive in REQUIRED_KIT_PRIMITIVES if primitive not in source]
    assert not missing, (
        "Screen 3 product renderer must depend on the shared product renderer kit primitives. "
        f"Missing primitive references: {missing}"
    )
    forbidden_legacy_helpers = (
        "render_items",
        "render_rows",
        "render_named_collections",
        "_format_value",
    )
    found = [helper for helper in forbidden_legacy_helpers if helper in source]
    assert not found, f"Screen 3 product renderer must not use legacy generic renderer helpers: {found}"


def test_screen3_renderer_accepts_only_screen3_product_handoff_input_contract():
    module, _ = screen3_renderer_source_and_module()
    valid_html = render_screen3(module, screen3_handoff())
    assert "screen3_diagnostic_snapshot" in valid_html or "Diagnostic Snapshot" in visible_text(valid_html)

    raw_view_model = screen3_view_model()
    assert_rejects_or_blocks(module, raw_view_model, ("CPU pressure from deterministic evidence",))
    assert_rejects_or_blocks(module, {"screen_id": "screen3_diagnostic_snapshot", "debug": ["raw", "list"]}, ("debug", "raw"))
    assert_rejects_or_blocks(module, ["raw", "screen3", "payload"], ("raw", "payload"))
    assert_rejects_or_blocks(
        module,
        "<section data-generated='true'>generated " + HTML_TEXT + " fragment</section>",
        ("data-generated", "fragment"),
    )
    assert_rejects_or_blocks(
        module,
        {
            "source": "browser_" + CACHE_TEXT,
            LOCAL_STORAGE_TEXT: {"selected_scope": "created by page continuity"},
        },
        ("created by page continuity",),
    )
    assert_rejects_or_blocks(
        module,
        {"llm_explanation": "LLM-created diagnosis: CPU saturation is truth"},
        ("LLM-created diagnosis", "CPU saturation is truth"),
    )


def test_screen3_renderer_required_first_fold_output_is_product_safe():
    module, _ = screen3_renderer_source_and_module()
    html = render_screen3(module, screen3_handoff())
    fold = first_fold_text(html)

    assert "Runtime scope" in fold or "single awr" in fold.lower()
    assert "single" in fold.lower() and "awr" in fold.lower()
    assert "point-in-time diagnostic snapshot" in fold
    assert "CPU pressure from deterministic evidence" in fold
    assert "DB CPU" in fold and "log file sync" in fold
    assert "No temporal trend evidence" in fold or "unavailable" in fold.lower()
    assert "0.82" in fold or "82" in fold or "critical" in fold.lower() or "warning" in fold.lower()
    assert "0.91" in fold or "91" in fold or "high" in fold.lower()
    assert "product-status-pill" in html and ("confidence" in html.lower() or "data-confidence" in html)
    assert_product_safe(first_fold_html(html))


def test_screen3_renderer_dynamic_flow_kind_states_are_distinct_and_contract_backed():
    module, _ = screen3_renderer_source_and_module()

    for flow_kind in FLOW_KINDS:
        primary_issue = f"{flow_kind.replace('_', ' ')} diagnostic posture"
        rows = (evidence_row(label="Selected AWR count", value=3),) if flow_kind == "multi_awr_set" else None
        unavailable = ()
        visual_contracts = None
        status = "diagnostic snapshot"
        if flow_kind in {"timeframe", "historical_multi_snapshot"}:
            status = "window-level diagnostic posture"
        if flow_kind in {"comparison", "multi_target_comparison"}:
            status = "deterministic comparative posture"
            rows = (evidence_row(label="Target delta", value="Target B higher DB CPU"),)
        if flow_kind in {"predictive_sizing", "comparative_sizing", "unavailable"}:
            unavailable = (unavailable_state("sizing_evidence_missing", "Sizing evidence unavailable"),)
            visual_contracts = ()
            primary_issue = "Sizing diagnostic unavailable"

        vm = screen3_view_model(
            flow_kind,
            primary_issue=primary_issue,
            status_label=status,
            rows=rows,
            visuals=visual_contracts,
        )
        html = render_screen3(
            module,
            screen3_handoff(
                flow_kind,
                view_model=vm,
                visual_contracts=visual_contracts,
                unavailable_states=unavailable,
            ),
        )
        text = visible_text(html)

        assert flow_kind.replace("_", " ") in text.lower() or flow_kind in html
        if flow_kind == "single_awr":
            assert "multi-snapshot analysis" not in text
            assert "24 snapshots were analyzed" not in text
        if flow_kind in {"timeframe", "historical_multi_snapshot"}:
            assert "window-level" in text.lower() or "window" in text.lower()
        if flow_kind == "multi_awr_set":
            assert "selected" in text.lower() and "3" in text
            assert "Target A" not in text and "Target B" not in text
        if flow_kind in {"comparison", "multi_target_comparison"}:
            assert "comparative" in text.lower() or "Target delta" in text
            assert "Target B" in text
        if flow_kind in {"fleet", "cohort"}:
            assert flow_kind in text.lower()
        if flow_kind in {"predictive_sizing", "comparative_sizing", "unavailable"}:
            assert "unavailable" in text.lower() and "sizing" in text.lower()


def test_screen3_renderer_evidence_rows_are_shaped_tables_not_raw_metric_snapshots():
    module, _ = screen3_renderer_source_and_module()
    html = render_screen3(module, screen3_handoff())
    text = visible_text(html)

    assert "product-evidence-table" in html
    for token in ("DB CPU", "91", "percent", "CPU pressure is above baseline.", "current diagnostic evidence", "fresh"):
        assert token in text, f"Screen 3 evidence table must render shaped evidence field: {token}"
    assert_product_safe(html, allow_annex_refs=True)

    toxic_row = evidence_row(value={"debug": ["raw", "list"], "diagnosis": "CPU pressure"})
    toxic_html = render_screen3(module, screen3_handoff(view_model=screen3_view_model(rows=(toxic_row,))))
    toxic_text = visible_text(toxic_html)
    assert "{'debug'" not in toxic_text and "[raw, list]" not in toxic_text


def test_screen3_renderer_visual_contracts_require_time_series_or_unavailable_state():
    module, _ = screen3_renderer_source_and_module()
    html = render_screen3(module, screen3_handoff(visual_contracts=(time_series_visual(),)))
    assert "TimeSeriesVisual" in html or "time-series" in html or "time_series" in html
    assert "<svg" not in html.lower() and "allowed_visualizations" not in html

    missing_visual_html = render_screen3(
        module,
        screen3_handoff(
            view_model=screen3_view_model(visuals=()),
            visual_contracts=(),
            unavailable_states=(unavailable_state(),),
        ),
    )
    missing_text = visible_text(missing_visual_html)
    assert "unavailable" in missing_text.lower() and "visual" in missing_text.lower()

    invalid = replace(screen3_handoff(), visual_contracts=({"visual_kind": "fake-static-svg", "svg": "<svg></svg>"},))
    assert_rejects_or_blocks(module, invalid, ("fake-static-svg", "<svg", "visual_kind"))


def test_screen3_renderer_llm_explanation_is_explanation_only_not_evidence_or_truth():
    module, _ = screen3_renderer_source_and_module()
    vm = screen3_view_model(
        explanation_text="LLM narrative summarizes deterministic CPU evidence; it is prohibited as evidence.",
    )
    html = render_screen3(module, screen3_handoff(view_model=vm))
    text = visible_text(html)

    assert "prohibited as evidence" in text.lower() or "not evidence" in text.lower()
    if "LLM narrative summarizes" in text:
        evidence_section = html.split("LLM narrative summarizes", 1)[0]
        assert "product-evidence-table" in evidence_section, (
            "LLM explanation may be displayed only after deterministic evidence, not as evidence rows."
        )
    assert "LLM-created diagnosis" not in text
    assert "LLM-created recommendation" not in text


def test_screen3_renderer_internal_refs_are_only_visible_in_collapsed_annex():
    module, _ = screen3_renderer_source_and_module()
    html = render_screen3(module, screen3_handoff())
    fold = first_fold_text(html)

    assert "selected-flow-internal" not in fold
    assert "evidence-pack-internal" not in fold
    assert "internal-debug-ref" not in fold
    if "selected-flow-internal" in html or "evidence-pack-internal" in html:
        assert "<details" in html and "product-internal-refs-annex" in html


def test_screen3_renderer_forbidden_output_regression_blocks_debug_and_non_authoritative_truth():
    module, _ = screen3_renderer_source_and_module()
    toxic_vm = screen3_view_model(
        primary_issue="LLM-created diagnosis: scale the database now",
        top_drivers=("dg_transport_lag_trend", "Point Count: 3", "Allowed Visualizations"),
        rows=(
            evidence_row(
                label="selected_flow_id",
                value="selected-flow-internal",
                interpretation="generated " + HTML_TEXT + " as truth",
            ),
        ),
        explanation_text="browser/" + LOCAL_STORAGE_TEXT + "/" + CACHE_TEXT + " creates truth",
    )
    html = render_screen3(module, screen3_handoff(view_model=toxic_vm, visual_contracts=()))
    assert_product_safe(html, allow_annex_refs=True)


def test_screen3_renderer_visual_style_markers_are_stable_for_product_review():
    module, _ = screen3_renderer_source_and_module()
    html = render_screen3(
        module,
        screen3_handoff(
            view_model=screen3_view_model(visuals=()),
            visual_contracts=(),
            unavailable_states=(unavailable_state(),),
        ),
    )

    missing = [marker for marker in PRODUCT_MARKERS if marker not in html]
    assert not missing, (
        "Screen 3 product renderer must expose stable product CSS/data markers compatible "
        f"with the approved dashboard visual grammar. Missing: {missing}"
    )


def test_screen3_renderer_gate_meta_does_not_use_generated_artifacts_or_legacy_truth_sources():
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden_source_tokens = (
        ARTIFACT_DIR + "/",
        "Path(" + repr(ARTIFACT_DIR),
        "read_text(" + repr(ARTIFACT_DIR),
        "src.reporting.html_" + "dashboard",
        "from src.reporting.dashboard.renderers." + "screen3_" + "renderer",
        "import src.reporting.dashboard.renderers." + "screen3_" + "renderer",
        LOCAL_STORAGE_TEXT + ".getItem",
        "browser_" + CACHE_TEXT + "_authority",
        "generated " + HTML_TEXT + " as source truth",
    )
    found = [token for token in forbidden_source_tokens if token in source]
    assert not found, (
        "This Screen 3 renderer contract gate must not inspect generated artifacts, import "
        f"legacy renderers or html_dashboard as truth, or use browser/cache state as authority. Found: {found}"
    )
