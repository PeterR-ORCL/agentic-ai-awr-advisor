# Phase 7BS Object Storage Configuration Model

## 1. Purpose

The Phase 7BS Object Storage configuration model provides deterministic local metadata validation for the future Object Storage source path. It validates metadata presence and shape only.

## 2. ObjectStorageConfiguration Object Shape

`ObjectStorageConfiguration` contains `config_id`, `namespace`, `bucket`, `object_name`, `prefix`, `region`, `compartment_id`, `credential_mode`, `profile_name`, `uri`, `configured_hint`, `created_at`, and `notes`.

## 3. ObjectStorageConfigurationValidation Object Shape

`ObjectStorageConfigurationValidation` contains `validation_id`, `config_id`, `valid_metadata`, `validation_status`, `namespace_present`, `bucket_present`, `object_or_prefix_present`, `region_present`, `compartment_present`, `credential_mode_supported`, `credential_validation_performed`, `object_storage_call_performed`, `bucket_list_performed`, `object_download_performed`, `can_attempt_future_access`, `execution_blocked`, `denied_reasons`, `warnings`, `required_next_steps`, and `notes`.

## 4. ObjectStorageConfigurationSummary Object Shape

`ObjectStorageConfigurationSummary` contains `summary_id`, `configured_count`, `valid_metadata_count`, `incomplete_count`, `unsupported_credential_count`, `execution_supported`, `handoff_supported`, `object_storage_call_performed`, `warnings`, `required_next_steps`, and `notes`.

## 5. Credential Modes

Supported credential modes are `env`, `instance_principal`, `resource_principal`, `config_file`, and `unknown`. Supported means metadata-supported only; no credential validation is performed and no secrets are stored.

## 6. Validation Statuses

Validation statuses are `VALID_METADATA_ONLY`, `INVALID`, `MISSING_NAMESPACE`, `MISSING_BUCKET`, `MISSING_OBJECT_OR_PREFIX`, `MISSING_REGION`, `MISSING_COMPARTMENT`, `UNSUPPORTED_CREDENTIAL_MODE`, and `EXECUTION_NOT_ALLOWED_IN_THIS_PHASE`.

## 7. Secret Field Rules

Secret fields are rejected. Disallowed fields include password, secret, token, api_key, private_key, and key_file_content. The model stores no credential values, private keys, API keys, or local config file contents.

## 8. Execution Rules

`credential_validation_performed=false`, `object_storage_call_performed=false`, `bucket_list_performed=false`, `object_download_performed=false`, `execution_supported=false`, `handoff_supported=false`, and `execution_blocked=true in 7BS`.

## 9. Serialization Rules

Serialization uses plain dictionaries with metadata fields only. Deserialization rejects secret fields and rebuilds dataclass instances. Serialization does not import OCI, call Object Storage, read config files, validate credentials, query DB, call run_analysis.py, execute source intake, or perform handoff.

## 10. Validation Rules

Configuration validation requires a config_id and rejects unsupported credential modes. Evaluation reports missing namespace, bucket, object_name or prefix, region, compartment_id, or unsupported credential mode as metadata statuses. Validation result records reject `credential_validation_performed=true`, `object_storage_call_performed=true`, `bucket_list_performed=true`, `object_download_performed=true`, and `execution_blocked=false`. Summary records reject `execution_supported=true`, `handoff_supported=true`, and `object_storage_call_performed=true`.

## 11. Non-Goals

The model does not import OCI SDK, call Object Storage, call network, list buckets, check bucket existence, check object existence, download objects, validate real credentials, read local OCI config files, read local source files, query DB, call run_analysis.py, execute analysis, execute source intake, create backend requests, create Screen 3 handoff, implement object storage access, implement EM Extract, mutate Phase 4I, change parser/scoring/decision/recommendation behavior, or implement Phase 8 sizing/TCO.

## 12. Acceptance Criteria

The model is accepted when deterministic IDs are stable, secret fields are rejected, missing metadata maps to the required validation statuses, complete metadata returns `VALID_METADATA_ONLY`, `can_attempt_future_access=true` only for complete metadata with supported credential mode, unsafe execution/access flags are rejected, summary counts validate, serialization round trips, no credential validation is performed, no object storage call is made, no bucket listing occurs, no object download occurs, EM Extract remains Phase 8, and Phase 8 sizing/TCO is not implemented.
