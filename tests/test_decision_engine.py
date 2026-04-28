from __future__ import annotations

import json
import unittest
from typing import Any, cast

from src.analysis.decision_engine import DOMAIN_ORDER, build_decision
from src.analysis.scoring_adapter import build_decision_input_from_score_result
from src.models.decision import DecisionInput


def _decision_input(
    canonical_domain_scores: dict[str, float],
    *,
    severity: float = 45.0,
    confidence: float = 0.72,
    coverage_ratio: float = 0.8,
    primary_signal_domain: str | None = None,
    feature_evidence: dict[str, object] | None = None,
) -> DecisionInput:
    return DecisionInput(
        awr_id=1,
        canonical_domain_scores=canonical_domain_scores,
        severity_input=severity,
        confidence_input=confidence,
        completeness=coverage_ratio,
        primary_signal_domain=primary_signal_domain,
        feature_evidence=feature_evidence or {},
        score_evidence={
            "canonical_domain_scores": canonical_domain_scores,
            "score_result": {
                "severity_score": severity,
                "confidence": confidence,
                "coverage_ratio": coverage_ratio,
                "primary_signal_domain": primary_signal_domain,
                "model_code": "AWR_WEIGHTED_CORE",
                "model_version": "1.0.0",
                "decision_domain": "SIZING",
            },
        },
    )


def _decision_input_with_anomalies(
    canonical_domain_scores: dict[str, float],
    anomaly_signals: list[dict[str, object]],
    *,
    severity: float = 45.0,
    confidence: float = 0.72,
    coverage_ratio: float = 0.8,
    primary_signal_domain: str | None = None,
) -> DecisionInput:
    return DecisionInput(
        awr_id=1,
        canonical_domain_scores=canonical_domain_scores,
        severity_input=severity,
        confidence_input=confidence,
        completeness=coverage_ratio,
        primary_signal_domain=primary_signal_domain,
        score_evidence={
            "canonical_domain_scores": canonical_domain_scores,
        },
        anomaly_signals=anomaly_signals,
    )


def _score_result(
    domain_totals: dict[str, float] | None = None,
    *,
    canonical_domain_scores: dict[str, float] | None = None,
    severity: float = 45.0,
    confidence: float = 0.72,
    coverage_ratio: float = 0.8,
    primary_signal_domain: str | None = None,
) -> dict[str, object]:
    scorecard_json: dict[str, object] = {
        "coverage_ratio": coverage_ratio,
        "primary_signal_domain": primary_signal_domain,
        "model_code": "AWR_WEIGHTED_CORE",
        "model_version": "1.0.0",
        "decision_domain": "SIZING",
    }
    if domain_totals is not None:
        scorecard_json["domain_totals"] = domain_totals
    if canonical_domain_scores is not None:
        scorecard_json["canonical_domain_scores"] = canonical_domain_scores
    return {
        "severity_score": severity,
        "confidence": confidence,
        "primary_signal_domain": primary_signal_domain,
        "scorecard_json": scorecard_json,
    }


