from dataclasses import dataclass
from pathlib import Path
import tomllib


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class ExecutionConfig:
    build_command: str | None
    test_command: str | None
    timeout_seconds: int


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

    return ExecutionConfig(
        build_command=_optional_command(commands, "build"),
        test_command=_optional_command(commands, "test"),
        timeout_seconds=_timeout_seconds(execution),
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
