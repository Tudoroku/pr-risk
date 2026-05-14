from pathlib import Path
import subprocess
import time

from pr_risk.runner import CommandResult


def run_docker_command(
    name: str,
    command: str,
    repo_path: Path,
    image: str,
    workdir: str,
    timeout_seconds: int,
) -> CommandResult:
    start_time = time.monotonic()
    resolved_repo_path = Path(repo_path).resolve()
    docker_args = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{resolved_repo_path}:{workdir}",
        "-w",
        workdir,
        image,
        "sh",
        "-c",
        command,
    ]

    try:
        completed = subprocess.run(
            docker_args,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
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
    except FileNotFoundError:
        return CommandResult(
            name=name,
            command=command,
            exit_code=127,
            stdout="",
            stderr="Docker executable was not found",
            timed_out=False,
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
