# Phase 7 Screen 4 Evidence Review Mode Shell

## 1. Purpose

Screen 4 is the Evidence Review shell for the dashboard. It is the operator's place to inspect supporting evidence behind deterministic analysis, including historical context today and future deterministic comparison and deep evidence review when those outputs exist.

The visible product role is `Screen 4 - Evidence Review`. The existing generated artifact and model names may remain `screen_4_historical_review.html` and `screen_4_historical_review` for compatibility during 7CV.

## 2. Non-Goals

This shell contract does not change diagnosis, scoring, severity, confidence, recommendation generation, parser behavior, database behavior, provider behavior, Phase 4I output shape, Phase 6 schema, generated dashboard artifact names, routes, screen ids, or cache keys.

This contract does not implement comparison runtime, comparison violin diagrams, Historical Review internals beyond the existing historical view, Comparative Review internals, Deep Analysis internals, provider routes, governed writes, learning materialization, runtime activation, or Phase 8 sizing, what-if, TCO, predictive, EMCC, or OEM behavior.

## 3. 7CV-A Baseline

7CV-A confirmed that Screen 4 already appears as `Screen 4 - Evidence Review` with nav label `4 Review`, while the implemented behavior remains mostly historical review.

Screen 4 does not compute A-vs-B comparison, assign comparison readiness, decide improvement or degradation, render comparison violin diagrams, or expose a Screen 4-specific provider route. Existing Screen 4 cache behavior is continuity only. Shared dashboard JavaScript can contain Screen 2 and Screen 3 route or Target A/B strings, but those strings are not Screen 4 ownership unless Screen 4 renders visible controls or invokes a Screen 4 route.

7CV-C added a static/local Screen 4 mode selector shell. Historical Review is active. Comparative Review remains prepared-only until deterministic comparison output exists. Deep Analysis remains reserved until future structured expert evidence review exists. The selector does not call backend or provider routes and does not persist state.

7CV-E adds only a Screen 2-to-Screen 4 handoff placeholder. Comparative Review may display that Target A/B context is prepared in Screen 2, but prepared targets are selected context only and do not create comparison evidence.

7CX-B adds a guarded Comparative Review state model. Prepared comparison context, route state, cache state, loose artifact references, Screen 3 prepared-only context, and 7CC metadata do not make Screen 4 output-ready. Only a strict Screen 4 deterministic comparison output contract can enter `comparison_output_ready`.

## 4. Screen 4 Role Contract

Screen 4 owns supporting evidence review. It may show deterministic evidence, governed historical context, selected runtime context, historical trend/anomaly/similarity context, and unavailable-state placeholders for future governed evidence review.

Screen 4 must not change diagnosis, score, severity, confidence, recommendations, parser mappings, Phase 4 truth, Phase 4I payload shape, Phase 6 schema, runtime behavior, future-run behavior, or learning materialization state.

Screen 4 must not treat browser cache, UI state, or LLM wording as evidence truth. It must not compute A-vs-B comparison in the browser, assign comparison readiness, decide improvement/degradation, create deterministic output, or execute re-analysis.

### Cross-Screen Runtime Rule

Screens 3-6 must vary by the source, run, scope, target, and comparison-preparation context selected in Screens 1-2. That variation is presentation and context selection only unless a governed backend workflow explicitly owns the behavior.

Screen 1 may establish new-source intake, parser/source governance, artifact readiness, validation, parser unknown/discovered element, and evidence handoff eligibility context. Screen 2 may establish existing platform evidence, selected run, selected runtime scope, selected target, Target A/Target B preparation, comparison readiness preparation, runtime-control context, and cache continuity context.

Screen 4 may reflect this upstream context so the operator reviews the relevant evidence surface. Screen 4 must label selected context as selected context, not truth. UI state, browser cache, and LLM wording must not change deterministic truth, diagnosis, scores, severity, confidence, recommendations, comparison results, learning state, materialization, runtime eligibility, or runtime behavior.

