from __future__ import annotations

import importlib
import unittest


def eligibility_module():
    return importlib.import_module(
        "src.reporting.dashboard.screen4.comparative_visual_eligibility"
    )


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class Screen4ComparativeVisualEligibilityTests(unittest.TestCase):
    def valid_contract(self, allowed: list[str] | None = None, **overrides):
        payload = {
            "screen4_contract_type": "deterministic_comparison_output",
            "contract_version": "7cx.screen4.comparison.v1",
            "adapter_version": "7cx-adapter-v1",
            "comparison_id": "VIS-7CX-G",
            "baseline_run_id": "RUN-A",
            "candidate_run_id": "RUN-B",
            "target_a_identity": {"run_id": "RUN-A"},
            "target_b_identity": {"run_id": "RUN-B"},
            "target_alignment": {"status": "aligned", "basis": ["run ids aligned"]},
            "source_scope": "same_db_historical",
            "comparison_scope": "target_a_vs_target_b",
            "generated_by": "deterministic_engine",
            "generated_at": "2026-06-05T12:00:00Z",
            "deterministic_engine_version": "phase7-am-comparison-v1",
            "metric_deltas": [
                {"metric": "cpu", "baseline_value": 70, "candidate_value": 58}
            ],
            "domain_deltas": [],
            "evidence_rows": [
                {"category": "score", "metric": "cpu", "delta": -12}
            ],
            "confidence_basis": {
                "basis_type": "deterministic_evidence",
                "sample_count": 2,
                "limitations": [],
            },
            "missing_evidence": [],
            "allowed_visualizations": list(allowed or []),
            "validation_status": "valid",
            "adapter_validation_messages": [],
        }
        payload.update(overrides)
        return payload

    def evaluate(self, contract, visualization):
        module = eligibility_module()
        return module.evaluate_screen4_comparative_visual_eligibility(
            contract,
            visualization,
        )

    def test_prepared_only_and_cache_only_inputs_produce_no_eligible_visuals(self) -> None:
        module = eligibility_module()

        for payload in (
            {"comparison_prepared_context": {"target_a": {"run_id": "RUN-A"}}},
            {
                "comparison_cache_status": "cached_continuity_only",
                "comparison_artifact_reference": "comparison:cached-only",
                "allowed_visualizations": ["time_series_overlay"],
            },
        ):
            with self.subTest(payload=payload):
                result = module.evaluate_screen4_comparative_visual_eligibility(
                    payload,
                    "time_series_overlay",
                )
                self.assertFalse(result.rendering_allowed)
                self.assertEqual("blocked", result.status)
                self.assertEqual("deterministic_contract_invalid", result.reason_code)

    def test_llm_text_cannot_produce_visual_eligibility(self) -> None:
        result = self.evaluate(
            {
                **self.valid_contract(["time_series_overlay"]),
                "generated_by": "llm",
                "evidence_rows": [
                    {
                        "visualization": "time_series_overlay",
                        "llm_explanation": "This is a chart-worthy trend.",
                    }
                ],
            },
            "time_series_overlay",
        )

        self.assertFalse(result.rendering_allowed)
        self.assertEqual("deterministic_contract_invalid", result.reason_code)

    def test_eligibility_results_emit_no_chart_markup(self) -> None:
        result = self.evaluate(
            self.valid_contract(["distribution_violin"]),
            "distribution_violin",
        )
        text = str(result.to_dict()).lower()

        for forbidden in ("<canvas", "<svg", "chart-container", "violin-container"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_fleet_visual_is_not_supported_without_fleet_contract(self) -> None:
        result = self.evaluate(
            self.valid_contract(["fleet_population_diagram"]),
            "fleet_population_diagram",
        )

        self.assertEqual("not_supported", result.status)
        self.assertFalse(result.rendering_allowed)
        self.assertEqual("fleet_evidence_contract_missing", result.reason_code)

    def test_time_series_overlay_not_requested_when_not_allowed(self) -> None:
        result = self.evaluate(self.valid_contract([]), "time_series_overlay")

        self.assertEqual("not_requested", result.status)
        self.assertFalse(result.rendering_allowed)
        self.assertEqual("allowed_visualization_missing", result.reason_code)

    def test_time_series_overlay_blocked_when_allowed_but_rows_missing(self) -> None:
        result = self.evaluate(
            self.valid_contract(["time_series_overlay"]),
            "time_series_overlay",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("aligned_time_series_rows_missing", result.reason_code)

    def test_time_series_overlay_blocked_from_metric_deltas_alone(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["time_series_overlay"],
                metric_deltas=[
                    {
                        "metric": "cpu",
                        "baseline_value": 70,
                        "candidate_value": 58,
                        "delta": -12,
                    }
                ],
            ),
            "time_series_overlay",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("aligned_time_series_rows_missing", result.reason_code)

    def test_time_series_overlay_ignores_top_level_rows_without_evidence_shape(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["time_series_overlay"],
                time_series_rows=[
                    {
                        "timestamp": "2026-06-05T12:00:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 70,
                        "target_b_value": 58,
                    },
                    {
                        "timestamp": "2026-06-05T12:05:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 71,
                        "target_b_value": 59,
                    },
                ],
            ),
            "time_series_overlay",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("aligned_time_series_rows_missing", result.reason_code)

    def test_time_series_overlay_blocked_with_one_aligned_point(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["time_series_overlay"],
                evidence_rows=[
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:00:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 70,
                        "target_b_value": 58,
                    }
                ],
            ),
            "time_series_overlay",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("insufficient_time_series_points", result.reason_code)

    def test_time_series_overlay_blocks_missing_metric_identity_and_timestamp(self) -> None:
        missing_metric = self.evaluate(
            self.valid_contract(
                ["time_series_overlay"],
                evidence_rows=[
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:00:00Z",
                        "target_a_value": 70,
                        "target_b_value": 58,
                    },
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:05:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 71,
                        "target_b_value": 59,
                    },
                ],
            ),
            "time_series_overlay",
        )
        self.assertEqual("missing_metric_identity", missing_metric.reason_code)

        missing_timestamp = self.evaluate(
            self.valid_contract(
                ["time_series_overlay"],
                evidence_rows=[
                    {
                        "visualization": "time_series_overlay",
                        "metric_key": "cpu",
                        "target_a_value": 70,
                        "target_b_value": 58,
                    },
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:05:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 71,
                        "target_b_value": 59,
                    },
                ],
            ),
            "time_series_overlay",
        )
        self.assertEqual("missing_timestamp", missing_timestamp.reason_code)

    def test_time_series_overlay_blocked_when_target_b_value_missing(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["time_series_overlay"],
                evidence_rows=[
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:00:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 70,
                    },
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:05:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 71,
                        "target_b_value": 59,
                    },
                ],
            ),
            "time_series_overlay",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("missing_target_b_value", result.reason_code)

    def test_time_series_overlay_blocked_when_values_are_non_numeric(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["time_series_overlay"],
                evidence_rows=[
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:00:00Z",
                        "metric_key": "cpu",
                        "target_a_value": "70",
                        "target_b_value": 58,
                    },
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:05:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 71,
                        "target_b_value": 59,
                    },
                ],
            ),
            "time_series_overlay",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("non_numeric_time_series_value", result.reason_code)

    def test_time_series_overlay_eligible_with_two_aligned_numeric_points(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["time_series_overlay"],
                evidence_rows=[
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:00:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 70,
                        "target_b_value": 58,
                    },
                    {
                        "visualization": "time_series_overlay",
                        "timestamp": "2026-06-05T12:05:00Z",
                        "metric_key": "cpu",
                        "target_a_value": 71,
                        "target_b_value": 59,
                    },
                ],
            ),
            "time_series_overlay",
        )

        self.assertEqual("eligible", result.status)
        self.assertTrue(result.rendering_allowed)
        self.assertEqual(2, result.evidence_count)

    def test_distribution_violin_not_requested_when_not_allowed(self) -> None:
        result = self.evaluate(self.valid_contract([]), "distribution_violin")

        self.assertEqual("not_requested", result.status)
        self.assertFalse(result.rendering_allowed)

    def test_distribution_violin_blocked_when_allowed_but_samples_missing(self) -> None:
        result = self.evaluate(
            self.valid_contract(["distribution_violin"]),
            "distribution_violin",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("distribution_samples_missing", result.reason_code)
        self.assertEqual("Distribution Evidence", result.visualization_label)
        self.assertIn("Distribution evidence is blocked", result.reason)

    def test_distribution_violin_blocked_from_summary_deltas(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["distribution_violin"],
                metric_deltas=[
                    {
                        "metric": "cpu",
                        "baseline_value": 70,
                        "candidate_value": 58,
                        "delta": -12,
                    }
                ],
            ),
            "distribution_violin",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("distribution_samples_missing", result.reason_code)

    def test_visuals_block_from_domain_deltas_alone(self) -> None:
        for visualization, reason_code in (
            ("time_series_overlay", "aligned_time_series_rows_missing"),
            ("distribution_violin", "distribution_samples_missing"),
        ):
            with self.subTest(visualization=visualization):
                result = self.evaluate(
                    self.valid_contract(
                        [visualization],
                        domain_deltas=[
                            {
                                "domain": "CPU",
                                "evidence_count": 2,
                                "difference_rows": 1,
                            }
                        ],
                    ),
                    visualization,
                )

                self.assertEqual("blocked", result.status)
                self.assertEqual(reason_code, result.reason_code)

    def test_distribution_violin_ignores_top_level_rows_without_evidence_shape(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["distribution_violin"],
                distribution_rows=[
                    {
                        "visualization": "distribution_violin",
                        "metric_key": "cpu",
                        "target_a_samples": [70, 71, 72],
                        "target_b_samples": [58, 59, 60],
                    }
                ],
            ),
            "distribution_violin",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("distribution_samples_missing", result.reason_code)

    def test_distribution_violin_blocked_from_min_max_only_rows(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["distribution_violin"],
                evidence_rows=[
                    {
                        "visualization": "distribution_violin",
                        "metric_key": "cpu",
                        "target_a_min": 70,
                        "target_a_max": 72,
                        "target_b_min": 58,
                        "target_b_max": 60,
                    }
                ],
            ),
            "distribution_violin",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("distribution_samples_missing", result.reason_code)
        self.assertIn("min/max", result.reason)

    def test_distribution_violin_blocked_with_one_sample_per_target(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["distribution_violin"],
                evidence_rows=[
                    {
                        "visualization": "distribution_violin",
                        "metric_key": "cpu",
                        "target_a_samples": [70],
                        "target_b_samples": [58],
                    }
                ],
            ),
            "distribution_violin",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("insufficient_distribution_samples", result.reason_code)

    def test_distribution_violin_blocked_when_target_b_samples_missing(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["distribution_violin"],
                evidence_rows=[
                    {
                        "visualization": "distribution_violin",
                        "metric_key": "cpu",
                        "target_a_samples": [70, 71, 72],
                    }
                ],
            ),
            "distribution_violin",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("target_b_samples_missing", result.reason_code)

    def test_distribution_violin_blocked_when_samples_are_non_numeric(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["distribution_violin"],
                evidence_rows=[
                    {
                        "visualization": "distribution_violin",
                        "metric_key": "cpu",
                        "target_a_samples": [70, "bad", 72],
                        "target_b_samples": [58, 59, 60],
                    }
                ],
            ),
            "distribution_violin",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("non_numeric_distribution_sample", result.reason_code)

    def test_distribution_violin_eligible_with_real_numeric_sample_arrays(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["distribution_violin"],
                evidence_rows=[
                    {
                        "visualization": "distribution_violin",
                        "metric_key": "cpu",
                        "metric_label": "CPU",
                        "target_a_samples": [70, 71, 72],
                        "target_b_samples": [58, 59, 60],
                        "unit": "score",
                    }
                ],
            ),
            "distribution_violin",
        )

        self.assertEqual("eligible", result.status)
        self.assertTrue(result.rendering_allowed)
        self.assertEqual(3, result.evidence_count)
        self.assertEqual("Distribution Evidence", result.visualization_label)
        self.assertIn("Distribution evidence has numeric", result.reason)

    def test_distribution_violin_accepts_separate_target_rows_only_with_both_sides(self) -> None:
        missing_b = self.evaluate(
            self.valid_contract(
                ["distribution_violin"],
                evidence_rows=[
                    {
                        "visualization": "distribution_violin",
                        "metric_key": "cpu",
                        "target": "A",
                        "samples": [70, 71, 72],
                    }
                ],
            ),
            "distribution_violin",
        )
        self.assertEqual("blocked", missing_b.status)
        self.assertEqual("target_b_samples_missing", missing_b.reason_code)

        eligible = self.evaluate(
            self.valid_contract(
                ["distribution_violin"],
                evidence_rows=[
                    {
                        "visualization": "distribution_violin",
                        "metric_key": "cpu",
                        "target": "A",
                        "samples": [70, 71, 72],
                    },
                    {
                        "visualization": "distribution_violin",
                        "metric_key": "cpu",
                        "target": "B",
                        "samples": [58, 59, 60],
                    },
                ],
            ),
            "distribution_violin",
        )
        self.assertEqual("eligible", eligible.status)
        self.assertTrue(eligible.rendering_allowed)

    def test_top_sql_movement_blocked_without_persistent_sql_identity(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["top_sql_movement_table"],
                evidence_rows=[
                    {
                        "category": "sql",
                        "sql_text": "select * from orders",
                        "target_a_value": 10,
                        "target_b_value": 20,
                    }
                ],
            ),
            "top_sql_movement_table",
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual("stable_sql_identity_missing", result.reason_code)

    def test_top_sql_movement_eligible_with_persistent_sql_identity(self) -> None:
        result = self.evaluate(
            self.valid_contract(
                ["top_sql_movement_table"],
                evidence_rows=[
                    {
                        "category": "sql",
                        "sql_id": "8abc123",
                        "target_a_value": 10,
                        "target_b_value": 20,
                    }
                ],
            ),
            "top_sql_movement_table",
        )

        self.assertEqual("eligible", result.status)
        self.assertTrue(result.rendering_allowed)

    def test_wait_and_event_movement_require_persistent_event_identity(self) -> None:
        for visualization in ("wait_class_movement_table", "top_event_movement_table"):
            with self.subTest(visualization=visualization):
                blocked = self.evaluate(
                    self.valid_contract(
                        [visualization],
                        evidence_rows=[
                            {
                                "category": "wait",
                                "label": "db file sequential read",
                                "target_a_value": 10,
                                "target_b_value": 20,
                            }
                        ],
                    ),
                    visualization,
                )
                self.assertEqual("blocked", blocked.status)
                self.assertEqual("stable_event_identity_missing", blocked.reason_code)

                eligible = self.evaluate(
                    self.valid_contract(
                        [visualization],
                        evidence_rows=[
                            {
                                "category": "wait",
                                "event_id": "db-file-sequential-read",
                                "target_a_value": 10,
                                "target_b_value": 20,
                            }
                        ],
                    ),
                    visualization,
                )
                self.assertEqual("eligible", eligible.status)
                self.assertTrue(eligible.rendering_allowed)

    def test_adapter_style_contract_without_visual_evidence_has_no_eligible_visuals(self) -> None:
        module = eligibility_module()
        results = module.build_screen4_comparative_visual_eligibility(
            self.valid_contract(["metric_delta_table", "domain_delta_summary"]),
            include_not_requested=False,
        )

        self.assertEqual([], results)

    def test_visual_ready_fixture_marks_eligible_and_dashboard_renders_visual(self) -> None:
        dashboard = dashboard_module()
        contract = self.valid_contract(
            ["metric_delta_table", "time_series_overlay"],
            evidence_rows=[
                {
                    "visualization": "time_series_overlay",
                    "timestamp": "2026-06-05T12:00:00Z",
                    "metric_key": "cpu",
                    "target_a_value": 70,
                    "target_b_value": 58,
                },
                {
                    "visualization": "time_series_overlay",
                    "timestamp": "2026-06-05T12:05:00Z",
                    "metric_key": "cpu",
                    "target_a_value": 71,
                    "target_b_value": 59,
                },
            ],
        )
        result = self.evaluate(contract, "time_series_overlay")
        self.assertEqual("eligible", result.status)

        state = dashboard._screen4_build_comparative_review_state(
            {"deterministic_comparison_output": contract}
        )
        html = dashboard._render_screen4_comparative_review_panel(state)

        self.assertIn("Time-series Overlay", html)
        self.assertIn("Eligible for future rendering", html)
        self.assertIn("screen4-comparative-time-series-evidence", html)
        self.assertIn("<svg", html)
        self.assertNotIn("<canvas", html)
        self.assertNotIn("screen4-comparative-time-series-overlay", html)

    def test_text_panel_omits_not_requested_future_visuals_and_synthetic_wording(self) -> None:
        dashboard = dashboard_module()
        contract = self.valid_contract(["metric_delta_table"])
        state = dashboard._screen4_build_comparative_review_state(
            {"deterministic_comparison_output": contract}
        )
        html = dashboard._render_screen4_comparative_review_panel(state)
        fragment_start = html.index("screen4-comparative-visualization-eligibility")
        fragment_end = html.index("</section>", fragment_start)
        fragment = html[fragment_start:fragment_end].lower()

        self.assertNotIn("time-series overlay", fragment)
        self.assertNotIn("distribution / violin evidence", fragment)
        self.assertNotIn("not requested", fragment)
        self.assertNotIn("coming soon", fragment)
        self.assertNotIn("synthetic", fragment)


if __name__ == "__main__":
    unittest.main()
