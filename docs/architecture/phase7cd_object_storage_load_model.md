# Phase 7CD Object Storage Load Model

## Object Shapes

`ObjectStorageLoadRequestEnvelope` contains `load_execution_id`, source selection metadata, `ObjectStorageConfiguration`, `ObjectStorageConfigurationValidation`, actor id, actor audit context, idempotency key, transaction group id, requested object name, requested prefix, load mode, expected file type, validation reference, rollback reference, dry-run flag, created timestamp, and notes.

`ObjectStorageLoadValidation` contains `load_validation_id`, `load_execution_id`, validity, validation status, actor/config/client checks, blocked state, denied reasons, warnings, required next steps, and secret safety flags. `credential_value_present=false` and `secret_detected=false` are enforced on persisted validation metadata.

`ObjectStorageLoadedObjectReference` contains object reference id, namespace, bucket, object name, region, size, etag, content type, checksum, artifact reference, file/content persistence flags, and notes.

`ObjectStorageLoadResult` contains load status, Object Storage call flags, safety flags, workflow persistence flags, loaded object references, denied reasons, warnings, required next steps, and notes.

## Load Statuses

Supported load statuses are `dry_run_only`, `blocked_invalid_config`, `blocked_no_client`, `blocked_secret_detected`, `metadata_validated`, `object_metadata_loaded`, `object_content_loaded_in_memory`, `prefix_listed`, `persisted_metadata_only`, `idempotent_replay`, and `failed_safely`.

## Load Modes

`metadata_only` validates and persists metadata without calling the client. `head_object` calls injected metadata lookup. `get_object` loads bytes in memory without file writes. `list_prefix` lists metadata and does not download objects.

## Validation Rules

The envelope requires actor id, actor audit context, idempotency key, transaction group id, rollback reference, source selection, Object Storage configuration, and 7BS Object Storage validation metadata. Non-metadata load modes require an injected client.

## Secret Detection

Secret detection scans metadata field names for `password`, `secret`, `token`, `api_key`, `private_key`, `key_file_content`, `auth_token`, and `credential_value`. Matching fields block execution. Values are not printed, returned, or persisted.

## Repository Behavior

The governed workflow repository persists request, transaction, validation, audit, `source_validation_artifact`, and `object_storage_load_artifact` metadata. Repeated idempotency keys return `idempotent_replay` and skip client calls.

## Deterministic IDs

`create_object_storage_load_execution_id(idempotency_key, object_name, prefix)` creates stable load ids. `create_object_storage_load_validation_id` and `create_loaded_object_reference_id` create stable validation and object reference ids.

## Prior Conventions

Phase 7CD reuses Phase 7BS `ObjectStorageConfiguration` and `ObjectStorageConfigurationValidation`. Existing loader conventions include `OCI_NAMESPACE`, `OCI_OBJECT_STORAGE_NAMESPACE`, `OCI_BUCKET_NAME`, `OCI_OBJECT_STORAGE_BUCKET`, `OCI_OBJECT_PREFIX`, and `OCI_OBJECT_STORAGE_PREFIX`. Older executable Object Storage ingestion exists in `src/ingest/awr_adb_loader.py`, but 7CD keeps a separate injected-client boundary because the older path can construct OCI clients, write temporary downloads, and proceed toward parsing or ingestion. No hard-coded bucket/namespace/credentials are introduced.

## Safety Flags

Results enforce `local_file_written=false`, `db_lookup_performed=false`, `run_analysis_called=false`, `parser_invoked=false`, `phase4i_mutated=false`, and `dashboard_regenerated=false`.

## Non-Goals

Phase 7CD does not parse AWR files, call parser/scoring/decision/recommendation modules, execute analysis, call run_analysis.py, regenerate dashboards, mutate Phase 4I, store credentials, require live Object Storage for normal tests, activate Screen 3 buttons, implement EM Extract, or implement Phase 8.