## 5. Mode Shell Model

### Historical Review

Purpose: review historical trend, anomaly, baseline, time-window, distribution, and similarity context.

Current state: mostly implemented as read-only historical review using deterministic/report-derived evidence and local exploratory selectors.

Allowed now: historical scope, current selection context, selected source/run/scope/target display context, trend review, anomaly review, baseline context, historical distributions, derived metrics, topology/platform context, similarity evidence, safe empty states, and disabled historical workflow previews.

Unavailable now: active historical workflow execution, official baseline selection, trend/anomaly approval, prior recommendation/outcome history as authoritative evidence unless governed data is explicitly available, and learning activation.

Future owner: 7CW.

Prohibited behavior: create historical truth from cache, infer trend changes without deterministic output, mutate run history, activate learning, replace deterministic trend/anomaly output, decide recommendation outcomes, or own Screen 5 action/outcome workflow.

### Comparative Review

Purpose: review deterministic Target A-vs-B comparison evidence after deterministic comparison output exists.

Current state: guarded state shell only. No active Screen 4 A-vs-B comparison output is rendered today unless a strict Screen 4 deterministic comparison output contract validates successfully.

Allowed now: unavailable, prepared-only, evidence-required, output-required, and output-ready state copy; neutral Target A/B identity display as preparation only; and ownership wording that reserves future comparison evidence and comparison violin panels for Screen 4. Target A/B is prepared comparison context only until deterministic comparison output is returned to Screen 4.

Unavailable now: target deltas, domain deltas, wait/event deltas, SQL deltas, topology/platform deltas, improvement/degradation/stable labels, comparison result summaries, and comparison violin diagrams.

Future owner: 7CX.

Prohibited behavior: compute comparison results in the browser, decide improvement/degradation without deterministic comparison output, assign comparison readiness, synthesize A-vs-B deltas, change Screen 3 diagnosis, change recommendations, render comparison violin diagrams as truth before deterministic comparison data exists, or treat 7CC metadata as Screen 4 output-ready without a future strict adapter.

The 7CX-B states are:

| State | Meaning | Allowed action |
| --- | --- | --- |
| `comparison_unavailable` | No useful prepared comparison context and no validated deterministic comparison output. | Prepare Target A/B context upstream. |
| `comparison_prepared_only` | Target A/B or comparison setup exists, but no validated deterministic comparison output exists. | Display neutral prepared Target A/B identity/context only. |
| `comparison_evidence_required` | Targets are selected, but persisted structured evidence is missing. | Prepare governed evidence before requesting output. |
| `comparison_output_required` | Comparison-ready evidence or workflow metadata exists, but no Screen 4 deterministic output contract was returned. | Return governed deterministic comparison output to Screen 4. |
| `comparison_output_ready` | Strict deterministic comparison output contract validates. | Display contract-backed comparative evidence only; graphics remain gated by `allowed_visualizations`. |

### Deep Analysis

Purpose: provide expert DBA evidence review for detailed AWR evidence in a structured way.

Current state: no explicit Deep Analysis mode. Some high-level evidence is present in Screen 4, such as DB time, I/O, commit, memory, RAC, ADG, topology/platform, derived metrics, and limited top-SQL availability.

Allowed now: scope definition, selected source/run/scope context wording, and unavailable/preview-only placeholder language only. Existing high-level deterministic evidence may continue to appear inside Historical Review.

Unavailable now: raw evidence drilldown, parser-discovered section drilldown, deep waits/events drilldown, top SQL investigation workflow, and expert panels that bypass deterministic analysis.

Future owner: 7CY.

Prohibited behavior: bypass deterministic analysis, diagnose directly from raw evidence, rewrite recommendations, add ungoverned scoring, allow LLM diagnosis/classification, mutate parser/source governance state, approve parser mappings, or own Screen 1 parser/source governance.

## 6. Truth and State Boundary

