"""Dashboard view model builders.

View models consume evidence_pack_contract objects and expose screen-specific
data structures. They do not render HTML or import dashboard renderers.
"""

from src.reporting.dashboard.view_models.screen3_diagnostic_view_model import (
    Screen3DiagnosticViewModel,
    build_screen3_diagnostic_view_model,
)
from src.reporting.dashboard.view_models.screen4_review_view_model import (
    Screen4ReviewModeViewModel,
    Screen4ReviewViewModel,
    build_screen4_review_view_model,
)
from src.reporting.dashboard.view_models.screen5_action_view_model import (
    Screen5ActionViewModel,
    build_screen5_action_view_model,
)
from src.reporting.dashboard.view_models.screen6_learning_view_model import (
    Screen6LearningViewModel,
    build_screen6_learning_view_model,
)

__all__ = [
    "Screen3DiagnosticViewModel",
    "Screen4ReviewModeViewModel",
    "Screen4ReviewViewModel",
    "Screen5ActionViewModel",
    "Screen6LearningViewModel",
    "build_screen3_diagnostic_view_model",
    "build_screen4_review_view_model",
    "build_screen5_action_view_model",
    "build_screen6_learning_view_model",
]

