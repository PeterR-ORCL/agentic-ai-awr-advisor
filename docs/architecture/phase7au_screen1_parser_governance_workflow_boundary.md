# Phase 7AU Screen 1 Ingestion / Parser Governance Workflow Boundary

## 1. Purpose

Phase 7AU defines the architecture boundary for future Screen 1 ingestion, source intake, parser unknown review, parser mapping request, parser backlog linkage, knowledge request, knowledge artifact review, and artifact materialization workflows in the Agentic AI AWR Advisor project.

This phase is boundary-only. It documents how future Screen 1 workflows may create governed source, parser, and artifact review state without changing ingestion behavior, parser behavior, parser output, backend runtime truth, or the Phase 4I contract.

Screen 1 ingestion/parser/governance remains read-only until workflow phases explicitly add controls.

## 2. Scope

The scope is documentation, lifecycle definition, optional inert local boundary metadata, validation tests, and architecture index updates for future Screen 1 ingestion and parser governance workflow boundaries.

Phase 7AU defines:

- the Screen 1 ingestion and parser governance workflow boundary
- future workflow target types
- future workflow actions
- future workflow statuses
- actor, governed write-path, audit, backend execution mode, and output artifact lifecycle requirements
- why parser unknown review state is separate from parser runtime truth
- why parser mapping requests are not parser mutations
- why knowledge artifact review is not artifact materialization
- what shortcuts are forbidden before future 7AV, 7AW, 7AX, and 7AY phases exist

No Screen 1 ingestion/parser governance workflow is implemented in Phase 7AU.

## 3. Non-Goals

Phase 7AU adds no Screen 1 workflow UI. No Screen 1 workflow UI is added.

Phase 7AU adds no source intake buttons, local source controls, object storage controls, existing source controls, parser unknown action buttons, parser mapping request controls, parser backlog link controls, knowledge request controls, knowledge artifact approval controls, dashboard forms, JavaScript backend calls, API routes, CLI commands, or backend calls.

Phase 7AU invokes no source intake. No source intake is invoked.

Phase 7AU reads no local files. No local files are read.

Phase 7AU makes no object storage calls. No object storage calls are made.

Phase 7AU performs no database lookup. No DB lookup is made.

Phase 7AU performs no parser unknown classification. No parser unknown classification is performed.

Phase 7AU creates no parser mapping records. No parser mapping records are created.

Phase 7AU creates no parser candidates. No parser candidates are created.

Phase 7AU approves or rejects no knowledge artifacts. No knowledge artifacts are approved/rejected.

Phase 7AU invokes no governed write path. No governed write path is invoked.

Phase 7AU does not call `scripts/run_analysis.py`, wire into backend execution, write database records, write governance records, create parser mapping candidates, create parser backlog items, create knowledge artifact review records, materialize artifacts, or activate artifacts.

Phase 7AU changes no parser behavior. No parser output is changed. No parser extraction behavior is changed. No source ingestion behavior is changed. No scoring behavior is changed. No decision behavior is changed. No recommendation behavior is changed. No Phase 4I mutation is added.

Phase 7AU does not implement the future 7AV source intake control model, future 7AW parser unknown review UI/workflow, future 7AX knowledge artifact review workflow, future 7AY validation/certification, Phase 8 EM Extract, or Phase 8 sizing/TCO.

Phase 8 EM Extract implementation is not included. Phase 8 sizing/TCO is not implemented.

## 4. Why Screen 1 Needs Ingestion / Parser Governance Workflow

Screen 1 is the ingestion and parser governance surface. It helps reviewers understand what was ingested, what parser sections were found, what parser confidence signals exist, what unknown signals were observed, what governance references are visible, and what knowledge artifacts may later need review.

Future users may need to choose a source for intake, validate local source metadata, validate object storage source metadata, validate existing run source metadata, request source intake, review parser unknown signals, classify unknowns, request parser mappings, link unknowns to candidates or backlog items, review knowledge artifacts, and route artifact or mapping work to governance.

Those actions are sensitive because parser changes can corrupt extracted metrics, feature vectors, scoring, trend and anomaly logic, decisions, recommendations, generated dashboard state, and the Phase 4I output contract. Screen 1 workflow therefore must create governed review state only until later certified paths explicitly validate and apply changes.

## 5. Existing Screen 1 Read-Only Boundary

