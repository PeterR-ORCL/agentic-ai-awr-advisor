# Phase 7X ML Explainability Layer

## 1. Purpose

Phase 7X defines a local, deterministic ML explainability layer for advisory and shadow Phase 7 ML artifacts. It explains deterministic baseline score context, Phase 7U trend-aware score context, Phase 7V shadow ML output context, and Phase 7W training/backtesting evaluation context.

Explainability is not runtime truth. Explanations do not change runtime scoring. Deterministic scoring remains authoritative.

## 2. Scope

Phase 7X adds explanation records, feature contribution records, score comparison explanation records, confidence/uncertainty explanation records, disagreement summaries, evidence references, boundary summaries, validation rules, deterministic ID helpers, and serialization/deserialization helpers.

The layer is local only and deterministic. It uses explanation records to describe advisory/shadow outputs. It does not apply those explanations to parser output, scoring, decisions, recommendations, dashboard behavior, CLI behavior, database state, or Phase 4I output.

## 3. Non-Goals

Phase 7X does not change runtime scoring weights, scoring thresholds, severity cutoffs, confidence logic, trend/anomaly runtime behavior, decision logic, recommendation logic, recommendation ranking, parser behavior, parser output, Phase 4I output, dashboard behavior, CLI behavior, database schema, or generated dashboard HTML.

Phase 7X does not train models, implement learned_model(x), activate models, create model registry behavior, approve models for runtime, write databases, call OCI, call Oracle Agent Memory, call LLMs, call network services, or add dashboard/CLI explainability controls.

No model registry is implemented. No runtime activation is implemented. Phase 8 sizing/TCO is not implemented.

## 4. Explainability Is Not Runtime Truth

Explainability is not runtime truth. An explanation can describe why a shadow or advisory result differs from deterministic scoring, but it cannot make that shadow or advisory result authoritative.

Explanation records are interpretation artifacts only. They do not update runtime score, severity, confidence, decision, recommendation, parser output, Phase 4I output, dashboard state, or CLI behavior.

## 5. Feature Contributions

Feature contributions are explanatory only. They describe deterministic placeholder signals such as whether a feature name and value suggest increased risk, decreased risk, neutral context, or insufficient context.

Contribution weights do not become model weights. Contribution strength does not become runtime score influence. Feature contributions do not add new diagnostic evidence and do not alter scoring thresholds or severity cutoffs.

## 6. Score Comparison Explanation

Score comparison explanations compare deterministic score, trend-aware score, and shadow ML score where present. The deterministic score remains the runtime source of truth.

Trend delta and shadow delta are deterministic arithmetic comparisons against the deterministic score. They explain disagreement; they do not resolve disagreement by changing runtime scoring.

## 7. Confidence / Uncertainty Explanation

Confidence explanation records describe confidence as a 0.0 to 0.95 advisory confidence/uncertainty value. Confidence is not score.

Confidence factors and insufficient context flags help reviewers understand why an explanation may be more or less reliable. They do not modify the deterministic score, trend-aware score, shadow ML score, runtime confidence logic, or Phase 4I output.

## 8. Disagreement Explanation

Disagreement summaries describe differences among deterministic, trend-aware, and shadow ML scores. Supported disagreement levels are `none`, `low`, `moderate`, `high`, and `insufficient_context`.

A disagreement between deterministic, trend-aware, and shadow ML scores is advisory. It does not change scoring authority, decisions, recommendations, parser behavior, dashboard behavior, or CLI behavior.

## 9. Evidence References

Evidence references are traceability aids. They can point to local advisory records, feature datasets, trend results, shadow outputs, or backtesting records.

Evidence references do not become new diagnostic evidence. They do not alter parser output, runtime scoring, decisions, recommendations, or Phase 4I output.

## 10. Boundary Summary

Every ML explanation record includes a boundary summary stating that the explanation is advisory/shadow only and does not change runtime scoring.

The boundary summary also preserves the required flags: `runtime_influence=false`, `runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true`.

## 11. Runtime Influence Boundary

Phase 7X validation rejects `runtime_influence=true`, `runtime_active=true`, and `runtime_influence_granted=true`.

No explanation record may be runtime active. No explanation record may grant runtime influence. No explanation helper may apply a change to runtime scoring, decisions, recommendations, parser output, dashboard behavior, CLI behavior, or Phase 4I output.

## 12. Deterministic Runtime Boundary

Deterministic scoring remains authoritative. Phase 7X can explain deterministic score context and compare advisory scores against it, but it cannot replace or revise deterministic scoring.

All IDs are deterministic and use stable inputs. No UUID, timestamp, database sequence, current time, network call, or external service is used to construct explanation IDs.

## 13. Relationship to Phase 7S

Phase 7S established the ML/adaptive scoring boundary, including shadow mode, no learned_model(x), no model activation, and no runtime scoring changes. Phase 7X preserves that boundary and adds explanation records only.

Phase 7X explains shadow/advisory artifacts inside the Phase 7S boundary. It does not expand the runtime boundary.

## 14. Relationship to Phase 7T

Phase 7T defines governed feature/label dataset records. Phase 7X can consume feature values and feature references as explanation inputs.

A feature/label dataset remains a governed local dataset, not a model. Semantic context is not ML explanation. Feature contributions are explanatory only and do not become training weights or runtime scoring weights.

## 15. Relationship to Phase 7U

Phase 7U trend-aware scoring remains advisory. Phase 7X can explain a Phase 7U trend-aware score and compare it to deterministic scoring.

The trend-aware score remains non-authoritative. Explanations do not activate trend-aware scoring or change runtime trend/anomaly behavior.

## 16. Relationship to Phase 7V

Phase 7V shadow ML output remains non-authoritative. Phase 7X can explain the shadow ML score, confidence, disagreement summary, and boundary status.

The shadow ML output does not become runtime truth. Phase 7X does not activate Score_ml(x), implement learned_model(x), or grant runtime influence.

## 17. Relationship to Phase 7W

Phase 7W training/backtesting artifacts are local evaluation records only. Phase 7X can reference those artifacts as explanatory evidence and describe metrics in boundary-aware explanations.

Training/backtesting success is not runtime activation. Backtesting metrics remain evidence records, not runtime approval or model registry entries.

## 18. Relationship to Future Phase 7Y

Future Phase 7Y may define governed model registry behavior. Phase 7X does not implement a model registry.

Explanation IDs, model IDs, and evidence references are local traceability fields only. They do not register, approve, certify, deploy, or activate a model.

## 19. Relationship to Future Phase 7Z

Future Phase 7Z may define certification or runtime activation governance. Phase 7X does not implement runtime activation.

No explanation record certifies runtime use. No explanation status means approved, certified, active, or runtime eligible.

## 20. Relationship to Phase 8

Phase 8 sizing/TCO is not implemented. Phase 7X does not implement sizing, capacity planning, TCO, cost modeling, what-if advisory, or resource recommendation behavior.

Explainability can describe ML/advisory score context only. It does not estimate infrastructure size or cost.

## 21. Acceptance Criteria

Phase 7X is accepted when the ML explainability layer exists; feature contribution, score comparison explanation, confidence explanation, and ML explanation record models exist; deterministic explanation helpers exist; validation rejects runtime influence and runtime activation; serialization/deserialization helpers exist; explanations are not runtime truth; feature contributions are explanatory only; confidence is not score; no model registry is implemented; no runtime activation is implemented; deterministic scoring remains authoritative; no runtime scoring changes are applied; no parser/scoring/decision/recommendation behavior changes are applied; no dashboard behavior is changed; no CLI behavior is changed; and Phase 8 sizing/TCO is not implemented.
