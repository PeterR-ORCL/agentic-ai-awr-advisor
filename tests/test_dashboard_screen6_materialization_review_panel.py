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


class DashboardScreen6MaterializationReviewPanelTests(unittest.TestCase):
    def test_html_dashboard_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_screen6_materialization_review_preview_exists(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen6()
        for phrase in (
            "Screen 6 Materialization Review Preview",
            "Read-Only Materialization Review Request Preview",
            "Phase 7BM Preview",
            "materialization_id",
            "materialization_type",
            "validation_status",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_all_preview_controls_are_present(self) -> None:
        rendered = self.render_screen6()
        for phrase in (
            "Mark Under Review",
            "Approve for Validation",
            "Reject Materialization",
            "Request Revision",
            "Attach Validation Reference",
            "Attach Rollback Reference",
            "Mark Validated",
            "Mark Implemented",
            "Close Materialization",
            "Add Materialization Note",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_controls_are_disabled_preview_only(self) -> None:
        rendered = self.render_screen6()
        self.assertIn('id="screen6-materialization-review-preview-panel"', rendered)
        self.assertEqual(
            rendered.count("screen6-materialization-review-control preview-only"),
            10,
        )
        self.assertGreaterEqual(rendered.count("disabled"), 10)
        self.assertGreaterEqual(rendered.count('aria-disabled="true"'), 10)
        self.assertGreaterEqual(rendered.count('data-preview-only="true"'), 11)
        self.assertIn("Controls are disabled/preview-only", rendered)
        self.assertIn("Materialization review disabled in this phase", rendered)
        self.assertIn("Preview only", rendered)

    def test_safety_labels_present(self) -> None:
        rendered = self.render_screen6()
        for phrase in (
            "Preview only",
            "Materialization review disabled in this phase",
            "No materialization status changed",
            "No governance action performed",
            "No validation reference attached",
            "No rollback reference attached",
            "No runtime activation requested",
            "No governed write path invoked",
            "No Phase 4I mutation",
            "Deterministic runtime remains authoritative",
            "write_performed=false",
            "materialization_status_changed=false",
            "governance_action_performed=false",
            "validation_reference_attached=false",
            "rollback_reference_attached=false",
            "runtime_activation_requested=false",
            "runtime_influence=false",
            "phase4i_mutation_requested=false",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_fetch_xhr_forms_or_backend_calls(self) -> None:
        dashboard = dashboard_module()
        panel_source = inspect.getsource(
            dashboard._render_screen6_materialization_review_preview_panel
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
            "materialization_review_endpoint",
            "invoke_governed_write_path(",
            "update_materialization_status(",
            "persist_materialization_review(",
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
            "Learning Visibility",
            "Learning candidates are proposal/review context only",
            "No runtime activation",
            "No governed write path invoked",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

        completed = subprocess.run(
            (
                "python3",
                "-m",
                "unittest",
                "tests/test_dashboard_screen6_fleet_governance_learning_exploration.py",
            ),
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


if __name__ == "__main__":
    unittest.main()
