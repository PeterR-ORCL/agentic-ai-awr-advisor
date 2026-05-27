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
        self.assertIn("New AWR Mapping Candidates", allowed)
        self.assertIn("parser health state", allowed)
        self.assertIn("unknown parser signal meaning", allowed)
        self.assertIn("artifact readiness meaning", allowed)
        self.assertIn("downstream handoff eligibility meaning", allowed)
        self.assertIn("deterministic analysis separation", allowed)
        self.assertIn("parser mapping candidates", allowed)
        self.assertIn("potential feature/domain candidates", allowed)
        self.assertIn("approve parser mappings", forbidden)
        self.assertIn("reject parser mappings", forbidden)
        self.assertIn("map parser candidates", forbidden)
        self.assertIn("create scoring features", forbidden)
        self.assertIn("assign diagnostic domains", forbidden)
        self.assertIn("load runtime options", forbidden)
        self.assertIn("assign Target A/B", forbidden)
        self.assertIn("decide comparison readiness", forbidden)
        self.assertIn("change future-run behavior", forbidden)

    def test_home_source_path_scope_explains_paths_without_workflow_control(self) -> None:
        allowed = self.contract.RUNTIME_EXPLANATION_ALLOWED_SCOPES["index_source_mode"]
        forbidden = self.contract.RUNTIME_EXPLANATION_FORBIDDEN_MUTATIONS["index_source_mode"]

        for phrase in (
            "local source path meaning",
            "Object Storage source path meaning",
            "existing platform evidence path meaning",
            "Screen 1 new-source handoff meaning",
            "Screen 2 existing-evidence handoff meaning",
            "generated artifact versus active downstream evidence",
            "downstream evidence handoff requirements",
        ):
            with self.subTest(allowed=phrase):
                self.assertIn(phrase, allowed)

        for phrase in (
            "select source path",
            "validate source availability",
            "load source",
            "parse AWR content",
            "load runtime options",
            "select existing run",
            "assign Target A/B",
            "decide comparison readiness",
            "set dashboardEvidenceReady",
            "perform deterministic analysis",
            "perform comparison",
            "unlock downstream screens",
        ):
            with self.subTest(forbidden=phrase):
                self.assertIn(phrase, forbidden)

    def test_home_source_path_contract_uses_dashboard_state_without_mutation(self) -> None:
        envelope = self.contract.build_runtime_explanation_contract(
            "index_source_mode",
            truth_source="generated_dashboard_state",
            provider_mode="mock",
        )

        self.assertEqual(
            envelope["screen_role"],
            "Home / Index - Platform Entry / Source Intake",
        )
        self.assertEqual(envelope["truth_source"], "generated_dashboard_state")
        self.assertEqual(envelope["truth_source_authority"], "presentation_snapshot")
        self.assertEqual(envelope["provider_mode"], "mock")
        self.assertTrue(envelope["non_mutating_explanation_only"])
        self.assertFalse(envelope["records_created_expected"])
        self.assertIsNone(envelope["audit_reference_expected"])
        self.assertIn("source-entry paths", envelope["allowed_explanation_scope"])
        self.assertIn("select source path", envelope["forbidden_mutations"])
        self.assertIn("set dashboardEvidenceReady", envelope["forbidden_mutations"])

    def test_screen2_runtime_scope_contract_explains_control_state_without_mutation(self) -> None:
        allowed = self.contract.RUNTIME_EXPLANATION_ALLOWED_SCOPES["screen_2"]
        forbidden = self.contract.RUNTIME_EXPLANATION_FORBIDDEN_MUTATIONS["screen_2"]

        for phrase in (
            "existing platform evidence meaning",
            "runtime options inventory meaning",
            "selected run/report/scope meaning",
            "snapshot/window context meaning",
            "Target A meaning",
            "Target B meaning",
            "comparison readiness versus comparison result",
            "request/result receipt meaning",
            "accepted/rejected/blocked/recorded result meaning",
            "request receipt versus execution",
            "backend-returned request/audit reference meaning",
            "validation failure meaning",
            "cached state is not authoritative truth",
            "downstream Screen 3 analysis context",
            "downstream Screen 4 comparison review handoff",
            "deterministic analysis separation",
        ):
            with self.subTest(allowed=phrase):
                self.assertIn(phrase, allowed)

        for phrase in (
            "select existing evidence",
            "select DB/report row",
            "load runtime options outside governed backend service",
            "choose runtime scope",
            "choose snapshot/window context",
            "assign Target A/B",
            "decide comparison readiness",
            "set dashboardEvidenceReady",
            "unlock downstream screens",
            "execute analysis",
            "execute comparison",
            "compare evidence",
            "perform comparison outcome analysis",
            "create deterministic comparison output",
            "create comparison result",
            "compute comparison result",
            "decide comparison result",
            "decide improvement/degradation",
            "generate comparative recommendation truth",
            "render comparison violin diagrams",
            "change evidence values",
            "change thresholds",
            "change action/outcome truth",
            "create hidden DB writes",
            "create hidden workflow records",
            "create hidden governance/audit records",
            "create hidden audit references",
            "invent request ids",
            "invent audit references",
            "claim request persisted without backend response",
            "claim analysis executed without governed output",
            "claim comparison executed without deterministic comparison output",
            "claim new output artifact without governed reference",
            "change future-run behavior",
        ):
            with self.subTest(forbidden=phrase):
                self.assertIn(phrase, forbidden)

    def test_screen2_runtime_scope_contract_uses_service_truth_without_mutation(self) -> None:
        envelope = self.contract.build_runtime_explanation_contract(
            "screen_2",
            truth_source="governed_workflow_service_response",
            provider_mode="mock",
        )

        self.assertEqual(
            envelope["screen_role"],
            "Screen 2 - Runtime Scope & Analysis Control",
        )
        self.assertEqual(envelope["truth_source"], "governed_workflow_service_response")
        self.assertEqual(envelope["truth_source_authority"], "governed_service_result")
        self.assertTrue(envelope["non_mutating_explanation_only"])
        self.assertFalse(envelope["records_created_expected"])
        self.assertIsNone(envelope["audit_reference_expected"])
        self.assertIn("runtime options inventory meaning", envelope["allowed_explanation_scope"])
        self.assertIn("request/result receipt meaning", envelope["allowed_explanation_scope"])
        self.assertIn("choose runtime scope", envelope["forbidden_mutations"])
        self.assertIn("decide improvement/degradation", envelope["forbidden_mutations"])

    def test_screens3_through6_scopes_are_screen_specific_and_non_mutating(self) -> None:
        expected = {
            "screen_3": {
                "allowed": (
                    "already-computed deterministic Phase 4 analysis",
                    "OK/LOW confidence/TUNE FIRST meaning",
                    "mixed-signal interpretation",
                    "Target A individual diagnostic context",
                    "Target B individual diagnostic context",
                    "selected target individual diagnostic output only",
                    "Screen 4 comparison review handoff",
                ),
                "forbidden": (
                    "compare Target A vs Target B",
                    "decide improvement/degradation",
                    "decide which target is better",
                    "assign comparison readiness",
                    "compute comparison result",
                    "render comparison violin panels",
                    "change diagnosis based on comparison",
                    "overwrite target deterministic truth",
                    "generate comparative recommendation truth",
                    "create DB/governance/audit records",
                ),
            },
            "screen_4": {
                "allowed": (
                    "governed comparison evidence meaning",
                    "future deterministic comparison violin meaning",
                    "why evidence supports or does not support deterministic diagnosis",
                    "historical and similarity context as advisory evidence context",
                ),
                "forbidden": (
                    "change trend values",
                    "change anomaly classification",
                    "change similarity result",
                    "change comparison result",
                    "create comparison outputs",
                    "persist comparison outputs",
                ),
            },
            "screen_5": {
                "allowed": (
                    "deterministic recommendation meaning",
                    "action priority/owner/status meaning",
                    "governed action request meaning",
                    "outcome capture meaning",
                    "post-action evidence context",
                ),
                "forbidden": (
                    "generate new recommendation truth",
                    "mark action complete",
                    "record outcome",
                    "change owner/status truth",
                    "change validation checklist result",
                ),
            },
            "screen_6": {
                "allowed": (
                    "learning governance",
                    "why candidate review is required",
                    "materialization meaning",
                    "runtime eligibility meaning",
                    "why materialization and runtime eligibility are separate",
                    "why future-run behavior requires explicit governed activation",
                ),
                "forbidden": (
                    "accept or reject candidates",
                    "create learning candidates",
                    "materialize candidates",
                    "activate runtime eligibility",
                    "change model registry state",
                    "activate models",
                    "change future-run behavior",
                ),
            },
        }

        for screen_id, checks in expected.items():
            allowed = self.contract.RUNTIME_EXPLANATION_ALLOWED_SCOPES[screen_id]
            forbidden = self.contract.RUNTIME_EXPLANATION_FORBIDDEN_MUTATIONS[screen_id]
            with self.subTest(screen_id=screen_id, boundary="scope"):
                for phrase in checks["allowed"]:
                    self.assertIn(phrase, allowed)
                for phrase in checks["forbidden"]:
                    self.assertIn(phrase, forbidden)

    def test_screens3_through6_payload_validation_rejects_truth_mutation_fields(self) -> None:
        validate = self.contract.validate_runtime_explanation_payload
        payload = {
            "request_type": "runtime_explanation",
            "provider_mode": "mock",
            "non_mutating_explanation_only": True,
        }
        forbidden_by_screen = {
            "screen_3": (
                "comparison_outcome_decision",
                "improvement_degradation_decision",
                "target_assignment",
                "diagnosis_update",
                "recommendation_update",
            ),
            "screen_4": (
                "comparison_output_creation",
                "comparison_violin_generation",
                "comparison_outcome_decision",
                "evidence_update",
                "score_update",
            ),
            "screen_5": (
                "recommendation_update",
                "action_state_update",
                "outcome_state_update",
                "owner_status_update",
                "validation_result_update",
            ),
            "screen_6": (
                "candidate_acceptance",
                "candidate_rejection",
                "learning_candidate_action",
                "materialization_action",
                "runtime_eligibility_action",
                "model_registry_update",
                "model_activation_action",
            ),
        }

        for screen_id, fields in forbidden_by_screen.items():
            safe_payload = {**payload, "screen_id": screen_id}
            self.assertEqual(validate(safe_payload, expected_screen_id=screen_id), "")
            for field in fields:
                with self.subTest(screen_id=screen_id, field=field):
                    self.assertIn(
                        "mutation/workflow fields",
                        validate({**safe_payload, field: True}, expected_screen_id=screen_id),
                    )

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

    def test_home_payload_validation_rejects_source_runtime_and_readiness_mutation_fields(self) -> None:
        validate = self.contract.validate_runtime_explanation_payload
        payload = {
            "screen_id": "index_source_mode",
            "request_type": "home_source_path_explanation",
            "provider_mode": "mock",
            "non_mutating_explanation_only": True,
        }

        self.assertEqual(validate(payload, expected_screen_id="index_source_mode"), "")
        for field in (
            "source_selection_update",
            "source_validation_update",
            "source_load",
            "parse_action",
            "runtime_options_load",
            "existing_run_selection",
            "runtime_scope_selection",
            "target_assignment",
            "comparison_readiness_decision",
            "dashboardEvidenceReady_update",
            "analysis_action",
            "comparison_action",
            "action_type",
        ):
            with self.subTest(field=field):
                self.assertIn(
                    "mutation/workflow fields",
                    validate({**payload, field: True}, expected_screen_id="index_source_mode"),
                )

    def test_screen2_payload_validation_rejects_runtime_control_mutation_fields(self) -> None:
        validate = self.contract.validate_runtime_explanation_payload
        payload = {
            "screen_id": "screen_2",
            "request_type": "screen2_runtime_scope_explanation",
            "provider_mode": "mock",
            "non_mutating_explanation_only": True,
        }

        self.assertEqual(validate(payload, expected_screen_id="screen_2"), "")
        for field in (
            "existing_run_selection",
            "db_report_row_selection",
            "runtime_options_load",
            "runtime_scope_selection",
            "snapshot_window_selection",
            "target_assignment",
            "comparison_readiness_decision",
            "comparison_action",
            "comparison_outcome_decision",
            "improvement_degradation_decision",
            "analysis_action",
            "readiness_update",
            "dashboardEvidenceReady_update",
            "evidence_update",
            "threshold_update",
            "action_outcome_update",
            "materialization_action",
            "runtime_eligibility_action",
            "downstream_unlock",
            "hidden_db_write",
            "hidden_workflow_record",
            "hidden_governance_record",
            "hidden_audit_record",
            "action_type",
        ):
            with self.subTest(field=field):
                self.assertIn(
                    "mutation/workflow fields",
                    validate({**payload, field: True}, expected_screen_id="screen_2"),
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
            "The LLM selected the source path.",
            "The explanation loaded evidence.",
            "The provider parsed AWR content.",
            "The provider loaded runtime options.",
            "The explanation selected existing run context.",
            "The explanation selected existing evidence.",
            "The wording selected DB/report row context.",
            "The provider selected snapshot/window context.",
            "The explanation performed deterministic analysis.",
            "Screen 2 executed analysis.",
            "Screen 2 executed comparison.",
            "Analyze executed.",
            "Re-run executed.",
            "Build Comparison computed.",
            "The comparison result was computed.",
            "Improvement was decided.",
            "Degradation was decided.",
            "Diagnosis was changed by request.",
            "Recommendation was changed by request.",
            "Parser output was changed by request.",
            "Runtime eligibility was activated by request.",
            "Future-run behavior was changed by request.",
            "Request ID was created by browser.",
            "Audit reference was created by browser.",
            "Records were created by wording.",
            "The provider compared evidence.",
            "The provider computed comparison result.",
            "The provider created comparison result.",
            "The provider decided comparison result.",
            "Screen 3 compares Target A and Target B.",
            "Screen 3 decided improvement.",
            "Screen 3 decided degradation.",
            "Screen 3 computes comparison result.",
            "Screen 3 renders comparison violin panels.",
            "Screen 3 assigns comparison readiness.",
            "The LLM compared Target A.",
            "The LLM compared Target B.",
            "The LLM decided improvement.",
            "The LLM decided degradation.",
            "The LLM changed diagnosis from comparison.",
            "The explanation unlocked downstream screens.",
            "The explanation set dashboardEvidenceReady.",
            "The provider decided improvement from comparison.",
            "The provider decided degradation from comparison.",
            "The explanation changed action/outcome truth.",
            "The explanation changed action state.",
            "The explanation recorded outcome.",
            "The explanation changed validation result.",
            "The provider generated new recommendation truth.",
            "The provider generated comparative recommendation truth.",
            "The explanation created comparison output.",
            "The explanation persisted comparison output.",
            "The provider generated comparison violin output.",
            "The explanation rendered comparison violin.",
            "The explanation created hidden DB write.",
            "The explanation created hidden audit record.",
            "The provider approved parser mapping.",
            "The explanation rejected the parser mapping.",
            "The wording mapped the parser candidate.",
            "The explanation created scoring features.",
            "The provider assigned diagnostic domains.",
            "The explanation changed artifact readiness.",
            "The explanation created learning candidate.",
            "This explanation activated runtime eligibility.",
            "The provider materialized candidates.",
            "The provider activated the model.",
            "The provider changed model registry state.",
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