Deterministic evidence comes from Phase 4I output, deterministic analysis artifacts, and deterministic scoring/trend/similarity/recommendation engines. It is authoritative for Screen 4 display. Examples include `metadata`, `decision`, `scores`, `trends`, `similarity_intelligence`, `recommendations`, canonical findings, deterministic domain evidence, deterministic trend/anomaly evidence, and deterministic similarity evidence generated by Phase 4. Recommendation generation remains owned by `src/analysis/recommendation_engine.py` through `generate_decision_recommendations`.

Governed persisted context comes from Phase 6/7 persistence where available. It is authoritative only for its own governed record. It may provide historical run, recommendation history, action history, outcome history, feedback history, parser governance records, learning governance records, materialization records, or runtime eligibility records, but it must not override deterministic diagnosis, scores, recommendations, or comparison truth.

Selected runtime context comes from Screen 1 source intake/source-governance handoff and Screen 2 runtime scope, selected source, selected run, selected target, Target A/Target B preparation, selected comparison context, or selected evidence scope. It is a context selector only. It may determine what Screen 4 displays, but it must not become evidence truth by itself and must not create diagnosis, scores, readiness, deltas, recommendations, actions, outcomes, or learning state.

Browser cache continuity comes from localStorage, hash state, or session continuity. It is display continuity only. It cannot create evidence, update evidence, determine readiness, or overwrite deterministic/governed truth.

Future unavailable output refers to planned deterministic comparison or future deep-analysis artifacts that are not active. It must be labeled unavailable, future, prepared-only, or pending deterministic output.

LLM explanatory wording is wording only. It may explain already-computed, already-selected, already-validated, already-recorded, or already-governed meaning, but it must not create evidence, classify evidence, diagnose, score, recommend, compare targets, persist records, activate runtime behavior, or change future-run behavior.

Strict deterministic comparison output for Screen 4 must carry `screen4_contract_type=deterministic_comparison_output`, `comparison_id`, `baseline_run_id`, `candidate_run_id`, `source_scope`, `comparison_scope`, `generated_by=deterministic_engine`, `generated_at`, `deterministic_engine_version`, `metric_deltas`, `domain_deltas`, `evidence_rows`, `confidence_basis`, `missing_evidence`, and `allowed_visualizations`. Empty metric/domain deltas are allowed only when the contract carries evidence rows or an explicit deterministic empty-evidence/no-change explanation.

Wording rule: reserve `comparison` language for prepared Target A/B context, deterministic comparison output, Comparative Review state names, and explicitly gated future comparison visualizations. Historical RAC, Data Guard, topology, period, baseline, and distribution content should use supporting context, historical supporting context, topology supporting context, RAC supporting context, Data Guard supporting context, period context, or broader historical context. Target A/B preparation alone does not create Screen 4 comparison evidence.

## 7. Screen Boundary Matrix

| Screen | Owner role | Allowed handoff to Screen 4 | Prohibited overlap |
| --- | --- | --- | --- |
| Home / Index | Platform entry and source intake | Source/run context already selected by the operator | Screen 4 must not own platform entry or source intake |
| Screen 1 | Ingestion, parser, source governance, unknowns, mappings, artifact readiness | Governed source/artifact readiness context | Screen 4 must not approve mappings, mutate parser state, or own source governance |
| Screen 2 | Runtime scope, existing evidence loading, Target A/B selection, comparison readiness preparation | Selected source/run/scope and future comparison-prepared context | Screen 4 must not assign readiness, select Target A/B, or own runtime-control requests |
| Screen 3 | Diagnostic Snapshot and selected target individual deterministic explanation | Deterministic diagnosis and selected target context for evidence review | Screen 4 must not change diagnosis, score, severity, confidence, or recommendations |
| Screen 4 | Evidence Review shell | Historical, future comparative, and future deep evidence review | Screen 4 must remain read-only until later governed workflows explicitly activate behavior |
| Screen 5 | Recommendation action, owner/status, validation checklist, outcome capture | Evidence context that may support operator action review | Screen 4 must not create actions, record outcomes, validate actions, or own recommendation truth |
| Screen 6 | Learning governance, candidate review, materialization, runtime eligibility | Governed learning context only when available and clearly labeled | Screen 4 must not materialize candidates, approve runtime eligibility, or activate learning |

