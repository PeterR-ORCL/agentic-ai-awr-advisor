import ast
import json
from pathlib import Path

from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts.evidence_pack_contract import EvidenceDomain
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    ComparisonTargetIdentity,
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)
from src.reporting.dashboard.view_models import screen3_diagnostic_view_model as module
from src.reporting.dashboard.view_models.screen3_diagnostic_view_model import (
    build_screen3_diagnostic_view_model,
)


def provenance():
    return SelectionProvenance(source_system="screen2_backend_contract_builder")


def runtime_scope():
    return RuntimeScopeIdentity(scope_id="runtime-1", alignment_key="db-prod")


def target(name):
    return ComparisonTargetIdentity(target_id=name, alignment_key="db-prod")


def selected_scope():
    return build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope=runtime_scope(),
        target_a=target("target-a"),
        target_b=target("target-b"),
        provenance=provenance(),
    )


def diagnostic_payload():
    return {
        "evidence_ids": ["diagnostic-evidence"],
        "rows": [{"row_id": "diagnostic-row", "metric": "db_cpu", "value": 42}],
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
        "rows": [{"row_id": "comparative-row", "metric": "delta", "value": 17}],
        "metrics": {"target_a_vs_target_b_delta": 17},
        "summary": "Comparative evidence",
    }


def model_for_pack(**payloads):
    pack = build_evidence_pack_contract(selected_scope(), provenance="deterministic_builder", **payloads)
    return build_screen3_diagnostic_view_model(pack)


def test_screen3_view_model_does_not_mutate_evidence_pack():
    pack = build_evidence_pack_contract(
        selected_scope(),
        diagnostic_payload=diagnostic_payload(),
        provenance="deterministic_builder",
    )
    before = pack.to_dict()

    build_screen3_diagnostic_view_model(pack)

    assert pack.to_dict() == before


def test_screen3_view_model_builds_from_valid_diagnostic_evidence():
    model = model_for_pack(diagnostic_payload=diagnostic_payload())

    assert model.screen_id == "screen3_diagnostic_snapshot"
    assert model.availability_status == "present"
    assert model.selected_flow_id
    assert model.evidence_pack_id
    assert model.evidence_rows[0]["domain"] == EvidenceDomain.DIAGNOSTIC.value
    assert model.metric_summaries[0]["domain"] == EvidenceDomain.DIAGNOSTIC.value
    assert model.trend_summaries[0]["domain"] == EvidenceDomain.DIAGNOSTIC.value
    assert model.anomaly_summaries[0]["domain"] == EvidenceDomain.DIAGNOSTIC.value
    assert model.similarity_context[0]["domain"] == EvidenceDomain.DIAGNOSTIC.value


def test_screen3_view_model_exposes_missing_unavailable_and_stale_diagnostic_evidence():
    missing = model_for_pack()
    invalid_scope = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=target("target-a"),
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
            "rows": [{"row_id": "diagnostic-row", "metric": "db_cpu", "value": 42}],
            "stale": True,
        }
    )

    assert missing.availability_status == "missing"
    assert missing.missing_evidence
    assert unavailable.availability_status == "unavailable"
    assert unavailable.unavailable_evidence
    assert stale.availability_status == "stale"
    assert stale.stale_evidence


def test_screen3_view_model_includes_provenance_and_diagnostic_llm_eligibility_only():
    model = model_for_pack(diagnostic_payload=diagnostic_payload(), comparative_payload=comparative_payload())

    assert model.provenance["source_system"] == "deterministic_builder"
    assert model.evidence_provenance["source_system"] == "deterministic_builder"
    assert len(model.llm_explanation_eligibility) == 1
    assert model.llm_explanation_eligibility[0]["domain"] == EvidenceDomain.DIAGNOSTIC.value


def test_screen3_view_model_excludes_comparative_evidence_and_target_deltas():
    model = model_for_pack(diagnostic_payload=diagnostic_payload(), comparative_payload=comparative_payload())
    text = json.dumps(model.to_dict(), sort_keys=True)

    assert "comparative-evidence" not in text
    assert "comparative-row" not in text
    assert "target_a_vs_target_b_delta" not in text
    assert "comparison_delta" not in text
    assert "ranking" not in text


def test_screen3_view_model_import_purity_and_no_rendered_html():
    source = Path(module.__file__).read_text()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    forbidden = ("html_dashboard", "renderer", "llm", "awr_dashboard", "browser", "comparison_execution", "screen4")
    assert not any(fragment in name.lower() for name in imports for fragment in forbidden)
    model = model_for_pack(diagnostic_payload=diagnostic_payload())
    assert "<html" not in json.dumps(model.to_dict()).lower()
