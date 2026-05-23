#!/usr/bin/env python3
"""Run the local governed dashboard workflow service."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.learning.dashboard_runtime_interaction import (
    load_screen3_runtime_options,
    lookup_existing_runs,
    process_dashboard_action,
    validate_object_storage_source,
)


ENDPOINT_PATH = "/phase7/dashboard/actions"
EXISTING_RUNS_ENDPOINT_PATH = "/phase7/dashboard/existing-runs"
SCREEN3_OPTIONS_ENDPOINT_PATH = "/phase7/dashboard/screen3/options"
OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH = "/phase7/dashboard/object-storage/validate"
SCREEN2_EXPLANATION_ENDPOINT_PATH = "/phase7/dashboard/screen2/explanation"
HEALTH_ENDPOINT_PATH = "/phase7/dashboard/health"
SCREEN2_EXPLANATION_PROVIDER_MODES = frozenset({"off", "mock", "local", "oci"})
SUPPORTED_ENDPOINT_PATHS = (
    ENDPOINT_PATH,
    EXISTING_RUNS_ENDPOINT_PATH,
    SCREEN3_OPTIONS_ENDPOINT_PATH,
    OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH,
    SCREEN2_EXPLANATION_ENDPOINT_PATH,
    HEALTH_ENDPOINT_PATH,
)
SCREEN2_EXPLANATION_FORBIDDEN_FIELDS = frozenset(
    {
        "action_type",
        "workflow_type",
        "audit_record",
        "audit_path",
        "audit_id",
        "request_id",
        "governance_record",
        "review_record",
        "feedback_record",
        "diagnosis_update",
        "primary_issue_update",
        "score_update",
        "severity_update",
        "confidence_update",
        "recommendation_update",
        "parser_mutation",
        "runtime_action",
        "runtime_execution",
        "materialization_action",
        "runtime_eligibility_action",
        "learning_candidate_action",
        "future_run_behavior_action",
        "create_audit_record",
        "create_review_record",
        "create_governance_record",
        "create_feedback_record",
        "create_learning_candidate",
        "create_materialization_candidate",
        "create_runtime_eligibility_record",
    }
)


class DashboardWorkflowHTTPServer(ThreadingHTTPServer):
    """Threaded local HTTP server with address reuse for dashboard restarts."""

    allow_reuse_address = True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local governed dashboard action service.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--queue-dir",
        default="",
        help="Optional directory for queued governed dashboard action records.",
    )
    return parser


class Phase7DashboardWorkflowHandler(BaseHTTPRequestHandler):
    """Small JSON-only local handler for governed dashboard action requests."""

    server_version = "DashboardWorkflowService"

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib handler naming
        self._send_json({"status": "ok"}, status_code=204)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler naming
        if self.path != HEALTH_ENDPOINT_PATH:
            self._send_json(
                {
                    "status": "rejected",
                    "message": "Dashboard workflow service route is unavailable.",
                },
                status_code=404,
            )
            return
        self._send_json(self._health_payload(), status_code=200)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler naming
        if self.path not in SUPPORTED_ENDPOINT_PATHS:
            self._send_json(
                {
                    "status": "rejected",
                    "message": "Dashboard workflow service route is unavailable.",
                },
                status_code=404,
            )
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            length = 0
        if length <= 0 or length > 128 * 1024:
            self._send_json(
                {
                    "status": "rejected",
                    "message": "Request body size is invalid for this source-intake workflow.",
                },
                status_code=400,
            )
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(
                {
                    "status": "rejected",
                    "message": "Request body must be valid JSON.",
                },
                status_code=400,
            )
            return
        if not isinstance(payload, dict):
            self._send_json(
                {
                    "status": "rejected",
                    "message": "Request body must be a JSON object.",
                },
                status_code=400,
            )
            return
        queue_dir = getattr(self.server, "phase7_queue_dir", None)
        if self.path == EXISTING_RUNS_ENDPOINT_PATH:
            connection_factory = getattr(
                self.server,
                "phase7_existing_run_connection_factory",
                None,
            )
            result_payload = lookup_existing_runs(
                payload,
                queue_dir=queue_dir,
                connection_factory=connection_factory,
            )
            status_code = 202 if result_payload.get("status") == "accepted" else 400
            if result_payload.get("status") == "pending":
                status_code = 503
            self._send_json(result_payload, status_code=status_code)
            return
        if self.path == SCREEN3_OPTIONS_ENDPOINT_PATH:
            connection_factory = getattr(
                self.server,
                "phase7_screen3_options_connection_factory",
                None,
            ) or getattr(
                self.server,
                "phase7_existing_run_connection_factory",
                None,
            )
            result_payload = load_screen3_runtime_options(
                payload,
                queue_dir=queue_dir,
                connection_factory=connection_factory,
            )
            status_code = 202 if result_payload.get("status") == "accepted" else 400
            if result_payload.get("status") == "pending":
                status_code = 503
            self._send_json(result_payload, status_code=status_code)
            return
        if self.path == OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH:
            result_payload = validate_object_storage_source(payload, queue_dir=queue_dir)
            status_code = 202 if result_payload.get("status") == "accepted" else 400
            self._send_json(result_payload, status_code=status_code)
            return
        if self.path == SCREEN2_EXPLANATION_ENDPOINT_PATH:
            result_payload = generate_screen2_explanation(payload)
            status_code = int(result_payload.pop("_http_status", 200))
            self._send_json(result_payload, status_code=status_code)
            return
        governance_connection_factory = getattr(
            self.server,
            "phase7_governance_connection_factory",
            None,
        )
        result = process_dashboard_action(
            payload,
            queue_dir=queue_dir,
            connection_factory=governance_connection_factory,
            db_persistence_enabled=True,
        )
        status_code = 202 if result.status in {"accepted", "blocked", "completed"} else 400
        self._send_json(result.to_dict(), status_code=status_code)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write("dashboard-workflow-service: " + format % args + "\n")

    def _send_json(self, payload: dict[str, Any], *, status_code: int) -> None:
        body = b"" if status_code == 204 else json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _health_payload(self) -> dict[str, Any]:
        host, port = self.server.server_address[:2]
        provider_mode = _default_screen2_provider_mode()
        return {
            "status": "ok",
            "service": "dashboard_workflow_service",
            "host": host,
            "port": port,
            "base_url": f"http://{host}:{port}",
            "supported_endpoints": list(SUPPORTED_ENDPOINT_PATHS),
            "supported_provider_modes": sorted(SCREEN2_EXPLANATION_PROVIDER_MODES),
            "screen2_explanation_provider_mode": provider_mode,
            "db_connectivity_status": "not_checked",
            "mutates_runtime_truth": False,
            "creates_screen2_records": False,
        }


def _default_screen2_provider_mode() -> str:
    for key in (
        "PHASE7_SCREEN2_EXPLANATION_PROVIDER_MODE",
        "SCREEN2_EXPLANATION_PROVIDER_MODE",
        "AI_PROVIDER",
    ):
        value = str(os.environ.get(key, "") or "").strip().lower()
        if value in SCREEN2_EXPLANATION_PROVIDER_MODES:
            return value
        if key == "AI_PROVIDER" and value in {"oracle", "oci-genai", "oci_genai"}:
            return "oci"
    return "off"


def generate_screen2_explanation(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate Screen 2 wording only; never create workflow/audit/governance records."""

    validation_error = _validate_screen2_explanation_payload(payload)
    if validation_error:
        return {
            "status": "rejected",
            "message": validation_error,
            "records_created": False,
            "audit_reference": None,
            "_http_status": 400,
        }

    provider_mode = str(payload.get("provider_mode") or "off").strip().lower()
    if provider_mode == "off":
        return {
            "status": "provider_off",
            "provider_mode": "off",
            "message": "Explanation generation is disabled for this run. The deterministic explanation remains available.",
            "explanation": "",
            "records_created": False,
            "audit_reference": None,
            "_http_status": 200,
        }
    if provider_mode in {"mock", "local"}:
        return {
            "status": "generated",
            "provider_mode": provider_mode,
            "message": (
                "Mock explanation generated from deterministic context. "
                if provider_mode == "mock"
                else "Local placeholder explanation generated from deterministic context. "
            )
            + "Deterministic values remain unchanged.",
            "explanation": _screen2_canned_explanation(payload, provider_mode=provider_mode),
            "records_created": False,
            "audit_reference": None,
            "_http_status": 200,
        }
    if provider_mode == "oci":
        try:
            from src.analysis.ai_provider_adapter import generate_ai_response

            result = generate_ai_response(
                "oci",
                _screen2_explanation_system_role(),
                _screen2_explanation_prompt(payload),
                ["Focused diagnostic explanation"],
            )
            explanation = _sanitize_screen2_provider_text(str(result.get("content") or ""))
        except Exception:
            return {
                "status": "provider_failed",
                "provider_mode": "oci",
                "message": "OCI GenAI explanation request failed. The deterministic explanation remains available.",
                "explanation": "",
                "records_created": False,
                "audit_reference": None,
                "_http_status": 502,
            }
        if not explanation or _screen2_explanation_violates_boundary(explanation):
            return {
                "status": "provider_rejected",
                "provider_mode": "oci",
                "message": (
                    "OCI GenAI returned wording that was empty or conflicted with Screen 2 boundaries. "
                    "The deterministic explanation remains available."
                ),
                "explanation": "",
                "records_created": False,
                "audit_reference": None,
                "_http_status": 502,
            }
        return {
            "status": "generated",
            "provider_mode": "oci",
            "message": "OCI GenAI explanation generated server-side. Deterministic values remain unchanged.",
            "explanation": explanation,
            "records_created": False,
            "audit_reference": None,
            "_http_status": 200,
        }
    return {
        "status": "rejected",
        "message": "Unsupported Screen 2 explanation provider mode.",
        "records_created": False,
        "audit_reference": None,
        "_http_status": 400,
    }