### Screen 1 and Screen 2 Handoff to Screen 4

Screen 1 may pass or display selected/new source context, generated artifact readiness context, parser/source-governance handoff state, source validation context, evidence handoff eligibility, and parser-discovered or unknown signal context only as governed/source context. Screen 4 must not treat unapproved parser mappings, ungoverned unknown signal interpretations, raw parser discoveries, source validation state, or artifact readiness as scoring truth or diagnosis.

Screen 2 may pass or display selected existing evidence/run context, selected runtime scope, selected target context, Target A/Target B preparation context, comparison readiness prepared by Screen 2, runtime-control context, and selected evidence mode/context. Screen 4 must not treat comparison readiness as comparison evidence, a UI-selected target as a diagnosis change, cache-restored selection as authoritative backend truth, or any comparison result, improvement/degradation/stable label, or domain delta as truth unless strict deterministic comparison output exists.

Screen 4 uses the handoff to vary the visible review context. It may show prepared comparison context that says Target A/B context comes from Screen 2, deterministic comparison output is required before comparison evidence can be reviewed, selected targets and cache-restored state do not create comparison evidence, and Screen 4 does not compute comparison in the browser. It remains read-only and does not mutate upstream source governance, runtime scope, target selection, comparison readiness, deterministic output, recommendations, action/outcome state, or learning governance.

## 8. Current vs Future Capability Map

| Capability | Current state | Truth source | Future workstream | Guardrail |
| --- | --- | --- | --- | --- |
| Historical trend review | Present | Deterministic trends/report data | 7CW | No trend recalculation |
| Anomaly timeline | Present/partial | Deterministic anomaly output | 7CW | No anomaly reclassification |
| Baseline context | Present as historical context | Deterministic/report comparison context | 7CW | Do not imply A-vs-B output |
| Similarity evidence | Present | `similarity_intelligence` and governed data where available | 7CW | No nearest-neighbor recomputation in UI |
| Prior recommendations/actions/outcomes | Mostly absent | Governed persistence only if available | 7CW | Must not become Screen 5 ownership |
| Target A/B comparison | Guarded state shell only | Future strict Screen 4 deterministic comparison output | 7CX | No browser-side comparison |
| Domain deltas | Absent | Future deterministic comparison output | 7CX | No synthesized deltas |
| Wait/event deltas | Absent | Future deterministic comparison output | 7CX | No synthesized deltas |
| SQL deltas | Absent | Future deterministic comparison output | 7CX | No synthesized deltas |
| Topology/platform deltas | Absent | Future deterministic comparison output | 7CX | No synthesized deltas |
| Comparison violin diagrams | Absent | Future deterministic comparison output | 7CX | Screen 4 owns future rendering, but none in 7CV |
| Raw evidence drilldown | Absent | Future governed parser/deterministic evidence contract | 7CY | Do not bypass deterministic diagnosis |
| Parser-discovered sections/elements | Absent | Screen 1/parser governance | 7CY | No parser governance mutation |
| LLM explanatory wording | Limited/common route only | Approved provider/service path if used | Future wording-only task if needed | No evidence creation or decisions |

## 9. Comparison and Violin Ownership

Screen 2 prepares Target A/B and comparison readiness. Screen 3 explains a selected Target A or Target B individually. Screen 4 owns future deterministic A-vs-B evidence review after deterministic comparison output exists.

Screen 4 owns future comparison violin panels. 7CX-B does not implement comparison violin diagrams, comparison violin data, comparison runtime, or comparison output rendering. Even after output-ready, graphics may render only when the specific visualization is present in `allowed_visualizations`.

