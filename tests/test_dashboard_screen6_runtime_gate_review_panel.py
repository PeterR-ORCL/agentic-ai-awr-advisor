from __future__ import annotations

import importlib
import inspect
import py_compile
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardScreen6RuntimeGateReviewPanelTests(unittest.TestCase):
    def test_html_dashboard_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_screen6_runtime_gate_review_preview_exists(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen6()
        for phrase in (
            "Screen 6 Runtime Gate Review Preview",
            "Read-Only Runtime Gate Review Request Preview",
            "Phase 7BO Preview",
            "gate_id",
            "gate_type",
            "validation_status",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_all_preview_controls_are_present(self) -> None:
        rendered = self.render_screen6()
        for phrase in (
            "Mark Gate Under Review",
            "Review Adaptive Runtime Context",
            "Review Scoring Integration",
            "Review Recommendation Integration",
            "Review Parser Integration",
            "Review Fallback Posture",
            "Request Runtime Review",
            "Request Rollback Review",
            "Request Gate Revision",
            "Close Gate Review",
            "Add Runtime Gate Note",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_controls_are_disabled_preview_only(self) -> None:
        rendered = self.render_screen6()
        self.assertIn('id="screen6-runtime-gate-review-preview-panel"', rendered)
        self.assertEqual(
            rendered.count("screen6-runtime-gate-review-control preview-only"),
            11,
        )
        self.assertGreaterEqual(rendered.count("disabled"), 11)
        self.assertGreaterEqual(rendered.count('aria-disabled="true"'), 11)
        self.assertGreaterEqual(rendered.count('data-preview-only="true"'), 12)
        self.assertIn("Controls are disabled/preview-only", rendered)
        self.assertIn("Runtime gate review disabled in this phase", rendered)
        self.assertIn("Preview only", rendered)

    def test_safety_labels_present(self) -> None:
        rendered = self.render_screen6()
        for phrase in (
            "Preview only",
            "Runtime gate review disabled in this phase",
            "No runtime gate state changed",
            "Adaptive runtime remains disabled",
            "Runtime influence not granted",
            "Runtime eligibility not granted",
            "Runtime active false",
            "No rollback execution",
            "No governed write path invoked",
            "No Phase 4I mutation",
            "Deterministic runtime remains authoritative",
            "write_performed=false",
            "gate_state_changed=false",
            "adaptive_runtime_enabled_changed=false",
            "runtime_influence_allowed_changed=false",
            "runtime_review_requested=false",
            "rollback_review_requested=false",
            "runtime_influence_granted=false",
            "runtime_eligibility_granted=false",
            "runtime_active=false",
            "governance_action_performed=false",
            "validation_reference_attached=false",
            "rollback_reference_attached=false",
            "phase4i_mutation_requested=false",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_fetch_xhr_forms_or_backend_calls(self) -> None:
        dashboard = dashboard_module()
        panel_source = inspect.getsource(
            dashboard._render_screen6_runtime_gate_review_preview_panel
        ).lower()
        rendered = self.render_screen6().lower()
        full_source = lower_text(HTML_DASHBOARD_PATH)

        for phrase in (
            "<form",
            "method=\"post\"",
            "action=\"/",
            "fetch(",
            "xmlhttprequest",
            "sendbeacon",
            "/api/",
            "runtime_gate_review_endpoint",
            "invoke_governed_write_path(",
            "update_runtime_gate_state(",
            "persist_runtime_gate_review(",
            "enable_adaptive_runtime(",
            "grant_runtime_influence(",
            "grant_runtime_eligibility(",
            "execute_rollback(",
            "activate_runtime(",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, rendered)
                self.assertNotIn(phrase, panel_source)
                self.assertNotIn(phrase, full_source)

    def test_existing_screen6_visibility_and_exploration_remain_present(self) -> None:
        rendered = self.render_screen6()
        for phrase in (
            "Screen 6 Fleet / Governance / Semantic / Learning Exploration",
            "Read-only fleet/governance/semantic/learning exploration",
            "ML / Adaptive Explainability Visibility",
            "Runtime Gate / Adapter / Fallback Posture",
            "Runtime gate visibility does not activate runtime",
            "No runtime activation",
            "No governed write path invoked",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        for test_path in (
            "tests/test_dashboard_screen6_fleet_governance_learning_exploration.py",
            "tests/test_dashboard_ml_explainability_visibility.py",
        ):
            with self.subTest(test_path=test_path):
                completed = subprocess.run(
                    ("python3", "-m", "unittest", test_path),
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    completed.returncode,
                    0,
                    completed.stdout + completed.stderr,
                )

    def render_screen6(self) -> str:
        return dashboard_module()._render_screen_6_page(
            self.sample_screen6_model(),
            governance_payload=self.sample_governance_payload(),
            semantic_recall_payload=self.sample_semantic_payload(),
            learning_visibility_payload=self.sample_learning_payload(),
            ml_explainability_visibility_payload=self.sample_ml_payload(),
        )

    @staticmethod
    def sample_screen6_model() -> dict[str, object]:
        return {
            "similarity_enabled": True,
            "header": {
                "scope_label": "ORCL / 123456",
                "db_name": "ORCL",
                "dbid": "123456",
                "instance_name": "ORCL1",
                "host_name": "dbhost01",
                "snapshot_count": 4,
                "comparison_window": "2 hours",
                "awr_id": 7001,
                "run_history_id": 42,
            },
            "fleet_summary": {
                "cluster_label": "CPU-bound peers",
                "cluster_confidence": 0.72,
                "similar_awrs": 2,
                "rarity": "common",
            },
            "clusters": {"similar_cases": []},
            "rare_patterns": {"is_rare_pattern": False},
            "anomaly_validation": {"supports_anomaly": True},
            "repeated_issues": [{"issue": "CPU", "count": 2}],
            "recommendation_backlog": [{"issue": "CPU", "count": 1}],
        }

    @staticmethod
    def sample_governance_payload() -> dict[str, object]:
        return {
            "available": True,
            "unknown_signal_summary": {"TOTAL": 3, "PENDING_REVIEW": 1},
            "approval_summary": {"PENDING": 1, "APPROVED": 1},
            "artifact_summary": {"INACTIVE": 1, "TOTAL": 1},
            "workflow_summary": {"NEW": 1, "PENDING": 1},
            "linkage": [
                {
                    "request_id": "KR-001",
                    "source_type": "UNKNOWN_SIGNAL",
                    "source_id": 11,
                    "approval_status": "PENDING",
                    "artifact_id": "MAT-001",
                    "materialization_id": "MAT-001",
                    "artifact_classification": "parser_mapping",
                    "materialization_status": "PROPOSED",
                    "activation_status": "INACTIVE",
                }
            ],
        }

    @staticmethod
    def sample_semantic_payload() -> dict[str, object]:
        return {
            "enabled": True,
            "provider": "Oracle Agent Memory",
            "mode": "offline metadata",
            "authoritative": False,
            "runtime_influence": False,
            "assist_scope": ["Reviewer context"],
            "latest_context": [{"query": "CPU wait context", "count": 2}],
        }

    @staticmethod
    def sample_learning_payload() -> dict[str, object]:
        return {
            "candidate_count": 1,
            "status_counts": {"PROPOSED": 1},
            "type_counts": {"parser_mapping_candidate": 1},
            "affected_domain_counts": {"CPU": 1},
            "semantic_context_count": 0,
            "candidates": [
                {
                    "candidate_id": "CAND-CPU-001",
                    "candidate_type": "parser_mapping_candidate",
                    "status": "PROPOSED",
                    "affected_domain": "CPU",
                    "title": "Map CPU parser signal",
                    "runtime_influence": False,
                    "requires_human_review": True,
                }
            ],
            "governance": {"records": []},
        }

    @staticmethod
    def sample_ml_payload() -> dict[str, object]:
        return {
            "read_only": True,
            "safety_labels": [
                "Read-only",
                "No runtime activation",
                "Deterministic runtime remains authoritative",
            ],
            "summary": {
                "explanation_count": 1,
                "feature_contribution_count": 1,
                "model_registry_count": 1,
                "score_delta_count": 1,
                "runtime_gate_count": 1,
                "adapter_result_count": 1,
                "fallback_decision_count": 1,
            },
            "model_registry_rows": [
                {
                    "model_id": "MODEL-CPU-001",
                    "model_family": "tree",
                    "model_version": "v1",
                    "governance_status": "PROPOSED",
                    "shadow_eligible": False,
                    "runtime_eligibility_requested": False,
                    "runtime_eligibility_granted": False,
                    "runtime_active": False,
                }
            ],
            "score_deltas": [],
            "explanation_rows": [],
            "feature_contribution_rows": [],
            "runtime_gate_rows": [
                {
                    "gate_id": "GATE-CPU-001",
                    "gate_type": "adaptive_runtime_gate",
                    "component_type": "scoring",
                    "allowed_for_consideration": False,
                    "runtime_active": False,
                    "runtime_influence_granted": False,
                    "gate_status": "DENIED",
                }
            ],
            "adapter_rows": [
                {
                    "adapter_type": "scoring",
                    "result_id": "ADAPTER-CPU-001",
                    "gate_allowed_for_consideration": False,
                }
            ],
            "fallback_rows": [
                {
                    "decision_id": "FALLBACK-CPU-001",
                    "final_runtime_posture": "deterministic_fallback",
                    "rollback_available": False,
                }
            ],
        }


if __name__ == "__main__":
    unittest.main()
