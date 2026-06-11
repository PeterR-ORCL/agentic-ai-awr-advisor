# 7RESET Dashboard Product Recut Audit

## 1. Repo-state verification

Verification was run from `/Users/probev/Projects/agentic-ai-awr-advisor` on branch
`phase7-final-operational-certification`.

| Check | Observed result |
| --- | --- |
| `pwd` | `/Users/probev/Projects/agentic-ai-awr-advisor` |
| `git branch --show-current` | `phase7-final-operational-certification` |
| `git log --oneline -25` | HEAD is `4582e25 Revert "Rebuild contract-backed product renderers"` |
| `git status --short` | `?? docs/forensics/` only before this document was created |
| `git diff --stat` | empty before this document was created |
| `git diff --name-only` | empty before this document was created |
| `git diff --cached --name-only` | empty |
| `git tag --list | grep PHASE7_COMPLETE || true` | empty |
| `test -e PHASE7_COMPLETE ...` | `PHASE7_COMPLETE file absent` |

The untracked `docs/forensics/7reset/` bundle records the reverted dirty-tree
state. It is recovery context only. It does not authorize generated HTML,
renderer patches, or a Phase 7 completion claim.

## 2. Historical notes policy

The historical project notes PDF is product and design context only. Later
phase labels, commit references, or "complete" statements in those notes are
not operational truth for this repository. Current truth must come from the
repo state, validated deterministic code paths, persisted contracts, and the
7RESET recovery handoff.

## 3. Phase 7 status

Phase 7 is not complete.

No `PHASE7_COMPLETE` file should be created. No `PHASE7_COMPLETE` tag should be
created. Generated dashboard HTML must not be treated as acceptance evidence.

## 4. Source-of-truth policy

| Source | Authority policy |
| --- | --- |
| Deterministic engines | Authoritative for the facts they compute, subject to their input contracts and tests. |
| Persisted contracts | Authoritative when validated, fresh, scoped, and produced by deterministic code. |
| Generated HTML | Output only. It is a symptom of source behavior, not source truth or acceptance proof. |
| Browser state, `localStorage`, hash, cache | Continuity only. It can restore a view preference but cannot create evidence, select truth, or satisfy freshness. |
| LLM explanation | Explanation only after deterministic truth already exists. It is not evidence and cannot decide diagnosis, recommendation, comparison, learning state, or readiness. |
| Old phase notes | Historical context only. They are not executable state, backlog authority, or completion evidence. |

Required recovery warnings:

- Generated HTML is output only.
- Browser state, `localStorage`, hash state, and cache are not truth.
- Deterministic engines decide.
- LLM explains only already-decided deterministic truth.
- Old phase notes are context only.
- Historical and multi-snapshot context must not contaminate selected single-AWR diagnosis.
- Screen 3 must not show raw dict, list, `<pre>`, or debug output.
- Screen 4 must not show trend-name/point-count flattened output as evidence review.
- `allowed_visualizations` metadata must not become product UI.
- Target A/B must not be fabricated.
- Deep Analysis must not be fabricated.
- Recommendations must not be LLM-created.
- Generated dashboard artifacts are not acceptance proof.

## 5. Layer classification

Layer labels:

| Layer | Meaning |
| --- | --- |
| A. Trusted deterministic core | Deterministic engines or persisted contracts that can be truth after validation. |
| B. Salvageable contract/adaptor layer | Useful normalizers or view-model scaffolds, but not product-renderer truth. |
| C. Legacy shell / quarantine | Existing display shell or legacy contract surface that may be mined for field names but should not be extended until product contracts are approved. |
| D. Failed product renderer | Current or reverted rendering chain that exposes implementation data as product UI. Do not continue it. |
| E. Generated artifact symptom only | Output artifact. Inspect only as a symptom; never accept as proof. |
| F. Unsafe / unknown | Non-authoritative or insufficiently bounded input. Must not drive implementation. |

