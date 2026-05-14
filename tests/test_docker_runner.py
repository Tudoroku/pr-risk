import subprocess

from pr_risk.docker_runner import run_docker_command
from pr_risk.runner import CommandResult


def test_run_docker_command_builds_expected_docker_args(tmp_path, monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr("pr_risk.docker_runner.subprocess.run", fake_run)

    run_docker_command(
        name="build",
        command="cmake --build build",
        repo_path=tmp_path,
        image="example/image:latest",
        workdir="/repo",
        timeout_seconds=30,
    )

    assert calls == [
        (
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{tmp_path.resolve()}:/repo",
                "-w",
                "/repo",
                "example/image:latest",
                "sh",
                "-c",
                "cmake --build build",
            ],
            {
                "capture_output": True,
                "text": True,
                "timeout": 30,
            },
        )
    ]


def test_run_docker_command_does_not_use_shell_true(tmp_path, monkeypatch):
    seen_kwargs = {}

    def fake_run(args, **kwargs):
        seen_kwargs.update(kwargs)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr("pr_risk.docker_runner.subprocess.run", fake_run)

    run_docker_command("test", "ctest", tmp_path, "image", "/workspace", 5)

    assert "shell" not in seen_kwargs


def test_run_docker_command_returns_original_configured_command(tmp_path, monkeypatch):
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr("pr_risk.docker_runner.subprocess.run", fake_run)

    result = run_docker_command("test", "ctest --output-on-failure", tmp_path, "image", "/repo", 5)

    assert result.command == "ctest --output-on-failure"


def test_run_docker_command_captures_success(tmp_path, monkeypatch):
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="passed\n", stderr="")

    monkeypatch.setattr("pr_risk.docker_runner.subprocess.run", fake_run)

    result = run_docker_command("test", "ctest", tmp_path, "image", "/repo", 5)

    assert result == CommandResult(
        name="test",
        command="ctest",
        exit_code=0,
        stdout="passed\n",
        stderr="",
        timed_out=False,
        duration_seconds=result.duration_seconds,
    )


def test_run_docker_command_captures_failure(tmp_path, monkeypatch):
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 7, stdout="", stderr="failed\n")

    monkeypatch.setattr("pr_risk.docker_runner.subprocess.run", fake_run)

    result = run_docker_command("build", "make", tmp_path, "image", "/repo", 5)

    assert result.exit_code == 7
    assert result.stderr == "failed\n"
    assert result.timed_out is False


def test_run_docker_command_captures_timeout(tmp_path, monkeypatch):
    def fake_run(args, **kwargs):
        raise subprocess.TimeoutExpired(args, kwargs["timeout"], output="partial\n", stderr=b"late\n")

    monkeypatch.setattr("pr_risk.docker_runner.subprocess.run", fake_run)

    result = run_docker_command("test", "ctest", tmp_path, "image", "/repo", 1)

    assert result.exit_code is None
    assert result.stdout == "partial\n"
    assert result.stderr == "late\n"
    assert result.timed_out is True


def test_run_docker_command_handles_missing_docker_executable(tmp_path, monkeypatch):
    def fake_run(args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("pr_risk.docker_runner.subprocess.run", fake_run)

    result = run_docker_command("build", "make", tmp_path, "image", "/repo", 5)

    assert result.exit_code == 127
    assert result.stderr == "Docker executable was not found"
    assert result.timed_out is False


def test_run_docker_command_returns_command_result(tmp_path, monkeypatch):
    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr("pr_risk.docker_runner.subprocess.run", fake_run)

    result = run_docker_command("build", "make", tmp_path, "image", "/repo", 5)

    assert isinstance(result, CommandResult)
