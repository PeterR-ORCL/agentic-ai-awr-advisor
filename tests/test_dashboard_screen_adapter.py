import ast
import copy
from pathlib import Path

import pytest

import src.reporting.dashboard.adapters.dashboard_screen_adapter as adapter_module
from src.reporting.dashboard.adapters.dashboard_screen_adapter import (
    DashboardScreenRenderBundle,
    build_dashboard_screen_render_bundle,
)
from src.reporting.dashboard.contracts.evidence_pack_contract import (
    EvidencePackValidationStatus,
)
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    CacheContinuityMetadata,
    CacheContinuityStatus,
    ComparisonTargetIdentity,
    ReviewMode,
    ReviewModeIntent,
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)
from src.reporting.dashboard.view_models.screen3_diagnostic_view_model import (
    Screen3DiagnosticViewModel,
)
from src.reporting.dashboard.view_models.screen4_review_view_model import (
    Screen4ReviewViewModel,
)
from src.reporting.dashboard.view_models.screen5_action_view_model import (
    Screen5ActionViewModel,
)
from src.reporting.dashboard.view_models.screen6_learning_view_model import (
    Screen6LearningViewModel,
)


def provenance():
    return SelectionProvenance(source_system="screen2_backend_contract_builder")


def runtime_scope():
    return RuntimeScopeIdentity(scope_id="runtime-1", alignment_key="db-prod")


def target(name, alignment_key="db-prod"):
    return ComparisonTargetIdentity(target_id=name, alignment_key=alignment_key)


def selected_scope(**overrides):
    payload = {
        "source_mode": SourceMode.EXISTING_EVIDENCE,
        "runtime_scope": runtime_scope(),
        "target_a": target("target-a"),
        "target_b": target("target-b"),
        "review_mode_intent": ReviewModeIntent(
            requested_modes=(ReviewMode.DEEP_ANALYSIS,),
            historical_evidence_available=True,
            deep_analysis_requested=True,
            deep_analysis_available=True,
        ),
        "provenance": provenance(),
    }
    payload.update(overrides)
    return build_selected_review_scope_contract(**payload)


def invalid_selected_scope():
    return build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=target("target-a"),
        provenance=provenance(),
    )


def payload(name):
    return {
        "evidence_ids": [f"{name}-evidence"],
        "rows": [{"row_id": f"{name}-row", "metric": name, "value": 7}],
        "metrics": {f"{name}_metric": 7},
        "trends": [
            {
                "trend_name": f"{name}-trend",
                "direction": "flat",
                "points": [{"index": 0, "value": 3}, {"index": 1, "value": 7}],
            }
        ],
        "summary": f"{name} evidence",
    }


def action_payload():
    return {
        "evidence_ids": ["action-evidence"],
        "rows": [
            {
                "row_id": "action-row",
                "recommendation": "Add deterministic capacity",
                "action": "scale_db_cpu",
                "risk": "medium",
                "impact": "high",
            }
        ],
        "confidence_basis": [{"basis_id": "action-confidence", "confidence": "medium"}],
        "summary": "Action evidence",
    }


def learning_payload():
    return {
        "evidence_ids": ["learning-evidence"],
        "rows": [
            {
                "row_id": "learning-row",
                "learning_candidate": "candidate-1",
                "governance_status": "pending_review",
                "memory_policy": "approval_required",
                "approval_boundary": "human_gate",
            }
        ],
        "confidence_basis": [{"basis_id": "learning-confidence", "confidence": "medium"}],
        "summary": "Learning governance evidence",
    }


def full_payloads():
    return {
        "diagnostic_payload": payload("diagnostic"),
        "historical_payload": payload("historical"),
        "comparative_payload": payload("comparative"),
        "deep_analysis_payload": payload("deep"),
        "recommendation_action_payload": action_payload(),
        "learning_governance_payload": learning_payload(),
        "provenance": "deterministic_builder",
    }


def build_bundle(scope=None, **payloads):
    return build_dashboard_screen_render_bundle(scope or selected_scope(), **payloads)


def all_html(bundle: DashboardScreenRenderBundle) -> str:
    return "\n".join(
        (
            bundle.screen3_html,
            bundle.screen4_html,
            bundle.screen5_html,
            bundle.screen6_html,
        )
    )


def test_bundle_construction_from_valid_scope_and_deterministic_payloads():
    bundle = build_bundle(**full_payloads())

    assert isinstance(bundle, DashboardScreenRenderBundle)
    assert bundle.selected_flow_id.startswith("selected-flow:")
    assert bundle.evidence_pack_id.startswith("evidence-pack:")
    assert bundle.selected_scope_status == "valid"
    assert bundle.evidence_pack_status == EvidencePackValidationStatus.VALID.value
    assert 'data-screen="screen3_diagnostic_snapshot"' in bundle.screen3_html
    assert 'data-screen="screen4_review"' in bundle.screen4_html
    assert 'data-screen="screen5_recommendation_action"' in bundle.screen5_html
    assert 'data-screen="screen6_learning_governance"' in bundle.screen6_html
    assert bundle.provenance["selected_scope"]["source_system"] == "screen2_backend_contract_builder"
    assert bundle.provenance["evidence_pack"]["source_system"] == "deterministic_builder"


