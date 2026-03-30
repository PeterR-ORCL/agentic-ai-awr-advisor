import json
from pathlib import Path
from dataclasses import asdict, is_dataclass

from src.parser.awr_parser import parse_awr_file

if __name__ == "__main__":
    result = parse_awr_file("data/input/sample_awr_01.out")

    print("Run Metadata:")

    if is_dataclass(result.run_metadata):
        metadata_dict = asdict(result.run_metadata)
    elif hasattr(result.run_metadata, "to_dict"):
        metadata_dict = result.run_metadata.to_dict()
    elif hasattr(result.run_metadata, "model_dump"):
        metadata_dict = result.run_metadata.model_dump()
    else:
        metadata_dict = dict(result.run_metadata)

    for key, value in metadata_dict.items():
        print(f"  {key}: {value}")

    print("\nSections Found:")
    for section_name, section_info in result.sections_found.items():
        print(f"  {section_name}: {section_info}")

    print("\nWarnings:")
    if result.parse_warnings:
        for warning in result.parse_warnings:
            print(f"  - {warning}")
    else:
        print("  None")

    print("\nErrors:")
    if result.parse_errors:
        for error in result.parse_errors:
            print(f"  - {error}")
    else:
        print("  None")

    output_path = Path("data/output/parse_result.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2)

    print(f"\nWrote parse result to: {output_path}")
