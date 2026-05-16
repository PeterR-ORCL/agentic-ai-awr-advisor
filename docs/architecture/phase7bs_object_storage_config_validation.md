# Phase 7BS Object Storage Configuration Validation

## 1. Purpose

Phase 7BS adds local deterministic Object Storage configuration validation metadata for the index/source mode entry workflow. It distinguishes complete metadata, incomplete metadata, unsupported credential modes, execution blocking, and required next steps without touching Object Storage.

## 2. Scope

This phase adds Object Storage configuration metadata, validation result metadata, summary metadata, validation helpers, serialization helpers, documentation, tests, and an optional preview-only index panel.

## 3. Non-Goals

Phase 7BS does not import OCI SDK, call OCI services, call Object Storage, call network, list buckets, check bucket existence, check object existence, download objects, validate real credentials, read local OCI config files, read local source files, query DB, call run_analysis.py, execute source intake, create backend requests, create Screen 3 handoff, implement EM Extract, or implement Phase 8 sizing/TCO.

## 4. Object Storage Config Validation Is Not Object Storage Access

Object Storage configuration validation is metadata validation only. No object storage call is made. No credential validation is performed. No bucket listing occurs. No object download occurs. No run_analysis.py call is made.

## 5. Configuration Metadata

The configuration metadata may include namespace, bucket, object_name, prefix, region, compartment_id, credential_mode, profile_name, uri, configured_hint, created_at, and notes. The model stores no secrets.

## 6. Credential Mode Boundary

Credential mode support is metadata-only. Supported credential modes are `env`, `instance_principal`, `resource_principal`, `config_file`, and `unknown`. No credential validation is performed and no local OCI config file is read.

## 7. Required Metadata

Valid metadata requires namespace, bucket, object_name or prefix, region, compartment_id, and a supported credential mode. Missing fields produce metadata validation statuses only; they do not trigger source access.

## 8. Validation Result

The validation result records field presence, credential mode support, future access eligibility metadata, denied reasons, warnings, and required next steps. `execution_blocked=true in 7BS`.

## 9. Summary Result

The summary result counts configured entries, valid metadata entries, incomplete entries, unsupported credential entries, and safety flags. `execution_supported=false`, `handoff_supported=false`, and `object_storage_call_performed=false`.

## 10. Secret Field Boundary

Secret fields are not allowed. The model rejects password, secret, token, api_key, private_key, and key_file_content fields. No credential value should be stored.

## 11. Execution Boundary

Phase 7BS does not execute future access. `execution_blocked=true in 7BS`, `credential_validation_performed=false`, `object_storage_call_performed=false`, `bucket_list_performed=false`, and `object_download_performed=false`.

## 12. Source Handoff Boundary

No Screen 3 handoff is implemented. `handoff_supported=false`; no backend request, handoff payload, form submit, fetch call, or API call is added.

## 13. Relationship to 7BQ

Phase 7BQ established the index source mode entry point. Phase 7BS adds Object Storage configuration metadata validation for that entry path without changing the 7BQ preview-only execution boundary.

## 14. Relationship to 7BR

Phase 7BR established source status visibility. Phase 7BS refines the Object Storage status path by validating configuration metadata presence and shape only. It still makes no object storage call.

## 15. Relationship to Future 7BT

Future 7BT may implement index to Screen 3 selection handoff. Phase 7BS does not implement handoff and keeps handoff unsupported.

## 16. Relationship to Phase 8 EM Extract

EM Extract belongs to Phase 8. Phase 7BS does not implement EM Extract and does not implement Phase 8 sizing/TCO.

## 17. Acceptance Criteria

Phase 7BS is accepted when Object Storage configuration metadata, validation result metadata, and summary metadata exist; secret fields are rejected; complete metadata returns `VALID_METADATA_ONLY`; `can_attempt_future_access` is future eligibility metadata only; no credential validation is performed; no object storage call is made; no bucket listing occurs; no object download occurs; `execution_blocked=true in 7BS`; related 7BQ and 7BR tests continue to pass; EM Extract remains Phase 8; and Phase 8 sizing/TCO is not implemented.
