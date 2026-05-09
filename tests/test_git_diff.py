import subprocess
from unittest.mock import Mock

import pytest

from pr_risk import git_diff
from pr_risk.git_diff import GitDiffError, get_changed_files, get_diff_numstat


def _git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_get_changed_files_detects_local_modified_tracked_file(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    tracked_file = repo / "src" / "widget.cpp"
    tracked_file.parent.mkdir()
    tracked_file.write_text("int main() { return 0; }\n", encoding="utf-8")

    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "add", "src/widget.cpp")
    _git(repo, "commit", "-m", "initial")

    tracked_file.write_text("int main() { return 1; }\n", encoding="utf-8")

    assert get_changed_files(str(repo), "main") == ["src/widget.cpp"]


def test_get_diff_numstat_runs_git_diff_numstat(monkeypatch):
    completed = Mock(stdout="2\t1\tsrc/widget.cpp\n")
    run = Mock(return_value=completed)
    monkeypatch.setattr(git_diff.subprocess, "run", run)

    assert get_diff_numstat("repo-path", "main") == "2\t1\tsrc/widget.cpp\n"
    run.assert_called_once_with(
        ["git", "-C", "repo-path", "diff", "--numstat", "main"],
        check=True,
        capture_output=True,
        text=True,
    )


def test_get_diff_numstat_wraps_missing_git(monkeypatch):
    run = Mock(side_effect=FileNotFoundError())
    monkeypatch.setattr(git_diff.subprocess, "run", run)

    with pytest.raises(GitDiffError, match="git executable was not found"):
        get_diff_numstat("repo-path", "main")


def test_get_diff_numstat_uses_stderr_for_git_failure(monkeypatch):
    run = Mock(
        side_effect=subprocess.CalledProcessError(
            returncode=128,
            cmd=["git"],
            stderr="fatal: bad revision\n",
            output="",
        )
    )
    monkeypatch.setattr(git_diff.subprocess, "run", run)

    with pytest.raises(GitDiffError, match="fatal: bad revision"):
        get_diff_numstat("repo-path", "missing-base")


def test_get_diff_numstat_uses_stdout_fallback_for_git_failure(monkeypatch):
    run = Mock(
        side_effect=subprocess.CalledProcessError(
            returncode=128,
            cmd=["git"],
            stderr="",
            output="stdout failure\n",
        )
    )
    monkeypatch.setattr(git_diff.subprocess, "run", run)

    with pytest.raises(GitDiffError, match="stdout failure"):
        get_diff_numstat("repo-path", "missing-base")
