"""Shared helpers for contract-backed dashboard renderer adapters.

The helpers in this module render deterministic HTML fragments from view model
data only. They do not read browser state, generated dashboard artifacts, or
runtime selectors.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from html import escape
from typing import Any


def escape_text(value: Any) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=True)


def join_fragments(parts: Iterable[str]) -> str:
    return "".join(part for part in parts if part)


def render_root(screen_id: str, title: str, parts: Sequence[str]) -> str:
    return (
        f'<section class="evidence-screen" data-screen="{escape_text(screen_id)}">'
        f"<h2>{escape_text(title)}</h2>"
        f"{join_fragments(parts)}"
        "</section>"
    )


def render_identity(selected_flow_id: str, evidence_pack_id: str) -> str:
    return (
        '<dl class="evidence-identity">'
        "<dt>Selected flow</dt>"
        f"<dd>{escape_text(selected_flow_id)}</dd>"
        "<dt>Evidence pack</dt>"
        f"<dd>{escape_text(evidence_pack_id)}</dd>"
        "</dl>"
    )


def render_summary(availability_status: str, summary: str | None) -> str:
    body = [
        '<section class="evidence-summary">',
        "<h3>Summary</h3>",
        f'<p class="availability-status">{escape_text(availability_status)}</p>',
    ]
    if summary:
        body.append(f"<p>{escape_text(summary)}</p>")
    body.append("</section>")
    return join_fragments(body)


def render_mapping(title: str, mapping: Mapping[str, Any] | None) -> str:
    if not mapping:
        return ""
    rows = []
    for key in sorted(mapping):
        rows.append(
            "<tr>"
            f"<th>{escape_text(key)}</th>"
            f"<td>{escape_text(_format_value(mapping[key]))}</td>"
            "</tr>"
        )
    return (
        '<section class="evidence-metadata">'
        f"<h3>{escape_text(title)}</h3>"
        f"<table><tbody>{join_fragments(rows)}</tbody></table>"
        "</section>"
    )


def render_items(title: str, items: Sequence[Mapping[str, Any]], class_name: str) -> str:
    if not items:
        return ""
    rendered = []
    for item in items:
        rendered.append(
            f'<li><pre>{escape_text(_format_value(item))}</pre></li>'
        )
    return (
        f'<section class="{escape_text(class_name)}">'
        f"<h3>{escape_text(title)}</h3>"
        f"<ul>{join_fragments(rendered)}</ul>"
        "</section>"
    )


def render_rows(title: str, rows: Sequence[Mapping[str, Any]]) -> str:
    return render_items(title, rows, "evidence-rows")


def render_state_lists(
    *,
    missing_evidence: Sequence[Mapping[str, Any]],
    unavailable_evidence: Sequence[Mapping[str, Any]],
    stale_evidence: Sequence[Mapping[str, Any]],
) -> str:
    return join_fragments(
        (
            render_items("Missing evidence", missing_evidence, "missing-evidence"),
            render_items("Unavailable evidence", unavailable_evidence, "unavailable-evidence"),
            render_items("Stale evidence", stale_evidence, "stale-evidence"),
        )
    )


def render_visualizations(visualizations: Sequence[Mapping[str, Any]]) -> str:
    if not visualizations:
        return ""
    return render_items("Allowed visualizations", visualizations, "allowed-visualizations")


def render_llm_eligibility(eligibility: Sequence[Mapping[str, Any]]) -> str:
    if not eligibility:
        return ""
    return render_items("LLM explanation eligibility", eligibility, "llm-explanation-eligibility")


def render_group(title: str, parts: Sequence[str], class_name: str) -> str:
    return (
        f'<section class="{escape_text(class_name)}">'
        f"<h3>{escape_text(title)}</h3>"
        f"{join_fragments(parts)}"
        "</section>"
    )


def render_named_collections(collections: Sequence[tuple[str, Sequence[Mapping[str, Any]]]]) -> str:
    return join_fragments(render_items(title, items, _slug(title)) for title, items in collections)


def _slug(value: str) -> str:
    return value.lower().replace("/", "-").replace(" ", "-")


def _format_value(value: Any) -> str:
    if isinstance(value, Mapping):
        parts = [f"{key}: {_format_value(value[key])}" for key in sorted(value)]
        return "{ " + ", ".join(parts) + " }"
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return "[" + ", ".join(_format_value(item) for item in value) + "]"
    return "" if value is None else str(value)
