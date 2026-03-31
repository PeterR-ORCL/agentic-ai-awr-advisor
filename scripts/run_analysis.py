from src.analysis.issue_detector import detect_issues
from src.analysis.recommendation_engine import generate_recommendations
from src.parser.awr_parser import parse_awr_file


if __name__ == "__main__":
    result = parse_awr_file("data/input/sample_awr_01.out")

    issues = detect_issues(result)
    recommendations = generate_recommendations(issues)

    print("\nDetected Issues:")
    if not issues:
        print("  None")
    else:
        for issue in issues:
            print(f"\n- issue_type: {issue['issue_type']}")
            print(f"  severity: {issue['severity']}")
            print(f"  summary: {issue['summary']}")
            print(f"  evidence: {issue['evidence']}")

    print("\nRecommendations:\n")

    for rec in recommendations:
        print(f"- {rec.issue_type} ({rec.severity})")
        print(f"  Recommendation: {rec.recommendation}")
        print(f"  Rationale: {rec.rationale}")
        print("  Actions:")
        for action in rec.actions:
            print(f"    - {action}")
        print()
