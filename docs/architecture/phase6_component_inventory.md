# Phase 6 Component Inventory

This document is the authoritative component inventory for Phase 6. It distinguishes deterministic runtime components from governed memory, governance workflows, semantic reviewer-assist systems, dashboard visibility, CLI operations, validation, and documentation.

## 1. Runtime Components

| Component | Purpose | Authority | Runtime Influence | Access Mode | Validation Coverage |
| --- | --- | --- | --- | --- | --- |
| `scripts/run_analysis.py` | Main runtime entrypoint for ingestion, parsing, analysis, memory persistence, and dashboard generation. | Authoritative runtime coordinator. | Yes, for deterministic runtime execution. | Runtime execution. | Phase 6 validation harness, readiness check, py_compile. |
| `src/loader/awr_loader.py` | Discovers and stages local AWR input sources. | Deterministic utility. | Yes, source inventory only. | Read-only input discovery. | Loader/parser boundary tests. |
| `src/parser/awr_parser.py` | Extracts AWR sections, metrics, topology hints, parser diagnostics, and unknown signals. | Authoritative parser output. | Yes, deterministic parser truth. | Deterministic parsing. | Parser boundary tests and runtime validation. |
| `src/parser/*_parser.py` | Domain parsers for CPU, waits, SQL, topology, IO, metadata, and related AWR sections. | Authoritative parser utilities. | Yes, deterministic extraction only. | Deterministic parsing. | Existing parser and integration validation. |
| `src/analysis/frontend_contract.py` | Builds the stable frontend/Phase 4I contract. | Authoritative contract layer. | Yes, dashboard/runtime output contract. | Deterministic transformation. | Frontend contract and Phase 6 validation tests. |
| `src/analysis/decision_engine.py` | Determines deterministic posture and issue prioritization. | Authoritative deterministic engine. | Yes. | Deterministic computation. | Decision and Phase 6 validation tests. |
| `src/analysis/recommendation_engine.py` | Produces deterministic action guidance. | Authoritative deterministic engine. | Yes. | Deterministic computation. | Recommendation and Phase 6 validation tests. |
| `src/recommendation/recommendation_engine.py` | Recommendation engine package implementation. | Authoritative deterministic engine. | Yes. | Deterministic computation. | Recommendation validation tests. |
| `src/analysis/ai_narrative_generator.py` | Prepares safe narrative input and optional AI phrasing. | Non-authoritative wording layer. | No effect on deterministic truth. | Optional presentation generation. | Narrative truthfulness and Phase 6 validation. |

Runtime components remain the deterministic truth path. Semantic recall, governance assistance, and Oracle Agent Memory are not authoritative runtime components.

## 2. Memory Components

| Component | Purpose | Authority | Runtime Influence | Access Mode | Validation Coverage |
| --- | --- | --- | --- | --- | --- |
| `src/memory/memory_agent.py` | Coordinates governed memory persistence workflows. | Authoritative governed memory writer. | No scoring or parser influence. | Explicit writes. | Memory orchestrator and persistence tests. |
| `src/memory/memory_orchestrator.py` | Coordinates memory lifecycle operations and exposes memory services. | Governed memory orchestration. | No runtime truth influence. | Explicit orchestration. | Memory orchestrator tests. |
| `src/memory/memory_recall.py` | Read-only structured recall over governed memory tables. | Observational structured recall. | No runtime influence. | Read-only. | Memory recall tests and Phase 6 validation. |
| `dbschema/memory/phase6_memory.sql` | Canonical Phase 6 governed memory schema entry point. | Schema source for governed memory. | No runtime computation. | DDL asset. | Schema deployment and operational validation. |

Governed memory is deterministic, structured, reviewable, and auditable. It is distinct from semantic recall and does not imply autonomous learning.

## 3. Governance Components

| Component | Purpose | Authority | Runtime Influence | Access Mode | Validation Coverage |
| --- | --- | --- | --- | --- | --- |
| `scripts/review_unknown_signal.py` | Explicit unknown signal review operation. | Human-controlled governance action. | None. | Write command with actor context. | Unknown signal review tests. |
| `scripts/create_knowledge_request.py` | Creates governed knowledge update requests. | Human-controlled governance action. | None. | Explicit write. | Knowledge approval tests. |
| `scripts/approve_knowledge_request.py` | Records approval status for knowledge requests. | Human-controlled governance action. | None. | Explicit write. | Knowledge approval tests. |
| `scripts/materialize_knowledge.py` | Materializes approved knowledge artifacts as controlled records. | Human-controlled artifact operation. | None. | Explicit write. | Knowledge materialization tests. |
| `src/memory/governance_semantic_assist.py` | Retrieves optional semantic context for human reviewers. | Non-authoritative reviewer assistance. | None. | Read-only semantic assist. | Governance semantic assist tests. |

Governance remains human-controlled. No Phase 6 component auto-approves, auto-rejects, auto-classifies parser signals, or activates artifacts.

## 4. Semantic Components

| Component | Purpose | Authority | Runtime Influence | Access Mode | Validation Coverage |
| --- | --- | --- | --- | --- | --- |
| `src/memory/oracle_agent_memory_adapter.py` | Optional Oracle Agent Memory prototype adapter. | Non-authoritative semantic memory boundary. | None. | Optional semantic read/write prototype only. | Oracle Agent Memory tests. |
| `src/memory/semantic_recall_service.py` | Curated semantic recall APIs for analyst assistance. | Non-authoritative semantic context. | None. | Read-only recall. | Semantic recall service tests. |
| `scripts/test_oracle_agent_memory.py` | Prototype validation script for Oracle Agent Memory connectivity and semantic recall. | Validation utility. | None. | Optional prototype validation. | Oracle Agent Memory tests. |

