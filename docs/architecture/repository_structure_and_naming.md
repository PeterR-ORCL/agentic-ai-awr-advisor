# Repository Structure and Naming Policy

This document defines repository structure, naming semantics, and artifact ownership for the Agentic AI AWR Advisor project. It exists to prevent architectural drift as Phase 6 memory, governance, recall, provider adapters, and future interactive control layers evolve.

## 1. Architectural Naming Semantics

### `_engine.py`

Engine modules contain deterministic computation. They transform explicit inputs into explicit outputs, have no workflow autonomy, and do not own persistence.

Examples:

- `decision_engine.py`
- `scoring_engine.py`
- `recommendation_engine.py`
- `trend_engine.py`

### `_agent.py`

Agent modules provide operational coordination. They own bounded workflow behavior, may mediate persistence or retrieval, and may coordinate tools or services. This suffix must not be used for pure deterministic utilities.

Example:

- `memory_agent.py`

### `_orchestrator.py`

Orchestrator modules coordinate multiple systems or components. They are runtime or cross-boundary control layers.

Examples:

- `memory_orchestrator.py`
- future `ingest_orchestrator.py`

### `_model.py`

Model modules define domain structures, schemas, contracts, dataclasses, and structured representations.

Examples:

- `feature_model.py`
- future `frontend_contract_model.py`

### `_adapter.py`

Adapter modules isolate external API, provider, cloud, or model integration boundaries.

Examples:

- future `oci_provider_adapter.py`
- future `openai_provider_adapter.py`

### `_reader.py`

Reader modules read files or raw content. They do not interpret domain meaning.

### `_loader.py`

Loader modules discover or stage sources. They do not interpret AWR content.

### `_parser.py`

Parser modules perform deterministic parsing or extraction. They do not discover sources and do not own orchestration autonomy.

### `_catalog.py`

Catalog modules contain static or domain catalogs.

### `_contract.py`

Contract modules define stable input or output contract definitions.

### `_harness.py`

Harness modules coordinate validation or test execution.

## 2. What Should Not Be Called an Agent

Do not use `_agent.py` for:

- deterministic parsers
- deterministic loaders
- scoring logic
- decision logic
- recommendation rules
- simple provider wrappers
- static model/catalog files

Agents must coordinate behavior; they are not just files that use AI.

## 3. Current Active Role Classification

`src/loader/awr_loader.py`  
→ loader utility/module

`src/parser/awr_parser.py`  
→ parser utility/module

`src/parser/*_parser.py`  
→ parser utilities

`src/analysis/decision_engine.py`  
→ engine

`src/analysis/trend_engine.py`  
→ engine

`src/analysis/recommendation_engine.py`  
→ engine

`src/recommendation/recommendation_engine.py`  
→ engine

`src/analysis/issue_detector.py`  
→ engine candidate / future naming cleanup

`src/analysis/similarity_intelligence.py`  
→ engine candidate / future naming cleanup

`src/memory/memory_agent.py`  
→ agent

`src/memory/memory_orchestrator.py`  
→ orchestrator

`src/models/*.py`  
→ models/contracts

`src/reporting/html_dashboard.py`  
→ deterministic renderer / utility

`ai_providers/*`  
→ provider adapter package / future adapter rename candidate

`scripts/*`  
→ CLI/runtime entrypoints

## 4. Generated Artifact Policy

### `awr_dashboard/`

The `awr_dashboard/` directory contains the generated dashboard HTML bundle. It is intentionally tracked for demo, review, and reference purposes.

The source of generation is:

- `src/reporting/html_dashboard.py`
- `scripts/run_analysis.py`

Generated HTML may change after `run_analysis.py`. Commit generated HTML only when intentionally updating the dashboard snapshot.

### `awr_dashboard.html`

`awr_dashboard.html` is an ad hoc/generated single-file artifact. It should remain ignored and untracked unless explicitly needed.

### Top-level Validation Artifacts

Top-level `validation_*.json` and `scoring_diagnostics_*` files are generated validation artifacts. They are generally not source of truth unless explicitly promoted.

## 5. Data Pack Policy

### `data/input/`

`data/input/` is the active local staging input directory.

### Validation and Test Data Packs

The following directories are validation/test data packs and should not be casually renamed:

- `data/input_15_gold/`
- `data/good_parse_mix_21/`
- `data/oracle_awr_adversarial_24/`

### `data/output/`

`data/output/` contains generated output and should remain ignored/generated.

## 6. Schema / DBSHEMA Policy

### `dbschema/memory/phase6_memory.sql`

`dbschema/memory/phase6_memory.sql` is the canonical Phase 6 memory schema entry point.

### `dbschema/*.sql`

SQL files under `dbschema/` are schema, view, validation, migration, or patch assets.

### `dbschema/*.log`

Log files under `dbschema/` are generated validation or execution logs. They are future candidates for `dbschema/logs/` or an ignore policy.

### Future Desired Structure

Future cleanup may organize database assets as:

- `dbschema/migrations/`
- `dbschema/memory/`
- `dbschema/validation/`
- `dbschema/logs/`
- `dbschema/archive/`

Do not reorganize without a dedicated migration cleanup commit.

## 7. Examples / Archive Policy

### `examples/`

`examples/` contains reference snapshots and demo artifacts. Use phase, version, or date naming when possible.

### `Old_Versions/`

`Old_Versions/` is a local/archive area. It is not active source and should remain ignored unless intentionally promoted to `docs/archive/`.

### `awr_dashboard_orig.html`

`awr_dashboard_orig.html` is a legacy/generated artifact. It is a future candidate for `examples/archive/` or `docs/archive/`.

## 8. Provider Adapter Naming Policy

The provider package uses explicit adapter and router naming for external AI provider boundaries.

Current provider boundary files:

- `ai_providers/ai_provider_router.py`
- `ai_providers/oci_provider_adapter.py`
- `ai_providers/openai_provider_adapter.py`
- `src/analysis/ai_provider_adapter.py`

Rules:

- provider/model identity display must be deterministic
- do not use LLM to determine provider/model display
- `AI_PROVIDER` must remain authoritative
- `OCI_MODEL` may be used for friendly display
- `OCI_MODEL_ID` remains backend identifier

## 9. Rename / Refactor Guardrails

Before renaming any architectural module:

1. classify role
2. identify import impact
3. update tests
4. validate `run_analysis.py`
5. confirm no Phase 4I contract drift
6. confirm no parser/scoring/recommendation behavior drift
7. confirm no memory behavior drift

Rename commits must be dedicated and small.

No mixed commits:

- do not combine renames with logic changes
- do not combine schema changes with source renames
- do not combine dashboard visual changes with provider adapter renames

## 10. Locked Architectural Boundaries

Memory does not equal learning.
Approval does not equal activation.
Knowledge artifacts do not influence runtime decisions.
Dashboard visibility does not equal control-plane authority.
Engines compute deterministic truth.
Agents coordinate bounded workflows.
Orchestrators coordinate cross-component execution.
Adapters isolate external/provider boundaries.
