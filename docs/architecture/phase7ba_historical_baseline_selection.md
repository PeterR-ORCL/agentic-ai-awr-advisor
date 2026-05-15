# Phase 7BA Historical Baseline Selection

## 1. Purpose

Phase 7BA defines local, deterministic historical baseline selection object models for future Screen 4 historical review workflows.

The model lets future workflows describe possible historical baselines, request baseline selection, validate selection metadata, and record comparison context without changing deterministic historical truth.

## 2. Scope

Phase 7BA adds local metadata models, deterministic ID helpers, validation helpers, serialization/deserialization helpers, documentation, validation tests, and architecture index links.

The scope includes historical baseline candidate records, baseline selection request records, baseline selection validation records, historical comparison context metadata, baseline quality/evidence metadata, actor/audit linkage fields, and metadata-only validation behavior.

Baseline selection records are local metadata only.

## 3. Non-Goals

Phase 7BA adds no Screen 4 UI, no baseline buttons, no persisted baseline records, no official baseline activation, no governed write path invocation, no backend execution, no database writes, no learning candidate creation, no trend/anomaly review object model, no historical-to-learning bridge, and no Phase 8 sizing/TCO.

No baseline is made official.

No historical truth is changed. No trend/anomaly/scoring behavior is changed. No recommendation truth is changed. No Phase 4I mutation occurs.

Phase 8 sizing/TCO is not implemented.

## 4. Baseline Selection Is Not Historical Truth Mutation

Historical baseline selection records are governed workflow metadata only.

A selected baseline is not official/runtime-active in Phase 7BA. It does not rewrite historical evidence, recalculate trends, reclassify anomalies, change scoring, change recommendation context, create learning candidates, mutate runtime behavior, or alter Phase 4I.

## 5. HistoricalBaselineCandidate

`HistoricalBaselineCandidate` describes a possible baseline interval, run, or snapshot for comparison.

Fields include `baseline_candidate_id`, `baseline_name`, `run_id`, `awr_id`, `dbid`, `database_name`, `snapshot_label`, `start_time`, `end_time`, `workload_class`, `stability_score`, `evidence_quality`, `missing_metric_count`, `anomaly_count`, `trend_volatility`, `candidate_status`, `source_context`, and `notes`.

Rules require candidate id and baseline name, at least one of `run_id` or `awr_id`, `stability_score` between 0.0 and 100.0, non-negative missing metric and anomaly counts, non-negative trend volatility, supported evidence quality, and supported candidate status.

## 6. HistoricalBaselineSelectionRequest

`HistoricalBaselineSelectionRequest` describes a future request to select a candidate baseline for comparison.

Fields include `selection_request_id`, `candidate_id`, `requested_by_actor_id`, `actor_audit_context`, `selection_reason`, `comparison_purpose`, `target_run_id`, `target_awr_id`, `target_snapshot_label`, `target_domain`, `requested_status`, `write_performed`, `baseline_official`, `runtime_influence`, `phase4i_mutation_requested`, `created_at`, and `notes`.

Rules require request id, candidate id, actor id, supported comparison purpose, `write_performed=false`, `baseline_official=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 7. HistoricalBaselineValidation

`HistoricalBaselineValidation` describes deterministic validation of a baseline selection request.

Fields include `validation_id`, `selection_request_id`, `candidate_id`, `valid`, `validation_status`, `evidence_quality`, `stability_acceptable`, `missing_metric_risk`, `anomaly_risk`, `workload_similarity`, `comparison_valid`, `baseline_official`, `write_performed`, `denied_reasons`, `warnings`, `required_next_steps`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

Rules require supported validation status, supported evidence quality, `baseline_official=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 8. HistoricalComparisonContext

`HistoricalComparisonContext` describes local metadata for what the baseline is compared against.

Fields include `comparison_context_id`, `baseline_candidate_id`, `target_run_id`, `target_awr_id`, `comparison_type`, `comparison_purpose`, `compared_domains`, `baseline_snapshot_label`, `target_snapshot_label`, `limitations`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

Rules require context id, baseline candidate id, supported comparison type, supported comparison purpose, list-valued compared domains, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 9. Baseline Statuses

Supported candidate and request statuses are:

- `proposed`
- `under_review`
- `validated`
- `rejected`
- `insufficient_evidence`
- `superseded`
- `closed`

No status means official runtime baseline.

## 10. Evidence Quality

Supported evidence quality values are:

- `high`
- `medium`
- `low`
- `insufficient`
- `unknown`

Low or insufficient quality blocks valid metadata-only selection.

## 11. Comparison Purposes

Supported comparison purposes are:

- `before_after_tuning`
- `stable_vs_degraded`
- `current_vs_baseline`
- `workload_regression`
- `anomaly_review`
- `trend_review`
- `general_historical_review`

## 12. Comparison Types

Supported comparison types are:

- `single_baseline_to_target`
- `before_after`
- `multi_snapshot_baseline`
- `workload_class_baseline`
- `historical_window_baseline`

## 13. Validation Rules

Candidate validation rejects missing identifiers, unsupported statuses, unsupported evidence quality, stability scores outside 0.0-100.0, negative missing metric count, negative anomaly count, and negative trend volatility.

Selection request validation rejects missing actor, unsupported comparison purpose, `baseline_official=true`, `write_performed=true`, `runtime_influence=true`, and `phase4i_mutation_requested=true`.

Validation result validation rejects unsupported validation status, unsupported evidence quality, `baseline_official=true`, `write_performed=true`, `runtime_influence=true`, and `phase4i_mutation_requested=true`.

Comparison context validation rejects unsupported comparison type, unsupported comparison purpose, non-list compared domains, `runtime_influence=true`, and `phase4i_mutation_requested=true`.

The deterministic evaluation helper returns `needs_actor` for missing actor, `needs_candidate` for missing candidate, `insufficient_evidence` for low/insufficient evidence or low stability, `high_missing_metric_risk` when missing metrics are present, `high_anomaly_risk` when anomalies are present, and `valid_metadata_only` when metadata passes local checks.

## 14. Baseline Official Boundary

No baseline is made official in 7BA.

Every request and validation record must keep `baseline_official=false`. A baseline candidate, selection request, or validation result cannot become an official runtime baseline in this phase.

## 15. Runtime Truth Boundary

Baseline selection records are local metadata only. They do not change historical truth, trend truth, anomaly truth, scoring behavior, recommendation truth, parser output, dashboard truth, or runtime behavior.

Deterministic runtime remains authoritative.

## 16. Phase 4I Boundary

No Phase 4I mutation occurs.

Historical baseline metadata cannot change Phase 4I payload shape, historical output, trend/anomaly output, scoring output, decision output, recommendation output, or generated dashboard artifacts.

## 17. Relationship to 7AZ

Phase 7AZ established the Screen 4 historical review workflow boundary. Phase 7BA stays inside that boundary by creating local metadata models only.

Phase 7BA does not add Screen 4 workflow UI, invoke a governed write path, create official baselines, or change runtime truth.

## 18. Relationship to Future 7BB

Future 7BB may define trend/anomaly review object models.

Phase 7BA does not implement trend/anomaly review records, approve trends, dispute trends, mark anomalies false positive, or change trend/anomaly logic.

## 19. Relationship to Future 7BC

Future 7BC may define the historical review to learning candidate bridge.

Phase 7BA does not create learning candidate intents, create learning candidates, route recurring trends/anomalies to learning, or activate materialized learning.

## 20. Relationship to Future 7BD

Future 7BD may define Screen 4 workflow validation, readiness, release certification, and operational documentation.

Phase 7BA adds only subphase model validation and directly related tests.

## 21. Relationship to Phase 8

Phase 8 sizing/TCO is out of scope.

Historical baseline comparison metadata may be useful to later what-if or sizing analysis, but Phase 7BA does not implement capacity planning, cost modeling, EM extract, sizing, TCO, or what-if advisory.

Phase 8 sizing/TCO is not implemented.

## 22. Acceptance Criteria

Phase 7BA acceptance requires local baseline candidate, selection request, validation, and comparison context models; deterministic IDs; validation helpers; serialization/deserialization helpers; documentation; and tests.

Acceptance also requires these guarantees: baseline selection records are local metadata only, no baseline is made official, no baseline records are persisted, no historical truth is changed, no trend/anomaly/scoring behavior is changed, no recommendation truth is changed, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
