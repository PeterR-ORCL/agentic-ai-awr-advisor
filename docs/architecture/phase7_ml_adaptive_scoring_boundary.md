# Phase 7S ML / Adaptive Scoring Boundary

## 1. Purpose

Phase 7S defines the ML / adaptive scoring boundary for the Agentic AI AWR Advisor project before any ML model, dataset builder, training harness, model registry, or runtime integration exists.

ML starts in shadow mode. Deterministic scoring remains authoritative. ML is non-authoritative by default, and deterministic runtime remains authoritative for parser output, feature engineering, scoring, trend/anomaly logic, decision logic, recommendations, and the Phase 4I output contract.

This phase establishes what future ML may observe, score, compare, explain, and propose. It also defines when ML is shadow-only, what must happen before runtime eligibility can be considered, and how future ML work relates to controlled materialization from Phase 7M–7R and to future Phase 8 sizing/TCO advisory.

## 2. Scope

Phase 7S covers boundary, documentation, inert local scaffolding, and validation assertions only. It defines future concepts and gates for adaptive scoring intelligence without implementing those concepts as runtime behavior.

The boundary applies to:

- deterministic score comparison;
- future trend-aware score comparison;
- future learned score comparison;
- future feature and label dataset governance;
- future ML candidate generation;
- future explainability and audit evidence;
- future model registry and certification gates;
- future runtime eligibility withdrawal and rollback.

## 3. Non-Goals

Phase 7S does not implement ML. learned_model(x) is not implemented. Score_ml(x) is not implemented. Score(x, t) is not implemented. No training is implemented. No backtesting is implemented. No feature/label dataset builder is implemented. No model registry is implemented. No model approval workflow is implemented. No model runtime activation is implemented.

Phase 7S does not modify parser behavior, parser output, scoring logic, scoring weights, scoring thresholds, decision logic, recommendation logic, trend/anomaly runtime behavior, the Phase 4I output contract, `run_analysis.py`, dashboard behavior, CLI behavior, database schema, generated dashboard HTML, or any runtime path.

Phase 7S does not add DB writes, OCI dependencies, ADB dependencies, Oracle Agent Memory dependencies, semantic recall service dependencies, LLM calls, network calls, dashboard ML controls, CLI ML commands, or Phase 8 sizing/TCO behavior.

## 4. Deterministic Scoring Boundary

The current deterministic scoring engine remains the runtime source of truth:

```text
Score(x)
```

Where `x` is the current deterministic feature vector produced by the existing parser and feature engineering pipeline. Score(x) remains authoritative in Phase 7S.

Future ML may compare against Score(x), explain disagreement with Score(x), and propose review candidates when governance permits. ML may not replace scoring, override deterministic severity, change deterministic confidence, or change recommendation truth.

## 5. ML Shadow Mode Boundary

ML starts in shadow mode. Shadow mode means ML output can be recorded, compared, explained, or reviewed as analytical context only. Shadow scoring is not runtime scoring.

ML is non-authoritative by default. ML predictions, ML scores, model confidence, feature influence, disagreement context, or explanations do not change runtime scoring, parser output, decision logic, recommendation truth, dashboard truth, CLI behavior, or the Phase 4I output contract.

Any future ML output must continue to report `runtime_influence_granted=false` and `runtime_active=false` until a later governed phase explicitly certifies runtime eligibility.

## 6. Observation Boundary

Future ML may observe governed inputs only after their source, schema, provenance, and retention rules are defined. Allowed observation sources may include:

- deterministic feature vectors;
- trends and anomalies;
- historical outcomes;
- governed feedback;
- action/outcome records;
- recommendation results;
- parser unknown records;
- materialization artifacts from Phase 7M–7R.

Observation does not imply scoring authority. Observation does not imply runtime influence. Observation does not allow ML to mutate the observed records.

## 7. Scoring Boundary

Future ML may score shadow-only analytical quantities, including shadow risk scores, shadow severity estimates, shadow anomaly confidence, shadow recommendation effectiveness, and future sizing inputs only after the Phase 8 boundary exists.

The following concepts are documented but not implemented:

```text
Score(x, t) = f(x, trends, anomalies)
Score_ml(x) = learned_model(x)
```

`t` is future time-series, trend, or anomaly context. Score(x, t) is not implemented in Phase 7S and belongs to future Phase 7U trend-aware scoring. Score_ml(x) is not implemented in Phase 7S and belongs to future Phase 7V shadow ML model interface. learned_model(x) is not implemented.

