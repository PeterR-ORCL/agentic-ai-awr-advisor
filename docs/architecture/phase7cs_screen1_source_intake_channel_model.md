# Phase 7CS Screen 1 Source Intake Channel Model

## 1. Purpose

This document defines the Screen 1 source intake channel model for 7CS-FU2.
It uses the OCI Data Load / Cloud Store pattern as a reference for channel
clarity, source context fields, validation before load, and governed backend
execution, while preserving the current safe Screen 1 architecture.

Screen 1 source intake is not browser execution. The browser may collect source
metadata and submit governed requests. Backend services decide whether a source
can be validated, staged, loaded, parsed, or converted into generated artifact
readiness.

## 2. Screen Ownership Boundary

Home / Index owns platform entry and source path selection. It distinguishes
new source intake from existing platform evidence.

Screen 1 owns new-source intake, source validation, parser/source governance,
generated artifact readiness when the backend returns `completed_artifact_ready`,
Full File / Report Table review, parser health, unknown parser signals, parser
governance backlog, and read-only source artifact context.

Screen 2 owns existing platform evidence selection, runtime scope, interval or
window selection, Target A/B preparation, and governed runtime handoff.
Existing platform evidence must not become a normal Screen 1 source card.

Screens 3, 4, 5, and 6 remain gated until a valid evidence handoff exists.
Generated artifact file existence alone is not active downstream evidence.

## 3. Channel Taxonomy

| Product label | `source_type` key | Current readiness | Operator purpose | Future phase |
|---|---|---|---|---|
| Local Staged / Local Folder | `local_staged` | Current most complete Screen 1 path | Use backend-visible staged AWR `.out` input for governed intake | Current / near-term |
| Local File | `local_file` | Browser metadata plus backend-visible path validation only | Identify a selected local file context for governed backend validation | Near-term upload/stage contract |
| Object Storage | `object_storage` | Metadata validation only today | Describe namespace, bucket, object or prefix, and region for governed validation | 7CS-FU3 / later source-loader contract |
| Existing Platform Evidence | `existing_run` | Screen 2-owned handoff reference only | Guide operators to Screen 2 for existing evidence runtime selection | Current handoff guidance |
| Enterprise Manager / OEM | `enterprise_manager_oem` | Not implemented | Future governed supplemental source metadata | Future governed source adapter |
| File System | `file_system` | Not implemented | Future backend-visible file-system source outside the local dev staging path | Future governed source adapter |
| Catalog / Repository | `catalog_repository` | Not implemented | Future persisted source catalog or repository reference | Future governed source adapter |
| AI Source | `ai_source` | Not implemented | Future governed source mode only, not runtime truth | Future governed source adapter |

## 4. Local Staged / Local Folder Channel

`local_staged` is the current most complete Screen 1 source path. It may reach
`completed_artifact_ready` when the governed backend runner succeeds and returns
current artifact readiness.

Required fields are a selected source mode and a backend-visible local folder
path, such as `data/input`. Browser folder picker metadata can support operator
selection, but it does not itself prove backend access.

Allowed browser behavior is selecting folder metadata, relative names, counts,
and size hints. Required backend behavior is validating the path, using the
governed intake runner, and returning failed-safe status when the folder is not
available or generation does not complete.

This channel must not claim that picker metadata alone staged evidence, parsed
an AWR report, called `run_analysis.py`, mutated Phase 4I, or activated
downstream evidence.

## 5. Local File Channel

`local_file` identifies a local file context for governed backend validation.
The current verified file type is `.out`.

Required fields are source mode and local file path or selected file metadata.
Allowed browser behavior is capturing file name, size, type, and extension
metadata. The browser must not read, upload, parse, or stage the file unless a
future governed upload/stage contract explicitly implements that behavior.

Required backend behavior is validating the request shape and failing safely
unless a backend-visible upload or staging path exists. This channel must not
claim artifact readiness without backend execution returning
`completed_artifact_ready`.

## 6. Object Storage Channel

`object_storage` is metadata validation only today.

Required fields are namespace, bucket, object name or prefix, and region. The
current validation route is `/phase7/dashboard/object-storage/validate`.
The detailed Screen 1 Object Storage source-intake contract is defined in
`phase7cs_object_storage_source_intake_contract.md`.

