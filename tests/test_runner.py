import subprocess
import sys

import pytest

from pr_risk.config import DockerConfig, ExecutionConfig
from pr_risk.runner import CommandResult, ExecutionResult, run_command, run_execution_checks


def _write_script(tmp_path, name, contents):
    script = tmp_path / name
    script.write_text(contents, encoding="utf-8")
    return script


def _python_command(script):
    return subprocess.list2cmdline([sys.executable, str(script)])


def _command_result(name="command", command="command", exit_code=0, timed_out=False):
    return CommandResult(
        name=name,
        command=command,
        exit_code=exit_code,
        stdout="",
        stderr="",
        timed_out=timed_out,
        duration_seconds=1.0,
    )


def test_run_command_successful_command(tmp_path):
    script = _write_script(tmp_path, "success.py", "print('ok')\n")

    result = run_command("success", _python_command(script), tmp_path, 5)

    assert result == CommandResult(
        name="success",
        command=_python_command(script),
        exit_code=0,
        stdout="ok\n",
        stderr="",
        timed_out=False,
        duration_seconds=result.duration_seconds,
    )


def test_run_command_returns_non_zero_exit_code(tmp_path):
    script = _write_script(
        tmp_path,
        "failure.py",
        "import sys\n"
        "sys.exit(7)\n",
    )

    result = run_command("failure", _python_command(script), tmp_path, 5)

    assert result.exit_code == 7
    assert result.timed_out is False


def test_run_command_times_out(tmp_path):
    script = _write_script(
        tmp_path,
        "timeout.py",
        "import time\n"
        "time.sleep(5)\n",
    )

    result = run_command("timeout", _python_command(script), tmp_path, 1)

    assert result.exit_code is None
    assert result.timed_out is True


def test_run_command_captures_stdout(tmp_path):
    script = _write_script(tmp_path, "stdout.py", "print('stdout text')\n")

    result = run_command("stdout", _python_command(script), tmp_path, 5)

    assert result.stdout == "stdout text\n"


def test_run_command_captures_stderr(tmp_path):
    script = _write_script(
        tmp_path,
        "stderr.py",
        "import sys\n"
        "print('stderr text', file=sys.stderr)\n",
    )

    result = run_command("stderr", _python_command(script), tmp_path, 5)

    assert result.stderr == "stderr text\n"


def test_run_command_populates_duration(tmp_path):
    script = _write_script(tmp_path, "duration.py", "print('done')\n")

    result = run_command("duration", _python_command(script), tmp_path, 5)

    assert result.duration_seconds >= 0


def test_run_command_respects_cwd(tmp_path):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    script = _write_script(
        tmp_path,
        "cwd.py",
        "from pathlib import Path\n"
        "print(Path.cwd())\n",
    )

    result = run_command("cwd", _python_command(script), work_dir, 5)

    assert result.stdout.strip() == str(work_dir)


def test_run_execution_checks_no_commands(tmp_path):
    config = ExecutionConfig(
        build_command=None,
        test_command=None,
        timeout_seconds=5,
    )

    result = run_execution_checks(tmp_path, config)

    assert result == ExecutionResult(
        build=None,
        test=None,
        executor="local",
        test_skipped=False,
        test_skip_reason=None,
    )


def test_run_execution_checks_build_only(tmp_path):
    build_script = _write_script(tmp_path, "build.py", "print('build ok')\n")
    config = ExecutionConfig(
        build_command=_python_command(build_script),
        test_command=None,
        timeout_seconds=5,
    )

    result = run_execution_checks(tmp_path, config)

    assert result.build is not None
    assert result.build.name == "build"
    assert result.build.exit_code == 0
    assert result.build.stdout == "build ok\n"
    assert result.test is None
    assert result.executor == "local"
    assert result.test_skipped is False
    assert result.test_skip_reason is None


def test_run_execution_checks_test_only(tmp_path):
    test_script = _write_script(tmp_path, "test.py", "print('test ok')\n")
    config = ExecutionConfig(
        build_command=None,
        test_command=_python_command(test_script),
        timeout_seconds=5,
    )

    result = run_execution_checks(tmp_path, config)

    assert result.build is None
    assert result.test is not None
    assert result.test.name == "test"
    assert result.test.exit_code == 0
    assert result.test.stdout == "test ok\n"
    assert result.executor == "local"
    assert result.test_skipped is False
    assert result.test_skip_reason is None