| Surface | Layer | Current classification |
| --- | --- | --- |
| `awr_dashboard/*.html` | E | Generated artifact symptom only. Do not regenerate, commit, or use as source truth. |
| `src/reporting/html_dashboard.py` | C | Legacy dashboard shell and rendering monolith. Quarantine until screen product contracts are approved. |
| `src/reporting/dashboard/renderers/*` | D | Failed product renderer chain. It renders raw mappings/lists through `<pre>`, exposes internal IDs, and displays `allowed_visualizations` as UI. |
| `src/reporting/dashboard/view_models/*` | B | Salvageable as a contract-adaptor starting point, but current shapes are too raw and ID-forward for product rendering. |
| `selected_review_scope_contract` | A | Persisted selected-scope authority when validation passes. Browser, LLM, and generated HTML inputs are explicitly non-authority. |
| `evidence_pack_contract` | A | Deterministic evidence authority downstream of selected scope when validation passes. |
| `evidence_pack_builder` | B | Useful deterministic normalizer from scoped payloads into evidence packs. It still needs screen-specific product view model recut. |
| `dashboard_screen_adapter` | B | Salvageable integration boundary, but current HTML bundle output must be disabled or replaced because it imports failed renderers. |
| `production_contract_bundle_adapter` | B | Useful readiness and production-normalization adapter. It should feed approved product contracts, not generated HTML acceptance. |
| `frontend_contract` | C | Legacy Phase 4/Screen 2 display contract. It may inform field mapping but is not the new product source of truth. |
| `output_layer` | B | Stable deterministic output adaptor from decisions, scores, trends, similarity, and recommendations. It can feed product contracts after scope/provenance validation. |
| Scoring, trend, similarity, recommendation engines | A | Deterministic core for analysis facts, trend context, similarity context, and recommendations. |
| Screen 2 browser/`localStorage` selector path | C | Continuity shell only. It cannot determine selected scope, Target A/B truth, or analysis readiness. |
| Screen 4 comparison/deep-analysis rendering path | D | Current rendering path is unsafe where it turns contract internals and visualization permissions into product UI. |
| Memory and learning governance modules | A | Deterministic governance core when persisted and validated. Must remain separate from LLM and browser state. |
| Historical notes PDF and old phase notes | F | Context only. Not executable backlog or operational completion proof. |
| LLM-generated narrative/recommendation fields | F | Explanation only after deterministic truth. Not evidence, action authority, or acceptance proof. |

## 6. Findings: why current Screen 3/4 rendering is unsafe

1. Generic dict/list rendering is product-hostile. `src/reporting/dashboard/renderers/common.py` flattens mappings and sequences with `_format_value(...)`, so product panels become implementation dumps instead of designed evidence views.

2. `<pre>` and debug-style output leak into product UI. `render_items(...)` wraps each raw mapping in `<pre>`, preserving backend shape as visible UI.

3. Internal IDs are exposed in the primary interface. `render_identity(...)` displays `selected_flow_id` and `evidence_pack_id`. These may belong in a metadata/debug annex, but not in the first fold or primary product UI.

4. `allowed_visualizations` is rendered as product UI. This field is a permission or eligibility input for rendering, not user-facing evidence.

5. Screen 3 can be contaminated by multi-snapshot or historical explanations. A single-AWR Diagnostic Snapshot must not present multi-snapshot trend context as selected-scope proof.

6. Screen 4 can collapse distinct modes. Historical context, Comparative Target A/B output, and Deep Analysis current-scope drilldown require separate scope classes and unavailable states. Rendering them through a common list path invites mode contamination.

7. Trend-name/point-count output is not evidence review. Showing that a trend exists, or that it has N points, is not the same as showing deterministic evidence, scope, provenance, freshness, and interpretation boundaries.

8. Generated HTML was treated as acceptance proof in the failed chain. Acceptance must be based on deterministic contracts and tests, not on the presence or appearance of regenerated `awr_dashboard/*.html`.

## 7. Canonical target screen roles

