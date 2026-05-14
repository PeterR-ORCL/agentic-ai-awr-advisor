# Phase 7AE Dashboard Actor / Reviewer Identity

## 1. Purpose

Phase 7AE defines the local dashboard actor/reviewer identity model required by future governed dashboard workflows.

Actor identity is required metadata for future governed write workflows. It gives future workflow requests a consistent actor shape before write paths, backend execution requests, review actions, approval actions, outcome capture, parser governance, materialization review, model registry review, and runtime gate review exist.

## 2. Scope

The scope is local deterministic actor metadata, reviewer role metadata, permission scope metadata, actor validation, audit context validation, serialization/deserialization helpers, deterministic actor identifiers, deterministic actor audit context identifiers, and safe system or unknown actor handling.

The implementation is standard-library-only and safe to import.

## 3. Non-Goals

Phase 7AE does not implement authentication. It does not implement login, logout, password validation, identity provider integration, session management, dashboard login UI, or real user verification.

Phase 7AE does not implement authorization enforcement. Permission scope is metadata only, and authorization/write-path enforcement is future 7AG.

Phase 7AE does not add dashboard buttons, dashboard forms, dashboard write controls, Screen 2/3/5/6 workflows, backend execution, governed write path behavior, output artifact lifecycle behavior, API routes, database writes, OCI/ADB dependencies, Oracle Agent Memory dependencies, semantic recall service dependencies, LLM calls, network calls, or Phase 8 sizing/TCO.

No dashboard UI is changed. No CLI behavior is changed. No run_analysis.py wiring is added. Parser, scoring, decision, recommendation, and Phase 4I behavior are unchanged.

## 4. Why Actor Identity Is Needed

Future dashboard workflows need a consistent actor model for Screen 2 diagnostic review / approval, Screen 3 backend re-analysis request, Screen 5 recommendation action / outcome tracking, Screen 1 parser unknown review, Screen 6 candidate / materialization / model registry review, index source-mode workflow, backend execution requests, governed write-path actions, and audit trails.

Without this common model, each screen would invent inconsistent identity fields. Phase 7AE defines the shared metadata first.

## 5. Actor Identity Boundary

An actor represents a person or system identity associated with a future dashboard workflow action.

Actor identity does not grant runtime authority. Actor identity does not mutate backend truth. Actor identity does not authorize mutation by itself. It is required metadata only.

## 6. Reviewer Boundary

A reviewer is a human actor who can be associated with future review metadata for evidence, candidates, actions, outcomes, materialization, model registry posture, or runtime gate posture.

Phase 7AE does not implement reviewer assignment, reviewer queues, reviewer UI, or reviewer approval workflows.

## 7. Actor Roles

Supported actor roles are `viewer`, `reviewer`, `approver`, `operator`, `admin`, and `system`.

Role metadata helps future workflows describe who requested an action. Role metadata does not enforce authorization and does not grant runtime authority.

## 8. Actor Sources

Supported actor sources are `local`, `cli`, `dashboard`, `system`, and `unknown`.

Actor source metadata describes where the identity metadata originated. It does not prove authentication and does not authorize a write.

## 9. Permission Scopes

Supported permission scopes are `read_only`, `review`, `approve`, `execute`, and `administer`.

Permission scope is metadata only in Phase 7AE. It does not enforce authorization, does not create a write path, does not bypass validation, and does not grant runtime authority.

## 10. Audit Context

Actor audit context is the normalized actor metadata future workflow actions will include in audit records. It includes actor id, display name, role, actor source, permission scope, authenticated flag, audit reference, action scope, and notes.

Audit context is trace metadata only. It does not authorize action by itself and does not mutate backend truth.

## 11. Authentication Boundary

Phase 7AE does not implement authentication. The `authenticated` field is a boolean metadata field supplied by future callers. It is not verified against a password, identity provider, session, token, SSO service, dashboard login, CLI login, or external service.

## 12. Authorization Boundary

Phase 7AE does not implement authorization enforcement. Metadata helpers may conservatively indicate whether an actor shape looks appropriate for review, approval, or execution requests, but those helpers do not enforce authorization.

Authorization, governed writes, and execution gating are future 7AG work.

## 13. Runtime Truth Boundary

Deterministic runtime remains authoritative. Actor identity does not modify parser output, scoring, decisions, recommendations, Phase 4I output, runtime gate state, generated dashboard HTML, or backend runtime behavior.

## 14. Dashboard Workflow Relationship

Phase 7AE satisfies the actor identity prerequisite identified by Phase 7AD. Future dashboard workflows may reference actor identity metadata, but Phase 7AE does not add workflow actions and does not wire identity into dashboard UI.

## 15. Relationship to Future 7AF

Future 7AF may define backend execution mode boundaries. Phase 7AE only provides actor metadata that future execution requests may include.

## 16. Relationship to Future 7AG

Future 7AG may define authorization and governed write-path enforcement. Phase 7AE does not enforce authorization and does not create write paths.

## 17. Relationship to Future Screen Workflows

Future Screen 1, Screen 2, Screen 3, Screen 4, Screen 5, Screen 6, and index/source-mode workflows may require actor identity before review, approval, execution, action, outcome, parser governance, materialization review, model registry review, runtime gate review, or source handoff actions.

Those screen workflows are not implemented in Phase 7AE.

## 18. Relationship to Phase 8

Phase 8 sizing/TCO is not implemented. Phase 7AE does not add sizing, TCO, what-if advisory, capacity planning, cost modeling, or sizing recommendation workflows.

## 19. Acceptance Criteria

Phase 7AE is accepted when the local actor identity model exists, actor audit context exists, deterministic actor ids exist, deterministic audit context ids exist, validation helpers exist, serialization/deserialization helpers exist, metadata helper behavior exists, documentation exists, tests exist, this phase does not implement authentication, this phase does not implement authorization enforcement, permission scope is metadata only, actor identity does not grant runtime authority, actor identity does not mutate backend truth, actor identity is required for future governed write workflows, no dashboard UI is changed, no CLI behavior is changed, no run_analysis.py wiring is added, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
