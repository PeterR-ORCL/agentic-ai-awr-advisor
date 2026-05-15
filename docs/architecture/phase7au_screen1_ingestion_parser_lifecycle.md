# Phase 7AU Screen 1 Ingestion / Parser Lifecycle

## 1. Purpose

Phase 7AU defines the lifecycle boundary for future Screen 1 ingestion, source intake, parser unknown review, parser mapping request, parser backlog linkage, knowledge artifact review, governed write-path handling, audit trail, output artifact handling, and closure.

No lifecycle stage is implemented in 7AU. The lifecycle is documentation only so future 7AV, 7AW, 7AX, and 7AY work cannot skip governance gates.

## 2. Lifecycle Overview

The future Screen 1 lifecycle is:

1. Read-only ingestion / parser visibility.
2. Source selection.
3. Source validation.
4. Source intake request.
5. Parser unknown review.
6. Parser mapping request.
7. Parser backlog linkage.
8. Knowledge artifact review.
9. Governed write-path validation.
10. Audit trail creation.
11. Output artifact creation.
12. Closure.

These stages are boundary concepts only in Phase 7AU. They do not create workflow records, execute intake, classify unknown signals, create mappings, approve artifacts, materialize artifacts, or mutate runtime.

## 3. Read-Only Ingestion / Parser Visibility Stage

Screen 1 starts as read-only ingestion and parser visibility.

The reviewer may inspect source/run metadata, parser sections, parser diagnostics, parser confidence, parser unknown signals, governance rows, knowledge requests, and artifact context that already exists in the static dashboard. This visibility does not create source intake, review records, mapping requests, artifact decisions, or runtime changes.

Screen 1 ingestion/parser/governance remains read-only until workflow phases explicitly add controls.

## 4. Source Selection Stage

Source selection is not source intake.

Future source selection may describe intended local source, object storage source, existing run source, future upload placeholder, or future EM Extract placeholder. Selecting a source means metadata intent only. It does not open a file, load a source, query a database, call object storage, parse an AWR report, call `run_analysis.py`, or create an ingestion run.

Future source selection cannot skip actor identity once it becomes a workflow action.

## 5. Source Validation Stage

Source validation is not source loading.

Future source validation must validate source metadata shape, source mode, source reference completeness, actor identity, authorization posture, backend execution mode, denied reasons, warnings, required next steps, and output lifecycle needs before source intake can be requested.

Future workflows cannot skip validation. Phase 7AU performs no source validation against real files, object storage objects, existing run databases, or source contents.

## 6. Source Intake Request Stage

Future source intake request is governed workflow state.

A future request_source_intake action may request that a validated source be routed to an intake path. That request is not automatic execution. It must use actor identity, governed write path, backend execution mode, audit trail, output artifact lifecycle, source validation evidence, and failure behavior before any backend execution can be considered.

Phase 7AU invokes no source intake, creates no ingestion run, calls no backend, and does not call `run_analysis.py`.

## 7. Parser Unknown Review Stage

Unknown review is not parser mutation.

Future parser unknown review may let an actor inspect a parser_unknown_signal and classify it as parser gap, source gap, not applicable, or false positive. That classification is governed review state. It does not change parser output, parser diagnostics, parser confidence, unknown signal output, extracted metrics, feature vectors, scoring, decisions, recommendations, or Phase 4I.

Phase 7AU performs no parser unknown classification.

## 8. Parser Mapping Request Stage

Parser mapping request is not parser update.

Future parser mapping requests may propose that a parser_unknown_signal, parser_section, parser_confidence issue, or parser_diagnostic should route to a parser_mapping_candidate. The request does not update parser code, parser config, parser mapping tables, parser adapters, parser output, or runtime truth.

Phase 7AU creates no parser mapping records and creates no parser candidates.

## 9. Parser Backlog Linkage Stage

Parser backlog linkage is governed routing.

Future workflow may link an unknown signal to a parser_backlog_item or route it for backlog consideration. Linkage does not create runtime parser changes, does not approve a parser mapping, does not activate a candidate, and does not change Phase 4I.

Phase 7AU links no unknown signals to candidates or backlog items.

## 10. Knowledge Artifact Review Stage

Artifact review is not materialization.

