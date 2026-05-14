# Phase 7AA.5 Parser Integration Model

## 1. Purpose

This document defines the Phase 7AA.5 parser integration result model. The model records parser backlog or parser evolution consideration only and preserves current parser authority.

## 2. ParserIntegrationResult Object Shape

`ParserIntegrationResult` contains:

- `result_id`
- `parser_section`
- `signal_name`
- `parser_evolution_id`
- `parser_backlog_id`
- `proposed_parser_change_type`
- `parser_runtime_authoritative`
- `selected_parser_action`
- `selected_parser_source`
- `parser_change_summary`
- `gate_allowed_for_consideration`
- `fallback_to_current_parser`
- `fallback_reason`
- `phase4i_contract_preserved`
- `awr_regression_required`
- `scoring_regression_required`
- `unknown_signal_safety_required`
- `runtime_parser_applied`
- `runtime_mutation_performed`
- `runtime_active`
- `runtime_influence_granted`
- `validation_reference`
- `rollback_reference`
- `awr_regression_reference`
- `scoring_regression_reference`
- `denied_reasons`
- `warnings`
- `rationale`
- `created_by`
- `notes`

## 3. Supported Parser Sources

Supported sources are:

- `current_parser`
- `parser_evolution`
- `parser_backlog`
- `none`

`current_parser` is the fallback and default source.

## 4. Supported Parser Actions

Supported actions are:

- `keep_current_parser`
- `consider_parser_backlog`
- `consider_parser_evolution`
- `deny_parser_integration`

Consideration actions do not apply parser changes.

## 5. Selection Rules

The adapter may select parser consideration only when the gate allows consideration, runtime context validates, Phase 4I contract is preserved, parser backlog or parser evolution input is valid, validation reference exists, rollback reference exists, AWR regression reference exists, scoring regression reference exists, and unknown signal safety is preserved.

Selection order is deterministic:

1. `parser_backlog`
2. `parser_evolution`
3. `current_parser`

## 6. Fallback Rules

Fallback to current parser is required if any gate, context, reference, or parser candidate condition fails.

Fallback results use `selected_parser_source=current_parser`, `selected_parser_action=keep_current_parser`, and `fallback_to_current_parser=true`.

## 7. Phase 4I / AWR / Scoring Regression Rules

Parser consideration requires:

- Phase 4I contract validation.
- AWR regression validation.
- Scoring regression check.
- Unknown signal safety validation.
- Rollback reference.

Missing references deny consideration and fall back to current parser.

## 8. Validation Rules

Validation requires:

- Non-empty `result_id`.
- Supported selected parser source.
- Supported selected parser action.
- Non-empty parser change summary.
- Non-empty rationale.
- List-shaped denied reasons and warnings.
- `parser_runtime_authoritative=true`.
- `phase4i_contract_preserved=true`.
- `awr_regression_required=true`.
- `scoring_regression_required=true`.
- `unknown_signal_safety_required=true`.
- `runtime_parser_applied=false`.
- `runtime_mutation_performed=false`.
- `runtime_active=false`.
- `runtime_influence_granted=false`.

Unsafe runtime flags are rejected.

## 9. Serialization Rules

Serialization uses deterministic dictionaries. Deserialization reconstructs and validates `ParserIntegrationResult` objects. No serialization helper reads files, calls services, imports parser modules, or mutates runtime state.

## 10. Deterministic ID Rules

Parser integration result IDs use stable input values:

`ADAPTIVE-PARSER-RESULT-<SECTION>-<SIGNAL>-<SOURCE>`

IDs use no random UUID, no timestamp, no database sequence, and no external service.

## 11. Runtime Safety Rules

The model never applies parser changes:

- `runtime_parser_applied=false`
- `runtime_mutation_performed=false`
- `runtime_active=false`
- `runtime_influence_granted=false`
- `parser_runtime_authoritative=true`

No runtime parser changes are applied. No parser module is modified.

## 12. Non-Goals

This model does not implement parser mutation, parser regex changes, section registry updates, unknown signal classification, scoring changes, recommendation changes, decision changes, dashboard controls, CLI commands, rollback execution, or `run_analysis.py` integration.

Phase 8 sizing/TCO is not implemented.

## 13. Acceptance Criteria

- Parser integration result model exists.
- Supported parser sources and actions are explicit.
- Selection is consideration only.
- Fallback to current parser is required.
- Parser regression references are required for consideration.
- Runtime flags remain false.
- Current parser remains authoritative.
- No runtime parser changes are applied.
- No parser module is modified.