Semantic systems are reviewer-assist only. They must never affect parser output, scoring, decisions, recommendations, governance approval, artifact activation, dashboard truth, or runtime analysis.

## 5. Dashboard Components

| Component | Purpose | Authority | Runtime Influence | Access Mode | Validation Coverage |
| --- | --- | --- | --- | --- | --- |
| `src/reporting/html_dashboard.py` | Deterministic HTML dashboard renderer. | Presentation layer over deterministic and read-only memory payloads. | No runtime computation influence. | Render-only. | Dashboard truth validation. |
| `src/reporting/ai_display_metadata.py` | Deterministic provider/model display metadata. | Presentation metadata. | None. | Read-only formatting. | Display validation and py_compile. |
| `awr_dashboard/*.html` | Generated dashboard snapshot bundle. | Generated artifact. | None. | Static output. | Dashboard grep and validation checks. |

The dashboard visualizes deterministic truth, governed memory, governance state, artifacts, and semantic visibility. It is not a control-plane authority.

## 6. CLI Components

| Component | Purpose | Authority | Runtime Influence | Access Mode | Validation Coverage |
| --- | --- | --- | --- | --- | --- |
| `scripts/awr_memory_cli.py` | Unified Phase 6 CLI for recall, review, governance, artifact, semantic, and status operations. | Operational control surface. | None on deterministic truth. | Read-only and explicit write subcommands. | CLI tests and Phase 6 validation. |
| `scripts/recall_memory.py` | Structured recall CLI. | Read-only operational utility. | None. | Read-only. | Memory recall tests. |
| `scripts/record_action.py` | Records tracked actions. | Explicit governed memory write. | None. | Explicit write. | Action tracking tests. |
| `scripts/record_outcome.py` | Records action outcomes. | Explicit governed memory write. | None. | Explicit write. | Outcome tracking tests. |
| `scripts/record_feedback.py` | Records feedback. | Explicit governed memory write. | None. | Explicit write. | Feedback capture tests. |

CLI write commands require intentional invocation and actor attribution. Semantic CLI commands remain read-only and non-authoritative.

## 7. Validation Components

| Component | Purpose | Authority | Runtime Influence | Access Mode | Validation Coverage |
| --- | --- | --- | --- | --- | --- |
| `tests/test_phase6_validation.py` | Architectural isolation and safety validation. | Validation authority. | None. | Test only. | Phase 6 validation suite. |
| `scripts/run_phase6_validation.py` | Consolidated Phase 6 validation runner. | Validation runner. | None. | Test execution. | 61-test validation summary. |
| `scripts/run_phase6_readiness_check.py` | Production readiness wrapper around validation and static readiness checks. | Readiness verification. | None. | Validation execution. | Readiness summary JSON. |
| `tests/test_awr_memory_cli.py` | Unified CLI safety tests. | Test coverage. | None. | Test only. | CLI operational safety. |
| `tests/test_memory_recall.py` | Structured recall tests. | Test coverage. | None. | Test only. | Recall correctness and ordering. |
| `tests/test_semantic_recall_service.py` | Semantic recall service tests. | Test coverage. | None. | Test only. | Semantic non-authoritativeness. |
| `tests/test_governance_semantic_assist.py` | Governance semantic assist tests. | Test coverage. | None. | Test only. | Reviewer-assist safety. |

Validation confirms deterministic runtime isolation, semantic non-authoritativeness, governance safety, dashboard truth preservation, CLI discipline, recall correctness, and write discipline.

## 8. Documentation Components

| Component | Purpose | Authority | Runtime Influence | Access Mode | Validation Coverage |
| --- | --- | --- | --- | --- | --- |
| `docs/architecture/phase6_memory_architecture.md` | Authoritative Phase 6 architecture overview. | Architecture documentation. | None. | Read-only. | Documentation review. |
| `docs/architecture/phase6_operational_model.md` | Operational model and failure behavior. | Operational documentation. | None. | Read-only. | Documentation review. |
| `docs/architecture/phase6_acceptance_criteria.md` | Formal acceptance criteria. | Acceptance documentation. | None. | Read-only. | Documentation review. |
| `docs/architecture/phase6_validation_matrix.md` | Validation matrix. | Validation documentation. | None. | Read-only. | Validation review. |
| `docs/architecture/phase6_production_readiness.md` | Production readiness certification. | Readiness documentation. | None. | Read-only. | Readiness review. |
| `docs/architecture/phase6_release_certification.md` | Release certification. | Certification documentation. | None. | Read-only. | Readiness review. |
| `docs/architecture/phase6_operational_checklist.md` | Deployment and demo checklist. | Operational checklist. | None. | Read-only. | Operator review. |
| `docs/architecture/phase6_component_inventory.md` | This component inventory. | Inventory documentation. | None. | Read-only. | Documentation review. |
| `docs/architecture/phase6_repository_map.md` | Repository structure map. | Repository navigation. | None. | Read-only. | Documentation review. |
| `docs/architecture/phase6_release_notes.md` | Release summary. | Release documentation. | None. | Read-only. | Release review. |
| `docs/architecture/phase6_demo_walkthrough.md` | Demo and executive walkthrough guide. | Demo documentation. | None. | Read-only. | Demo preparation. |

The documentation package is designed for architecture review, OCI demo presentation, operational onboarding, repository handoff, executive walkthrough, and engineering continuation.
