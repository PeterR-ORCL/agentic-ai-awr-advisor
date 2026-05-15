# Phase 7AQ.1 Evidence Availability Review

## 1. Purpose

Phase 7AQ.1 defines Screen 2-specific evidence availability and missing metric review metadata for future diagnostic review workflows.

Evidence availability review classifies missing, insufficient, unavailable, unsupported, not extracted, and unreliable evidence for governance. It does not alter diagnosis or scoring.

## 2. Scope

The scope is local evidence review metadata, supported evidence statuses, reliability statuses, missing reasons, confidence impact metadata, parser/source/scoring/recommendation review recommendation flags, deterministic classification helpers, serialization helpers, validation helpers, documentation, and tests.

Phase 7AQ.1 is review-model only. It creates no candidates and invokes no workflow bridge.

## 3. Non-Goals

Phase 7AQ.1 does not alter diagnosis, alter scoring, alter recommendations, adjust confidence, change severity, change domain scores, change evidence values, mutate parser output, call backend code, invoke governed write paths, persist records, create learning candidates automatically, implement UI, or implement Phase 8 sizing/TCO.

Evidence availability review does not alter diagnosis. Evidence availability review does not alter scoring. Evidence availability review does not alter recommendations. No candidate is created automatically. EM Extract implementation belongs to Phase 8.

## 4. Evidence Availability Review

Evidence availability review is metadata attached to an evidence review record.

It can classify whether a metric is unavailable, absent from AWR, unsupported by topology or platform, not extracted by the parser, present but unreliable, insufficient for confidence, or related to recommendation context. These classifications are governance inputs only.

## 5. Evidence Statuses

Supported evidence statuses are `available`, `unavailable`, `missing`, `unsupported`, `not_extracted`, `not_reliable`, `not_applicable`, and `unknown`.

Statuses describe evidence review posture. They do not rewrite evidence or change diagnostic truth.

## 6. Reliability Statuses

Supported reliability statuses are `reliable`, `partially_reliable`, `unreliable`, `insufficient_context`, and `unknown`.

Reliability status is reviewer-assessment metadata. It does not alter runtime confidence, score, severity, or recommendation truth.

## 7. Missing Reasons

Supported missing reasons are `absent_from_report`, `unsupported_by_topology`, `unsupported_by_platform`, `parser_gap`, `source_not_collected`, `source_misconfigured`, `value_not_reliable`, `not_applicable`, and `unknown`.

Missing reasons help future governance routing. They do not create candidates automatically.

## 8. Parser Review Recommendation

`parser_gap` and `not_extracted` evidence recommend parser review.

Parser review recommendation is metadata only. It does not mutate parser output, create parser mappings, or create parser candidates automatically.

## 9. Source Review Recommendation

`source_not_collected` and `source_misconfigured` recommend source review.

Source review recommendation is metadata only. It does not load local files, query databases, call object storage, or validate credentials.

## 10. Scoring Review Recommendation

Missing score or domain score evidence may recommend scoring review.

Scoring review recommendation is metadata only. It does not change scores, domain scores, severity, confidence, or scoring behavior.

## 11. Recommendation Review Recommendation

Missing or unreliable `recommendation_context` evidence may recommend recommendation review.

Recommendation review recommendation is metadata only. It does not change recommendations, recommendation ranking, recommendation rationale, action records, or outcome records.

## 12. Confidence Impact

Confidence impact may be recorded as `none`, `low`, `medium`, `high`, or `unknown`.

Confidence impact metadata describes review concern only. It does not alter runtime confidence, score, severity, diagnosis, or recommendations.

## 13. Candidate Linkage Boundary

Missing metric review candidates are future workflow links only.

No candidate is created automatically. A missing metric, parser gap, source gap, scoring concern, or recommendation context concern may become eligible for future governance linkage, but Phase 7AQ.1 does not create or persist that candidate.

## 14. Relationship to 7AO.1

Phase 7AO.1 introduced validation-only missing metric / evidence availability handling for Screen 3 re-analysis readiness.

Phase 7AQ.1 builds on those concepts for Screen 2 diagnostic review records. It remains local review metadata and does not alter diagnosis, scoring, recommendations, parser output, Phase 4I, or runtime truth.

## 15. Relationship to Future 7AR

Future 7AR may route evidence availability review records to governance.

Phase 7AQ.1 does not route records, write governance records, invoke governed write paths, or create candidates.

## 16. Relationship to Phase 8

EM Extract implementation belongs to Phase 8.

Phase 7AQ.1 does not implement EM Extract, sizing, TCO, what-if advisory, capacity planning, cost modeling, or sizing recommendation workflows.

## 17. Acceptance Criteria

Phase 7AQ.1 is accepted when Screen 2 evidence availability review metadata exists, evidence statuses are validated, reliability statuses are validated, missing reasons are validated, parser/source/scoring/recommendation review recommendation flags are deterministic, serialization/deserialization helpers round trip, and tests prove the model is local-only.

Acceptance also requires that evidence availability review does not alter diagnosis, evidence availability review does not alter scoring, evidence availability review does not alter recommendations, missing metric review candidates are future workflow links only, no candidate is created automatically, EM Extract implementation belongs to Phase 8, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
