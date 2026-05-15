# Phase 7AO Missing Metric Evidence Availability

## 1. Purpose

Phase 7AO.1 defines validation-only missing metric / evidence availability handling for Screen 3 re-analysis and comparison readiness.

## 2. Scope

The scope is local classification and summary metadata for supplied evidence records. The model reports whether evidence is available, missing, unavailable, unsupported, not extracted, unreliable, not applicable, or unknown.

## 3. Non-Goals

Evidence availability handling does not alter diagnosis, does not alter scoring, does not alter recommendations, does not alter parser output, does not call parser, does not call run_analysis.py, does not read files, does not query DB, does not call object storage, and does not create learning candidates automatically.

## 4. Evidence Availability Record

An EvidenceAvailabilityRecord captures evidence id, evidence name, evidence type, domain, source report/run identifiers, availability status, reliability status, missing reason, confidence impact, diagnosis/comparison impact flags, review recommendation flags, fallback evidence, and notes.

## 5. Evidence Availability Summary

An EvidenceAvailabilitySummary aggregates records into total, available, missing, unreliable, unsupported, and parser gap counts. It also reports confidence impact summary, parser/source/scoring review recommendation flags, warnings, and required next steps.

## 6. Evidence Types

Supported evidence types are metric, wait_event, sql_signal, trend, anomaly, topology, platform, source_option, score, recommendation_context, and unknown.

## 7. Availability Statuses

Supported availability statuses are available, missing, unavailable, unsupported, not_extracted, not_reliable, not_applicable, and unknown.

## 8. Reliability Statuses

Supported reliability statuses are reliable, partially_reliable, unreliable, insufficient_context, and unknown.

## 9. Missing Reasons

Supported missing reasons are absent_from_report, unsupported_by_topology, unsupported_by_platform, parser_gap, source_not_collected, source_misconfigured, value_not_reliable, not_applicable, and unknown.

## 10. Confidence Impact

Confidence impact is validation metadata only. It may be none, low, medium, high, or unknown. It does not mutate runtime confidence, scoring, diagnosis, or recommendations.

## 11. Parser Review Recommendation

Parser review may be recommended when evidence is not_extracted or the missing reason is parser_gap. Missing metric review candidates are recommendations for future workflow only.

## 12. Source Review Recommendation

Source review may be recommended when evidence indicates source_not_collected or source_misconfigured. It does not load sources or validate object storage credentials.

## 13. Scoring Review Recommendation

Scoring review may be recommended for high-impact score evidence, but evidence availability handling does not alter scoring.

## 14. Relationship to Re-Analysis Validation

Re-analysis validation uses evidence availability summaries to report warnings and next steps before any future execution can be considered.

## 15. Relationship to Screen 2 Future 7AQ.1

Screen 2 evidence review model remains future 7AQ.1. Phase 7AO.1 classifies evidence availability only and does not implement the Screen 2 diagnostic review workflow.

## 16. Relationship to Phase 8 EM Extract

Future EM Extract support belongs to Phase 8. EM Extract implementation belongs to Phase 8.

## 17. Acceptance Criteria

- Evidence records validate supported evidence types, availability statuses, reliability statuses, missing reasons, and confidence impacts.
- Evidence summaries count available, missing, unreliable, unsupported, and parser gap records.
- Parser/source/scoring review recommendation flags are deterministic.
- Evidence availability handling does not alter diagnosis.
- Evidence availability handling does not alter scoring.
- Evidence availability handling does not alter recommendations.
- Missing metric review candidates are recommendations for future workflow only.
- EM Extract implementation belongs to Phase 8.
