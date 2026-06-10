import ast
from pathlib import Path

from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    ComparisonTargetIdentity,
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)
from src.reporting.dashboard.renderers import screen3_renderer as module
from src.reporting.dashboard.renderers.screen3_renderer import render_screen3_diagnostic
from src.reporting.dashboard.view_models.screen3_diagnostic_view_model import (
    build_screen3_diagnostic_view_model,
)


def provenance():
    return SelectionProvenance(source_system="screen2_backend_contract_builder")


def selected_scope():
    return build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope=RuntimeScopeIdentity(scope_id="runtime-1", alignment_key="db-prod"),
        target_a=ComparisonTargetIdentity(target_id="target-a", alignment_key="db-prod"),
        target_b=ComparisonTargetIdentity(target_id="target-b", alignment_key="db-prod"),
        provenance=provenance(),
    )


def diagnostic_payload():
    return {
        "evidence_ids": ["diagnostic-evidence"],
        "rows": [{"row_id": "diagnostic-row", "metric": "db_cpu", "value": "<script>alert(1)</script>"}],
        "metrics": {"db_cpu_score": 91},
        "trends": [{"trend_name": "diagnostic-trend", "direction": "up"}],
        "anomalies": [{"anomaly_name": "diagnostic-anomaly", "severity": "warning"}],
        "similarity_context": [{"context_id": "diagnostic-similarity", "similar_case_ids": ["case-1"]}],
        "confidence_basis": [{"basis_id": "diagnostic-confidence", "confidence": "high"}],
        "summary": "Diagnostic evidence",
    }


def comparative_payload():
    return {
        "evidence_ids": ["comparative-evidence"],
        "rows": [{"row_id": "comparative-row", "metric": "target_a_vs_target_b_delta", "value": 17}],
        "metrics": {"target_a_vs_target_b_delta": 17},
        "summary": "Comparative evidence",
    }


def model_for_pack(**payloads):
    pack = build_evidence_pack_contract(selected_scope(), provenance="deterministic_builder", **payloads)
    return build_screen3_diagnostic_view_model(pack)


def test_screen3_renderer_renders_diagnostic_summary_and_evidence_only():
    html = render_screen3_diagnostic(model_for_pack(diagnostic_payload=diagnostic_payload()))

    assert 'data-screen="screen3_diagnostic_snapshot"' in html
    assert "Diagnostic Snapshot" in html
    assert "diagnostic-row" in html
    assert "db_cpu_score" in html
    assert "diagnostic-trend" in html
    assert "deterministic_builder" in html
    assert "<script" not in html.lower()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_screen3_renderer_renders_missing_unavailable_and_stale_states():
    missing_html = render_screen3_diagnostic(model_for_pack())
    invalid_scope = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=ComparisonTargetIdentity(target_id="target-a", alignment_key="db-prod"),
        provenance=provenance(),
    )
    unavailable = build_screen3_diagnostic_view_model(
        build_evidence_pack_contract(
            invalid_scope,
            diagnostic_payload=diagnostic_payload(),
            provenance="deterministic_builder",
        )
    )
    stale = model_for_pack(
        diagnostic_payload={
            "evidence_ids": ["diagnostic-evidence"],
            "rows": [{"row_id": "diagnostic-row", "metric": "db_cpu"}],
            "stale": True,
        }
    )

    assert "Missing evidence" in missing_html
    assert "payload_missing" in missing_html
    assert "Unavailable evidence" in render_screen3_diagnostic(unavailable)
    assert "selected_scope_invalid" in render_screen3_diagnostic(unavailable)
    assert "Stale evidence" in render_screen3_diagnostic(stale)
    assert "payload_stale" in render_screen3_diagnostic(stale)


def test_screen3_renderer_excludes_comparative_output_and_readiness():
    html = render_screen3_diagnostic(
        model_for_pack(diagnostic_payload=diagnostic_payload(), comparative_payload=comparative_payload())
    )

    assert "comparative-row" not in html
    assert "target_a_vs_target_b_delta" not in html
    assert "comparison_delta" not in html
    assert "Comparative Review" not in html
    assert "comparison readiness" not in html.lower()


def test_screen3_renderer_import_boundary():
    imports = _imports_for(module)
    forbidden = (
        "html_dashboard",
        "evidence_pack_builder",
        "selected_review_scope_contract",
        "evidence_pack_contract",
        "llm",
        "awr_dashboard",
        "browser",
        "comparison_execution",
        "screen4",
    )
    assert not any(fragment in name.lower() for name in imports for fragment in forbidden)


def _imports_for(imported_module):
    tree = ast.parse(Path(imported_module.__file__).read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return imports
