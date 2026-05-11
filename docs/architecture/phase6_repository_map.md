# Phase 6 Repository Map

This document maps the Phase 6 repository structure for reviewers, operators, and engineers continuing development. It identifies the deterministic runtime truth path and the isolated semantic reviewer-assist path.

## 1. Runtime Analysis Layer

Important paths:

- `scripts/run_analysis.py`
- `src/loader/`
- `src/parser/`
- `src/analysis/`
- `src/recommendation/`
- `src/models/`

Runtime truth path:

```text
Input files
  -> loader source inventory
  -> parser extraction
  -> feature model and frontend contract
  -> scoring and decision engines
  -> deterministic recommendations
  -> governed memory persistence
  -> dashboard rendering
```

The runtime path is deterministic and authoritative. Semantic recall is not part of the runtime truth path.

## 2. Dashboard Layer

Important paths:

- `src/reporting/html_dashboard.py`
- `src/reporting/ai_display_metadata.py`
- `awr_dashboard/*.html`

The dashboard layer renders deterministic diagnosis, governed memory visibility, parser review visibility, governance and artifact visibility, and semantic recall status. It does not approve, classify, activate, or alter runtime truth.

Generated dashboard files are intentionally useful for review and demo snapshots. Source changes belong in `src/reporting/html_dashboard.py`.

## 3. Memory Layer

Important paths:

- `src/memory/memory_agent.py`
- `src/memory/memory_orchestrator.py`
- `src/memory/memory_recall.py`
- `dbschema/memory/phase6_memory.sql`

The governed memory layer persists structured records for runs, recommendations, actions, outcomes, feedback, unknown signals, governance requests, and knowledge artifacts.

Structured recall is read-only and query-oriented. It does not alter parser behavior, scoring, recommendations, decisions, or dashboard truth.

## 4. Governance Layer

Important paths:

- `scripts/review_unknown_signal.py`
- `scripts/create_knowledge_request.py`
- `scripts/approve_knowledge_request.py`
- `scripts/materialize_knowledge.py`
- `src/memory/governance_semantic_assist.py`

Governance workflows are human-controlled. Review, approval, and artifact materialization require explicit command invocation and actor context.

Governance semantic assistance is read-only reviewer context. It does not determine governance outcomes.

## 5. Semantic Layer

Important paths:

- `src/memory/oracle_agent_memory_adapter.py`
- `src/memory/semantic_recall_service.py`
- `src/memory/governance_semantic_assist.py`
- `scripts/test_oracle_agent_memory.py`

Semantic isolation path:

```text
Optional Oracle Agent Memory configuration
  -> adapter boundary
  -> curated semantic recall service
  -> reviewer-assist summaries
  -> dashboard or CLI visibility as non-authoritative context
```

Semantic recall is optional, non-authoritative, and marked with `runtime_influence=false`. It is not consumed by parser, scoring, decision, recommendation, or dashboard truth paths.

## 6. CLI Layer

Important paths:

- `scripts/awr_memory_cli.py`
- `scripts/recall_memory.py`
- `scripts/record_action.py`
- `scripts/record_outcome.py`
- `scripts/record_feedback.py`
- `scripts/review_unknown_signal.py`
- `scripts/create_knowledge_request.py`
- `scripts/approve_knowledge_request.py`
- `scripts/materialize_knowledge.py`

Major operational entrypoint:

```text
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py status
```

The unified CLI groups operations into `recall`, `review`, `governance`, `artifact`, `semantic`, and `status`. Read-only commands perform no writes. Write commands are explicit and require actor attribution.

## 7. Validation Layer

Important paths:

- `tests/test_phase6_validation.py`
- `scripts/run_phase6_validation.py`
- `scripts/run_phase6_readiness_check.py`
- `tests/test_awr_memory_cli.py`
- `tests/test_memory_recall.py`
- `tests/test_semantic_recall_service.py`
- `tests/test_governance_semantic_assist.py`
- `tests/test_oracle_agent_memory.py`

Primary validation commands:

```text
PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py
PYTHONPATH=. .venv/bin/python scripts/run_phase6_readiness_check.py
```

Validation confirms runtime isolation, semantic isolation, governance safety, dashboard truth preservation, CLI operational safety, recall correctness, import isolation, and write discipline.

## 8. Documentation Layer

Important paths:

- `docs/architecture/README.md`
- `docs/architecture/phase6_memory_architecture.md`
- `docs/architecture/phase6_operational_model.md`
- `docs/architecture/phase6_acceptance_criteria.md`
- `docs/architecture/phase6_validation_matrix.md`
- `docs/architecture/phase6_production_readiness.md`
- `docs/architecture/phase6_release_certification.md`
- `docs/architecture/phase6_operational_checklist.md`
- `docs/architecture/phase6_component_inventory.md`
- `docs/architecture/phase6_repository_map.md`
- `docs/architecture/phase6_release_notes.md`
- `docs/architecture/phase6_demo_walkthrough.md`

The documentation layer is the release-quality package for architecture review, operational onboarding, repository handoff, executive walkthrough, and engineering continuation.

## 9. OCI/Provider Layer

Important paths:

- `ai_providers/ai_provider_router.py`
- `ai_providers/oci_provider_adapter.py`
- `ai_providers/openai_provider_adapter.py`
- `src/analysis/ai_provider_adapter.py`
- `src/reporting/ai_display_metadata.py`

Provider routing remains deterministic and controlled by configuration. Provider/model identity display is deterministic and does not use LLM-generated values.

OCI provider execution and Oracle Agent Memory are separate concerns. Runtime AI narrative generation does not make semantic recall authoritative.

## 10. Tests Layout

Important test groups:

- Runtime and contract tests: `tests/test_frontend_contract.py`, `tests/test_decision_engine.py`, `tests/test_recommendation_engine.py`
- Memory workflow tests: `tests/test_memory_orchestrator.py`, `tests/test_action_tracking.py`, `tests/test_outcome_tracking.py`, `tests/test_feedback_capture.py`
- Governance tests: `tests/test_unknown_signal_review.py`, `tests/test_knowledge_approval.py`, `tests/test_knowledge_materialization.py`
- Recall and semantic tests: `tests/test_memory_recall.py`, `tests/test_oracle_agent_memory.py`, `tests/test_semantic_recall_service.py`, `tests/test_governance_semantic_assist.py`
- CLI and validation tests: `tests/test_awr_memory_cli.py`, `tests/test_phase6_validation.py`

Tests are designed to avoid live Oracle Agent Memory requirements unless explicitly using the live prototype validation script.
