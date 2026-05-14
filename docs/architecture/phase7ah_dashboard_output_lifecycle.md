# Phase 7AH Dashboard Output Refresh / Artifact Lifecycle

## 1. Purpose

Phase 7AH defines the local dashboard output lifecycle boundary for future
governed dashboard workflows. It provides deterministic metadata shapes for
workflow outputs, refresh instructions, output validation, and artifact
references.

This phase does not write artifacts. This phase does not regenerate dashboards.
This phase does not mutate Phase 4I. This phase does not execute refresh.

## 2. Scope

Phase 7AH covers output artifact metadata and refresh instruction metadata for
future dashboard workflows. It defines artifact types, refresh modes, lifecycle
statuses, safety flags, validation rules, deterministic identifiers, and
serialization rules.

Output records are metadata only. Refresh instructions are metadata only.

## 3. Non-Goals

Phase 7AH does not generate files, write DB records, call backend execution,
call object storage, update dashboard state, call analysis entrypoints, mutate
Phase 4I, modify parser/scoring/decision/recommendation behavior, add dashboard
buttons, add dashboard forms, add CLI commands, implement Screen 2/3/5/6
workflows, implement re-analysis, or implement Phase 8 sizing/TCO.

## 4. Why Output Lifecycle Is Needed

Future dashboard workflows need traceable output descriptions. Screen 3
analysis requests will need run records, comparison artifacts, refreshed payload
references, dashboard artifact references, source validation artifacts, and error
artifacts. Screen 2, Screen 5, and Screen 6 review workflows will need review,
outcome, governance, and audit artifacts.

Without a shared lifecycle model, each future workflow could invent incompatible
output fields and refresh semantics.

## 5. Output Artifact Types

Supported artifact types are:

- `validation_response`
- `analysis_run_record`
- `phase4i_payload_reference`
- `dashboard_artifact_reference`
- `comparison_artifact`
- `error_artifact`
- `source_validation_artifact`
- `object_storage_load_artifact`
- `workflow_audit_artifact`
- `governance_review_artifact`
- `outcome_capture_artifact`

These types describe future outputs. They do not prove that any output was
physically created by Phase 7AH.

## 6. Refresh Modes

Supported refresh modes are:

- `no_refresh`
- `show_message`
- `link_to_artifact`
- `link_to_run`
- `regenerate_dashboard_requested`
- `future_live_refresh`

`regenerate_dashboard_requested` is request metadata only. `future_live_refresh`
is request metadata only. Neither mode executes refresh in Phase 7AH.

## 7. Lifecycle Statuses

Supported lifecycle statuses are:

- `PROPOSED`
- `VALIDATED`
- `AVAILABLE`
- `FAILED`
- `SUPERSEDED`
- `CLOSED`

No lifecycle status means an artifact was physically written by 7AH.

## 8. Output Artifact Record

The output artifact record captures artifact identity, artifact type, source
request id, source validation id, source audit id, run id, Phase 4I reference,
dashboard reference, comparison reference, artifact URI, summary, lifecycle
status, validation status, error summary, creator metadata, safety flags, and
notes.

Every output artifact preserves:

- `output_written=false`
- `dashboard_regenerated=false`
- `phase4i_mutated=false`
- `runtime_mutation_performed=false`

## 9. Refresh Instruction Record

The refresh instruction record captures refresh identity, artifact identity,
refresh mode, display message, link target, run id, dashboard reference,
display-safety metadata, manual action requirement, refresh status, and notes.

Every refresh instruction preserves `refresh_performed=false`.

## 10. Validation Response Artifacts

Validation response artifacts describe future validation results. They can link
to a governed write request, backend execution request, or workflow validation
record. They are not backend writes and they do not authorize runtime mutation.

## 11. Analysis Run Artifacts

Analysis run artifacts describe future run records. They require a run id. They
do not execute analysis and they do not call backend execution in Phase 7AH.

## 12. Phase 4I Payload References

Phase 4I payload reference artifacts describe a future validated payload
reference. They require `phase4i_reference`. They do not mutate Phase 4I and do
not change the Phase 4I output contract.

## 13. Dashboard Artifact References

Dashboard artifact reference records describe a future dashboard artifact
reference. They require `dashboard_reference`. They do not regenerate dashboards
or update dashboard state in Phase 7AH.

## 14. Comparison Artifacts

Comparison artifacts describe future comparison output references. They require
`comparison_reference`. They do not build a comparison artifact in Phase 7AH.

## 15. Error Artifacts

Error artifacts describe failure metadata. They require `error_summary`. They do
not create error files and they do not write DB records.

## 16. Source Validation / Object Storage Artifacts

Source validation artifacts and object storage load artifacts describe future
source validation or load results. They do not call object storage and they do
not load sources in Phase 7AH.

## 17. Audit Artifacts

Workflow audit artifacts describe future audit outputs. They do not replace the
7AG governed write audit record, and they are not backend writes.

## 18. Runtime Truth Boundary

Deterministic runtime remains authoritative. Output lifecycle records do not
change parser output, scoring, decisions, recommendations, runtime gates, or
dashboard truth.

## 19. Phase 4I Boundary

Phase 7AH does not mutate Phase 4I. Phase 4I payload references are metadata
only, and the Phase 4I contract remains protected.

## 20. Dashboard Refresh Boundary

Phase 7AH does not regenerate dashboards and does not execute refresh. Refresh
instructions describe how a future dashboard may present an output after a
separate governed workflow has completed.

## 21. Relationship to 7AD

7AD established that future dashboard workflow outputs must be traceable,
auditable, and separate from runtime truth. 7AH supplies the metadata model for
those future output references.

## 22. Relationship to 7AF

7AF defines backend execution request metadata. 7AH can describe future
validation responses or run artifacts related to those requests, but it does not
execute requests.

## 23. Relationship to 7AG

7AG defines governed write request, validation, and audit metadata. 7AH can
describe output artifacts produced by future governed handling, but it does not
perform a write and does not replace 7AG audit metadata.

## 24. Relationship to Future Screen 3 Re-Analysis

Future Screen 3 re-analysis may create run records, refreshed payload
references, comparison artifacts, and dashboard artifact references. Phase 7AH
only defines how those records will be described.

## 25. Relationship to Phase 8

Phase 8 sizing/TCO and what-if advisory workflows are out of scope. Phase 7AH
does not implement sizing, TCO, what-if calculations, or cost artifacts.

## 26. Acceptance Criteria

- Output artifact metadata exists.
- Refresh instruction metadata exists.
- Output records are metadata only.
- Refresh instructions are metadata only.
- This phase does not write artifacts.
- This phase does not regenerate dashboards.
- This phase does not mutate Phase 4I.
- This phase does not execute refresh.
- Safety flags remain false.
- Deterministic runtime remains authoritative.
- No dashboard UI is changed.
- No CLI behavior is changed.
- No backend execution is added.
- No parser/scoring/decision/recommendation behavior changes are added.
- Phase 8 sizing/TCO is not implemented.
