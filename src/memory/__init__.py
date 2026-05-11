"""Phase 6 memory package."""

from importlib import import_module
from typing import Any

__all__ = [
    "governance_semantic_assist",
    "memory_orchestrator",
    "memory_recall",
    "semantic_recall_service",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
