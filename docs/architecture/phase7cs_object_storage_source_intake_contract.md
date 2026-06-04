# Phase 7CS Object Storage Source Intake Contract

## 1. Purpose

This document defines the governed Object Storage source-intake contract for
Screen 1. It is contract-first documentation for 7CS-FU3.

Screen 1 may collect Object Storage source metadata and submit a governed
validation or intake request. The browser must not call OCI, read credentials,
list buckets, download objects, parse files, invoke `run_analysis.py`, or claim
artifact readiness by itself.

The backend/service layer owns credential handling, Object Storage client
injection, validation, future staging, parser/ingest handoff, deterministic
run output, persistence, audit, and generated artifact readiness.

## 2. Current Status

The current Screen 1 Object Storage path is metadata validation only.

Current browser fields include namespace, bucket, object or prefix, and region.
The current governed validation route is
`/phase7/dashboard/object-storage/validate`.

Current source execution validation accepts `object_storage`, but the current
backend source-intake runner only completes generated artifact readiness for
`local_staged`. Non-local-folder execution fails safely and does not claim
`completed_artifact_ready`.

Phase 7CD already defines the future controlled Object Storage load model with
injected clients, metadata/head/get/list modes, secret rejection, idempotency,
and governed workflow persistence. FU3 adopts that pattern for Screen 1 source
intake without implementing live load-to-analysis.

## 3. Non-Negotiable Boundaries

- No browser-side OCI client construction.
- No browser-side bucket listing, object listing, object reads, or downloads.
- No browser-side credential, token, private key, or local OCI config capture.
- No browser-side parser execution.
- No browser-triggered `run_analysis.py` execution.
- No generated artifact readiness unless a governed backend path returns
  `completed_artifact_ready`.
- No Object Storage source becomes active downstream evidence by file existence
  or metadata validation alone.
- No direct wiring from Screen 1 UI to `src/ingest/awr_adb_loader.py`.
- No parser, scoring, diagnosis, recommendation, learning, materialization, or
  runtime eligibility mutation from source-intake UI.
- No Phase 8 EMCC/OEM, sizing, prediction, or TCO behavior.

## 4. Contract Stages

### Stage 0 - Metadata Capture

The browser may collect source metadata only:

- `source_type=object_storage`
- `source_channel=object_storage`
- `namespace`
- `bucket`
- `region`
- `object_name` or `object_key`
- `prefix`, when prefix mode is selected
- `selection_mode`, with values `object` or `prefix`
- optional object URL, when a future model supports it
- `expected_file_type`
- optional operator note
- optional source owner or source label, only when an existing metadata model
  supports it

The browser must not collect secrets, private keys, auth tokens, credential
values, local OCI config profile contents, or credential file contents.

### Stage 1 - Metadata Validation

The backend validates Object Storage source metadata before any load-to-staging
or parser handoff can be considered.

Validation checks include:

- required fields are present
- `selection_mode` explicitly identifies object or prefix intent
- object key, prefix, bucket, namespace, and region have safe metadata shape
- expected file type and extension are eligible for the current parser/source
  contract
- secret-like field names are absent
- path traversal or unsafe key assumptions are rejected
- request id, session id where applicable, and audit context exist
- operator intent is recorded

Validation may return:

- `valid`, `invalid`, `partial`, or `unavailable`
- normalized source identity
- candidate object count, only when the backend has safe metadata for it or a
  future governed metadata/list mode explicitly supports it
- supported file-type result
- warnings and errors
- next allowed action
- request id or validation id
- audit reference if persisted

Metadata validation is not object availability, object content access, parser
execution, artifact readiness, or downstream evidence activation.

### Stage 2 - Governed Load-to-Staging, Future

Load-to-staging is future work and is not implemented by FU3.

Future load-to-staging requires:

- server-side Object Storage client injection
- no browser credentials
- actor identity and audit context
- idempotency key
- durable source-intake request
- server-side object head/get/list permission validation when active access is
  allowed
- staged reference, object checksum, byte count, and source snapshot metadata
- failed-safe behavior for missing object, denied access, invalid type,
  timeout, duplicate request, unsafe metadata, and parser handoff failure
- no `artifact_ready=true` until staging plus parser/ingest/generation succeeds

### Stage 3 - Parser / Ingest Handoff, Future

Parser/ingest handoff is future work and is not implemented by FU3.

Future parser handoff requires:

- source artifact identity
- staged path or object reference
- parser request id
- deterministic run id or output reference
- Phase 4I contract preservation
- failure-safe parser/ingest result
- generated artifact reference only after deterministic generation succeeds

`completed_artifact_ready` may be returned only after backend
parser/ingest/generation confirms the generated dashboard artifact is current.

### Stage 4 - Downstream Handoff, Future

Downstream use remains gated.

Screen 1 may show generated artifact readiness only when the backend confirms
current readiness. Screen 2 remains the owner of existing evidence selection
and runtime scope. Screens 3 and 4 may show diagnostic/evidence context only
after deterministic output exists and valid evidence handoff is active.

