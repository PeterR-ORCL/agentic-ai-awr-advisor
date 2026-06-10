"""Contract-backed dashboard renderer adapters."""

from src.reporting.dashboard.renderers.screen3_renderer import render_screen3_diagnostic
from src.reporting.dashboard.renderers.screen4_renderer import (
    render_review_mode,
    render_screen4_review,
)
from src.reporting.dashboard.renderers.screen5_renderer import render_screen5_action
from src.reporting.dashboard.renderers.screen6_renderer import render_screen6_learning

__all__ = [
    "render_review_mode",
    "render_screen3_diagnostic",
    "render_screen4_review",
    "render_screen5_action",
    "render_screen6_learning",
]
