# Phase 7CY Screen 4 Deep Analysis Mode Contract

## 1. Purpose

Screen 4 Deep Analysis Mode is a future deterministic current-scope evidence drilldown for the selected diagnostic output. It lets an operator inspect already-computed diagnostic evidence at a deeper level, such as diagnostic drivers, DB time components, waits, top SQL, topology/RAC/Data Guard details, metric breakdowns, and engineering detail, after a strict Screen 4 Deep Analysis contract validates.

Deep Analysis is a separate Screen 4 lane from Historical Review and Comparative Review. It may inspect and explain deterministic evidence already present in the current selected diagnostic output, `report_data`, `screen_model`, `chart_payload`, derived scalar metrics, time-series groups, distribution groups, evidence rows, and validated backend/display contracts. It does not create diagnostic truth.

## 2. Non-Goals

Deep Analysis does not generate a diagnosis, score, primary domain, severity, confidence, posture, recommendation, threshold, comparison output, fleet output, learning candidate, materialization decision, runtime execution, parser output, or new evidence.

Deep Analysis does not execute parsers, query Object Storage or OCI from the browser, call a comparison engine, call fleet review, create browser-side calculations, add a backend route, mutate runtime truth, or regenerate dashboard artifacts by itself.

Deep Analysis does not own Screen 3 Diagnostic Snapshot, Screen 5 recommendation action/outcome, Screen 6 learning/materialization, Screen 1 parser/source governance, Screen 2 runtime scope/Target A/B preparation, Historical Review, or Comparative Review.

## 3. Lane Separation

| Lane or context | Purpose | Deep Analysis relationship |
| --- | --- | --- |
| Historical Review | Same-DB historical trend, anomaly, distribution, period, baseline, and similarity support. | Historical data may appear only as labeled supporting context, never as primary current-scope proof. |
| Comparative Review | Deterministic Target A/B comparison output after the 7CX contract validates. | Comparative evidence remains Comparative Review only unless a future adapter explicitly relabels, rescope-validates, and proves it as Deep Analysis supporting context. |
| Prepared Target A/B | Screen 2/3 selected Target A/B identity and readiness preparation. | Prepared context cannot render as Deep Analysis evidence. |
| Fleet/population review | Population or fleet-wide evidence from a future fleet contract. | Not allowed in Deep Analysis without a separate fleet/population evidence contract. |
| Cache-only restoration | Browser localStorage, hash, or continuity state. | Continuity only; cannot render evidence or satisfy freshness. |
| LLM-only explanation | Wording about already validated facts. | May explain validated Deep Analysis content only after the contract exists; cannot create evidence or decide meaning. |
| Screen 3 Diagnostic Snapshot | Current deterministic diagnosis and selected target individual explanation. | Deep Analysis may reference immutable truth IDs from Screen 3, but cannot mutate them. |
| Screen 5 action/outcome | Recommendation execution, owner/status, validation, and outcome capture. | Deep Analysis cannot create actions, outcomes, or recommendation truth. |
| Screen 6 learning/materialization | Learning candidate review, materialization, runtime eligibility. | Deep Analysis cannot create candidates or activate learning/materialization. |

## 4. Scope Classification Model

Every Deep Analysis section and row must carry one scope classification.

| Classification | Primary Deep Analysis evidence | Supporting context | Required labeling | Rendering restrictions | Validation failure behavior |
| --- | --- | --- | --- | --- | --- |
| `current_scope` | Allowed when deterministic, fresh, and aligned to the selected diagnostic output. | Allowed. | "Current selected scope" or "Current Diagnostic Evidence". | May render populated evidence sections and rows after contract validation. | Missing provenance, stale freshness, or selected-scope mismatch blocks readiness. |
| `historical_supporting_context` | Not allowed as primary evidence. | Allowed when explicitly labeled. | "Historical Supporting Context" or "Supporting Evidence". | Must not claim current proof, new diagnosis, or current root cause. | If unlabeled or mixed with primary evidence, contract invalid. |
| `comparative_output` | Not allowed as primary evidence. | Not allowed by default. | "Comparative Review only" if referenced. | Must stay in Comparative Review unless future Deep Analysis adapter relabels and validates. | Primary use invalidates contract. |
| `prepared_only` | Not allowed. | Not allowed as evidence. | "Prepared context only" if shown in a blocked state. | No evidence rows, no charts, no conclusions. | Contract unavailable or output required. |
| `cache_only` | Not allowed. | Not allowed as evidence. | "Cache continuity only" if shown in a blocked state. | Cannot satisfy freshness or provenance; cannot render evidence. | Contract invalid or unavailable. |
| `fleet_population` | Not allowed without a future fleet contract. | Not allowed unless separate fleet contract exists and labels it. | "Fleet/population context" with contract reference. | No fleet diagrams or population visuals from page identity. | Blocks or returns `not_supported` without fleet contract. |
| `llm_explanation_only` | Not allowed. | Allowed only as wording after validated deterministic content exists. | "Analysis Explanation" or "LLM explanation only". | Cannot create rows, scope labels, chart eligibility, freshness, or conclusions. | Evidence row or section generated by LLM invalidates contract. |
| `unknown_or_mixed` | Not allowed. | Not allowed until split or relabeled. | "Unknown or mixed scope" in validation messages only. | No rendering as evidence. | Blocks readiness. |

