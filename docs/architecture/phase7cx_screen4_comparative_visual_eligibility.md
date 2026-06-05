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
  "timestamp": "2026-06-05T12:00:00Z",
  "metric_key": "cpu",
  "target_a_value": 70,
  "target_b_value": 58,
  "unit": "score"
}
```

Rows may appear in `time_series_rows`, `aligned_time_series_rows`, `time_series_evidence_rows`, `visual_evidence.time_series_overlay`, or evidence rows explicitly marked with `visualization=time_series_overlay`.

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

## Distribution / Violin Eligibility

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

Blocked reason codes include:

- `allowed_visualization_missing`
- `distribution_samples_missing`
- `missing_metric_identity`
- `target_a_samples_missing`
- `target_b_samples_missing`
- `insufficient_distribution_samples`
- `non_numeric_distribution_sample`

Summary deltas, min/max values, one sample per target, and synthetic samples cannot make a violin eligible.

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

## Rendering Boundary

The 7CX-G helper returns structured status data only. It emits no chart markup, no canvas, no SVG, no visual containers, and no placeholder panels.

The Screen 4 Rendering Eligibility panel may show text-only eligibility facts. It must omit `not_requested` visuals unless the absence is useful and must not create empty visual shells.

## Future Gate

Future 7CX-H rendering may draw graphs or violins only after:

- the Screen 4 deterministic comparison output contract validates,
- `allowed_visualizations` includes the specific visual,
- 7CX-G eligibility returns `eligible`,
- the renderer can draw from real contract evidence without synthetic points or samples,
- and no empty chart shell would be produced.
