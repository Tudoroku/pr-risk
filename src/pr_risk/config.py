from dataclasses import dataclass
from pathlib import Path
import tomllib


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class DockerConfig:
    image: str | None
    workdir: str = "/workspace"


@dataclass(frozen=True)
class ExecutionConfig:
    build_command: str | None
    test_command: str | None
    timeout_seconds: int
    executor: str = "local"
    docker: DockerConfig | None = None
    ci_fail_on: str = "never"


def load_config(repo_path: Path) -> ExecutionConfig:
    config_path = repo_path / ".pr-risk.toml"
    if not config_path.exists():
        return _default_config()

    try:
        with config_path.open("rb") as config_file:
            config_data = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {config_path}") from exc

    commands = _table(config_data, "commands")
    execution = _table(config_data, "execution")
    ci = _table(config_data, "ci")
    executor = _executor(execution)

    return ExecutionConfig(
        build_command=_optional_command(commands, "build"),
        test_command=_optional_command(commands, "test"),
        timeout_seconds=_timeout_seconds(execution),
        executor=executor,
        docker=_docker_config(config_data, executor),
        ci_fail_on=_ci_fail_on(ci),
    )


def _default_config() -> ExecutionConfig:
    return ExecutionConfig(
        build_command=None,
        test_command=None,
        timeout_seconds=300,
    )


def _table(config_data: dict[str, object], name: str) -> dict[str, object]:
    value = config_data.get(name, {})
    if not isinstance(value, dict):
        raise ConfigError(f"Config section [{name}] must be a table")
    return value


def _optional_command(commands: dict[str, object], name: str) -> str | None:
    value = commands.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError(f"Command {name} must be a string")

    command = value.strip()
    if not command:
        return None
    return command


def _timeout_seconds(execution: dict[str, object]) -> int:
    value = execution.get("timeout_seconds", 300)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError("execution.timeout_seconds must be a positive integer")
    if value <= 0:
        raise ConfigError("execution.timeout_seconds must be positive")
    return value


def _executor(execution: dict[str, object]) -> str:
    value = execution.get("executor", "local")
    if not isinstance(value, str):
        raise ConfigError("execution.executor must be one of: local, docker")

    executor = value.strip()
    if executor not in {"local", "docker"}:
        raise ConfigError("execution.executor must be one of: local, docker")
    return executor


def _ci_fail_on(ci: dict[str, object]) -> str:
    value = ci.get("fail_on", "never")
    if not isinstance(value, str):
        raise ConfigError("ci.fail_on must be one of: never, medium, high")

    fail_on = value.strip()
    if fail_on not in {"never", "medium", "high"}:
        raise ConfigError("ci.fail_on must be one of: never, medium, high")
    return fail_on


def _docker_config(config_data: dict[str, object], executor: str) -> DockerConfig | None:
    if executor != "docker":
        return None

    docker = _table(config_data, "docker")
    image = _docker_image(docker)
    return DockerConfig(
        image=image,
        workdir=_docker_workdir(docker),
    )


def _docker_image(docker: dict[str, object]) -> str:
    value = docker.get("image")
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("docker.image is required when execution.executor is docker")
    return value.strip()


def _docker_workdir(docker: dict[str, object]) -> str:
    value = docker.get("workdir", "/workspace")
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("docker.workdir must be a non-empty string")
    return value.strip()
