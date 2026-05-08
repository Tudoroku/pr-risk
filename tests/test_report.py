from pr_risk.report import print_report
from pr_risk.risk import RiskResult


def test_print_report_outputs_changed_files_and_risk_summary(capsys):
    risk = RiskResult(
        score=75,
        level="HIGH",
        reasons=["Changed CMake files", "No test files changed"],
    )

    print_report(["CMakeLists.txt", "src/widget.cpp"], risk)

    output = capsys.readouterr().out
    assert "PR Risk Report" in output
    assert "Changed Files" in output
    assert "CMakeLists.txt" in output
    assert "src/widget.cpp" in output
    assert "Risk score: 75/100" in output
    assert "Risk level: HIGH" in output
    assert "Reasons:" in output
    assert "- Changed CMake files" in output
    assert "- No test files changed" in output
