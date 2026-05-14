from pr_risk.diff_stats import DiffStats
from pr_risk.report import print_report
from pr_risk.risk import RiskResult
from pr_risk.runner import CommandResult, ExecutionResult


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
    assert "Recommendation:" in output
    assert "- Require senior review." in output
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


def test_print_report_omits_execution_checks_when_not_provided(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report([], risk)

    output = capsys.readouterr().out
    assert "Execution Checks:" not in output
    assert "Executor:" not in output


def test_print_report_outputs_executor_when_execution_checks_are_provided(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report(
        [],
        risk,
        execution_result=ExecutionResult(
            build=_command_result("build", 0, 12.4),
            test=_command_result("test", 8, 5.1),
            executor="docker",
        ),
    )

    output = capsys.readouterr().out
    assert "Execution Checks:" in output
    assert "Executor: docker" in output
    assert "- Build: passed (exit code 0, 12.4s)" in output
    assert "- Test: failed (exit code 8, 5.1s)" in output


def test_print_report_outputs_normal_review_recommendation(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report([], risk)

    output = capsys.readouterr().out
    assert "Recommendation:" in output
    assert "- Normal review." in output


def test_print_report_outputs_build_failed_recommendation(capsys):
    risk = RiskResult(score=75, level="HIGH", reasons=["Header/API files changed", "Build failed"])

    print_report(
        [],
        risk,
        execution_result=ExecutionResult(
            build=_command_result("build", 1, 2.0),
            test=None,
            test_skipped=True,
            test_skip_reason="Build failed",
        ),
    )

    output = capsys.readouterr().out
    assert "Recommendation:" in output
    assert "- Do not merge until build passes." in output


def test_print_report_outputs_no_execution_commands_configured(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report([], risk, execution_result=ExecutionResult(build=None, test=None, executor="docker"))

    output = capsys.readouterr().out
    assert "Execution Checks:" in output
    assert "Executor: docker" in output
    assert "No execution commands configured" in output


def test_print_report_outputs_build_not_configured(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report([], risk, execution_result=ExecutionResult(build=None, test=_command_result("test", 0, 2.3)))

    output = capsys.readouterr().out
    assert "- Build: not configured" in output


def test_print_report_outputs_build_passed(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report([], risk, execution_result=ExecutionResult(build=_command_result("build", 0, 12.4), test=None))

    output = capsys.readouterr().out
    assert "- Build: passed (exit code 0, 12.4s)" in output


def test_print_report_outputs_build_failed(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report([], risk, execution_result=ExecutionResult(build=_command_result("build", 8, 5.1), test=None))

    output = capsys.readouterr().out
    assert "- Build: failed (exit code 8, 5.1s)" in output


def test_print_report_outputs_build_timed_out(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report(
        [],
        risk,
        execution_result=ExecutionResult(build=_command_result("build", None, 10.0, timed_out=True), test=None),
    )

    output = capsys.readouterr().out
    assert "- Build: timed out (10.0s)" in output


def test_print_report_outputs_test_not_configured(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report([], risk, execution_result=ExecutionResult(build=_command_result("build", 0, 1.2), test=None))

    output = capsys.readouterr().out
    assert "- Test: not configured" in output


def test_print_report_outputs_test_passed(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report(
        [],
        risk,
        execution_result=ExecutionResult(
            build=_command_result("build", 0, 1.2),
            test=_command_result("test", 0, 3.4),
        ),
    )

    output = capsys.readouterr().out
    assert "- Test: passed (exit code 0, 3.4s)" in output


def test_print_report_outputs_test_failed(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report([], risk, execution_result=ExecutionResult(build=None, test=_command_result("test", 8, 5.1)))

    output = capsys.readouterr().out
    assert "- Test: failed (exit code 8, 5.1s)" in output


def test_print_report_outputs_test_timed_out(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report(
        [],
        risk,
        execution_result=ExecutionResult(build=None, test=_command_result("test", None, 10.0, timed_out=True)),
    )

    output = capsys.readouterr().out
    assert "- Test: timed out (10.0s)" in output


def test_print_report_outputs_test_skipped_with_reason(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report(
        [],
        risk,
        execution_result=ExecutionResult(
            build=_command_result("build", 1, 2.0),
            test=None,
            test_skipped=True,
            test_skip_reason="Build failed",
        ),
    )

    output = capsys.readouterr().out
    assert "- Test: skipped (Build failed)" in output


def test_print_report_does_not_output_execution_stdout_or_stderr(capsys):
    risk = RiskResult(score=0, level="LOW", reasons=["No changed files"])

    print_report(
        [],
        risk,
        execution_result=ExecutionResult(
            build=_command_result("build", 0, 1.0, stdout="secret stdout", stderr="secret stderr"),
            test=None,
        ),
    )

    output = capsys.readouterr().out
    assert "secret stdout" not in output
    assert "secret stderr" not in output


def _command_result(
    name: str,
    exit_code: int | None,
    duration_seconds: float,
    timed_out: bool = False,
    stdout: str = "",
    stderr: str = "",
) -> CommandResult:
    return CommandResult(
        name=name,
        command=f"{name} command",
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        duration_seconds=duration_seconds,
    )