| Screen | Canonical role |
| --- | --- |
| Screen 1 | Ingestion / parser / source governance |
| Screen 2 | Runtime Scope and Analysis Control |
| Screen 3 | Diagnostic Snapshot |
| Screen 4 | Evidence Review with Historical, Comparative, and Deep Analysis modes |
| Screen 5 | Recommendation Action |
| Screen 6 | Learning Governance |

## 8. Screen-specific product requirements

### Screen 1: Ingestion / parser / source governance

| Area | Requirement |
| --- | --- |
| First fold | Source mode, source identity, parse status, snapshot window, parser coverage, and source-governance status. |
| Primary cards | Source Intake, Parser Health, Parse Diagnostics, Unknown or Unmapped Sections, Source Governance. |
| Secondary sections | File/object metadata, skipped inputs, section registry coverage, parser warnings, rejected non-authority inputs. |
| Required deterministic fields | `source_mode`, source reference, `dbid` or database identity, instance identity when present, snapshot begin/end, parser version, parser status, parsed section count, unknown section count, fatal errors, provenance. |
| Unavailable states | No source selected, source unreadable, Object Storage config blocked, parser failed, unsupported report shape, stale parsed artifact. |
| Forbidden content | LLM diagnosis, recommendation, generated HTML path as source authority, browser cache as source selection, phase-completion claims. |
| Visual components | Source flow status, parser coverage bar/table, warning badges, source provenance table. |
| Acceptance tests | Fails if source authority comes from generated HTML or browser state; fails if parse errors are hidden; fails if unknown sections are shown as successful coverage. |

### Screen 2: Runtime Scope and Analysis Control

| Area | Requirement |
| --- | --- |
| First fold | Product-safe selected runtime scope, flow kind, mode availability, Target A/B readiness, freshness, and deterministic run readiness. |
| Primary cards | Runtime Scope, Analysis Mode Control, Target A/B Preparation, Readiness Gates, Cache Continuity Notice. |
| Secondary sections | Contract provenance, source-to-scope mapping, invalidated cache notices, unavailable mode reasons. |
| Required deterministic fields | `contract_type`, `contract_version`, `review_flow_kind`, `source_mode`, `scope_validation_status`, `target_alignment_status`, `cache_continuity_status`, selected runtime scope refs, Target A and Target B refs when applicable, provenance, freshness. |
| Unavailable states | Missing selected scope, invalid scope, missing Target A, missing Target B, prepared-only comparison, stale cache, source mismatch. |
| Forbidden content | `localStorage` deciding truth, generated HTML deciding scope, comparison output before deterministic comparison exists, Deep Analysis output before its contract exists. |
| Visual components | Segmented mode control, target readiness matrix, scope provenance ribbon, unavailable-state panel. |
| Acceptance tests | Fails if browser selectors create scope; fails if Target A/B is fabricated; fails if internal IDs replace product-safe labels in the first fold. |

### Screen 3: Diagnostic Snapshot

| Area | Requirement |
| --- | --- |
| First fold | Current selected AWR scope, deterministic health status, primary issue, severity/confidence, top evidence drivers, and missing-evidence notice. |
| Primary cards | Health Summary, Primary Drivers, Domain Scores, Metric Snapshot, Confidence Basis. |
| Secondary sections | Waits, top SQL, I/O, CPU, memory, RAC/Data Guard/topology details, anomaly notes, similarity context only when scoped as context. |
| Required deterministic fields | Current-scope ref, diagnostic decision ref, primary/secondary issues, severity, confidence, domain scores, evidence rows, metric values, trend/anomaly refs with scope class, similarity context refs, freshness, provenance, missing evidence. |
| Unavailable states | No current diagnostic output, stale evidence, scope mismatch, parser missing required sections, single-AWR mode polluted by multi-snapshot-only evidence. |
| Forbidden content | Raw dict/list/`<pre>` output, flattened debug text, `selected_flow_id` or `evidence_pack_id` in primary UI, `allowed_visualizations`, multi-snapshot explanation as single-AWR proof, LLM-created diagnosis. |
| Visual components | Score cards, driver table, evidence heat map, current-scope `TimeSeriesVisual` only when contract-backed, `UnavailableVisualState`. |
| Acceptance tests | Fails if raw mapping text appears; fails if first fold exposes internal IDs; fails if Screen 3 single-AWR includes multi-snapshot trend claims as selected-scope proof. |

