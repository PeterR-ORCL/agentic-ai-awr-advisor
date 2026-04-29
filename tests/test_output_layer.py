from __future__ import annotations

import json
import unittest

from src.analysis.output_layer import OUTPUT_VERSION, build_analysis_output, render_analysis_json
from src.models.decision import AwrDecision
from src.models.recommendation import ActionRecommendation


class OutputLayerTests(unittest.TestCase):
    def _decision(self) -> AwrDecision:
        return AwrDecision(
            awr_id=501,
            overall_status="WARNING",
            primary_issue="CPU",
            secondary_issues=["IO"],
            severity_score=78.5,
            confidence=0.87,
            evidence={
                "domain_scores": {"CPU": 9.1, "IO": 4.2},
                "feature_evidence": {
                    "WORKLOAD_CLASS": "CPU_BOUND",
                    "TOPOLOGY_CLASS": "RAC",
                    "PLATFORM_CLASS": "EXADATA",
                    "EVENT_CLASS": "STEADY_STATE",
                },
            },
        )

    def _recommendations(self) -> list[ActionRecommendation]:
        return [
            ActionRecommendation(
                priority=1,
                issue="CPU",
                action="Investigate Top SQL",
                impact="HIGH",
                confidence=0.87,
                evidence={},
            )
        ]

    def test_output_structure_keys_exist(self) -> None:
        payload = build_analysis_output(
            decision=self._decision(),
            scores={"CPU": 9.1, "IO": 4.2},
            trends={"findings": ["CPU rising"], "time_series": {"cpu_trend": [1, 2]}},
            similarity_intelligence={"enabled": True},
            recommendations=self._recommendations(),
            metadata={"awr_id": 501, "db_name": "VALDB"},
        )

        self.assertEqual(
            list(payload.keys()),
            [
                "metadata",
                "decision",
                "scores",
                "trends",
                "similarity_intelligence",
                "recommendations",
            ],
        )

    def test_metadata_fields_exist(self) -> None:
        payload = build_analysis_output(
            decision=self._decision(),
            scores={},
            trends={"findings": [], "time_series": {}},
            similarity_intelligence={"enabled": True},
            recommendations=[],
            metadata={
                "awr_id": 501,
                "db_name": "VALDB",
                "snapshot_begin": "2026-04-29T00:00:00Z",
                "snapshot_end": "2026-04-29T01:00:00Z",
            },
        )

        self.assertEqual(payload["metadata"]["awr_id"], 501)
        self.assertEqual(payload["metadata"]["db_name"], "VALDB")
        self.assertEqual(payload["metadata"]["snapshot_begin"], "2026-04-29T00:00:00Z")
        self.assertEqual(payload["metadata"]["snapshot_end"], "2026-04-29T01:00:00Z")
        self.assertEqual(payload["metadata"]["output_version"], OUTPUT_VERSION)
        self.assertEqual(payload["metadata"]["source"], "AWR_ANALYSIS")
        self.assertTrue(payload["metadata"]["generated_at"].endswith("Z"))

    def test_recommendations_default_to_empty_list(self) -> None:
        payload = build_analysis_output(
            decision=self._decision(),
            scores={},
            trends={"findings": [], "time_series": {}},
            similarity_intelligence={"enabled": True},
            recommendations=None,
            metadata={},
        )

        self.assertEqual(payload["recommendations"], [])

    def test_similarity_defaults_correctly(self) -> None:
        payload = build_analysis_output(
            decision=self._decision(),
            scores={},
            trends={"findings": [], "time_series": {}},
            similarity_intelligence={},
            recommendations=[],
            metadata={},
        )

        self.assertEqual(payload["similarity_intelligence"], {"enabled": False})

    def test_decision_mapping_correct(self) -> None:
        payload = build_analysis_output(
            decision=self._decision(),
            scores={},
            trends={"findings": [], "time_series": {}},
            similarity_intelligence={"enabled": True},
            recommendations=[],
            metadata={},
        )

        self.assertEqual(payload["decision"]["primary_domain"], "CPU")
        self.assertEqual(payload["decision"]["secondary_domains"], ["IO"])
        self.assertEqual(payload["decision"]["risk_level"], "WARNING")
        self.assertEqual(payload["decision"]["confidence"], 0.87)
        self.assertEqual(
            payload["decision"]["classification"],
            {
                "workload_class": "CPU_BOUND",
                "topology_class": "RAC",
                "platform_class": "EXADATA",
                "event_class": "STEADY_STATE",
            },
        )

    def test_scores_nested_correctly(self) -> None:
        payload = build_analysis_output(
            decision=self._decision(),
            scores={"CPU": 9.1, "IO": 4.2},
            trends={"findings": [], "time_series": {}},
            similarity_intelligence={"enabled": True},
            recommendations=[],
            metadata={},
        )

        self.assertEqual(payload["scores"], {"domain_scores": {"CPU": 9.1, "IO": 4.2}})

    def test_trends_pass_through_unchanged(self) -> None:
        trends = {"findings": ["CPU rising"], "time_series": {"cpu_trend": [1, 2]}}
        payload = build_analysis_output(
            decision=self._decision(),
            scores={},
            trends=trends,
            similarity_intelligence={"enabled": True},
            recommendations=[],
            metadata={},
        )

        self.assertEqual(payload["trends"], trends)

    def test_render_analysis_json_uses_new_contract(self) -> None:
        rendered = render_analysis_json(
            decision=self._decision(),
            recommendations=self._recommendations(),
        )
        payload = json.loads(rendered)

        self.assertEqual(payload["metadata"]["output_version"], OUTPUT_VERSION)
        self.assertEqual(payload["decision"]["primary_domain"], "CPU")


if __name__ == "__main__":
    unittest.main()
