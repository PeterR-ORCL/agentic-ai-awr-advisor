from __future__ import annotations

import ast
import importlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardScreen4HistoricalReviewPanelTests(unittest.TestCase):
    def test_dashboard_source_compiles(self) -> None:
        ast.parse(read_text(HTML_DASHBOARD_PATH), filename=str(HTML_DASHBOARD_PATH))
        dashboard = dashboard_module()

        self.assertTrue(
            hasattr(dashboard, "_render_screen4_historical_review_preview_panel")
        )
        self.assertTrue(
            hasattr(dashboard, "_build_screen4_historical_review_preview_model")
        )

    def test_screen4_historical_review_panel_exists(self) -> None:
        rendered = self.render_screen4()

        required = (
            "Screen 4 Historical Review / Learning Preview",
            "Approve Trend",
            "Dispute Trend",
            "Mark Trend Insufficient",
            "Approve Anomaly",
            "Mark Anomaly False Positive",
            "Mark Anomaly Insufficient",
            "Request Trend-Aware Scoring Review",
            "Request Anomaly Sensitivity Review",
            "Request Scoring Threshold Review",
            "Request Learning Candidate",
            "Add Historical Review Note",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_controls_are_disabled_preview_only(self) -> None:
        rendered = self.render_screen4()

        self.assertIn('data-preview-only="true"', rendered)
        self.assertIn('aria-disabled="true"', rendered)
        self.assertIn("disabled-preview-only", rendered)
        self.assertIn("Disabled preview only", rendered)

        forbidden_controls = (
            "<button",
            "<form",
            "method=\"post\"",
            "type=\"submit\"",
            "onclick=",
            "data-action=",
            "role=\"button\"",
            "approval-control",
            "write-control",
            "learning-approval-control",
            "apply-control",
        )
        lowered = rendered.lower()
        for control in forbidden_controls:
            with self.subTest(control=control):
                self.assertNotIn(control, lowered)

    def test_safety_labels_exist(self) -> None:
        rendered = self.render_screen4()

        safety_labels = (
            "Preview only",
            "Historical review disabled in this phase",
            "No trend truth mutation",
            "No anomaly truth mutation",
            "No scoring change",
            "No candidate created automatically",
            "No governed write path invoked",
            "No Phase 4I mutation",
            "Deterministic runtime remains authoritative",
        )
        for label in safety_labels:
            with self.subTest(label=label):
                self.assertIn(label, rendered)

    def test_no_fetch_xhr_forms_or_backend_calls(self) -> None:
        dashboard = dashboard_module()
        rendered = self.render_screen4().lower()
        source = read_text(HTML_DASHBOARD_PATH).lower()
        script = dashboard._build_dashboard_interactivity_javascript().lower()

        forbidden_rendered = (
            "<form",
            "method=\"post\"",
            "type=\"submit\"",
            "<button",
            "data-action=",
            "onclick=",
        )
        for phrase in forbidden_rendered:
            with self.subTest(rendered=phrase):
                self.assertNotIn(phrase, rendered)

        forbidden_backend = (
            "fetch(",
            "xmlhttprequest",
            "sendbeacon",
            "/api/write",
            "/api/approve",
            "/api/reject",
            "/api/implement",
            "/api/validate",
            "/api/close",
            "/api/activate",
        )
        for phrase in forbidden_backend:
            with self.subTest(backend=phrase):
                self.assertNotIn(phrase, script)
                self.assertNotIn(phrase, source)

    def render_screen4(self) -> str:
        return dashboard_module()._render_screen_4_page(
            self.sample_screen4_model(),
            chart_payload=self.sample_chart_payload(),
            violin_metric_groups=self.sample_violin_metric_groups(),
            time_series_groups=self.sample_time_series_groups(),
            derived_scalar_metrics={"pga_spill_pressure": 4.5},
        )

    @staticmethod
    def sample_screen4_model() -> dict[str, object]:
        return {
            "header": {
                "scope_label": "ORCL / 123456",
                "instance_name": "ORCL1",
                "host_name": "dbhost01",
                "snapshot_count": 4,
                "comparison_window": "4 snapshots / 2 hours",
            },
            "current_selection_summary": {
                "current_window": "Latest snapshot (10:00-11:00)",
                "comparison_mode": "Latest interval vs broader comparison window",
                "latest_vs_prior": "Latest interval aligns with the broader window.",
            },
            "historical_verdict": {
                "display_severity_label": "High",
                "historical_stability": "Mixed",
                "anomaly_burden": "2 anomaly windows",
                "historical_posture": "TUNE FIRST",
            },
            "normalized_decision": {
                "primary_issue": "CPU",
                "overall_status": "WARNING",
                "display_severity_label": "High",
                "confidence": 0.82,
                "domain_scores": {"CPU": 72.0, "IO": 18.0, "COMMIT": 12.0},
            },
            "historical_summary": {"summary": "CPU remained visible across the window."},
            "trend_review": {
                "trend_summary": {
                    "summary": "CPU trend remained visible.",
                    "findings": ["CPU stayed visible across snapshots."],
                }
            },
            "anomaly_review": {
                "anomalies": {"count": 2},
                "anomaly_summary": {
                    "windows": [
                        {"label": "snap-2 CPU anomaly", "severity": "medium"},
                        {"label": "snap-3 IO anomaly", "severity": "low"},
                    ]
                },
            },
            "comparison_review": {
                "latest_interval": "10:00-11:00",
                "worst_interval": "09:00-10:00",
                "latest_vs_trend": "Latest remains aligned with history.",
                "drift_summary": "No contradictory drift.",
            },
            "similarity_evidence": {
                "enabled": True,
                "similar_cases": [
                    {
                        "awr_id": 7002,
                        "db_name": "ORCL",
                        "similarity_score": 0.91,
                        "distance": 0.09,
                        "primary_signal_domain": "CPU",
                        "risk_level": "High",
                        "workload_class": "OLTP",
                    }
                ],
                "workload_cluster": {"cluster_label": "CPU-led OLTP"},
                "pattern_rarity": {
                    "is_rare_pattern": False,
                    "reason": "Common CPU-led case.",
                },
                "anomaly_validation": {
                    "supports_anomaly": True,
                    "reason": "Similar cases exist.",
                },
            },
            "visual_analysis": {"story": {"section_order": ["time_series", "violin"]}},
            "historical_scope_memory": {},
            "topology_platform_review": {},
            "explanation_panel": {},
        }

    @staticmethod
    def sample_chart_payload() -> dict[str, object]:
        return {
            "time_series_charts": {
                "snapshot_labels": ["snap-1", "snap-2", "snap-3", "snap-4"],
            },
            "violin_panel": {},
        }

    @staticmethod
    def sample_time_series_groups() -> list[dict[str, object]]:
        return [
            {
                "group_key": "cpu",
                "group_title": "CPU Time-Series Charts",
                "charts": [
                    {
                        "key": "cpu_trend",
                        "container_id": "timeSeriesCpuTrend",
                        "title": "DB CPU % DB Time",
                        "label": "DB CPU % DB time",
                        "color": "rgba(255, 107, 107, 0.92)",
                    }
                ],
            }
        ]

    @staticmethod
    def sample_violin_metric_groups() -> list[dict[str, object]]:
        return [
            {
                "group_key": "workload",
                "group_title": "Workload Distributions",
                "group_note": "Cluster-level workload values aggregated per snapshot.",
                "metrics": [
                    {
                        "payload_key": "cluster_cpu_pct_db_time",
                        "container_id": "violinClusterCpuPct",
                        "title": "Cluster CPU % DB Time",
                        "color": "rgba(255, 107, 107, 0.72)",
                    }
                ],
            }
        ]


if __name__ == "__main__":
    unittest.main()