### Screen 4: Evidence Review with Historical, Comparative, Deep Analysis modes

| Area | Requirement |
| --- | --- |
| First fold | Mode selector, mode availability, current selected scope, Target A/B state when relevant, and explicit historical/comparative/deep-analysis boundaries. |
| Primary cards | Historical Evidence, Comparative Delta, Deep Analysis Drilldown, Missing/Blocked Evidence. |
| Secondary sections | Distribution/violin panels, evidence tables, provenance, freshness, limitations, raw-evidence drilldown only after product-safe shaping. |
| Required deterministic fields | `active_mode`, per-mode `availability_status`, per-row `scope_classification`, historical baseline refs, comparison contract refs, Target A/B product labels, Deep Analysis contract refs, freshness, provenance, missing evidence, allowed visual eligibility as renderer input only. |
| Unavailable states | No historical baseline, prepared-only comparison, missing Target A/B, invalid comparison output, absent Deep Analysis contract, Deep Analysis scope mismatch, historical-only context. |
| Forbidden content | Historical context represented as selected-scope truth, Target A/B fabrication, comparative rows rendered as Deep Analysis evidence, `allowed_visualizations` as product UI, browser mode/cache state as evidence, LLM-created evidence. |
| Visual components | `TimeSeriesVisual`, `DistributionVisual`, `ViolinVisual`, `ComparisonDeltaVisual`, `UnavailableVisualState`. |
| Acceptance tests | Fails if Historical, Comparative, and Deep Analysis rows share an untyped generic renderer; fails if Deep Analysis is fabricated; fails if Target A/B is fabricated; fails if visual permission fields are visible as UI. |

### Screen 5: Recommendation Action

| Area | Requirement |
| --- | --- |
| First fold | Deterministic recommendation decision, action priority, reason, confidence, expected impact, risk, and action readiness. |
| Primary cards | Recommended Action, Evidence Behind Action, Risk and Impact, Validation Checklist, Owner/Status. |
| Secondary sections | Alternatives, dependencies, action history, outcome capture, feedback-to-learning route. |
| Required deterministic fields | Recommendation decision ref, recommendation source engine, action label, priority, impact estimate, risk statement, prerequisites, confidence basis, validation evidence, governance status, outcome state, provenance. |
| Unavailable states | No deterministic recommendation, insufficient evidence, confidence below threshold, governance blocked, action prerequisites missing. |
| Forbidden content | LLM-created recommendations, browser-selected actions as truth, fake ROI/TCO, owner/status fabricated by UI, generated HTML as recommendation proof. |
| Visual components | Action priority ladder, risk/impact matrix, validation checklist, status timeline, `UnavailableVisualState`. |
| Acceptance tests | Fails if recommendations appear without deterministic engine output; fails if LLM text creates an action; fails if action state is inferred from browser cache. |

### Screen 6: Learning Governance

| Area | Requirement |
| --- | --- |
| First fold | Governance posture, candidate counts by status, materialization gate, runtime eligibility, memory policy, and approval requirements. |
| Primary cards | Learning Candidate Queue, Governance Status, Materialization Approval, Runtime Eligibility, Memory Policy. |
| Secondary sections | Audit log, backtesting summary, feature labels, model registry, rollback/fallback status, governed write path. |
| Required deterministic fields | Candidate refs, candidate evidence refs, governance state, approval authority, materialization status, runtime eligibility, memory refs, persisted audit state, freshness, provenance. |
| Unavailable states | Governance store unavailable, no candidates, registry unavailable, missing approval boundary, memory disabled, runtime gate blocked. |
| Forbidden content | Auto-activation from UI, LLM approval, memory recall as evidence without governance, localStorage as learning state, generated HTML as materialization proof. |
| Visual components | Governance lane, approval matrix, candidate table, audit timeline, runtime gate state, `UnavailableVisualState`. |
| Acceptance tests | Fails if learning state is inferred from UI/cache; fails if materialization appears approved without persisted governance; fails if LLM or memory output bypasses approval. |