Existing Screen 1 behavior provides read-only ingestion, parser, governance, knowledge request, and artifact visibility. Existing Screen 1 exploration is browser-side and read-only.

Screen 1 may help a reviewer inspect source/run context, parser sections, parser diagnostics, parser confidence, parser unknown signals, governance rows, knowledge requests, and artifacts. That exploration does not create records, write governance state, execute analysis, validate source contents, change source intake, classify unknown signals, create parser mappings, create candidates, approve artifacts, change parser output, or mutate Phase 4I.

Phase 7AU preserves the existing read-only Screen 1 boundary.

## 6. Source Intake Boundary

Source intake is not automatic.

Future source intake may request an ingestion run for a validated source, but source intake is governed workflow state until a future backend execution path accepts it. A future request_source_intake action must require actor identity, source validation, backend execution mode, governed write-path validation, audit trail, and output artifact lifecycle handling.

Phase 7AU invokes no source intake, creates no ingestion run, reads no source, calls no object storage service, queries no existing run database, calls no `run_analysis.py`, and refreshes no dashboard artifact.

## 7. Local Source Boundary

Local source references are metadata only until future phases explicitly validate and execute source intake.

Future local source workflow may describe a path, file name, staged file id, checksum, expected file type, or availability hint. Those values do not authorize file loading and do not prove file existence.

Phase 7AU reads no local files, checks no filesystem paths, opens no AWR reports, parses no local contents, computes no checksums, and validates no local source content.

## 8. Object Storage Source Boundary

Object storage source references are metadata only until future phases explicitly validate credentials and execute source intake.

Future object storage workflow may describe namespace, bucket, object name, region, compartment, credential mode, URI, or configuration hints. Those values do not authorize object loading and do not prove object availability.

Phase 7AU imports no OCI SDK, validates no credentials, lists no buckets, downloads no objects, inspects no object metadata, and calls no object storage service. No object storage calls are made.

## 9. Parser Unknown Review Boundary

Parser unknown review is governed.

Future parser unknown review may let an actor inspect an unknown signal and classify it as parser gap, source gap, not applicable, or false positive. That classification creates governed review state only. It does not mutate parser output, parser mappings, parser confidence, parser diagnostics, source ingestion, feature vectors, scoring, decisions, recommendations, or Phase 4I.

Phase 7AU performs no parser unknown classification and creates no parser unknown review records.

## 10. Parser Mapping Request Boundary

Parser mapping request is not parser mutation.

Future parser mapping requests may propose that an unknown signal, parser section, parser diagnostic, or parser confidence issue should be considered for a parser mapping candidate. The request is governance path metadata only until future governed parser evolution and certified runtime integration paths handle it.

Phase 7AU creates no parser mapping records, creates no parser mapping candidates, updates no parser config, changes no parser code, and changes no parser extraction behavior.

## 11. Parser Backlog Boundary

Parser backlog linkage is governance routing, not runtime mutation.

Future Screen 1 workflow may link an unknown signal to a parser backlog item or request that a backlog item be created by a governed downstream process. That linkage is review and routing state only. It does not update parser mappings, parser output, parser runtime eligibility, parser adapter state, or Phase 4I.

Phase 7AU creates no parser backlog items and links no unknown signals to backlog items.

## 12. Knowledge Request Boundary

Knowledge requests are governed review context.

Future Screen 1 workflow may reference knowledge requests that explain parser behavior, source gaps, artifact needs, review notes, or proposed documentation. A knowledge request is not parser evidence, not a parser mapping, not source intake approval, not scoring evidence, and not recommendation truth.

Phase 7AU creates no knowledge requests and updates no knowledge request state.

## 13. Knowledge Artifact Boundary

Knowledge artifact review is governed.

Future knowledge artifact workflow may allow review, revision request, approval for review, rejection, or linkage to a parser/scoring/recommendation candidate. Artifact review does not activate artifacts and does not make artifacts runtime truth.

Phase 7AU approves no artifacts, rejects no artifacts, requests no revisions, links no artifacts to candidates, and creates no artifact review records. No knowledge artifacts are approved/rejected.

## 14. Artifact Materialization Boundary

Artifact materialization is outside Phase 7AU.

Future artifact materialization must use a governed materialization path, audit trail, explicit runtime gate posture, output artifact lifecycle, and certified validation before any artifact can influence runtime behavior.

