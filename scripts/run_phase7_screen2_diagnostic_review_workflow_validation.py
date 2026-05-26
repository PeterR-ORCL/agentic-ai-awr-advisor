#!/usr/bin/env python3
"""Validate the 7CO Screen 2 diagnostic review runtime workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCREEN2_HTML = ROOT / "awr_dashboard" / "screen_3_analysis.html"
HTML_DASHBOARD = ROOT / "src" / "reporting" / "html_dashboard.py"
DASHBOARD_STYLES = ROOT / "src" / "reporting" / "dashboard" / "styles.py"
RUNTIME_CONTRACT = ROOT / "src" / "learning" / "dashboard_runtime_interaction.py"
WORKFLOW_SERVICE = ROOT / "scripts" / "dashboard_workflow_service.py"

PRIMARY_SECTIONS = (
    "Diagnostic Snapshot",
    "Why This Posture",
    "Current Diagnostic Drivers",
    "Interactive Evidence Focus",
    "Focused Diagnostic Meaning",
    "Visual Summary",
    "Health / Data Completeness",
    "Selected-Scope Explanation",
    "Diagnostic Conclusion",
    "Similarity Context",
)

PRIMARY_SECTION_ORDER_MARKERS = (
    "<h2>Diagnostic Snapshot</h2>",
    "<h2>Why This Posture</h2>",
    "<h2>Current Diagnostic Drivers</h2>",
    "<h2>Visual Summary</h2>",
    "<h2>Health / Data Completeness</h2>",
    "<h2>Selected-Scope Explanation</h2>",
    "<h2>Diagnostic Conclusion</h2>",
    "<h2>Similarity Context</h2>",
    "<h2>Interactive Evidence Focus</h2>",
    "<h2>Focused Diagnostic Meaning</h2>",
)

FORBIDDEN_PRIMARY_SNIPPETS = (
    "Phase 7H.3",
    "Phase 7AS",
    "Screen 2 Diagnostic Review / Approval Panel",
    "Review Action Preview Controls",
    "Review Request Preview",
    "Request Parser Review",
    "Request Scoring Review",
    "Request Recommendation Review",
    "Request Learning Candidate",
    "needs_parser_review",
    "needs_scoring_review",
    "needs_recommendation_review",
    "needs_learning_candidate",
    "execute_reanalysis",
    "promote_candidate",
    "materialize_rule",
    "change_runtime_eligibility",
    "capture_recommendation_outcome",
    "sizing/tco",
    "what-if",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate 7CO Screen 2 diagnostic review runtime workflow.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_validation()
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human_summary(summary)
    return 0 if summary["screen2_diagnostic_review_ready"] else 1


def run_validation() -> dict[str, Any]:
    generated_text = read_text(SCREEN2_HTML)
    source_text = "\n".join((read_text(HTML_DASHBOARD), read_text(DASHBOARD_STYLES)))
    contract_text = read_text(RUNTIME_CONTRACT)
    service_text = read_text(WORKFLOW_SERVICE)
    result = validate_screen2_diagnostic_review(
        generated_text=generated_text,
        source_text=source_text,
        contract_text=contract_text,
        service_text=service_text,
        generated_exists=SCREEN2_HTML.is_file(),
    )
    return {
        "phase": "Phase 7",
        "subphase": "7CO",
        "scope": "screen2_diagnostic_review_runtime_workflow",
        "screen2_diagnostic_review_ready": result["screen2_diagnostic_review_ready"],
        "product_sections_ready": result["product_sections_ready"],
        "product_section_order_ready": result["product_section_order_ready"],
        "interactive_evidence_review_ready": result["interactive_evidence_review_ready"],
        "evidence_focus_ready": result["evidence_focus_ready"],
        "screen2_submission_absent_ready": result["screen2_submission_absent_ready"],
        "safety_boundary_ready": result["safety_boundary_ready"],
        "forbidden_primary_ui_absent": result["forbidden_primary_ui_absent"],
        "blocker_active": not result["screen2_diagnostic_review_ready"],
        "remaining_deferred_screens": ["7CP", "7CQ", "7CR", "7CS", "7CT"],
        "failures": result["failures"],
    }


def validate_screen2_diagnostic_review(
    *,
    generated_text: str,
    source_text: str,
    contract_text: str,
    service_text: str = "",
    generated_exists: bool,
) -> dict[str, Any]:
    failures: list[str] = []
    combined = "\n".join((generated_text, source_text, contract_text, service_text))

    if not generated_exists:
        failures.append("generated Screen 2 HTML is missing")

    missing_sections = [section for section in PRIMARY_SECTIONS if section not in generated_text]
    product_sections_ready = not missing_sections
    failures.extend(f"missing primary Screen 2 section: {section}" for section in missing_sections)

    product_section_order_ready = section_order_ready(
        generated_text,
        PRIMARY_SECTION_ORDER_MARKERS,
    )
    if not product_section_order_ready:
        failures.append("primary Screen 2 sections are not in diagnostic-review order")

    interactive_evidence_review_ready = all(
        snippet in generated_text
        for snippet in (
            "Interactive Evidence Focus",
            'data-dashboard-select-key="selectedEvidenceGroup"',
            'data-dashboard-select-key="selectedMetricGroup"',
            'data-dashboard-select-key="selectedWaitEventGroup"',
            'data-dashboard-select-key="selectedDiagnosticSection"',
            "Use Domain to choose the high-level diagnostic lens.",
            "Related selections stay grouped",
            "active domain lens",
        )
    )
    if not interactive_evidence_review_ready:
        failures.append("interactive evidence review selector context is incomplete")

    evidence_focus_markup_ready = all(
        snippet in generated_text
        for snippet in (
            "Focused Diagnostic Meaning",
            "Selected Focus Summary",
            "screen2-focus-summary-compact",
            "data-screen2-focus=\"heading\"",
            "data-screen2-focus=\"summary_line\"",
            "data-screen2-focus=\"meaning\"",
            "data-screen2-focus=\"impact\"",
            "data-screen2-focus=\"handoff\"",
            "data-screen2-focus=\"inferred_domain\"",
            "Active domain lens",
            "Active explanation focus",
            "Focus type",
            "Evidence focus only",
            "Focused Diagnostic Explanation",
            "screen2-focused-explanation-panel",
            "screen2-focused-explanation-list",
            "screen2-focused-explanation-item",
            "screen2-focus-summary-group",
            "screen2-focus-summary-facts",
            "What changes",
            "What does not change",
            'href="screen_4_historical_review.html"',
            'data-dashboard-propagate-state="true"',
            "Deterministic output remains authoritative",
            "LLM-style wording may explain",
        )
    )
    evidence_focus_dynamic_copy_ready = all(
        snippet in combined
        for snippet in (
            "The selected CPU signal shows CPU pressure",
            "The selected I/O signal shows User I/O Pressure",
            "The selected MEMORY signal shows PGA Spill Pressure",
            "The selected COMMIT signal shows commit latency",
            "The selected RAC signal shows cluster wait context",
            "ADG / redo transport evidence is present as topology/context",
            "Not domain-specific",
        )
    )
    explanation_generation_ready = all(
        snippet in combined
        for snippet in (
            "Generate Focused Explanation",
            'data-screen2-generate-explanation="true"',
            "data-screen2-explanation-provider-mode",
            "provider_mode: providerMode",
            "screen2_explanation_provider_mode",
            "PHASE7_SCREEN2_EXPLANATION_PROVIDER_MODE",
            "SCREEN2_EXPLANATION_PROVIDER_MODE",
            "/phase7/dashboard/screen2/explanation",
            "SCREEN2_EXPLANATION_ENDPOINT",
            "/phase7/dashboard/health",
            "PHASE7_DASHBOARD_HEALTH_ENDPOINT",
            "handleScreen2GenerateExplanationClick",
            "screen2GeneratedExplanationText",
            "dashboardScreen2ExplanationProvider",
            "window.fetch(SCREEN2_EXPLANATION_ENDPOINT",
            "screen_id: 'screen_2'",
            "providerMode === 'off'",
            "Explanation provider service is not running. Start the dashboard workflow service and try again. The deterministic explanation remains available.",
            "Explanation endpoint is not available in the dashboard workflow service. The deterministic explanation remains available.",
            "screen2ExplanationViolatesBoundary",
            "No workflow request, audit record, governance record",
            "justify-items: center",
        )
    )
    endpoint_ready = all(
        snippet in service_text
        for snippet in (
            'SCREEN2_EXPLANATION_ENDPOINT_PATH = "/phase7/dashboard/screen2/explanation"',
            'HEALTH_ENDPOINT_PATH = "/phase7/dashboard/health"',
            "generate_screen2_explanation",
            "def do_GET",
            "SCREEN2_EXPLANATION_FORBIDDEN_FIELDS",
            "records_created",
            "audit_reference",
            "generate_ai_response",
        )
    )
    if not endpoint_ready:
        failures.append("Screen 2 explanation backend endpoint is incomplete")
    selection_local_ready = all(
        snippet in source_text
        for snippet in (
            "SCREEN2_FOCUS_STATE_KEYS",
            "SCREEN2_FOCUS_ITEM_STATE_KEYS",
            "screen2ActiveFocusKey",
            "screen2ActiveFocusDomain",
            "screen2ActiveFocusLabel",
            "screen2ActiveEvidenceGroup",
            "screen2ActiveMetric",
            "screen2ActiveWaitEvent",
            "screen2ActiveDiagnosticSection",
            "screen2InferredDomain",
            "nextState.selectedDomain = inferredDomain",
            "screen2EnsureEvidenceParentForDomain(nextState, inferredDomain)",
            "screen2ClearIncompatibleFocusContext(nextState, inferredDomain, key)",
            "updateScreen2DomainScopedSelectors(safeState, root)",
            "data-screen2-domain-scoped",
            "updateScreen2DiagnosticReviewSummary(safeState, root)",
            "selectDashboardElement(element)",
        )
    ) and "SCREEN2_FOCUS_ITEM_STATE_KEYS.forEach(function (focusKey)" not in source_text
    dynamic_selector_ready = all(
        snippet in generated_text
        for snippet in (
            "<strong>CPU</strong>",
            "<strong>IO</strong>",
            "<strong>MEMORY</strong>",
            "<strong>COMMIT</strong>",
            "<strong>RAC</strong>",
            "<strong>ADG</strong>",
            'data-screen2-domain-scoped="true"',
            "Select a domain lens to see evidence groups for that domain.",
            "No metric focus items are available for the active {domain} lens.",
            "No wait-event focus items are directly associated with the active {domain} lens.",
            "No wait-event focus items are directly associated with the active CPU lens. Select COMMIT or RAC to inspect wait-event evidence.",
            "No SQL signal groups are available for the active {domain} lens.",
            "Report Section Explanation Focus",
            "<strong>CPU Signal</strong>",
            "<strong>I/O Signal</strong>",
            "<strong>Commit Signal</strong>",
            "<strong>DB CPU % DB Time</strong>",
        )
    ) and all(
        snippet in combined
        for snippet in (
            'data-screen2-domain-scope-active',
            "screen2DomainScopedEmptyMessage",
            ".screen2-selector-card[hidden]",
        )
    ) and (
        "<strong>User I/O Pressure</strong>" in generated_text
        or "<strong>User I/O % DB Time</strong>" in generated_text
    ) and all(
        snippet not in generated_text
        for snippet in (
            "<strong>CPU score</strong>",
            "<strong>IO score</strong>",
            "<strong>MEMORY score</strong>",
            "<strong>COMMIT score</strong>",
            "<strong>RAC score</strong>",
            "<strong>ADG score</strong>",
        )
    )
    if not dynamic_selector_ready:
        failures.append("Screen 2 evidence focus selectors are not dynamic/case-aware")
    evidence_focus_ready = (
        evidence_focus_markup_ready
        and evidence_focus_dynamic_copy_ready
        and explanation_generation_ready
        and endpoint_ready
        and selection_local_ready
        and dynamic_selector_ready
    )
    if not evidence_focus_ready:
        failures.append("Screen 2 evidence focus explanation panel is incomplete")

    forbidden_submission_snippets = (
        "Submit Governed Diagnostic Review Request",
        'data-action-type="diagnostic_review"',
        'data-workflow-type="screen2_diagnostic_review_evidence_validation"',
        "screen2ReviewDisposition",
        "screen2Reviewer",
        "screen2ReviewNote",
        "Review disposition",
        "Reviewer note",
        "Request / Audit Result",
        "Technical audit record",
        "Review request submitted",
        "request_governed_diagnostic_review",
        "confirm_evidence_reviewed",
        "flag_insufficient_evidence",
        "dispute_diagnostic_interpretation",
        "add_reviewer_note",
    )
    submission_found = [
        snippet for snippet in forbidden_submission_snippets if snippet in generated_text
    ]
    screen2_submission_absent_ready = not submission_found
    failures.extend(
        f"Screen 2 submission/review request UI remains: {snippet}"
        for snippet in submission_found
    )

    if "Confidence is displayed from the authoritative Phase 4I output" in generated_text:
        failures.append("Screen 2 still exposes Phase 4I confidence wording in product UI")
    removed_focus_snippets = (
        "Selected Evidence Summary",
        "Current diagnosis",
        "<h3>Current AWR / Run Context</h3>",
        "<strong>Current AWR</strong>",
        "<strong>Current confidence</strong>",
        "static export",
        "static report",
    )
    for snippet in removed_focus_snippets:
        if snippet.lower() in generated_text.lower():
            failures.append(f"removed Screen 2 focus wording remains: {snippet}")

    forbidden_found = [
        snippet for snippet in FORBIDDEN_PRIMARY_SNIPPETS if snippet.lower() in generated_text.lower()
    ]
    forbidden_primary_ui_absent = not forbidden_found
    failures.extend(f"forbidden primary Screen 2 UI remains: {snippet}" for snippet in forbidden_found)

    request_builder_ready = all(
        snippet in source_text
        for snippet in (
            "dashboardScreen2ExplanationProvider",
            "SCREEN2_EXPLANATION_ENDPOINT",
            "screen2ExplanationViolatesBoundary",
            "allowed_screen2_changes",
            "Focused Diagnostic Meaning",
            "LLM-style wording may explain",
            "screen2FocusedDiagnosticMeaning",
            "screen2SelectedFocusDomain",
            "screen2ActiveEvidenceGroup",
            "screen2ActiveMetric",
            "screen2ActiveWaitEvent",
            "screen2ActiveDiagnosticSection",
            "handleScreen2GenerateExplanationClick",
        )
    )
    if not request_builder_ready:
        failures.append("Screen 2 evidence focus source contract is incomplete")

    hierarchy_panel_ready = all(
        snippet in generated_text
        for snippet in (
            "Active domain lens",
            "Active evidence group",
            "Active metric / wait / SQL",
            "Active diagnostic section",
            "Active explanation focus",
            "Focus type",
            "Inferred domain",
            '<div class="screen2-outcome-row"><dt>Decision posture</dt><dd data-screen2-focus="decision_posture"><span class="status-pill',
            '<div class="screen2-outcome-row"><dt>Severity</dt><dd data-screen2-focus="severity"><span class="status-pill',
            '<div class="screen2-outcome-row"><dt>Confidence</dt><dd data-screen2-focus="confidence"><span class="confidence-pill',
        )
    ) and all(
        snippet in combined
        for snippet in (
            ".screen2-selected-evidence-card .screen2-outcome-row .status-pill",
            ".screen2-selected-evidence-card .screen2-outcome-row .confidence-pill",
            "min-width: 72px",
        )
    )
    if not hierarchy_panel_ready:
        failures.append("Screen 2 focused meaning hierarchy summary is incomplete")

    safety_boundary_ready = (
        "does not remove evidence or change diagnosis, scoring" in generated_text
        and "Selection changes only the local explanation focus. It does not change diagnosis, scoring, recommendations, parser output, runtime behavior, ML behavior, materialization, runtime eligibility, or future-run behavior." in generated_text
        and "Generate Focused Explanation refreshes explanatory wording only when the operator explicitly requests it." in generated_text
        and "governed service behavior remain unchanged" in generated_text
        and "Diagnosis, score, confidence, and recommendation changes require deterministic analysis" in generated_text
        and "ML behavior" in generated_text
        and "future-run behavior" in generated_text
        and "No workflow request, audit record, governance record" in generated_text
        and "<details class=\"screen2-focus-helper\">" in generated_text
    )
    if not safety_boundary_ready:
        failures.append("Screen 2 safety boundary is incomplete")

    ready = all(
        (
            product_sections_ready,
            product_section_order_ready,
            interactive_evidence_review_ready,
            evidence_focus_ready,
            screen2_submission_absent_ready,
            forbidden_primary_ui_absent,
            request_builder_ready,
            hierarchy_panel_ready,
            safety_boundary_ready,
        )
    ) and not failures
    return {
        "screen2_diagnostic_review_ready": ready,
        "product_sections_ready": product_sections_ready,
        "product_section_order_ready": product_section_order_ready,
        "interactive_evidence_review_ready": interactive_evidence_review_ready,
        "evidence_focus_ready": evidence_focus_ready,
        "screen2_submission_absent_ready": screen2_submission_absent_ready,
        "safety_boundary_ready": safety_boundary_ready,
        "hierarchy_panel_ready": hierarchy_panel_ready,
        "endpoint_ready": endpoint_ready,
        "forbidden_primary_ui_absent": forbidden_primary_ui_absent,
        "failures": failures,
    }


def section_order_ready(text: str, sections: Sequence[str]) -> bool:
    cursor = -1
    for section in sections:
        index = text.find(section)
        if index < 0 or index <= cursor:
            return False
        cursor = index
    return True


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def print_human_summary(summary: dict[str, Any]) -> None:
    status = "passed" if summary["screen2_diagnostic_review_ready"] else "failed"
    print(f"Phase 7CO Screen 2 diagnostic review workflow validation {status}.")
    print(f"screen2_diagnostic_review_ready={summary['screen2_diagnostic_review_ready']}")
    print(f"blocker_active={summary['blocker_active']}")
    if summary["failures"]:
        print("Failures:")
        for failure in summary["failures"]:
            print(f"- {failure}")


if __name__ == "__main__":
    raise SystemExit(main())