## 9. Exact proposed view model shapes

These shapes replace the current raw dict/list renderer inputs. Renderers should
consume only these product-safe fields. Internal IDs may exist only inside
`internal_refs`, which is not part of the first fold or primary product UI.

```text
Screen3DiagnosticSnapshotViewModel {
  screen_id: "screen3_diagnostic_snapshot"
  contract_version: "7reset.product.screen3.v1"
  scope_summary: ProductScopeSummary
  first_fold: DiagnosticFirstFold
  primary_cards: tuple[DiagnosticProductCard, ...]
  secondary_sections: tuple[EvidenceReviewSection, ...]
  visuals: tuple[TimeSeriesVisual | UnavailableVisualState, ...]
  evidence_table: EvidenceTable
  missing_evidence: tuple[UnavailableVisualState, ...]
  llm_explanation: ExplanationBlock | None
  provenance: ProvenanceBlock
  freshness: FreshnessBlock
  internal_refs: InternalReferenceBlock
}

DiagnosticFirstFold {
  status_label: str
  primary_issue_label: str | None
  severity_score: number | None
  confidence_score: number | None
  top_driver_labels: tuple[str, ...]
  missing_evidence_summary: str | None
}
```

```text
Screen4EvidenceReviewViewModel {
  screen_id: "screen4_evidence_review"
  contract_version: "7reset.product.screen4.v1"
  scope_summary: ProductScopeSummary
  active_mode: "historical" | "comparative" | "deep_analysis"
  mode_tabs: tuple[ReviewModeTab, ReviewModeTab, ReviewModeTab]
  historical: EvidenceReviewModePanel
  comparative: EvidenceReviewModePanel
  deep_analysis: EvidenceReviewModePanel
  cross_mode_warnings: tuple[UnavailableVisualState, ...]
  provenance: ProvenanceBlock
  freshness: FreshnessBlock
  internal_refs: InternalReferenceBlock
}

EvidenceReviewModePanel {
  mode: "historical" | "comparative" | "deep_analysis"
  availability: "ready" | "partial" | "unavailable" | "blocked"
  first_fold_summary: str
  primary_cards: tuple[EvidenceProductCard, ...]
  secondary_sections: tuple[EvidenceReviewSection, ...]
  visuals: tuple[TimeSeriesVisual | DistributionVisual | ViolinVisual | ComparisonDeltaVisual | UnavailableVisualState, ...]
  evidence_table: EvidenceTable
  unavailable_states: tuple[UnavailableVisualState, ...]
  llm_explanation: ExplanationBlock | None
}
```

```text
Screen5RecommendationActionViewModel {
  screen_id: "screen5_recommendation_action"
  contract_version: "7reset.product.screen5.v1"
  scope_summary: ProductScopeSummary
  first_fold: RecommendationFirstFold
  recommendation_decision: RecommendationDecisionCard | UnavailableVisualState
  action_plan: ActionPlanCard | UnavailableVisualState
  validation_checklist: tuple[ValidationChecklistItem, ...]
  risk_impact: RiskImpactPanel | UnavailableVisualState
  owner_status: ActionStatusPanel | UnavailableVisualState
  outcome_capture: OutcomeCapturePanel | UnavailableVisualState
  secondary_sections: tuple[EvidenceReviewSection, ...]
  llm_explanation: ExplanationBlock | None
  provenance: ProvenanceBlock
  freshness: FreshnessBlock
  internal_refs: InternalReferenceBlock
}

RecommendationFirstFold {
  action_label: str | None
  priority_label: str | None
  reason_summary: str | None
  confidence_score: number | None
  readiness_status: "ready" | "blocked" | "unavailable"
}
```

