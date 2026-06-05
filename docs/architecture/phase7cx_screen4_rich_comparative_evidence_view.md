# Phase 7CX Screen 4 Rich Comparative Evidence View Design

## Purpose

Screen 4 Comparative Review is an evidence review surface for already-adapted deterministic comparison output. It displays backend deterministic comparison evidence only after the strict Screen 4 deterministic comparison output contract validates.

Comparative Review does not prepare targets, execute comparison, compute deltas in the browser, dereference artifacts in the browser, create diagnosis truth, change scoring, create recommendations, create actions, record outcomes, or mutate learning state. It renders dynamically from available validated contract data only.

## Scope and Non-Scope

This document designs the future product-grade Comparative Review view. It does not implement rendering, charts, violins, A/B overlays, backend routes, Build Comparison actions, browser computation, dashboard regeneration, or `html_dashboard.py` decomposition.

Every future section must use one of three render states:

1. Render populated evidence when the required contract fields exist and `allowed_visualizations` permits the section when applicable.
2. Render a meaningful blocked or empty explanation only when the absence itself is useful to the operator and identifies the missing field, prerequisite, or action.
3. Omit the section entirely when it has no useful evidence and no operator-relevant blocked explanation.

Forbidden future behavior: static examples, hard-coded rows, fake deltas, placeholder conclusions, empty cards, empty tables, empty chart containers, placeholder graphs, generic filler panels, and evidence-looking "coming soon" panels.

## Prerequisites

The existing 7CX-B state model remains unchanged:

- `comparison_unavailable`
- `comparison_prepared_only`
- `comparison_evidence_required`
- `comparison_output_required`
- `comparison_output_ready`

The rich view may render only inside `comparison_output_ready`, after the strict deterministic comparison output contract validates. Prepared Target A/B context, cache, route state, loose 7CC metadata, and artifact references remain non-output states.

## Dynamic Output Rule

All Comparative Review content must be derived from the validated contract. The renderer must not create comparison facts, direction labels, metric rows, category availability, confidence, missing evidence, or visualization eligibility.

The rendering algorithm should:

1. Validate the Screen 4 contract.
2. Read `allowed_visualizations`.
3. Build section eligibility from contract fields.
4. Render populated sections first.
5. Render concise blocked explanations only when useful and not already covered elsewhere.
6. Omit all other sections.

No section should exist merely to fill space.

## Contract Field Families

Identity and provenance:

- `comparison_id`
- `validation_status`
- `generated_by`
- `generated_at`
- `deterministic_engine_version`
- `adapter_version`
- `contract_version`
- `artifact_source`
- `workflow_request_id`
- `workflow_transaction_id`
- `comparison_execution_id`
- `artifact_reference`
- `generated_from_hash`

Target identity:

- `target_a_identity`
- `target_b_identity`
- `baseline_run_id`
- `candidate_run_id`
- `target_alignment`
- `input_snapshot_range`
- `source_scope`
- `comparison_scope`

Evidence:

- `metric_deltas`
- `domain_deltas`
- `evidence_rows`
- `confidence_basis`
- `missing_evidence`
- `adapter_validation_messages`
- `allowed_visualizations`
- optional `no_change_evidence`
- optional future time-series rows
- optional future distribution/sample rows

## Layout Layers

The future view should render in this order when eligible:

1. Contract / Readiness Banner
2. Target A vs Target B Identity Summary
3. Evidence Completeness Matrix
4. Domain Delta Summary
5. Metric Delta Table
6. Wait/Event Movement Table
7. SQL Movement Table
8. Confidence Basis Panel
9. Missing Evidence / Limitations Panel
10. Visualization Eligibility Panel
11. Future Time-Series Overlay
12. Future Distribution / Violin Panel
13. LLM Explanation Boundary Panel

Sections should be compact, operational, and scannable. Repeated empty states should collapse into one Missing Evidence or Visualization Eligibility explanation.

