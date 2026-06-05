from __future__ import annotations

import importlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "architecture" / "phase7cx_screen4_comparative_review_contract.md"
MODE_SHELL_DOC_PATH = ROOT / "docs" / "architecture" / "phase7_screen4_evidence_review_mode_shell.md"


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class Screen4ComparativeReviewGuardTests(unittest.TestCase):
    def test_prepared_target_ab_context_only_returns_prepared_only(self) -> None:
        dashboard = dashboard_module()

        state = dashboard._screen4_build_comparative_review_state(
            {
                "comparison_prepared_context": {
                    "target_a": {"label": "AWR 1001", "run_id": "run-a"},
                    "target_b": {"label": "AWR 1002", "run_id": "run-b"},
                    "comparison_mode": "target_a_vs_target_b",
                    "comparison_window": "prepared window",
                    "context_source": "Screen 2 prepared context",
                }
            }
        )

        self.assertEqual("comparison_prepared_only", state["state"])
        self.assertFalse(state["comparison_output_ready"])
        self.assertEqual(2, len(state["prepared_targets"]))
        self.assertEqual("blocked", state["graphics_state"])

    def test_route_state_targets_do_not_make_output_ready(self) -> None:
        dashboard = dashboard_module()

        state = dashboard._screen4_build_comparative_review_state(
            {
                "selectedComparisonTargetA": "run-a",
                "selectedComparisonTargetB": "run-b",
                "selectedComparisonTargetAScopeValue": "1001",
                "selectedComparisonTargetBScopeValue": "1002",
            }
        )

        self.assertEqual("comparison_prepared_only", state["state"])
        self.assertFalse(dashboard._screen4_has_deterministic_comparison_output(state))

    def test_cache_only_reference_and_loose_handoffs_do_not_make_output_ready(self) -> None:
        dashboard = dashboard_module()

        cache_state = dashboard._screen4_build_comparative_review_state(
            {
                "comparison_cache_status": "cached_continuity_only",
                "comparison_artifact_reference": "comparison:cached-only",
            }
        )
        self.assertEqual("comparison_prepared_only", cache_state["state"])
        self.assertFalse(cache_state["comparison_output_ready"])

        for payload in (
            {"comparison_screen4_handoff": {"status": "ready"}},
            {"comparison_result_metadata": {"comparison_id": "legacy-result"}},
            {"comparison_result_status": "comparison_ready"},
            {"comparison_review": {"comparison_artifact_reference": "comparison:legacy"}},
        ):
            with self.subTest(payload=payload):
                state = dashboard._screen4_build_comparative_review_state(payload)
                self.assertEqual("comparison_output_required", state["state"])
                self.assertFalse(state["comparison_output_ready"])

    def test_screen3_prepared_only_context_is_not_output_ready(self) -> None:
        dashboard = dashboard_module()

        state = dashboard._screen4_build_comparative_review_state(
            {
                "screen3_evidence_context": {
                    "comparison_context": {
                        "comparison_status": "comparison_prepared_only",
                        "target_a": {"label": "AWR 1001", "run_id": "run-a"},
                        "target_b": {"label": "AWR 1002", "run_id": "run-b"},
                    }
                }
            }
        )

        self.assertEqual("comparison_prepared_only", state["state"])
        self.assertFalse(state["comparison_output_ready"])

    def test_7cc_metadata_without_screen4_contract_is_rejected(self) -> None:
        dashboard = dashboard_module()

        validation = dashboard._screen4_validate_deterministic_comparison_output(
            {
                "comparison_id": "comparison-7cc",
                "baseline_run_id": "run-a",
                "candidate_run_id": "run-b",
                "source_scope": "same_db_historical",
                "comparison_scope": "target_a_vs_target_b",
                "generated_by": "deterministic_engine",
                "generated_at": "2026-06-05T12:00:00Z",
                "deterministic_engine_version": "7cc",
                "metric_deltas": [],
                "domain_deltas": [],
                "evidence_rows": [{"metric": "db_time"}],
                "confidence_basis": {
                    "basis_type": "deterministic_evidence",
                    "sample_count": 2,
                    "limitations": [],
                },
                "missing_evidence": [],
                "allowed_visualizations": ["metric_delta_table"],
                "comparison_output_reference": {"artifact_id": "7cc-output"},
            }
        )

        self.assertFalse(validation["valid"])
        self.assertEqual("screen4_contract_type_missing", validation["reason"])

    def test_malformed_contracts_are_rejected(self) -> None:
        dashboard = dashboard_module()

        rejected_payloads = (
            None,
            {},
            "comparison:artifact-only",
            {"comparison_artifact_reference": "comparison:legacy"},
            {**self.valid_contract(), "generated_by": "browser"},
            {k: v for k, v in self.valid_contract().items() if k != "deterministic_engine_version"},
            {k: v for k, v in self.valid_contract().items() if k != "allowed_visualizations"},
            {**self.valid_contract(), "confidence_basis": {"basis_type": "llm_explanation"}},
            {**self.valid_contract(), "evidence_rows": [], "no_change_evidence": {}},
        )

        for payload in rejected_payloads:
            with self.subTest(payload=payload):
                validation = dashboard._screen4_validate_deterministic_comparison_output(payload)
                self.assertFalse(validation["valid"])

    def test_valid_contract_returns_output_ready(self) -> None:
        dashboard = dashboard_module()

        state = dashboard._screen4_build_comparative_review_state(
            {"deterministic_comparison_output": self.valid_contract()}
        )

        self.assertEqual("comparison_output_ready", state["state"])
        self.assertTrue(state["comparison_output_ready"])
        self.assertTrue(
            dashboard._screen4_comparison_visualization_allowed(
                self.valid_contract(),
                "metric_delta_table",
            )
        )
        self.assertFalse(
            dashboard._screen4_comparison_visualization_allowed(
                self.valid_contract(),
                "comparison_violin",
            )
        )

    def test_valid_no_change_contract_can_be_output_ready_without_delta_rows(self) -> None:
        dashboard = dashboard_module()
        contract = {
            **self.valid_contract(),
            "metric_deltas": [],
            "domain_deltas": [],
            "evidence_rows": [],
            "no_change_evidence": {
                "basis_type": "deterministic_evidence",
                "explanation": "Deterministic engine found no displayable evidence rows for this comparison scope.",
            },
        }

        validation = dashboard._screen4_validate_deterministic_comparison_output(contract)

        self.assertTrue(validation["valid"])

    def test_target_identity_mismatch_is_rejected(self) -> None:
        dashboard = dashboard_module()

        validation = dashboard._screen4_validate_deterministic_comparison_output(
            self.valid_contract(),
            selected_context={
                "target_a": {"run_id": "other-baseline"},
                "target_b": {"run_id": "run-b"},
            },
        )

        self.assertFalse(validation["valid"])
        self.assertEqual("target_identity_mismatch", validation["reason"])

    def test_evidence_required_and_output_required_states_are_distinct(self) -> None:
        dashboard = dashboard_module()

        evidence_required = dashboard._screen4_build_comparative_review_state(
            {
                "comparison_prepared_context": {
                    "target_a": {"label": "AWR 1001", "run_id": "run-a"},
                    "target_b": {"label": "AWR 1002", "run_id": "run-b"},
                    "evidence_status": "load_required",
                }
            }
        )
        output_required = dashboard._screen4_build_comparative_review_state(
            {
                "comparison_prepared_context": {
                    "target_a": {"label": "AWR 1001", "run_id": "run-a"},
                    "target_b": {"label": "AWR 1002", "run_id": "run-b"},
                    "target_evidence_state": "ready_for_comparison",
                }
            }
        )

        self.assertEqual("comparison_evidence_required", evidence_required["state"])
        self.assertEqual("comparison_output_required", output_required["state"])

    def test_prepared_only_rendered_panel_has_no_conclusion_words_or_graphics(self) -> None:
        dashboard = dashboard_module()
        state = dashboard._screen4_build_comparative_review_state(
            {
                "comparison_prepared_context": {
                    "target_a": {"label": "AWR 1001", "run_id": "run-a"},
                    "target_b": {"label": "AWR 1002", "run_id": "run-b"},
                }
            }
        )

        rendered = dashboard._render_screen4_comparative_review_panel(state)
        section = rendered[
            rendered.index("screen4-comparative-review-guard"):
        ].lower()

        self.assertIn("prepared comparison context exists", section)
        self.assertIn("comparative review is not ready yet", section)
        self.assertIn("no governed deterministic comparison output has been returned to screen 4", section)
        self.assertIn("it does not create comparison evidence", section)
        self.assertIn("target a/b selections are preparation only", section)
        self.assertIn("no comparison graphics are available", section)
        for forbidden in (
            "improved",
            "degraded",
            "stable",
            "better",
            "worse",
            "winner",
            "loser",
            "regression",
            "improvement",
            "delta conclusion",
            "comparison trend",
            "comparison-violin-panel",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, section)

    def test_comparative_review_contract_documentation_exists(self) -> None:
        self.assertTrue(DOC_PATH.is_file())
        text = DOC_PATH.read_text(encoding="utf-8").lower()
        shell_text = MODE_SHELL_DOC_PATH.read_text(encoding="utf-8").lower()

        required = (
            "prepared comparison context",
            "deterministic comparison output",
            "comparison_unavailable",
            "comparison_prepared_only",
            "comparison_evidence_required",
            "comparison_output_required",
            "comparison_output_ready",
            "target a/b setup from screen 2 is prepared comparison context only",
            "cache-only evidence is not evidence",
            "the word comparison is reserved",
            "supporting context, historical supporting context, topology supporting context",
            "allowed_visualizations",
            "7cc metadata unless a future adapter creates the strict screen 4 contract",
            "llm wording may explain validated deterministic comparison output only after that output exists",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

        shell_required = (
            "7cx-b adds a guarded comparative review state model",
            "only a strict screen 4 deterministic comparison output contract can enter `comparison_output_ready`",
            "target a/b is prepared comparison context only",
            "target a/b preparation alone does not create screen 4 comparison evidence",
            "7cc comparison execution metadata requires a future adapter",
        )
        for phrase in shell_required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, shell_text)

    @staticmethod
    def valid_contract() -> dict[str, object]:
        return {
            "screen4_contract_type": "deterministic_comparison_output",
            "comparison_id": "comparison-001",
            "baseline_run_id": "run-a",
            "candidate_run_id": "run-b",
            "source_scope": "same_db_historical",
            "comparison_scope": "target_a_vs_target_b",
            "generated_by": "deterministic_engine",
            "generated_at": "2026-06-05T12:00:00Z",
            "deterministic_engine_version": "screen4-contract-v1",
            "metric_deltas": [],
            "domain_deltas": [],
            "evidence_rows": [{"metric": "db_time", "baseline": 10, "candidate": 12}],
            "confidence_basis": {
                "basis_type": "deterministic_evidence",
                "sample_count": 2,
                "limitations": [],
            },
            "missing_evidence": [],
            "allowed_visualizations": ["metric_delta_table"],
        }


if __name__ == "__main__":
    unittest.main()
