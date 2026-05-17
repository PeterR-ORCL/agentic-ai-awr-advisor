# Phase 7CD Object Storage Load Execution

## 1. Purpose

Phase 7CD introduces controlled Object Storage load execution for Screen 3 and index source workflows. It records governed metadata for Object Storage source access while preserving deterministic runtime truth.

## 2. Scope

The scope is limited to validating Object Storage load metadata, using an injected client for metadata/head/get/list operations, returning load result metadata, and persisting workflow request, validation, audit, source validation, and object storage load artifact references through the Phase 7CA repository.

## 3. Non-Goals

Phase 7CD does not run analysis, call run_analysis.py, parse AWR files, invoke parser/scoring/decision/recommendation modules, regenerate dashboards, mutate Phase 4I, activate Screen 3 buttons, implement EM Extract, or implement Phase 8.

## 4. Object Storage Load Is Not Analysis Execution

Object Storage load execution loads or references objects only. It does not analyze loaded objects, does not parse them, does not call deterministic re-analysis, and does not materialize runtime truth.

## 5. Prior Object Storage Context

Object Storage was part of earlier project architecture. The project owner already has an Object Storage bucket. Existing project conventions include Phase 7BS metadata validation and older loader environment names such as `OCI_NAMESPACE`, `OCI_OBJECT_STORAGE_NAMESPACE`, `OCI_BUCKET_NAME`, `OCI_OBJECT_STORAGE_BUCKET`, `OCI_OBJECT_PREFIX`, and `OCI_OBJECT_STORAGE_PREFIX`. Older executable ingestion code also exists in `src/ingest/awr_adb_loader.py`; Phase 7CD does not call that path because it can construct OCI clients, download objects to temporary files, and continue into parsing or ingestion behavior that is outside this phase. Phase 7CD aligns with existing names and source concepts while adding no hard-coded bucket/namespace/credentials.

## 6. Client Injection Boundary

The Object Storage client must be injected by the caller. The 7CD module does not construct an OCI client, does not read OCI config files, and has no OCI SDK import required.

## 7. Credential / Secret Boundary

Secret-like field names such as `password`, `secret`, `token`, `api_key`, `private_key`, `key_file_content`, `auth_token`, and `credential_value` block execution. No credentials persisted. Credential values are not logged, returned, or stored.

## 8. Load Modes

Supported load modes are `metadata_only`, `head_object`, `get_object`, and `list_prefix`.

## 9. Metadata-Only Mode

`metadata_only` validates metadata and persists workflow/source validation metadata. It performs no Object Storage client call.

## 10. Head Object Mode

`head_object` may call the injected client to retrieve object metadata. It does not download object content and performs no file write.

## 11. Get Object Mode

`get_object` may call the injected client to load object content in memory. It does not write content to disk, persist object content, parse content, or trigger analysis.

## 12. Prefix List Mode

`list_prefix` may call the injected client to list object metadata under a prefix. It does not download listed objects.

## 13. Repository Persistence

Phase 7CD uses the governed workflow repository to persist transaction, request, validation, audit, source validation artifact, and object storage load artifact metadata. Persistence records references and summaries only.

## 14. Idempotency

An idempotency key is required. Existing workflow metadata returns `idempotent_replay` and does not call the Object Storage client again.

## 15. Output Artifact Metadata

Output artifacts use `source_validation_artifact` and `object_storage_load_artifact`. Artifact metadata records object references, sizes, etags, checksums, and safety flags where available, but never credentials or object content.

## 16. Runtime Truth Boundary

Object Storage load metadata is source workflow state. It is not parser output, score output, recommendation output, deterministic analysis output, or dashboard output.

## 17. Phase 4I Boundary

Phase 7CD does not mutate Phase 4I. Loaded object references may be used by future phases, but Phase 4I remains unchanged.

## 18. Relationship to 7BS

Phase 7BS created Object Storage configuration metadata validation. Phase 7CD reuses `ObjectStorageConfiguration` and `ObjectStorageConfigurationValidation` and requires valid metadata before active load attempts.

## 19. Relationship to 7CA

Phase 7CA provides the persistence repository, idempotency, transaction, validation, audit, and output artifact tables used by Phase 7CD.

## 20. Relationship to 7CB

Phase 7CB executes deterministic re-analysis through an injected runner. Phase 7CD only loads or references source objects and does not call the 7CB runner.

## 21. Relationship to 7CC

Phase 7CC compares already-loaded structured payloads. Phase 7CD may create load metadata that future phases can use to prepare structured payloads, but it does not implement Load-and-Compare.

## 22. Relationship to Future 7CE

Dashboard output refresh and regenerated artifact handling remain future 7CE work. No dashboard regeneration occurs in Phase 7CD.

## 23. Relationship to Phase 8 EM Extract

EM Extract remains Phase 8. Phase 7CD does not implement EM Extract adapters, Enterprise Manager access, sizing/TCO comparison, or what-if advisory.

## 24. Acceptance Criteria

Phase 7CD is accepted when Object Storage load execution validates 7BS configuration metadata, requires actor/audit/idempotency/transaction/repository metadata, uses injected clients only, supports fake-client tests for metadata/head/get/list modes, persists governed workflow metadata, prevents duplicate client calls on idempotent replay, performs no file write, has no run_analysis.py call, has no parser invocation, has no dashboard regeneration, has no Phase 4I mutation, has no credentials persisted, and leaves deterministic runtime authoritative.