Existing Screen 4 workload distribution violins are historical/supporting distribution evidence, not A-vs-B comparison violin diagrams.

7CC comparison execution metadata requires a future adapter before Screen 4 can render it. A comparison artifact reference, output reference, or 7CC metadata payload is not sufficient by itself.

## 10. LLM / Provider Boundary

7CV-B through 7CV-D add no Screen 4 provider route. Existing common Screen 2 explanation plumbing remains outside Screen 4 ownership unless Screen 4 renders visible controls and an approved route in a later task.

Future LLM wording on Screen 4 may explain already-computed deterministic evidence, governed persisted context, or validated deterministic comparison output after that output exists. It must not create evidence, choose evidence, validate evidence, decide comparison outcome, score, diagnose, recommend, persist records, or mutate workflow state.

## 11. Cache / State Boundary

Cache is continuity only. Screen 4 may use browser-local state to restore selected source/run context or local evidence-review selection highlights.

Cache cannot create evidence, determine comparison readiness, create comparison output, change deterministic diagnosis, change recommendation truth, overwrite governed persistence, or fabricate Historical, Comparative, or Deep Analysis state.

Stale cache must yield unavailable or refresh-needed wording rather than evidence claims.

## 12. Product Copy Guidance

Use `historical baseline context` or `historical period context` when referring to existing multi-snapshot or latest-vs-prior review. Reserve `Comparative Review` and `Target A-vs-B` for deterministic comparison output.

Avoid `Learning Preview` wording when it could imply Screen 6 ownership. Prefer `Historical Review Workflow Preview` or `Evidence Review Notes Preview` for disabled Screen 4 concepts.

Keep visible product language aligned to `Evidence Review` while preserving technical artifact compatibility with `screen_4_historical_review.html`, `screen_4_historical_review`, existing routes, existing screen ids, and existing cache keys.

Do not treat shared JavaScript search hits as ownership evidence. Ownership requires Screen 4 visible controls, Screen 4 route invocation, or Screen 4-specific source rendering.

## 13. 7CV-D / 7CV-E Readiness Criteria

7CV-D may safely clarify the shared evidence context contract through documentation, compact Screen 4 wording, and focused tests only. It must keep selected runtime context, browser cache continuity, and LLM wording separate from deterministic evidence and governed persisted truth.

7CV-D must not add a backend route, comparison computation, comparison violin implementation, deep analysis internals, artifact rename, route rename, screen id rename, cache key rename, provider route, or generated comparison truth.

7CV-E may add a Screen 2-to-Screen 4 handoff placeholder only if it displays prepared Target A/Target B context without claiming comparison output exists. Comparative Review must render unavailable/prepared-state copy until deterministic comparison output exists. Deep Analysis must render unavailable/preview-only scope copy until 7CY. Historical Review may continue existing content without changing its current behavior.

If `src/reporting/html_dashboard.py` changes during 7CV-E or later 7CV work, generated dashboard artifacts must be refreshed through the source dashboard generation flow using `.venv/bin/python`. Manual generated-HTML patching must not be the only artifact update.

Tests should verify no mutation, no provider route, no comparison truth claims, no comparison readiness assignment, no comparison violin rendering, and no Screen 3/5/6 boundary drift.

## 14. Deferrals

7CW owns Historical Review internals.

7CX owns Comparative Review internals, deterministic comparison evidence rendering, A-vs-B deltas, deterministic improvement/degradation/stable labels when available, and comparison violin panels.

7CY owns Deep Analysis internals, expert DBA evidence panels, raw evidence drilldown, governed parser-discovered section display, and detailed AWR evidence review.

7DD or later owns any runtime execution activation where explicitly governed.

Phase 8 owns sizing, what-if advisory, TCO, predictive analytics, EMCC expansion, and OEM expansion.
