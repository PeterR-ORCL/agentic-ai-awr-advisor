# Phase 7CX Screen 4 Comparative Visual Eligibility

## Purpose

7CX-G adds deterministic guardrails for future Screen 4 comparative visuals. It decides whether a requested visual is eligible, blocked, omitted, not requested, or not supported from the validated Screen 4 deterministic comparison output contract.

This is eligibility only. It does not render charts, draw violins, create time-series overlays, create distribution panels, add browser-side comparison computation, add a backend route, create synthetic samples, create synthetic time-series points, or mutate runtime truth.

## Preconditions

Visual eligibility may be evaluated only from a Screen 4 deterministic comparison output contract with:

- `screen4_contract_type=deterministic_comparison_output`
- `generated_by=deterministic_engine`
- `validation_status=valid`
- `allowed_visualizations` as a list

Prepared Target A/B context, route state, cache state, loose comparison metadata, LLM text, and unadapted 7CC artifact references cannot make a visual eligible.

## Data-to-Render Contract

`allowed_visualizations` is permission only. It does not create time-series points, distribution samples, SQL/event identity, graph rows, or chart-ready evidence.

7CX-G visual eligibility is a gate only. It does not create evidence; it only checks whether the validated contract already contains the exact evidence shape required by the requested future visual.

Future visual renderers may read visual evidence only from `evidence_rows` entries that carry an explicit visual-specific evidence shape:

- Time-series evidence rows must be marked with `visualization=time_series_overlay`.
- Distribution/violin evidence rows must be marked with `visualization=distribution_violin`.
- SQL/event movement rows must live in `evidence_rows` and include persistent SQL/event/wait identity plus numeric Target A/B values.

Top-level convenience fields such as `time_series_rows`, `distribution_rows`, `visual_evidence`, or artifact references are not visual evidence for Screen 4 rendering. A future adapter may normalize trusted backend data into visual-shaped `evidence_rows`, but Screen 4 must not render from those loose fields directly.

`metric_deltas` feed the Metric Differences table only. `domain_deltas` feed the Domain Differences table only. Summary deltas, min/max-only rows, one sample per target, prepared Target A/B context, cache/route continuity, LLM text, UI-generated values, and synthetic samples or time-series points cannot feed future visuals.

## Result Model

`Screen4ComparativeVisualEligibility` records:

- `visualization_name`
- `visualization_label`
- `status`
- `rendering_allowed`
- `reason_code`
- `reason`
- `required_fields`
- `evidence_count`
- `missing_fields`
- `supported`
- `notes`

Allowed statuses:

- `eligible`: the visual is listed in `allowed_visualizations` and the required deterministic evidence shape exists.
- `blocked`: the visual is requested or relevant, but required evidence is missing or invalid.
- `omitted`: there is no useful visual evidence and no useful blocked explanation.
- `not_requested`: the visual is not listed in `allowed_visualizations`.
- `not_supported`: the visual is outside the current 7CX-G scope or requires a future fleet/population evidence contract.

## Time-Series Overlay Eligibility

`time_series_overlay` is eligible only when:

- `allowed_visualizations` includes `time_series_overlay`.
- The contract contains explicit aligned time-series rows.
- At least two aligned points exist for one metric.
- Every point has `timestamp`, `metric_key`, `target_a_value`, and `target_b_value`.
- Target values are numeric.

Accepted row shape:

```json
{
  "visualization": "time_series_overlay",
  "timestamp": "2026-06-05T12:00:00Z",
  "metric_key": "cpu",
  "target_a_value": 70,
  "target_b_value": 58,
  "unit": "score"
}
```

Rows must appear in `evidence_rows` and must be explicitly marked with `visualization=time_series_overlay`. Top-level `time_series_rows`, `aligned_time_series_rows`, `time_series_evidence_rows`, and `visual_evidence.time_series_overlay` are not Screen 4 visual render evidence.

Blocked reason codes include:

- `allowed_visualization_missing`
- `aligned_time_series_rows_missing`
- `insufficient_time_series_points`
- `missing_metric_identity`
- `missing_timestamp`
- `missing_target_a_value`
- `missing_target_b_value`
- `non_numeric_time_series_value`

Metric deltas, domain deltas, snapshot identity, prepared Target A/B context, route/cache state, and LLM text are not time-series evidence.

## Distribution Evidence Eligibility (`distribution_violin`)

`distribution_violin` is eligible only when:

- `allowed_visualizations` includes `distribution_violin`.
- The contract contains actual distribution/sample rows.
- Target A and Target B samples both exist.
- Samples are numeric.
- At least three numeric samples per target exist for one metric.
- Metric identity is stable through `metric_key`.

Accepted paired row shape:

```json
{
  "visualization": "distribution_violin",
  "metric_key": "cpu",
  "metric_label": "CPU",
  "target_a_samples": [70, 71, 72],
  "target_b_samples": [58, 59, 60],
  "unit": "score"
}
```

