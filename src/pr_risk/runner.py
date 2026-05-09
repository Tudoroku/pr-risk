from dataclasses import dataclass
from pathlib import Path
import subprocess
import time

from pr_risk.config import ExecutionConfig


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration_seconds: float


@dataclass(frozen=True)
class ExecutionResult:
    build: CommandResult | None
    test: CommandResult | None
    test_skipped: bool = False
    test_skip_reason: str | None = None


def run_command(
    name: str,
    command: str,
    cwd: Path,
    timeout_seconds: int,
) -> CommandResult:
    start_time = time.monotonic()

    try:
        # shell=True is local/trusted-config only; Docker isolation is future work.
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=True,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            name=name,
            command=command,
            exit_code=None,
            stdout=_safe_output(exc.stdout),
            stderr=_safe_output(exc.stderr),
            timed_out=True,
            duration_seconds=time.monotonic() - start_time,
        )

    return CommandResult(
        name=name,
        command=command,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        timed_out=False,
        duration_seconds=time.monotonic() - start_time,
    )


def run_execution_checks(repo_path: Path, config: ExecutionConfig) -> ExecutionResult:
    build_result = None
    if config.build_command is not None:
        build_result = run_command(
            "build",
            config.build_command,
            repo_path,
            config.timeout_seconds,
        )

    if build_result is not None:
        if build_result.timed_out:
            return ExecutionResult(
                build=build_result,
                test=None,
                test_skipped=True,
                test_skip_reason="Build timed out",
            )
        if build_result.exit_code != 0:
            return ExecutionResult(
                build=build_result,
                test=None,
                test_skipped=True,
                test_skip_reason="Build failed",
            )

    test_result = None
    if config.test_command is not None:
        test_result = run_command(
            "test",
            config.test_command,
            repo_path,
            config.timeout_seconds,
        )

    return ExecutionResult(build=build_result, test=test_result)


def _safe_output(output: str | bytes | None) -> str:
    if output is None:
        return ""

    if isinstance(output, bytes):
        return output.decode(errors="replace")

    return output