## Section Design

| Section | Purpose | Render condition | Required fields | Required `allowed_visualizations` | Populated state | Blocked/empty state | Omission rule | Forbidden fallback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Contract / Readiness Banner | Show output is adapted and validated. | `comparison_output_ready` and validated contract. | `comparison_id`, `validation_status`, `generated_by`, `generated_at`, `deterministic_engine_version`, `adapter_version`, `contract_version`, `artifact_source`. | None. | Show comparison id, timestamp, deterministic engine marker, adapter version, contract version, validation status, workflow ids when present. | None inside output-ready; missing required fields should keep parent state non-output-ready. | Omit when contract is not validated. | Do not render from cache, route, or workflow metadata alone. |
| Target A vs Target B Identity Summary | Show exactly what was compared. | `target_a_identity` and `target_b_identity` exist and `target_alignment.status=aligned`. | target identities, `baseline_run_id`, `candidate_run_id`, `target_alignment`, `source_scope`, `comparison_scope`, `input_snapshot_range`. | None. | Two cards: Target A / Baseline and Target B / Candidate. Show only present fields. | None inside output-ready; missing identities keep contract invalid. | Omit absent optional fields. | Do not infer identity from browser state or show conclusions in identity cards. |
| Evidence Completeness Matrix | Show available, partial, missing, not applicable, or blocked categories. | Evidence or missing/adapter messages contain category information. | `evidence_rows`, `missing_evidence`, `confidence_basis`, `adapter_validation_messages`, `allowed_visualizations`. | Optional future `evidence_completeness_matrix`. | Show category, status, row count, missing count, and blocked visualization impact. | If missing evidence itself is useful, render concise missing explanation. | Omit categories with neither evidence nor missing/blocked explanation. | Do not show an empty matrix or mark categories available without evidence rows. |
| Domain Delta Summary | Summarize by domain without unsupported outcome claims. | `domain_delta_summary` allowed and `domain_deltas` has rows, or explicit no-domain evidence exists. | `domain_deltas`, supporting `evidence_rows`, `confidence_basis`. | `domain_delta_summary`. | Show domain, evidence count, change basis, affected metrics, limitations. | If allowed but empty, explain that `domain_deltas` is empty or only non-domain evidence exists. | Omit when not allowed unless Visualization Eligibility explains why. | Do not invent domain summaries or infer dominance from metric names without contract support. |
| Metric Delta Table | Show normalized Target A vs Target B metric differences. | `metric_delta_table` allowed and `metric_deltas` has rows, or explicit no-delta evidence exists. | `metric_deltas`, supporting `evidence_rows`. | `metric_delta_table`. | Columns: metric label, domain/category, Target A value, Target B value, delta value, delta percent, unit, evidence source, notes/limitations. Omit optional columns when empty across all rows. | If allowed but empty and no explicit no-delta evidence exists, render a concise explanation unless already covered by Missing Evidence. | Omit when not allowed unless Visualization Eligibility explains why. | No sample rows, fake metric rows, or generic A/B change claims. |
| Wait/Event Movement Table | Show wait/event movement only with stable identity. | Wait/event visualization allowed and rows include stable event/wait identity. | wait/event `evidence_rows`, `missing_evidence`. | `wait_class_movement_table` or `top_event_movement_table`. | Show event/wait identity, Target A value, Target B value, delta, unit, evidence source, notes. | If allowed but stable identity is missing, explain the missing identity. | Omit when not allowed unless Visualization Eligibility explains why. | Do not render empty wait/event tables or group unrelated waits without contract identity. |
| SQL Movement Table | Show SQL movement only with stable SQL identity. | `top_sql_movement_table` allowed and rows include stable SQL identity. | SQL `evidence_rows`, `missing_evidence`. | `top_sql_movement_table`. | Show SQL identity, Target A metric, Target B metric, delta, unit, source, limitations. | If allowed but stable SQL identity is missing, explain the missing identity. | Omit when not allowed unless Visualization Eligibility explains why. | Do not render empty SQL tables or match SQL by label alone. |
| Confidence Basis Panel | Explain deterministic basis. | `confidence_basis_panel` allowed, or `confidence_basis` exists and is operator-relevant. | `confidence_basis`. | `confidence_basis_panel` when treated as a visual asset. | Show `basis_type`, `sample_count`, `evidence_row_count`, `missing_evidence_count`, and limitations. | Missing `confidence_basis` keeps output non-ready; do not render empty panel. | Omit empty optional fields. | Do not generate confidence from LLM or UI. |
| Missing Evidence / Limitations Panel | Make gaps visible. | `missing_evidence` non-empty or adapter messages contain limitation/blocking messages. | `missing_evidence`, `adapter_validation_messages`, `confidence_basis.limitations`. | `missing_evidence_panel` when treated as a visual asset. | Show category, field, reason, impact, blocked visualization if available. | If empty, optionally show no missing evidence only when useful and not redundant. | Omit if empty and not useful. | Do not invent missing evidence. |
| Visualization Eligibility Panel | Explain available or blocked visuals. | Allowed visuals exist, or blocked visual explanation is useful. | `allowed_visualizations`, `missing_evidence`, `evidence_rows`, `confidence_basis`, `adapter_validation_messages`. | None; it explains permissions. | Show allowed visualizations and meaningful blocked reasons. | Do not list every blocked visual unless helpful. | Omit if it duplicates other blocked messages. | No visual shells or "coming soon" placeholders. |
| Future Time-Series Overlay | Define future graph behavior. | Future only: allowed and aligned time-series evidence exists. | timestamp, metric key, Target A value, Target B value, unit, alignment basis. | `time_series_overlay`. | Render overlay from aligned points only. | "Time-series overlay is blocked because aligned time-series evidence is not present in this deterministic comparison output." | Omit if not allowed and not useful. | No synthetic series from summary deltas or snapshot identity alone. |
| Future Distribution / Violin Panel | Define future violin behavior. | Future only: allowed and distribution/sample evidence exists. | metric key, Target A sample set, Target B sample set, sample values or buckets, unit, sample count. | `distribution_violin`. | Render violin from actual samples only. | "Distribution violin is blocked because this deterministic comparison output does not include distribution sample rows." | Omit if not allowed and not useful. | No violin from summary deltas, empty containers, or synthetic samples. |
| LLM Explanation Boundary Panel | Keep explanation separate from truth. | Comparative explanation exists or planned and a boundary note is useful. | validated contract presence. | None. | "LLM-assisted wording may explain validated deterministic comparison output only after that output exists. It does not compute comparison meaning or decide outcome direction." | Omit if redundant. | No LLM-created deltas, direction labels, evidence rows, or confidence. |

