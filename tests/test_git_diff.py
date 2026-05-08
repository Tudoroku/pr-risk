import subprocess

from pr_risk.git_diff import get_changed_files


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
