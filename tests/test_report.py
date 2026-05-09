from pr_risk.diff_stats import DiffStats
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


def test_print_report_outputs_diff_stats_when_provided(capsys):
    risk = RiskResult(score=20, level="LOW", reasons=["Small change"])
    diff_stats = DiffStats(
        files_changed=3,
        lines_added=12,
        lines_deleted=5,
        total_churn=17,
        binary_files_changed=1,
    )

    print_report(["src/widget.cpp"], risk, diff_stats)

    output = capsys.readouterr().out
    assert "Diff Stats" in output
    assert "Files changed" in output
    assert "3" in output
    assert "Lines added" in output
    assert "12" in output
    assert "Lines deleted" in output
    assert "5" in output
    assert "Total churn" in output
    assert "17" in output
    assert "Binary files changed" in output
    assert "1" in output


def test_print_report_outputs_cmake_patch_signals(capsys):
    risk = RiskResult(score=25, level="LOW", reasons=["Build system files changed"])

    print_report(
        ["CMakeLists.txt"],
        risk,
        cmake_signals=["Link dependencies changed", "Package dependency changed"],
    )

    output = capsys.readouterr().out
    assert "Patch Signals:" in output
    assert "CMake:" in output
    assert "- Link dependencies changed" in output
    assert "- Package dependency changed" in output


def test_print_report_outputs_api_patch_signals(capsys):
    risk = RiskResult(score=25, level="LOW", reasons=["Header/API files changed"])

    print_report(
        ["include/widget.hpp"],
        risk,
        api_signals=["API-like header change detected in include/widget.hpp"],
    )

    output = capsys.readouterr().out
    assert "Patch Signals:" in output
    assert "Header/API:" in output
    assert "- API-like header change detected in include/widget.hpp" in output


def test_print_report_outputs_no_patch_signals_cleanly(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report([], risk, cmake_signals=[], api_signals=[])

    output = capsys.readouterr().out
    assert "Patch Signals:" in output
    assert "No patch signals detected" in output
    assert "CMake:" not in output
    assert "Header/API:" not in output
