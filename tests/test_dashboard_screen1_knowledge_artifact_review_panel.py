from __future__ import annotations

import importlib
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"
PANEL_DOC = DOCS / "phase7ax_screen1_knowledge_artifact_review_panel.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardScreen1KnowledgeArtifactReviewPanelTests(unittest.TestCase):
    def render_screen1(self) -> str:
        return dashboard_module()._render_screen_1_page(
            self.sample_screen1_model(),
            parser_review_payload={},
            parser_governance_payload=self.sample_parser_governance_payload(),
            report_data={"run_history_id": "RUN-1"},
        )

    @staticmethod
    def sample_screen1_model() -> dict[str, object]:
        return {
            "header": {"run_history_id": "RUN-1"},
            "intake_summary": {
                "total_files": 1,
                "processed": 1,
                "succeeded": 1,
                "failed": 0,
                "skipped": 0,
            },
            "parse_confidence_adaptation": {
                "parse_completeness_score": 0.91,
                "warnings_count": 1,
                "sections_detected": 12,
                "unknowns_captured": 0,
            },
            "report_rows": [],
            "validation_notes": {"notes": []},
        }

    @staticmethod
    def sample_parser_governance_payload() -> dict[str, object]:
        return {
            "knowledge_artifacts": [
                {
                    "artifact_id": "ARTIFACT-1",
                    "artifact_type": "parser_mapping_guidance",
                    "artifact_title": "Parser mapping guidance",
                }
            ]
        }

    def test_dashboard_source_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_knowledge_artifact_review_preview_panel_exists(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen1()
        for phrase in (
            "Screen 1 Knowledge Artifact Review Preview",
            "Approve for Review",
            "Reject Artifact",
            "Request Revision",
            "Link to Candidate",
            "Link to Materialization",
            "Link to Parser Review",
            "Link to Scoring Review",
            "Link to Recommendation Review",
            "Mark Superseded",
            "Add Review Note",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_controls_are_disabled_preview_only(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen1()
        for phrase in (
            "aria-disabled",
            "data-preview-only",
            "disabled-preview-only",
            "Knowledge artifact review disabled in this phase",
            "Preview only",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_safety_labels_exist(self) -> None:
        rendered = self.render_screen1()
        for phrase in (
            "No artifact approval executed",
            "No artifact rejection executed",
            "No revision request persisted",
            "No candidate created automatically",
            "No materialization created",
            "No parser/scoring/recommendation change",
            "No Phase 4I mutation",
            "No governed write path invoked",
            "Deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_unsafe_backend_calls(self) -> None:
        source = lower_text(HTML_DASHBOARD_PATH)
        for phrase in (
            "fetch(",
            "xmlhttprequest",
            "method=\"post\"",
            "action=\"/",
            "persist_artifact_review",
            "approve_artifact",
            "reject_artifact",
            "request_artifact_revision",
            "create_materialization_artifact",
            "update_parser",
            "update_scoring",
            "update_recommendation",
            "mutate_phase4i",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, source)

    def test_preview_fields_exist(self) -> None:
        rendered = self.render_screen1()
        for phrase in (
            "artifact_id",
            "artifact_type",
            "artifact_title",
            "review_decision",
            "review_status",
            "candidate_type",
            "materialization_type",
            "followup_type",
            "actor required",
            "audit required",
            "governed write path required",
            "write_performed=false",
            "artifact_approved=false",
            "artifact_rejected=false",
            "artifact_revision_requested=false",
            "candidate_created=false",
            "materialization_created=false",
            "phase4i_mutation_requested=false",
            "runtime_influence=false",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_docs_exist_and_contain_required_phrases(self) -> None:
        self.assertTrue(PANEL_DOC.is_file(), PANEL_DOC)
        text = lower_text(PANEL_DOC)
        for phrase in (
            "all controls are disabled/preview-only",
            "no artifact review is persisted",
            "no artifact approval/rejection is executed",
            "no artifact revision request is persisted",
            "no candidate is created automatically",
            "no materialization artifact is created",
            "no parser/scoring/recommendation behavior changes occur",
            "no phase 4i mutation occurs",
            "deterministic runtime remains authoritative",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