Phase 7AU materializes no artifacts, activates no artifacts, writes no artifact payloads, and grants no runtime influence.

## 15. Actor Requirement

Future source actions require actor identity.

Future parser review actions require actor identity.

Future artifact workflows require actor identity.

Actor identity is required through the Phase 7AE actor/reviewer identity model before any future non-read-only Screen 1 action can be accepted. Browser state, URL hash state, selected parser card state, local dashboard state, semantic context, source metadata, or learning metadata cannot stand in for a human actor.

Phase 7AU does not implement actor identity and does not wire actor identity into Screen 1.

## 16. Governed Write-Path Requirement

Future parser review actions require governed write path.

Future source intake actions require governed write path.

Future artifact workflows require governed write path.

Any future non-read-only Screen 1 action must use the Phase 7AG governed write-path framework. The future write path must validate request shape, actor identity, authorization posture, target reference, workflow action, status transition, audit fields, source validation posture, backend execution mode where applicable, parser runtime protection, Phase 4I protection, failure behavior, and closure state before workflow state can be created.

Phase 7AU does not implement a governed write path and does not invoke one.

## 17. Audit Requirement

Future source actions require audit.

Future parser review actions require audit.

Future artifact workflows require audit trail.

Future audit records must identify the actor, target type, target reference, workflow action, requested status transition, source payload reference, parser signal reference when applicable, artifact reference when applicable, validation result, authorization result, governed write-path result, backend execution mode where applicable, output artifact reference where applicable, timestamp or sequence marker supplied by the future audit layer, notes when present, routed governance references when present, and closure state.

Phase 7AU creates no audit records.

## 18. Backend Execution Mode Requirement

Future source intake must use the Phase 7AF backend execution mode boundary and future source execution validation.

Future source validation or intake must declare whether it is static/read-only, local command generation, local backend execution, or future API/server execution before any execution can be considered.

Phase 7AU declares no execution mode for a real request, performs no backend execution, calls no `run_analysis.py`, starts no analysis run, and creates no ingestion run.

## 19. Output Artifact Lifecycle Requirement

Future source intake and review responses must use the Phase 7AH output artifact lifecycle.

Future responses may include source validation results, intake request previews, ingestion run records, parser review records, artifact review records, routed governance references, error artifacts, or closure artifacts. Those outputs must be traceable and must not silently replace parser output or generated dashboard artifacts.

Phase 7AU creates no output artifacts and refreshes no generated dashboard HTML.

## 20. Runtime Parser Boundary

Parser runtime remains authoritative.

No Screen 1 workflow can directly alter parser extraction behavior. Future Screen 1 workflow state may propose parser review, parser mapping, parser backlog linkage, or artifact review, but it cannot change parser code, parser config, section recognition, extracted metrics, unknown signal output, parser diagnostics, parser confidence, feature vectors, scoring, decisions, recommendations, runtime adapter state, or generated Phase 4I output.

Deterministic runtime remains authoritative.

## 21. Phase 4I Contract Boundary

Phase 4I contract remains protected.

No Screen 1 workflow can directly change Phase 4I. Phase 7AU adds no Phase 4I mutation and no Phase 4I contract change.

Any future workflow that proposes a Phase 4I-affecting correction must use a separately versioned, validated, governed backend contract. Workflow state alone cannot update Phase 4I, parser output, scoring output, decision output, recommendation output, dashboard payload shape, or generated dashboard artifacts.

## 22. Future Workflow Target Types

Future Screen 1 workflow target types are boundary concepts only in Phase 7AU:

- `source_intake`
- `local_source`
- `object_storage_source`
- `existing_run_source`
- `parser_unknown_signal`
- `parser_section`
- `parser_confidence`
- `parser_diagnostic`
- `parser_mapping_candidate`
- `parser_backlog_item`
- `knowledge_request`
- `knowledge_artifact`
- `artifact_materialization`
- `source_validation_result`
- `ingestion_run`

These target types are references for future governed workflow state. They are not mutable runtime artifacts in Phase 7AU.

## 23. Future Workflow Actions

Future Screen 1 workflow actions are boundary concepts only in Phase 7AU:

- `validate_source`
- `request_source_intake`
- `classify_unknown_signal`
- `mark_unknown_false_positive`
- `mark_unknown_not_applicable`
- `request_parser_mapping`
- `link_unknown_to_candidate`
- `link_unknown_to_backlog`
- `request_artifact_revision`
- `approve_artifact_for_review`
- `reject_artifact`
- `link_artifact_to_candidate`
- `add_parser_review_note`