## Evidence Completeness Categories

Allowed category statuses:

- `available`
- `partial`
- `missing`
- `not applicable`
- `blocked`

Categories:

- score
- wait
- sql
- trend
- anomaly
- topology
- platform
- availability
- time_series
- distribution

A category may be `available` only when matching evidence rows exist. It may be `partial` when both evidence rows and missing evidence exist. It may be `blocked` when missing identity, missing samples, missing aligned time points, or missing visualization permission prevents rendering. It may be omitted when it has no evidence and no useful absence explanation.

## allowed_visualizations Mapping

| Visualization | Required value | Required contract fields | Required evidence shape | Blocked wording | Omission rule | Forbidden fallback |
| --- | --- | --- | --- | --- | --- | --- |
| Metric Delta Table | `metric_delta_table` | `metric_deltas`, `evidence_rows` | Metric rows with Target A/B values and metric key. Explicit no-delta evidence may support a concise no-row explanation. | "Metric delta table is unavailable because this comparison output does not include `metric_deltas`." | Omit when not allowed and already explained. | No static rows or fake deltas. |
| Domain Delta Summary | `domain_delta_summary` | `domain_deltas`, `evidence_rows`, `confidence_basis` | Domain rows with evidence count and affected metrics. | "Domain summary is unavailable because this comparison output does not include `domain_deltas`." | Omit when not allowed and not useful. | No inferred domain dominance. |
| Evidence Completeness Matrix | `evidence_completeness_matrix` when formalized | `evidence_rows`, `missing_evidence`, `confidence_basis` | Category counts, missing counts, and meaningful blocked reasons. | "Evidence completeness is unavailable because the contract has no evidence or missing-evidence category data." | Omit when empty. | No empty matrix. |
| Confidence Basis Panel | `confidence_basis_panel` | `confidence_basis` | Deterministic basis, sample count, evidence count, missing count, limitations. | None inside output-ready. | Omit empty optional fields. | No UI or LLM confidence. |
| Missing Evidence Panel | `missing_evidence_panel` | `missing_evidence`, limitations/messages | Missing field/category rows or limitation messages. | None when empty; omit instead. | Omit when empty and not useful. | No invented missing evidence. |
| Time-Series Overlay | `time_series_overlay` | future time-series rows | Timestamp, metric key, Target A value, Target B value, unit, alignment basis. | "Time-series overlay is blocked because aligned time-series evidence is not present in this deterministic comparison output." | Omit when not allowed and not useful. | No synthetic time series. |
| Distribution Violin | `distribution_violin` | future distribution/sample rows | Metric key, samples or buckets, Target A sample set, Target B sample set, unit, sample count. | "Distribution violin is blocked because this deterministic comparison output does not include distribution sample rows." | Omit when not allowed and not useful. | No violin from summary deltas. |
| Wait Class Movement Table | `wait_class_movement_table` | wait/event evidence rows | Stable wait class or event identity, Target A/B values, unit, source. | "Wait/event movement is blocked because stable wait/event identity is not present." | Omit when not allowed and not useful. | No empty wait table or loose grouping. |
| Top SQL Movement Table | `top_sql_movement_table` | SQL evidence rows | Stable SQL identity across Target A/B, metric key, values, unit, source. | "SQL movement is blocked because stable SQL identity is not present." | Omit when not allowed and not useful. | No SQL matching by label alone. |
| Top Event Movement Table | `top_event_movement_table` | event evidence rows | Stable event identity, Target A/B values, unit, source. | "Top event movement is blocked because stable event identity is not present." | Omit when not allowed and not useful. | No empty event table. |