## 5. Browser Metadata Contract

The browser metadata envelope should represent only operator intent and source
location metadata.

Required source identity fields:

- `source_type`
- `source_channel`
- `namespace`
- `bucket`
- `region`
- `selection_mode`
- `object_key` for object mode
- `prefix` for prefix mode
- `file_name`, derived from object key when available
- `file_extension`, derived from object key when available

Backend-only source identity fields when known:

- `file_size_bytes`
- `etag`
- `checksum`
- `object_last_modified`

The browser may store continuity state for visible source controls, but browser
state is not Object Storage truth, object availability, parser truth, artifact
truth, or downstream evidence truth.

## 6. Backend Validation Contract

The backend validation response should include:

- `status`
- `normalized_source_identity`
- `eligible_file_type`
- `supported_extension`
- `candidate_count`
- `warnings`
- `errors`
- `next_allowed_action`
- `request_id` or `validation_id`
- `audit_reference`, if persisted
- `persistence_status`

The backend must reject secret-like fields and unsafe execution flags. The
backend may persist validation and audit metadata. It must not persist
credentials or object content.

Current validation may accept metadata as valid without proving live object
availability. Any live availability check must be server-side, explicit,
governed, and reflected as metadata, not as artifact readiness.

## 7. Governed Load-to-Staging Contract, Future

A future staging result should include:

- `staging_status`
- `staged_reference`
- `checksum`
- `byte_count`
- `source_snapshot`
- `idempotency_key`
- `failure_reason`

The staging contract must use injected clients and governed workflow
persistence. It must not download objects from browser code, write local files
without an explicit backend contract, or call parser/analysis code as a side
effect of validation.

## 8. Parser / Artifact Readiness Contract, Future

The artifact readiness record should include:

- `artifact_ready`, false by default
- `completed_artifact_ready`, only after backend parser/ingest/generation
  confirms current generated artifact readiness
- `artifact_reference`
- `deterministic_run_id`
- `output_reference`

Object Storage validation, object metadata availability, object listing,
object download, or staging alone is insufficient for active downstream
evidence.

## 9. Failure and Safety Behavior

All Object Storage source-intake stages fail closed.

Failure states should preserve operator-visible context and audit details where
safe, but they must not create parser output, deterministic output, generated
artifact readiness, comparison readiness, recommendations, learning state, or
runtime eligibility.

Failure reasons should distinguish:

- incomplete metadata
- unsupported extension or file type
- unsafe key or prefix shape
- secret-like metadata rejected
- backend validation unavailable
- Object Storage client unavailable in future active-load modes
- access denied
- object missing
- prefix empty
- duplicate idempotency key
- staging failure
- parser/ingest failure

## 10. Persistence / Audit Fields

The request context should include:

- `request_id`
- `operator_session_id`
- `generated_dashboard_session_id`, when applicable
- `submitted_at`
- `validation_status`
- `persistence_status`
- `audit_reference`

Governed persistence should record request, validation, audit, source identity,
source validation artifact, future staging artifact, future Object Storage load
artifact, and failure artifact metadata as applicable.

Persistence must not store credentials, private keys, auth tokens, credential
file contents, object contents, or browser-local file contents.

## 11. Source Identity / Provenance

Normalized source identity should be stable enough for audit and idempotency:

- namespace
- bucket
- region
- object key or prefix
- selection mode
- expected file type
- file name and extension when known
- backend-known size, etag, checksum, and last modified when available
- source label or owner only when supported by the metadata model

Provenance must distinguish:

- browser-entered metadata
- backend-validated metadata
- backend-read object metadata
- backend-staged source reference
- parser/ingest output
- generated artifact readiness

## 12. Screen Handoff Rules

Screen 1 owns Object Storage source metadata, validation status, source-intake
request state, and generated artifact readiness when backend completion returns
it.

Screen 2 owns existing platform evidence selection, runtime options, target and
window scope, and Target A/B preparation.

Screens 3 and 4 consume deterministic output only after valid evidence handoff.
Object Storage metadata validation alone must not unlock diagnostic,
historical, comparison, action, learning, or runtime eligibility workflows.

## 13. Explicitly Out of Scope for FU3

- live Object Storage download
- live object listing UI
- browser-side OCI calls
- browser-side credentials
- parser invocation
- `run_analysis.py` invocation
- dashboard regeneration from browser
- `completed_artifact_ready` for `object_storage`
- direct use of `src/ingest/awr_adb_loader.py` from Screen 1
- Screen 2/3/4 behavior changes
- generated artifact filename changes
- Phase 8 EMCC/OEM, sizing, prediction, or TCO behavior

## 14. Follow-Up Work

7CS-FU4 should refine Screen 1 product UX using the OCI Data Load pattern
without implementing browser-side Object Storage access.

7CS-FU5 should define and wire source-intake validation/backend handoff only
where the governed contract is explicit, validated, failed-safe, and separated
from parser/analysis execution.
