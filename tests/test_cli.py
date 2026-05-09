import json
import tomllib
from pathlib import Path

import pytest

from pr_risk.diff_stats import DiffStats
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
    stats = DiffStats(
        files_changed=1,
        lines_added=10,
        lines_deleted=2,
        total_churn=12,
    )

    def fake_get_changed_files(repo, base):
        calls.append(("changed_files", repo, base))
        return ["src/widget.cpp"]

    def fake_get_diff_numstat(repo, base):
        calls.append(("numstat", repo, base))
        return "10\t2\tsrc/widget.cpp\n"

    def fake_get_diff_patch(repo, base):
        calls.append(("patch", repo, base))
        return "patch text"

    def fake_parse_numstat(numstat_text):
        calls.append(("parse_numstat", numstat_text))
        return stats

    def fake_analyze_cmake_changes(patch_text):
        calls.append(("cmake", patch_text))
        return ["Link dependencies changed"]

    def fake_analyze_api_changes(patch_text):
        calls.append(("api", patch_text))
        return ["API-like header change detected in include/widget.hpp"]

    def fake_calculate_risk(changed_files, diff_stats, cmake_signals, api_signals):
        calls.append(("risk", changed_files, diff_stats, cmake_signals, api_signals))
        return risk_result

    def fake_print_report(changed_files, risk, diff_stats, cmake_signals, api_signals):
        calls.append(("report", changed_files, risk, diff_stats, cmake_signals, api_signals))

    monkeypatch.setattr(cli.git_diff, "get_changed_files", fake_get_changed_files)
    monkeypatch.setattr(cli.git_diff, "get_diff_numstat", fake_get_diff_numstat)
    monkeypatch.setattr(cli.git_diff, "get_diff_patch", fake_get_diff_patch)
    monkeypatch.setattr(cli.diff_stats, "parse_numstat", fake_parse_numstat)
    monkeypatch.setattr(cli.cmake_analysis, "analyze_cmake_changes", fake_analyze_cmake_changes)
    monkeypatch.setattr(cli.api_change, "analyze_api_changes", fake_analyze_api_changes)
    monkeypatch.setattr(cli.risk, "calculate_risk", fake_calculate_risk)
    monkeypatch.setattr(cli.report, "print_report", fake_print_report)

    exit_code = cli.app(["analyze", "--repo", ".", "--base", "main"])

    assert exit_code == 0
    assert calls == [
        ("changed_files", ".", "main"),
        ("numstat", ".", "main"),
        ("patch", ".", "main"),
        ("parse_numstat", "10\t2\tsrc/widget.cpp\n"),
        ("cmake", "patch text"),
        ("api", "patch text"),
        (
            "risk",
            ["src/widget.cpp"],
            stats,
            ["Link dependencies changed"],
            ["API-like header change detected in include/widget.hpp"],
        ),
        (
            "report",
            ["src/widget.cpp"],
            risk_result,
            stats,
            ["Link dependencies changed"],
            ["API-like header change detected in include/widget.hpp"],
        ),
    ]


def test_analyze_format_text_calls_report(monkeypatch):
    calls = []
    risk_result = RiskResult(score=30, level="LOW", reasons=["reason"])
    stats = DiffStats(
        files_changed=1,
        lines_added=10,
        lines_deleted=2,
        total_churn=12,
    )

    monkeypatch.setattr(cli.git_diff, "get_changed_files", lambda repo, base: ["src/widget.cpp"])
    monkeypatch.setattr(cli.git_diff, "get_diff_numstat", lambda repo, base: "10\t2\tsrc/widget.cpp\n")
    monkeypatch.setattr(cli.git_diff, "get_diff_patch", lambda repo, base: "")
    monkeypatch.setattr(cli.diff_stats, "parse_numstat", lambda numstat_text: stats)
    monkeypatch.setattr(cli.cmake_analysis, "analyze_cmake_changes", lambda patch_text: [])
    monkeypatch.setattr(cli.api_change, "analyze_api_changes", lambda patch_text: [])
    monkeypatch.setattr(
        cli.risk,
        "calculate_risk",
        lambda changed_files, diff_stats, cmake_signals, api_signals: risk_result,
    )
    monkeypatch.setattr(
        cli.report,
        "print_report",
        lambda changed_files, risk, diff_stats, cmake_signals, api_signals: calls.append(
            ("report", changed_files, risk, diff_stats, cmake_signals, api_signals)
        ),
    )

    exit_code = cli.app(["analyze", "--repo", ".", "--base", "main", "--format", "text"])

    assert exit_code == 0
    assert calls == [("report", ["src/widget.cpp"], risk_result, stats, [], [])]