## Rendering Capability Tiers

These tiers exist inside `comparison_output_ready`. They do not replace the 7CX-B state model.

| Tier | Derivation | Rendering capability |
| --- | --- | --- |
| `output_ready_table_only` | Valid contract plus table/panel permissions only. | Readiness banner, Target A/B identity, metric/domain tables when data exists, confidence, missing evidence. |
| `output_ready_summary_tables` | Metric and domain table permissions plus meaningful completeness data. | Table-focused summary with completeness and limitations. |
| `output_ready_with_time_series` | `time_series_overlay` allowed and aligned time-series rows exist. | Adds time-series overlay. |
| `output_ready_with_distribution` | `distribution_violin` allowed and distribution/sample rows exist. | Adds distribution/violin evidence. |
| `output_ready_with_sql_movement` | `top_sql_movement_table` allowed and stable SQL identity rows exist. | Adds SQL movement table. |
| `output_ready_with_full_visuals` | All required visual permissions and evidence shapes exist. | Rich tables, time series, distribution/violin, SQL/event movement, confidence, and missing evidence. |

If a higher tier lacks evidence shape despite an allowed visualization, the renderer should show a concise blocked explanation only when useful, otherwise omit.

## Wording and Conclusion Policy

Avoid outcome-direction labels unless the deterministic contract explicitly includes supported direction semantics and provenance:

- improved
- degraded
- stable
- better
- worse
- winner
- loser
- regression
- improvement

