"""Day 1 orchestration for parsing Oracle AWR report files."""

from __future__ import annotations

from pathlib import Path

from src.models.parse_result import ParseResult
from src.models.run_metadata import RunMetadata
from src.parser.awr_file_loader import load_awr_file
from src.parser.awr_section_locator import locate_awr_sections
from src.parser.metadata_parser import parse_awr_metadata


def parse_awr_file(file_path: str | Path) -> ParseResult:
    """Parse an Oracle AWR report file into the canonical Day 1 result.

    The Day 1 orchestrator loads the source file, locates major sections,
    extracts run-level metadata, and assembles a deterministic
    ``ParseResult``. Metric collections remain empty placeholders until
    later parser phases are implemented.

    Args:
        file_path: Path to the Oracle AWR report file.

    Returns:
        A canonical ``ParseResult`` object for the provided file.

    Raises:
        FileNotFoundError: If the source file does not exist.
        IsADirectoryError: If the provided path is not a file.
        AwrFileLoaderError: If the file cannot be read or decoded.
    """

    loaded_file = load_awr_file(file_path)
    sections_found = locate_awr_sections(loaded_file["lines"])

    metadata_dict, metadata_warnings = parse_awr_metadata(
        file_path=loaded_file["file_path"],
        file_name=loaded_file["file_name"],
        lines=loaded_file["lines"],
        report_header=sections_found.get("report_header"),
    )

    run_metadata = RunMetadata(**metadata_dict)

    return ParseResult(
        run_metadata=run_metadata,
        sections_found=sections_found,
        cpu_metrics=[],
        io_metrics=[],
        wait_events=[],
        top_sql=[],
        session_metrics=[],
        parse_warnings=metadata_warnings,
        parse_errors=[],
    )
