from pr_risk.diff_stats import DiffStats
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


def render_markdown_report(
    risk_result: RiskResult,
    changed_files: list[str],
    diff_stats: DiffStats,
    cmake_signals: list[str],
    api_signals: list[str],
    execution_result: ExecutionResult | None,
    recommendation: str,
) -> str:
    lines = [
        "## PR Risk Report",
        "",
        f"**Risk:** {risk_result.level} - {risk_result.score}/100",
        f"**Recommendation:** {_format_recommendation(recommendation)}",
        "",
        "### Reasons",
    ]

    lines.extend(_bullet_list(risk_result.reasons, "_None._"))
    lines.extend(["", "### Changed Files"])
    lines.extend(_bullet_list(changed_files, "_No changed files._"))
    lines.extend(["", "### Diff Stats"])
    lines.extend(_diff_stats_lines(diff_stats))
    lines.extend(["", "### Patch Signals"])
    lines.extend(_patch_signal_lines(cmake_signals, api_signals))

    if execution_result is not None:
        lines.extend(["", "### Execution Checks"])
        lines.extend(_execution_lines(execution_result))

    lines.extend(
        [
            "",
            "### Limitations",
            "- Static heuristic analysis only.",
            "- Configured checks depend on repository-provided commands.",
            "- stdout/stderr are not included in this report.",
        ]
    )

    return "\n".join(lines) + "\n"


def _format_recommendation(recommendation: str) -> str:
    return _RECOMMENDATION_MESSAGES.get(recommendation, recommendation)


def _bullet_list(items: list[str], empty_text: str) -> list[str]:
    if not items:
        return [empty_text]

    return [f"- {item}" for item in items]


def _diff_stats_lines(diff_stats: DiffStats) -> list[str]:
    return [
        f"- Files changed: {diff_stats.files_changed}",
        f"- Lines added: {diff_stats.lines_added}",
        f"- Lines deleted: {diff_stats.lines_deleted}",
        f"- Total churn: {diff_stats.total_churn}",
        f"- Binary files changed: {diff_stats.binary_files_changed}",
    ]


def _patch_signal_lines(cmake_signals: list[str], api_signals: list[str]) -> list[str]:
    if not cmake_signals and not api_signals:
        return ["_None detected._"]

    lines = []
    for signal in cmake_signals:
        lines.append(f"- CMake: {signal}")
    for signal in api_signals:
        lines.append(f"- API: {signal}")
    return lines


def _execution_lines(execution_result: ExecutionResult) -> list[str]:
    lines = [f"Executor: {execution_result.executor}"]
    if execution_result.build is None and execution_result.test is None and not execution_result.test_skipped:
        lines.append("_No execution commands configured._")
        return lines

    lines.append(f"- Build: {_format_command_status(execution_result.build)}")
    lines.append(f"- Test: {_format_test_status(execution_result)}")
    return lines


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