Allowed browser behavior is collecting and submitting Object Storage metadata.
The browser must not expose credentials, call OCI APIs, list buckets, read
objects, download objects, or validate real credentials.

Required backend behavior today is governed metadata validation and audit
recording. Future load-to-staging requires a governed source-loader contract,
server-side credential resolution, injected Object Storage clients where active
access is allowed, secret rejection, idempotency, audit persistence, and
failed-safe results.

Object Storage must not claim object availability, parser execution, generated
artifact readiness, active downstream evidence, comparison readiness, diagnosis,
score, recommendation, learning materialization, or runtime eligibility unless
the appropriate deterministic backend workflow has produced those states.

## 7. Existing Platform Evidence Boundary

Existing platform evidence is an entry/handoff reference, not a Screen 1 source
card. Its source key remains `existing_run` for compatibility, but actual
selection belongs to Screen 2 Runtime Scope & Analysis Control.

Home may route existing platform evidence intent to Screen 2. Screen 1 may
explain that existing platform evidence is Screen 2-owned. Screen 1 must not
load runtime options, choose target/window scope, assign Target A/B comparison,
or treat an existing run as new source intake.

## 8. Future Source Placement

Enterprise Manager / OEM is a future governed supplemental source. It must use
a server-side adapter, provenance, validation, audit, and deterministic
evidence contracts. It must not bypass parser/source governance or introduce
Phase 8 sizing/TCO behavior in Phase 7.

File System is a future backend-visible storage channel, distinct from the
current local development staged folder path. It must not use browser-local path
strings as truth.

Catalog / Repository is a future persisted source reference. It must distinguish
catalog metadata from source contents and must require governed backend lookup
before evidence readiness can be claimed.

AI Source is a future governed source mode only. It cannot create source truth,
parser truth, diagnosis, scoring, recommendation, materialization, or runtime
eligibility. LLM explanations remain explanatory only; deterministic/governed
state wins.

## 9. Object Storage Future Progression

A safe Object Storage progression is:

1. Collect metadata in Screen 1.
2. Validate metadata through the governed service.
3. Create a governed source-loader request with actor, audit, idempotency, and
   validation references.
4. Resolve credentials server-side only.
5. Use an injected Object Storage client for allowed metadata/head/get/list
   operations.
6. Stage or reference source content through a backend contract.
7. Run deterministic parser/intake only after source-loader success.
8. Return `completed_artifact_ready` only from the backend when the generated
   dashboard artifact is current.
9. Keep Screens 3/4/5/6 gated until valid evidence handoff is active.

The FU3 Object Storage source-intake contract formalizes these stages and keeps
FU4/FU5 implementation work bounded to governed backend handoff behavior.

The older `src/ingest/awr_adb_loader.py` path may remain a historical project
capability, but it must not be wired directly into Screen 1 UI. If reused, it
must sit behind a governed server-side adapter that preserves source validation,
audit, failure behavior, and deterministic truth boundaries.

## 10. Non-Negotiable Safety Rules

- No browser-side OCI credentials or direct Object Storage API access.
- No browser-side parser execution.
- No browser-side local file read or upload claim without a governed upload
  contract.
- No DB query from browser source controls.
- No generated artifact readiness without backend `completed_artifact_ready`.
- No active downstream evidence from file existence alone.
- No Screen 1 existing-run runtime selection.
- No parser, scoring, diagnosis, recommendation, learning, materialization, or
  runtime eligibility mutation from source-channel UI.
- No Phase 8 EMCC/OEM, sizing, prediction, or TCO behavior in Phase 7.

## 11. Current Validation Coverage

Current coverage is provided by Screen 1 parser governance workflow validation,
Index source validation, dashboard runtime interaction validation, and focused
dashboard tests. These guard the new-source/Screen 2 split, Object Storage
metadata-only behavior, browser safety flags, generated artifact readiness
wording, and downstream evidence gating.

Future FU3/FU4/FU5 work should add or update tests only when contracts or UI
copy change. Tests must continue to prove that `existing_run` stays out of
Screen 1 source cards, Object Storage remains governed backend-only until a
source-loader contract exists, and generated artifact readiness is not active
downstream evidence by file existence alone.