Only `current_scope` deterministic evidence may become primary Deep Analysis evidence. Historical evidence may be supporting context only. Comparative evidence remains Comparative Review only. Prepared-only and cache-only context cannot render as Deep Analysis evidence. LLM text cannot create evidence.

## 5. Contract Object Design

The future contract should use a clearly separate type:

```json
{
  "contract_type": "screen4_deep_analysis_contract",
  "contract_version": "7cy.screen4.deep_analysis.v1",
  "generated_by": "deterministic_backend",
  "generated_at": "ISO-8601 backend timestamp",
  "deterministic_engine_version": "required",
  "source_scope": "current_selected_diagnostic_scope",
  "selected_run_id": "required when available",
  "selected_source_identifier": {},
  "selected_snapshot_identifier": {},
  "generation_context": {},
  "freshness": {},
  "provenance": {},
  "current_diagnostic_output_ref": {},
  "immutable_truth_refs": {},
  "evidence_sections": [],
  "evidence_rows": [],
  "chart_eligibility": [],
  "limitations": [],
  "missing_evidence": [],
  "validation_messages": [],
  "llm_explanation_boundary": {},
  "mutation_boundaries": {}
}
```

Required invariants:

- `contract_type` must equal `screen4_deep_analysis_contract`.
- `generated_by` must identify deterministic/backend contract generation, not browser, UI, cache, or LLM.
- `source_scope` must identify the current selected diagnostic scope, not prepared Target A/B, cache continuity, route state, fleet/population, or comparative output.
- `selected_run_id`, `selected_source_identifier`, and `selected_snapshot_identifier` must align with `current_diagnostic_output_ref` when present.
- `immutable_truth_refs` must identify the deterministic diagnostic truth being inspected and mark score, domain, severity, confidence, posture, recommendation, and thresholds as read-only references.
- `mutation_boundaries` must explicitly prove no diagnostic, scoring, recommendation, runtime, learning, parser, comparison, fleet, or materialization mutation.
- `evidence_sections` and `evidence_rows` must be dynamic from validated deterministic data; hard-coded rows and synthetic rows are forbidden.

## 6. Generation Context, Freshness, and Provenance

`generation_context` should include dashboard generation ID, source artifact ID, backend run ID, report ID or AWR ID, DB identity, instance/host, snapshot/window identity, selected scope labels, and any current diagnostic output hash used for alignment.

`freshness` should include:

- `freshness_status`: `fresh`, `stale`, `unknown`, or `cache_only`.
- `generated_at`.
- `source_generated_at` or backend source timestamp when available.
- `current_dashboard_generation_id`.
- `source_payload_hash` or deterministic source hash.
- `cache_status`, with cache allowed only as continuity metadata.

`provenance` should include backend source path or source contract reference, deterministic engine name/version, source table or artifact reference where relevant, and hash of the inputs used to build the contract. Browser time, route state, localStorage, and LLM output cannot satisfy provenance.

## 7. Immutable Truth References

`current_diagnostic_output_ref` should point to the selected diagnostic output without copying authority into Deep Analysis. Recommended fields:

- `diagnostic_output_id` or `run_id`.
- `source_artifact_id`.
- `selected_scope_identity`.
- `normalized_decision_hash` or equivalent source hash.
- `screen3_snapshot_ref` when Screen 3 handed off the selected diagnostic context.

`immutable_truth_refs` should include read-only references such as:

- `primary_domain_ref`.
- `score_ref`.
- `severity_ref`.
- `confidence_ref`.
- `posture_ref`.
- `recommendation_ref`.
- `threshold_refs`.
- `diagnostic_driver_refs`.

Each reference should include `read_only: true`. Deep Analysis may say "this row supports the existing diagnostic output reference"; it must not write new values into those references.

## 8. Evidence Section Design

Each `evidence_sections` entry should include:

- `section_id`.
- `title`.
- `scope_classification`.
- `evidence_type`.
- `source_path` or `source_contract_ref`.
- `provenance`.
- `freshness_status`.
- `rows_present`.
- `allowed_rendering`.
- `limitations`.
- `missing_evidence`.
- `llm_explainable`.
- `display_priority`.

Allowed evidence types:

- `diagnostic_driver`.
- `metric_breakdown`.
- `top_sql_detail`.
- `wait_event_detail`.
- `db_time_breakdown`.
- `domain_score_detail`.
- `scalar_metric_detail`.
- `time_series_supporting_context`.
- `distribution_supporting_context`.
- `anomaly_supporting_context`.
- `similarity_supporting_context`.
- `rac_adg_topology_detail`.
- `engineering_detail`.
- `limitation`.
- `missing_evidence`.

Forbidden behavior:

- No section may render if `rows_present` is false, unless it is a single explicit blocked, limitation, or missing-evidence state.
- No section may contain placeholder conclusions.
- No section may convert historical context into current proof.
- No section may convert comparative output into current-scope evidence.
- No section may convert LLM text into evidence.
- No section may exist only to fill space.

## 9. Evidence Row Design

Each `evidence_rows` entry should include:

- `row_id`.
- `section_id`.
- `scope_classification`.
- `evidence_type`.
- `metric_name` or `evidence_name`.
- `deterministic_value`.
- `unit`.
- `comparator_or_threshold_ref` when applicable.
- `source_path`.
- `provenance`.
- `freshness_status`.
- `supports_existing_truth_ref`.
- `limitation_flags`.
- `display_label`.
- `render_as`.

Rules:

- Deep Analysis rows must not reuse 7CX comparative `evidence_rows` as current-scope evidence.
- If a future adapter reuses a source structure, it must relabel, rescope, and validate under the Deep Analysis contract.
- Comparative `metric_deltas` and `domain_deltas` are not Deep Analysis current-scope evidence.
- Synthetic rows, hard-coded rows, page-identity rows, route-state rows, cache rows, prepared Target A/B rows, and LLM-created rows are forbidden.
- Rows with `historical_supporting_context` may support interpretation only after they are labeled as supporting context.

## 10. Chart Eligibility Design

Deep Analysis chart eligibility is optional future contract data. It must be separate from 7CX comparative visual eligibility.

Each chart eligibility item should include:

- `chart_type`.
- `required_evidence_shape`.
- `allowed_scope_classifications`.
- `minimum_rows`.
- `source_paths`.
- `deterministic_only`.
- `browser_computation_allowed`.
- `synthetic_data_allowed`.
- `empty_chart_allowed`.
- `eligibility_status`.
- `blocked_reason`.

Allowed statuses:

- `eligible`: chart type is requested and required deterministic evidence shape exists.
- `blocked`: chart is relevant/requested but required evidence is missing or invalid.
- `omitted`: no useful evidence and no useful blocked explanation.
- `not_requested`: chart type was not requested by the contract.
- `not_supported`: chart type requires a future contract, such as fleet/population or unsupported density semantics.

Required fixed constraints:

- `browser_computation_allowed=false`.
- `synthetic_data_allowed=false`.
- `empty_chart_allowed=false`.
- Eligibility does not create chart evidence.
- A chart may render only from evidence rows or source paths that already contain the exact required evidence shape.
- No chart may render from page identity, route state, cache, prepared Target A/B context, comparative permission fields, or LLM text.

7CY-B does not implement charts.

## 11. Validation Model

A future builder or renderer must validate:

- `contract_type` is `screen4_deep_analysis_contract`.
- `contract_version` is supported.
- `generated_by` is deterministic/backend, not LLM, browser, UI, route state, or cache.
- `source_scope` is the current selected diagnostic scope.
- selected identifiers align with `current_diagnostic_output_ref`.
- provenance is present and backend/deterministic.
- freshness is present and not stale or cache-only.
- immutable truth refs are present and read-only.
- all mutation boundary flags are false.
- `evidence_sections` are non-empty for ready states.
- each section has rows or a meaningful blocked/limitation state.
- each row has a valid `scope_classification`.
- no `cache_only` or `prepared_only` row renders as Deep Analysis evidence.
- no `comparative_output` row renders as primary Deep Analysis evidence.
- no `fleet_population` row renders without a future fleet/population evidence contract.
- no LLM-generated section or row is accepted as evidence.
- no synthetic, hard-coded, demo, placeholder, or page-identity row is accepted.
- chart eligibility never creates evidence.
- missing evidence displays only as limitation, not proof.

## 12. State Model

| State | Meaning | Prerequisites | Allowed content | Forbidden content | Future UI behavior | Validation behavior | LLM explanation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `deep_analysis_unavailable` | No valid current-scope Deep Analysis contract or selected diagnostic output. | None, or only cache/prepared/page state. | One blocked/unavailable message. | Evidence panels, charts, rows, conclusions. | Show concise blocked state only. | Contract invalid or absent. | Not allowed except static boundary text. |
| `deep_analysis_output_required` | Candidate deterministic evidence exists, but no Deep Analysis contract has been returned. | Selected diagnostic output or candidate evidence refs. | Required next step and missing contract reason. | Drilldown evidence, charts, LLM-generated rows. | Explain that deterministic contract is required. | Contract absent or wrong type. | Boundary explanation only. |
| `deep_analysis_current_scope` | Current selected diagnostic output is aligned, but detailed evidence rows are not ready. | Current diagnostic output ref and selected identifiers align. | Current-scope identity and immutable truth references. | Evidence sections that imply row-level proof. | Show scope/contract readiness when implemented. | Valid identity refs; not ready for rows. | May explain scope boundary from validated refs. |
| `deep_analysis_historical_supporting_context` | Only historical/supporting evidence is available. | Historical deterministic context with labels. | Supporting context and limitations. | Primary current-scope proof, root-cause language. | Show labeled supporting context only when useful. | Ready only for supporting context, not primary evidence. | May explain that history is supporting only. |
| `deep_analysis_evidence_available` | Valid contract has sections/rows, but chart eligibility is absent or blocked. | Valid contract, fresh provenance, populated rows. | Populated text/table evidence and limitations. | Empty sections, chart shells, new truth claims. | Render populated evidence sections only. | Valid contract with row-level evidence. | May explain validated rows and limitations. |
| `deep_analysis_ready` | Valid fresh contract has aligned current scope, populated evidence, and any requested chart eligibility passed. | Valid contract, populated rows, eligible chart data if charts requested. | Deterministic evidence drilldown and contract-backed optional visuals. | Mutation, LLM decisions, synthetic charts. | Full Deep Analysis view in future implementation. | All validation checks pass. | May explain validated contract content only. |

## 13. LLM Boundary

LLM may:

- Explain validated deterministic Deep Analysis contract content.
- Summarize limitations and missing evidence.
- Explain what a metric means.
- Explain why evidence is missing.
- Explain that historical context is supporting only.

LLM must not:

- Create evidence rows or sections.
- Classify scope.
- Decide root cause.
- Assign or change severity.
- Assign or change confidence.
- Change score, primary domain, posture, recommendation, or thresholds.
- Choose chart eligibility.
- Decide freshness or provenance.
- Turn missing evidence into conclusions.
- Generate comparison output.
- Generate fleet output.
- Mutate runtime, parser, learning, materialization, or future-run behavior.

## 14. Product Wording

Allowed language:

- Deep Analysis.
- Current Diagnostic Evidence.
- Evidence Drilldown.
- Deterministic Evidence Detail.
- Supporting Evidence.
- Evidence Limitations.
- Missing Evidence.
- Analysis Explanation.
- Current selected scope.
- Existing diagnostic output.

Avoid unless a deterministic contract explicitly supports the statement:

- root cause.
- proven cause.
- definitive cause.
- new diagnosis.
- model-decided insight.
- LLM-determined cause.
- recommended action from Deep Analysis.
- improved, degraded, better, worse, winner, loser, regression, or improvement.

When historical evidence appears, use "historical supporting context" or "supporting evidence". Reserve "comparison" for prepared Target A/B context, deterministic comparison output, Comparative Review state names, and explicitly gated comparative visualizations.

## 15. Relationship to 7CX Comparative Contracts

7CX Comparative Review boundaries remain intact.