```text
Screen6LearningGovernanceViewModel {
  screen_id: "screen6_learning_governance"
  contract_version: "7reset.product.screen6.v1"
  governance_summary: GovernanceFirstFold
  candidate_queue: LearningCandidateQueue | UnavailableVisualState
  governance_status: GovernanceStatusPanel | UnavailableVisualState
  materialization_gate: MaterializationGatePanel | UnavailableVisualState
  runtime_eligibility: RuntimeEligibilityPanel | UnavailableVisualState
  memory_policy: MemoryPolicyPanel | UnavailableVisualState
  audit_timeline: AuditTimeline | UnavailableVisualState
  secondary_sections: tuple[EvidenceReviewSection, ...]
  provenance: ProvenanceBlock
  freshness: FreshnessBlock
  internal_refs: InternalReferenceBlock
}

GovernanceFirstFold {
  posture_label: str
  candidates_pending: integer
  candidates_blocked: integer
  candidates_approved: integer
  materialization_status: "not_requested" | "pending" | "approved" | "blocked"
  runtime_gate_status: "eligible" | "ineligible" | "blocked" | "unknown"
}
```

Shared product-safe supporting shapes:

```text
ProductScopeSummary {
  label: str
  database_label: str | None
  instance_label: str | None
  snapshot_window_label: str | None
  flow_kind: "single_awr" | "historical" | "comparative" | "deep_analysis" | "unavailable"
  validation_status: "valid" | "partial" | "invalid" | "unavailable"
}

EvidenceReviewSection {
  section_id: str
  title: str
  scope_classification: "current_scope" | "historical_supporting_context" | "comparative_output" | "deep_analysis_current_scope" | "governance_persisted"
  rows: tuple[EvidenceDisplayRow, ...]
  limitations: tuple[str, ...]
}

EvidenceDisplayRow {
  label: str
  value: str | number | None
  unit: str | None
  interpretation: str | None
  evidence_ref_label: str
  freshness_status: "fresh" | "stale" | "unknown"
}

ExplanationBlock {
  eligibility: "allowed" | "blocked" | "not_applicable"
  explanation_text: str | None
  explains_refs: tuple[str, ...]
  prohibited_as_evidence: true
}
```

## Canonical SelectedReviewScopeContract shape

The selected scope contract is the canonical deterministic statement of what
the operator is reviewing. It identifies scope only; it does not create
diagnosis, comparison evidence, sizing evidence, recommendations, or learning
state.

```text
SelectedReviewScopeContract {
  contract_type: "selected_review_scope_contract"
  contract_version: str
  flow_kind:
    | "single_awr"
    | "runtime_scope"
    | "historical_multi_snapshot"
    | "comparison"
    | "fleet"
    | "predictive_sizing"
    | "comparative_sizing"
    | "healthcheck"
  selected_report: {
    report_id: str | None
    awr_id: str | None
    database_id: str | None
    database_name: str | None
    instance_id: str | None
    instance_name: str | None
    source_ref: str | None
  }
  selected_snapshot_window: {
    snapshot_id: str | None
    begin_time: str | None
    end_time: str | None
    window_label: str | None
  }
  runtime_scope: {
    scope_id: str | None
    scope_label: str | None
    source_mode: str | None
    run_id: str | None
  }
  target_a: TargetScopeRef | None
  target_b: TargetScopeRef | None
  fleet_cohort: {
    cohort_id: str | None
    cohort_label: str | None
    member_refs: tuple[str, ...]
  } | None
  source_of_truth: {
    source_system: str
    deterministic_source_refs: tuple[str, ...]
    generated_html_allowed_as_truth: false
    browser_state_allowed_as_truth: false
    llm_allowed_as_truth: false
  }
  validation_status: "valid" | "partial" | "invalid" | "unavailable"
  freshness: FreshnessBlock
  unsupported_states: tuple[UnavailableVisualState, ...]
  missing_states: tuple[UnavailableVisualState, ...]
  provenance: ProvenanceBlock
  internal_refs: InternalReferenceBlock
}

TargetScopeRef {
  label: str
  report_ref: str
  snapshot_window_ref: str | None
  deterministic_resolution_status: "resolved" | "missing" | "ambiguous" | "unavailable"
}
```