def test_run_execution_checks_build_and_test_pass(tmp_path):
    build_script = _write_script(tmp_path, "build.py", "print('build ok')\n")
    test_script = _write_script(tmp_path, "test.py", "print('test ok')\n")
    config = ExecutionConfig(
        build_command=_python_command(build_script),
        test_command=_python_command(test_script),
        timeout_seconds=5,
    )

    result = run_execution_checks(tmp_path, config)

    assert result.build is not None
    assert result.build.exit_code == 0
    assert result.test is not None
    assert result.test.exit_code == 0
    assert result.executor == "local"
    assert result.test_skipped is False
    assert result.test_skip_reason is None


def test_run_execution_checks_build_fails_and_test_is_skipped(tmp_path):
    build_script = _write_script(
        tmp_path,
        "build.py",
        "import sys\n"
        "sys.exit(2)\n",
    )
    test_script = _write_script(tmp_path, "test.py", "print('should not run')\n")
    config = ExecutionConfig(
        build_command=_python_command(build_script),
        test_command=_python_command(test_script),
        timeout_seconds=5,
    )

    result = run_execution_checks(tmp_path, config)

    assert result.build is not None
    assert result.build.exit_code == 2
    assert result.build.timed_out is False
    assert result.test is None
    assert result.executor == "local"
    assert result.test_skipped is True
    assert result.test_skip_reason == "Build failed"


def test_run_execution_checks_build_times_out_and_test_is_skipped(tmp_path):
    build_script = _write_script(
        tmp_path,
        "build.py",
        "import time\n"
        "time.sleep(5)\n",
    )
    test_script = _write_script(tmp_path, "test.py", "print('should not run')\n")
    config = ExecutionConfig(
        build_command=_python_command(build_script),
        test_command=_python_command(test_script),
        timeout_seconds=1,
    )

    result = run_execution_checks(tmp_path, config)

    assert result.build is not None
    assert result.build.exit_code is None
    assert result.build.timed_out is True
    assert result.test is None
    assert result.executor == "local"
    assert result.test_skipped is True
    assert result.test_skip_reason == "Build timed out"


def test_run_execution_checks_test_fails(tmp_path):
    build_script = _write_script(tmp_path, "build.py", "print('build ok')\n")
    test_script = _write_script(
        tmp_path,
        "test.py",
        "import sys\n"
        "sys.exit(3)\n",
    )
    config = ExecutionConfig(
        build_command=_python_command(build_script),
        test_command=_python_command(test_script),
        timeout_seconds=5,
    )

    result = run_execution_checks(tmp_path, config)

    assert result.build is not None
    assert result.build.exit_code == 0
    assert result.test is not None
    assert result.test.exit_code == 3
    assert result.test.timed_out is False
    assert result.executor == "local"
    assert result.test_skipped is False
    assert result.test_skip_reason is None


def test_run_execution_checks_test_times_out(tmp_path):
    build_script = _write_script(tmp_path, "build.py", "print('build ok')\n")
    test_script = _write_script(
        tmp_path,
        "test.py",
        "import time\n"
        "time.sleep(5)\n",
    )
    config = ExecutionConfig(
        build_command=_python_command(build_script),
        test_command=_python_command(test_script),
        timeout_seconds=1,
    )

    result = run_execution_checks(tmp_path, config)

    assert result.build is not None
    assert result.build.exit_code == 0
    assert result.test is not None
    assert result.test.exit_code is None
    assert result.test.timed_out is True
    assert result.executor == "local"
    assert result.test_skipped is False
    assert result.test_skip_reason is None


def test_run_execution_checks_local_executor_uses_local_runner(monkeypatch, tmp_path):
    calls = []

    def fake_run_command(name, command, cwd, timeout_seconds):
        calls.append((name, command, cwd, timeout_seconds))
        return _command_result(name=name, command=command)

    monkeypatch.setattr("pr_risk.runner.run_command", fake_run_command)
    config = ExecutionConfig(
        build_command="build command",
        test_command="test command",
        timeout_seconds=17,
        executor="local",
    )

    result = run_execution_checks(tmp_path, config)

    assert calls == [
        ("build", "build command", tmp_path, 17),
        ("test", "test command", tmp_path, 17),
    ]
    assert result.executor == "local"


