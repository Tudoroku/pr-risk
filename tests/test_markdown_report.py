from pr_risk.diff_stats import DiffStats
from pr_risk.markdown_report import render_markdown_report
from pr_risk.risk import RiskResult
from pr_risk.runner import CommandResult, ExecutionResult


def test_render_markdown_report_includes_core_sections():
    output = render_markdown_report(
        risk_result=RiskResult(
            score=82,
            level="HIGH",
            reasons=[
                "CMake/build files changed",
                "API-like header changes detected",
                "Build failed",
            ],
        ),
        changed_files=["src/foo.cpp", "include/foo.hpp"],
        diff_stats=DiffStats(
            files_changed=2,
            lines_added=120,
            lines_deleted=20,
            total_churn=140,
            binary_files_changed=0,
        ),
        cmake_signals=["build target changed"],
        api_signals=["public header changed"],
        execution_result=ExecutionResult(
            build=_command_result("build", exit_code=1, duration_seconds=8.2),
            test=None,
            executor="docker",
            test_skipped=True,
            test_skip_reason="Build failed",
        ),
        recommendation="do_not_merge_until_build_passes",
    )

    assert "## PR Risk Report" in output
    assert "**Risk:** HIGH - 82/100" in output
    assert "**Recommendation:** Do not merge until build passes." in output
    assert "### Reasons" in output
    assert "- CMake/build files changed" in output
    assert "- API-like header changes detected" in output
    assert "- Build failed" in output
    assert "### Changed Files" in output
    assert "- src/foo.cpp" in output
    assert "- include/foo.hpp" in output
    assert "### Diff Stats" in output
    assert "- Files changed: 2" in output
    assert "- Lines added: 120" in output
    assert "- Lines deleted: 20" in output
    assert "- Total churn: 140" in output
    assert "- Binary files changed: 0" in output
    assert "### Patch Signals" in output
    assert "- CMake: build target changed" in output
    assert "- API: public header changed" in output
    assert "### Execution Checks" in output
    assert "Executor: docker" in output
    assert "- Build: failed (exit code 1, 8.2s)" in output
    assert "- Test: skipped (Build failed)" in output
    assert "### Limitations" in output
    assert "- Static heuristic analysis only." in output
    assert "- Configured checks depend on repository-provided commands." in output
    assert "- stdout/stderr are not included in this report." in output


def test_render_markdown_report_says_no_changed_files():
    output = render_markdown_report(
        risk_result=RiskResult(score=0, level="LOW", reasons=["No changed files"]),
        changed_files=[],
        diff_stats=DiffStats(0, 0, 0, 0),
        cmake_signals=[],
        api_signals=[],
        execution_result=None,
        recommendation="normal_review",
    )

    assert "### Changed Files\n_No changed files._" in output


def test_render_markdown_report_no_patch_signals_exact_text():
    output = render_markdown_report(
        risk_result=RiskResult(score=0, level="LOW", reasons=["No changed files"]),
        changed_files=[],
        diff_stats=DiffStats(0, 0, 0, 0),
        cmake_signals=[],
        api_signals=[],
        execution_result=None,
        recommendation="normal_review",
    )

    assert "### Patch Signals\n_None detected._" in output


def test_render_markdown_report_omits_execution_checks_when_not_run():
    output = render_markdown_report(
        risk_result=RiskResult(score=25, level="LOW", reasons=["reason"]),
        changed_files=["src/widget.cpp"],
        diff_stats=DiffStats(1, 10, 2, 12),
        cmake_signals=[],
        api_signals=[],
        execution_result=None,
        recommendation="normal_review",
    )

    assert "### Execution Checks" not in output
    assert "Executor:" not in output


def test_render_markdown_report_does_not_include_stdout_or_stderr():
    output = render_markdown_report(
        risk_result=RiskResult(score=25, level="LOW", reasons=["reason"]),
        changed_files=["src/widget.cpp"],
        diff_stats=DiffStats(1, 10, 2, 12),
        cmake_signals=[],
        api_signals=[],
        execution_result=ExecutionResult(
            build=_command_result(
                "build",
                exit_code=0,
                duration_seconds=1.2,
                stdout="secret stdout",
                stderr="secret stderr",
            ),
            test=None,
        ),
        recommendation="normal_review",
    )

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
