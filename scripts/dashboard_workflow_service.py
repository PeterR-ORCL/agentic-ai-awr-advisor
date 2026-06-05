#!/usr/bin/env python3
"""Run the local governed dashboard workflow service."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlsplit
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.dashboard_runtime_explanation_contract import (
    RUNTIME_EXPLANATION_GLOBAL_FORBIDDEN_FIELDS,
    RUNTIME_EXPLANATION_PROVIDER_MODES,
    normalize_runtime_explanation_provider_mode,
    normalize_runtime_explanation_response,
    runtime_explanation_violates_boundary,
    validate_runtime_explanation_payload,
)
from src.learning.dashboard_runtime_interaction import (
    DASHBOARD_RUNTIME_ACTION_TYPES,
    SCREEN_REQUIRED_ACTION_TYPES,
    default_action_queue_dir,
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
SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_ENDPOINT_PATH = (
    "/phase7/dashboard/screen3/evidence-context/explanation"
)
HEALTH_ENDPOINT_PATH = "/phase7/dashboard/health"
ACTION_STATUS_ENDPOINT_PATH = "/phase7/dashboard/actions/status"
SCREEN2_EXPLANATION_PROVIDER_MODES = RUNTIME_EXPLANATION_PROVIDER_MODES
SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_PROVIDER_MODES = RUNTIME_EXPLANATION_PROVIDER_MODES
SUPPORTED_ENDPOINT_PATHS = (
    ENDPOINT_PATH,
    EXISTING_RUNS_ENDPOINT_PATH,
    SCREEN3_OPTIONS_ENDPOINT_PATH,
    OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH,
    SCREEN2_EXPLANATION_ENDPOINT_PATH,
    SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_ENDPOINT_PATH,
    HEALTH_ENDPOINT_PATH,
    ACTION_STATUS_ENDPOINT_PATH,
)
SCREEN2_EXPLANATION_FORBIDDEN_FIELDS = RUNTIME_EXPLANATION_GLOBAL_FORBIDDEN_FIELDS
SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_FORBIDDEN_FIELDS = (
    RUNTIME_EXPLANATION_GLOBAL_FORBIDDEN_FIELDS
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
        parsed = urlsplit(self.path)
        if parsed.path == HEALTH_ENDPOINT_PATH:
            self._send_json(self._health_payload(), status_code=200)
            return
        if parsed.path == ACTION_STATUS_ENDPOINT_PATH:
            queue_dir = getattr(self.server, "phase7_queue_dir", None)
            result_payload, status_code = screen1_source_intake_status_payload(
                parse_qs(parsed.query),
                queue_dir=queue_dir,
            )
            self._send_json(result_payload, status_code=status_code)
            return
        if parsed.path != HEALTH_ENDPOINT_PATH:
            self._send_json(
                {
                    "status": "rejected",
                    "message": "Dashboard workflow service route is unavailable.",
                },
                status_code=404,
            )
            return

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
        if self.path == SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_ENDPOINT_PATH:
            result_payload = generate_screen3_evidence_context_explanation(payload)
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
            source_intake_executor=lambda request: start_screen1_source_intake_execution(
                request,
                queue_dir=queue_dir,
            ),
        )
        status_code = (
            202
            if result.status in {
                "accepted",
                "blocked",
                "completed",
                "completed_artifact_ready",
                "pending",
                "running",
            }
            else 400
        )
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
        screen3_provider_mode = _default_screen3_evidence_context_provider_mode()
        return {
            "status": "ok",
            "service": "dashboard_workflow_service",
            "host": host,
            "port": port,
            "base_url": f"http://{host}:{port}",
            "supported_endpoints": list(SUPPORTED_ENDPOINT_PATHS),
            "screen1_source_intake_status_endpoint": ACTION_STATUS_ENDPOINT_PATH,
            "supported_action_types": list(DASHBOARD_RUNTIME_ACTION_TYPES),
            "supported_screen_action_types": {
                screen_id: list(action_types)
                for screen_id, action_types in SCREEN_REQUIRED_ACTION_TYPES.items()
            },
            "supported_provider_modes": sorted(SCREEN2_EXPLANATION_PROVIDER_MODES),
            "screen2_explanation_provider_mode": provider_mode,
            "screen3_evidence_context_explanation_provider_mode": screen3_provider_mode,
            "db_connectivity_status": "not_checked",
            "mutates_runtime_truth": False,
            "creates_screen2_records": False,
            "creates_screen3_evidence_context_records": False,
        }


def screen1_source_intake_status_payload(
    query: dict[str, list[str]],
    *,
    queue_dir: Path | None,
) -> tuple[dict[str, Any], int]:
    request_id = str((query.get("request_id") or [""])[0] or "").strip()
    if not request_id:
        return {
            "status": "rejected",
            "message": "request_id query parameter is required.",
            "artifact_ready": False,
        }, 400
    target_dir = _screen1_queue_dir(queue_dir)
    status_path = _screen1_status_path(target_dir, request_id)
    if status_path.exists():
        try:
            payload = json.loads(status_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {
                "status": "failed_safely",
                "request_id": request_id,
                "message": "Screen 1 source intake status file could not be read safely.",
                "artifact_ready": False,
            }, 500
        return payload, 200
    audit_path = _screen1_audit_path(target_dir, request_id)
    if audit_path.exists():
        return {
            "status": "running",
            "request_id": request_id,
            "audit_reference": str(audit_path),
            "message": (
                "Screen 1 source intake request was recorded; backend status "
                "is not available yet."
            ),
            "artifact_ready": False,
            "source_summary": {
                "artifact_ready": False,
                "execution_status": "running",
                "screen1GeneratedArtifactReady": False,
                "screen1GeneratedRunExecuted": False,
                "screen1SelectedGeneratedArtifactReady": False,
            },
        }, 202
    return {
        "status": "failed_safely",
        "request_id": request_id,
        "message": "No Screen 1 source intake request/status record was found for this request_id.",
        "artifact_ready": False,
        "source_summary": {
            "artifact_ready": False,
            "execution_status": "failed_safely",
            "screen1GeneratedArtifactReady": False,
            "screen1GeneratedRunExecuted": False,
            "screen1SelectedGeneratedArtifactReady": False,
        },
    }, 404


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


def _default_screen3_evidence_context_provider_mode() -> str:
    for key in (
        "PHASE7_SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_PROVIDER_MODE",
        "SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_PROVIDER_MODE",
    ):
        value = str(os.environ.get(key, "") or "").strip().lower()
        if value in SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_PROVIDER_MODES:
            return value
    return _default_screen2_provider_mode()


def start_screen1_source_intake_execution(
    request: Any,
    *,
    queue_dir: Path | None,
) -> dict[str, Any]:
    """Start governed local Screen 1 source intake and return a pollable running state."""

    target_dir = _screen1_queue_dir(queue_dir)
    request_id = str(getattr(request, "request_id", "") or "screen1-source-intake")
    audit_path = _screen1_audit_path(target_dir, request_id)
    status_path = _screen1_status_path(target_dir, request_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    running_payload = _screen1_source_intake_status_response(
        request,
        {
            "status": "running",
            "execution_status": "running",
            "artifact_ready": False,
            "runner_invoked": False,
            "message": (
                "Source intake request accepted. Backend intake/generation is "
                "running. Keep this page open; status will update automatically."
            ),
        },
        audit_path=audit_path,
    )
    _write_json(status_path, running_payload)
    worker = threading.Thread(
        target=_screen1_source_intake_worker,
        args=(request, audit_path, status_path),
        name=f"screen1-source-intake-{_safe_status_filename(request_id)[:48]}",
        daemon=True,
    )
    worker.start()
    return {
        "status": "running",
        "execution_status": "running",
        "artifact_ready": False,
        "runner_invoked": False,
        "request_status_endpoint": ACTION_STATUS_ENDPOINT_PATH,
        "message": running_payload["message"],
        "audit_reference": str(audit_path),
    }


def _screen1_source_intake_worker(
    request: Any,
    audit_path: Path,
    status_path: Path,
) -> None:
    result = run_screen1_source_intake_execution(request)
    status_payload = _screen1_source_intake_status_response(
        request,
        result,
        audit_path=audit_path,
    )
    _write_json(status_path, status_payload)
    _update_screen1_source_intake_audit(audit_path, result)


def run_screen1_source_intake_execution(request: Any) -> dict[str, Any]:
    """Run governed local Screen 1 source intake through the backend generator."""

    payload = getattr(request, "payload", {}) or {}
    mode = str(payload.get("selectedSourceMode") or payload.get("source_mode") or "").strip()
    if mode != "local_staged":
        if mode == "local_file":
            message = (
                "Local file source intake is metadata/path validation only until "
                "a governed upload or staging path is configured. No browser file "
                "read, upload, parse, or generated artifact readiness was claimed."
            )
        elif mode == "object_storage":
            message = (
                "Object Storage source intake is metadata-validation only until "
                "a governed backend load-to-staging and parser chain exists. "
                "No OCI object was read and no generated artifact readiness was claimed."
            )
        else:
            message = (
                "Screen 1 source intake execution currently supports local folder "
                "sources only. Unsupported or Screen 2-owned source modes fail safely."
            )
        return {
            "status": "failed_safely",
            "execution_status": "failed_safely",
            "artifact_ready": False,
            "runner_invoked": False,
            "message": message,
        }

    source_path = str(payload.get("selectedSourcePath") or "").strip()
    if not source_path:
        return {
            "status": "failed_safely",
            "execution_status": "failed_safely",
            "artifact_ready": False,
            "runner_invoked": False,
            "message": (
                "Backend intake execution requires a backend-visible local folder "
                "path. Browser folder metadata alone is not sufficient."
            ),
        }
    input_dir = Path(source_path).expanduser()
    if not input_dir.is_absolute():
        input_dir = (ROOT / input_dir).resolve()
    else:
        input_dir = input_dir.resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        return {
            "status": "failed_safely",
            "execution_status": "failed_safely",
            "artifact_ready": False,
            "runner_invoked": False,
            "source_input_dir": str(input_dir),
            "message": (
                "Backend intake execution failed safely because the selected "
                f"local folder is not available to the service: {input_dir}"
            ),
        }

    env = os.environ.copy()
    env["PHASE7_DASHBOARD_WORKFLOW_SERVICE_AUTOSTART"] = "false"
    env["AWR_SOURCE_INPUT_DIR"] = str(input_dir)
    env["PYTHONPATH"] = (
        str(ROOT)
        if not env.get("PYTHONPATH")
        else str(ROOT) + os.pathsep + str(env.get("PYTHONPATH"))
    )
    timeout = int(os.getenv("PHASE7_SCREEN1_SOURCE_INTAKE_TIMEOUT", "420"))
    command = [sys.executable, "-m", "scripts.run_analysis"]
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "failed_safely",
            "execution_status": "failed_safely",
            "artifact_ready": False,
            "runner_invoked": True,
            "source_input_dir": str(input_dir),
            "message": (
                "Source intake failed safely because backend generation timed out. "
                "No generated artifact was claimed."
            ),
            "stdout_tail": _tail_text(exc.stdout),
            "stderr_tail": _tail_text(exc.stderr),
        }
    dashboard_path = ROOT / "awr_dashboard" / "index.html"
    if completed.returncode != 0:
        return {
            "status": "failed_safely",
            "execution_status": "failed_safely",
            "artifact_ready": False,
            "runner_invoked": True,
            "source_input_dir": str(input_dir),
            "returncode": completed.returncode,
            "message": (
                "Source intake failed safely because backend generation returned "
                f"exit code {completed.returncode}. No generated artifact was claimed."
            ),
            "stdout_tail": _tail_text(completed.stdout),
            "stderr_tail": _tail_text(completed.stderr),
        }
    return {
        "status": "completed_artifact_ready",
        "execution_status": "completed_artifact_ready",
        "artifact_ready": True,
        "runner_invoked": True,
        "dashboard_regenerated": dashboard_path.exists(),
        "dashboard_artifact_path": str(dashboard_path),
        "source_input_dir": str(input_dir),
        "returncode": completed.returncode,
        "message": "Source intake completed. Generated artifact is ready.",
        "stdout_tail": _tail_text(completed.stdout),
        "stderr_tail": _tail_text(completed.stderr),
    }


def _screen1_source_intake_status_response(
    request: Any,
    execution: dict[str, Any],
    *,
    audit_path: Path,
) -> dict[str, Any]:
    request_id = str(getattr(request, "request_id", "") or "")
    status = str(execution.get("status") or execution.get("execution_status") or "failed_safely")
    artifact_ready = bool(execution.get("artifact_ready")) and status == "completed_artifact_ready"
    source_summary = {
        "execution_status": execution.get("execution_status") or status,
        "backend_execution_status": status,
        "backend_execution_performed": bool(execution.get("runner_invoked")),
        "backend_source_intake_runner_invoked": bool(execution.get("runner_invoked")),
        "artifact_ready": artifact_ready,
        "screen1GeneratedArtifactReady": artifact_ready,
        "screen1GeneratedRunExecuted": artifact_ready,
        "screen1SelectedGeneratedArtifactReady": artifact_ready,
        "dashboard_regenerated": bool(execution.get("dashboard_regenerated")),
        "dashboard_artifact_path": execution.get("dashboard_artifact_path"),
        "source_input_dir": execution.get("source_input_dir")
        or getattr(request, "payload", {}).get("selectedSourcePath"),
        "runner_message": execution.get("message"),
        "runner_returncode": execution.get("returncode"),
        "stdout_tail": execution.get("stdout_tail"),
        "stderr_tail": execution.get("stderr_tail"),
        "current_run_truth_mutated": False,
        "deterministic_truth_changed": False,
        "parser_mutated": False,
        "learning_candidate_created": False,
        "materialization_changed": False,
        "runtime_eligibility_changed": False,
        "phase8_started": False,
        "browser_parsing_performed": False,
        "browser_db_query_attempted": False,
        "browser_file_read_attempted": False,
        "browser_object_storage_access_attempted": False,
    }
    return {
        "status": status,
        "request_id": request_id,
        "audit_reference": str(audit_path),
        "message": execution.get("message")
        or (
            "Source intake completed. Generated artifact is ready."
            if artifact_ready
            else "Source intake status is available."
        ),
        "artifact_ready": artifact_ready,
        "queued": True,
        "persisted": False,
        "run_analysis_called": False,
        "source_summary": source_summary,
    }


def _update_screen1_source_intake_audit(audit_path: Path, execution: dict[str, Any]) -> None:
    try:
        envelope = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(envelope, dict):
        return
    envelope["source_intake_execution"] = execution
    _write_json(audit_path, envelope)


def _screen1_queue_dir(queue_dir: Path | None) -> Path:
    return queue_dir or default_action_queue_dir()


def _safe_status_filename(value: str) -> str:
    normalized = "".join(
        character if character.isalnum() or character in "_.:-" else "-"
        for character in str(value or "").strip()
    ).strip("-")
    return normalized or "screen1-source-intake"


def _screen1_audit_path(queue_dir: Path, request_id: str) -> Path:
    return queue_dir / f"{_safe_status_filename(request_id)}.json"


def _screen1_status_path(queue_dir: Path, request_id: str) -> Path:
    return queue_dir / f"{_safe_status_filename(request_id)}.status.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _tail_text(value: Any, limit: int = 4000) -> str:
    text = str(value or "")
    return text[-limit:]


def generate_screen2_explanation(payload: dict[str, Any]) -> dict[str, Any]:
    """Explain already-computed Screen 3 diagnostic analysis through the legacy Screen 2 route."""

    validation_error = _validate_screen2_explanation_payload(payload)
    if validation_error:
        return normalize_runtime_explanation_response(
            {
                "status": "rejected",
                "message": validation_error,
                "records_created": False,
                "audit_reference": None,
                "_http_status": 400,
            },
            boundary_validation_result="request_rejected",
        )

    provider_mode = normalize_runtime_explanation_provider_mode(payload.get("provider_mode"))
    if provider_mode == "off":
        return normalize_runtime_explanation_response(
            {
                "status": "provider_off",
                "provider_mode": "off",
                "message": "Explanation generation is disabled for this run. The deterministic explanation remains available.",
                "explanation": "",
                "records_created": False,
                "audit_reference": None,
                "_http_status": 200,
            },
            boundary_validation_result="not_applicable",
        )
    if provider_mode in {"mock", "local"}:
        return normalize_runtime_explanation_response(
            {
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
            },
            boundary_validation_result="passed",
        )
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
            return normalize_runtime_explanation_response(
                {
                    "status": "provider_failed",
                    "provider_mode": "oci",
                    "message": "OCI GenAI explanation request failed. The deterministic explanation remains available.",
                    "explanation": "",
                    "records_created": False,
                    "audit_reference": None,
                    "_http_status": 502,
                },
                boundary_validation_result="not_checked",
            )
        if not explanation or _screen2_explanation_violates_boundary(explanation):
            return normalize_runtime_explanation_response(
                {
                    "status": "provider_rejected",
                    "provider_mode": "oci",
                    "message": (
                        "OCI GenAI returned wording that was empty or conflicted with Screen 3 diagnostic boundaries. "
                        "The deterministic explanation remains available."
                    ),
                    "explanation": "",
                    "records_created": False,
                    "audit_reference": None,
                    "_http_status": 502,
                },
                boundary_validation_result="rejected",
            )
        return normalize_runtime_explanation_response(
            {
                "status": "generated",
                "provider_mode": "oci",
                "message": "OCI GenAI explanation generated server-side. Deterministic values remain unchanged.",
                "explanation": explanation,
                "records_created": False,
                "audit_reference": None,
                "_http_status": 200,
            },
            boundary_validation_result="passed",
        )
    return normalize_runtime_explanation_response(
        {
            "status": "rejected",
            "message": "Unsupported Screen 2 explanation provider mode.",
            "records_created": False,
            "audit_reference": None,
            "_http_status": 400,
        },
        boundary_validation_result="request_rejected",
    )


def _validate_screen2_explanation_payload(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return "Screen 2 explanation request must be a JSON object."
    if payload.get("screen_id") != "screen_2":
        return "Screen 2 explanation request must use screen_id=screen_2."
    if payload.get("non_mutating_explanation_only") is not True:
        return "Screen 2 explanation request must be marked non-mutating."
    provider_mode = normalize_runtime_explanation_provider_mode(payload.get("provider_mode"))
    if provider_mode not in SCREEN2_EXPLANATION_PROVIDER_MODES:
        return "Unsupported Screen 2 explanation provider mode."
    present_forbidden = sorted(key for key in SCREEN2_EXPLANATION_FORBIDDEN_FIELDS if key in payload)
    if present_forbidden:
        return "Screen 2 explanation request cannot include mutation/workflow fields: " + ", ".join(
            present_forbidden
        )
    shared_validation_error = validate_runtime_explanation_payload(
        payload,
        expected_screen_id="screen_2",
        forbidden_fields=SCREEN2_EXPLANATION_FORBIDDEN_FIELDS,
    )
    if shared_validation_error == "Runtime explanation request cannot create records.":
        return "Screen 2 explanation request cannot create records."
    if shared_validation_error == "Runtime explanation request cannot provide an audit reference.":
        return "Screen 2 explanation request cannot provide an audit reference."
    if shared_validation_error:
        return shared_validation_error
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
        f"{mode_label} explanation: {selected_focus} is the active Screen 3 diagnostic explanation focus "
        "for already-computed deterministic analysis "
        f"({target_type}; inferred domain: {inferred_domain}). Deterministic facts used: {facts}. "
        f"The decision posture remains {posture}, confidence remains {confidence}, and primary issue/domain remains "
        f"{primary_issue}. Diagnosis, score, confidence, recommendation, parser output, runtime behavior, ML behavior, "
        f"learning candidates, materialization, runtime eligibility, future-run behavior, evidence values, thresholds, "
        f"and DB/governance/audit state are unchanged. If the selected context is Target A or Target B, this wording "
        f"explains that target's individual deterministic diagnostic output only. A-vs-B comparison review belongs "
        f"on Screen 4 after deterministic comparison output exists. This wording-only explanation does not load "
        f"evidence, parse AWR content, compare evidence, select runtime scope, assign Target A/B, decide comparison "
        f"readiness, compute comparison results, render comparison violin panels, or mutate deterministic analysis output."
    )


def _screen2_explanation_system_role() -> str:
    return (
        "You write concise operator-facing Oracle AWR diagnostic explanation text. "
        "The deterministic engine decides. You explain already-computed product Screen 3 deterministic analysis only. "
        "If the selected context is Target A or Target B, explain that target's individual deterministic diagnostic output only. "
        "A-vs-B comparison review and future comparison violin panels belong on Screen 4 after deterministic comparison output exists. "
        "You do not load evidence, parse AWR content, compare evidence, select runtime scope, assign Target A/B, "
        "decide comparison readiness, compute comparison results, render comparison violin panels, or mutate deterministic analysis output. "
        "Return plain text only, with no Markdown headings, no bullets, and no leading # characters."
    )


def _screen2_explanation_prompt(payload: dict[str, Any]) -> str:
    return (
        "Generate one concise plain-text paragraph for the product Screen 3 Focused Diagnostic Meaning panel. "
        "Explain already-computed deterministic analysis only. "
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
        "Boundary: product Screen 3 selection and Generate Focused Explanation change only local selected focus and displayed "
        "explanation wording. Do not say or imply that diagnosis, primary issue/domain, score, severity, confidence, "
        "recommendation, parser output, runtime behavior, ML behavior, learning candidates, materialization, runtime "
        "eligibility, future-run behavior, evidence values, thresholds, or DB/governance/audit state changed. "
        "If the selected context is Target A or Target B, explain that target's individual deterministic diagnostic "
        "output only. A-vs-B comparison review and future comparison violin panels belong on Screen 4 after "
        "deterministic comparison output exists. "
        "Do not say or imply that this path loads evidence, parses AWR content, compares evidence, selects runtime "
        "scope, assigns Target A/B, decides comparison readiness, computes comparison results, renders comparison "
        "violin panels, or performs deterministic analysis. "
        "Do not mention threshold status unless a threshold value is provided. Do not describe runtime eligibility "
        "except to say that this Screen 3 diagnostic explanation path does not change it."
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
    return runtime_explanation_violates_boundary(explanation)


def generate_screen3_evidence_context_explanation(payload: dict[str, Any]) -> dict[str, Any]:
    """Explain already-computed Screen 3 evidence-context contract fields."""

    payload = _normalize_screen3_evidence_context_explanation_payload(payload)
    validation_error = _validate_screen3_evidence_context_explanation_payload(payload)
    if validation_error:
        return normalize_runtime_explanation_response(
            {
                "status": "rejected",
                "message": validation_error,
                "records_created": False,
                "audit_reference": None,
                "_http_status": 400,
            },
            boundary_validation_result="request_rejected",
        )

    provider_mode = normalize_runtime_explanation_provider_mode(payload.get("provider_mode"))
    if provider_mode == "off":
        return normalize_runtime_explanation_response(
            {
                "status": "provider_off",
                "provider_mode": "off",
                "message": "Explanation unavailable. Deterministic evidence context remains unchanged.",
                "explanation": "",
                "records_created": False,
                "audit_reference": None,
                "_http_status": 200,
            },
            boundary_validation_result="not_applicable",
        )
    if provider_mode in {"mock", "local"}:
        return normalize_runtime_explanation_response(
            {
                "status": "generated",
                "provider_mode": provider_mode,
                "message": (
                    "Mock review-context explanation generated from already-computed evidence context. "
                    if provider_mode == "mock"
                    else "Local review-context explanation generated from already-computed evidence context. "
                )
                + "Deterministic values remain unchanged.",
                "explanation": _screen3_evidence_context_canned_explanation(
                    payload,
                    provider_mode=provider_mode,
                ),
                "records_created": False,
                "audit_reference": None,
                "_http_status": 200,
            },
            boundary_validation_result="passed",
        )
    if provider_mode == "oci":
        try:
            from src.analysis.ai_provider_adapter import generate_ai_response

            result = generate_ai_response(
                "oci",
                _screen3_evidence_context_system_role(),
                _screen3_evidence_context_prompt(payload),
                ["Review context explanation"],
            )
            explanation = _sanitize_screen2_provider_text(str(result.get("content") or ""))
        except Exception:
            return normalize_runtime_explanation_response(
                {
                    "status": "provider_failed",
                    "provider_mode": "oci",
                    "message": "Explanation unavailable. Deterministic evidence context remains unchanged.",
                    "explanation": "",
                    "records_created": False,
                    "audit_reference": None,
                    "_http_status": 502,
                },
                boundary_validation_result="not_checked",
            )
        if not explanation or runtime_explanation_violates_boundary(explanation):
            return normalize_runtime_explanation_response(
                {
                    "status": "provider_rejected",
                    "provider_mode": "oci",
                    "message": "Explanation unavailable. Deterministic evidence context remains unchanged.",
                    "explanation": "",
                    "records_created": False,
                    "audit_reference": None,
                    "_http_status": 502,
                },
                boundary_validation_result="rejected",
            )
        return normalize_runtime_explanation_response(
            {
                "status": "generated",
                "provider_mode": "oci",
                "message": "Review context explanation generated server-side. Deterministic values remain unchanged.",
                "explanation": explanation,
                "records_created": False,
                "audit_reference": None,
                "_http_status": 200,
            },
            boundary_validation_result="passed",
        )
    return normalize_runtime_explanation_response(
        {
            "status": "rejected",
            "message": "Unsupported Screen 3 evidence-context explanation provider mode.",
            "records_created": False,
            "audit_reference": None,
            "_http_status": 400,
        },
        boundary_validation_result="request_rejected",
    )


def _normalize_screen3_evidence_context_explanation_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Accept both browser-flat and direct nested evidence-context contracts."""

    if not isinstance(payload, dict):
        return payload
    normalized = dict(payload)
    contract = normalized.get("evidence_context_contract")
    if isinstance(contract, dict):
        for key in (
            "selected_scope_identity",
            "evidence_inventory",
            "context_classification",
            "artifact_alignment",
            "screen4_graphics_eligibility_hints",
            "truth_boundary",
        ):
            if key not in normalized and isinstance(contract.get(key), dict):
                normalized[key] = contract[key]
    if not normalized.get("provider_mode"):
        normalized["provider_mode"] = _default_screen3_evidence_context_provider_mode()
    for key in (
        "selected_scope_identity",
        "evidence_inventory",
        "context_classification",
        "artifact_alignment",
        "screen4_graphics_eligibility_hints",
        "truth_boundary",
    ):
        if key not in normalized:
            normalized[key] = {}
    return normalized