Deep Analysis must not treat 7CX `evidence_rows`, `metric_deltas`, `domain_deltas`, `allowed_visualizations`, visual eligibility, or comparative SVG rendering as Deep Analysis evidence. They are comparative-only unless a future adapter explicitly:

1. Reads trusted backend evidence, not rendered UI.
2. Relabels the scope classification.
3. Validates the evidence under `screen4_deep_analysis_contract`.
4. Preserves that comparative semantics remain Comparative Review unless the row is only used as labeled supporting context.

`allowed_visualizations` in 7CX controls comparative rendering permission only. Deep Analysis chart eligibility must use a separate field and must not create chart evidence.

## 16. Relationship to Historical Review

Historical Review remains the lane for same-DB trends, anomalies, distribution, period, baseline, and similarity context. Deep Analysis may use historical content only as `historical_supporting_context`, with explicit labeling and limitations.

Historical supporting context is not deterministic comparison output and is not current-scope Deep Analysis proof unless the Deep Analysis contract explicitly marks it as current-scope deterministic evidence from the selected diagnostic output. Browser-side historical selectors remain local display controls only.

## 17. Relationship to Cache and Prepared-Only State

Cache restores continuity only. It cannot satisfy freshness, provenance, source scope, selected identifiers, evidence rows, chart eligibility, or readiness.

Prepared Target A/B context identifies possible comparison sides only. It is not comparison output and not Deep Analysis output. It cannot render Deep Analysis sections, rows, charts, or conclusions.

Route state, localStorage, hash state, page identity, selected tab/mode, and client-created flags cannot create Deep Analysis evidence.

## 18. Relationship to Screens 3, 5, and 6

Screen 3 owns the current Diagnostic Snapshot. Deep Analysis may reference Screen 3 deterministic truth through immutable read-only refs, but it cannot change diagnosis, score, severity, confidence, posture, recommendation, thresholds, or evidence values.

Screen 5 owns recommendation action, owner/status, validation checklist, and outcome capture. Deep Analysis cannot recommend a new action, change recommendation truth, create action records, or record outcomes.

Screen 6 owns learning candidate review, materialization, model registry/runtime eligibility, and future-run influence. Deep Analysis cannot create learning candidates, approve materialization, activate runtime eligibility, or change future-run behavior.

## 19. Future Implementation Plan

Recommended sequence:

1. 7CY-C: Add a small non-rendering Deep Analysis contract helper and validation tests.
2. 7CY-D: Add a small non-rendering builder/adapter that assembles the contract from existing deterministic current-scope inputs and validates it.
3. 7CY-E: Add guarded state integration that can classify unavailable, output-required, and ready states without rendering evidence panels.
4. 7CY-F: Render text/table-only populated Deep Analysis evidence sections from a validated contract.
5. 7CY-G: Add a non-rendering dynamic visualization selection contract that inspects validated evidence shapes.
6. 7CY-H or later: Render selected visualization candidates only from eligible evidence shapes, with no browser computation and no empty chart shells.

Do not skip directly to UI panels or charts.

### 7CY-D Builder / Adapter Implementation Note

7CY-D adds `src/reporting/dashboard/screen4/deep_analysis_builder.py` as a pure, non-rendering adapter. Its public entry points are `build_deep_analysis_contract(...)` and `build_and_validate_deep_analysis_contract(...)`.

The builder accepts in-memory `report_data`, `selected_scope`, optional `screen_model`, optional `chart_payload`, and optional `generation_context` mappings. It assembles a `screen4_deep_analysis_contract` from deterministic current-scope diagnostic/display inputs only, treats historical time-series and distribution inputs as `historical_supporting_context`, records missing or blocked inputs as limitations/missing evidence, and ignores comparative, prepared-only, cache-only, fleet, and LLM text as Deep Analysis proof.

Readiness remains owned by `src/reporting/dashboard/screen4/deep_analysis_contract.py`. `build_and_validate_deep_analysis_contract(...)` calls `validate_deep_analysis_contract(...)`; the builder does not independently declare readiness, render UI, render charts, call backend routes, call LLMs, or mutate runtime truth.

### 7CY-E Guarded State Implementation Note

7CY-E adds a Screen 4 Deep Analysis guarded state card in `src/reporting/html_dashboard.py`. The card calls `build_and_validate_deep_analysis_contract(...)` and renders only state metadata: readiness, validator state, selected scope summary, provenance/freshness summary, current/supporting section and row counts, blocked reasons, missing evidence categories, and limitation categories.