def test_selected_scope_is_required():
    with pytest.raises(ValueError):
        build_dashboard_screen_render_bundle(None)  # type: ignore[arg-type]


def test_contract_spine_order_and_renderer_view_model_domains(monkeypatch):
    order = []

    real_pack_builder = adapter_module.build_evidence_pack_contract
    real_screen3_vm = adapter_module.build_screen3_diagnostic_view_model
    real_screen4_vm = adapter_module.build_screen4_review_view_model
    real_screen5_vm = adapter_module.build_screen5_action_view_model
    real_screen6_vm = adapter_module.build_screen6_learning_view_model
    real_screen3_renderer = adapter_module.render_screen3_diagnostic
    real_screen4_renderer = adapter_module.render_screen4_review
    real_screen5_renderer = adapter_module.render_screen5_action
    real_screen6_renderer = adapter_module.render_screen6_learning

    def pack_builder(*args, **kwargs):
        order.append("evidence_pack")
        return real_pack_builder(*args, **kwargs)

    def screen3_vm(pack):
        order.append("screen3_vm")
        return real_screen3_vm(pack)

    def screen4_vm(pack):
        order.append("screen4_vm")
        return real_screen4_vm(pack)

    def screen5_vm(pack):
        order.append("screen5_vm")
        return real_screen5_vm(pack)

    def screen6_vm(pack):
        order.append("screen6_vm")
        return real_screen6_vm(pack)

    def screen3_renderer(view_model):
        order.append("screen3_renderer")
        assert isinstance(view_model, Screen3DiagnosticViewModel)
        return real_screen3_renderer(view_model)

    def screen4_renderer(view_model):
        order.append("screen4_renderer")
        assert isinstance(view_model, Screen4ReviewViewModel)
        return real_screen4_renderer(view_model)

    def screen5_renderer(view_model):
        order.append("screen5_renderer")
        assert isinstance(view_model, Screen5ActionViewModel)
        return real_screen5_renderer(view_model)

    def screen6_renderer(view_model):
        order.append("screen6_renderer")
        assert isinstance(view_model, Screen6LearningViewModel)
        return real_screen6_renderer(view_model)

    monkeypatch.setattr(adapter_module, "build_evidence_pack_contract", pack_builder)
    monkeypatch.setattr(adapter_module, "build_screen3_diagnostic_view_model", screen3_vm)
    monkeypatch.setattr(adapter_module, "build_screen4_review_view_model", screen4_vm)
    monkeypatch.setattr(adapter_module, "build_screen5_action_view_model", screen5_vm)
    monkeypatch.setattr(adapter_module, "build_screen6_learning_view_model", screen6_vm)
    monkeypatch.setattr(adapter_module, "render_screen3_diagnostic", screen3_renderer)
    monkeypatch.setattr(adapter_module, "render_screen4_review", screen4_renderer)
    monkeypatch.setattr(adapter_module, "render_screen5_action", screen5_renderer)
    monkeypatch.setattr(adapter_module, "render_screen6_learning", screen6_renderer)

    build_bundle(**full_payloads())

    assert order == [
        "evidence_pack",
        "screen3_vm",
        "screen4_vm",
        "screen5_vm",
        "screen6_vm",
        "screen3_renderer",
        "screen4_renderer",
        "screen5_renderer",
        "screen6_renderer",
    ]


def test_invalid_selected_scope_blocks_payload_evidence_and_renders_unavailable_state():
    bundle = build_dashboard_screen_render_bundle(invalid_selected_scope(), **full_payloads())
    text = all_html(bundle)

    assert bundle.selected_scope_status == "invalid"
    assert bundle.evidence_pack_status == "invalid"
    assert "selected_scope_invalid" in text
    assert "Unavailable evidence" in text
    assert "diagnostic-row" not in text
    assert "comparative-row" not in text
    assert "action-row" not in text
    assert "learning-row" not in text
    assert any(error["code"] == "selected_scope_invalid" for error in bundle.errors)


def test_screen_outputs_remain_domain_scoped():
    bundle = build_bundle(**full_payloads())

    assert "Diagnostic Snapshot" in bundle.screen3_html
    assert "Top diagnostic drivers" in bundle.screen3_html
    assert "comparative-row" not in bundle.screen3_html
    assert "comparison_delta" not in bundle.screen3_html
    assert "target_a_vs_target_b_delta" not in bundle.screen3_html

    assert "Historical Review evidence cards" in bundle.screen4_html
    assert "Comparative Review evidence cards" in bundle.screen4_html
    assert "Deep Analysis evidence cards" in bundle.screen4_html
    assert "diagnostic-row" not in bundle.screen4_html
    assert "action-row" not in bundle.screen4_html
    assert "learning-row" not in bundle.screen4_html

    assert "Recommendation/action cards" in bundle.screen5_html
    assert "diagnostic-row" not in bundle.screen5_html
    assert "learning-row" not in bundle.screen5_html

    assert "Learning/governance cards" in bundle.screen6_html
    assert "action-row" not in bundle.screen6_html
    assert "diagnostic-row" not in bundle.screen6_html


