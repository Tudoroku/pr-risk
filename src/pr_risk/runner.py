from dataclasses import dataclass
from pathlib import Path
import subprocess
import time


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration_seconds: float


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


def _safe_output(output: str | bytes | None) -> str:
    if output is None:
        return ""

    if isinstance(output, bytes):
        return output.decode(errors="replace")

    return output