def _realistic_score_result_record(
    *,
    domain_totals: dict[str, float],
    total_score: float,
    confidence_score: float,
    severity_score: float | None = None,
    primary_signal_domain: str | None = None,
    risk_level: str = "LOW",
) -> dict[str, object]:
    severity_value = total_score if severity_score is None else severity_score
    explanation_payload = {
        "summary": (
            "Deterministic model AWR_WEIGHTED_CORE produced a total score "
            "of 26.90 with risk level LOW and confidence 63.67."
        ),
        "evidence": {
            "feature_coverage": 5,
            "feature_codes_used": [
                "CPU_UTIL_P95",
                "DB_TIME_PER_TXN",
                "READ_LATENCY_MS",
                "LOG_FILE_SYNC_MS",
                "TOP_SQL_LOAD_CONCENTRATION",
            ],
            "top_domains": [
                {"domain": "CPU", "score": 12.8372},
                {"domain": "LOAD", "score": 5.471},
                {"domain": "SQL", "score": 3.75},
                {"domain": "WAIT", "score": 0.72},
                {"domain": "IO", "score": 0.0862},
            ],
        },
    }
    contribution_payload = {
        "components": [
            {
                "feature_code": "CPU_UTIL_P95",
                "feature_name": "CPU Utilization P95",
                "feature_domain": "CPU",
                "raw_value": 64.186,
                "transformed_value": 64.186,
                "normalized_value": 0.64186,
                "weight_value": 0.2,
                "weighted_points": 12.8372,
                "feature_path": "$.CPU_UTIL_P95",
                "normalization_method": "MINMAX",
                "transform_method": "NONE",
                "polarity": "HIGH_BAD",
            },
            {
                "feature_code": "DB_TIME_PER_TXN",
                "feature_name": "DB Time Per Transaction",
                "feature_domain": "LOAD",
                "raw_value": 0.91,
                "transformed_value": 0.647103,
                "normalized_value": 0.273552,
                "weight_value": 0.2,
                "weighted_points": 5.47104,
                "feature_path": "$.DB_TIME_PER_TXN",
                "normalization_method": "ROBUST",
                "transform_method": "LOG1P",
                "polarity": "HIGH_BAD",
            },
            {
                "feature_code": "READ_LATENCY_MS",
                "feature_name": "Read Latency (ms)",
                "feature_domain": "IO",
                "raw_value": 0.23,
                "transformed_value": 0.23,
                "normalized_value": 0.00575,
                "weight_value": 0.15,
                "weighted_points": 0.08625,
                "feature_path": "$.READ_LATENCY_MS",
                "normalization_method": "MINMAX",
                "transform_method": "NONE",
                "polarity": "HIGH_BAD",
            },
            {
                "feature_code": "LOG_FILE_SYNC_MS",
                "feature_name": "Log File Sync (ms)",
                "feature_domain": "WAIT",
                "raw_value": 0.96,
                "transformed_value": 0.96,
                "normalized_value": 0.048,
                "weight_value": 0.15,
                "weighted_points": 0.72,
                "feature_path": "$.LOG_FILE_SYNC_MS",
                "normalization_method": "MINMAX",
                "transform_method": "NONE",
                "polarity": "HIGH_BAD",
            },
        ]
    }
    return {
        "awr_id": 42,
        "source_system_id": 42,
        "feature_vector_id": 42,
        "scoring_model_id": 1,
        "decision_domain": "SIZING",
        "risk_level": risk_level,
        "total_score": total_score,
        "confidence_score": confidence_score,
        "severity_score": severity_value,
        "urgency_score": total_score,
        "business_impact_score": 0.0,
        "workload_class": "CPU_BOUND",
        "topology_class": None,
        "platform_class": None,
        "event_class": None,
        "primary_signal_domain": primary_signal_domain,
        "explanation_json": json.dumps(explanation_payload),
        "contribution_json": json.dumps(contribution_payload),
        "scorecard_json": json.dumps(
            {
                "model_code": "AWR_WEIGHTED_CORE",
                "model_version": "1.0.0",
                "decision_domain": "SIZING",
                "domain_totals": domain_totals,
                "feature_vector_version": "3.0.0",
                "workload_class": "CPU_BOUND",
                "topology_class": None,
                "platform_class": None,
                "event_class": None,
                "primary_signal_domain": primary_signal_domain,
                "coverage_ratio": 0.8333,
            }
        ),
    }


def _anomaly(
    metric_name: str,
    anomaly_score: str = "MEDIUM",
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "metric_name": metric_name,
        "anomaly_flag": "Y",
        "anomaly_type": "SPIKE",
        "anomaly_score": anomaly_score,
        "metric_value_num": 1.0,
    }
    payload.update(extra)
    return payload


def _decision_diagnostics(decision: Any) -> dict[str, Any]:
    diagnostics = decision.evidence.get("decision_diagnostics")
    assert diagnostics is not None
    return cast(dict[str, Any], diagnostics)


def _decision_evidence(decision: Any) -> dict[str, Any]:
    evidence = decision.evidence
    assert evidence is not None
    return cast(dict[str, Any], evidence)


def _score_evidence(decision_input: DecisionInput) -> dict[str, Any]:
    score_evidence = decision_input.score_evidence
    assert score_evidence is not None
    return cast(dict[str, Any], score_evidence)


