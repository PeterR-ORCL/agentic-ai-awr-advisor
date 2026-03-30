"""Utilities for loading Oracle AWR report text files.

This module provides a small, deterministic file-loading helper for the
Day 1 parser foundation. It is responsible only for safely reading an
Oracle AWR ``.out`` file into normalized text and a canonical dictionary
shape that downstream parsing logic can consume.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict


class AwrFileLoadResult(TypedDict):
    """Canonical result returned when an AWR file is loaded."""

    file_path: str
    file_name: str
    raw_text: str
    lines: list[str]
    line_count: int


class AwrFileLoaderError(Exception):
    """Raised when an AWR file cannot be loaded successfully."""


def load_awr_file(file_path: str | Path) -> AwrFileLoadResult:
    """Load an Oracle AWR report file into a canonical text structure.

    The loader validates that the target exists and is a file, reads the
    contents from disk, normalizes line endings to ``\\n``, and returns a
    deterministic dictionary suitable for downstream parsing.

    A UTF-8 decode is attempted first. If that fails, a small fallback
    sequence is used to handle common text-export encodings gracefully.

    Args:
        file_path: Path to the Oracle AWR report file.

    Returns:
        A dictionary containing the normalized file content and metadata.

    Raises:
        FileNotFoundError: If the provided path does not exist.
        IsADirectoryError: If the provided path points to a directory.
        AwrFileLoaderError: If the file cannot be read or decoded.
    """

    path = Path(file_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"AWR file does not exist: {path}")

    if not path.is_file():
        raise IsADirectoryError(f"AWR file path is not a file: {path}")

    raw_bytes = _read_file_bytes(path)
    raw_text = _decode_text(raw_bytes, path)
    normalized_text = _normalize_line_endings(raw_text)
    lines = normalized_text.splitlines()

    return {
        "file_path": str(path.resolve()),
        "file_name": path.name,
        "raw_text": normalized_text,
        "lines": lines,
        "line_count": len(lines),
    }


def _read_file_bytes(path: Path) -> bytes:
    """Read file bytes and raise a clear loader error on failure."""

    try:
        return path.read_bytes()
    except OSError as exc:
        raise AwrFileLoaderError(f"Failed to read AWR file '{path}': {exc}") from exc


def _decode_text(raw_bytes: bytes, path: Path) -> str:
    """Decode file bytes using UTF-8 first, then common fallbacks."""

    encodings = ("utf-8", "utf-8-sig", "cp1252", "latin-1")

    for encoding in encodings:
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise AwrFileLoaderError(
        "Failed to decode AWR file "
        f"'{path}' using supported encodings: {', '.join(encodings)}"
    )


def _normalize_line_endings(text: str) -> str:
    """Convert CRLF and CR line endings to a canonical LF form."""

    return text.replace("\r\n", "\n").replace("\r", "\n")