def test_missing_unavailable_and_stale_states_survive_into_rendered_fragments():
    missing = build_bundle(
        historical_payload=payload("historical"),
        deep_analysis_payload=payload("deep"),
        recommendation_action_payload=action_payload(),
        learning_governance_payload=learning_payload(),
        provenance="deterministic_builder",
    )
    stale = build_bundle(
        diagnostic_payload={
            "evidence_ids": ["diagnostic-evidence"],
            "rows": [{"row_id": "diagnostic-row", "metric": "db_cpu"}],
            "stale": True,
        },
        comparative_payload={
            "evidence_ids": ["comparative-evidence"],
            "rows": [{"row_id": "comparative-row", "metric": "known_delta", "value": 5}],
            "stale": True,
        },
        provenance="deterministic_builder",
    )
    unavailable = build_dashboard_screen_render_bundle(invalid_selected_scope(), provenance="deterministic_builder")

    assert "Missing evidence" in missing.screen3_html
    assert "payload_missing" in missing.screen3_html
    assert "Missing evidence" in missing.screen4_html
    assert "payload_missing" in missing.screen4_html
    assert "Stale evidence" in stale.screen3_html
    assert "payload_stale" in stale.screen3_html
    assert "Stale evidence" in stale.screen4_html
    assert "payload_stale" in stale.screen4_html
    assert "Unavailable evidence" in unavailable.screen3_html
    assert "selected_scope_invalid" in all_html(unavailable)


def test_dynamic_visuals_appear_only_when_allowed_by_view_model_data():
    present = build_bundle(**full_payloads())
    missing = build_bundle(provenance="deterministic_builder")

    assert 'data-visual-kind="time-series"' in present.screen4_html
    assert "Allowed visualizations" not in all_html(present)
    assert "visualization_id" not in all_html(present)
    assert "source_evidence_ids" not in all_html(present)
    assert 'data-visual-kind="time-series"' not in missing.screen4_html
    assert "Missing evidence" in missing.screen4_html
    assert "show everything" not in all_html(present).lower()
    assert "decorative" not in all_html(present).lower()


def test_non_authoritative_payload_fields_are_rejected_or_ignored():
    bundle = build_bundle(
        diagnostic_payload={
            "evidence_ids": ["diagnostic-evidence"],
            "rows": [{"row_id": "diagnostic-row"}],
            "browser_state": {"selected": "not-authority"},
            "localStorage": "not-authority",
            "hash_state": "#not-authority",
        },
        historical_payload={
            "evidence_ids": ["historical-evidence"],
            "rows": [{"row_id": "historical-row"}],
            "generated_html": "awr_dashboard/screen_4_historical_review.html",
        },
        recommendation_action_payload={
            "llm_recommendation": "LLM says scale now",
            "rows": [{"row_id": "action-row"}],
        },
        learning_governance_payload={
            "llm_text": "approve",
            "rows": [{"row_id": "learning-row"}],
        },
        provenance="deterministic_builder",
    )
    text = all_html(bundle)

    assert "payload_rejected" in text
    assert "not-authority" not in text
    assert "awr_dashboard" not in text
    assert "LLM says scale now" not in text
    assert "approve" not in text
    assert "fallback" not in text.lower()


def test_cache_continuity_does_not_create_evidence():
    scope = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        cache_continuity=CacheContinuityMetadata(status=CacheContinuityStatus.DISPLAY_ONLY),
        provenance=provenance(),
    )

    bundle = build_dashboard_screen_render_bundle(scope, provenance="deterministic_builder")

    assert bundle.selected_scope_status == "invalid"
    assert "selected_scope_invalid" in all_html(bundle)
    assert "diagnostic-row" not in bundle.screen3_html


def test_adapter_does_not_mutate_selected_scope_or_payloads():
    scope = selected_scope()
    before_scope = scope.to_dict()
    payloads = full_payloads()
    before_payloads = copy.deepcopy(payloads)

    build_dashboard_screen_render_bundle(scope, **payloads)

    assert scope.to_dict() == before_scope
    assert payloads == before_payloads


def test_bundle_serializes_to_dict_shape():
    bundle = build_bundle(**full_payloads())
    payload = bundle.to_dict()

    assert payload["selected_flow_id"] == bundle.selected_flow_id
    assert payload["evidence_pack_id"] == bundle.evidence_pack_id
    assert payload["screen3_html"] == bundle.screen3_html
    assert payload["warnings"] == list(bundle.warnings)
    assert payload["errors"] == list(bundle.errors)


def test_dashboard_screen_adapter_import_purity():
    source = Path(adapter_module.__file__).read_text()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    forbidden = (
        "html_dashboard",
        "awr_dashboard",
        "browser",
        "localstorage",
        "hash_state",
        "selector",
        "dashboard_workflow_service",
        "llm",
        "ai_provider",
        "scripts.",
    )
    assert not any(fragment in name.lower() for name in imports for fragment in forbidden)
