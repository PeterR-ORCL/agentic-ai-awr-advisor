"""Tests for the 7CT-F shared runtime LLM explanation contract."""

from __future__ import annotations

import importlib
import unittest


class Phase7RuntimeLLMExplanationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = importlib.import_module(
            "scripts.dashboard_runtime_explanation_contract"
        )

    def valid_legacy_payload(self) -> dict[str, object]:
        return {
            "screen_id": "screen_2",
            "request_type": "screen2_focused_explanation",
            "provider_mode": "mock",
            "selected_focus": "COMMIT",
            "target_type": "diagnostic_domain",
            "inferred_domain": "COMMIT",
            "decision_posture": "TUNE FIRST",
            "primary_issue_domain": "No dominant scored domain selected",
            "severity": "OK",
            "confidence": "LOW",
            "deterministic_facts": "log file sync = 8.4",
            "non_mutating_explanation_only": True,
        }

    def test_truth_source_registry_marks_cache_and_provider_non_authoritative(self) -> None:
        registry = self.contract.RUNTIME_EXPLANATION_TRUTH_SOURCE_AUTHORITY

        self.assertIn("deterministic_phase4_output", registry)
        self.assertEqual(registry["deterministic_phase4_output"]["authority"], "highest")
        self.assertTrue(registry["cache_continuity_only"]["cache_only"])
        self.assertEqual(
            registry["provider_generated_wording"]["authority"],
            "non_authoritative_wording",
        )

    def test_contract_docstring_preserves_governed_access_distinction(self) -> None:
        doc = self.contract.__doc__ or ""
        normalized_doc = " ".join(doc.split())

        self.assertIn(
            "DB calls, provider calls, and runtime side effects are not categorically forbidden",
            normalized_doc,
        )
        self.assertIn("ungoverned access", normalized_doc)
        self.assertIn("hidden mutation", normalized_doc)
        self.assertIn(
            "wording-only explanation causing or claiming state changes",
            normalized_doc,
        )
        self.assertIn(
            "Screen 3 through Screen 6 may require future runtime DB calls, provider calls, and governed workflow side effects",
            normalized_doc,
        )
        self.assertIn("validated/audited as designed", normalized_doc)

    def test_screen1_parser_governance_scope_allows_explanation_not_mutation(self) -> None:
        allowed = self.contract.RUNTIME_EXPLANATION_ALLOWED_SCOPES["screen_1"]
        forbidden = self.contract.RUNTIME_EXPLANATION_FORBIDDEN_MUTATIONS["screen_1"]

        self.assertIn("new AWR sections/elements/signals", allowed)
        self.assertIn("parser mapping candidates", allowed)
        self.assertIn("potential feature/domain candidates", allowed)
        self.assertIn("create scoring features", forbidden)
        self.assertIn("assign diagnostic domains", forbidden)

    def test_all_product_screens_have_allowed_and_forbidden_scopes(self) -> None:
        expected = {
            "index_source_mode",
            "screen_1",
            "screen_2",
            "screen_3",
            "screen_4",
            "screen_5",
            "screen_6",
        }

        self.assertEqual(
            expected,
            set(self.contract.RUNTIME_EXPLANATION_SCREEN_ROLES),
        )
        for screen_id in expected:
            with self.subTest(screen_id=screen_id):
                self.assertTrue(
                    self.contract.RUNTIME_EXPLANATION_ALLOWED_SCOPES[screen_id]
                )
                self.assertTrue(
                    self.contract.RUNTIME_EXPLANATION_FORBIDDEN_MUTATIONS[screen_id]
                )

    def test_payload_validation_requires_non_mutating_provider_and_no_mutation_fields(self) -> None:
        validate = self.contract.validate_runtime_explanation_payload
        payload = self.valid_legacy_payload()

        self.assertEqual(validate(payload, expected_screen_id="screen_2"), "")
        self.assertIn(
            "marked non-mutating",
            validate({**payload, "non_mutating_explanation_only": False}, expected_screen_id="screen_2"),
        )
        self.assertIn(
            "Unsupported runtime explanation provider mode",
            validate({**payload, "provider_mode": "grok"}, expected_screen_id="screen_2"),
        )
        self.assertIn(
            "mutation/workflow fields",
            validate({**payload, "action_type": "diagnostic_review"}, expected_screen_id="screen_2"),
        )
        self.assertIn(
            "cannot create records",
            validate({**payload, "records_created": True}, expected_screen_id="screen_2"),
        )
        self.assertIn(
            "cannot provide an audit reference",
            validate({**payload, "audit_reference": "AUDIT-1"}, expected_screen_id="screen_2"),
        )

    def test_payload_validation_can_allow_explicit_governed_record_context(self) -> None:
        validate = self.contract.validate_runtime_explanation_payload
        payload = {
            **self.valid_legacy_payload(),
            "records_created": True,
            "audit_reference": "AUDIT-1",
        }

        self.assertEqual(
            validate(
                payload,
                expected_screen_id="screen_2",
                allow_records_created=True,
                allow_audit_reference=True,
            ),
            "",
        )

    def test_boundary_detector_rejects_unsafe_provider_wording(self) -> None:
        violates = self.contract.runtime_explanation_violates_boundary

        for text in (
            "The LLM changed the diagnosis.",
            "The provider assigned Target A for comparison.",
            "This explanation activated runtime eligibility.",
            "Phase 8 is active and sizing is active.",
            "Future runs will use the trained model.",
        ):
            with self.subTest(text=text):
                self.assertTrue(violates(text))

        self.assertFalse(
            violates(
                "The deterministic diagnosis remains unchanged; this wording only explains the selected context."
            )
        )

    def test_response_normalization_preserves_wording_only_expectations(self) -> None:
        response = self.contract.normalize_runtime_explanation_response(
            {
                "status": "generated",
                "provider_mode": "mock",
                "explanation": "Deterministic values remain unchanged.",
                "records_created": True,
                "audit_reference": "AUDIT-1",
            },
            boundary_validation_result="passed",
        )

        self.assertEqual(response["status"], "generated")
        self.assertFalse(response["records_created"])
        self.assertIsNone(response["audit_reference"])
        self.assertFalse(response["records_created_expected"])
        self.assertIsNone(response["audit_reference_expected"])
        self.assertEqual(response["provider_output_status"], "generated")
        self.assertEqual(response["boundary_validation_result"], "passed")

    def test_legacy_screen2_explanation_route_conforms_to_shared_contract(self) -> None:
        service = importlib.import_module("scripts.dashboard_workflow_service")
        payload = self.valid_legacy_payload()

        result = service.generate_screen2_explanation(payload)

        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["provider_mode"], "mock")
        self.assertFalse(result["records_created"])
        self.assertIsNone(result["audit_reference"])
        self.assertFalse(result["records_created_expected"])
        self.assertIsNone(result["audit_reference_expected"])
        self.assertEqual(result["provider_output_status"], "generated")
        self.assertEqual(result["boundary_validation_result"], "passed")
        self.assertIn("active Screen 3 diagnostic explanation focus", result["explanation"])
        self.assertIn("already-computed deterministic analysis", result["explanation"])
        self.assertIn("does not load evidence, parse AWR content, compare evidence", result["explanation"])
        self.assertIn("assign Target A/B", result["explanation"])
        self.assertIn("decide comparison readiness", result["explanation"])
        self.assertNotIn("active Screen 2 explanation focus", result["explanation"])

        rejected = service.generate_screen2_explanation(
            {**payload, "create_audit_record": True}
        )
        self.assertEqual(rejected["status"], "rejected")
        self.assertFalse(rejected["records_created"])
        self.assertIsNone(rejected["audit_reference"])


if __name__ == "__main__":
    unittest.main()
