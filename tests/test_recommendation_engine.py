from __future__ import annotations

from pathlib import Path
import unittest

from src.analysis import recommendation_engine as canonical_recommendation_engine
from src.analysis.recommendation_engine import generate_decision_recommendations
from src.models.decision import AwrDecision
from src.models.recommendation import ActionRecommendation
from src.recommendation import recommendation_engine as specialized_recommendation_engine

ROOT = Path(__file__).resolve().parents[1]


class RecommendationEngineTests(unittest.TestCase):
    def test_authoritative_phase4i_import_path_is_analysis_engine(self) -> None:
        self.assertIs(
            generate_decision_recommendations,
            canonical_recommendation_engine.generate_decision_recommendations,
        )
        self.assertEqual(
            generate_decision_recommendations.__module__,
            "src.analysis.recommendation_engine",
        )
        self.assertNotEqual(
            generate_decision_recommendations,
            specialized_recommendation_engine.generate_recommendations,
        )

        analysis_source = (ROOT / "src" / "analysis" / "recommendation_engine.py").read_text()
        analysis_imports = "\n".join(
            line
            for line in analysis_source.splitlines()
            if line.startswith(("import ", "from "))
        )
        self.assertNotIn("src.recommendation", analysis_imports)

    def test_run_analysis_uses_phase4i_recommendation_path_before_output_contract(self) -> None:
        run_analysis_source = (ROOT / "scripts" / "run_analysis.py").read_text()

        self.assertIn(
            "from src.analysis.recommendation_engine import generate_decision_recommendations",
            run_analysis_source,
        )
        self.assertNotIn(
            "from src.recommendation.recommendation_engine import generate_recommendations",
            run_analysis_source,
        )
        generation_index = run_analysis_source.index(
            "decision_recommendations = generate_decision_recommendations(decision)"
        )
        output_index = run_analysis_source.index("analysis_output = build_analysis_output")
        self.assertLess(generation_index, output_index)
        self.assertIn("recommendations=decision_recommendations", run_analysis_source)

    def test_primary_issue_only(self) -> None:
        decision = AwrDecision(
            awr_id=201,
            overall_status="CRITICAL",
            primary_issue="CPU",
            secondary_issues=[],
            severity_score=81.0,
            confidence=0.92,
            evidence={"domain_scores": {"CPU": 0.9}},
        )

        recommendations = generate_decision_recommendations(decision)

        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].priority, 1)
        self.assertEqual(recommendations[0].issue, "CPU")

    def test_primary_plus_secondary_issues(self) -> None:
        decision = AwrDecision(
            awr_id=202,
            overall_status="WARNING",
            primary_issue="RAC",
            secondary_issues=["CPU", "IO"],
            severity_score=58.0,
            confidence=0.81,
            evidence={"domain_scores": {"RAC": 0.7, "CPU": 0.5, "IO": 0.4}},
        )

        recommendations = generate_decision_recommendations(decision)

        self.assertEqual([item.issue for item in recommendations], ["RAC", "CPU", "IO"])

    def test_recommendation_count_capped_at_three(self) -> None:
        decision = AwrDecision(
            awr_id=203,
            overall_status="CRITICAL",
            primary_issue="ADG",
            secondary_issues=["CPU", "IO", "MEMORY", "COMMIT", "RAC"],
            severity_score=79.0,
            confidence=0.87,
            evidence={"domain_scores": {}},
        )

        recommendations = generate_decision_recommendations(decision)

        self.assertEqual(len(recommendations), 3)
        self.assertEqual(recommendations[0].issue, "ADG")

    def test_duplicate_prevention(self) -> None:
        decision = AwrDecision(
            awr_id=204,
            overall_status="WARNING",
            primary_issue="IO",
            secondary_issues=["IO", "COMMIT", "IO"],
            severity_score=44.0,
            confidence=0.73,
            evidence={"domain_scores": {}},
        )

        recommendations = generate_decision_recommendations(decision)

        self.assertEqual([item.issue for item in recommendations], ["IO", "COMMIT"])

    def test_fixed_order_tie_handling_for_equal_secondaries(self) -> None:
        decision = AwrDecision(
            awr_id=205,
            overall_status="CRITICAL",
            primary_issue="CPU",
            secondary_issues=["RAC", "COMMIT", "IO"],
            severity_score=61.0,
            confidence=0.78,
            evidence={"domain_scores": {}},
        )

        recommendations = generate_decision_recommendations(decision)

        self.assertEqual([item.issue for item in recommendations], ["CPU", "IO", "RAC"])

    def test_symmetric_handling_across_all_issue_domains(self) -> None:
        for issue in ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG"):
            decision = AwrDecision(
                awr_id=300,
                overall_status="WARNING",
                primary_issue=issue,
                secondary_issues=[],
                severity_score=35.0,
                confidence=0.66,
                evidence={"domain_scores": {issue: 0.4}},
            )
            recommendations = generate_decision_recommendations(decision)
            self.assertEqual(len(recommendations), 1)
            self.assertEqual(recommendations[0].issue, issue)
            self.assertGreaterEqual(recommendations[0].confidence, 0.0)
            self.assertLessEqual(recommendations[0].confidence, 1.0)

    def test_lower_level_cpu_helper_is_not_phase4i_authority(self) -> None:
        decision = AwrDecision(
            awr_id=301,
            overall_status="WARNING",
            primary_issue="IO",
            secondary_issues=[],
            severity_score=42.0,
            confidence=0.7,
            evidence={"domain_scores": {"IO": 0.5}},
        )

        canonical_recommendations = generate_decision_recommendations(decision)
        specialized_recommendations = specialized_recommendation_engine.generate_recommendations(
            primary_issue="IO",
            secondary_issues=[],
            overall_status="WARNING",
            severity=42.0,
            feature_vector={},
        )

        self.assertEqual([item.issue for item in canonical_recommendations], ["IO"])
        self.assertIsInstance(canonical_recommendations[0], ActionRecommendation)
        self.assertEqual(specialized_recommendations, [])


if __name__ == "__main__":
    unittest.main()
