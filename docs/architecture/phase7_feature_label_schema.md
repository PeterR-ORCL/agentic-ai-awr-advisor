# Phase 7T Feature / Label Schema

## 1. Purpose

This document defines the governed schema metadata for Phase 7T feature and label datasets. Schemas are versioned, deterministic, local-only metadata records for X = feature vectors and y = observed outcomes.

Schemas describe dataset structure. They do not train a model, activate a model, change runtime scoring, or modify parser/scoring/decision/recommendation behavior.

## 2. Feature Schema

A feature schema includes `schema_id`, `schema_version`, `feature_names`, `feature_domains`, `required_features`, `optional_features`, `created_by`, and `notes`.

The schema version must be explicit. The schema ID must be deterministic and derived from stable schema inputs. Feature names identify the governed vector dimensions that future phases may use as X.

## 3. Label Schema

A label schema includes `schema_id`, `schema_version`, `label_names`, `label_values`, `supervised_labels`, `excluded_labels`, `created_by`, and `notes`.

The schema version must be explicit. The schema ID must be deterministic and derived from stable schema inputs. Label names identify governed observed outcomes that future phases may use as y.

## 4. Supported Feature Types

Supported feature types are:

- `numeric`
- `categorical`
- `boolean`
- `text`
- `derived_numeric`
- `derived_categorical`
- `missing`

Unsupported feature types fail validation. Unsupported feature value shapes fail validation clearly.

## 5. Supported Label Types

Supported label types are:

- `binary`
- `categorical`
- `ordinal`
- `numeric`
- `outcome_status`
- `review_status`
- `unknown`

Unsupported label types fail validation. Confidence must be between 0.0 and 1.0.

## 6. Supported Label Names

Supported label names are:

- `tuning_success`
- `performance_improved`
- `performance_worsened`
- `recommendation_accepted`
- `recommendation_rejected`
- `issue_recurred`
- `risk_confirmed`
- `false_positive`
- `false_negative`
- `action_effective`
- `action_ineffective`
- `no_change`
- `unknown_outcome`

Unsupported label names fail validation.

## 7. Supervised vs Excluded Labels

Supervised labels include the supported label names that represent auditable observed outcomes.

unknown_outcome is excluded from supervised labels by default. unknown_outcome is allowed as a governed label value for incomplete or unresolved evidence, but it must not be treated as supervised truth.

## 8. Deterministic ID Rules

IDs must be deterministic. They must not use random UUIDs, timestamps, database sequences, external services, network calls, or mutable runtime state.

Feature IDs follow stable inputs such as `FEATURE-<SCHEMA_VERSION>-<RUN_OR_AWR>-<FEATURE_NAME>`. Label IDs follow stable inputs such as `LABEL-<SCHEMA_VERSION>-<RUN_OR_AWR>-<LABEL_NAME>`. Feature schema IDs and label schema IDs include deterministic stable hashes of schema names. Dataset IDs are derived from dataset name, feature schema version, and label schema version.

## 9. Validation Rules

Feature validation requires `feature_id`, `feature_name`, `feature_schema_version`, a supported `feature_type`, at least one of `run_id` or `awr_id`, and a feature value that reasonably matches the declared feature type.

Label validation requires `label_id`, a supported `label_name`, `label_schema_version`, a supported `label_type`, at least one of `run_id` or `awr_id`, confidence between 0.0 and 1.0, and audit evidence for supervised labels where available.

Dataset validation requires `dataset_id`, `dataset_name`, `feature_schema_version`, `label_schema_version`, feature records, label records, `runtime_influence=false`, and `runtime_active=false`. Validation reports unmatched feature and label records in validation notes.

## 10. Lineage Requirements

Dataset lineage must identify feature schema version, label schema version, source records, dataset purpose, creation actor, and validation notes.

Lineage is metadata only. It does not call parsers, recompute scores, fetch database records, contact OCI, contact Oracle Agent Memory, call LLMs, or invoke network services.

## 11. Evidence Requirements

Labels must be auditable. Supervised labels must reference a source outcome, source record, feedback record, action record, recommendation record, or evidence reference where available.

Evidence references do not become deterministic runtime truth by themselves. Evidence supports future review and governance; it does not change parser output, scoring truth, decision truth, recommendation truth, or dashboard truth.

## 12. Runtime Boundary

Schema metadata has no runtime activation path. Dataset records have `runtime_influence=false` and `runtime_active=false`.

No model training happens here. No runtime scoring changes happen here. learned_model(x) is not implemented. Score_ml(x) is not implemented. Score(x, t) is not implemented. Deterministic runtime remains authoritative.

## 13. Non-Goals

Phase 7T schemas do not implement model training, model inference, shadow ML scoring, trend-aware scoring, backtesting, explainability, model registry behavior, dashboard ML controls, CLI ML commands, database writes, OCI dependencies, Oracle Agent Memory dependencies, semantic recall dependencies, LLM calls, network calls, or Phase 8 sizing/TCO.

Phase 7T schemas do not modify parser behavior, parser output, scoring logic, scoring weights, scoring thresholds, decision logic, recommendation logic, recommendation ranking, dashboard behavior, CLI behavior, or the Phase 4I output contract.

## 14. Acceptance Criteria

Acceptance requires deterministic feature schema metadata, deterministic label schema metadata, supported type constants, supported label name constants, supervised/excluded label constants, deterministic ID helpers, validation helpers, serialization helpers, and local tests.

Acceptance also requires explicit statements that unknown_outcome is excluded from supervised labels by default, labels must be auditable, schemas are versioned, no model training happens here, no runtime scoring changes happen here, dataset is not a model, dataset validation is not training, `runtime_influence=false`, `runtime_active=false`, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
