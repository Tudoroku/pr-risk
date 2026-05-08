import tomllib
from pathlib import Path

from pr_risk import cli, git_diff
from pr_risk.risk import RiskResult


def test_version_prints_package_version(capsys):
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    expected_version = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]["version"]

    exit_code = cli.app(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == f"{expected_version}\n"
    assert captured.err == ""


def test_analyze_calls_diff_risk_and_report(monkeypatch):
    calls = []
    risk_result = RiskResult(score=30, level="LOW", reasons=["reason"])

    def fake_get_changed_files(repo, base):
        calls.append(("diff", repo, base))
        return ["src/widget.cpp"]

    def fake_calculate_risk(changed_files):
        calls.append(("risk", changed_files))
        return risk_result

    def fake_print_report(changed_files, risk):
        calls.append(("report", changed_files, risk))

    monkeypatch.setattr(cli.git_diff, "get_changed_files", fake_get_changed_files)
    monkeypatch.setattr(cli.risk, "calculate_risk", fake_calculate_risk)
    monkeypatch.setattr(cli.report, "print_report", fake_print_report)

    exit_code = cli.app(["analyze", "--repo", ".", "--base", "main"])

    assert exit_code == 0
    assert calls == [
        ("diff", ".", "main"),
        ("risk", ["src/widget.cpp"]),
        ("report", ["src/widget.cpp"], risk_result),
    ]


def test_analyze_uses_default_repo_and_base(monkeypatch):
    seen = {}

    def fake_get_changed_files(repo, base):
        seen["repo"] = repo
        seen["base"] = base
        return []

    monkeypatch.setattr(cli.git_diff, "get_changed_files", fake_get_changed_files)
    monkeypatch.setattr(cli.risk, "calculate_risk", lambda changed_files: RiskResult(0, "NONE", []))
    monkeypatch.setattr(cli.report, "print_report", lambda changed_files, risk: None)

    exit_code = cli.app(["analyze"])

    assert exit_code == 0
    assert seen == {"repo": ".", "base": "main"}


def test_analyze_returns_non_zero_for_expected_git_error(monkeypatch, capsys):
    def fake_get_changed_files(repo, base):
        raise git_diff.GitDiffError("not a git repository")

    monkeypatch.setattr(cli.git_diff, "get_changed_files", fake_get_changed_files)

    exit_code = cli.app(["analyze", "--repo", "missing", "--base", "main"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "error: not a git repository\n"
