from src.parser.awr_parser import parse_awr_file
from src.analysis.issue_detector import detect_issues


if __name__ == "__main__":
    result = parse_awr_file("data/input/sample_awr_01.out")
    issues = detect_issues(result)

    print("Detected Issues:")
    if not issues:
        print("  None")
    else:
        for issue in issues:
            print(f"\n- issue_type: {issue['issue_type']}")
            print(f"  severity: {issue['severity']}")
            print(f"  summary: {issue['summary']}")
            print(f"  evidence: {issue['evidence']}")
