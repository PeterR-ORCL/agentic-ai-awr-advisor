#!/usr/bin/env python3
"""Run the local governed dashboard workflow service."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from typing import Any, Sequence


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.learning.dashboard_runtime_interaction import (
    lookup_existing_runs,
    process_dashboard_action,
    validate_object_storage_source,
)


ENDPOINT_PATH = "/phase7/dashboard/actions"
EXISTING_RUNS_ENDPOINT_PATH = "/phase7/dashboard/existing-runs"
OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH = "/phase7/dashboard/object-storage/validate"


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

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler naming
        if self.path not in {
            ENDPOINT_PATH,
            EXISTING_RUNS_ENDPOINT_PATH,
            OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH,
        }:
            self._send_json(
                {
                    "status": "rejected",
                    "message": "Unsupported dashboard workflow endpoint.",
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
        if self.path == OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH:
            result_payload = validate_object_storage_source(payload, queue_dir=queue_dir)
            status_code = 202 if result_payload.get("status") == "accepted" else 400
            self._send_json(result_payload, status_code=status_code)
            return
        result = process_dashboard_action(payload, queue_dir=queue_dir)
        status_code = 202 if result.status == "accepted" else 400
        self._send_json(result.to_dict(), status_code=status_code)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write("dashboard-workflow-service: " + format % args + "\n")

    def _send_json(self, payload: dict[str, Any], *, status_code: int) -> None:
        body = b"" if status_code == 204 else json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    queue_dir = Path(args.queue_dir).expanduser().resolve() if args.queue_dir else None
    server = ThreadingHTTPServer((args.host, args.port), Phase7DashboardWorkflowHandler)
    server.phase7_queue_dir = queue_dir
    print(
        f"Governed dashboard workflow service listening on "
        f"http://{args.host}:{args.port}{ENDPOINT_PATH}"
    )
    print(f"Existing run lookup endpoint: http://{args.host}:{args.port}{EXISTING_RUNS_ENDPOINT_PATH}")
    print(f"Object Storage validation endpoint: http://{args.host}:{args.port}{OBJECT_STORAGE_VALIDATE_ENDPOINT_PATH}")
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
