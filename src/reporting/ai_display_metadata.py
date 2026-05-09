"""Deterministic display helpers for AI provider and model metadata."""

from __future__ import annotations

import os
from typing import Any


def format_ai_provider_display_name(provider: Any) -> str:
    """Return the human-facing provider name without changing runtime routing."""

    normalized = str(provider or os.getenv("AI_PROVIDER") or "").strip().lower()
    if normalized == "oci":
        return "OCI Generative AI"
    if normalized == "openai":
        return "OpenAI"
    return str(provider or "LLM provider not available").strip()


def format_ai_model_display_name(
    provider: Any,
    raw_model: Any,
    alias: str | None = None,
) -> str:
    """Return the human-facing model name without changing backend identifiers."""

    configured_model = _runtime_model_config_value(provider, raw_model)
    return _format_model_display_name(configured_model, alias=alias)


def _runtime_model_config_value(provider: Any, raw_model: Any) -> str:
    normalized_provider = str(provider or os.getenv("AI_PROVIDER") or "").strip().lower()
    if normalized_provider == "oci":
        return (
            str(os.getenv("OCI_MODEL", "") or "").strip()
            or str(raw_model or "").strip()
            or str(os.getenv("OCI_MODEL_ID", "") or "").strip()
        )
    if normalized_provider == "openai":
        return (
            str(os.getenv("OPENAI_MODEL", "") or "").strip()
            or str(raw_model or "").strip()
            or "gpt-5.4-mini"
        )
    return str(raw_model or "").strip()


def _format_model_display_name(raw_model: str, alias: str | None = None) -> str:
    if _has_display_value(alias):
        return str(alias).strip()
    model_name = str(raw_model or "").strip()
    if not model_name:
        return "Model not identified in current runtime"
    mappings = {
        "xai.grok-4-1-fast-reasoning": "Grok 4.1 Fast (Reasoning)",
        "xai.grok-4-1-fast": "Grok 4.1 Fast",
        "xai.grok-4-fast-reasoning": "Grok 4 Fast (Reasoning)",
        "xai.grok-4.20-reasoning": "Grok 4.20 Reasoning",
        "gpt-5.4-mini": "GPT-5.4 Mini",
    }
    if model_name in mappings:
        return mappings[model_name]
    if model_name.startswith("ocid1.generativeaimodel."):
        return model_name
    if len(model_name) > 40:
        return model_name[:40] + "..."
    return model_name


def _has_display_value(value: Any) -> bool:
    return value is not None and str(value).strip() not in {"", "None", "null"}