Prefer:

- delta
- difference
- evidence row
- available signal
- missing evidence
- limitation
- deterministic comparison output
- contract-supported direction label, if present

If future deterministic output includes direction labels, Screen 4 must display them as contract-supported deterministic labels with provenance, not UI-created claims.

## Blocked, Empty, and Omission Rules

Use a blocked/empty explanation only when it helps the operator understand why an expected evidence surface is unavailable. The message must name the missing contract field, evidence shape, or `allowed_visualizations` value.

Omit the section when absence carries no operator value or is already covered by Missing Evidence or Visualization Eligibility.

Never render:

- an empty table shell
- an empty chart shell
- an empty card
- a placeholder graph
- a generic future panel
- a static example
- a fake row

## LLM Boundary

LLM-assisted wording may explain validated deterministic comparison output only after that output exists. It must not create comparison facts, evidence rows, confidence, direction labels, visual eligibility, diagnosis, scoring, recommendation, action, outcome, or learning truth.

Any future LLM explanation panel must quote or summarize only contract-backed facts and should identify that deterministic output remains authoritative.

## Implementation Sequence

Recommended sequence after 7CX-E:

1. 7CX-F: Screen 4 Comparative Tables from Validated Contract.
2. 7CX-G: Screen 4 Comparative Graphs and Violins from Validated Contract.

Tables should come before graphs because current 7CX-D adapter output supports conservative table/panel permissions only. Graphs and violins require stronger evidence shapes such as aligned time-series points, distribution samples, stable SQL identity, and stable event identity.

Do not skip directly to graphics.

## html_dashboard.py Growth Controls

`html_dashboard.py` is already too large. Future implementation should avoid large monolithic additions, duplicated HTML/JS blocks, browser computation, static examples, empty blocks, generated placeholder charts, and visual shells.

If implementation must occur before 7DG, use small extraction-ready rendering helpers and keep data shaping outside the browser. Prefer future module seams:

- `src/reporting/dashboard/screen4/comparative_view.py`
- `src/reporting/dashboard/screen4/comparative_tables.py`
- `src/reporting/dashboard/screen4/comparative_visuals.py`
- `src/reporting/dashboard/screen4/comparative_empty_states.py`
- `src/reporting/dashboard/screen4/comparative_contract_rendering.py`

7CX-E does not implement these modules.

## Future Test Plan

Future tests should verify:

- Output-ready contract renders readiness banner.
- Target A/B identity cards render only populated fields.
- Empty identity fields are omitted.
- No empty identity cards render.
- `metric_delta_table` appears only when allowed and data exists.
- `metric_delta_table` shows blocked explanation only when useful.
- `metric_delta_table` is omitted when not useful.
- `domain_delta_summary` appears only when allowed and data exists.
- `confidence_basis_panel` appears only when confidence basis exists.
- `missing_evidence_panel` appears only when missing evidence or limitations exist.
- `distribution_violin` is blocked unless allowed and samples exist.
- No empty violin container renders.
- `time_series_overlay` is blocked unless allowed and aligned points exist.
- No empty overlay chart renders.
- SQL movement is blocked unless stable SQL identity exists.
- No empty SQL table renders.
- No forbidden conclusion labels appear unless contract-supported.
- LLM explanation panel cannot create comparison meaning.
- Cache-only and prepared-only states remain non-output states.
- No Screen 4 graphics render from page identity alone.
- No hard-coded sample rows exist in rendered Comparative Review.

## Documentation Cross-References

This design depends on:

- `docs/architecture/phase7cx_screen4_comparative_review_contract.md`
- `docs/architecture/phase7cx_screen4_comparison_output_adapter.md`
- `docs/architecture/phase7_screen4_evidence_review_mode_shell.md`
- `docs/architecture/phase7cc_comparison_execution.md`
- `docs/architecture/phase7am_awr_report_comparison_engine.md`