def test_analyze_format_json_prints_valid_json(monkeypatch, capsys):
    risk_result = RiskResult(
        score=65,
        level="MEDIUM",
        reasons=["Source implementation files changed"],
    )
    stats = DiffStats(
        files_changed=1,
        lines_added=120,
        lines_deleted=30,
        total_churn=150,
        binary_files_changed=0,
    )

    monkeypatch.setattr(cli.git_diff, "get_changed_files", lambda repo, base: ["src/foo.cpp"])
    monkeypatch.setattr(cli.git_diff, "get_diff_numstat", lambda repo, base: "120\t30\tsrc/foo.cpp\n")
    monkeypatch.setattr(cli.git_diff, "get_diff_patch", lambda repo, base: "patch text")
    monkeypatch.setattr(cli.diff_stats, "parse_numstat", lambda numstat_text: stats)
    monkeypatch.setattr(cli.cmake_analysis, "analyze_cmake_changes", lambda patch_text: ["Link dependencies changed"])
    monkeypatch.setattr(cli.api_change, "analyze_api_changes", lambda patch_text: [])
    monkeypatch.setattr(
        cli.risk,
        "calculate_risk",
        lambda changed_files, diff_stats, cmake_signals, api_signals: risk_result,
    )
    monkeypatch.setattr(
        cli.report,
        "print_report",
        lambda changed_files, risk, diff_stats, cmake_signals, api_signals: pytest.fail(
            "text report should not be printed"
        ),
    )

    exit_code = cli.app(["analyze", "--repo", ".", "--base", "main", "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "score": 65,
        "level": "MEDIUM",
        "changed_files": ["src/foo.cpp"],
        "diff_stats": {
            "files_changed": 1,
            "lines_added": 120,
            "lines_deleted": 30,
            "total_churn": 150,
            "binary_files_changed": 0,
        },
        "reasons": ["Source implementation files changed"],
        "patch_signals": {
            "cmake": ["Link dependencies changed"],
            "api": [],
        },
    }


def test_analyze_rejects_invalid_format(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.app(["analyze", "--format", "yaml"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "invalid choice: 'yaml'" in captured.err


def test_analyze_uses_default_repo_and_base(monkeypatch):
    seen = {}

    def fake_get_changed_files(repo, base):
        seen["repo"] = repo
        seen["base"] = base
        return []

    monkeypatch.setattr(cli.git_diff, "get_changed_files", fake_get_changed_files)
    monkeypatch.setattr(cli.git_diff, "get_diff_numstat", lambda repo, base: "")
    monkeypatch.setattr(cli.git_diff, "get_diff_patch", lambda repo, base: "")
    monkeypatch.setattr(cli.diff_stats, "parse_numstat", lambda numstat_text: DiffStats(0, 0, 0, 0))
    monkeypatch.setattr(cli.cmake_analysis, "analyze_cmake_changes", lambda patch_text: [])
    monkeypatch.setattr(cli.api_change, "analyze_api_changes", lambda patch_text: [])
    monkeypatch.setattr(
        cli.risk,
        "calculate_risk",
        lambda changed_files, diff_stats, cmake_signals, api_signals: RiskResult(0, "NONE", []),
    )
    monkeypatch.setattr(
        cli.report,
        "print_report",
        lambda changed_files, risk, diff_stats, cmake_signals, api_signals: None,
    )

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


def test_analyze_without_run_checks_does_not_load_config_or_run_commands(monkeypatch):
    _stub_analyze_pipeline(monkeypatch, RiskResult(25, "LOW", ["reason"]))
    monkeypatch.setattr(
        cli.config,
        "load_config",
        lambda repo_path: pytest.fail("config should not be loaded without --run-checks"),
    )
    monkeypatch.setattr(
        cli.runner,
        "run_execution_checks",
        lambda repo_path, execution_config: pytest.fail("checks should not run without --run-checks"),
    )

    exit_code = cli.app(["analyze", "--repo", ".", "--base", "main"])

    assert exit_code == 0


def test_analyze_run_checks_loads_config_and_runs_execution_checks(monkeypatch):
    calls = []
    risk_result = RiskResult(25, "LOW", ["reason"])
    execution_config = cli.config.ExecutionConfig(
        build_command="cmake --build build",
        test_command="ctest --test-dir build",
        timeout_seconds=10,
    )
    _stub_analyze_pipeline(monkeypatch, risk_result)

    def fake_load_config(repo_path):
        calls.append(("load_config", repo_path))
        return execution_config

    def fake_run_execution_checks(repo_path, loaded_config):
        calls.append(("run_execution_checks", repo_path, loaded_config))
        return cli.runner.ExecutionResult(build=None, test=None)

    monkeypatch.setattr(cli.config, "load_config", fake_load_config)
    monkeypatch.setattr(cli.runner, "run_execution_checks", fake_run_execution_checks)

    exit_code = cli.app(["analyze", "--repo", ".", "--base", "main", "--run-checks"])

    assert exit_code == 0
    assert calls == [
        ("load_config", Path(".")),
        ("run_execution_checks", Path("."), execution_config),
    ]


def test_analyze_run_checks_with_no_config_or_commands_does_not_crash(monkeypatch, tmp_path):
    _stub_analyze_pipeline(monkeypatch, RiskResult(25, "LOW", ["reason"]))

    exit_code = cli.app(["analyze", "--repo", str(tmp_path), "--base", "main", "--run-checks"])

    assert exit_code == 0


def test_analyze_run_checks_failed_build_does_not_change_json_risk(monkeypatch, capsys):
    risk_result = RiskResult(42, "MEDIUM", ["Source implementation files changed"])
    _stub_analyze_pipeline(monkeypatch, risk_result)
    monkeypatch.setattr(
        cli.config,
        "load_config",
        lambda repo_path: cli.config.ExecutionConfig(
            build_command="build command",
            test_command="test command",
            timeout_seconds=10,
        ),
    )
    monkeypatch.setattr(
        cli.runner,
        "run_execution_checks",
        lambda repo_path, execution_config: cli.runner.ExecutionResult(
            build=cli.runner.CommandResult(
                name="build",
                command="build command",
                exit_code=1,
                stdout="build stdout",
                stderr="build stderr",
                timed_out=False,
                duration_seconds=0.1,
            ),
            test=None,
            test_skipped=True,
            test_skip_reason="Build failed",
        ),
    )

    exit_code = cli.app(["analyze", "--repo", ".", "--base", "main", "--format", "json", "--run-checks"])

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert output["score"] == 42
    assert output["level"] == "MEDIUM"
    assert "execution" not in output


def _stub_analyze_pipeline(monkeypatch, risk_result):
    stats = DiffStats(
        files_changed=1,
        lines_added=10,
        lines_deleted=2,
        total_churn=12,
    )
    monkeypatch.setattr(cli.git_diff, "get_changed_files", lambda repo, base: ["src/widget.cpp"])
    monkeypatch.setattr(cli.git_diff, "get_diff_numstat", lambda repo, base: "10\t2\tsrc/widget.cpp\n")
    monkeypatch.setattr(cli.git_diff, "get_diff_patch", lambda repo, base: "patch text")
    monkeypatch.setattr(cli.diff_stats, "parse_numstat", lambda numstat_text: stats)
    monkeypatch.setattr(cli.cmake_analysis, "analyze_cmake_changes", lambda patch_text: [])
    monkeypatch.setattr(cli.api_change, "analyze_api_changes", lambda patch_text: [])
    monkeypatch.setattr(
        cli.risk,
        "calculate_risk",
        lambda changed_files, diff_stats, cmake_signals, api_signals: risk_result,
    )
    monkeypatch.setattr(
        cli.report,
        "print_report",
        lambda changed_files, risk, diff_stats, cmake_signals, api_signals: None,
    )