Selected scope guardrails:

- Browser state, `localStorage`, hash state, and cache cannot create selected truth.
- Generated HTML cannot create selected truth.
- LLM output cannot create selected truth.
- `single_awr` scope cannot be polluted by `historical_multi_snapshot` context.
- `comparison` scope is unavailable unless Target A and Target B are deterministically resolved.
- `predictive_sizing` and `comparative_sizing` are unavailable unless real sizing contracts exist.

## Canonical EvidencePackContract shape

The evidence pack contract is the canonical deterministic evidence bundle for a
validated selected scope. It separates selected diagnostic truth from
supporting context and keeps renderer metadata away from user-facing evidence.

```text
EvidencePackContract {
  contract_type: "evidence_pack_contract"
  contract_version: str
  selected_scope_ref: {
    selected_scope_id: str
    selected_scope_contract_version: str
    flow_kind: str
    validation_status: str
  }
  selected_diagnostic_evidence: EvidenceSection
  supporting_historical_context: EvidenceSection
  comparison_evidence: EvidenceSection
  deep_analysis_evidence: EvidenceSection
  recommendation_evidence: EvidenceSection
  sizing_evidence: EvidenceSection
  healthcheck_evidence: EvidenceSection
  visualization_evidence: tuple[TimeSeriesVisual | DistributionVisual | ViolinVisual | ComparisonDeltaVisual | UnavailableVisualState, ...]
  confidence_basis: tuple[EvidenceDisplayRow, ...]
  missing_evidence: tuple[UnavailableVisualState, ...]
  unavailable_states: tuple[UnavailableVisualState, ...]
  provenance: ProvenanceBlock
  debug_metadata: {
    builder_version: str | None
    validation_messages: tuple[str, ...]
    rejected_authority_inputs: tuple[str, ...]
  }
  internal_refs: InternalReferenceBlock
}
```

Evidence pack guardrails:

- Selected diagnostic evidence is not the same as supporting historical context.
- Historical context must be labeled supporting or contextual.
- Comparison evidence requires a deterministic comparison contract.
- Deep Analysis evidence requires a real deep-analysis input contract.
- Visualization evidence is renderer input only, not product UI by itself.
- `allowed_visualizations` must never be rendered as user-facing evidence.
- Debug metadata and internal refs must not appear in first-fold product UI.

## 10. Exact visual contracts

Visuals must be data contracts, not pre-rendered static art. A renderer may draw
from these contracts only when required fields and provenance validate.

```text
TimeSeriesVisual {
  visual_id: str
  visual_kind: "time_series"
  title: str
  scope_classification: "current_scope" | "historical_supporting_context"
  x_axis: { label: str, type: "datetime" | "snapshot_index" }
  y_axis: { label: str, unit: str | None }
  series: tuple[{
    series_label: str
    metric_name: str
    points: tuple[{ x: str | number, y: number | None, evidence_ref_label: str }, ...]
  }, ...]
  minimum_point_count: integer
  interpolation_allowed: false
  synthetic_data_allowed: false
  provenance: ProvenanceBlock
  unavailable_state: UnavailableVisualState | None
}
```

```text
DistributionVisual {
  visual_id: str
  visual_kind: "distribution"
  title: str
  scope_classification: "historical_supporting_context" | "comparative_output"
  metric_name: str
  groups: tuple[{
    group_label: str
    n: integer
    values: tuple[number, ...]
    quartiles: { q1: number, median: number, q3: number } | None
    evidence_ref_label: str
  }, ...]
  synthetic_data_allowed: false
  provenance: ProvenanceBlock
  unavailable_state: UnavailableVisualState | None
}

ViolinVisual {
  visual_id: str
  visual_kind: "violin"
  distribution: DistributionVisual
  density_method: "deterministic_kernel" | "precomputed_density"
  density_points: tuple[{ group_label: str, x: number, density: number }, ...]
  synthetic_data_allowed: false
}
```

