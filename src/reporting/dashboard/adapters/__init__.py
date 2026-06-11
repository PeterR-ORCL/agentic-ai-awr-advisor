"""Dashboard contract and screen adapter modules.

Adapters normalize deterministic backend payloads into explicit dashboard
contracts. The dashboard screen adapter is the only adapter allowed to call
screen view model builders and renderer adapters; no adapter may import browser
state, generated artifacts, the dashboard shell, or LLM modules.
"""

from src.reporting.dashboard.adapters.dashboard_screen_adapter import (
    DashboardScreenRenderBundle,
    build_dashboard_screen_render_bundle,
)
from src.reporting.dashboard.adapters.evidence_pack_builder import (
    build_evidence_pack_contract,
)

__all__ = [
    "DashboardScreenRenderBundle",
    "build_dashboard_screen_render_bundle",
    "build_evidence_pack_contract",
]