def _validate_screen2_explanation_payload(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return "Screen 2 explanation request must be a JSON object."
    if payload.get("screen_id") != "screen_2":
        return "Screen 2 explanation request must use screen_id=screen_2."
    if payload.get("non_mutating_explanation_only") is not True:
        return "Screen 2 explanation request must be marked non-mutating."
    provider_mode = str(payload.get("provider_mode") or "off").strip().lower()
    if provider_mode not in SCREEN2_EXPLANATION_PROVIDER_MODES:
        return "Unsupported Screen 2 explanation provider mode."
    present_forbidden = sorted(key for key in SCREEN2_EXPLANATION_FORBIDDEN_FIELDS if key in payload)
    if present_forbidden:
        return "Screen 2 explanation request cannot include mutation/workflow fields: " + ", ".join(
            present_forbidden
        )
    for key in (
        "selected_focus",
        "target_type",
        "decision_posture",
        "primary_issue_domain",
        "severity",
        "confidence",
    ):
        if not str(payload.get(key) or "").strip():
            return f"Screen 2 explanation request is missing {key}."
    if not str(payload.get("deterministic_facts") or "").strip():
        return "Screen 2 explanation request must include deterministic facts."
    return ""


def _screen2_canned_explanation(payload: dict[str, Any], *, provider_mode: str) -> str:
    selected_focus = str(payload.get("selected_focus") or "overall deterministic result").strip()
    target_type = str(payload.get("target_type") or "explanation_focus").strip()
    inferred_domain = str(payload.get("inferred_domain") or "Not domain-specific").strip()
    posture = str(payload.get("decision_posture") or "TUNE FIRST").strip()
    primary_issue = str(payload.get("primary_issue_domain") or "No dominant scored domain selected").strip()
    confidence = str(payload.get("confidence") or "LOW").strip()
    facts = str(payload.get("deterministic_facts") or "deterministic evidence context").strip()
    mode_label = provider_mode.upper()
    return (
        f"{mode_label} explanation: {selected_focus} is the active Screen 2 explanation focus "
        f"({target_type}; inferred domain: {inferred_domain}). Deterministic facts used: {facts}. "
        f"The decision posture remains {posture}, confidence remains {confidence}, and primary issue/domain remains "
        f"{primary_issue}. Diagnosis, score, confidence, recommendation, parser output, runtime behavior, ML behavior, "
        f"learning candidates, materialization, runtime eligibility, future-run behavior, evidence values, thresholds, "
        f"and DB/governance/audit state are unchanged."
    )


def _screen2_explanation_system_role() -> str:
    return (
        "You write concise operator-facing Oracle AWR diagnostic explanation text. "
        "The deterministic engine decides. You explain already-decided Screen 2 diagnostic meaning only. "
        "Return plain text only, with no Markdown headings, no bullets, and no leading # characters."
    )


def _screen2_explanation_prompt(payload: dict[str, Any]) -> str:
    return (
        "Generate one concise plain-text paragraph for the Screen 2 Focused Diagnostic Meaning panel. "
        "Do not use Markdown, heading markers, bullet lists, or leading # characters.\n"
        "Use only these deterministic values:\n"
        f"- Active explanation focus: {payload.get('selected_focus')}\n"
        f"- Target type: {payload.get('target_type')}\n"
        f"- Inferred domain: {payload.get('inferred_domain')}\n"
        f"- Decision posture: {payload.get('decision_posture')}\n"
        f"- Primary issue/domain: {payload.get('primary_issue_domain')}\n"
        f"- Severity: {payload.get('severity')}\n"
        f"- Confidence: {payload.get('confidence')}\n"
        f"- Deterministic facts: {payload.get('deterministic_facts')}\n\n"
        "Boundary: Screen 2 selection and Generate Focused Explanation change only local selected focus and displayed "
        "explanation wording. Do not say or imply that diagnosis, primary issue/domain, score, severity, confidence, "
        "recommendation, parser output, runtime behavior, ML behavior, learning candidates, materialization, runtime "
        "eligibility, future-run behavior, evidence values, thresholds, or DB/governance/audit state changed. "
        "Do not mention threshold status unless a threshold value is provided. Do not describe runtime eligibility "
        "except to say that Screen 2 does not change it."
    )


def _sanitize_screen2_provider_text(value: str) -> str:
    lines = []
    for raw_line in value.replace("<", "").replace(">", "").splitlines():
        line = raw_line.strip()
        while line.startswith("#"):
            line = line[1:].lstrip()
        lines.append(line)
    return " ".join(" ".join(lines).split())[:2000]


def _screen2_explanation_violates_boundary(explanation: str) -> bool:
    lowered = explanation.lower()
    unsafe_markers = (
        "changed the diagnosis",
        "changes the diagnosis",
        "updated the diagnosis",
        "updates the diagnosis",
        "changed the score",
        "changes the score",
        "updated the score",
        "updates the score",
        "changed confidence",
        "updates confidence",
        "updated the recommendation",
        "changes the recommendation",
        "runtime behavior changed",
        "changes runtime behavior",
        "materialized",
        "runtime eligible",
        "normal runtime eligibility",
        "runtime eligibility aligns",
        "runtime eligibility is normal",
        "created audit",
        "created governance",
        "created review",
        "trained the model",
        "future runs will",
        "below concern threshold",
        "below concern thresholds",
        "above concern threshold",
        "above concern thresholds",
    )
    return any(marker in lowered for marker in unsafe_markers)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    queue_dir = Path(args.queue_dir).expanduser().resolve() if args.queue_dir else None
    server = DashboardWorkflowHTTPServer(
        (args.host, args.port),
        Phase7DashboardWorkflowHandler,
    )
    server.phase7_queue_dir = queue_dir
    print(
        f"Governed dashboard workflow service listening on "
        f"http://{args.host}:{args.port}{ENDPOINT_PATH}"
    )
    print(f"Existing run lookup endpoint: http://{args.host}:{args.port}{EXISTING_RUNS_ENDPOINT_PATH}")
    print(f"Object Storage validation endpoint: http://{args.host}:{args.port}{OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH}")
    print(f"Screen 2 explanation endpoint: http://{args.host}:{args.port}{SCREEN2_EXPLANATION_ENDPOINT_PATH}")
    print(f"Health endpoint: http://{args.host}:{args.port}{HEALTH_ENDPOINT_PATH}")
    print("This service queues governed request records only; it does not mutate Phase 4I or runtime truth.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard workflow service stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
