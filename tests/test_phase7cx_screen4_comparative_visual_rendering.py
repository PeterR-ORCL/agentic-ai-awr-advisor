from __future__ import annotations

import importlib
import unittest


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class Screen4ComparativeVisualRenderingTests(unittest.TestCase):
    def valid_contract(self, allowed: list[str] | None = None, **overrides):
        payload = {
            "screen4_contract_type": "deterministic_comparison_output",
            "contract_version": "7cx.screen4.comparison.v1",
            "adapter_version": "7cx-adapter-v1",
            "comparison_id": "VISUAL-7CX-H",
            "baseline_run_id": "RUN-H-A",
            "candidate_run_id": "RUN-H-B",
            "target_a_identity": {"run_id": "RUN-H-A", "db_name": "FINDB"},
            "target_b_identity": {"run_id": "RUN-H-B", "db_name": "FINDB"},
            "target_alignment": {"status": "aligned", "basis": ["run ids aligned"]},
            "source_scope": "same_db_historical",
            "comparison_scope": "target_a_vs_target_b",
            "generated_by": "deterministic_engine",
            "generated_at": "2026-06-05T12:00:00Z",
            "deterministic_engine_version": "phase7-am-comparison-v1",
            "metric_deltas": [],
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

    def render_contract(self, contract: dict[str, object]) -> str:
        dashboard = dashboard_module()
        state = dashboard._screen4_build_comparative_review_state(
            {"deterministic_comparison_output": contract}
        )
        return dashboard._render_screen4_comparative_review_panel(state)

    def time_series_rows(self) -> list[dict[str, object]]:
        return [
            {
                "visualization": "time_series_overlay",
                "timestamp": "2026-06-05T12:00:00Z",
                "metric_key": "cpu",
                "metric_label": "CPU",
                "target_a_value": 70,
                "target_b_value": 58,
                "unit": "score",
                "alignment_basis": "snapshot boundary",
            },
            {
                "visualization": "time_series_overlay",
                "timestamp": "2026-06-05T12:05:00Z",
                "metric_key": "cpu",
                "metric_label": "CPU",
                "target_a_value": 71,
                "target_b_value": 59,
                "unit": "score",
                "alignment_basis": "snapshot boundary",
            },
        ]

    def distribution_rows(self) -> list[dict[str, object]]:
        return [
            {
                "visualization": "distribution_violin",
                "metric_key": "cpu",
                "metric_label": "CPU",
                "target_a_samples": [70, 71, 72],
                "target_b_samples": [58, 59, 60],
                "unit": "score",
            }
        ]

    def assert_no_visuals(self, html: str) -> None:
        self.assertNotIn("screen4-comparative-visuals", html)
        self.assertNotIn("screen4-comparative-time-series-evidence", html)
        self.assertNotIn("screen4-comparative-distribution-evidence", html)
        self.assertNotIn("<svg", html)
        self.assertNotIn("<canvas", html)

    def test_prepared_only_and_cache_only_states_render_no_visuals(self) -> None:
        dashboard = dashboard_module()
        for screen_model in (
            {
                "comparison_prepared_context": {
                    "target_a": {"label": "AWR A", "run_id": "RUN-H-A"},
                    "target_b": {"label": "AWR B", "run_id": "RUN-H-B"},
                }
            },
            {
                "comparison_cache_status": "cached_continuity_only",
                "comparison_artifact_reference": "comparison:cached-only",
            },
        ):
            with self.subTest(screen_model=screen_model):
                state = dashboard._screen4_build_comparative_review_state(screen_model)
                html = dashboard._render_screen4_comparative_review_panel(state)
                self.assertNotEqual("comparison_output_ready", state["state"])
                self.assert_no_visuals(html)

    def test_output_ready_without_visual_evidence_renders_no_visuals(self) -> None:
        html = self.render_contract(
            self.valid_contract(["metric_delta_table", "domain_delta_summary"])
        )

        self.assert_no_visuals(html)

    def test_allowed_visualization_and_eligible_status_are_required(self) -> None:
        evidence_rows = self.time_series_rows()
        omitted_permission = self.render_contract(
            self.valid_contract([], evidence_rows=evidence_rows)
        )
        self.assert_no_visuals(omitted_permission)

        one_point = self.render_contract(
            self.valid_contract(
                ["time_series_overlay"],
                evidence_rows=evidence_rows[:1],
            )
        )
        self.assert_no_visuals(one_point)
        self.assertIn("at least two aligned points", one_point.lower())

    def test_no_visuals_from_non_visual_sources(self) -> None:
        cases = [
            self.valid_contract(
                ["time_series_overlay"],
                metric_deltas=[
                    {"metric": "cpu", "baseline_value": 70, "candidate_value": 58}
                ],
            ),
            self.valid_contract(
                ["time_series_overlay"],
                domain_deltas=[{"domain": "CPU", "evidence_count": 2}],
            ),
            self.valid_contract(
                ["distribution_violin"],
                metric_deltas=[
                    {"metric": "cpu", "baseline_value": 70, "candidate_value": 58}
                ],
            ),
            self.valid_contract(
                ["time_series_overlay"],
                time_series_rows=self.time_series_rows(),
            ),
            self.valid_contract(
                ["distribution_violin"],
                distribution_rows=self.distribution_rows(),
            ),
            self.valid_contract(
                ["time_series_overlay"],
                visual_evidence={"time_series_overlay": self.time_series_rows()},
            ),
            self.valid_contract(
                ["time_series_overlay"],
                evidence_rows=[
                    {
                        "visualization": "time_series_overlay",
                        "llm_explanation": "draw a useful chart",
                    }
                ],
            ),
        ]
        for contract in cases:
            with self.subTest(contract=contract):
                html = self.render_contract(contract)
                self.assert_no_visuals(html)

    def test_time_series_visual_blocks_malformed_visual_rows(self) -> None:
        cases = [
            [
                {
                    "visualization": "time_series_overlay",
                    "timestamp": "2026-06-05T12:00:00Z",
                    "metric_key": "cpu",
                    "target_a_value": 70,
                },
                self.time_series_rows()[1],
            ],
            [
                {
                    "visualization": "time_series_overlay",
                    "timestamp": "2026-06-05T12:00:00Z",
                    "metric_key": "cpu",
                    "target_a_value": "70",
                    "target_b_value": 58,
                },
                self.time_series_rows()[1],
            ],
        ]
        for evidence_rows in cases:
            with self.subTest(evidence_rows=evidence_rows):
                html = self.render_contract(
                    self.valid_contract(
                        ["time_series_overlay"],
                        evidence_rows=evidence_rows,
                    )
                )
                self.assert_no_visuals(html)

    def test_time_series_visual_renders_from_aligned_evidence_rows(self) -> None:
        html = self.render_contract(
            self.valid_contract(
                ["time_series_overlay"],
                evidence_rows=self.time_series_rows(),
            )
        )

        self.assertIn("screen4-comparative-visuals", html)
        self.assertIn("screen4-comparative-time-series-evidence", html)
        self.assertIn("screen4-comparative-time-series-svg", html)
        self.assertIn("Time-Series Evidence", html)
        self.assertIn(
            'aria-labelledby="screen4-time-series-title screen4-time-series-desc"',
            html,
        )
        self.assertIn(
            '<title id="screen4-time-series-title">Time-Series Evidence for CPU</title>',
            html,
        )
        self.assertIn('<desc id="screen4-time-series-desc">', html)
        self.assertIn("Target B (dashed)", html)
        self.assertIn('stroke-dasharray="6 4"', html)
        self.assertIn("2026-06-05T12:00:00Z", html)
        self.assertIn("2026-06-05T12:05:00Z", html)
        self.assertIn("70", html)
        self.assertIn("59", html)
        self.assertNotIn("screen4-comparative-distribution-evidence", html)
        self.assertNotIn("<canvas", html)

    def test_distribution_visual_blocks_invalid_distribution_sources(self) -> None:
        cases = [
            [
                {
                    "visualization": "distribution_violin",
                    "metric_key": "cpu",
                    "target_a_min": 70,
                    "target_a_max": 72,
                    "target_b_min": 58,
                    "target_b_max": 60,
                }
            ],
            [
                {
                    "visualization": "distribution_violin",
                    "metric_key": "cpu",
                    "target_a_samples": [70],
                    "target_b_samples": [58],
                }
            ],
            [
                {
                    "visualization": "distribution_violin",
                    "metric_key": "cpu",
                    "target_a_samples": [70, 71, 72],
                }
            ],
            [
                {
                    "visualization": "distribution_violin",
                    "metric_key": "cpu",
                    "target_a_samples": [70, "bad", 72],
                    "target_b_samples": [58, 59, 60],
                }
            ],
        ]
        for evidence_rows in cases:
            with self.subTest(evidence_rows=evidence_rows):
                html = self.render_contract(
                    self.valid_contract(
                        ["distribution_violin"],
                        evidence_rows=evidence_rows,
                    )
                )
                self.assert_no_visuals(html)

    def test_distribution_visual_renders_conservative_sample_plot(self) -> None:
        html = self.render_contract(
            self.valid_contract(
                ["distribution_violin"],
                evidence_rows=self.distribution_rows(),
            )
        )

        self.assertIn("screen4-comparative-visuals", html)
        self.assertIn("screen4-comparative-distribution-evidence", html)
        self.assertIn("screen4-comparative-distribution-svg", html)
        self.assertIn("Distribution Evidence", html)
        self.assertIn(
            'aria-labelledby="screen4-distribution-title screen4-distribution-desc"',
            html,
        )
        self.assertIn(
            '<title id="screen4-distribution-title">Distribution Evidence for CPU</title>',
            html,
        )
        self.assertIn('<desc id="screen4-distribution-desc">', html)
        self.assertIn("sample plot", html)
        self.assertIn("Sample Count", html)
        self.assertIn("70, 71, 72", html)
        self.assertIn("58, 59, 60", html)
        self.assertNotIn("screen4-comparative-time-series-evidence", html)
        self.assertIn("No density curve is estimated.", html)
        self.assertNotIn("Distribution / Violin Evidence", html)
        self.assertNotIn(">Violin<", html)
        self.assertNotIn("<canvas", html)

    def test_distribution_visual_accepts_separate_target_sample_rows(self) -> None:
        html = self.render_contract(
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
            )
        )

        self.assertIn("screen4-comparative-distribution-evidence", html)
        self.assertIn("70, 71, 72", html)
        self.assertIn("58, 59, 60", html)

    def test_visual_ready_fixture_renders_only_eligible_visual_types(self) -> None:
        html = self.render_contract(
            self.valid_contract(
                ["time_series_overlay", "distribution_violin"],
                evidence_rows=self.time_series_rows(),
            )
        )

        self.assertIn("screen4-comparative-time-series-evidence", html)
        self.assertNotIn("screen4-comparative-distribution-evidence", html)

    def test_no_placeholder_or_unsupported_conclusion_wording(self) -> None:
        html = self.render_contract(
            self.valid_contract(
                ["time_series_overlay", "distribution_violin"],
                evidence_rows=self.time_series_rows() + self.distribution_rows(),
            )
        ).lower()

        self.assertIn("screen4-comparative-time-series-evidence", html)
        self.assertIn("screen4-comparative-distribution-evidence", html)
        for forbidden in (
            "placeholder",
            "coming soon",
            "fake",
            "synthetic",
            "improved",
            "degraded",
            "stable",
            "better",
            "worse",
            "winner",
            "loser",
            "regression",
            "improvement",
            "empty chart",
            "chart-container",
            "violin-container",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, html)


if __name__ == "__main__":
    unittest.main()