7CY-E does not render Deep Analysis evidence rows, evidence tables, drilldowns, charts, SVGs, Chart.js/Plotly panels, backend routes, browser computation, parser/comparison execution, LLM calls, or runtime mutation. Historical inputs remain supporting context only, comparative/7CX fields remain Comparative Review only, and cache/prepared-only state cannot create Deep Analysis readiness. 7CY-F owns future text/table evidence rendering from validated contract rows.

### 7CY-F Evidence Rendering Implementation Note

7CY-F renders populated Screen 4 Deep Analysis evidence sections from the validated `screen4_deep_analysis_contract` only. The guarded state card remains first, then text/table evidence sections render from `evidence_sections`, `evidence_rows`, `limitations`, `missing_evidence`, and validator `allowed_section_ids` / `supporting_section_ids`.

Current-scope rows render as "Current Diagnostic Evidence" only when the builder/validator marks the contract ready. Historical rows render only as "Historical Supporting Context" and do not become current proof. Comparative/7CX rows, metric/domain deltas, `allowed_visualizations`, comparative visual eligibility, prepared Target A/B, cache-only state, page identity, and LLM text do not feed Deep Analysis rendering.

7CY-F does not render charts, SVGs, Chart.js/Plotly panels, violin/distribution diagrams, chart canvases, visual selectors, backend routes, browser computation, LLM calls, parser/comparison execution, or runtime mutation. Future graph work should be context-driven, evidence-shape-driven, dynamic, and extensible from validated contract data for the active evidence mode, not selected from a hard-coded small chart menu or inferred from page identity.

### 7CY-G Dynamic Visualization Selection Implementation Note

7CY-G adds `src/reporting/dashboard/screen4/deep_analysis_visual_selection.py` as a pure, non-rendering selector. Its public entry point is `select_deep_analysis_visualizations(contract, validation_result=None)`.

The selector inspects only the validated Deep Analysis contract: `evidence_sections`, `evidence_rows`, optional `chart_eligibility`, limitations, missing evidence, and validator `allowed_section_ids` / `supporting_section_ids`. It emits candidate metadata for visualization families such as contribution, ranked contribution, time series, aligned overlay, distribution evidence, anomaly timeline, pressure band, topology fact map, similarity neighborhood, fleet/population blocked state, and table-only fallback. It does not render HTML, SVG, Chart.js, Plotly, chart containers, or visual shells.

Visualization selection is evidence-shape-driven and extensible. It is not limited to DB time, wait, or Top SQL buckets, and it does not use page identity, route state, cache, prepared Target A/B, comparative output, fleet evidence without a future fleet contract, or LLM text as visual proof. `chart_eligibility` remains an input signal only; it cannot create evidence, bypass row/shape validation, or make an invalid contract ready.

Distribution and violin-style future candidates use "Distribution Evidence" wording unless true density semantics are explicitly validated. One-sample, min/max-only, summary-only, synthetic, demo, placeholder, stale, cache-only, or LLM-created samples are not eligible. Future 7CY-H rendering may consume eligible candidates only after this selector and the Deep Analysis contract remain valid.

## 20. Future Test Plan

Future tests should verify:

- Rejects cache-only contract/state.
- Rejects prepared-only Target A/B contract/state.
- Rejects comparative-only evidence as primary Deep Analysis evidence.
- Rejects fleet/population evidence without fleet contract.
- Rejects LLM-generated evidence rows.
- Rejects missing provenance.
- Rejects stale freshness.
- Rejects mutation boundaries when any mutation flag is true.
- Omits empty sections or renders only one meaningful blocked/limitation state.
- Allows current-scope deterministic evidence.
- Allows historical supporting context only with explicit supporting labels.
- Chart eligibility cannot create chart evidence.
- No chart renders from page identity, route state, cache, prepared Target A/B, or LLM text.
- No generated artifact drift unless a future implementation intentionally regenerates artifacts.
- `html_dashboard.py` does not render Deep Analysis before a contract-ready state.

## 21. Implementation Limits for 7CY-B

7CY-B is design-only. It does not add:

- UI rendering.
- HTML dashboard changes.
- Generated dashboard artifact changes.
- Browser JavaScript behavior.
- Backend routes.
- Charts.
- Visual renderers.
- Runtime mutation paths.
- Screen 5 or Screen 6 behavior.
- 7CX comparative rendering changes.
- Dashboard generator decomposition.