def test_run_execution_checks_docker_executor_uses_docker_runner(monkeypatch, tmp_path):
    calls = []

    def fake_run_docker_command(name, command, repo_path, image, workdir, timeout_seconds):
        calls.append((name, command, repo_path, image, workdir, timeout_seconds))
        return _command_result(name=name, command=command)

    monkeypatch.setattr("pr_risk.docker_runner.run_docker_command", fake_run_docker_command)
    config = ExecutionConfig(
        build_command="cmake --build build",
        test_command="ctest --test-dir build",
        timeout_seconds=29,
        executor="docker",
        docker=DockerConfig(image="cpp:latest", workdir="/src"),
    )

    result = run_execution_checks(tmp_path, config)

    assert calls == [
        ("build", "cmake --build build", tmp_path, "cpp:latest", "/src", 29),
        ("test", "ctest --test-dir build", tmp_path, "cpp:latest", "/src", 29),
    ]
    assert result.executor == "docker"


def test_run_execution_checks_docker_build_failure_skips_docker_test(monkeypatch, tmp_path):
    calls = []

    def fake_run_docker_command(name, command, repo_path, image, workdir, timeout_seconds):
        calls.append(name)
        return _command_result(name=name, command=command, exit_code=2)

    monkeypatch.setattr("pr_risk.docker_runner.run_docker_command", fake_run_docker_command)
    config = ExecutionConfig(
        build_command="build",
        test_command="test",
        timeout_seconds=5,
        executor="docker",
        docker=DockerConfig(image="cpp:latest"),
    )

    result = run_execution_checks(tmp_path, config)

    assert calls == ["build"]
    assert result.executor == "docker"
    assert result.build is not None
    assert result.build.exit_code == 2
    assert result.test is None
    assert result.test_skipped is True
    assert result.test_skip_reason == "Build failed"


def test_run_execution_checks_docker_build_timeout_skips_docker_test(monkeypatch, tmp_path):
    calls = []

    def fake_run_docker_command(name, command, repo_path, image, workdir, timeout_seconds):
        calls.append(name)
        return _command_result(name=name, command=command, exit_code=None, timed_out=True)

    monkeypatch.setattr("pr_risk.docker_runner.run_docker_command", fake_run_docker_command)
    config = ExecutionConfig(
        build_command="build",
        test_command="test",
        timeout_seconds=5,
        executor="docker",
        docker=DockerConfig(image="cpp:latest"),
    )

    result = run_execution_checks(tmp_path, config)

    assert calls == ["build"]
    assert result.executor == "docker"
    assert result.build is not None
    assert result.build.timed_out is True
    assert result.test is None
    assert result.test_skipped is True
    assert result.test_skip_reason == "Build timed out"


def test_run_execution_checks_docker_no_commands(tmp_path):
    config = ExecutionConfig(
        build_command=None,
        test_command=None,
        timeout_seconds=5,
        executor="docker",
        docker=DockerConfig(image="cpp:latest"),
    )

    result = run_execution_checks(tmp_path, config)

    assert result == ExecutionResult(
        build=None,
        test=None,
        executor="docker",
        test_skipped=False,
        test_skip_reason=None,
    )


def test_run_execution_checks_rejects_unknown_executor_even_without_commands(tmp_path):
    config = ExecutionConfig(
        build_command=None,
        test_command=None,
        timeout_seconds=5,
        executor="weird",
    )

    with pytest.raises(ValueError, match="Unsupported execution executor: weird"):
        run_execution_checks(tmp_path, config)


def test_run_execution_checks_docker_executor_requires_docker_config(tmp_path):
    config = ExecutionConfig(
        build_command="build",
        test_command=None,
        timeout_seconds=5,
        executor="docker",
        docker=None,
    )

    with pytest.raises(ValueError, match="docker config is required"):
        run_execution_checks(tmp_path, config)