```text
ComparisonDeltaVisual {
  visual_id: str
  visual_kind: "comparison_delta"
  title: str
  scope_classification: "comparative_output"
  target_a: { label: str, evidence_ref_label: str }
  target_b: { label: str, evidence_ref_label: str }
  delta_rows: tuple[{
    metric_label: str
    target_a_value: number | str | None
    target_b_value: number | str | None
    delta_value: number | str | None
    delta_unit: str | None
    direction_label: "higher" | "lower" | "unchanged" | "not_comparable"
    interpretation: str
    evidence_ref_label: str
  }, ...]
  synthetic_data_allowed: false
  provenance: ProvenanceBlock
  unavailable_state: UnavailableVisualState | None
}
```

```text
UnavailableVisualState {
  state_id: str
  reason_code: str
  title: str
  message: str
  required_contract: str | None
  missing_fields: tuple[str, ...]
  scope_classification: str | None
  prohibited_substitutes: tuple["generated_html" | "browser_cache" | "llm_text" | "static_fake_visual" | "allowed_visualizations", ...]
  next_deterministic_step: str | None
}
```

## 11. Tests that must be written before implementation

Create failing tests before any renderer or `html_dashboard.py` implementation.
The current renderer chain should fail these tests.

Required test groups:

1. Product view model shape tests:
   - `Screen3DiagnosticSnapshotViewModel` rejects raw dict/list-only product fields.
   - `Screen4EvidenceReviewViewModel` requires per-mode scope classification.
   - `Screen5RecommendationActionViewModel` requires deterministic recommendation refs.
   - `Screen6LearningGovernanceViewModel` requires persisted governance refs.

2. Product renderer safety tests:
   - Fails for raw dict/list/`<pre>` output.
   - Fails for flattened debug text such as `{ key: value }` or `[item, item]` in product panels.
   - Fails for internal IDs in the first fold.
   - Fails for `selected_flow_id` or `evidence_pack_id` in primary product UI.
   - Fails for `allowed_visualizations` as product UI.
   - Fails for fake/static visuals that are not backed by `TimeSeriesVisual`, `DistributionVisual`, `ViolinVisual`, or `ComparisonDeltaVisual`.

3. Screen 3 scope tests:
   - Fails when a single-AWR Diagnostic Snapshot is contaminated by multi-snapshot explanation.
   - Fails when trend name and point count replace current-scope evidence review.
   - Fails when generated HTML is used as diagnostic proof.

4. Screen 4 mode-boundary tests:
   - Fails when historical context is represented as selected-scope truth.
   - Fails for Target A/B fabrication.
   - Fails for Deep Analysis fabrication.
   - Fails when comparative rows render as Deep Analysis current-scope evidence.
   - Fails when `allowed_visualizations` creates chart evidence instead of only permitting an eligible renderer.

5. Screen 5 recommendation authority tests:
   - Fails for LLM-created recommendations.
   - Fails when browser selection creates recommendation/action state.
   - Fails when generated HTML is treated as recommendation evidence.

6. Screen 6 governance tests:
   - Fails when memory recall is treated as learning approval.
   - Fails when materialization or runtime eligibility is inferred from UI/cache.
   - Fails when LLM output approves governance state.

7. Acceptance-source tests:
   - Fails when generated HTML is treated as truth.
   - Fails when browser/localStorage/cache is treated as truth.
   - Fails when old phase notes are treated as current executable state.
   - Fails when LLM explanation is treated as evidence.

## 12. Explicit recommendation

Do not continue the failed renderer patch chain.

Do not start `src/reporting/html_dashboard.py` decomposition until product
contracts are reviewed and approved.

Recut screen-specific product renderers only after this document is reviewed
and approved. The recut should start with failing tests, then approved product
view models, then renderers, and only then shell integration.
