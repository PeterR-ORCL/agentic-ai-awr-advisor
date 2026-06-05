# Phase 7CX Screen 4 Comparison Output Adapter

## Purpose

7CX-D adds a backend-only adapter that converts trusted deterministic comparison artifacts into the strict Screen 4 deterministic comparison output contract.

The adapter is contract/table-first. It does not render charts, comparison violins, A/B overlays, fleet diagrams, or rich Comparative Review UI. It does not add a backend route, browser-side comparison computation, artifact dereferencing in the browser, or a Build Comparison action. It does not add browser-side comparison computation.

## Trusted Inputs

The adapter may accept trusted backend inputs only:

- Phase 7CC `ComparisonExecutionResult`.
- Phase 7AM `AWRReportComparisonArtifact`.
- Serialized comparison artifact metadata from governed workflow output rows.
- Prepared Target A/B identity context for alignment checks only.
- Governed workflow metadata such as request, transaction, output artifact, execution, timestamp, and source scope fields.

Prepared Target A/B context is not comparison output. It only validates that the adapted artifact matches the selected baseline and candidate identities.

## Forbidden Inputs

The adapter must not treat these as Screen 4 output-ready:

- `selectedComparisonTargetA` or `selectedComparisonTargetB` alone.
- Route state or browser cache state alone.
- `comparison_artifact_reference` alone.
- `comparison_screen4_handoff` alone.
- Loose `comparison_result_*` fields.
- Client-created output-ready flags.
- LLM wording.
- Browser-computed deltas.

Loose artifact metadata remains non-output-ready until the adapter emits the strict Screen 4 contract and validation succeeds.

## Output Contract

Valid adapter output uses:

```json
{
  "screen4_contract_type": "deterministic_comparison_output",
  "contract_version": "7cx.screen4.comparison.v1",
  "adapter_version": "7cx-adapter-v1",
  "comparison_id": "required",
  "baseline_run_id": "required",
  "candidate_run_id": "required",
  "target_a_identity": {},
  "target_b_identity": {},
  "target_alignment": {"status": "aligned", "basis": []},
  "source_scope": "same_db_historical",
  "comparison_scope": "target_a_vs_target_b",
  "artifact_source": "phase7cc_comparison_execution",
  "artifact_reference": "comparison:<id>",
  "workflow_request_id": "optional",
  "workflow_transaction_id": "optional",
  "comparison_execution_id": "optional",
  "input_artifact_ids": [],
  "input_snapshot_range": {},
  "generated_from_hash": "required",
  "generated_by": "deterministic_engine",
  "generated_at": "required",
  "deterministic_engine_version": "phase7-am-comparison-v1",
  "metric_deltas": [],
  "domain_deltas": [],
  "evidence_rows": [],
  "confidence_basis": {
    "basis_type": "deterministic_evidence",
    "sample_count": 0,
    "limitations": []
  },
  "missing_evidence": [],
  "allowed_visualizations": [],
  "validation_status": "valid",
  "adapter_validation_messages": []
}
```

The adapter-controlled deterministic engine version is `phase7-am-comparison-v1` until the comparison engine exposes a native version marker.

## Target Identity Alignment

Target A and Target B identities must include enough stable identity to prevent mismatched artifacts from passing. In 7CX-D, `run_id` is required for both targets. AWR id, DBID, database name, instance, host, snapshot/window, source type, scope type, and scope value are optional but checked when available.

The adapter rejects output-ready when target identity is missing, baseline/candidate run ids cannot be resolved, Target A/B does not match the artifact baseline/candidate, or supplied source/comparison scope values conflict.

## Provenance Rules

`generated_by` is always `deterministic_engine`. Phase 7AM artifact `created_by` and workflow actor fields represent operator or request provenance only and must not be copied into `generated_by`.

`generated_at` must be supplied by trusted backend metadata or by the backend caller. The adapter does not use browser time or cache time as evidence truth.

`generated_from_hash` is derived from the artifact, Target A/B identity, and workflow metadata so downstream consumers can detect contract input changes.

## Field Mapping

`metric_deltas` comes from numeric or comparable score, wait/event, and SQL concentration difference rows.

`domain_deltas` is derived neutrally from metric names when a domain can be identified. It does not create outcome-direction labels.

`evidence_rows` normalizes score, wait/event, SQL, trend, anomaly, topology, platform, and data-availability difference dictionaries.

`missing_evidence` normalizes missing fields and artifact limitations.

`confidence_basis` records deterministic basis type, compared report count, evidence row count, missing evidence count, and limitations.

The adapter avoids outcome language. It does not create improvement, degradation, winner, loser, or trend conclusions.

## allowed_visualizations Policy

7CX-D allows only conservative table/panel permissions when supporting contract fields exist:

- `metric_delta_table`
- `domain_delta_summary`
- `confidence_basis_panel`
- `missing_evidence_panel`

The adapter does not grant:

- `time_series_overlay`
- `distribution_violin`
- `wait_class_movement_table`
- `top_sql_movement_table`
- `top_event_movement_table`

Those require future evidence shapes such as aligned time-series points, distribution samples, stable SQL identity, or event movement contracts. Fleet/population visualizations remain blocked without a fleet/population evidence contract.

## Rendering Boundary

7CX-D does not make Screen 4 render new graphics. It only produces a strict contract that can pass the 7CX-B validator. Screen 4 graphics remain gated by `allowed_visualizations`, and no specific graphic may render unless future UI work implements that visualization from validated contract data.

## Future Sequence

After 7CX-D review, the next safe step is 7CX-E: Screen 4 Rich Comparative Evidence View Design. Rich tables, deltas, graphs, and violins should remain deferred until the validated contract contains the required evidence and `allowed_visualizations` explicitly permits the visualization.

The 7CX-E design is documented in `docs/architecture/phase7cx_screen4_rich_comparative_evidence_view.md`.

7CX-G adds a visual eligibility layer after table rendering. The adapter may eventually emit visual evidence shapes such as aligned time-series rows or distribution samples, but those rows still must pass 7CX-G eligibility before any future Screen 4 graph or violin renderer can draw them. 7CX-G does not render visuals and does not treat summary deltas as graph or violin evidence.