All future actions require actor. All future actions require audit. All future actions require governed write path. None directly mutate parser output. None directly mutate runtime. None directly materialize artifacts.

## 24. Future Workflow Statuses

Future Screen 1 workflow statuses are boundary concepts only in Phase 7AU:

- `proposed`
- `under_review`
- `validated`
- `rejected`
- `needs_revision`
- `routed_to_governance`
- `linked_to_candidate`
- `linked_to_backlog`
- `closed`

Statuses are governed workflow state. Statuses are not parser runtime state.

## 25. Relationship to 7AD-7AI

Phase 7AD-7AI established dashboard workflow infrastructure:

- 7AD defined dashboard workflow boundaries.
- 7AE defined actor/reviewer identity metadata.
- 7AF defined backend execution mode metadata.
- 7AG defined governed write-path metadata.
- 7AH defined output artifact lifecycle metadata.
- 7AI validated the workflow infrastructure block.

Phase 7AU depends on those boundaries for future Screen 1 ingestion and parser governance workflows. It does not replace them and does not activate a workflow.

## 26. Relationship to 7AK Source Selection

Phase 7AK defined a metadata-only source selection model for future Screen 3 backend re-analysis. Source selection is not execution.

Phase 7AU uses the same governance principle for future Screen 1 source intake. Selecting or describing a local source, object storage source, or existing run source is not source intake. Source validation is not source loading. Future Screen 1 source intake must require actor identity, governed write path, backend execution mode, audit, and output artifact lifecycle.

Phase 7AU does not implement 7AK source execution and does not extend 7AK into Screen 1 source controls.

## 27. Relationship to Future 7AV

Future 7AV may define the Source Intake Control Model.

Phase 7AU only defines the boundary that future source intake is governed, actor-bound, audited, write-path protected, execution-mode aware, and output-lifecycle tracked. Phase 7AU does not implement source intake controls, source validation objects, source intake records, or ingestion runs.

## 28. Relationship to Future 7AW

Future 7AW may define Parser Unknown Review UI / Workflow.

Phase 7AU only defines the boundary that future parser unknown review creates governed review state and does not mutate parser output. Phase 7AU does not add parser unknown action buttons, classify unknown signals, request mappings, link candidates, link backlog items, or create review records.

## 29. Relationship to Future 7AX

Future 7AX may define Knowledge Artifact Review Workflow.

Phase 7AU only defines the boundary that future knowledge artifact review requires actor identity, governed write path, audit trail, and materialization separation. Phase 7AU does not approve artifacts, reject artifacts, request revisions, link artifacts to candidates, materialize artifacts, or activate artifacts.

## 30. Relationship to Future 7AY

Future 7AY may validate and certify the Screen 1 workflow block.

Phase 7AU only introduces boundary documentation, lifecycle documentation, optional inert metadata, validation tests, and architecture index links for this first subtask. It does not implement final validation/certification for 7AU-7AY.

## 31. Relationship to Phase 8 EM Extract

Phase 8 may later define EM Extract support, sizing/TCO, and what-if advisory features.

Phase 7AU does not implement EM Extract collection, source acquisition, extract parsing, extract conversion, sizing, TCO, capacity planning, cost modeling, or what-if advisory workflows.

Phase 8 EM Extract implementation is not included. Phase 8 sizing/TCO is not implemented.

## 32. Acceptance Criteria

Phase 7AU is accepted when Screen 1 ingestion/parser governance boundary documentation exists, Screen 1 ingestion/parser lifecycle documentation exists, boundary validation tests exist, optional scaffolding is inert and local-only if present, architecture index links exist if the index is updated, no Screen 1 workflow UI is added, no source intake is invoked, no local files are read, no object storage calls are made, no DB lookup is made, no parser unknown classification is performed, no parser mapping records are created, no parser candidates are created, no knowledge artifacts are approved/rejected, no governed write path is invoked, no parser output is changed, no Phase 4I mutation is added, future source actions require actor identity, future parser review actions require governed write path, future artifact workflows require audit trail, parser runtime remains authoritative, deterministic runtime remains authoritative, Phase 8 EM Extract implementation is not included, and Phase 8 sizing/TCO is not implemented.