ML may compare, explain, and propose. ML may not replace scoring.

## 8. Proposal Boundary

Future ML may propose review candidates only. Possible proposal types include:

- scoring review candidates;
- threshold review candidates;
- trend/anomaly sensitivity review candidates;
- recommendation review candidates;
- model review candidates;
- parser review candidates through governance only.

ML proposals are not applied changes. A proposal is evidence for human review, not parser/scoring/recommendation truth.

## 9. Runtime Influence Boundary

ML may not:

- replace deterministic score;
- change severity;
- change confidence;
- change recommendation;
- classify parser output;
- modify parser output;
- modify Phase 4I;
- activate itself;
- bypass review;
- bypass Phase 7M–7R materialization.

ML runtime influence requires governance, validation, model registry approval, rollback, and certification. Runtime eligibility requires an explicit runtime eligibility decision after those gates pass. Until then, ML remains shadow-only and non-authoritative.

## 10. Governance Boundary

Future ML runtime eligibility requires human approval and actor-specific ownership. At minimum, the governed path must include:

- model owner approval;
- scoring owner approval;
- parser owner approval when parser proposals are involved;
- recommendation owner approval when recommendation proposals are involved;
- governance reviewer approval;
- validation reviewer approval;
- release/certification approval.

Model validation is not runtime activation. Model approval is not runtime activation. Runtime eligibility requires explicit certification.

## 11. Materialization Boundary

ML cannot bypass materialization. Any future ML-driven parser, scoring, recommendation, threshold, trend/anomaly, or model-runtime change must flow through controlled materialization from Phase 7M–7R.

The relationship is:

```text
ML shadow observation
-> ML comparison / explanation
-> governed proposal candidate
-> Phase 7M–7R materialization path
-> validation evidence
-> rollback plan
-> certification
-> explicit runtime eligibility decision
```

Candidate approval is not activation. Materialization is not activation. Runtime eligibility is separate from both approval and materialization.

## 12. Validation Boundary

Future ML runtime eligibility requires validation evidence before any runtime influence can be considered. Required evidence must include deterministic regression validation, before/after comparison against Score(x), disagreement analysis, false positive/false negative review, backtesting, stability checks, drift checks, explainability checks, rollback rehearsal, Phase 4I contract validation, and controlled materialization validation.

Phase 7S does not implement backtesting. Phase 7S only documents that future Phase 7W training/backtesting must exist before runtime eligibility can be considered.

## 13. Explainability Boundary

Any future ML score must include explanation, feature influence, confidence, and disagreement context. Explanations must identify:

- input feature schema version;
- label schema version;
- model version;
- dataset version;
- top contributing features;
- confidence and calibration context;
- disagreement with Score(x);
- any trend/anomaly context used;
- known limitations;
- reviewer notes.

Explainability is required for review and audit. Explainability does not activate runtime influence.

## 14. Rollback Boundary

Future ML runtime eligibility requires a rollback plan before activation can be considered. Rollback must identify the model version, dataset version, feature schema version, label schema version, scoring integration point, affected recommendations, validation evidence to rerun, responsible operator, and decision record that withdraws eligibility.

Runtime eligibility can be withdrawn. Withdrawing eligibility must restore deterministic Score(x) as the only authoritative scoring path and must leave parser, scoring, decision, recommendation, dashboard, CLI, and Phase 4I behavior deterministic and validated.

## 15. Semantic Context Boundary

ML and semantic context are separate. Semantic context is reviewer-assist. ML model output is analytical/shadow. Neither is deterministic runtime truth by default.

Semantic recall, Oracle Agent Memory, LLM summaries, and reviewer-assist context cannot become ML labels, scoring evidence, parser evidence, recommendation evidence, approval evidence, or runtime evidence unless a later governed phase defines that path explicitly.

Phase 7S adds no Oracle Agent Memory dependency, no semantic recall service dependency, and no LLM calls.

## 16. Parser Boundary

ML may not change parser output. ML may not classify unknown parser records into parser truth. ML may not mutate parser mappings, rewrite parser sections, update parser rules, or change loader behavior.

Future ML may propose parser review candidates only through controlled evidence and governance. Parser review candidates must flow through Phase 7M–7R materialization, parser-owner review, parser tests, AWR regression validation, Phase 4I contract validation, rollback planning, and certification before runtime eligibility can be considered.

