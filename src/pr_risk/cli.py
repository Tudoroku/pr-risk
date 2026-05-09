import argparse
import importlib.metadata
import json
import sys
from dataclasses import asdict

from pr_risk import api_change, cmake_analysis, diff_stats, git_diff, report, risk


def app(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(_get_version())
        return 0

    if args.command == "analyze":
        return _run_analyze(args.repo, args.base, args.format)

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pr-risk")
    parser.add_argument("--version", action="store_true", help="show package version and exit")
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--repo", default=".")
    analyze_parser.add_argument("--base", default="main")
    analyze_parser.add_argument("--format", choices=("text", "json"), default="text")

    return parser


def _get_version() -> str:
    return importlib.metadata.version("pr-risk")


def _run_analyze(repo: str, base: str, output_format: str) -> int:
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
    result = risk.calculate_risk(changed_files, stats)
    if output_format == "json":
        print(json.dumps(_json_report(changed_files, result, stats, cmake_signals, api_signals)))
    else:
        report.print_report(changed_files, result, stats, cmake_signals, api_signals)
    return 0


def _json_report(
    changed_files: list[str],
    result: risk.RiskResult,
    stats: diff_stats.DiffStats,
    cmake_signals: list[str],
    api_signals: list[str],
) -> dict[str, object]:
    return {
        "score": result.score,
        "level": result.level,
        "changed_files": changed_files,
        "diff_stats": asdict(stats),
        "reasons": result.reasons,
        "patch_signals": {
            "cmake": cmake_signals,
            "api": api_signals,
        },
    }


if __name__ == "__main__":
    raise SystemExit(app())
