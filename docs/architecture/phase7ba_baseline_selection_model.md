# Phase 7BA Baseline Selection Model

## 1. Purpose

Phase 7BA defines the concrete local object model for historical baseline selection metadata used by future Screen 4 historical review workflows.

The model is deterministic and local-only. No baseline is persisted or made official in 7BA.

## 2. HistoricalBaselineCandidate Object Shape

`HistoricalBaselineCandidate` has this metadata shape:

- `baseline_candidate_id`
- `baseline_name`
- `run_id`
- `awr_id`
- `dbid`
- `database_name`
- `snapshot_label`
- `start_time`
- `end_time`
- `workload_class`
- `stability_score`
- `evidence_quality`
- `missing_metric_count`
- `anomaly_count`
- `trend_volatility`
- `candidate_status`
- `source_context`
- `notes`

The candidate is a possible comparison baseline only. It is not an official runtime baseline.

## 3. HistoricalBaselineSelectionRequest Object Shape

`HistoricalBaselineSelectionRequest` has this metadata shape:

- `selection_request_id`
- `candidate_id`
- `requested_by_actor_id`
- `actor_audit_context`
- `selection_reason`
- `comparison_purpose`
- `target_run_id`
- `target_awr_id`
- `target_snapshot_label`
- `target_domain`
- `requested_status`
- `write_performed`
- `baseline_official`
- `runtime_influence`
- `phase4i_mutation_requested`
- `created_at`
- `notes`

In Phase 7BA, `baseline_official=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 4. HistoricalBaselineValidation Object Shape

`HistoricalBaselineValidation` has this metadata shape:

- `validation_id`
- `selection_request_id`
- `candidate_id`
- `valid`
- `validation_status`
- `evidence_quality`
- `stability_acceptable`
- `missing_metric_risk`
- `anomaly_risk`
- `workload_similarity`
- `comparison_valid`
- `baseline_official`
- `write_performed`
- `denied_reasons`
- `warnings`
- `required_next_steps`
- `runtime_influence`
- `phase4i_mutation_requested`
- `notes`

In Phase 7BA, `baseline_official=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 5. HistoricalComparisonContext Object Shape

`HistoricalComparisonContext` has this metadata shape:

- `comparison_context_id`
- `baseline_candidate_id`
- `target_run_id`
- `target_awr_id`
- `comparison_type`
- `comparison_purpose`
- `compared_domains`
- `baseline_snapshot_label`
- `target_snapshot_label`
- `limitations`
- `runtime_influence`
- `phase4i_mutation_requested`
- `notes`

In Phase 7BA, `runtime_influence=false` and `phase4i_mutation_requested=false`.

## 6. Statuses

Supported baseline statuses are:

- `proposed`
- `under_review`
- `validated`
- `rejected`
- `insufficient_evidence`
- `superseded`
- `closed`

These are metadata statuses. No status makes a baseline official.

## 7. Evidence Quality Values

Supported evidence quality values are:

- `high`
- `medium`
- `low`
- `insufficient`
- `unknown`

Low and insufficient evidence quality block valid metadata-only baseline selection.

## 8. Comparison Purposes

Supported comparison purposes are:

- `before_after_tuning`
- `stable_vs_degraded`
- `current_vs_baseline`
- `workload_regression`
- `anomaly_review`
- `trend_review`
- `general_historical_review`

## 9. Comparison Types

Supported comparison types are:

- `single_baseline_to_target`
- `before_after`
- `multi_snapshot_baseline`
- `workload_class_baseline`
- `historical_window_baseline`

## 10. Validation Rules

Candidate validation requires candidate id, baseline name, at least one of run id or AWR id, supported status, supported evidence quality, stability score between 0.0 and 100.0, non-negative missing metric count, non-negative anomaly count, and non-negative trend volatility.

Selection request validation requires request id, candidate id, actor id, supported comparison purpose, supported requested status, `baseline_official=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

Validation result validation requires validation id, request id, candidate id, supported validation status, supported evidence quality, `baseline_official=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

Comparison context validation requires context id, baseline candidate id, supported comparison type, supported comparison purpose, list-valued domains, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 11. Serialization Rules

All object types serialize to deterministic dictionaries with explicit fields.

Deserialization reconstructs frozen dataclass objects and reruns validation. Round trips must be stable for the same input.

Serialization is not persistence. Serialization does not write files, write database rows, call services, call dashboard code, or make a baseline official.

## 12. Deterministic ID Rules

IDs are deterministic and based only on supplied metadata:

- `HIST-BASELINE-CANDIDATE-<RUN_OR_AWR>-<SNAPSHOT>`
- `HIST-BASELINE-REQUEST-<CANDIDATE>-<PURPOSE>`
- `HIST-BASELINE-VALIDATION-<REQUEST>`
- `HIST-COMPARISON-CONTEXT-<BASELINE>-<TARGET>-<TYPE>`

IDs use no random UUID, no timestamp, no database sequence, and no external service. The same input creates the same ID.

## 13. Runtime Safety Rules

Phase 7BA safety rules require `baseline_official=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

Baseline selection records are local metadata only. No baseline is persisted or made official in 7BA.

The model must not change historical truth, trend/anomaly interpretation, scoring behavior, recommendation truth, parser output, dashboard behavior, runtime behavior, or Phase 4I.

## 14. Non-Goals

Phase 7BA does not add Screen 4 UI, persist records, make baselines official, invoke governed write path, execute analysis, write databases, create learning candidates, implement trend/anomaly review, implement historical-to-learning bridge, implement validation/certification for the whole Screen 4 block, or implement Phase 8 sizing/TCO.

## 15. Acceptance Criteria

Acceptance requires deterministic dataclasses, supported constants, validation helpers, deterministic IDs, serialization/deserialization helpers, metadata-only evaluation, documentation, and tests.

Acceptance also requires these guarantees: baseline_official=false, write_performed=false, runtime_influence=false, phase4i_mutation_requested=false, no baseline is persisted or made official in 7BA, no historical truth is changed, no trend/anomaly/scoring behavior is changed, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