Future knowledge artifact review may request revision, approve an artifact for review, reject an artifact, link an artifact to a candidate, or add parser review notes. That review state requires actor identity, validation, governed write path, and audit trail. It does not materialize artifacts, activate artifacts, grant runtime influence, update parser behavior, update scoring behavior, update recommendation behavior, or change Phase 4I.

Phase 7AU approves no artifacts, rejects no artifacts, requests no revisions, and materializes no artifacts.

## 11. Governed Write-Path Stage

Future workflows cannot bypass governed write path.

Any future non-read-only Screen 1 action must pass through the Phase 7AG governed write-path framework. The write path must validate actor identity, authorization posture, request shape, target type, target reference, action, status transition, source validation result, backend execution mode where applicable, parser runtime protection, Phase 4I contract protection, audit fields, output artifact needs, and failure behavior.

Phase 7AU invokes no governed write path.

## 12. Audit Trail Stage

Future workflows cannot skip audit.

Future audit trail records must identify actor, target type, target reference, action, requested status transition, source payload reference, parser signal reference, artifact reference, validation result, authorization result, governed write-path result, backend execution mode where applicable, output artifact reference where applicable, notes, routed governance references, and closure state.

Phase 7AU creates no audit records.

## 13. Output Artifact Stage

Future source intake and review responses must use output artifact lifecycle.

Future outputs may include source_validation_result, source intake request preview, ingestion_run reference, parser unknown review state, parser mapping request state, parser backlog linkage state, knowledge artifact review state, routed governance reference, error artifact, or closure artifact.

Output artifacts are not parser runtime state. They cannot silently replace parser output, Phase 4I payloads, generated dashboard artifacts, or deterministic runtime truth.

Phase 7AU creates no output artifacts.

## 14. Closure Stage

Closure is governed workflow state.

Future Screen 1 workflow items may close after validation, rejection, routing to governance, candidate linkage, backlog linkage, revision handling, or artifact review. Closure does not prove runtime mutation occurred and does not activate parser changes, source intake, artifacts, or Phase 4I changes.

Phase 7AU closes no workflow records because no workflow records are created.

## 15. Forbidden Shortcuts

Future workflows cannot skip actor.

Future workflows cannot skip validation.

Future workflows cannot skip audit.

Future workflows cannot bypass governed write path.

Future source intake cannot bypass backend execution mode.

Future source intake cannot read local files directly from dashboard state.

Future source intake cannot call object storage directly from dashboard state.

Future source intake cannot query databases directly from dashboard state.

Future parser unknown review cannot mutate parser output.

Future parser mapping request cannot update parser code, parser config, parser mappings, parser adapters, or parser runtime.

Future artifact review cannot materialize artifacts.

Future artifact review cannot activate parser, scoring, or recommendation changes.

Future Screen 1 workflows cannot mutate Phase 4I directly.

Parser runtime remains authoritative.

Phase 8 EM Extract implementation is not included. Phase 8 sizing/TCO is not implemented.

## 16. Required Validation Evidence

Future Screen 1 workflow phases must provide validation evidence for:

- actor identity supplied by the 7AE actor model
- source metadata completeness
- source validation result
- request target type
- request action type
- requested status transition
- governed write-path validation from 7AG
- audit fields
- backend execution mode from 7AF when source intake is requested
- output artifact lifecycle from 7AH when a response or artifact is created
- parser runtime protection
- Phase 4I contract protection
- no direct parser output mutation
- no direct artifact materialization
- deterministic runtime authority

Phase 7AU provides boundary validation only and does not validate real source contents or execute workflow stages.

## 17. Acceptance Criteria

Phase 7AU lifecycle documentation is accepted when it clearly states that no lifecycle stage is implemented in 7AU, source selection is not source intake, source validation is not source loading, unknown review is not parser mutation, parser mapping request is not parser update, artifact review is not materialization, future workflows cannot skip actor, future workflows cannot skip validation, future workflows cannot skip audit, future workflows cannot bypass governed write path, parser runtime remains authoritative, no source intake is invoked, no local files are read, no object storage calls are made, no DB lookup is made, no parser output is changed, no Phase 4I mutation is added, Phase 8 EM Extract implementation is not included, and Phase 8 sizing/TCO is not implemented.
