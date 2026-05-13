# Phase 7AA.2 Runtime Context Model

## 1. Purpose

The Phase 7AA.2 runtime context model defines local deterministic dataclasses and helpers for building a read-only adaptive runtime context. The model normalizes already-existing Phase 7 records for future adapters without applying changes or activating adaptive behavior.

## 2. AdaptiveRuntimeContext Object Shape

`AdaptiveRuntimeContext` contains `context_id`, `runtime_mode`, `deterministic_runtime_authoritative`, `fallback_to_deterministic`, `phase4i_contract_preserved`, `runtime_influence_applied`, `runtime_mutation_performed`, `adaptive_runtime_config`, `gate_results`, scoring/recommendation/parser/trend/shadow ML/model registry/explainability/materialization sections, validation context, readiness context, denied reasons, warnings, required next steps, `created_by`, and `notes`.

The context requires `deterministic_runtime_authoritative=true`, `fallback_to_deterministic=true`, `phase4i_contract_preserved=true`, `runtime_influence_applied=false`, and `runtime_mutation_performed=false`.

## 3. AdaptiveRuntimeSection Object Shape

`AdaptiveRuntimeSection` contains `section_name`, `available`, `item_count`, `eligible_count`, `allowed_for_consideration_count`, `runtime_active_count`, `summaries`, and `warnings`. `runtime_active_count` must remain 0.

The section also exposes read-only derived counts for review count, result count, output count, model count, registered model count, shadow eligibility count, runtime eligibility count, artifact count, runtime-sensitive count, and domains when those values are present in summaries.

## 4. AdaptiveParserRuntimeSection Object Shape

`AdaptiveParserRuntimeSection` contains `section_name`, `available`, `parser_evolution_count`, `parser_backlog_count`, `runtime_active_count`, `phase4i_contract_required`, `awr_regression_required`, `scoring_regression_required`, `summaries`, and `warnings`. It requires `phase4i_contract_required=true`, `awr_regression_required=true`, `scoring_regression_required=true`, and `runtime_active_count=0`.

## 5. Input Sources

Input sources are optional in-memory dictionaries or dataclasses. Supported sources include report metadata, Phase 4I output summary, adaptive runtime config, component eligibilities, gate results, materialization artifacts, adaptive scoring reviews, recommendation rule evolutions, parser mapping evolutions, trend-aware scores, shadow ML outputs, ML explanations, model registry entries, validation references, and readiness references.

## 6. Section Summaries

Section summaries are deterministic dictionaries derived from the supplied in-memory inputs. Summaries keep source identifiers, status fields, advisory fields, domain fields, runtime-sensitive fields, and other serializable metadata without invoking source modules or applying changes.

## 7. Validation Rules

Validation requires a non-empty context ID, a runtime mode supported by the 7AA.1 gate, deterministic runtime authority, deterministic fallback, Phase 4I contract preservation, no runtime influence applied, no runtime mutation performed, inactive gate results, inactive sections, list-shaped denied reasons, list-shaped warnings, and list-shaped required next steps. Section counts must be non-negative, and `runtime_active_count` must remain 0.

## 8. Serialization Rules

Serialization uses stable dictionaries with explicit field names. Context, generic sections, and parser sections round-trip through `to_dict` and `from_dict` helpers without file reads, DB reads, network calls, dashboard calls, CLI calls, or `run_analysis.py` calls.

## 9. Deterministic ID Rules

Context IDs follow `ADAPTIVE-RUNTIME-CONTEXT-<MODE>-<PHASE4I_REFERENCE>`. IDs use no UUID, timestamp, database sequence, or external service and remain stable for the same mode and Phase 4I reference.

## 10. Empty Context Rules

`empty_adaptive_runtime_context` creates a safe deterministic empty context. It uses `deterministic_only` mode, keeps deterministic runtime authoritative, keeps fallback to deterministic runtime required, preserves Phase 4I contract protection, keeps `runtime_influence_applied=false`, keeps `runtime_mutation_performed=false`, sets all sections unavailable with zero item counts, and includes required next steps reminding future adapters to re-evaluate the 7AA.1 gate.

## 11. Runtime Safety Rules

The context does not apply changes and context does not activate adaptive behavior. `runtime_active_count` must remain 0, `runtime_influence_applied=false`, and `runtime_mutation_performed=false`. If supplied inputs claim `runtime_active=true`, validation fails clearly instead of converting the input into runtime authority.

## 12. Non-Goals

Phase 7AA.2 does not implement scoring adapters, recommendation adapters, parser adapters, fallback execution, rollback execution, dashboard runtime controls, CLI runtime commands, database writes, OCI calls, Oracle Agent Memory calls, semantic recall calls, LLM calls, network calls, or Phase 8 sizing/TCO.

## 13. Acceptance Criteria

The runtime context model is accepted when the adaptive runtime context model exists, the builder exists, section models exist, parser-specific validation exists, empty context is safe, serialization is deterministic, validation rejects unsafe runtime-active or mutation-applied states, context is read-only, context is not runtime activation, `runtime_active_count` remains 0, `runtime_influence_applied=false`, `runtime_mutation_performed=false`, deterministic runtime remains authoritative, fallback to deterministic runtime remains required, context does not apply changes, context does not activate adaptive behavior, and Phase 8 sizing/TCO is not implemented.