class DecisionEngineTests(unittest.TestCase):
    def test_single_dominant_issue(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 18.0, "IO": 4.0, "COMMIT": 3.0},
                severity=82.0,
                confidence=0.88,
                primary_signal_domain="CPU",
            )
        )

        self.assertEqual(decision.primary_issue, "CPU")
        self.assertEqual(decision.secondary_issues, [])
        self.assertEqual(decision.overall_status, "CRITICAL")

    def test_no_qualifying_primary_returns_none(self) -> None:
        decision = build_decision(
            _decision_input(
                {},
                severity=12.0,
                confidence=0.30,
                coverage_ratio=0.4,
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, [])
        self.assertEqual(decision.overall_status, "OK")

    def test_tie_resolution_uses_locked_domain_order(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 12.0, "IO": 12.0},
                severity=48.0,
                confidence=0.74,
            ),
            include_diagnostics=True,
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["CPU"])
        diagnostics = _decision_diagnostics(decision)
        self.assertFalse(diagnostics["tie_break_applied"])
        self.assertEqual(diagnostics["final_ranked_domains"][:2], ["CPU", "IO"])

    def test_multiple_secondary_issues_are_selected_generically(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 24.0, "MEMORY": 7.0, "COMMIT": 7.0},
                severity=56.0,
                confidence=0.79,
                primary_signal_domain="CPU",
            )
        )

        self.assertEqual(decision.primary_issue, "CPU")
        self.assertEqual(decision.secondary_issues, ["MEMORY", "COMMIT"])

    def test_diagnostics_structure_is_available_when_enabled(self) -> None:
        decision = build_decision(
            _decision_input(
                {"IO": 21.0, "COMMIT": 4.5},
                severity=41.0,
                confidence=0.67,
            ),
            include_diagnostics=True,
        )

        diagnostics = _decision_diagnostics(decision)
        self.assertEqual(set(diagnostics["domain_diagnostics"].keys()), set(DOMAIN_ORDER))
        self.assertIn("qualified_for_secondary", diagnostics["domain_diagnostics"]["IO"])
        self.assertIsInstance(diagnostics["ordered_candidates_pre_tiebreak"], list)
        self.assertEqual(diagnostics["final_ranked_domains"][0], decision.primary_issue)

    def test_primary_below_7_does_not_qualify(self) -> None:
        decision = build_decision(
            _decision_input(
                {"COMMIT": 6.9},
                severity=40.0,
                confidence=0.52,
                coverage_ratio=0.6,
                primary_signal_domain="COMMIT",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["COMMIT"])

    def test_primary_at_or_above_7_requires_severity_gate(self) -> None:
        decision = build_decision(
            _decision_input(
                {"IO": 7.0},
                severity=12.9,
                confidence=0.50,
                coverage_ratio=0.5,
                primary_signal_domain="IO",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["IO"])
        self.assertEqual(decision.overall_status, "OK")

    def test_primary_requires_material_total_support(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 15.0, "IO": 1.9},
                severity=18.0,
                confidence=0.62,
                coverage_ratio=0.6,
                primary_signal_domain="CPU",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["CPU"])

    def test_low_severity_primary_requires_concentrated_score_share(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 15.0, "IO": 5.0},
                severity=17.4,
                confidence=0.62,
                coverage_ratio=0.45,
                primary_signal_domain="CPU",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["CPU"])

    def test_low_severity_primary_can_still_qualify_when_highly_concentrated(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 15.0, "IO": 3.6},
                severity=16.2,
                confidence=0.62,
                coverage_ratio=0.45,
                primary_signal_domain="CPU",
                feature_evidence={
                    "db_time_per_sec": 4.0,
                    "db_time_per_txn": 0.03,
                },
            )
        )

        self.assertEqual(decision.primary_issue, "CPU")
        self.assertEqual(decision.secondary_issues, [])

    def test_secondary_above_floor_qualifies(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 18.0, "IO": 6.2},
                severity=45.0,
                confidence=0.68,
                coverage_ratio=0.7,
                primary_signal_domain="CPU",
            )
        )

        self.assertEqual(decision.primary_issue, "CPU")
        self.assertEqual(decision.secondary_issues, ["IO"])

    def test_secondary_only_at_or_above_3_5_qualifies(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 3.5},
                severity=18.0,
                confidence=0.42,
                coverage_ratio=0.4,
                primary_signal_domain="CPU",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["CPU"])

    def test_tie_break_applies_only_to_meaningful_qualifying_ties(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 18.0},
                severity=42.0,
                confidence=0.78,
                primary_signal_domain="CPU",
            ),
            include_diagnostics=True,
        )

        diagnostics = _decision_diagnostics(decision)
        self.assertFalse(diagnostics["tie_break_applied"])
        self.assertIsNone(diagnostics["tie_break_reason"])

    def test_ambiguous_primary_yields_top_secondary_only(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 15.0, "IO": 10.8},
                severity=24.9,
                confidence=0.73,
                primary_signal_domain="CPU",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["CPU"])

    def test_share_suppressed_no_primary_excludes_top_domain_from_secondaries(self) -> None:
        decision = build_decision(
            _decision_input(
                {"COMMIT": 15.0, "IO": 6.2, "CPU": 3.3},
                severity=18.0,
                confidence=0.66,
                primary_signal_domain="COMMIT",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["IO"])

    def test_tied_ambiguous_primary_uses_locked_order_for_secondary_orientation(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 15.0, "COMMIT": 15.0, "IO": 6.5},
                severity=35.0,
                confidence=0.68,
                primary_signal_domain="CPU",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["CPU"])

    def test_no_primary_secondary_only_candidates_are_capped(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 8.6, "COMMIT": 6.7, "IO": 4.6},
                severity=15.0,
                confidence=0.58,
                primary_signal_domain="CPU",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["CPU"])

    def test_activity_supported_primary_override_allows_supported_top_signal(self) -> None:
        decision = build_decision(
            _decision_input(
                {"IO": 7.3, "CPU": 6.7, "COMMIT": 2.9},
                severity=11.4,
                confidence=0.58,
                coverage_ratio=0.75,
                primary_signal_domain="IO",
                feature_evidence={
                    "db_time_per_sec": 8.7,
                    "db_time_per_txn": 0.06,
                },
            )
        )

        self.assertEqual(decision.primary_issue, "IO")
        self.assertEqual(decision.secondary_issues, ["CPU"])

    def test_low_activity_ambiguous_no_primary_excludes_top_candidate(self) -> None:
        decision = build_decision(
            _decision_input(
                {"COMMIT": 9.7, "CPU": 8.6, "IO": 4.4},
                severity=15.1,
                confidence=0.55,
                coverage_ratio=0.6,
                primary_signal_domain="COMMIT",
                feature_evidence={
                    "db_time_per_sec": 0.7,
                    "db_time_per_txn": 0.01,
                },
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["CPU", "IO"])

    def test_low_activity_diffuse_no_primary_prefers_single_follow_on_secondary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 8.2, "IO": 5.3, "COMMIT": 3.9},
                severity=11.8,
                confidence=0.56,
                coverage_ratio=0.6,
                primary_signal_domain="CPU",
                feature_evidence={
                    "db_time_per_sec": 2.2,
                    "db_time_per_txn": 0.02,
                },
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["IO"])

    def test_close_secondary_gap_is_allowed_under_primary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"MEMORY": 9.3, "IO": 8.9, "CPU": 4.9},
                severity=16.4,
                confidence=0.61,
                coverage_ratio=0.8,
                primary_signal_domain="MEMORY",
                feature_evidence={
                    "db_time_per_sec": 10.2,
                    "db_time_per_txn": 0.07,
                },
            )
        )

        self.assertEqual(decision.primary_issue, "MEMORY")
        self.assertEqual(decision.secondary_issues, ["IO"])

    def test_material_runner_up_primary_qualifier_can_surface_as_secondary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"MEMORY": 10.6, "IO": 8.9, "CPU": 4.9},
                severity=61.6,
                confidence=0.69,
                coverage_ratio=0.85,
                primary_signal_domain="MEMORY",
                feature_evidence={
                    "db_time_per_sec": 5.2,
                    "db_time_per_txn": 0.07,
                },
            )
        )

        self.assertEqual(decision.primary_issue, "MEMORY")
        self.assertIn("IO", decision.secondary_issues)

    def test_weak_runner_up_does_not_surface_as_secondary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"MEMORY": 12.0, "IO": 3.0, "CPU": 2.5},
                severity=44.0,
                confidence=0.69,
                coverage_ratio=0.8,
                primary_signal_domain="MEMORY",
            )
        )

        self.assertEqual(decision.primary_issue, "MEMORY")
        self.assertNotIn("IO", decision.secondary_issues)

    def test_material_runner_up_rule_is_generic_across_domains(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 11.0, "COMMIT": 8.0},
                severity=52.0,
                confidence=0.71,
                coverage_ratio=0.8,
                primary_signal_domain="CPU",
                feature_evidence={
                    "db_time_per_sec": 4.2,
                    "db_time_per_txn": 0.03,
                },
            )
        )

        self.assertEqual(decision.primary_issue, "CPU")
        self.assertIn("COMMIT", decision.secondary_issues)

    def test_material_runner_up_rule_preserves_no_primary_secondary_behavior(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 3.5},
                severity=18.0,
                confidence=0.42,
                coverage_ratio=0.4,
                primary_signal_domain="CPU",
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertEqual(decision.secondary_issues, ["CPU"])

    def test_topology_presence_without_rac_pressure_does_not_surface_rac(self) -> None:
        decision = build_decision(
            _decision_input(
                {"ADG": 14.0, "IO": 6.5, "RAC": 0.9, "CPU": 5.0},
                severity=16.0,
                confidence=0.7,
                coverage_ratio=0.75,
                feature_evidence={
                    "is_rac": 1.0,
                    "topology_class": "RAC",
                    "apply_lag_sec": 80.0,
                    "transport_lag_sec": 40.0,
                    "redo_transport_issue_flag": 1.0,
                    "read_latency_ms": 38.0,
                    "user_io_pressure": 12.0,
                    "db_time_per_sec": 2.1,
                    "db_time_per_txn": 0.02,
                },
            )
        )

        self.assertNotIn("RAC", decision.secondary_issues)

    def test_rac_with_pressure_evidence_can_surface_as_secondary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 13.0, "RAC": 5.2},
                severity=48.0,
                confidence=0.74,
                coverage_ratio=0.8,
                primary_signal_domain="CPU",
                feature_evidence={
                    "gc_cr_wait_pct_db_time": 4.5,
                    "gc_current_wait_pct_db_time": 3.8,
                    "cluster_wait_pct_db_time": 4.5,
                },
            )
        )

        self.assertEqual(decision.primary_issue, "CPU")
        self.assertIn("RAC", decision.secondary_issues)

    def test_severe_adg_case_remains_primary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"ADG": 22.0, "COMMIT": 7.0},
                severity=71.0,
                confidence=0.82,
                coverage_ratio=0.84,
                primary_signal_domain="ADG",
                feature_evidence={
                    "apply_lag_sec": 900.0,
                    "transport_lag_sec": 500.0,
                    "redo_transport_issue_flag": 1.0,
                },
            )
        )

        self.assertEqual(decision.primary_issue, "ADG")
        self.assertIn("COMMIT", decision.secondary_issues)

    def test_moderate_mixed_adg_case_does_not_force_adg_primary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"ADG": 14.5, "IO": 6.8, "CPU": 6.1, "COMMIT": 5.1, "MEMORY": 4.0},
                severity=29.0,
                confidence=0.79,
                coverage_ratio=0.85,
                feature_evidence={
                    "apply_lag_sec": 80.0,
                    "transport_lag_sec": 40.0,
                    "redo_transport_issue_flag": 1.0,
                    "read_latency_ms": 37.0,
                    "user_io_pressure": 15.0,
                    "cpu_util_p95": 31.0,
                    "db_cpu_pct_db_time": 31.0,
                    "log_file_sync_ms": 9.0,
                    "pga_spill_pressure": 0.12,
                    "temp_spill_pct": 12.0,
                    "db_time_per_sec": 11.0,
                    "db_time_per_txn": 0.04,
                },
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertIn("ADG", decision.secondary_issues)

    def test_sparse_topology_mixed_case_suppresses_cpu_baseline_secondary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"ADG": 14.4, "IO": 6.9, "CPU": 6.0, "RAC": 0.6},
                severity=15.5,
                confidence=0.76,
                coverage_ratio=0.8,
                feature_evidence={
                    "apply_lag_sec": 78.0,
                    "transport_lag_sec": 42.0,
                    "redo_transport_issue_flag": 1.0,
                    "read_latency_ms": 39.0,
                    "user_io_pressure": 13.0,
                    "cpu_util_p95": 30.0,
                    "db_cpu_pct_db_time": 30.0,
                    "cluster_wait_pct_db_time": 2.16,
                    "gc_cr_wait_pct_db_time": 2.16,
                    "db_time_per_sec": 2.3,
                    "db_time_per_txn": 0.02,
                },
            )
        )

        self.assertIsNone(decision.primary_issue)
        self.assertIn("ADG", decision.secondary_issues)
        self.assertIn("IO", decision.secondary_issues)
        self.assertNotIn("CPU", decision.secondary_issues)

    def test_adg_can_be_primary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"ADG": 18.0},
                severity=72.0,
                confidence=0.82,
                primary_signal_domain="ADG",
            )
        )

        self.assertEqual(decision.primary_issue, "ADG")
        self.assertEqual(decision.secondary_issues, [])
        self.assertIn("ADG", _decision_evidence(decision)["domain_scores"])

    def test_adg_can_be_secondary(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 18.0, "ADG": 7.0},
                severity=54.0,
                confidence=0.78,
                primary_signal_domain="CPU",
            )
        )

        self.assertEqual(decision.primary_issue, "CPU")
        self.assertIn("ADG", decision.secondary_issues)

    def test_adg_participates_in_tie_breaks(self) -> None:
        decision = build_decision(
            _decision_input(
                {"COMMIT": 4.0, "ADG": 4.0},
                severity=18.0,
                confidence=0.73,
            ),
            include_diagnostics=True,
        )

        diagnostics = _decision_diagnostics(decision)
        self.assertIsNone(decision.primary_issue)
        self.assertTrue(diagnostics["tie_break_applied"])
        self.assertIn("ADG", diagnostics["final_ranked_domains"])
        self.assertLess(
            diagnostics["final_ranked_domains"].index("COMMIT"),
            diagnostics["final_ranked_domains"].index("ADG"),
        )

    def test_adg_appears_in_diagnostics_and_evidence(self) -> None:
        decision = build_decision(
            _decision_input(
                {"ADG": 18.0},
                severity=61.0,
                confidence=0.77,
                primary_signal_domain="ADG",
            ),
            include_diagnostics=True,
        )

        evidence = _decision_evidence(decision)
        self.assertIn("ADG", evidence["domain_scores"])
        self.assertIn("canonical_domain_scores", evidence["score_evidence"])
        self.assertIn(
            "ADG",
            _decision_diagnostics(decision)["domain_diagnostics"],
        )

    def test_memory_can_be_selected_from_upstream_score_and_anomaly_support(self) -> None:
        decision = build_decision(
            _decision_input(
                {"MEMORY": 18.0, "IO": 7.0},
                severity=52.0,
                confidence=0.71,
                primary_signal_domain="MEMORY",
            )
        )

        self.assertEqual(decision.primary_issue, "MEMORY")
        self.assertIn("IO", decision.secondary_issues)

    def test_adapter_preserves_domain_totals_scale(self) -> None:
        decision_input = build_decision_input_from_score_result(
            awr_id=111,
            score_result=_score_result(
                {"CPU": 18.0, "LOAD": 6.0, "IO": 4.0, "DG": 2.0},
                severity=68.0,
                confidence=0.84,
                primary_signal_domain="CPU",
            ),
        )

        canonical_scores = decision_input.canonical_domain_scores
        score_evidence = _score_evidence(decision_input)
        self.assertEqual(canonical_scores["CPU"], 24.0)
        self.assertEqual(canonical_scores["IO"], 4.0)
        self.assertEqual(canonical_scores["ADG"], 2.0)
        self.assertEqual(
            score_evidence["canonical_domain_totals"]["CPU"],
            24.0,
        )

    def test_adapter_does_not_normalize_scores_to_sum_one(self) -> None:
        decision_input = build_decision_input_from_score_result(
            awr_id=112,
            score_result=_score_result(
                canonical_domain_scores={"CPU": 9.0, "IO": 3.0, "ADG": 2.0},
                severity=55.0,
                confidence=0.75,
                primary_signal_domain="CPU",
            ),
        )

        canonical_scores = decision_input.canonical_domain_scores
        self.assertEqual(canonical_scores["CPU"], 9.0)
        self.assertEqual(sum(canonical_scores.values()), 14.0)

    def test_adapter_characterizes_real_score_result_record_shape(self) -> None:
        decision_input = build_decision_input_from_score_result(
            awr_id=113,
            score_result=_realistic_score_result_record(
                domain_totals={
                    "CPU": 12.8372,
                    "LOAD": 5.471,
                    "SQL": 3.75,
                    "WAIT": 0.72,
                    "IO": 0.0862,
                },
                total_score=26.9,
                confidence_score=63.67,
                primary_signal_domain="CPU",
            ),
        )

        self.assertEqual(decision_input.severity_input, 26.9)
        self.assertAlmostEqual(decision_input.confidence_input or 0.0, 0.6367, places=4)
        self.assertEqual(decision_input.completeness, 0.8333)
        self.assertEqual(decision_input.primary_signal_domain, "CPU")
        canonical_scores = decision_input.canonical_domain_scores
        score_evidence = _score_evidence(decision_input)
        self.assertEqual(canonical_scores["CPU"], 22.0582)
        self.assertEqual(canonical_scores["COMMIT"], 0.72)
        self.assertEqual(canonical_scores["IO"], 0.0862)
        self.assertEqual(
            score_evidence["raw_domain_totals"]["WAIT"],
            0.72,
        )

    def test_wait_domain_maps_to_commit_for_current_core_model_shape(self) -> None:
        decision_input = build_decision_input_from_score_result(
            awr_id=114,
            score_result=_realistic_score_result_record(
                domain_totals={"WAIT": 4.5},
                total_score=15.0,
                confidence_score=55.0,
                primary_signal_domain="WAIT",
            ),
        )

        self.assertEqual(decision_input.canonical_domain_scores["COMMIT"], 4.5)
        self.assertEqual(decision_input.primary_signal_domain, "COMMIT")

    def test_anomalies_without_explicit_delta_do_not_change_domain_scores(self) -> None:
        decision = build_decision(
            _decision_input(
                {"CPU": 15.0},
                severity=52.0,
                confidence=0.71,
                primary_signal_domain="CPU",
            ),
            include_diagnostics=True,
        )
        baseline_score = _decision_evidence(decision)["domain_scores"]["CPU"]

        decision_with_anomaly = build_decision(
            _decision_input_with_anomalies(
                {"CPU": 15.0},
                [_anomaly("CPU_UTIL_P95", "HIGH")],
                severity=52.0,
                confidence=0.71,
                primary_signal_domain="CPU",
            ),
            include_diagnostics=True,
        )

        self.assertEqual(
            _decision_evidence(decision_with_anomaly)["domain_scores"]["CPU"],
            baseline_score,
        )
        self.assertEqual(len(_decision_evidence(decision_with_anomaly)["anomaly_signals"]), 1)

    def test_explicit_anomaly_delta_adjusts_score_generically(self) -> None:
        decision = build_decision(
            _decision_input_with_anomalies(
                {"CPU": 15.0},
                [_anomaly("CPU_UTIL_P95", "HIGH", domain_score_delta=2.0)],
                severity=52.0,
                confidence=0.71,
                primary_signal_domain="CPU",
            )
        )

        self.assertEqual(_decision_evidence(decision)["domain_scores"]["CPU"], 17.0)


if __name__ == "__main__":
    unittest.main()
