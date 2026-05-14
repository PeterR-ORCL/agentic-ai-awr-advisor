# Phase 7AE Actor Identity Model

## 1. Purpose

This document defines the object model, deterministic id rules, validation rules, serialization rules, and metadata helper rules for Phase 7AE dashboard actor/reviewer identity.

The model is local, deterministic, standard-library-only, and metadata-only.

## 2. DashboardActorIdentity Object Shape

`DashboardActorIdentity` has these fields:

- `actor_id`: required string
- `display_name`: required string
- `role`: supported actor role
- `actor_source`: supported actor source
- `permission_scope`: supported permission scope
- `authenticated`: boolean metadata
- `email`: optional string
- `organization`: optional string
- `audit_reference`: optional string
- `created_at`: optional string, defaulting to `None`
- `notes`: optional string

`created_at` does not use the current timestamp. Callers may supply a value in future workflows, but Phase 7AE does not create time-dependent state.

## 3. ActorAuditContext Object Shape

`ActorAuditContext` has these fields:

- `audit_context_id`: required deterministic string
- `actor_id`: required string
- `display_name`: required string
- `role`: supported actor role
- `actor_source`: supported actor source
- `permission_scope`: supported permission scope
- `authenticated`: boolean metadata
- `audit_reference`: optional string
- `action_scope`: optional string
- `notes`: optional string

Actor audit context is trace metadata only. It does not authorize action by itself.

## 4. Actor Roles

Supported roles are:

- `viewer`
- `reviewer`
- `approver`
- `operator`
- `admin`
- `system`

Unsupported roles fail validation.

## 5. Actor Sources

Supported sources are:

- `local`
- `cli`
- `dashboard`
- `system`
- `unknown`

Unsupported sources fail validation.

## 6. Permission Scopes

Supported permission scopes are:

- `read_only`
- `review`
- `approve`
- `execute`
- `administer`

Permission scope is metadata only. It does not enforce authorization and does not grant runtime authority.

## 7. Deterministic ID Rules

Actor ids are deterministic and use normalized actor source plus display name or email metadata:

- `ACTOR-<SOURCE>-<DISPLAY_OR_EMAIL>`

Audit context ids are deterministic and use normalized actor id plus action scope metadata:

- `ACTOR-AUDIT-<ACTOR_ID>-<ACTION_SCOPE>`

Rules:

- no random UUID
- no timestamp
- no DB sequence
- no external service
- stable for same input
- whitespace and case are normalized

## 8. Validation Rules

Actor validation requires actor id, display name, supported role, supported actor source, supported permission scope, boolean authenticated value, optional string metadata, and no runtime authority fields.

Audit context validation requires audit context id, actor id, display name, supported role, supported actor source, supported permission scope, boolean authenticated value, optional action scope, optional audit reference, optional notes, and no runtime authority fields.

No function validates real authentication. No function checks an external identity provider. No network calls occur.

## 9. Serialization Rules

Actor serialization and deserialization use dictionaries with deterministic field names. Audit context serialization and deserialization use dictionaries with deterministic field names.

Round trips preserve the original metadata. Serialization does not write files, write databases, call services, call networks, or mutate runtime state.

## 10. Metadata Helper Rules

The actor metadata helpers are conservative:

- `actor_can_request_review` is true for reviewer, approver, operator, and admin metadata with a compatible permission scope.
- `actor_can_request_approval` is true for approver and admin metadata with a compatible permission scope.
- `actor_can_request_execution` is true for operator and admin metadata with a compatible permission scope.
- viewer metadata cannot request approval or execution.
- system metadata is for system-generated audit context only.

actor_can_* helpers are metadata helpers only. actor_can_* helpers do not enforce authorization.

## 11. Non-Goals

Phase 7AE does not implement authentication, login, logout, session management, password validation, identity provider integration, authorization enforcement, dashboard UI, CLI behavior changes, backend execution, governed write paths, backend writes, database writes, OCI/ADB dependencies, Object Storage integration, Oracle Agent Memory dependencies, semantic recall service dependencies, LLM calls, network calls, parser/scoring/decision/recommendation changes, Phase 4I mutation, or Phase 8 sizing/TCO.

No backend writes occur. No authentication provider is used.

## 12. Acceptance Criteria

Acceptance requires the `DashboardActorIdentity` object shape, `ActorAuditContext` object shape, supported role/source/scope constants, deterministic id helpers, validation helpers, serialization helpers, metadata helpers, documentation, and tests.

Acceptance also requires that actor_can_* helpers are metadata helpers only, actor_can_* helpers do not enforce authorization, no backend writes occur, no authentication provider is used, actor identity does not grant runtime authority, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
