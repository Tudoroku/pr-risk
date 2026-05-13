from rich import box
from rich.console import Console
from rich.table import Table

from pr_risk.diff_stats import DiffStats
from pr_risk.recommendation import recommend_review
from pr_risk.risk import RiskResult
from pr_risk.runner import CommandResult, ExecutionResult

_RECOMMENDATION_MESSAGES = {
    "do_not_merge_until_build_passes": "Do not merge until build passes.",
    "do_not_merge_until_tests_pass": "Do not merge until tests pass.",
    "investigate_execution_timeout": "Investigate execution timeout.",
    "require_senior_review": "Require senior review.",
    "careful_review": "Careful review.",
    "normal_review": "Normal review.",
}


def print_report(
    changed_files: list[str],
    risk: RiskResult,
    diff_stats: DiffStats | None = None,
    cmake_signals: list[str] | None = None,
    api_signals: list[str] | None = None,
    execution_result: ExecutionResult | None = None,
) -> None:
    console = Console()

    console.print("PR Risk Report", style="bold")
    console.print(_changed_files_table(changed_files))
    if diff_stats is not None:
        console.print(_diff_stats_table(diff_stats))
    console.print(f"Risk score: {risk.score}/100")
    console.print(f"Risk level: {risk.level}")
    _print_recommendation(console, risk, execution_result)
    console.print("Reasons:")
    for reason in risk.reasons:
        console.print(f"- {reason}")
    _print_patch_signals(console, cmake_signals or [], api_signals or [])
    if execution_result is not None:
        _print_execution_checks(console, execution_result)


def _print_recommendation(
    console: Console,
    risk: RiskResult,
    execution_result: ExecutionResult | None,
) -> None:
    recommendation = recommend_review(risk, execution_result)
    message = _RECOMMENDATION_MESSAGES[recommendation]
    console.print("Recommendation:")
    console.print(f"- {message}")


def _print_patch_signals(console: Console, cmake_signals: list[str], api_signals: list[str]) -> None:
    console.print("Patch Signals:")
    if not cmake_signals and not api_signals:
        console.print("No patch signals detected")
        return

    if cmake_signals:
        console.print("CMake:")
        for signal in cmake_signals:
            console.print(f"- {signal}")

    if api_signals:
        console.print("Header/API:")
        for signal in api_signals:
            console.print(f"- {signal}")


def _print_execution_checks(console: Console, execution_result: ExecutionResult) -> None:
    console.print("Execution Checks:")
    if execution_result.build is None and execution_result.test is None and not execution_result.test_skipped:
        console.print("No execution commands configured")
        return

    console.print(f"- Build: {_format_command_status(execution_result.build)}")
    console.print(f"- Test: {_format_test_status(execution_result)}")


def _format_test_status(execution_result: ExecutionResult) -> str:
    if execution_result.test_skipped:
        reason = execution_result.test_skip_reason or "Skipped"
        return f"skipped ({reason})"

    return _format_command_status(execution_result.test)


def _format_command_status(result: CommandResult | None) -> str:
    if result is None:
        return "not configured"

    if result.timed_out:
        status = "timed out"
    elif result.exit_code == 0:
        status = "passed"
    else:
        status = "failed"

    details = []
    if result.exit_code is not None:
        details.append(f"exit code {result.exit_code}")
    details.append(f"{result.duration_seconds:.1f}s")

    return f"{status} ({', '.join(details)})"


def _changed_files_table(changed_files: list[str]) -> Table:
    table = Table(title="Changed Files", box=box.ASCII)
    table.add_column("#", justify="right")
    table.add_column("File")

    for index, path in enumerate(changed_files, start=1):
        table.add_row(str(index), path)

    return table


def _diff_stats_table(diff_stats: DiffStats) -> Table:
    table = Table(title="Diff Stats", box=box.ASCII)
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Files changed", str(diff_stats.files_changed))
    table.add_row("Lines added", str(diff_stats.lines_added))
    table.add_row("Lines deleted", str(diff_stats.lines_deleted))
    table.add_row("Total churn", str(diff_stats.total_churn))
    table.add_row("Binary files changed", str(diff_stats.binary_files_changed))

    return table