def _validate_screen3_evidence_context_explanation_payload(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return "Screen 3 evidence-context explanation request must be a JSON object."
    if payload.get("screen_id") != "screen_3":
        return "Screen 3 evidence-context explanation request must use screen_id=screen_3."
    if payload.get("request_type") != "screen3_evidence_context_explanation":
        return "Screen 3 evidence-context explanation request must use request_type=screen3_evidence_context_explanation."
    if payload.get("context_type") != "evidence_context":
        return "Screen 3 evidence-context explanation request must use context_type=evidence_context."
    if payload.get("non_mutating_explanation_only") is not True:
        return "Screen 3 evidence-context explanation request must be marked non-mutating."
    provider_mode = normalize_runtime_explanation_provider_mode(payload.get("provider_mode"))
    if provider_mode not in SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_PROVIDER_MODES:
        return "Unsupported Screen 3 evidence-context explanation provider mode."
    shared_validation_error = validate_runtime_explanation_payload(
        payload,
        expected_screen_id="screen_3",
        forbidden_fields=SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_FORBIDDEN_FIELDS,
    )
    if shared_validation_error:
        return shared_validation_error
    for key in (
        "selected_scope_identity",
        "evidence_inventory",
        "context_classification",
        "artifact_alignment",
        "screen4_graphics_eligibility_hints",
        "truth_boundary",
    ):
        if not isinstance(payload.get(key), dict):
            return f"Screen 3 evidence-context explanation request is missing {key}."
    return ""


def _screen3_evidence_context_canned_explanation(
    payload: dict[str, Any],
    *,
    provider_mode: str,
) -> str:
    identity = _screen3_payload_dict(payload, "selected_scope_identity")
    inventory = _screen3_payload_dict(payload, "evidence_inventory")
    classification = _screen3_payload_dict(payload, "context_classification")
    alignment = _screen3_payload_dict(payload, "artifact_alignment")
    truth = _screen3_payload_dict(payload, "truth_boundary")
    context_type = _screen3_payload_label(
        classification.get("primary") or identity.get("context_type"),
        "Unknown context",
    )
    runtime_scope = _screen3_payload_text(identity.get("runtime_scope") or identity.get("run_reference"), "the selected evidence context")
    evidence_path = _screen3_payload_label(identity.get("evidence_path"), "Evidence path unknown")
    freshness = _screen3_payload_label(identity.get("freshness"), "Source status unknown")
    selected_evidence = _screen3_payload_text(
        inventory.get("exact_selected_scope_evidence"),
        "Unknown",
    )
    same_db_history = _screen3_payload_text(
        inventory.get("same_db_historical_evidence"),
        "Not inventoried",
    )
    comparison_status = _screen3_payload_text(
        inventory.get("deterministic_comparison_output"),
        "No deterministic comparison output",
    )
    alignment_summary = _screen3_payload_text(
        alignment.get("product_summary") or alignment.get("mismatch_reason"),
        "Artifact alignment cannot be determined from available identity keys.",
    )
    cache_text = (
        "Cache restore is continuity only, not evidence truth."
        if truth.get("browser_cache_is_truth") is False
        else "Cache authority was not asserted."
    )
    mode_label = provider_mode.upper()
    return (
        f"{mode_label} explanation: Screen 3 currently treats {runtime_scope} as {context_type} "
        f"through {evidence_path}, with freshness shown as {freshness}. Selected AWR evidence is "
        f"{selected_evidence}; same-DB historical context is {same_db_history}; comparison output is "
        f"{comparison_status}. {alignment_summary} Screen 4 must still verify deterministic evidence "
        "and alignment before rendering review graphics. "
        f"{cache_text} Target A/B selections are prepared context only until deterministic comparison "
        "output exists. This explanation does not change diagnosis, scores, recommendations, comparison "
        "output, Screen 4 graphics eligibility, learning, materialization, runtime eligibility, or runtime behavior."
    )


def _screen3_evidence_context_system_role() -> str:
    return (
        "You write concise product-facing Oracle AWR review-context explanation text. "
        "Use only the already-computed Screen 3 evidence-context contract. "
        "The deterministic engine has already classified context, inventory, and alignment. "
        "You explain the meaning only. Do not classify evidence, decide availability, decide graphics eligibility, "
        "choose graphics, render graphics, compute trends, compute anomalies, compare Target A/B, diagnose, score, "
        "recommend, persist records, materialize rules, change runtime eligibility, or change future-run behavior. "
        "Return plain text only, with no Markdown headings, no bullets, and no leading # characters."
    )


def _screen3_evidence_context_prompt(payload: dict[str, Any]) -> str:
    context = {
        "selected_scope_identity": _screen3_payload_dict(payload, "selected_scope_identity"),
        "evidence_inventory": _screen3_payload_dict(payload, "evidence_inventory"),
        "context_classification": _screen3_payload_dict(payload, "context_classification"),
        "artifact_alignment": _screen3_payload_dict(payload, "artifact_alignment"),
        "screen4_graphics_eligibility_hints": _screen3_payload_dict(
            payload,
            "screen4_graphics_eligibility_hints",
        ),
        "truth_boundary": _screen3_payload_dict(payload, "truth_boundary"),
        "cache_live_status": _screen3_payload_text(payload.get("cache_live_status"), ""),
        "target_ab_prepared_only": bool(payload.get("target_ab_prepared_only")),
    }
    return (
        "Generate one concise plain-text paragraph for the product Screen 3 Review Context & Evidence Availability panel. "
        "Explain already-computed evidence context only. Do not use Markdown, heading markers, bullet lists, or leading # characters.\n"
        "Use only this deterministic/runtime contract JSON:\n"
        f"{json.dumps(context, sort_keys=True)}\n\n"
        "Boundary: explain why the selected context is single AWR, historical context, generated artifact, fleet context, "
        "or comparison-prepared only when those values are already present in the contract. "
        "Do not say or imply that you classified evidence, decided availability, decided graphics eligibility, chose graphics, "
        "rendered graphics, computed trends, computed anomalies, compared Target A/B, created deterministic comparison output, "
        "changed diagnosis, scores, severity, confidence, recommendations, learning, materialization, runtime eligibility, "
        "runtime behavior, or future-run behavior. "
        "State that Screen 4 must still verify deterministic evidence and alignment before rendering graphics."
    )


def _screen3_payload_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _screen3_payload_text(value: Any, fallback: str) -> str:
    return str(value or fallback).strip()[:500] or fallback


def _screen3_payload_label(value: Any, fallback: str) -> str:
    raw = _screen3_payload_text(value, fallback)
    labels = {
        "single_awr": "Single AWR",
        "selected_runtime_scope": "Selected Runtime Scope",
        "existing_platform_evidence": "Existing platform evidence",
        "generated_artifact": "Generated artifact",
        "generated_artifact_path": "Generated artifact",
        "browser_cache_continuity": "Cached continuity only",
        "cached_continuity_only": "Cached continuity only",
        "live_backend_metadata": "Live backend metadata",
        "governed_backend_runtime_options": "Live backend metadata",
        "no_deterministic_comparison_output": "No deterministic comparison output",
    }
    return labels.get(raw.strip().lower(), raw)


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
    print(
        "Screen 3 evidence-context explanation endpoint: "
        f"http://{args.host}:{args.port}{SCREEN3_EVIDENCE_CONTEXT_EXPLANATION_ENDPOINT_PATH}"
    )
    print(f"Health endpoint: http://{args.host}:{args.port}{HEALTH_ENDPOINT_PATH}")
    print(
        "This service queues governed requests and can run Screen 1 backend "
        "source intake/generation; it does not mutate Phase 4I or runtime truth "
        "in the browser."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard workflow service stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