## 17. Recommendation Boundary

ML may not change recommendation truth. ML may not change recommendation priority, ranking, rationale, supporting evidence, action sequencing, or output contracts.

Future ML may estimate shadow recommendation effectiveness and propose recommendation review candidates. Those candidates must flow through Phase 7M–7R materialization, recommendation-owner review, evidence mapping validation, recommendation regression tests, rollback planning, and certification before runtime eligibility can be considered.

## 18. Phase 4I Contract Boundary

Phase 4I remains the validated output contract consumed by the dashboard and other presentation layers. ML may not change Phase 4I output. ML may not add runtime fields to Phase 4I, remove fields from Phase 4I, reinterpret diagnostic truth, rewrite severity, or alter recommendation truth.

Future ML metadata may be considered only after a later governed contract extension is designed, validated, documented, versioned, and certified.

## 19. Phase 8 Boundary

Phase 8 sizing/TCO is not implemented here. Phase 8 may later consume validated intelligence only after Phase 7 ML boundaries, validation evidence, governance, materialization, rollback, and certification are in place.

Phase 7S does not implement sizing, TCO, what-if advisory, capacity modeling, cost modeling, or advisory runtime changes.

## 20. Future Phase 7T Dataset Model

Future Phase 7T defines the feature / label dataset model:

```text
(X, y)
```

`X` represents governed feature vectors. `y` represents observed outcomes, tuning success, performance results, accepted/rejected recommendations, recurrence, false positives, or risk confirmation.

Phase 7S documents the concept only. The 7T dataset model is not implemented here. No feature/label dataset builder exists in Phase 7S.

## 21. Future Phase 7U Trend-Aware Scoring

Future Phase 7U may define trend-aware scoring:

```text
Score(x, t) = f(x, trends, anomalies)
```

The 7U trend-aware scoring concept remains shadow/advisory until certified. Score(x, t) is not implemented in Phase 7S.

## 22. Future Phase 7V Shadow ML Model Interface

Future Phase 7V may define a shadow ML model interface:

```text
Score_ml(x) = learned_model(x)
```

The 7V shadow ML model interface is not implemented in Phase 7S. Score_ml(x) is not implemented. learned_model(x) is not implemented. Any future learned score remains shadow/advisory until certified.

## 23. Future Phase 7W Training / Backtesting

Future Phase 7W may define training and backtesting. The 7W training/backtesting phase must define train/test separation, leakage controls, reproducibility, baseline comparison, drift checks, performance metrics, false positive/false negative review, and governed evidence retention.

Phase 7S implements none of this behavior.

## 24. Future Phase 7X Explainability

Future Phase 7X may define explainability artifacts and review evidence. The 7X explainability phase must require feature influence, confidence, disagreement context, model limitation notes, and reviewer-visible explanations.

Phase 7S documents explainability as a requirement only.

## 25. Future Phase 7Y Model Registry

Future Phase 7Y may define a model registry. The 7Y model registry must version models, datasets, feature schema, label schema, metrics, approval state, validation results, runtime eligibility, rollback plans, and retirement state.

Phase 7S does not implement a model registry.

## 26. Future Phase 7Z ML Certification

Future Phase 7Z may define ML certification. The 7Z certification phase must prove that governance, validation, explainability, materialization, rollback, runtime eligibility, and contract preservation are complete before any ML runtime influence can be considered.

Phase 7S does not certify any model and does not grant runtime influence.

## 27. Acceptance Criteria

Phase 7S is accepted when:

- the ML / adaptive scoring boundary is documented;
- the ML lifecycle is documented;
- ML starts in shadow mode;
- deterministic scoring remains authoritative;
- ML is non-authoritative by default;
- learned_model(x) is not implemented;
- Score_ml(x) is not implemented;
- Score(x, t) is not implemented;
- ML may compare, explain, and propose;
- ML may not replace scoring;
- ML may not change parser output;
- ML may not change recommendation truth;
- ML may not change Phase 4I output;
- ML may not bypass Phase 7M–7R materialization;
- ML runtime influence requires governance, validation, model registry, rollback, and certification;
- Phase 8 sizing/TCO is not implemented here;
- no parser, scoring, decision, recommendation, dashboard, CLI, database, generated HTML, or runtime behavior changes are made.