Accepted separate row shape:

```json
{
  "visualization": "distribution_violin",
  "metric_key": "cpu",
  "target": "A",
  "samples": [70, 71, 72]
}
```

Separate rows are accepted only when both Target A and Target B sample rows exist for the same metric.

Distribution rows must appear in `evidence_rows` and must be explicitly marked with `visualization=distribution_violin`. Top-level `distribution_rows`, `distribution_sample_rows`, `distribution_evidence_rows`, and `visual_evidence.distribution_violin` are not Screen 4 distribution render evidence.

Blocked reason codes include:

- `allowed_visualization_missing`
- `distribution_samples_missing`
- `missing_metric_identity`
- `target_a_samples_missing`
- `target_b_samples_missing`
- `insufficient_distribution_samples`
- `non_numeric_distribution_sample`

Summary deltas, min/max-only rows, one sample per target, and synthetic samples cannot make distribution evidence eligible. Min/max rows must remain blocked unless the contract also carries actual Target A/B sample arrays or paired sample rows.

## SQL/Event Movement Eligibility

`top_sql_movement_table` is eligible only when:

- `allowed_visualizations` includes `top_sql_movement_table`.
- Evidence rows contain persistent SQL identity such as `sql_id`, `sql_signature`, or `stable_sql_identity`.
- Target A and Target B numeric values exist.

`wait_class_movement_table` and `top_event_movement_table` are eligible only when:

- The visual is listed in `allowed_visualizations`.
- Evidence rows contain persistent event/wait identity such as `event_id`, `event_name`, `wait_event`, or `stable_event_identity`.
- Target A and Target B numeric values exist.

Rows identified only by a loose label are blocked.

## Fleet / Population Visuals

Fleet or population visuals are `not_supported` in 7CX-G unless a future fleet/population evidence contract exists. 7CX-G does not add fleet diagrams or population visuals.

The missing fleet/population contract reason code is `fleet_evidence_contract_missing`.

## Rendering Boundary

The 7CX-G helper returns structured status data only. It emits no chart markup, no canvas, no SVG, no visual containers, and no placeholder panels.

The Screen 4 Rendering Eligibility panel may show text-only eligibility facts. It must omit `not_requested` visuals unless the absence is useful and must not create empty visual shells.

## 7CX-G-FU1 Review Findings

7CX-G-FU1 confirms and tightens the product boundary before any rendering work:

- `eligible` means eligible for future rendering only; it does not mean Screen 4 draws a chart today.
- `blocked` must identify the missing deterministic evidence shape, such as aligned time-series rows, Target A/B samples, persistent SQL identity, or persistent event/wait identity.
- `not_requested` visuals stay out of the text-only panel by default so the panel does not become noisy.
- Fleet/population visuals use `fleet_evidence_contract_missing` when no fleet/population evidence contract is present.
- Min/max-only distribution rows are explicitly blocked as `distribution_samples_missing`; they are not sample evidence.
- The text-only panel must not use "coming soon" wording, synthetic-data wording, chart containers, or visual placeholders.

## 7CX-H Rendering Gate

7CX-H may render comparative visuals only after:

- the Screen 4 deterministic comparison output contract validates,
- `allowed_visualizations` includes the specific visual,
- 7CX-G eligibility returns `eligible`,
- the renderer reads explicit visual-shaped `evidence_rows`, not permission, cache, route state, or loose artifact fields,
- the renderer can draw from real contract evidence without synthetic points or samples,
- and no empty chart shell would be produced.

7CX-H implements:

- a static Time-Series Evidence SVG from `evidence_rows` marked `visualization=time_series_overlay`,
- a static Distribution Evidence sample plot from `evidence_rows` marked `visualization=distribution_violin`.

The distribution view is intentionally conservative. It is a sample plot from actual Target A/B samples, not a true violin density plot, because the contract does not provide density estimates and Screen 4 must not synthesize samples or infer density.

Blocked or malformed visual evidence renders no SVG, no axes, no chart frame, and no placeholder visual section.

## 7CX-H-FU1 Visual Review Findings

7CX-H-FU1 keeps the machine contract key `distribution_violin`, but the operator-facing label is `Distribution Evidence` unless a future deterministic density contract supports a true violin plot. Eligibility reasons should describe missing sample evidence as Distribution Evidence, not as an implemented violin.

The first visual renderer remains server-side/static and no-browser-compute:

- Time-Series Evidence SVGs include accessible title and description text, visible Target A/Target B labels, and dashed Target B line styling so the visual does not rely on color alone.
- Distribution Evidence SVGs include accessible title and description text, visible Target A/Target B sample rows, and a textual sample table with sample counts.
- Blocked or malformed visual evidence continues to render no SVG, no chart frame, no axes, and no placeholder visual section.
- The renderer still reads only explicit visual-shaped `evidence_rows`; permission, eligibility, top-level loose fields, and UI/LLM values do not create visual evidence.
