import argparse
import sys

from pr_risk import git_diff, report, risk


def app(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _run_analyze(args.repo, args.base)

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pr-risk")
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--repo", default=".")
    analyze_parser.add_argument("--base", default="main")

    return parser


def _run_analyze(repo: str, base: str) -> int:
    try:
        changed_files = git_diff.get_changed_files(repo=repo, base=base)
    except git_diff.GitDiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = risk.calculate_risk(changed_files)
    report.print_report(changed_files, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(app())
