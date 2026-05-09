import subprocess
import sys

from pr_risk.runner import CommandResult, run_command


def _write_script(tmp_path, name, contents):
    script = tmp_path / name
    script.write_text(contents, encoding="utf-8")
    return script


def _python_command(script):
    return subprocess.list2cmdline([sys.executable, str(script)])


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
