import argparse
import importlib.metadata
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

from pr_risk import (
    api_change,
    cmake_analysis,
    config,
    diff_stats,
    git_diff,
    markdown_report,
    recommendation,
    report,
    risk,
    runner,
)


def app(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(_get_version())
        return 0

    if args.command == "analyze":
        try:
            executor = _validate_executor(args.executor)
        except ValueError as exc:
            parser.error(f"argument --executor: {exc}")
        return _run_analyze(args.repo, args.base, args.format, args.run_checks, executor)

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pr-risk")
    parser.add_argument("--version", action="store_true", help="show package version and exit")
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--repo", default=".")
    analyze_parser.add_argument("--base", default="main")
    analyze_parser.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    analyze_parser.add_argument("--run-checks", action="store_true", default=False)
    analyze_parser.add_argument("--executor", default=None)

    return parser


def _get_version() -> str:
    return importlib.metadata.version("pr-risk")


def _validate_executor(executor: str | None) -> str | None:
    if executor is None:
        return None
    if executor not in {"local", "docker"}:
        raise ValueError("must be one of: local, docker")
    return executor


def _run_analyze(
    repo: str,
    base: str,
    output_format: str,
    run_checks: bool,
    executor: str | None = None,
) -> int:
    try:
        changed_files = git_diff.get_changed_files(repo=repo, base=base)
        numstat_text = git_diff.get_diff_numstat(repo=repo, base=base)
        patch_text = git_diff.get_diff_patch(repo=repo, base=base)
    except git_diff.GitDiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    stats = diff_stats.parse_numstat(numstat_text)
    cmake_signals = cmake_analysis.analyze_cmake_changes(patch_text)
    api_signals = api_change.analyze_api_changes(patch_text)
    execution_config = None
    execution_result = None

    if run_checks:
        execution_config = config.load_config(Path(repo))
        if executor is not None:
            execution_config = replace(execution_config, executor=executor)
        try:
            execution_result = runner.run_execution_checks(Path(repo), execution_config)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        result = risk.calculate_risk(
            changed_files,
            stats,
            cmake_signals,
            api_signals,
            execution_result=execution_result,
        )
    else:
        result = risk.calculate_risk(changed_files, stats, cmake_signals, api_signals)

    if output_format == "json":
        print(
            json.dumps(
                _json_report(
                    changed_files,
                    result,
                    stats,
                    cmake_signals,
                    api_signals,
                    run_checks,
                    execution_config,
                    execution_result,
                )
            )
        )
    elif output_format == "markdown":
        print(
            markdown_report.render_markdown_report(
                result,
                changed_files,
                stats,
                cmake_signals,
                api_signals,
                execution_result,
                recommendation.recommend_review(result, execution_result),
            ),
            end="",
        )
    elif run_checks:
        report.print_report(changed_files, result, stats, cmake_signals, api_signals, execution_result)
    else:
        report.print_report(changed_files, result, stats, cmake_signals, api_signals)
    return 0


def _json_report(
    changed_files: list[str],
    result: risk.RiskResult,
    stats: diff_stats.DiffStats,
    cmake_signals: list[str],
    api_signals: list[str],
    run_checks: bool,
    execution_config: config.ExecutionConfig | None,
    execution_result: runner.ExecutionResult | None,
) -> dict[str, object]:
    return {
        "score": result.score,
        "level": result.level,
        "recommendation": recommendation.recommend_review(result, execution_result),
        "changed_files": changed_files,
        "diff_stats": asdict(stats),
        "reasons": result.reasons,
        "patch_signals": {
            "cmake": cmake_signals,
            "api": api_signals,
        },
        "execution": _json_execution(run_checks, execution_config, execution_result),
    }


def _json_execution(
    run_checks: bool,
    execution_config: config.ExecutionConfig | None,
    execution_result: runner.ExecutionResult | None,
) -> dict[str, object]:
    if not run_checks:
        return {"run": False}

    if execution_config is None or execution_result is None:
        return {"run": True}

    return {
        "run": True,
        "executor": execution_result.executor,
        "build": _json_build_execution(execution_config, execution_result),
        "test": _json_test_execution(execution_config, execution_result),
    }


def _json_build_execution(
    execution_config: config.ExecutionConfig,
    execution_result: runner.ExecutionResult,
) -> dict[str, object]:
    if execution_config.build_command is None:
        return {"configured": False}

    return _json_command_execution(execution_result.build, execution_config.build_command)


def _json_test_execution(
    execution_config: config.ExecutionConfig,
    execution_result: runner.ExecutionResult,
) -> dict[str, object]:
    if execution_config.test_command is None:
        return {
            "configured": False,
            "skipped": False,
            "skip_reason": None,
        }

    if execution_result.test_skipped:
        return {
            "configured": True,
            "command": execution_config.test_command,
            "exit_code": None,
            "timed_out": False,
            "duration_seconds": None,
            "skipped": True,
            "skip_reason": execution_result.test_skip_reason,
        }

    result = _json_command_execution(execution_result.test, execution_config.test_command)
    result["skipped"] = False
    result["skip_reason"] = None
    return result


def _json_command_execution(
    command_result: runner.CommandResult | None,
    command: str,
) -> dict[str, object]:
    if command_result is None:
        return {
            "configured": True,
            "command": command,
            "exit_code": None,
            "timed_out": False,
            "duration_seconds": None,
        }

    return {
        "configured": True,
        "command": command_result.command,
        "exit_code": command_result.exit_code,
        "timed_out": command_result.timed_out,
        "duration_seconds": command_result.duration_seconds,
    }


if __name__ == "__main__":
    raise SystemExit(app())
